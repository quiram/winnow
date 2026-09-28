# AGENTS.md

The index of winnow's context. Each entry below says what that document holds — load only the ones the task needs, and file new knowledge where this table says it goes.

| Document | What belongs in it |
| --- | --- |
| [ai-context/objectives.md](ai-context/objectives.md) | What winnow is for and the properties it is trying to hold: what it must be, what it refuses to do, what "done well" means. |
| [ai-context/glossary.md](ai-context/glossary.md) | Terms the skills use throughout and define nowhere else. |
| [ai-context/task-tracking.md](ai-context/task-tracking.md) | Which tracker holds work on winnow, how to reach it, and any ticket conventions. |
| [ai-context/ways-of-working.md](ai-context/ways-of-working.md) | Conventions for changing this repo: documentation, commits, releases. |
| [README.md](README.md) | The user-facing surface: what winnow is, what each public skill does, what a consuming repo must provide, how to install it. |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Everything needed to change winnow's code: repo layout, architectural decisions and their reasoning, the release process. |
| `skills/*/SKILL.md` | A single skill's own behaviour and rules, which live there and nowhere else. |

There is no deeper structure under `ai-context/`, and none is needed until a document exists that no entry above can hold.
