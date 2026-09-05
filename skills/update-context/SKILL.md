---
name: update-context
description: >-
  Apply approved knowledge updates from a requirements proposal to the
  project's AI context documentation, keeping every document cohesive,
  human-sounding, and describing present state only. Use after
  process-requirements has produced approved context updates, or when asked to
  fold agreed knowledge, decisions or conventions into the project's context
  docs. Requires the project to define which knowledge belongs in which
  document; halts and asks if it doesn't.
---

# Update context

You are part of a three-skill pipeline: **process-requirements** distils input into a proposal; then this skill applies the proposal's context updates to the project's AI context documentation, while **create-tasks** handles the proposal's tasks. The two application skills are peers — they run independently, in any order. This skill never creates or edits tickets.

The AI context exists so that *people and AI alike know how to work on this project after reading it*. Every edit you make is judged against that goal.

## Step 1 — Load the work

Operate from a proposal file written by process-requirements. Proposals live outside the repo: in the coding agent's scratchpad/staging area when the harness provides one, otherwise in `/tmp/winnow/<repo-folder-name>-<hash>/proposals/`, where `<hash>` is the first 8 hex characters of the SHA-256 of the repo root's absolute path (`printf '%s' "<abs repo root>" | shasum -a 256 | cut -c1-8`). If the user points you at one, use it; otherwise use the most recent proposal with unapplied context updates, confirming your pick with the user.

If the user instead hands you facts directly in conversation ("record that we've chosen Kafka"), just work from the conversation — the user's request is the approval. Don't create a proposal file only to delete it.

Everything in the proposal has already been agreed with the user — apply all of it. There are no statuses to check: if something wasn't approved, it isn't in the file.

## Step 2 — Check for the project's own documentation machinery

The host project may already have its own way of managing documentation: instructions in the AI context, a dedicated skill, plugin or command available in your environment, or scripts in the repo (for instance a staging-and-promote workflow with its own review checkpoints). Look for such machinery before doing the work yourself — check the AI context entry point for documentation-management instructions, and scan the skills, plugins and commands available to you for one whose purpose is maintaining this project's documentation.

If you find one, use it: hand the approved items to that mechanism and respect its workflow, including any checkpoints it imposes, rather than editing documents directly. The project's machinery and norms override this skill's default procedure. Tell the user which mechanism you used.

Only when nothing local exists, carry on with the steps below.

## Step 3 — Find the doc map

The project is expected to indicate which kind of knowledge goes in which document (a doc map). This need not be a dedicated meta-document: it may be explicit meta-documentation, or implicit in the structure and instructions of `README.md`, `CLAUDE.md`, `AGENTS.md`, or a similar entry point — a context file whose sections and cross-references make clear where each kind of knowledge lives counts as a doc map. Look in the AI context entry points, or wherever the project's conventions point.

**If no doc map exists, propose one.** Do not guess placement item-by-item, and do not ask the user to invent a structure from a blank page — that is exactly how context rots into an incoherent pile of sentences, or never gets structured at all. Instead, tell the user this is a structural gap in how the project records knowledge, and bring a concrete default structure for them to approve, amend, or reject:

- Documentation serves **both humans and AI agents**. That dual audience is the reason for the structure, not an afterthought.
- `README.md` at the repo root is the starting point: it says what the project is and how to get started, then points into `docs/`. It does not accumulate content that belongs in `docs/`.
- Each **domain** of knowledge gets its own subfolder under `docs/` (e.g. product/vision, technology, design) — adapt the folder names to the project's actual domains rather than proposing empty folders that match this example.
- Every level carries its **own index** — a README naming what each file and subfolder below it contains, so a reader or agent can find the right document without opening several wrong ones first.
- Indexes exist so agents can load context **selectively** rather than reading everything and filling the context window.

Present this as a starting point tuned to the project at hand, not a rigid template. The user may cancel instead — leaving the proposal untouched for later — but explicit approval is still required before anything is written. Once agreed, record the doc map into the AI context as your first update, then continue with the rest.

## Step 4 — Place each item

For each approved item, choose the target document using the doc map. If the proposal already names a target, verify it against the map rather than trusting it blindly.

If placement is genuinely ambiguous, ask the user.

When new knowledge contradicts what a document currently says, remember that documentation shows **present state**: a newer decision supersedes the old text, so rewrite it. But if you cannot tell which statement reflects current truth — the proposal might be from an old meeting — flag the conflict to the user instead of guessing.

## Step 5 — Write like the document's author

This is the heart of the skill. Repeated small updates are how documents decay into incoherent collections of bolted-on sentences; your job is to prevent that. The project's own documented writing norms always override these defaults:

- **Integrate, never append.** Do not tack sentences onto the end of a section or bullet onto the end of a list because it is easy. Find where the knowledge belongs in the document's existing structure and rewrite the surrounding passage so it reads as if written in one sitting. If the structure has no natural home for it, adjust the structure deliberately (and check that against the doc map).
- **Match the document's voice** — its tense, person, terminology, heading style, level of formality, and formatting conventions. A reader must not be able to spot where your edit starts and ends.
- **Present state only.** Remove statements your update supersedes. No changelog prose — "previously we used X", "as of the September meeting" — history lives in version control, not in the context. The one exception: keep the *reason* something was abandoned when that reason protects future decisions ("we don't use X because it cannot Y"), stated as a present-tense fact.
- **One idea, one place.** If the update duplicates something said elsewhere in the corpus, consolidate rather than repeat, or link if the project's conventions support it.
- **Calibrate headings and restatement to actual complexity, not to how many concerns you can name.** A heading must be a declarative noun phrase in the document's existing style — never phrased as a question or FAQ entry ("Which products sell online vs offline", "How each channel works"); question-style headings break the document into disconnected Q&A instead of flowing prose. A new heading level is justified only when a section has genuinely grown too long or complex to scan without one — splitting a handful of lines into their own sub-heading because they're "a separate concern" is escalation the content doesn't need; a plain topic sentence introducing the point does the same job without adding structure. Similarly, don't restate a fact the reader just read a few lines above merely because it's newly relevant to the passage you're editing — repetition is only earned when omitting it risks the reader losing the thread (a long section, or a fact from a distant part of the document), not by default and not never. In all three cases, judge by rereading the whole surrounding passage as one piece, not by whether the new content technically deserves its own label.

After editing a document, **re-read it in full**. Check that it flows, that headings still describe their sections, that nothing is now stated twice or contradicted, and that a newcomer reading only this document would come away with a correct picture. Fix any incoherence your edit introduced, but resist unrelated rewrites — keep the diff explainable.

## Step 6 — Wrap up

- Remove the context updates you have applied from the proposal (along with any item the user withdrew during the run). If nothing remains in the file, delete it: it is intermediate working state, not a record. If its tasks are still to be created, leave it for create-tasks.
- Report back per document: what changed, and which proposal items drove it. Quote or summarise the edits so the user can review without opening every file.
