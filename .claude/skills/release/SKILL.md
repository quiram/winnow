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

2. **Bump the version** — it lives in three places that must stay in step:
   - `apm.yml` → top-level `version:`
   - `apm.yml` → `marketplace.packages[0].version` (the self-entry)
   - `plugin.json` → `version`

3. **Validate and regenerate:**

   ```bash
   apm marketplace check   # entries must resolve OK
   apm pack                # regenerates .claude-plugin/marketplace.json and .claude-plugin/plugin.json
   ```

   Both regenerated files are committed — consumers resolve from
   `marketplace.json`, not from `apm.yml`. If `apm pack` warns or fails, stop
   and surface it; don't release over a warning.

4. **Commit** the changed files (`apm.yml`, `plugin.json`, `.claude-plugin/`)
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
