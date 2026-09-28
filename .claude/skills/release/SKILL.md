---
name: release
description: >-
  Release a new version of winnow: bump the version everywhere it lives,
  validate the marketplace, regenerate the packed manifests, then commit, tag
  and push. Local to this repo — not part of the winnow package. Use when asked
  to release, cut, or publish a new version of winnow.
---

# Release winnow

Cut a release of this repo. The version follows semver; if the user hasn't said which version to release, ask — never pick one for them.

## Steps

1. **Preflight.** The working tree must be clean and on `main` with no unpushed
   commits you weren't told about. If anything unexpected is lying around, stop
   and ask.

2. **Work out the version.** Survey what has landed since the last release,
   classify it, and recommend a version *with the evidence for it*. Never pick
   one silently, and never bump on a hunch.

   ```bash
   git describe --tags --abbrev=0        # the last released tag
   git log --oneline "$(git describe --tags --abbrev=0)"..HEAD
   ```

   Read those commits — and the diff, where a subject line does not settle it —
   and sort them by what they do to a *consumer*. A consumer installs the
   package and invokes its skills, so their contract is skill names, the
   arguments those skills take, and what each skill promises to do:

   - **breaking** — a skill renamed or removed, an argument dropped or
     redefined, a promise withdrawn: anything that makes an invocation that
     worked before stop working, or quietly work differently.
   - **feature** — a new skill, a new argument, behaviour nothing relied on
     before.
   - **fix** — corrections, wording, docs, and restructuring a consumer cannot
     observe.

   The highest category present sets the bump — normally `breaking` → major,
   `feature` → minor, `fix` → patch.

   **While winnow is below 1.0 the major slot stays parked** and the whole
   mapping shifts down one: `breaking` → minor (0.8.0 → 0.9.0), `feature` and
   `fix` → patch (0.8.0 → 0.8.1). 1.0.0 is a deliberate "this is stable now"
   call that only the user makes — never infer it from a breaking change, no
   matter how big.

   Then put it to the user: the version you arrived at, the category that drove
   it, and the specific changes in that category, so they can see what pushed
   the number. They have the final say — if they name a different version, use
   theirs.

3. **Bump the version** — it lives in two places, both in `apm.yml`, that
   must stay in step (package identity vs the marketplace's self-listing):
   - top-level `version:`
   - `marketplace.packages[0].version` (the self-entry)

   Verify they agree: `grep -n 'version:' apm.yml`

4. **Validate and regenerate:**

   ```bash
   apm marketplace check   # entries must resolve OK
   apm pack                # regenerates .claude-plugin/marketplace.json
   ```

   `marketplace.json` is the only generated file in the repo and is committed —
   consumers resolve from it, not from `apm.yml`. If `apm pack` warns, fails,
   or produces any file other than `marketplace.json` and the `build/` bundle
   (e.g. a `.claude-plugin/plugin.json` — this repo deliberately has none),
   stop and surface it; don't release over it.

5. **Commit** the changed files (`apm.yml`, `.claude-plugin/marketplace.json`)
   with the message `Release vX.Y.Z`.

6. **Tag** — annotated, the tag is what the marketplace resolves
   (`tagPattern: v{version}`):

   ```bash
   git tag -m "vX.Y.Z" vX.Y.Z
   ```

7. **Push** the branch and the tag:

   ```bash
   git push && git push origin vX.Y.Z
   ```

8. **Verify** with a final `apm marketplace check`, and report the released
   version and tag to the user.
