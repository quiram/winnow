# Glossary

Terms winnow's skills use throughout and define nowhere else.

**winnow** — both the package and the skill at its centre. The package is the whole set of skills; the skill is the one that does the winnowing, distilling a source into a proposal. Which is meant is nearly always clear from the sentence — a package doesn't triage a transcript — and where it isn't, write "the winnow skill" or "the winnow package" rather than relying on markup. The shared name is deliberate: the skill is the pipeline's one door in, so knowing that single name is enough to operate it — see [objectives](objectives.md).

**AI context** — a project's durable documentation: the "advanced README" that tells agents how to work on it. winnow's skills read it to ground their judgements and write approved knowledge back into it.

**Doc map**, aka the **document index** — the rule saying which kind of knowledge belongs in which document. It may be explicit meta-documentation or implicit in a context's structure and cross-references. Without one, `update-context` refuses to guess. This repo's doc map is [AGENTS.md](../AGENTS.md).

**Proposal** — the short-lived handoff file between `winnow` and the skills that apply its output. Kept outside the consuming repo and deleted once applied. Plumbing, never a deliverable.

**The three buckets** — how `winnow` sorts everything it hears: *irrelevant* (discarded), *durable knowledge* (to the AI context), *actionable work* (to the tracker).

**Host repo / consuming repo** — the project winnow runs *against*, as distinct from this one.

**Public / private skill** — public skills are meant to be invoked by name and are documented in the README; private ones are internal parts of a public skill and are documented only in CONTRIBUTING.
