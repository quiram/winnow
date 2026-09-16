#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "faster-whisper>=1.1,<2",
#     "numpy>=1.24",
#     "sounddevice>=0.4.6",
#     "soundcard>=0.4.3; sys_platform == 'win32'",
# ]
# ///
"""Live meeting capture for the listen-to-meeting skill.

Captures two audio channels — the user's microphone ("Me") and the system /
speaker audio carrying the other participants ("Others") — transcribes both
locally through one shared Whisper model (via the transcribe-audio skill's
module), and writes finalized transcript chunks to files that the agent
polls. Everything runs on this machine; no hosted service is involved.

Commands:
  check   verify the capture path for this OS and report actionable,
          OS-specific setup instructions for anything missing (exit 0 = ready)
  run     capture until stopped: --session-dir receives chunk-NNNN.txt files,
          a running transcript.md, and status.json. Stop by creating a file
          named `stop` in the session dir (or SIGTERM/SIGINT).

Layering: all audio-level segmentation — voice-activity detection and
utterance finalization — belongs to transcribe-audio's StreamSegmenter; this
script feeds it raw PCM continuously and decides nothing about audio
boundaries. What it does own is text-level batching: the finalized text
segments coming back from transcription, from both channels, are batched
into chunks of at least MIN_CHUNK and at most MAX_CHUNK seconds, flushed
early at conversation-turn boundaries (a channel switch or a pause) once the
minimum is met. That interleaving of two labelled channels is the reason the
batching lives here and not in the generic single-stream transcriber.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

# The transcription engine lives in the transcribe-audio skill; both skills
# ship in the same package, so it is reachable relative to this file.
TRANSCRIBE_SCRIPTS = Path(__file__).resolve().parents[2] / "transcribe-audio" / "scripts"
sys.path.insert(0, str(TRANSCRIBE_SCRIPTS))

CAPTURE_RATE = 48_000  # capture rate; decimated 3:1 to Whisper's 16 kHz
MIN_CHUNK = 5.0
MAX_CHUNK = 60.0
TURN_GAP = 2.0  # a pause this long counts as a turn boundary
IDLE_FLUSH = 3.0  # flush pending segments after this much silence
MIC_LABEL = "Me"
SYSTEM_LABEL = "Others"


def fail(message: str) -> "NoReturn":  # noqa: F821
    print(message, file=sys.stderr)
    sys.exit(1)


# --------------------------------------------------------------------------
# Audio plumbing
# --------------------------------------------------------------------------


class Decimator:
    """48 kHz -> 16 kHz by averaging non-overlapping triples (fine for ASR)."""

    def __init__(self, np):
        self._np = np
        self._carry = np.zeros(0, dtype=np.float32)

    def process(self, samples):
        np = self._np
        samples = np.concatenate([self._carry, np.asarray(samples, dtype=np.float32)])
        usable = (len(samples) // 3) * 3
        self._carry = samples[usable:]
        if usable == 0:
            return np.zeros(0, dtype=np.float32)
        return samples[:usable].reshape(-1, 3).mean(axis=1)


class Channel:
    """One audio channel: capture -> decimate -> VAD segmentation."""

    def __init__(self, label: str, segmenter, np):
        self.label = label
        self.segmenter = segmenter
        self.decimator = Decimator(np)
        self.np = np
        self.started_at: float | None = None  # session-relative capture start

    def feed_int16_48k(self, pcm_bytes: bytes, session_t0: float) -> None:
        if self.started_at is None:
            self.started_at = time.monotonic() - session_t0
        samples = self.np.frombuffer(pcm_bytes, dtype=self.np.int16).astype(
            self.np.float32
        ) / 32768.0
        self.segmenter.feed_float32(self.decimator.process(samples))

    def feed_float32_48k(self, samples, session_t0: float) -> None:
        if self.started_at is None:
            self.started_at = time.monotonic() - session_t0
        self.segmenter.feed_float32(self.decimator.process(samples))


def start_mic_capture(channel: Channel, session_t0: float, stop_event: threading.Event):
    """Microphone capture via sounddevice/PortAudio (cross-platform)."""
    import sounddevice as sd

    def callback(indata, frames, time_info, status):
        if stop_event.is_set():
            raise sd.CallbackStop
        channel.feed_float32_48k(indata[:, 0].copy(), session_t0)

    stream = sd.InputStream(
        samplerate=CAPTURE_RATE, channels=1, dtype="float32", callback=callback
    )
    stream.start()
    return stream


def macos_helper_binary(compile_if_missing: bool = True) -> Path:
    """Compile the ScreenCaptureKit helper on first use; cache by source hash."""
    source = Path(__file__).resolve().parent / "macos" / "SystemAudioCapture.swift"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:12]
    cache_dir = Path.home() / ".cache" / "winnow"
    binary = cache_dir / f"system-audio-capture-{digest}"
    if binary.exists():
        return binary
    if not compile_if_missing:
        raise FileNotFoundError("helper not compiled yet")
    if not shutil.which("swiftc"):
        fail(
            "swiftc not found. Install the Xcode Command Line Tools:\n"
            "  xcode-select --install"
        )
    cache_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["swiftc", "-O", str(source), "-o", str(binary)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "license" in stderr.lower():
            fail(
                "swiftc cannot run until the Xcode license is accepted:\n"
                "  sudo xcodebuild -license accept\n\n" + stderr
            )
        fail(f"failed to compile the macOS audio helper:\n{stderr}")
    return binary


def linux_monitor_command() -> list[str]:
    """Command that streams the default sink's monitor as s16le mono 48 kHz."""
    if shutil.which("pactl") and shutil.which("parec"):
        sink = subprocess.run(
            ["pactl", "get-default-sink"], capture_output=True, text=True
        ).stdout.strip()
        if sink:
            return [
                "parec",
                "-d",
                f"{sink}.monitor",
                "--format=s16le",
                f"--rate={CAPTURE_RATE}",
                "--channels=1",
            ]
    if shutil.which("pw-record"):
        return [
            "pw-record",
            "--rate", str(CAPTURE_RATE),
            "--channels", "1",
            "--format", "s16",
            "-P", "stream.capture.sink=true",
            "-",
        ]
    fail(
        "No PulseAudio/PipeWire capture utility found. Install one:\n"
        "  Debian/Ubuntu: sudo apt install pulseaudio-utils\n"
        "  Fedora:        sudo dnf install pulseaudio-utils\n"
        "(pipewire-pulse provides pactl/parec on PipeWire systems)"
    )


def start_system_capture(channel: Channel, session_t0: float, stop_event: threading.Event):
    """System/speaker audio capture; OS-specific. Returns a cleanup callable."""
    platform = sys.platform

    if platform == "darwin":
        binary = macos_helper_binary()
        process = subprocess.Popen(
            [str(binary)], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        def reader():
            while not stop_event.is_set():
                data = process.stdout.read(CAPTURE_RATE // 5 * 2)  # ~0.1 s
                if not data:
                    break
                channel.feed_int16_48k(data, session_t0)

        threading.Thread(target=reader, daemon=True).start()

        def cleanup():
            process.terminate()

        # Fail fast if the helper dies immediately (e.g. no permission).
        time.sleep(1.0)
        if process.poll() is not None:
            stderr = process.stderr.read().decode(errors="replace")
            fail(f"macOS system-audio helper exited at startup:\n{stderr}")
        return cleanup

    if platform == "win32":
        import soundcard as sc

        speaker = sc.default_speaker()
        loopback = sc.get_microphone(speaker.name, include_loopback=True)

        def recorder():
            with loopback.recorder(samplerate=CAPTURE_RATE, channels=1) as rec:
                while not stop_event.is_set():
                    data = rec.record(numframes=CAPTURE_RATE // 10)  # 0.1 s
                    channel.feed_float32_48k(data[:, 0], session_t0)

        thread = threading.Thread(target=recorder, daemon=True)
        thread.start()
        return lambda: None

    if platform.startswith("linux"):
        command = linux_monitor_command()
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        def reader():
            while not stop_event.is_set():
                data = process.stdout.read(CAPTURE_RATE // 5 * 2)
                if not data:
                    break
                channel.feed_int16_48k(data, session_t0)

        threading.Thread(target=reader, daemon=True).start()
        time.sleep(1.0)
        if process.poll() is not None:
            stderr = process.stderr.read().decode(errors="replace")
            fail(f"system-audio capture ({command[0]}) exited at startup:\n{stderr}")
        return lambda: process.terminate()

    fail(f"unsupported platform: {platform}")


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------


def cmd_check(args) -> int:
    ready = True

    def report(item: str, ok: bool, detail: str = ""):
        nonlocal ready
        ready = ready and ok
        status = "ok" if ok else "MISSING"
        print(f"{item}: {status}" + (f" — {detail}" if detail else ""))

    try:
        import numpy  # noqa: F401
        import sounddevice as sd

        report("python audio dependencies", True)
        try:
            device = sd.query_devices(kind="input")
            report("microphone", True, device["name"])
        except Exception as exc:
            report("microphone", False, f"no input device found ({exc})")
    except Exception as exc:
        report("python audio dependencies", False, str(exc))
        if sys.platform.startswith("linux"):
            print(
                "  PortAudio may be missing: sudo apt install libportaudio2 "
                "(Debian/Ubuntu) or sudo dnf install portaudio (Fedora)"
            )

    try:
        import transcribe

        report("transcription engine (transcribe-audio skill)", True)
        cached = transcribe.model_is_cached(args.model)
        print(f"whisper model '{args.model}' cached: {'yes' if cached else 'no'}")
        if not cached:
            print("  note: run `listen.py prefetch` before the meeting to download it now")
    except Exception as exc:
        report("transcription engine (transcribe-audio skill)", False, str(exc))

    if sys.platform == "darwin":
        if not shutil.which("swiftc"):
            report(
                "system audio (macOS/ScreenCaptureKit)",
                False,
                "swiftc not found — install Xcode Command Line Tools: "
                "xcode-select --install",
            )
        else:
            probe = subprocess.run(
                ["swiftc", "--version"], capture_output=True, text=True
            )
            if probe.returncode != 0 and "license" in (probe.stdout + probe.stderr).lower():
                report(
                    "system audio (macOS/ScreenCaptureKit)",
                    False,
                    "Xcode license not accepted — run: sudo xcodebuild -license accept",
                )
            else:
                try:
                    binary = macos_helper_binary()
                    check = subprocess.run(
                        [str(binary), "--check"], capture_output=True, text=True
                    )
                    if check.returncode == 0:
                        report("system audio (macOS/ScreenCaptureKit)", True, "permission granted")
                    else:
                        report(
                            "system audio (macOS/ScreenCaptureKit)",
                            False,
                            "Screen Recording permission not granted. Grant it in "
                            "System Settings > Privacy & Security > Screen & System "
                            "Audio Recording (a prompt may have just appeared), then "
                            "restart the terminal.",
                        )
                except SystemExit:
                    raise
                except Exception as exc:
                    report("system audio (macOS/ScreenCaptureKit)", False, str(exc))
    elif sys.platform == "win32":
        try:
            import soundcard as sc

            speaker = sc.default_speaker()
            report("system audio (WASAPI loopback)", True, speaker.name)
        except Exception as exc:
            report("system audio (WASAPI loopback)", False, str(exc))
    elif sys.platform.startswith("linux"):
        if shutil.which("parec") or shutil.which("pw-record"):
            report("system audio (PulseAudio/PipeWire monitor)", True)
        else:
            report(
                "system audio (PulseAudio/PipeWire monitor)",
                False,
                "install pulseaudio-utils (provides parec; works on PipeWire "
                "via pipewire-pulse)",
            )
    else:
        report("system audio", False, f"unsupported platform {sys.platform}")

    print(f"\nready: {'yes' if ready else 'no'}")
    return 0 if ready else 1


def cmd_prefetch(args) -> int:
    from transcribe import Transcriber

    print(f"loading model '{args.model}' (downloads on first use)...", file=sys.stderr)
    Transcriber(args.model)
    print("model ready", file=sys.stderr)
    return 0


# --------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------


def format_clock(seconds: float) -> str:
    m, s = divmod(int(max(0, seconds)), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


class ChunkWriter:
    """Batches finalized segments into chunk files per the chunking policy."""

    def __init__(self, session_dir: Path):
        self.chunk_dir = session_dir / "chunks"
        self.chunk_dir.mkdir(parents=True, exist_ok=True)
        self.transcript = session_dir / "transcript.md"
        self.transcript.write_text("# Meeting transcript\n\n", encoding="utf-8")
        self.pending: list[dict] = []
        self.counter = 0

    def add(self, segment: dict) -> None:
        if self.pending:
            last = self.pending[-1]
            span_with_new = segment["end"] - self.pending[0]["start"]
            turn_boundary = (
                segment["label"] != last["label"]
                or segment["start"] - last["end"] >= TURN_GAP
            )
            current_span = last["end"] - self.pending[0]["start"]
            if span_with_new > MAX_CHUNK or (current_span >= MIN_CHUNK and turn_boundary):
                self.flush()
        self.pending.append(segment)

    def maybe_idle_flush(self, stream_now: float) -> None:
        if not self.pending:
            return
        span = self.pending[-1]["end"] - self.pending[0]["start"]
        idle = stream_now - self.pending[-1]["end"]
        if idle >= IDLE_FLUSH and span >= MIN_CHUNK:
            self.flush()

    def flush(self, force: bool = False) -> None:
        if not self.pending:
            return
        self.pending.sort(key=lambda s: s["start"])
        self.counter += 1
        lines = [
            f"# chunk {self.counter:04d}",
            f"# {format_clock(self.pending[0]['start'])} - "
            f"{format_clock(self.pending[-1]['end'])}",
        ]
        for seg in self.pending:
            lines.append(
                f"[{format_clock(seg['start'])}] {seg['label']}: {seg['text']}"
            )
        body = "\n".join(lines) + "\n"
        final = self.chunk_dir / f"chunk-{self.counter:04d}.txt"
        tmp = final.with_suffix(".tmp")
        tmp.write_text(body, encoding="utf-8")
        os.replace(tmp, final)  # atomic: the polling agent never sees partials
        with self.transcript.open("a", encoding="utf-8") as fh:
            for seg in self.pending:
                fh.write(f"[{format_clock(seg['start'])}] {seg['label']}: {seg['text']}\n")
        self.pending = []


def cmd_run(args) -> int:
    from transcribe import StreamSegmenter, Transcriber

    import numpy as np

    session_dir = Path(args.session_dir).resolve()
    session_dir.mkdir(parents=True, exist_ok=True)
    stop_file = session_dir / "stop"
    if stop_file.exists():
        stop_file.unlink()

    print("loading whisper model...", file=sys.stderr)
    transcriber = Transcriber(args.model, args.language)
    print("model loaded", file=sys.stderr)

    session_t0 = time.monotonic()
    stop_event = threading.Event()
    channels = [
        Channel(MIC_LABEL, StreamSegmenter(), np),
        Channel(SYSTEM_LABEL, StreamSegmenter(), np),
    ]
    mic_channel, system_channel = channels

    mic_stream = start_mic_capture(mic_channel, session_t0, stop_event)
    system_cleanup = start_system_capture(system_channel, session_t0, stop_event)

    work: "queue.Queue" = queue.Queue()
    results: "queue.Queue" = queue.Queue()

    def transcription_worker():
        while True:
            item = work.get()
            if item is None:
                results.put(None)
                return
            channel, utterance = item
            text = transcriber.transcribe_array(utterance.audio)
            if text:
                offset = channel.started_at or 0.0
                results.put(
                    {
                        "label": channel.label,
                        "start": utterance.start + offset,
                        "end": utterance.end + offset,
                        "text": text,
                    }
                )

    threading.Thread(target=transcription_worker, daemon=True).start()

    writer = ChunkWriter(session_dir)
    status_path = session_dir / "status.json"

    import signal

    def request_stop(*_args):
        stop_event.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    print(f"listening; session dir: {session_dir}", file=sys.stderr)
    last_status = 0.0
    try:
        while not stop_event.is_set():
            time.sleep(0.25)
            if stop_file.exists():
                stop_event.set()
                break
            for channel in channels:
                for utterance in channel.segmenter.poll():
                    work.put((channel, utterance))
            drained = False
            while True:
                try:
                    segment = results.get_nowait()
                except queue.Empty:
                    break
                if segment:
                    writer.add(segment)
                    drained = True
            stream_now = time.monotonic() - session_t0
            writer.maybe_idle_flush(stream_now)
            if drained or stream_now - last_status >= 5.0:
                last_status = stream_now
                status_path.write_text(
                    json.dumps(
                        {
                            "listening": True,
                            "elapsed": round(stream_now, 1),
                            "chunks": writer.counter,
                        }
                    ),
                    encoding="utf-8",
                )
    finally:
        stop_event.set()
        try:
            mic_stream.stop()
            mic_stream.close()
        except Exception:
            pass
        try:
            system_cleanup()
        except Exception:
            pass

    # Drain: finalize whatever audio is still buffered.
    for channel in channels:
        for utterance in channel.segmenter.flush():
            work.put((channel, utterance))
    work.put(None)
    while True:
        segment = results.get()
        if segment is None:
            break
        writer.add(segment)
    writer.flush(force=True)
    status_path.write_text(
        json.dumps(
            {
                "listening": False,
                "elapsed": round(time.monotonic() - session_t0, 1),
                "chunks": writer.counter,
                "transcript": str(writer.transcript),
            }
        ),
        encoding="utf-8",
    )
    print(
        f"stopped; {writer.counter} chunk(s); transcript: {writer.transcript}",
        file=sys.stderr,
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--model", default="small", help="Whisper model size (default: small)")
    common.add_argument("--language", default=None, help="force a language code (default: auto-detect)")

    p_check = sub.add_parser("check", parents=[common], help="verify the capture path for this OS")
    p_check.set_defaults(func=cmd_check)

    p_prefetch = sub.add_parser("prefetch", parents=[common], help="download/load the model now")
    p_prefetch.set_defaults(func=cmd_prefetch)

    p_run = sub.add_parser("run", parents=[common], help="capture until stopped")
    p_run.add_argument("--session-dir", required=True, help="directory for chunks, transcript and status")
    p_run.set_defaults(func=cmd_run)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
