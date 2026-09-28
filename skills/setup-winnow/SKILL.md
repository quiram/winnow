---
name: setup-winnow
description: >-
  Prepare a machine and a project so that every winnow skill runs without
  surprises: check the AI context and its doc map, the task tracker and whether
  winnow can reach it, the working area outside the repo, and the local audio
  stack — then establish whatever is missing, with the user's approval and
  without paying for anything they don't need. Idempotent and safe to re-run —
  it changes nothing that is already in place. Use when asked to set up,
  prepare, configure or onboard winnow, before first use on a machine or in a
  repo, or when a winnow skill reports a missing prerequisite.
---

# Set up winnow

You get a machine and a project into a state where every winnow skill just works. The point is not a report — it is that nobody discovers a missing prerequisite in the middle of something else: a documentation structure demanded at the moment the user expected agreed knowledge to be filed, a tracker credential missing once every ticket has been drafted, a model download starting as a meeting begins.

Four things winnow depends on:

- **The AI context and its doc map** — winnow grounds its triage in it, update-context writes to it, listen-to-meeting checks live statements against it.
- **The task tracker** — create-tasks writes tickets to it and needs a working way in.
- **A working area outside the host repo** — the pipeline hands proposals and transcripts between skills without leaving a footprint in the project.
- **The audio stack** — what transcribe-audio and listen-to-meeting run on, if this machine will handle voice notes or live meetings at all.

You own none of them. Each has a skill that does, and you delegate to it. Your job is the order, the asking, and the verdict. Everything here is idempotent: re-running changes nothing that is already in place.

## Step 1 — Find out what is missing, before asking anything

Do all of this first, and quietly. A machine and project that are already set up should be told exactly that, without being asked a single question.

**The project side** — all read-only, all quick:

- An AI context entry point: `AGENTS.md`, `CLAUDE.md`, `README.md`, a `docs/` or `context/` directory, or whatever the repo's conventions point to.
- A doc map in it: explicit meta-documentation, or a structure and cross-references that already make clear where each kind of knowledge lives.
- The project's own documentation machinery, if it has one — instructions, a skill, a plugin, or scripts in the repo. Where it exists, it defines where knowledge goes, not winnow.
- A named task tracker, and whether more than one is plausible.
- The working area: your harness's scratchpad if it provides one, otherwise that `/tmp/winnow/<repo-folder-name>-<hash>/` can be created, with `shasum` available for the hash the other skills derive the same path from (`printf '%s' "<abs repo root>" | shasum -a 256 | cut -c1-8`).

**The audio side**, from the filesystem only. Don't run the audio tooling yet: its first run *is* the slow part, and knowing whether it would be slow is the whole point of asking first.

- `uv` on the PATH.
- On macOS, a compiled capture helper in `~/.cache/winnow/` (`system-audio-capture-<hash>`).
- The Whisper model in the Hugging Face cache (`models--Systran--faster-whisper-<size>`, under `~/.cache/huggingface/hub` unless `HF_HOME` or `XDG_CACHE_HOME` moves it).

Those three are a signal, not proof — the helper is cached per source version, so an older binary can linger, and only winnow-setup-audio's own check is authoritative. What they tell you is what the audio phase would *cost*. All present, and it is a fast re-verification. Any of them missing, and it means resolving a Python environment, compiling a Swift helper, a download of a few hundred megabytes, and possibly an OS permission prompt that needs the terminal restarted afterwards.

## Step 2 — Report, then ask once

Tell the user what is already in place and what is missing, with the cost attached to anything that isn't cheap. Then ask what to do now, in a single exchange rather than a drip of questions.

Two things shape the ask:

- **Audio is only needed by some users.** Ask whether this machine will handle voice notes or live meetings at all — a project whose requirements arrive as text needs none of it.
- **The project side is nearly free.** Where something is missing there, the fix is a conversation, not a download; it is rarely worth deferring.

If nothing is missing, say so and stop. Don't ask a question you already know the answer to.

Nothing slow, interactive, or irreversible happens before the user has answered.

## Step 3 — Delegate, cheapest first

Invoke the skill that owns each part, in this order, and never do its work yourself:

1. **winnow-setup-context** — the AI context and its doc map. First, because the tracker's answer gets recorded into the context, so the context has to exist to receive it.
2. **winnow-setup-tracker** — the tracker, and a verified way to reach it.
3. **winnow-setup-audio** — uv, the Python audio stack, the macOS helper, the OS permission, the model download, and a live capture self-test.

Skip any part Step 1 found in place, or that the user declined. If one of them cannot finish — the user cancels, a permission needs a terminal restart, a credential is theirs to create — carry on with the rest and record what remains. A blocked part is not a reason to leave the others undone.

One thing is yours rather than a part's: if the user expects to bring meeting transcripts in as links (a Granola MCP server, an authenticated fetch for a private doc), confirm such a tool is actually reachable, and say so if it isn't — winnow stops rather than guess at a transcript it cannot read. Nothing else depends on it.

## Step 4 — Give the verdict

Close with the state everything ended in, part by part: what was already in place, what this run established, and for anything unresolved exactly what remains and whose action it needs. The parts each report on themselves; the overall verdict is yours alone to give.

Then say what it means in the terms the user cares about — which skills are ready, and which are not and why:

- **winnow, update-context, create-tasks** — the pipeline, ready once the AI context, its doc map and the tracker are in place.
- **transcribe-audio, listen-to-meeting** — voice notes and live meetings, ready once the audio stack passes its self-test.

If a permission grant needs the terminal restarted, say so plainly, and that re-running this skill afterwards is how to confirm it — it will change nothing that is already done.
