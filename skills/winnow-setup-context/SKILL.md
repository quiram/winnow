---
name: winnow-setup-context
description: >-
  The context part of setup-winnow: make a project's AI context fit to receive
  knowledge — establish an AI context where none exists, and a doc map (an
  indication of which kind of knowledge belongs in which document) where the
  context has none, proposing a concrete default structure for the user to
  approve. Use when setup-winnow delegates the AI context here, or when update-
  context finds no doc map and winnow finds no context to ground itself in.
  Someone asking to prepare a project or machine for winnow wants setup-winnow,
  which covers this and every other prerequisite.
---

# Set up winnow's context

You make a project's AI context fit to receive knowledge. Winnow reads that context to ground every judgement it makes and writes durable knowledge back into it, so two things must exist before any of that works: a context, and a **doc map** — an indication of which kind of knowledge belongs in which document. You establish whichever is missing and nothing more. You never file actual knowledge; that is update-context's job.

You are the context part of **setup-winnow**, which checks winnow's other prerequisites and delegates here. The skills that depend on this also invoke you directly when they find it missing — update-context cannot place anything without a doc map, and winnow cannot triage reliably without a context.

The work is the user's to approve. Nothing is written until they agree to it, and "not now" is a valid answer: report the gap and stop.

## Step 1 — Check for the project's own documentation machinery

The host project may already have its own way of managing documentation: instructions in the AI context, a dedicated skill, plugin or command available in your environment, or scripts in the repo. Look for it first — check the AI context entry point for documentation-management instructions, and scan the skills, plugins and commands available to you.

If you find one, the project's structure is that machinery's business, not yours. Say what you found, confirm with the user that it defines where knowledge goes, and stop — imposing a second structure on top of an existing one is how a project ends up with two competing answers to the same question.

## Step 2 — Find the AI context and judge what is missing

Look for the usual entry points: `AGENTS.md`, `CLAUDE.md`, `README.md`, a `docs/` or `context/` directory, or whatever the repo's own conventions point to — the same places winnow looks.

Three outcomes:

- **A context with a doc map.** Nothing to do. Report where both live and stop.
- **A context with no doc map.** Go to Step 4.
- **No context at all.** Go to Step 3, then Step 4.

A doc map need not be a dedicated meta-document. It may be explicit meta-documentation, or implicit in the structure and instructions of an entry point — a context file whose sections and cross-references make clear where each kind of knowledge lives is a doc map. A project that already reads coherently has one; do not tell it to restructure.

## Step 3 — Establish an AI context

Explain what is missing and why it costs the user something: the AI context exists so that *people and AI alike know how to work on this project after reading it*, and without it every later judgement about relevance and placement is a guess.

Propose the minimum entry point at the repo root: `AGENTS.md`, or `README.md` where the project would rather keep one file. It covers the project's purpose and objectives, its domain vocabulary, its tech stack and key architectural decisions, where tasks are tracked, and any conventions that already exist in practice.

Propose `AGENTS.md` rather than an assistant-specific file such as `CLAUDE.md`, even when the user works with one assistant today. It is the convention coding agents share, so the context you establish stays readable by whatever the project uses next — and on Claude Code specifically, adding a `CLAUDE.md` alongside an `AGENTS.md` stops the `AGENTS.md` being read at all by default. Recognising an assistant-specific file the project already has is a different matter: read it as the context it is.

Fill it from what the user actually confirms. Where they don't know yet, leave the subject out and tell them it is still open, rather than writing a plausible-sounding answer: an entry point full of invented facts is worse than no entry point, because everything downstream trusts it.

## Step 4 — Establish the doc map

**Do not guess placement item-by-item, and do not ask the user to invent a structure from a blank page** — that is exactly how context rots into an incoherent pile of sentences, or never gets structured at all. Bring a concrete default for the user to approve, amend, or reject:

- Documentation serves **both humans and AI agents**. That dual audience is the reason for the structure, not an afterthought.
- `README.md` at the repo root is the starting point: it says what the project is and how to get started, then points into `docs/`. It does not accumulate content that belongs in `docs/`.
- Each **domain** of knowledge gets its own subfolder under `docs/` (e.g. product/vision, technology, design) — adapt the folder names to the project's actual domains rather than proposing empty folders that match this example.
- Every level carries its **own index** — a README naming what each file and subfolder below it contains, so a reader or agent can find the right document without opening several wrong ones first.
- Indexes exist so agents can load context **selectively** rather than reading everything and filling the context window.

Present this as a starting point tuned to the project at hand, not a rigid template.

## Step 5 — Record it

Once the user has approved, write the doc map into the AI context itself — it is knowledge about the project, so it belongs where the project's knowledge lives. Write it the way update-context writes: integrate it into the document's existing structure rather than appending a block, match the document's voice, and describe present state only.

Create the folders and indexes the map describes only where they have content to hold. An empty tree of READMEs promising documents that don't exist is noise that every later reader has to work around.

## Step 6 — Report

Say what now exists, where the doc map is recorded, and what a skill reading this project will find. If the user declined part of it, or left subjects open in Step 3, name those precisely — they are the next thing someone will trip over.

Report on the context only. When setup-winnow delegated to you, it owns the overall verdict; when update-context or winnow did, hand back and let them carry on with the work they paused.
