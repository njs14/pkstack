---
release: "0.3.0"
status: candidate
version_authority: powers/pkstack/plugin.json
---

# PKStack release status

PKStack 0.3.0 is an unreleased candidate. The identity cleanup and a bounded
updater campaign passed their acceptance gates; the subsequent PKStack & friends
changes have green deterministic CI, with live limitations recorded below.
[v0.2.0](https://github.com/njs14/pkstack/releases/tag/v0.2.0) remains the latest
published release. Publishing 0.3.0 requires a tag on the reviewed main commit
and a successful release workflow.

The merged identity cleanup uses **PKStack** for the product and `pkstack` for
its technical handle, with `/pkstack` as the entry point. The package, six
PKStack command routes, installed assets, documentation, and banner agree.
Upstream methods and historical source identities are preserved.

## What has passed

- **Deterministic checks:** 177 repository tests, 17 JavaScript tests, and
  854 Power tests passed on the friends product head in CI, with one
  installed-Kiro check skipped there.
  Tests also prove retrieval-date updates through both inventory formats and
  reproducible release archives.
  Lint, formatting, types, lockfile checks, Actionlint, and ShellCheck passed.
- **Kiro CLI:** CLI 2.21.1 with Luna / Low completed both native Standard and
  Quick Spec planning, then a same-conversation handoff to `pkstack` and a
  Spec-bound failure → implementation-only repair → pass. Both retained the
  four acceptance tests and planning artifacts unchanged.
- **Kiro IDE:** IDE 1.0.437 imported the renamed Power and displayed all six
  canonical skills. The installed skill files matched the source.
- **Permissions:** The Linux smoke passed seven allowed writes and six denied
  paths, including protected-file checks and cleanup.

The [friends report](friends-validation.md),
[identity report](pkstack-identity-validation.md), and
[pipeline report](pipeline-readiness-validation.md) separate exact commands,
commits, usage, results, and review scope.

## Autonomous updates

The owner-approved updater is enabled daily at **13:17 UTC**. It reconciles
one selected upstream source, runs deterministic checks, and requires an
independent Kiro-hosted Opus review before merging.

The [live source run](https://github.com/njs14/pkstack/actions/runs/33951163753)
passed on its first attempt. Its
[candidate gate](https://github.com/njs14/pkstack/actions/runs/33951477875)
passed both test suites, validated an independent Opus approval with no material
findings, and automatically merged [PR #29](https://github.com/njs14/pkstack/pull/29)
as `db35a9f221d5c6ef0bbdb685c367ae23161ae43f`. The
[retained approval](ci-opus-updater-approval-2026-09-05.json) binds the exact
candidate and source hashes. All three earlier review findings were addressed.

This proves a bounded OKF metadata/exclusion update through detection, repair,
verification, independent review, and automatic merge. Archify drift remains for
the normal cadence. Updates requiring executable code or broader authority still
stop for a maintainer. GitHub's separate ordinary bot-PR CI can require owner
approval; the autonomous candidate gate does not depend on that additional run.

## Limits and release gate

Kiro Web and Crew are untested. The latest IDE campaign completed native Standard
planning and same-tab agent selection, then paused when the Mac locked. Its
repair loop and Quick Spec campaign remain pending; import and discovery are
not substitutes for that evidence.

All six curated helpers received bounded CLI smokes. The bundled Archify sample
failed vertical containment. The control-loop retest skipped a required
reference, and the builder's generated sample had verification/attempt-bound
defects. These limits are retained in the
[curated report](friends-curated-validation.md), not counted as passing workflows.
No bundled upstream executable was changed to hide those findings.

The friends update extends the existing Opus review with digest-bound catalog,
neighboring instructions, and trusted-base routing cases. Oversized or uncovered
changes require manual review. Deterministic tests and independent code review
cover the change; it has not received a new live autonomous-updater run.

Release readiness does not publish a version: the reviewed main commit must
still receive a release tag and complete the release workflow. No 0.3.0 tag or
release was created during this acceptance work. Repository privacy is retained;
server-enforced branch protection is unavailable on the current private-repo
plan, so the exact-head workflow and manual PR gates remain important.

Earlier evidence remains in the [cleanup report](cleanup-validation.md) and
[historical records](historical/pre-v0.2/). The
[Floci lab](https://github.com/njs14/pk-stack-floci-lab) is a separate private
consumer repository.
