# AGENTS.md

The index of winnow's context. Each entry below says what that document holds — load only the ones the task needs, and file new knowledge where this table says it goes.

| Document | What belongs in it |
| --- | --- |
| [ai-context/objectives.md](ai-context/objectives.md) | What winnow is for and the properties it is trying to hold: what it must be, what it refuses to do, what "done well" means. |
| [ai-context/glossary.md](ai-context/glossary.md) | Terms the skills use throughout and define nowhere else. |
| [ai-context/task-tracking.md](ai-context/task-tracking.md) | Which tracker holds work on winnow, how to reach it, and any ticket conventions. |
| [ai-context/ways-of-working.md](ai-context/ways-of-working.md) | Conventions for changing this repo: commits and releases. |
| [README.md](README.md) | The user-facing surface: what winnow is, what a consuming repo must provide, how to install it. It documents the **public** skills only, and never names a private one. |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Everything needed to change winnow's code: repo layout, architectural decisions and their reasoning, the release process. The **private** skills are documented here and nowhere else. |
| `skills/*/SKILL.md` | A single skill's own behaviour and rules, which live there and nowhere else. |
| `apm.yml` | Package identity, version and the marketplace self-listing. Its package description documents how to *use* winnow, so like the README it names no private skill. |

There is no deeper structure under `ai-context/`, and none is needed until a document exists that no entry above can hold.
