#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     # listen-to-meeting's listen.py imports this module, so it declares these
#     # same two pins in its own header. Keep the two blocks in step.
#     "faster-whisper>=1.1,<2",
#     "numpy>=1.24",
# ]
# ///
"""Local audio transcription on a Whisper-family model (faster-whisper).

Runs entirely on this machine: the only network access is the one-time
download of the model weights into the Hugging Face cache.

Modes:
  file      transcribe a complete audio file in one shot
  stream    read raw PCM (s16le, mono, 16 kHz) from stdin and emit finalized
            utterances as JSON lines on stdout as they become stable
  check     verify the runtime environment and report whether the model
            weights are already cached
  prefetch  download/load the model now (so a later run starts instantly)

Importable API — a supported contract, not an internal detail. `Transcriber`
(thread-safe, one shared model) and `StreamSegmenter` (per-channel VAD
segmentation) let another script run several audio channels through a single
model instance. listen-to-meeting's listen.py imports both, and depends on
them by name: treat a change to either signature as a breaking change to that
skill, not a local refactor. `model_is_cached` is part of the same contract —
its `check` command calls it. See CONTRIBUTING.md.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
from dataclasses import dataclass

SAMPLE_RATE = 16_000

DEFAULT_MODEL = "small"


def _load_numpy():
    import numpy as np

    return np


class Transcriber:
    """A thread-safe wrapper around one shared WhisperModel instance."""

    def __init__(
        self,
        model_size: str = DEFAULT_MODEL,
        language: str | None = None,
        device: str = "auto",
        compute_type: str = "int8",
    ):
        from faster_whisper import WhisperModel

        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.language = language
        self._lock = threading.Lock()

    def transcribe_array(self, audio) -> str:
        """Transcribe a float32 mono 16 kHz numpy array; returns plain text."""
        with self._lock:
            segments, _ = self.model.transcribe(
                audio,
                language=self.language,
                beam_size=1,
                condition_on_previous_text=False,
                vad_filter=False,  # the caller already segmented on speech
            )
            return " ".join(s.text.strip() for s in segments).strip()

    def transcribe_file(self, path: str, word_timestamps: bool = False):
        """Yield faster-whisper segments for a complete audio file."""
        with self._lock:
            segments, info = self.model.transcribe(
                path,
                language=self.language,
                vad_filter=True,
                word_timestamps=word_timestamps,
            )
            for segment in segments:
                yield segment


@dataclass
class Utterance:
    """A finalized stretch of speech, ready to transcribe."""

    audio: "object"  # float32 mono 16 kHz numpy array
    start: float  # seconds since the start of the stream
    end: float


class StreamSegmenter:
    """Turns a continuous mono 16 kHz PCM stream into finalized utterances.

    Feed PCM with `feed()`, then call `poll()` periodically. An utterance is
    interim while speech is still resolving and finalizes once followed by
    `silence_close` seconds of silence, or when it reaches `max_utterance`
    seconds (Whisper's window) regardless. Only finalized utterances are ever
    returned, so downstream transcription always sees stable audio.
    """

    KEEP_TAIL = 0.5  # seconds of context kept when discarding silence
    PAD = 0.15  # seconds of padding around detected speech

    def __init__(
        self,
        silence_close: float = 0.6,
        max_utterance: float = 30.0,
        min_speech: float = 0.25,
    ):
        np = _load_numpy()
        from faster_whisper.vad import VadOptions, get_speech_timestamps

        self._np = np
        self._get_speech_timestamps = get_speech_timestamps
        self._vad_options = VadOptions(
            min_silence_duration_ms=300, speech_pad_ms=100
        )
        self.silence_close = silence_close
        self.max_utterance = max_utterance
        self.min_speech = min_speech
        self._buf = np.zeros(0, dtype=np.float32)
        self._buf_start = 0  # absolute sample index of _buf[0]
        self._lock = threading.Lock()

    def feed(self, pcm_int16) -> None:
        np = self._np
        samples = np.asarray(pcm_int16, dtype=np.float32) / 32768.0
        with self._lock:
            self._buf = np.concatenate([self._buf, samples])

    def feed_float32(self, samples) -> None:
        np = self._np
        with self._lock:
            self._buf = np.concatenate(
                [self._buf, np.asarray(samples, dtype=np.float32)]
            )

    def poll(self) -> list[Utterance]:
        with self._lock:
            return self._poll_locked(force=False)

    def flush(self) -> list[Utterance]:
        """Finalize whatever is buffered (end of stream / shutdown)."""
        with self._lock:
            return self._poll_locked(force=True)

    def _poll_locked(self, force: bool) -> list[Utterance]:
        np = self._np
        sr = SAMPLE_RATE
        if len(self._buf) < int(0.5 * sr) and not force:
            return []
        if len(self._buf) == 0:
            return []

        speech = self._get_speech_timestamps(self._buf, self._vad_options)
        if not speech:
            # Pure silence: keep a short tail for context, drop the rest.
            keep = int(self.KEEP_TAIL * sr)
            if len(self._buf) > keep:
                self._drop(len(self._buf) - keep)
            return []

        last_end = speech[-1]["end"]
        trailing_silence = (len(self._buf) - last_end) / sr
        duration = len(self._buf) / sr

        if not force and trailing_silence < self.silence_close and duration < self.max_utterance:
            return []  # utterance still open (interim)

        # Finalize everything up to the end of detected speech.
        utterances: list[Utterance] = []
        for ts in speech:
            start = max(0, ts["start"] - int(self.PAD * sr))
            end = min(len(self._buf), ts["end"] + int(self.PAD * sr))
            if (end - start) / sr < self.min_speech:
                continue
            abs_start = (self._buf_start + start) / sr
            abs_end = (self._buf_start + end) / sr
            utterances.append(
                Utterance(audio=self._buf[start:end].copy(), start=abs_start, end=abs_end)
            )
        cut = min(len(self._buf), last_end + int(self.PAD * sr))
        self._drop(cut)
        return utterances

    def _drop(self, n_samples: int) -> None:
        self._buf = self._buf[n_samples:]
        self._buf_start += n_samples


def _format_timestamp(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def cmd_file(args) -> int:
    transcriber = Transcriber(args.model, args.language)
    out = open(args.output, "w", encoding="utf-8") if args.output else sys.stdout
    try:
        for segment in transcriber.transcribe_file(args.input):
            if args.timestamps:
                out.write(f"[{_format_timestamp(segment.start)}] {segment.text.strip()}\n")
            else:
                out.write(segment.text.strip() + "\n")
            out.flush()
    finally:
        if args.output:
            out.close()
    return 0


def cmd_stream(args) -> int:
    transcriber = Transcriber(args.model, args.language)
    segmenter = StreamSegmenter(
        silence_close=args.silence_close, max_utterance=args.max_utterance
    )
    np = _load_numpy()
    stdin = sys.stdin.buffer

    def emit(utterance: Utterance) -> None:
        text = transcriber.transcribe_array(utterance.audio)
        if not text:
            return
        line = json.dumps(
            {
                "start": round(utterance.start, 2),
                "end": round(utterance.end, 2),
                "text": text,
            },
            ensure_ascii=False,
        )
        print(line, flush=True)

    while True:
        data = stdin.read1(65536)
        if not data:
            break
        if len(data) % 2:  # keep int16 alignment across short reads
            data += stdin.read(1) or b"\x00"
        segmenter.feed(np.frombuffer(data, dtype=np.int16))
        for utterance in segmenter.poll():
            emit(utterance)
    for utterance in segmenter.flush():
        emit(utterance)
    return 0


def model_is_cached(model_size: str) -> bool:
    try:
        from huggingface_hub import try_to_load_from_cache

        repo = f"Systran/faster-whisper-{model_size}"
        result = try_to_load_from_cache(repo_id=repo, filename="model.bin")
        return isinstance(result, str)
    except Exception:
        return False


def cmd_check(args) -> int:
    problems = []
    try:
        import faster_whisper  # noqa: F401
        import numpy  # noqa: F401
    except Exception as exc:  # pragma: no cover - uv resolves these
        problems.append(f"python dependencies failed to import: {exc}")
    cached = model_is_cached(args.model)
    print(f"dependencies: {'ok' if not problems else 'FAIL'}")
    print(f"model '{args.model}' cached: {'yes' if cached else 'no'}")
    if not cached:
        print(
            f"note: first transcription will download the model "
            f"(run `transcribe.py prefetch --model {args.model}` to do it now)"
        )
    for problem in problems:
        print(f"problem: {problem}", file=sys.stderr)
    return 1 if problems else 0


def cmd_prefetch(args) -> int:
    print(f"loading model '{args.model}' (downloads on first use)...", file=sys.stderr)
    Transcriber(args.model)
    print("model ready", file=sys.stderr)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--model", default=DEFAULT_MODEL, help="Whisper model size (default: small)")
    common.add_argument("--language", default=None, help="force a language code (default: auto-detect)")

    p_file = sub.add_parser("file", parents=[common], help="transcribe a complete audio file")
    p_file.add_argument("input", help="audio file (wav, mp3, m4a, ogg/opus, ...)")
    p_file.add_argument("--output", help="write transcript here instead of stdout")
    p_file.add_argument("--timestamps", action="store_true", help="prefix each line with [hh:mm:ss]")
    p_file.set_defaults(func=cmd_file)

    p_stream = sub.add_parser(
        "stream", parents=[common], help="raw PCM (s16le mono 16 kHz) on stdin -> JSONL on stdout"
    )
    p_stream.add_argument("--silence-close", type=float, default=0.6)
    p_stream.add_argument("--max-utterance", type=float, default=30.0)
    p_stream.set_defaults(func=cmd_stream)

    p_check = sub.add_parser("check", parents=[common], help="verify environment and model cache")
    p_check.set_defaults(func=cmd_check)

    p_prefetch = sub.add_parser("prefetch", parents=[common], help="download/load the model now")
    p_prefetch.set_defaults(func=cmd_prefetch)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
