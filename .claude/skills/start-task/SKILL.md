---
name: start-task
description: >-
  One-off setup for beginning new implementation work: identify the task (from
  a ticket in the project's tracker, or from a requirement given inline), open
  a fresh branch from an up-to-date default branch, and get a model
  recommendation, following the project's own conventions and confirming any
  default it has to assume. Use when the user says things like "start a task",
  "pick up a ticket", "begin work on issue #N", "I need you to change X so
  that...", or otherwise signals they are about to start new work.
---

# Start task

One-off setup that runs once, before implementation begins. It ends by handing over to the project's own implementation workflow; it never starts writing code itself.

## When to use

The user signals the start of new implementation work: "start a task", "pick up ticket #N", "let's work on issue #N", "begin work on X", or simply describes what they want changed. Not for mid-task branch corrections.

## Asking the user

Whenever this skill needs something from the user (a default to confirm, a missing detail, a choice), use the harness's structured question facility if it has one, and plain text in the conversation if not. Batch related questions into one ask where you can.

## Step 0 — Learn the project's conventions

Read the project's AI context (`AGENTS.md`, `CLAUDE.md`, and the documents they point to) for four things:

1. **The task tracker**, if there is one, and how to reach it (CLI, MCP server, API).
2. **Branch naming** and any rules about where branches start from.
3. **Worktree or isolation practice** — whether work happens in worktrees, and where they live.
4. **The implementation workflow** — the process that takes over once setup is done (planning, approval, quality checks, commits).

Anything the context answers, follow. Anything it does not answer, you will need a **default** — and a default is never simply assumed. When you reach the step that needs one, tell the user what the context is silent about, state the default you propose, and wait for them to confirm or replace it.

The defaults, for reference:

| Gap | Default to propose |
|---|---|
| Tracker | None needed if the task was given inline. If the user refers to a ticket but the context names no tracker, ask which tracker it is and how to reach it. |
| Branch name | `type/<ticket#>-<short-description>` (e.g. `fix/123-login-redirect`), or `type/<short-description>` with no ticket. `type` is one of `feat`, `fix`, `chore`, `docs`, `refactor`. |
| Base branch | The remote's default branch. |
| Isolation | A worktree if the harness offers one; otherwise a plain branch in the current checkout. |
| Implementation workflow | Propose a numbered plan and wait for explicit approval before writing code. |

## Step 1 — Identify the task

The task arrives in one of two forms; either is enough.

- **A ticket.** If a ticket was named (or can be inferred from the request), read it through the project's tracker. Take the description, acceptance criteria and any linked PR or branch as inputs to everything that follows, not optional context. If the tracker cannot be reached, stop and report precisely what failed.
- **An inline requirement.** The user may simply describe the work ("change the login screen so that..."). That is the task; no tracker is needed. Restate it in a sentence or two so any misunderstanding surfaces now, and ask about anything that is ambiguous.

If neither was given, ask what the task is before continuing. Don't guess.

## Step 2 — Fresh branch from an up-to-date base

Always start from the current tip of the base branch, never from whatever branch happens to be checked out. This comes before the model recommendation so that the code assessed there is the code the work will actually start from, not a stale checkout.

1. **Check the starting state.** `git status --porcelain` must be clean enough to leave behind. If there are uncommitted changes, tell the user and ask what to do; never stash, discard or carry them over silently.
2. **Find and sync the base.** Find the default branch (`git symbolic-ref --short refs/remotes/origin/HEAD`) unless the context names one, then `git fetch origin`. Create the branch from `origin/<base>`, not from a possibly stale local copy.
3. **Create the branch** with the confirmed name, in an isolated worktree if that is the practice in play. If the harness has a worktree facility, prefer it; otherwise use `git worktree add -b <branch> <path> origin/<base>`.
   - Anchor the worktree path at the **main repo root** (absolute path), never relative to the current directory: if you are already inside a worktree, a relative path nests the new one inside it, and removing the outer worktree later orphans the inner one. This applies whether you create the worktree yourself or the harness does.
4. **Verify.** Run `git branch --show-current` and confirm it is the intended name. If the tooling named it differently, rename it with `git branch -m <intended-name>` before doing anything else.
5. **Submodules.** If the repo has any (`.gitmodules` exists), run `git submodule update --init --recursive`. A fresh worktree does not populate them, and rules or tooling that import from a submodule fail silently without it. Do this regardless of whether the directories look populated.

## Step 3 — Recommend a model

Now, on the fresh branch, skim the code areas the task touches, then invoke **recommend-model** with a brief: the task (ticket text or the inline requirement) plus what you found there (how many areas, how well-trodden the patterns, anything risky). If the user has already delegated the model choice (in this request or in the project's context), say so in the brief so recommend-model selects the model without asking; otherwise present its recommendation and let the user confirm or override before continuing, switching models themselves with whatever their harness provides.

If recommend-model cannot be found, say so and proceed: the model choice must never block starting the work.

## Step 4 — Hand off

Report where things stand: the task, the branch and worktree path if any, and the model. Then continue into the implementation workflow found in Step 0. If the project documents none, read the relevant source, produce a numbered implementation plan, and wait for explicit approval before writing any code.
