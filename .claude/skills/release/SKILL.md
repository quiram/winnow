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

2. **Bump the version** — it lives in two places, both in `apm.yml`, that
   must stay in step (package identity vs the marketplace's self-listing):
   - top-level `version:`
   - `marketplace.packages[0].version` (the self-entry)

   Verify they agree: `grep -n 'version:' apm.yml`

3. **Validate and regenerate:**

   ```bash
   apm marketplace check   # entries must resolve OK
   apm pack                # regenerates .claude-plugin/marketplace.json
   ```

   `marketplace.json` is the only generated file in the repo and is committed —
   consumers resolve from it, not from `apm.yml`. If `apm pack` warns, fails,
   or produces any file other than `marketplace.json` and the `build/` bundle
   (e.g. a `.claude-plugin/plugin.json` — this repo deliberately has none),
   stop and surface it; don't release over it.

4. **Commit** the changed files (`apm.yml`, `.claude-plugin/marketplace.json`)
   with the message `Release vX.Y.Z`.

5. **Tag** — annotated, the tag is what the marketplace resolves
   (`tagPattern: v{version}`):

   ```bash
   git tag -m "vX.Y.Z" vX.Y.Z
   ```

6. **Push** the branch and the tag:

   ```bash
   git push && git push origin vX.Y.Z
   ```

7. **Verify** with a final `apm marketplace check`, and report the released
   version and tag to the user.
