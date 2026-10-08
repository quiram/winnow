---
name: recommend-model
description: >-
  Recommend which model to use for a piece of work, balancing capability
  against cost: not the most powerful model by default, and not an
  under-powered one for genuinely hard work. Takes a brief (ticket text plus
  what is known about the code it touches) and returns a recommendation with a
  rationale tied to that task. Use when asked which model to use for a task,
  or when start-task needs a recommendation.
---

# Recommend model

Judging how hard a task is needs the task in front of you, so this skill works from a **brief**, not from a ticket number: the task's description and acceptance criteria, plus whatever is known about the code it touches. `start-task` writes that brief after reading the ticket and skimming the code; a user can also hand one over directly. If the brief is too thin to judge ("fix the bug"), ask for what is missing rather than guessing.

By default the skill only recommends, and the user switches models with whatever their harness provides. If the user has said the choice is the agent's to make ("pick the model yourself", "no need to ask"), or the project's context says so, the skill goes on to select the model itself, wherever the harness gives it a way to (Step 6).

## Step 1 — Know the project's own guidance

Read the project's AI context for model guidance: a table of models, cost constraints, areas where the cost of an error is high. Where the project has its own guidance, it overrides the tiers below.

If the project gives **no** guidance and the harness has an automatic mode that routes each request to a suitable model, recommend that mode and stop there: it already does this skill's job, request by request, and needs no tier mapping. Say that this is why you are recommending it. If the harness has no such mode, carry on to the assessment.

## Step 2 — Assess the task

Weigh these signals, using the brief and the code, not the ticket's title alone:

- **Ambiguity** — are the requirements and the right design clear, or must they be worked out?
- **Reach** — one file following an existing pattern, or several systems with non-obvious interactions?
- **Diagnosability** — for a bug, is there a clear repro, or is finding the cause the real work?
- **Cost of error** — payments, data integrity, security, migrations, anything hard to undo.
- **Kind of work** — engineering, or primarily creative writing (copy, brand voice, descriptions)?

## Step 3 — Pick a tier

| Tier | Reach for it when... |
|---|---|
| **Lightweight** | The task is mechanical and low-ambiguity: renames, small copy edits, simple config changes, straightforward CRUD that follows an existing pattern exactly. |
| **Standard** | The default. Most feature work, bug fixes and refactors: multi-file changes and design trade-offs that do not need the strongest reasoning available. |
| **Frontier** | Real architectural ambiguity, several systems interacting in non-obvious ways, a tricky bug with no clear repro, or a high cost of getting it wrong. |
| **Creative** | The work is primarily writing (marketing copy, brand-voice text, descriptions) rather than engineering. Use only if the host offers a model chosen for that; otherwise fold into Standard or Frontier by how much the quality matters. |

## Step 4 — Map the tier to a model that is actually available

Tiers are vendor-neutral; the recommendation must name something the user can actually select. Take the available models from the project's context, or from what the harness reports about itself. If neither tells you, **ask the user what models they can choose from** and map the tier onto those. Do not recite a vendor's lineup from memory as if it were the user's choices. Where the offering has fewer tiers than the table, pick the nearest and say so.

## Step 5 — Present

Ask the user things through the harness's structured question facility if it has one, and in plain text otherwise.


Give one recommendation: the model, the tier, and a one-line rationale tied to this specific task, not to the generic table. Mention a close runner-up only if the call is genuinely tight.

## Step 6 — Confirm, or apply

- **Choice not delegated** (the default): let the user confirm or choose differently, and leave the switching to them.
- **Choice delegated:** don't ask. Select the model with whatever mechanism the harness exposes to the agent, then say in one line which model you selected and why, so the user can still override. Delegation covers the model choice only; it does not extend to anything else the user is asked to confirm.
- **Delegated, but the harness gives the agent no way to switch** (some only let the user change the session's model): say so, give the recommendation, and carry on. Never pretend a switch happened.

Delegation holds for the task at hand. Don't write it into the project's context or treat it as standing for later tasks unless the user asks you to record it.
