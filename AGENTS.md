# AGENTS.md

Orientation for anyone — person or agent — working on winnow itself. It says what the project is, where knowledge lives, and the conventions that hold; the detail sits in the documents it points at, so nobody loads more than the task needs.

To *use* winnow, start at [README.md](README.md). To change its code, read [CONTRIBUTING.md](CONTRIBUTING.md) — it carries the repo layout, the public/private skill split, the cross-skill engine dependency, and the release process.

## Where tasks are tracked

GitHub Issues on [quiram/winnow](https://github.com/quiram/winnow/issues), reached with the `gh` CLI.

No ticket conventions are recorded, so create-tasks' defaults apply: business goal first, dedupe against existing tickets, one goal per ticket, independent tickets wherever possible.

## The doc map

Four homes, each with its own audience. New knowledge goes where its audience is:

| Where | What belongs there |
| --- | --- |
| `ai-context/objectives.md` | What winnow is for and the properties it is trying to hold. |
| `ai-context/glossary.md` | Terms the skills use throughout and define nowhere else. |
| `README.md` | What winnow is, what each public skill does, what a consuming repo must provide, how to install it. The user-facing surface. |
| `CONTRIBUTING.md` | Everything needed to change winnow's code: layout, architectural decisions and their reasoning, the release process. |
| `AGENTS.md` (this file) | Orientation, vocabulary, tracker, conventions, and the routing rule itself. It points rather than repeats. |
| `skills/*/SKILL.md` | A skill's own behaviour and rules, which live there and nowhere else. |

So: something a *user* needs → README. Something a *contributor* needs → CONTRIBUTING. Something one *skill* does → that SKILL.md. A term, convention or decision spanning them → here.

There is no `docs/` tree, and none is needed until a document exists that no home above can hold.

## Conventions

- **Public skills are documented in README, private parts only in CONTRIBUTING** — and the package description in `apm.yml` names no private part either, because both document how to use winnow rather than how it works.
- **Releases go through the repo-local `release` skill** at `.claude/skills/release/SKILL.md`, which is not part of the package. Versions follow semver and are never picked on the user's behalf.
- **Commits are small and single-purpose** — one concern each, never a single sweep at the end of a piece of work.
