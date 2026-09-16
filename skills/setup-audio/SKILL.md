---
name: setup-audio
description: >-
  Prepare the machine for winnow's audio skills in one guided pass: verify uv
  and the Python audio stack, compile the macOS system-audio helper, walk the
  user through OS permissions, download the local Whisper model, and finish
  with a live capture self-test. Idempotent and safe to re-run — it changes
  nothing that is already in place. Use when asked to set up or prepare audio
  transcription or meeting listening, before a first meeting, or when
  transcribe-audio or listen-to-meeting report missing prerequisites.
---

# Set up audio

You prepare a machine so that **transcribe-audio** and **listen-to-meeting** just work when they are needed — moving every slow or interactive step (downloads, compilation, permission prompts) to a moment when nothing depends on them, instead of the start of a meeting or the arrival of a voice note. Run to completion whenever invoked: the goal is a machine that passes every check, not a report of what would fail.

This skill has no tools of its own; it drives the ones shipped with the other audio skills — `listen.py` in listen-to-meeting's scripts directory, whose `check` covers everything transcribe-audio needs too. Nothing here duplicates their logic, and nothing here touches the host project: everything lands in per-user caches (uv environments, the Hugging Face model cache, the compiled helper in `~/.cache/winnow`), shared by every project on the machine.

## Step 1 — uv

Everything below runs through `uv`. If it is not on the PATH, have the user install it, then continue:

- macOS: `brew install uv`
- macOS/Linux script: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows: `winget install astral-sh.uv`

## Step 2 — Run the readiness check

```bash
uv run <listen-to-meeting-skill-dir>/scripts/listen.py check
```

The first run performs real setup work as a side effect — it resolves the Python environment (a short one-time download) and, on macOS, compiles the capture helper — so a slow first check is normal. It verifies the Python audio dependencies, a working microphone, the transcription engine, the Whisper model cache, and the OS-specific system-audio route:

- **macOS**: a Core Audio system-audio tap (macOS 14.2+; the helper compiles automatically but needs the Xcode Command Line Tools), gated behind the System Audio Recording permission — audio only, no screen access. The permission prompt may fire during the check; after the user grants it, the terminal must be restarted, so expect to re-run this skill afterwards.
- **Windows**: native WASAPI loopback — no extra software.
- **Linux**: the default sink's PulseAudio/PipeWire monitor source (`parec`, from pulseaudio-utils; works on PipeWire via pipewire-pulse).

## Step 3 — Fix, re-run, repeat

Relay each gap the check reports, with the instruction it prints (install the Xcode Command Line Tools, accept the Xcode license, grant the permission, install a package). Every fix is the user's action on their machine — never work around a missing prerequisite. After each fix, re-run the check, until it ends with `ready: yes`.

## Step 4 — Prefetch the model

If the check reports the Whisper model as not cached, offer to download it now: a one-time, per-machine download of a few hundred MB (the default `small` model is roughly 500 MB) into the user's Hugging Face cache, shared by every project on the machine. State the size and get the user's go-ahead, then:

```bash
uv run <listen-to-meeting-skill-dir>/scripts/listen.py prefetch
```

Skipping this only defers the download to first real use — which is exactly the moment it hurts.

## Step 5 — Self-test with real audio

A passing check proves the pieces exist; it does not prove audio actually flows — a permission can report as granted while capture yields pure silence. Finish with a live test. **Warn the user before running it: it plays a short tone through the speakers.** Ask them to make sure output is unmuted and at an audible volume, and wait for their go-ahead so the sound doesn't startle anyone — they may be in an office or on a call.

```bash
uv run <listen-to-meeting-skill-dir>/scripts/listen.py selftest
```

It captures both channels for a few seconds, plays the tone, and reports per channel whether real signal arrived. On mute: the macOS tap captures upstream of the output mute and may pass even on a muted machine, but Windows loopback and Linux monitor sources capture what the endpoint plays, so mute can fail them — unmuting is part of the test conditions, not a nicety. If the system channel stays silent while the tone was audible, treat it as a real capture problem: re-check the permission, restart the terminal, re-run.

## Step 6 — Report

Tell the user the state the machine ended in: what was already in place, what this run installed, downloaded, or got granted, and that transcribe-audio (voice notes, recordings — including as input to process-requirements) and listen-to-meeting (live meetings) are now ready. If something could not be completed, say exactly what remains and whose action it needs.
