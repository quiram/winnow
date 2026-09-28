# Objectives

winnow exists so that the knowledge and the work buried in a conversation stop being lost. A brainstorm, a meeting, a voice note — each carries things worth keeping and things worth doing, and both normally evaporate. winnow's job is to separate them out and land each one where it belongs: durable knowledge in the project's AI context, actionable work in its task tracker.

What it is trying to be:

- **Conversational, never autonomous.** Nothing permanent changes until the user has agreed it. The skills propose; the user decides.
- **Agent-agnostic.** The same skills must work on Claude Code, Copilot, Cursor, Codex and whatever comes next, so nothing may depend on one assistant's mechanisms. It ships through [APM](https://microsoft.github.io/apm/), and this repo is both the package and the marketplace that serves it.
- **Tracker-agnostic and context-agnostic.** winnow brings no opinion about where a project's knowledge or tickets live; it reads that from the project itself and refuses to guess when the project has not said.
- **Footprint-free in the host project.** The pipeline's intermediate state lives outside the consuming repo, so using winnow adds no working folders and no gitignore entries to a project.
- **One door in.** The `winnow` skill is the pipeline's entry point and invokes whatever it needs — transcription for audio input, the setup parts for a missing context or tracker, `update-context` and `create-tasks` to apply what was agreed — so knowing that one name is enough to run the pipeline end to end. Outside it are only the skills that start somewhere else: `listen-to-meeting` begins at a live meeting and feeds its transcript back in, and `setup-winnow` prepares a machine in one deliberate pass rather than piecemeal.
- **Honest about gaps.** Where a prerequisite is missing, the skills surface it rather than inventing a plausible answer, because everything downstream trusts what the context says.
