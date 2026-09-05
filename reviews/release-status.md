---
release: "0.3.0"
status: candidate
version_authority: powers/pkstack/plugin.json
---

# PKStack release status

PKStack 0.3.0 remains an unreleased candidate; publication approval is separate.
[v0.2.0](https://github.com/njs14/pkstack/releases/tag/v0.2.0)
remains the published release. The reviewed implementation is merged through
`23b34a7df75fcabd8998f174002aa175aecf0ad3`. The bounded updater campaign and
authenticated upstream verification passed. The user waived further GUI testing
on September 5, 2026 and directed that IDE operation be assumed. The final
report commit, its CI, and the archive/checksum are
bound in the local publication handoff after these reports are merged. The
[acceptance ledger](release-030-acceptance.md) tracks the remaining gates.

## Verified delivery

| Reviewed repair | Reviewed head | Merged main |
| --- | --- | --- |
| [PR #33](https://github.com/njs14/pkstack/pull/33): product and security scopes approved | `67b7e36` | `3859f63` |
| [PR #35](https://github.com/njs14/pkstack/pull/35): browser cleanup independently approved | `9c3e630` | `a1c0c9a` |
| [PR #36](https://github.com/njs14/pkstack/pull/36): retry cleanup security approved | `e94c357` | `7533634` |
| [PR #37](https://github.com/njs14/pkstack/pull/37): bounded upstream update independently approved and automatically merged | `277b2ee` | `23b34a7` |

The retry repair's exact [PR CI run](https://github.com/njs14/pkstack/actions/runs/33979933200)
and [main CI run](https://github.com/njs14/pkstack/actions/runs/33980155633) passed.
Local evidence includes 870 Power tests and the latest 185 Python policy tests
plus 17 Node tests. Candidate gate
[33980726626](https://github.com/njs14/pkstack/actions/runs/33980726626) passed
both exact base and candidate suites: each passed 869 Power tests, one skip for
unavailable Kiro CLI, 185 Python policy tests, and 17 Node tests. The merged
implementation tree equals that candidate tree. Doctor passed 81 checks;
feature, generated-parity, and canonical `okn` checks passed. Authenticated
upstream and feature verification passed for all seven configured sources with
no selected semantic drift on accepted main `23b34a7`.

CLI Standard and Quick completed native failure/repair/pass loops. Curated
helpers passed their bounded tasks with recorded corrections and follow-ups;
installation, idempotence, conflict handling, and the clean 0.2-to-0.3 transition
have retained evidence. See [core](release-030-core.md), [CLI](release-030-cli.md),
[loop helpers](release-030-loop-helpers.md), [other helpers](release-030-other-helpers.md),
[Archify](release-030-archify.md), and [permissions](release-030-permissions.md).
The final [builder/verified-goal composition](release-030-composition.md) also
passed natively at attempt 2 of 4. Its fixed five-test suite and 169 managed
files were preserved, and the one-line repair restored the exact implementation
already covered by 24 independent process/state cases.

## Coverage assumptions and final binding

- **GUI coverage assumed by user direction:** IDE Standard, Quick, and setup;
  Agent Focus; Crew; and Web final follow-up were not completed in this campaign.
  They are no longer release blockers. The Web fixture's stored
  failure/repair/pass and earlier IDE results remain bounded evidence; the waiver
  does not establish fresh passing results for these surfaces.
- **Final artifact:** Reproducible archives and extracted-consumer checks for
  main `3859f63` are historical evidence. Notes, archive, checksum, and acceptance
  must bind to the final report commit in the local handoff; this report does not
  substitute the earlier archive for that final evidence.

The [pipeline history](release-030-pipeline.md) retains all three campaigns.
Campaign 1 closed PR #34 unmerged after a base-browser CDP timeout; the proven
startup-cleanup defect is fixed, while the timeout initiator remains unproven.
Campaign 2 stopped before publication. Its reproduced EOF cleanup defect is
fixed, while the earlier `accept-preview` initiating error was not retained.
Campaign 3 passed its bounded repair, both test suites, independent review, and
automatic merge. These later passes do not reconstruct the missing initiators.

## Publication boundary

The repository remains private and the daily updater remains enabled at
13:17 UTC. Its isolated tests, independent Kiro-hosted review, and exact-SHA
merge gates remain required; executable upstream changes also require
maintainer review. Server-enforced branch protection is unavailable on the
current private-repository plan, so workflow and manual PR gates remain
necessary.

Publication requires approval of a concrete reviewed main commit, proposed
`v0.3.0` tag, version-specific notes, and final archive/checksum. The
[upgrade guide](../powers/pkstack/docs/upgrade-0.3.md) preserves existing
installations and user evidence through a separate clean consumer.
