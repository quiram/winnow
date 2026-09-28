# AGENTS.md

Orientation for anyone — person or agent — working on winnow itself. It says what the project is, where knowledge lives, and the conventions that hold; the detail sits in the documents it points at, so nobody loads more than the task needs.

To *use* winnow, start at [README.md](README.md). To change its code, read [CONTRIBUTING.md](CONTRIBUTING.md) — it carries the repo layout, the public/private skill split, the cross-skill engine dependency, and the release process.

## The doc map

Four homes, each with its own audience. New knowledge goes where its audience is:

| Where | What belongs there |
| --- | --- |
| `ai-context/objectives.md` | What winnow is for and the properties it is trying to hold. |
| `ai-context/glossary.md` | Terms the skills use throughout and define nowhere else. |
| `ai-context/task-tracking.md` | Which tracker holds work on winnow, how to reach it, and any ticket conventions. |
| `ai-context/ways-of-working.md` | Conventions for changing this repo: documentation, commits, releases. |
| `README.md` | What winnow is, what each public skill does, what a consuming repo must provide, how to install it. The user-facing surface. |
| `CONTRIBUTING.md` | Everything needed to change winnow's code: layout, architectural decisions and their reasoning, the release process. |
| `AGENTS.md` (this file) | Orientation, vocabulary, tracker, conventions, and the routing rule itself. It points rather than repeats. |
| `skills/*/SKILL.md` | A skill's own behaviour and rules, which live there and nowhere else. |

So: something a *user* needs → README. Something a *contributor* needs → CONTRIBUTING. Something one *skill* does → that SKILL.md. A term, convention or decision spanning them → here.

There is no `docs/` tree, and none is needed until a document exists that no home above can hold.

