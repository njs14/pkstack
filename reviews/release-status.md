---
release: "0.3.0"
status: candidate
version_authority: powers/pkstack/plugin.json
---

# PKStack release status

PKStack 0.3.0 remains an unreleased candidate. The September 5 release campaign
repairs reproduced helper, permission, review-context, and documentation defects.
Current acceptance is tracked in the [release ledger](release-030-acceptance.md);
its incomplete entries prevent a readiness verdict. No 0.3.0 tag or release has
been created. [v0.2.0](https://github.com/njs14/pkstack/releases/tag/v0.2.0) remains
the published release.

## Current campaign

- **Core and installation:** CLI Standard and Quick each completed native
  planning, same-conversation handoff, a stored failing verifier, an
  implementation-only repair, and a passing second attempt. The four tests and
  native planning files remained unchanged. Clean setup, exact-hash idempotence,
  managed-file conflict handling, and the documented 0.2-to-0.3 clean transition
  passed. Doctor passed 81 checks and canonical `okn` validation passed.
- **Curated helpers:** The design and builder repairs passed fresh native tasks
  and independent generated-output checks. Show-me and React narrowing passed;
  writing-for-agents completed after one explicit follow-up for omitted method
  steps. Archify's original input exposed a reader-height defect; fresh input
  exposed incorrect caption placement. Both responsible renderer paths were
  repaired without changing the failing specifications or quality thresholds.
- **Permissions:** Reordered forced switching, prefixed Git commands, and forced
  branch creation now match explicit deny rules. Native acceptance verifies the
  blocked results separately from the ordinary-switch approval path.
- **Pipelines:** The prior updater rejection confused two omitted file identities
  and a valid same-day retrieval date. Review bundles now carry complete changed
  records within the existing shared context budget. Candidate checks align
  with ordinary CI; release notes come from the exact version's changelog entry.

Commands, hashes, native session identities, findings, and limitations are in
[core acceptance](release-030-core.md), [CLI acceptance](release-030-cli.md),
[loop helper acceptance](release-030-loop-helpers.md),
[other helper acceptance](release-030-other-helpers.md),
[Archify acceptance](release-030-archify.md), and
[pipeline acceptance](release-030-pipeline.md).

## Remaining release gates

The Mac locked during current desktop acceptance. IDE planning, Agent Focus,
Crew progress, and Web follow-up still need inspection. Web already stored a
bounded failure/repair/pass in its repository sandbox; that is limited evidence
for the observed fixture. Earlier IDE Standard and Quick successes remain
historical evidence in [friends validation](friends-validation.md).

The authenticated upstream feature check validated all seven inventories,
accepted provenance histories, and generated parity, but initially returned nonzero for
OKF-skills and Archify drift. Archify has since been reconciled through reviewed
runtime fixes and transactional source acceptance. OKF-skills remains for the
bounded updater campaign; no overall freshness pass is claimed yet. A fresh
bounded updater campaign on the repaired controls, frozen-candidate independent
review, exact-commit CI, and final reproducible archive installation remain
required. These gates are recorded individually in the release ledger.

## Publication boundary

The updater remains enabled at its existing daily 13:17 UTC cadence. It selects
one eligible source and requires isolated tests and an independent Kiro-hosted
review before an exact-SHA merge; executable upstream updates still require a
maintainer's review. The current campaign will not override a rejection or
change the schedule to manufacture acceptance.

Publication requires approval of a concrete reviewed main commit, proposed
`v0.3.0` tag, version-specific notes, and the final archive/checksum. Repository
privacy is retained. Server-enforced branch protection is unavailable on this
private-repository plan, so exact-head workflow and manual PR gates remain
necessary. The [upgrade guide](../powers/pkstack/docs/upgrade-0.3.md) preserves
old installations and user evidence through a separate clean consumer.

Earlier results remain in the [identity report](pkstack-identity-validation.md),
[pipeline report](pipeline-readiness-validation.md),
[cleanup report](cleanup-validation.md), and [historical records](historical/pre-v0.2/).
The [Floci lab](https://github.com/njs14/pk-stack-floci-lab) is a separate private
consumer repository.
