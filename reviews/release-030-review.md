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

## Remediation and delta review

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

The product reviewer **approved the inspected runtime and source-acceptance
delta** at `51ddb3a5365c0a933cc6503d3a3a3b4470ac3178`. It independently confirmed
the grouped denial patterns and benign controls, retained native denial evidence,
all three Archify corrections, both reconstructed 192-file source inventories,
the seven-path accepted transition, exact upstream CLI/preview blobs, separate
adapted-runtime identities, inverse-patch applicability, all 168 receipt hashes,
the 71-file bundle, unchanged render replays, and the 1,959-character steering
budget. R030-07 is closed for the demonstrated forms. Two stale current-source
documentation references were identified and corrected in the follow-up diff.

The security reviewer carried its scoped approval forward to `51ddb3a`: the
`.github` tree is unchanged at `e46bfc943c678319639b9589defee3d1de47bf6a`, and the
CI reviewer profile remains blob `9bd2837417a87c0cccf26c53837e84b33b3cda06` with
mode `100644`. Neither reviewer repeated the coordinator's full test campaign.
CI run `33976365514` passed on that exact commit.

Neither scoped code approval nor this record declares release readiness. The
follow-up reviews and live gates are recorded below. Desktop acceptance was
subsequently waived as a release blocker by explicit user direction; it is not
reported as tested coverage.

## Merged repairs and live updater review

PR #33 froze the reviewed product and pipeline repairs at
`67b7e3631e8aecf79653321addbff24a8bc319db`, passed exact-head CI, and merged as
`3859f635e36b26d813802445cceb037cc26d0dfc`, whose main CI passed. Later review
covered two separately reproduced campaign defects:

- The browser startup cleanup fix at
  `9c3e6309076075010ab1d8dd9018f74aeba7348f` received independent read-only product
  approval. PR #35 and merged main `a1c0c9a` passed exact CI. The injected failing
  startup reproduced the leak before the fix and passed afterward. The earlier
  live CDP timeout's initiator remains unproven.
- The pending-provenance EOF cleanup fix at
  `e94c357502969e9d3e7fc9845855d2179ca78ecd` received independent read-only security
  approval, including an independent run of all three focused cases. PR #36 and
  merged main `7533634` passed exact CI. The unchanged whitespace guard continues
  to reject unrelated trailing spaces. The earlier live accept-preview error
  was unavailable and is not reconstructed by this reproduction.

The third bounded live updater source run `33980370382` produced exact candidate
`277b2ee5aff153c01632955060dae215d7fa4531`. In candidate gate `33980726626`, both
isolated test jobs passed, the actual no-tool Kiro-hosted Opus verdict approved
with no material findings, and automatic exact-SHA merge succeeded. A separate
read-only reviewer checked full upstream path/blob identities, the deterministic
schema v3 review context, same-day provenance, package and report binding, and
terminal merge evidence. Main `23b34a7df75fcabd8998f174002aa175aecf0ad3` has the
same tree as the reviewed candidate and the expected `7533634` parent.

Authenticated upstream and feature verification on that accepted main passed
all seven configured sources with no selected semantic drift. The detailed
[pipeline report](release-030-pipeline.md) preserves both earlier failed runs
alongside this accepted result. Final report PR/main CI, reproducible packaging,
notes, and extracted-consumer checks must bind to the final main commit in the
local handoff. The user subsequently directed that IDE operation be assumed and
further GUI testing not block delivery. This waives the remaining IDE, Agent
Focus, Crew, and Web GUI follow-up gates; it does not turn them into verified
results or broaden either reviewer's inspected scope.

## Bounded final helper composition

A fresh native CLI conversation loaded both the loop builder and verified-goal
helper against the accepted Power at `23b34a7`. The coordinator introduced one
known implementation-only fault into the earlier passing loop fixture. The
runner rejected the initial `node --test` spelling before any goal was created;
independent code/docs inspection confirmed this was intentional command policy.
Direct execution of the same immutable test file proved five clean passes and
four passes plus one failure with the injected fault before that supported
command was bound.

Goal `f223b5ea-8344-4f29-804f-988d5708993c` then recorded failure and pass at
attempts 1 and 2 of 4 in that same native conversation. The one-line repair
restored the exact original implementation hash, so the earlier 24 independent
process/state cases apply by byte identity. All 169 managed files and six
protected inputs remained unchanged. The separate
[composition report](release-030-composition.md) retains the exact predicate,
session, hashes, preflight limitation, and evidence boundary. This adds current
composition coverage without claiming a new native Spec or broader GUI proof.
