---
name: process-requirements
description: >-
  Distil requirements from a brainstorming conversation or from meeting
  transcripts. Separates noise from durable project knowledge and actionable
  work, surfaces gaps, conflicts and ambiguities, agrees the findings with the
  user, and hands them to the update-context and create-tasks skills. Use when
  brainstorming product requirements or roadmap items, when given one or more
  meeting transcripts or notes to process, or when asked to extract
  requirements, decisions or actions from a discussion.
---

# Process requirements

You are the analysis stage of a three-skill pipeline:

1. **process-requirements** (this skill) — understand the input, triage it, and write a proposal.
2. **update-context** — folds approved knowledge into the project's AI context documentation.
3. **create-tasks** — turns approved work items into tickets in the project's task tracker.

**This skill never edits context documentation and never touches the task tracker.** The split is a separation of concerns: extracting knowledge from a source and deciding where it belongs (task or context) is one job; applying it to its destination is another. Before handing off, give the user a short summary of what is about to happen — "this is what we're about to do" — as the natural close of the conversation, not a heavyweight review gate.

## Step 1 — Ground yourself in the project

Before analysing anything, find and read the project's AI context — the "advanced README" that holds durable knowledge. Look for the usual entry points: `AGENTS.md`, `CLAUDE.md`, `README.md`, a `docs/` or `context/` directory, or whatever the repo's own conventions point to. From it, learn at minimum:

- the project's purpose, objectives, and domain vocabulary;
- the tech stack and key architectural decisions;
- **where tasks are tracked** (JIRA, GitHub Issues, Linear, Trello, ...);
- any norms for documentation or task writing.

You cannot triage well without this baseline: relevance is defined relative to what the project already knows and cares about.

If no AI context exists, say so plainly. You may still triage the input, but flag that placement of knowledge will be unreliable and recommend establishing an AI context first. In an interactive session, ask whether to continue anyway; in a batch run, continue but record the missing context as the first open question in the proposal.

## Step 2 — Gather the input

This skill works conversationally: a person is present to answer questions, whether the input is a live brainstorm or a transcript brought in for processing.

**Brainstorming.** Act as a facilitator: trade questions back and forth, test ideas against the existing context, and keep going until a coherent set of requirements and knowledge has been surfaced *and agreed*. Don't rush to conclusions — the conversation is the work. Summarise what has been agreed at natural checkpoints so the user can correct you early.

**Transcripts.** One or more meeting transcripts may be supplied:

- **inline** — text pasted into the conversation;
- **as files** — read them from disk;
- **as links** — before doing anything else, check you actually have a tool that can access the link (e.g. a Granola MCP server for Granola transcripts, an authenticated fetch for a private doc). If no suitable tool or permission is available, stop and tell the user exactly what is missing — never guess at a transcript's content.

With multiple transcripts, process them all and keep per-source provenance: sources can disagree, and the user will want to know who said what. After reading them, continue conversationally — raise gaps and conflicts with the user before settling your findings.

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

Ask the user about all of it. Group related questions together rather than dripping them one at a time, and offer your best-guess interpretation alongside each question so the user can simply confirm. Never invent answers, and never leave a conflict silently unresolved.

## Step 5 — Write the proposal

Write the proposal **outside the repo** — the pipeline must leave no footprint in the host project, so never create working files or gitignore entries inside it. Prefer the coding agent's own staging area: if your harness provides a scratchpad or temporary-files directory for the session, put the proposal there. Only when no such area exists, fall back to:

```
/tmp/winnow/<repo-folder-name>-<hash>/proposals/YYYY-MM-DD-<topic-slug>.md
```

where `<hash>` is the first 8 hex characters of the SHA-256 of the repo root's absolute path (`printf '%s' "<abs repo root>" | shasum -a 256 | cut -c1-8`). The hash keeps two checkouts with the same folder name apart; the formula is fixed so the other skills in the pipeline can find the fallback directory without being told.

The proposal is **short-lived internal working state, not a project artefact** — plumbing between the skills, not a deliverable. The user doesn't need to know where it is or what it looks like, any more than a program reports which memory address holds a variable; what the user sees is your summary in the chat. It exists for the duration of a processing run — minutes, maybe hours — and is deleted once the pipeline is done with it. If the OS cleans `/tmp` before then, nothing durable is lost — re-run this skill from the original input.

There is no prescribed format. Structure the file however you like, as long as a separate skill invocation can unambiguously extract:

- the **context updates** — each piece of knowledge written out in full, with its intended target document if known;
- the **tasks** — each with its business goal, the work itself, what done looks like, and any dependency on another task in the same proposal;
- the **sources** each item came from.

## Step 6 — Hand off

Present your findings in the chat: a short summary, then the proposed context updates, the candidate tasks, and what you discarded. Iterate in conversation until the user has decided what to do with each piece.

Then point at the next step: run **update-context** for approved context updates and **create-tasks** for approved tasks. Do not perform those steps yourself, even if asked to "just do it all" — invoke the corresponding skill so its safeguards apply.
