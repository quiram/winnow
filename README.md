<p align="center">
  <img src="assets/logo.svg" alt="winnow logo — a winnowing basket separating grain from chaff" width="170"/>
</p>

# winnow

Agent skills for managing a software product's requirements and roadmap. They distil brainstorming conversations and meeting transcripts into two kinds of output — durable project knowledge and tracker-ready tasks — while keeping a human in the loop before anything permanent changes.

The package is agent-agnostic: it is distributed with [APM (Agent Package Manager)](https://microsoft.github.io/apm/), so the same skills deploy to Claude Code, GitHub Copilot, Cursor, Codex, and any other harness APM supports. This repo is both the package and the marketplace that serves it.

## Why "winnow"?

Winnowing is one of farming's oldest techniques: after threshing, the harvest is tossed into the air from a broad, shallow basket — a *winnow*, or winnowing fan — so the wind carries off the light chaff while the heavy grain falls back into the basket. Same crop goes up; only what nourishes comes down.

That is precisely what these skills do to a conversation. A meeting transcript or a brainstorm gets tossed into the air, scrutiny blows the small talk and noise away, and two kinds of grain fall back to be kept: knowledge worth recording and work worth doing. The logo is a winnowing basket mid-toss.

## The pipeline

Three skills, deliberately separated so a human checkpoint sits between analysis and application:

```mermaid
flowchart LR
    A[Conversation /<br/>transcripts] --> P[process-requirements]
    P --> F[Proposal file<br/><i>short-lived, outside the repo</i>]
    F -->|approved knowledge| C[update-context]
    F -->|approved tasks| T[create-tasks]
    C --> D[AI context docs]
    T --> K[Task tracker]
```

### process-requirements

Works conversationally, whether the input is a live brainstorm or one or more meeting transcripts (inline, as files, or as links, provided a tool with access exists) worked through with the user. It triages everything into three buckets:

- **irrelevant** — discarded; the skill lists what it dropped when presenting its findings, and keeps no record beyond that;
- **durable knowledge** — things anyone working on the project later would need, destined for the AI context;
- **actionable work** — concrete tasks with a done-state and a why, destined for the tracker.

It actively hunts gaps, conflicts, and ambiguity, and asks the user rather than inventing answers. Its output is a **proposal file** — never a direct edit to docs or tracker.

### update-context

Applies a proposal's approved knowledge to the project's AI context documentation. It first checks whether the project has its own documentation-management machinery — instructions, skills, plugins, or scripts — and delegates to that where it exists, respecting its workflow and checkpoints. Failing that, it requires the project to define which knowledge belongs in which document (a *doc map*); if none exists it halts and asks the user to cancel or define one. Its writing rules keep documents from decaying under repeated updates: integrate rather than append, match the document's voice, describe present state only, and re-read the whole document after editing.

### create-tasks

Turns a proposal's approved tasks into tickets. It discovers the tracker and its tooling (CLI, MCP server, API credentials) from the project's own documentation, probes access non-destructively, and stops with a precise report if anything is missing. If more than one tracker is plausible, it asks — it never assumes. Ticket defaults, overridable by project conventions: business goal first, dedupe against existing tickets, check for conflicts, one goal per ticket (splits confirmed with the user), and independent tickets wherever possible with tracker-native dependency links otherwise.

## The proposal file

The handoff between skills is a structured markdown file kept **outside the consuming repo**, so the pipeline leaves no footprint in the host project — no working folders, no gitignore entries. Proposals live in the coding agent's own scratchpad/staging area when the harness provides one, falling back to `/tmp/winnow/<repo-folder-name>-<hash>/proposals/` otherwise (the hash is derived from the repo's absolute path so every skill in the pipeline finds the same directory). They are **short-lived**: a proposal exists for the duration of a processing run — minutes, maybe hours — and the skills delete it once every item reaches a terminal state (applied, created, or rejected). The durable records are the AI context and the tracker, not the proposal.

## What a consuming repo must provide

The skills assume they run inside a mono/meta-repo that carries the project's durable knowledge:

- **An AI context** — an "advanced README" (e.g. `AGENTS.md`, `CLAUDE.md`, `docs/`) covering the project's purpose, domain, tech stack, and conventions. Its goal: people and AI alike know how to work on the project after reading it.
- **A doc map** — an indication of which kind of knowledge belongs in which document. This may be explicit meta-documentation, or implicit in the structure of the README, `CLAUDE.md`, `AGENTS.md`, or similar. Without either, update-context refuses to guess.
- **A named task tracker** — the context must say where tasks live and, ideally, how to interact with it (cheatsheets, templates, conventions). The skills are fully tracker-agnostic; the project's docs are the only source of tracker knowledge.

Where any of these is missing, the skills surface the gap instead of working around it — and offer to record the answer so the gap closes permanently.

## Installation

### With APM

Directly as a dependency in your project's `apm.yml`:

```yaml
dependencies:
  apm:
    - quiram/winnow
```

Or via the marketplace this repo publishes:

```bash
apm marketplace add quiram/winnow
apm install winnow@winnow
apm install
```

### As a Claude Code plugin

The generated `.claude-plugin/marketplace.json` makes this repo a Claude Code marketplace too:

```
/plugin marketplace add quiram/winnow
/plugin install winnow@winnow
```

## Working on winnow itself

See [CONTRIBUTING.md](CONTRIBUTING.md) for the repo layout and release process.
