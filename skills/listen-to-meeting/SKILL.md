---
name: listen-to-meeting
description: >-
  Listen to a live meeting through the machine's microphone and system audio,
  transcribe it locally in near-real-time, and flag unacknowledged
  contradictions while the meeting is still running so they can be resolved
  in the room. Deliberately narrow: it does not run the winnow pipeline live —
  formal processing happens afterwards via process-requirements on the full
  transcript. Use when asked to listen in on, monitor, or join a live meeting
  or call, or to catch inconsistencies as they happen.
---

# Listen to meeting

You are a live inconsistency-spotter, and only that. During the meeting you keep a running transcript and flag contradictions the room hasn't noticed; you do **not** triage requirements, update context, or create tasks live. When the meeting ends, you propose — never auto-run — **process-requirements** on the complete transcript, which is where the formal winnow pipeline begins, unchanged.

Everything runs locally: capture through the OS's own facilities, transcription through the **transcribe-audio** skill's local Whisper model. No hosted transcription or meeting-bot service is ever involved.

Two channels are captured and kept separate throughout: the user's microphone (labelled **Me**) and the system/speaker audio carrying the other participants (labelled **Others**). A channel switch is a cheap, useful proxy for "a different person is now talking" — there is no full speaker diarization.

## Step 1 — Preflight: verify the capture path, or stop

Before anything else, run the readiness check from this skill's directory:

```bash
uv run <this-skill-dir>/scripts/listen.py check
```

(If `uv` itself is missing, that is the first gap: tell the user to install it — `brew install uv`, `curl -LsSf https://astral.sh/uv/install.sh | sh`, or `winget install astral-sh.uv` — and stop.)

The check detects the host OS and verifies the whole path: Python audio dependencies, microphone, the transcription engine, and the OS-specific system-audio capture route —

- **macOS**: a small ScreenCaptureKit helper, compiled automatically on first use (needs the Xcode Command Line Tools) and gated behind the Screen Recording permission;
- **Windows**: native WASAPI loopback;
- **Linux**: the default sink's PulseAudio/PipeWire monitor source.

If the check reports anything missing, relay its instructions to the user **and stop — do not start a partial listening session** (e.g. mic-only). Every reported gap is fixable by the user (grant a permission, accept the Xcode license, install a package); once fixed, re-run the check. If the Whisper model isn't cached yet, run `uv run .../listen.py prefetch` before the meeting starts, not during it.

## Step 2 — Start listening, and say how to stop

Create a session directory in your scratchpad (or, failing that, under winnow's `/tmp/winnow/<repo-folder-name>-<hash>/` convention — same hash formula as the proposal directory — in a `listen/<timestamp>/` subfolder). Then launch the capture as a background process:

```bash
uv run <this-skill-dir>/scripts/listen.py run --session-dir <session-dir>
```

It loads the model, captures both channels, and writes finalized transcript chunks to `<session-dir>/chunks/chunk-NNNN.txt` (atomically — a chunk file is complete the moment it exists), plus a running `transcript.md` and a `status.json` heartbeat. All audio-level work — voice-activity detection, utterance finalization, transcription — is delegated to transcribe-audio; the tool here only captures raw audio and batches the transcribed *text* from the two channels into chunks: minimum ~5 s, maximum ~60 s, flushed early at conversation-turn boundaries (a channel switch or a pause).

Confirm from its startup output that it is actually capturing before telling the user you're listening.

**Immediately tell the user how to end the session.** Say it explicitly — don't leave them guessing. For example:

> I'm listening now. When the meeting ends, just tell me in plain language — "meeting's over", "we're done", "stop listening" — and I'll wrap up.

Treat any clear plain-language statement to that effect as the stop signal.

## Step 3 — Ground yourself while capture warms up

Discover the host project's AI context the same way process-requirements does — `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/`, or whatever the repo's conventions point to. Winnow has no context of its own; the project's recorded decisions, constraints and domain facts are one of the two baselines you check statements against. If no AI context exists, tell the user context-mismatch checking is unavailable and continue with in-meeting consistency checking only.

Create `<session-dir>/meeting-state.md` to hold the second baseline: a running model of what has been asserted **in this meeting** — one line per assertion, with channel, timestamp, and a status of `live` or `corrected`. Also track the number of the last chunk you processed there. Keep this file updated as you go: it is what lets you resume cleanly if your conversation context gets compacted mid-meeting.

## Step 4 — The listening loop

Wait for new chunk files, using whatever mechanism your harness provides — a file-watch or monitor tool, a blocking wait command, or periodic checks; never a busy-loop of instant re-checks. Process chunks strictly in order. For each new chunk:

1. **Update the meeting state.** Extract assertions — decisions, constraints, facts, commitments — and add them to `meeting-state.md`. Rephrasing of an existing assertion updates nothing.
2. **Distinguish correction from conflict** when a statement clashes with an earlier one:
   - **Correction** — the room is visibly aware: an explicit revision ("actually, scratch that", "let's change that to..."), or an immediate acknowledgement. Mark the earlier assertion `corrected`, record the new one, and stay silent. Corrections are the meeting working as intended.
   - **Conflict** — the contradiction passes unremarked (e.g. "seniors go free" at 00:03, then "we don't offer any discounts to anyone" at 00:14 with no reaction). This is exactly what you exist to catch.
3. **Apply the flagging threshold** below, and surface anything that passes it to the user in the chat, immediately — the value of a flag decays fast in a live meeting.
4. Record the chunk number as processed in `meeting-state.md`.

### Flagging threshold (v1 — expect to refine)

Surface a flag **only** if at least one of these holds:

1. **Contradicts recorded context** — the statement conflicts with something the project's AI context documents as a current decision, constraint, or fact.
2. **Unacknowledged in-meeting conflict** — it contradicts an earlier assertion whose status is still `live`, and nothing in the surrounding conversation suggests anyone noticed or resolved the clash.
3. **Build-changing ambiguity** — taken at face value it would change what gets built, and the room moved on without pinning it down.

Never flag: rephrasings or elaborations; refinements that narrow an earlier statement without reversing it; hedged exploration ("what if...", "maybe we could...") unless it gets adopted as a decision; small talk and logistics; figures differing only in precision ("about a hundred" vs "103").

When you are unsure whether the room noticed a contradiction, hold the flag for one more chunk and raise it only if it is still unresolved then. Bias firmly toward silence: a flag must be rare enough that every one gets read. A chatty flagger gets ignored, and then it catches nothing.

### Flag format

Short enough to act on mid-meeting, with the receipts and a ready-made question:

> ⚑ **Possible conflict** (00:14:30)
> Earlier (00:03:10, Others): "seniors go free"
> Now (00:14:30, Me): "we don't offer any discounts to anyone"
> Suggested check for the room: "Earlier we said seniors go free — are we dropping that, or is it an exception?"

## Step 5 — On the stop signal

When the user says the meeting is over:

1. **Tear down the capture**: create a file named `stop` in the session directory; the tool flushes remaining audio, writes the final chunks, completes `transcript.md`, and exits. Confirm it has exited before proceeding.
2. **Report briefly**: duration, number of flags raised, and where any unresolved flags stand.
3. **Propose the pipeline**: offer to run **process-requirements** on `<session-dir>/transcript.md` — the full accumulated transcript. **Only proceed if the user confirms; never auto-chain.** This is the same human checkpoint winnow uses between all its skills.

If the user declines, tell them where the transcript lives so it isn't lost, and leave the session directory in place. If they proceed, process-requirements takes over — the session directory can be cleaned up once the pipeline has consumed the transcript.
