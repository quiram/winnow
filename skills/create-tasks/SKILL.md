---
name: create-tasks
description: >-
  Create well-formed tickets in the project's task tracker from a requirements
  proposal: goal-first, deduplicated, conflict-checked, one goal per ticket,
  independent where possible. Discovers the tracker and its tooling from the
  project's documentation and refuses to guess when they are missing or
  ambiguous. Use after winnow has produced approved candidate tasks, or when
  asked to raise tickets, issues or tasks from agreed requirements.
---

# Create tasks

You are part of a three-skill pipeline: **winnow** distils input into a proposal; then this skill turns the proposal's tasks into tickets in the project's task tracker, while **update-context** handles the proposal's knowledge. The two application skills are peers — they run independently, in any order. This skill never edits the AI context documentation.

## Step 1 — Load the work

Operate from a proposal file written by winnow. Proposals live outside the repo: in the coding agent's scratchpad/staging area when the harness provides one, otherwise in `/tmp/winnow/<repo-folder-name>-<hash>/proposals/`, where `<hash>` is the first 8 hex characters of the SHA-256 of the repo root's absolute path (`printf '%s' "<abs repo root>" | shasum -a 256 | cut -c1-8`). If the user points you at one, use it; otherwise use the most recent proposal with uncreated tasks, confirming your pick with the user.

If the user instead describes tasks directly in conversation, just work from the conversation — the user's request is the approval. Don't create a proposal file only to delete it.

Everything in the proposal has already been agreed with the user — act on all of it. There are no statuses to check: if something wasn't approved, it isn't in the file.

## Step 2 — Get the tracker and a way in

Read the project's AI context for any project-specific instructions on writing tickets: templates, labels, components, naming, workflow states, cheatsheets for the tracker's tooling. Project instructions always override the defaults in this skill.

The same read should tell you **which tracker this project uses and how to reach it**. That answer is recorded in the context precisely so it is settled once and read thereafter: take it and get on with the work. You do not need a separate connectivity probe either — searching the tracker for existing similar tickets, in Step 3, is a read-only interaction that comes before anything is created, so a broken credential surfaces there, in time to stop.

Invoke **winnow-setup-tracker** only when the context cannot answer: it names no tracker, or names more than one without saying which is this project's, or the tooling turns out to be unusable when you first reach for it. What you need back is the tracker and a verified way to talk to it — CLI, MCP server or API credentials, already probed non-destructively. It asks the user where the documentation can't answer, and records the outcome so the next run reads it instead of asking again.

If anything is missing — the CLI isn't installed, the MCP server isn't configured, a credential is absent, permissions are insufficient — **stop**, and relay exactly what is needed. Do not create a partial batch of tickets and fail halfway through discovering this.

## Step 3 — Prepare the tickets

Apply these defaults to every candidate task; the project's own task-creation instructions win wherever they differ.

1. **Begin with the business goal.** Every ticket must answer *why* before *what*. Technical tickets need at least an indirect business goal — reduce risk, increase performance, simplify development, cut costs. If you cannot state a goal for a task, take it back to the user rather than inventing one.

2. **Check for existing similar tickets.** Search the tracker (open tickets, and recently closed ones) before creating each ticket. If a similar one exists, present it and ask the user what to do with the candidate ticket: fold it into the existing ticket by updating that one, drop the candidate and leave the existing ticket as it is, or create the candidate anyway as a separate ticket. Recommend folding it in, since dropping the candidate throws away whatever new detail it carries.

   How to fold it in depends on how the candidate's information relates to the existing ticket. If it complements the ticket, rewrite the existing description (see item 6) so that it reads as if the new information had been known from the start, rather than as an addition tacked on. If it contradicts the ticket, tell the user about the conflict and ask which way to go (see item 3) before changing anything; the description then follows their decision.

   Whichever option is taken, leave a brief comment on the existing ticket recording it: what was merged, what was considered and not adopted, or how a conflict was resolved. The description holds only the current requirement, and the comment keeps the trail of what was weighed. Add these comments as part of the flow; don't ask the user to confirm each one.

3. **Check for conflicts.** Look for existing tickets that the new ones would contradict, duplicate in part, or clash with (e.g. an open ticket building the thing this one removes), including the similar ticket found in item 2. Surface any conflict and resolve it with the user before creating anything.

4. **One goal per ticket.** If a candidate task serves two or more goals, or its goal is too broad to have a crisp done-state, split it into several tickets — and **confirm the split with the user before creating them**. Before drafting each ticket, also scan the proposal's supporting detail/"what's known" text for that task — not just its stated title/goal — for any embedded finding that has its own distinct goal and done-state separate from the task's stated goal. If found, treat it as a missed split: confirm with the user whether it should become its own ticket before proceeding, the same as an explicit second goal would trigger.

5. **Prefer independent tickets.** Write tickets so they can be executed in any order. Where a dependency is genuinely unavoidable, make it explicit: use the tracker's native relations if it has them (JIRA's "blocked by"/"depends on", GitHub's task-list or dependency links, Linear's blocking relations); otherwise state the dependency prominently in the ticket description.

6. **State the present requirement only.** A ticket description states what is required *now*; it must not narrate the ticket's own history. Never write "this ticket previously covered X, that half is dropped" into a body, and avoid dated-decision stamps ("Decision, 4th September 2026: ..."). State the requirement and its rationale in plain present tense. This applies equally to tickets the skill rewrites and to ones it creates fresh — a rescoped ticket's old scope does not belong quoted at the top of the new body.

   When rescoping or otherwise rewriting an existing ticket: rewrite the body to describe only what is now required, then add a **comment** explaining what changed and why. The same goes for a decision that leaves the body untouched (new detail skipped, a conflict resolved): the comment is where it is recorded. Whether this comment can stay brief depends on the tracker: if it keeps a revision history of the description (e.g. an edit log or diff view), a short comment pointing to that history suffices for minor changes, and a fuller explanation is only needed when the change is significant enough to warrant one. If the tracker does not track description history at all, be more verbose in the comment — it is the only record of what changed and why.

   Don't confuse this with present-tense rationale for a *current* constraint, which does belong in the body — "blocked by #123 because the structure must settle first" is a live fact about the work, not history.

   Before finishing, check each body for history framing (phrases like "previously", "used to", "no longer covers", "scope change", or a dated decision stamp). Any hit belongs in a comment instead.

### Default ticket shape

Unless the project defines its own template:

```
<Title: outcome-oriented, one goal>

**Why:** <the business goal this serves, stated as present rationale>

**What:** <the work, and enough context to do it without archaeology — present requirement only, no history of how the ticket got here>

**Done when:** <observable acceptance criteria>

**Out of scope:** <optional — what this deliberately does not cover>

**Depends on:** <optional — only when independence is impossible>
```

Create tickets in dependency order (prerequisites first) so relations can be linked as you go.

## Step 4 — Wrap up

- Remove the tasks you have created from the proposal (along with any item the user withdrew during the run). If nothing remains in the file, delete it: it is intermediate working state, not a record. If its context updates are still to be applied, leave it for update-context.
- Report the created tickets with their links, any skips with reasons, and any dependency relations you set.
