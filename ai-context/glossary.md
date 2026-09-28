# Glossary

Terms winnow's skills use throughout and define nowhere else.

**AI context** — a project's durable documentation: the "advanced README" that tells agents how to work on it. winnow reads it to ground its judgements and writes approved knowledge back into it.

**Doc map**, aka the **document index** — the rule saying which kind of knowledge belongs in which document. It may be explicit meta-documentation or implicit in a context's structure and cross-references. Without one, `update-context` refuses to guess. This repo's doc map is [AGENTS.md](../AGENTS.md).

**Proposal** — the short-lived handoff file between `winnow` and the skills that apply its output. Kept outside the consuming repo and deleted once applied. Plumbing, never a deliverable.

**The three buckets** — how `winnow` sorts everything it hears: *irrelevant* (discarded), *durable knowledge* (to the AI context), *actionable work* (to the tracker).

**Host repo / consuming repo** — the project winnow runs *against*, as distinct from this one.

**Public / private skill** — public skills are meant to be invoked by name and are documented in the README; private ones are internal parts of a public skill and are documented only in CONTRIBUTING.
