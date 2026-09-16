---
name: transcribe-audio
description: >-
  Transcribe audio to text entirely on the local machine using a
  Whisper-family model — no hosted transcription service, no account. File
  mode turns a complete audio file (voice note, recording) into a transcript
  in one shot; streaming mode turns a live PCM audio feed into finalized
  transcript segments as they become stable. Use when given an audio file or
  voice note to transcribe or process, or when another skill needs text from
  audio — process-requirements delegates audio input here, and
  listen-to-meeting builds on the streaming mode.
---

# Transcribe audio

Convert audio to text locally. This skill is a generic building block: it has no opinion about what the transcript is *for*. Other winnow skills delegate to it (process-requirements for audio input, listen-to-meeting for live capture), and it works just as well standalone.

Everything runs on this machine. The only network access ever made is the one-time download of the model weights into the local Hugging Face cache; after that, transcription works offline. Never substitute a hosted transcription API, even if one is available in your environment.

## The tool

The work is done by `scripts/transcribe.py` (in this skill's directory), a self-contained script whose dependencies — [faster-whisper](https://github.com/SYSTRAN/faster-whisper) and numpy — are declared inline (PEP 723). Run it with `uv run`; uv resolves and caches the environment automatically, leaving no footprint in the host project.

**Prerequisite: uv.** If `uv` is not on the PATH — or anything else below reports missing — invoke the **setup-audio** skill, which owns installation and setup guidance for winnow's whole audio stack; don't improvise a pip/venv workaround.

Check readiness (verifies imports and reports whether the model is cached):

```bash
uv run <this-skill-dir>/scripts/transcribe.py check
```

If the model is not yet cached, the first transcription will download it (a few hundred MB). When that delay matters — or the machine will be offline later — prefetch it: `uv run .../transcribe.py prefetch` (setup-audio offers this as part of first-time preparation).

## File mode

Given a complete audio file, produce the full transcript in one shot:

```bash
uv run <this-skill-dir>/scripts/transcribe.py file <audio-file> [--timestamps] [--output <path>] [--model <size>] [--language <code>]
```

Common formats all work — wav, mp3, m4a, ogg/opus (WhatsApp voice notes), flac. Language is auto-detected unless `--language` forces one. Write the transcript to wherever the calling context needs it — for pipeline use, that is a working file outside the host repo (scratchpad first, `/tmp/winnow/...` fallback), per winnow's no-footprint rule.

## Streaming mode

Given a live audio source, emit finalized transcript segments as they become stable, rather than waiting for the end:

```bash
<audio-source> | uv run <this-skill-dir>/scripts/transcribe.py stream [--model <size>] [--language <code>]
```

- **Input**: raw PCM on stdin — signed 16-bit little-endian, mono, 16 kHz. (On Windows, pipe via cmd or PowerShell 7.4+ — older PowerShell corrupts binary pipes. Callers that feed audio in-process, as listen-to-meeting does, are unaffected.)
- **Output**: one JSON object per line on stdout, each a finalized utterance: `{"start": 12.4, "end": 15.1, "text": "..."}` (times in seconds from stream start).
- **Finalization**: a voice-activity detector holds an utterance open (interim) while speech is still resolving, and finalizes it once ~0.6 s of trailing silence follows, or at 30 s regardless. Only finalized text is ever emitted; finalization happens continuously throughout the stream, not at the end.

For multi-channel callers (several audio sources through one model), import the script as a module instead of piping: `Transcriber` is a thread-safe shared model wrapper and `StreamSegmenter` a per-channel segmenter — this is what listen-to-meeting does.

## Choosing a model

The default, `small` (multilingual, int8), transcribes several times faster than real-time on any modern CPU and is accurate enough for meeting speech. Deviate only with reason:

- `base` or `tiny` — noticeably less accurate; only for very weak machines.
- `small.en` / `distil-small.en` — faster, English-only.
- `medium` and up — better accuracy but risks falling behind real-time on CPU; fine for file mode where pace doesn't matter.

Pass the choice with `--model`; don't hardcode it anywhere.
