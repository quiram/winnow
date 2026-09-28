---
name: winnow-setup-tracker
description: >-
  The tracker part of setup-winnow: establish which task tracker a project uses
  and confirm winnow can actually talk to it — identify the tracker from the AI
  context, ask when the documentation names none or more than one, probe the
  CLI, MCP server or API credentials non-destructively, and record the answer
  so the question never recurs. Use when setup-winnow delegates the tracker
  here, or when create-tasks or winnow need a tracker they cannot find. Someone
  asking to prepare a project or machine for winnow wants setup-winnow, which
  covers this and every other prerequisite.
---

# Set up winnow's task tracker

You settle two things: **which** tracker this project uses, and whether winnow can actually reach it. Both are cheap to establish now and expensive to discover late — create-tasks needs them at the moment tickets are ready to be created, by which point the user has already agreed every one of them in conversation.

You are the tracker part of **setup-winnow**, which checks winnow's other prerequisites and delegates here; create-tasks and winnow invoke you directly when they need a tracker they cannot find. You never create, edit or close a ticket — you confirm that create-tasks could.

## Step 1 — Identify the tracker

Read the project's AI context to learn which task tracker it uses. Rules of discovery:

- If the documentation clearly names one tracker, use it.
- If **more than one tracker** is available or mentioned (e.g. the project has both GitHub Issues and JIRA in reach) **and the documentation isn't explicit about which one should be used**, **ask the user which one — never assume**.
- If no tracker is documented at all, ask the user. A repo with a GitHub remote is a hint, not an answer: plenty of projects host code on GitHub and track work in JIRA or Linear.

## Step 2 — Verify the tooling, non-destructively

Work out how winnow would talk to the tracker — a CLI (`gh`, `jira`, ...), an MCP server, or an API with credentials — from the project docs and the tools available to you. Then probe it **read-only**: check auth status, or list or read a single existing item. Never create a test ticket; a tracker is a shared, visible place and a probe must leave no trace.

If anything is missing — the CLI isn't installed, the MCP server isn't configured, an API key or authentication is absent, permissions are insufficient — say exactly what is needed: the tool, the configuration, the credential, and where it goes. Every fix is the user's action on their machine or account. After each fix, probe again.

Read access proving out does not prove write access, and you are not going to test writing. Say which one you confirmed, so nobody reads more into it than you checked.

## Step 3 — Record the answer

A tracker the user had to name once is knowledge the project should carry, and recording it is what stops every later run from repeating this conversation. Once it is settled, hand it to **update-context** to record in the AI context: the name of the tracker, and how winnow talks to it.

If the context already said both and you only confirmed them, there is nothing to record. Say so and move on — a re-run of this skill on a settled project should be a read and a probe, not an edit.

While you are there, ask whether the project has conventions for writing tickets that aren't yet written down: a template, labels, components, naming, workflow states, a cheatsheet for the tracker's tooling. create-tasks reads those and lets them override its own defaults, so anything the user can state now is worth recording alongside the tracker. Don't press if they have none — defaults exist for exactly that case.

## Step 4 — Report

Say which tracker this project uses, how winnow reaches it, and what you confirmed — read access, and whether the context now records the answer. If anything is still missing, name it precisely and whose action it needs.

Report on the tracker only. When setup-winnow delegated to you, it owns the overall verdict; when create-tasks did, hand back the tracker and the interaction method so it can carry on.
