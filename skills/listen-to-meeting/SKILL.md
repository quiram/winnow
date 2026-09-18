---
name: listen-to-meeting
description: >-
  Listen to a live meeting through the machine's microphone and system audio,
  transcribe it locally in near-real-time, and flag unacknowledged
  contradictions and information gaps while the meeting is still running, so
  they can be resolved in the room. Deliberately narrow: it does not run the
  winnow pipeline live — formal processing happens afterwards via
  process-requirements on the full transcript. Use when asked to listen in
  on, monitor, or join a live meeting or call, or to catch inconsistencies or
  missing information as they happen.
---

# Listen to meeting

You are a live meeting watcher with two narrow jobs: flag contradictions the room hasn't noticed, and surface genuine gaps — statements that presuppose information nobody has stated, or that don't anchor to anything the project knows — while the people who can resolve them are still in the room. You do **not** triage requirements, update context, or create tasks live. When the meeting ends, you propose — never auto-run — **process-requirements** on the complete transcript, which is where the formal winnow pipeline begins.

Everything runs locally: capture through the OS's own facilities, transcription through the **transcribe-audio** skill's local Whisper model. No hosted transcription or meeting-bot service is ever involved.

Two channels are captured and kept separate throughout: the user's microphone (labelled **Me**) and the system/speaker audio carrying the other participants (labelled **Others**). A channel switch is a cheap, useful proxy for "a different person is now talking" — there is no full speaker diarization.

## Step 1 — Preflight: verify the capture path, or stop

Before anything else, run the readiness check from this skill's directory:

```bash
uv run <this-skill-dir>/scripts/listen.py check
```

If it ends with `ready: yes`, continue — though if it notes the Whisper model isn't cached yet, prefer getting that download done (via **setup-audio** or `listen.py prefetch`) before the meeting starts, not during it.

Anything else — including `uv` itself being missing, so the check can't even run — is a setup problem, and setup is not this skill's job: invoke the **setup-audio** skill, which owns all installation, permission, and download guidance, and **do not start listening until it reports the machine ready. Never start a partial session** (e.g. mic-only).

## Step 2 — Start listening, and say how to stop

Create a session directory in your scratchpad (or, failing that, under winnow's `/tmp/winnow/<repo-folder-name>-<hash>/` convention — same hash formula as the proposal directory — in a `listen/<timestamp>/` subfolder). Then launch the capture as a background process:

```bash
uv run <this-skill-dir>/scripts/listen.py run --session-dir <session-dir>
```

It loads the model, captures both channels, and writes finalized transcript chunks to `<session-dir>/chunks/chunk-NNNN.txt` (atomically — a chunk file is complete the moment it exists), plus a running `transcript.md` and a `status.json` heartbeat. All audio-level work — voice-activity detection, utterance finalization, transcription — is delegated to transcribe-audio; the tool here only captures raw audio and batches the transcribed *text* from the two channels into chunks: minimum ~5 s, maximum ~60 s, flushed early at conversation-turn boundaries (a channel switch or a pause).

Confirm from its startup output that it is actually capturing before telling the user you're listening — and keep an eye on `status.json`'s `warnings` list early in the session: an entry means a channel has produced no signal at all (dead capture, a muted mic, a missing permission). A silent system channel can also just mean no other participant has spoken yet, so the warning clears itself once audio arrives; if it persists once the meeting is clearly under way — the other channel keeps producing transcript, or several minutes have passed — relay it and ask the user, who knows whether that channel should have carried sound by now, and let them decide whether to fix it or knowingly continue with one channel.

**Immediately tell the user how to end the session.** Say it explicitly — don't leave them guessing. For example:

> I'm listening now. When the meeting ends, just tell me in plain language — "meeting's over", "we're done", "stop listening" — and I'll wrap up.

Treat any clear plain-language statement to that effect as the stop signal.

## Step 3 — Ground yourself while capture warms up

Discover the host project's AI context the same way process-requirements does — `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/`, or whatever the repo's conventions point to. Winnow has no context of its own; the project's recorded decisions, constraints and domain facts are one of the two baselines you check statements against. If no AI context exists, tell the user context-mismatch checking is unavailable and continue with in-meeting consistency checking only.

Create `<session-dir>/meeting-state.md` to hold the second baseline: a running model of what has been asserted **in this meeting** — one line per assertion, with channel, timestamp, and a status of `live` or `corrected` — plus the *candidate gaps* you are watching (status `watching`, `surfaced`, or `filled`). Also track two things there: the number of the last chunk you processed, and the meeting-clock time at which you last said anything to the user. Keep this file updated as you go: it is what lets you resume cleanly if your conversation context gets compacted mid-meeting.

## Step 4 — The listening loop

Wait for new chunk files with the tool's own blocking wait, run in the foreground, where `<n>` is the last chunk number you recorded as processed:

```bash
uv run <this-skill-dir>/scripts/wait.py --session-dir <session-dir> --after <n>
```

It prints the paths of any chunks past `<n>` and returns the moment one exists — or after 10 seconds if the room is silent, or immediately once the capture stops. Then process what it printed and call it again.

**Do not use a file-watch, monitor, or notification tool instead.** Every event they deliver is a visible message in the user's chat, and chunks arrive every few seconds; a foreground wait is silent. Nor should you raise the timeout: you cannot see the user's stop signal while blocked on it.

Process chunks strictly in order. For each new chunk:

1. **Update the meeting state.** Extract assertions — decisions, constraints, facts, commitments — and add them to `meeting-state.md`. Rephrasing of an existing assertion updates nothing.
2. **Distinguish correction from conflict** when a statement clashes with an earlier one:
   - **Correction** — the room is visibly aware: an explicit revision ("actually, scratch that", "let's change that to..."), or an immediate acknowledgement. Mark the earlier assertion `corrected`, record the new one, and stay silent. Corrections are the meeting working as intended.
   - **Conflict** — the contradiction passes unremarked (e.g. "seniors go free" at 00:03, then "we don't offer any discounts to anyone" at 00:14 with no reaction). This is exactly what you exist to catch.
3. **Watch for gaps.** A statement can contradict nothing and still be trouble, in two ways:
   - **Context misfit** — it leans on the project context where the context has nothing to lean on: a component, rule, constraint, or term the recorded context doesn't know, used as if settled.
   - **Missing information** — it presupposes something nobody has stated: an undefined term treated as defined, an unowned action ("someone should..."), a decision that silently assumes a prior decision that was never made.

   Record these in `meeting-state.md` as candidate gaps with status `watching` — not surfaced yet. On every later chunk, re-check the watch list: mark a gap `filled` (and drop it) the moment the meeting supplies the missing piece.
4. **Apply the flagging threshold** below, and surface anything that passes it to the user in the chat, immediately — the value of a flag decays fast in a live meeting.
5. Record the chunk number as processed in `meeting-state.md`.

### Flagging threshold

Surface a flag **only** if at least one of these holds:

1. **Contradicts recorded context** — the statement conflicts with something the project's AI context documents as a current decision, constraint, or fact.
2. **Unacknowledged in-meeting conflict** — it contradicts an earlier assertion whose status is still `live`, and nothing in the surrounding conversation suggests anyone noticed or resolved the clash.
3. **Build-changing ambiguity** — taken at face value it would change what gets built, and the room moved on without pinning it down.
4. **Unanchored, build-changing gap** — the statement presupposes information that neither this meeting nor the recorded context contains, the discussion is proceeding as if it were settled, and what gets built depends on it.

Never flag: rephrasings or elaborations; refinements that narrow an earlier statement without reversing it; hedged exploration ("what if...", "maybe we could...") unless it gets adopted as a decision; small talk and logistics; figures differing only in precision ("about a hundred" vs "103"). And for gaps specifically: terms or references the participants visibly share even though the recorded context doesn't — the room's common knowledge is a context-update candidate for after the meeting, not a live question — and gaps nothing in the meeting depends on resolving now, which process-requirements will catch on the full transcript anyway. A live gap flag is only worth its interruption when asking in the room beats asking afterwards.

When you are unsure whether the room noticed a contradiction, hold the flag for one more chunk and raise it only if it is still unresolved then. Gaps get a longer leash: meetings routinely clarify themselves, so hold a candidate gap for at least two further chunks (or until the topic visibly moves on) and surface it only if it is still open and the discussion has kept building on the unstated assumption — dropping it silently the moment the meeting fills it. Bias firmly toward silence: a flag must be rare enough that every one gets read. A chatty flagger gets ignored, and then it catches nothing.

### Staying quiet between flags

Silence is the correct output for an ordinary chunk, and ordinary is what almost every chunk is. Between the Step 2 confirmation and the first thing that passes the flagging threshold, say **nothing**. In particular, never narrate the listening itself: no "Listening.", no "Still listening — nothing to flag yet", no summarising what the room has moved on to. The user can hear their own meeting; a running commentary on it is pure noise, and it trains them to skim past your messages exactly when a real flag needs reading.

The one exception is proof of life. If nothing at all has gone to the user for **about ten minutes** — no flag, no question, no answer of any kind — send one short line so they know you are still up. Anything you send resets that clock, so an active meeting full of flags never produces one. Record the time in `meeting-state.md` whenever you send anything, and check it against the meeting clock rather than your sense of elapsed turns, which compaction destroys.

Keep it to a single line, and prefer saying something concrete about the state of the session over a bare ping:

> Still listening — 34 chunks in, nothing worth flagging so far.

### Flag format

Short enough to act on mid-meeting, with the receipts and a ready-made question. Conflicts:

> ⚑ **Possible conflict** (00:14:30)
> Earlier (00:03:10, Others): "seniors go free"
> Now (00:14:30, Me): "we don't offer any discounts to anyone"
> Suggested check for the room: "Earlier we said seniors go free — are we dropping that, or is it an exception?"

Gaps — quote the statement, say in one line what it is missing its anchor to, and offer the clarifying question:

> ❓ **Possible gap** (00:22:05)
> (00:22:05, Others): "The importer will just reuse the enterprise quota rules."
> Neither the project context nor this meeting has defined any enterprise quota rules.
> Suggested check for the room: "Do the enterprise quota rules exist somewhere already, or does the importer need them defined first?"

## Step 5 — On the stop signal

When the user says the meeting is over:

1. **Tear down the capture**: create a file named `stop` in the session directory; the tool flushes remaining audio, writes the final chunks, completes `transcript.md`, and exits. Confirm it has exited before proceeding.
2. **Report briefly**: duration, number of flags raised, and where any unresolved flags stand.
3. **Propose the pipeline**: offer to run **process-requirements** on `<session-dir>/transcript.md` — the full accumulated transcript. **Only proceed if the user confirms; never auto-chain.** This is the same human checkpoint winnow uses between all its skills.

If the user declines, tell them where the transcript lives so it isn't lost, and leave the session directory in place. If they proceed, process-requirements takes over — the session directory can be cleaned up once the pipeline has consumed the transcript.
