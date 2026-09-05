---
release: "0.3.0"
status: candidate
version_authority: powers/pkstack/plugin.json
---

# PKStack release status

PKStack 0.3.0 is not yet released.
[v0.2.0](https://github.com/njs14/pkstack/releases/tag/v0.2.0) remains the latest
published release. Publishing 0.3.0 requires a tag on the reviewed main commit
and a successful release workflow.

The merged identity cleanup uses **PKStack** for the product and `pkstack` for
its technical handle, with `/pkstack` as the entry point. The package, six
PKStack command routes, installed assets, documentation, and banner agree.
Upstream methods and historical source identities are preserved.

## What has passed

- **Deterministic checks:** 167 repository tests, 17 JavaScript tests, and
  the full Power suite passed. New targeted tests also prove retrieval-date
  updates through both inventory formats and reproducible release archives.
  Lint, formatting, types, lockfile checks, Actionlint, and ShellCheck passed.
- **Kiro CLI:** CLI 2.21.1 with Luna / Low discovered `/pkstack` and completed
  a same-session `/pkstack-verified-goal` failure → repair → pass.
- **Kiro IDE:** IDE 1.0.437 imported the renamed Power and displayed all six
  canonical skills. The installed skill files matched the source.
- **Permissions:** The Linux smoke passed seven allowed writes and six denied
  paths, including protected-file checks and cleanup.

The [identity report](pkstack-identity-validation.md) and
[pipeline report](pipeline-readiness-validation.md) record exact commands,
commits, usage, and results.

## Autonomous updates

The owner-approved updater is enabled daily at **13:17 UTC**. It reconciles
one selected upstream source, runs deterministic checks, and requires an
independent Kiro-hosted Opus review before merging.

The [live source run](https://github.com/njs14/pkstack/actions/runs/33949567639)
passed on its first attempt and published
[PR #27](https://github.com/njs14/pkstack/pull/27). Its
[candidate gate](https://github.com/njs14/pkstack/actions/runs/33949846412)
passed both test suites, Opus stream validation, and all candidate bindings,
but rejected the verdict's malformed findings field. Cleanup closed the PR
without merging. A local review with the clarified schema returned three
findings. Their fixes preserve safety rationale, use the detector's trusted
retrieval date, and terminate the new marker with LF. A fresh full campaign
is still required for end-to-end acceptance.

## Limits and release gate

Kiro Web is untested. Crew remains an optional compatibility target. IDE
import and discovery do not prove an IDE verified-goal repair loop or native
Spec/Quick Spec execution.

The full updater campaign must pass before hands-off maintenance is declared
validated. Release readiness does not publish a version: the final reviewed
commit must still pass its checks, receive the release tag, and complete the
release workflow.

Earlier evidence remains in the [cleanup report](cleanup-validation.md) and
[historical records](historical/pre-v0.2/). The
[Floci lab](https://github.com/njs14/pk-stack-floci-lab) is a separate private
consumer repository.
