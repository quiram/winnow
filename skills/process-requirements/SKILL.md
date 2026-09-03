---
name: process-requirements
description: >-
  Distil requirements from a brainstorming conversation or from meeting
  transcripts. Separates noise from durable project knowledge and actionable
  work, surfaces gaps, conflicts and ambiguities, and produces a reviewable
  proposal that feeds the update-context and create-tasks skills. Use when
  brainstorming product requirements or roadmap items, when given one or more
  meeting transcripts or notes to process, or when asked to extract
  requirements, decisions or actions from a discussion.
---

# Process requirements

You are the analysis stage of a three-skill pipeline:

1. **process-requirements** (this skill) — understand the input, triage it, and write a proposal.
2. **update-context** — folds approved knowledge into the project's AI context documentation.
3. **create-tasks** — turns approved work items into tickets in the project's task tracker.

**This skill never edits context documentation and never touches the task tracker.** Its only output is a proposal file plus conversation with the user. Keeping analysis separate from application is deliberate: it gives a human a checkpoint before anything durable changes.

## Step 1 — Ground yourself in the project

Before analysing anything, find and read the project's AI context — the "advanced README" that holds durable knowledge. Look for the usual entry points: `AGENTS.md`, `CLAUDE.md`, `README.md`, a `docs/` or `context/` directory, or whatever the repo's own conventions point to. From it, learn at minimum:

- the project's purpose, objectives, and domain vocabulary;
- the tech stack and key architectural decisions;
- **where tasks are tracked** (JIRA, GitHub Issues, Linear, Trello, ...);
- any norms for documentation or task writing.

You cannot triage well without this baseline: relevance is defined relative to what the project already knows and cares about.

If no AI context exists, say so plainly. You may still triage the input, but flag that placement of knowledge will be unreliable and recommend establishing an AI context first. In an interactive session, ask whether to continue anyway; in a batch run, continue but record the missing context as the first open question in the proposal.

## Step 2 — Gather the input

Two modes of operation:

**Conversational.** A person is brainstorming with you. Act as a facilitator: trade questions back and forth, test ideas against the existing context, and keep going until a coherent set of requirements and knowledge has been surfaced *and agreed*. Don't rush to the proposal — the conversation is the work. Summarise what has been agreed at natural checkpoints so the user can correct you early.

**Transactional / batch.** You are given one or more transcripts to distil. Transcripts may arrive:

- **inline** — text pasted into the conversation;
- **as files** — read them from disk;
- **as links** — before doing anything else, check you actually have a tool that can access the link (e.g. a Granola MCP server for Granola transcripts, an authenticated fetch for a private doc). If no suitable tool or permission is available, stop and tell the user exactly what is missing — never guess at a transcript's content.

With multiple transcripts, process them all and keep per-source provenance: the proposal must say which source each item came from, because sources can disagree.

If a batch run is invoked by a person in a chat (rather than fully unattended), you may blend the modes: process the transcripts, then ask clarifying questions before finalising the proposal.

## Step 3 — Triage every piece of information

Sort everything in the input into exactly one of three buckets (or the fourth, hybrid case):

**Irrelevant.** Small talk, scheduling logistics, tangents, transient status updates ("the build was red this morning"), and restatements of what the context already documents. Discard it — but list what you dropped, one line per item, when you present your findings, so the user can catch anything that shouldn't have been discarded. No record of discarded content is kept beyond that mention in the conversation.

**Durable knowledge → context update.** Decisions, constraints, domain facts, architectural choices, conventions, goals, non-goals. The test: *would someone (person or AI) working on this project in three months need this to do the work correctly?* If yes, it belongs in the AI context, not in a ticket comment where it will be lost.

**Actionable work → candidate task.** Concrete work someone must do. The test: it has a plausible done-state and a *why* (a business goal, even an indirect one). A vague aspiration with no done-state is not a task — it is either knowledge (record the goal) or a gap (ask about it).

**Both.** A decision often implies work ("we're switching to PostgreSQL" = knowledge *and* a migration task). Record it in both sections and cross-reference the items.

When in doubt between irrelevant and knowledge, prefer to surface it as a question rather than silently discarding or silently recording.

## Step 4 — Hunt gaps, conflicts and ambiguity

Actively look for trouble; don't just transcribe:

- statements that **contradict the existing AI context** — has a documented decision been reversed, or is someone misinformed?
- statements from different sources or speakers that **contradict each other**;
- **undefined terms**, unstated assumptions, unowned decisions ("someone should...");
- candidate tasks with **no discernible goal**, or goals with no path to done;
- scope that is implied but never confirmed.

In an interactive session, ask the user. Batch related questions together rather than dripping them one at a time, and offer your best-guess interpretation alongside each question so the user can simply confirm.

In an unattended batch run, **never invent answers**. Record every unresolved point in the proposal's *Open questions* section, attached to the items it affects; downstream skills will refuse to act on items with blocking open questions.

## Step 5 — Write the proposal

Write the proposal **outside the repo** — the pipeline must leave no footprint in the host project, so never create working files or gitignore entries inside it. The proposal directory for a repo is:

```
/tmp/winnow/<repo-folder-name>-<hash>/proposals/YYYY-MM-DD-<topic-slug>.md
```

where `<hash>` is the first 8 hex characters of the SHA-256 of the repo root's absolute path (`printf '%s' "<abs repo root>" | shasum -a 256 | cut -c1-8`). The hash keeps two checkouts with the same folder name apart; the formula is fixed so the other skills in the pipeline can find the directory independently.

The proposal is **short-lived working state, not a project artefact**: it exists for the duration of a processing run — minutes, maybe hours, from writing through review to application — and downstream skills mark items as they process them and delete the file once every item has reached a terminal state. If the OS cleans `/tmp` before a proposal is applied, nothing durable is lost — re-run this skill from the original input. Always tell the user the full path you wrote to.

### Proposal format

The file is self-describing — downstream skills and humans parse it by its headings, so keep the structure exact:

```markdown
---
proposal: <topic-slug>
created: <YYYY-MM-DD>
status: pending-review   # pending-review | approved | in-progress
sources:
  - <one line per input: "meeting transcript 2026-09-01 (file: notes/x.md)">
---

# Proposal: <human-readable topic>

## Summary
<3–6 sentences: what was discussed, what this proposal changes.>

## Context updates
### CU-1: <short title>
- **Status:** pending          # pending | approved | applied | rejected
- **Target:** <doc path, or "unknown — needs doc map">
- **Source:** <which input / speaker>
- **Related:** T-2              # optional cross-references
- **Blocked by:** Q-1           # optional; open questions that must be answered first

<The knowledge itself, written out in full, plus a one-line rationale for
why it is durable knowledge.>

## Candidate tasks
### T-1: <short title>
- **Status:** pending          # pending | approved | created (<ticket ref>) | rejected
- **Goal:** <the business goal — the why>
- **Source:** <which input / speaker>
- **Depends on:** T-3           # optional; only when true independence is impossible
- **Blocked by:** Q-2           # optional

<What needs doing and what done looks like, in enough detail for
create-tasks to write a full ticket.>

## Open questions
### Q-1: <the question>
- **Affects:** CU-1, T-2
- **Best guess:** <your interpretation, clearly marked as a guess>
```

Number items sequentially (CU-n, T-n, Q-n) — the identifiers are how the user and the other skills refer to them.

## Step 6 — Hand off

Present the proposal to the user: summary first, then context updates, candidate tasks, and open questions. In conversational mode, iterate until the user marks items approved (update the item statuses as they decide). In batch mode, deliver the summary and the path to the proposal file.

Then point at the next step: run **update-context** for approved context updates and **create-tasks** for approved tasks. Do not perform those steps yourself, even if asked to "just do it all" — invoke the corresponding skill so its safeguards apply.
