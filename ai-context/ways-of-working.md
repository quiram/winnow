# Ways of working

## Documentation

Public skills are documented in the README; private parts only in CONTRIBUTING. The package description in `apm.yml` names no private part either, because both it and the README document how to *use* winnow rather than how it works.

## Commits

Small and single-purpose — one concern each, never a single sweep at the end of a piece of work.

## Releases

Releases go through the repo-local `release` skill at `.claude/skills/release/SKILL.md`, which is not part of the winnow package and doubles as manual step-by-step instructions. Versions follow semver and are never picked on the user's behalf.
