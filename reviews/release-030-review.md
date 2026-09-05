# PKStack 0.3.0 independent review

## Frozen candidate 8e1554a

Two fresh read-only reviewers inspected
`8e1554aa560a4d3772d9a203dbe392bf15c90a02` against
`3d4583a16fe2caca497d8b8fe7d5c860a12c1a2f`. They did not implement the changes,
modify files, operate native sessions, use credentials, or publish anything.

The pipeline/security reviewer **approved the inspected code scope**: exact
base/head source-record projection, digest binding, the shared 64 KiB context
cap, schema v3 rejection behavior, trusted reviewer controls, candidate/Kiro
credential separation, same-day provenance semantics, and exact-version release
notes. Four release-note tests also passed in that review. It did not reconstruct
the original remote PR #32 objects or replace the pending live campaign.

The product reviewer **requested changes** for one P2 finding: grouped Git
switch options `-qf`, `-dqf`, and `-qC` still resolved to ask while standalone
destructive options resolved to deny. This is a hard-deny coverage gap, not
silent execution. The reviewer required explicit grouped-form rules, regression
and native negative cases, ordinary controls, generated refresh, and bounded
release-note wording. Broad `-*f*` globs were rejected because they span spaces
and can incorrectly match benign arguments.

The remaining inspected product changes had no material finding. The reviewer
checked the Archify rendered original/native and narrow examples, all six export
hashes, inverse-patch application, bundle manifests, 168 root receipt hashes,
generated parity, retained 24-case loop result and candidate hash, setup-discovery
documentation, and the upgrade boundary. It did not rerun the full suite.

## Remediation and next review

The grouped-option correction now covers the three demonstrated forms with
explicit first/later-argument and Git-prefix patterns. The expanded regression
checks 243 strings, including benign branch names that broad patterns would
incorrectly deny. Three fresh native grouped-form calls returned automatic
agent-profile denial with no approvals, and all 172 consumer hashes remained
unchanged. Ordinary ask/cancel evidence is retained. A separate read-only inspection of
the authenticated upstream delta also identified three narrow Archify runtime
defects: invalid render argument handling, asynchronous watcher errors, and
horizontal sequence-caption bounds. These were outside the frozen product
review. All were reproduced, repaired, and reconciled through the maintainer lane;
the accepted source transition is recorded in the Archify report. The final local
gates passed 869 Power, 184 repository Python, and 17 Node tests, plus static,
doctor, and canonical knowledge checks.
The updater's executable-write boundary remains unchanged.

The new frozen commit must receive review of those deltas and affected evidence.
Neither scoped code approval nor this record declares release readiness.
Desktop follow-up, upstream freshness, live updater review, exact-commit CI,
and final artifact installation remain separate acceptance gates.
