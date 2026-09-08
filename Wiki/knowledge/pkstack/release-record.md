---
type: Record
title: Published releases and acceptance evidence
description: Retained publication identities, checksums, and scope for PKStack releases.
tags: [pkstack, release, evidence]
---

# Published releases and acceptance evidence

This record retains exact release identities, checksums, and acceptance scope. The 0.5.5, 0.5.4,
0.5.3, 0.5.2, 0.5.1, and 0.5.0 entries record publication verification; earlier entries retain the facts reported
before the root reviews directory was removed. The Power manifest remains version authority.
Future release work updates this record and the [changelog](../../../CHANGELOG.md),
following the [release evidence contract](release-and-review.md).

## Verified publication: 0.5.5

[Version 0.5.5](https://github.com/njs14/pkstack/releases/tag/v0.5.5) was published in the
private repository on September 8, 2026 at 02:57:36 UTC from commit
`4f4953606bebdbe17767c09c8637c811c3b8587e`, following
[PR #74](https://github.com/njs14/pkstack/pull/74). It removes exactly three primary-profile
blanket `ask` rules for Git, ordinary writes, and canonical controller commands. It adds no
allow rule and preserves every deny, tool selection, and delegated-agent restriction.
Existing Kiro user, workspace, and session permissions determine routine authorization.

[Exact-main CI](https://github.com/njs14/pkstack/actions/runs/34181644213) passed all 12 jobs
on attempt 1. The [tag-bound release workflow](https://github.com/njs14/pkstack/actions/runs/34181804549)
passed verification and publication, promoting artifact `10039130970` from that run.
The downloaded 4,599,304-byte archive matched the pre-tag verified CI package byte-for-byte;
its checksum file, both release asset digests, and release notes also matched.
Release ID: `384418309`; archive asset ID: `549764720`; checksum asset ID: `549764721`.

Archive SHA-256: `cda86771e9cdfbbb98d30b1fc6516a9700a21725cec35dfe7786d696351a4268`.
Artifact ZIP SHA-256: `dcaca8812a305827da09a77e96898bd01dd28d2fa0b6f9b8e8550c2f2db4311c`.

The frozen candidate `9aefea1635d31315c38659c3b90fecda6a22f4c6` passed the complete local
release gate: 1,092 product tests, 273 Python policy tests, 17 JavaScript policy tests,
and all ten validation lanes. [PR CI](https://github.com/njs14/pkstack/actions/runs/34181213752)
passed all 12 jobs on attempt 1. The merge tree `c00bae46471cde4704990d8175cfef9fff033df6`
equals the reviewed candidate tree. Independent Codex reviewer `release_055_review` returned
ACCEPT after inspecting the full diff and independently asserting exact rule removals,
metadata equality, source/generated profile equality, 192 managed receipt hashes, and
258 coverage hashes. The reviewer did not rerun the full suite or native runtime.
Local doctor reported 91 passes, no warnings or failures; setup was unchanged on repeat.

Native Kiro CLI 2.21.1 probes used the unchanged candidate profile bytes with the prior
0.5.4 controller. Routine Git, write, and controller actions used existing saved permissions
without repeated approval; protected-write and destructive-Git probes were denied by the
selected primary profile. No new remembered Git/write/controller allowance was created.
Kiro separately requested one-shot approval to load the verified-goal skill.

Native Plan session `sess_11e71f8f-cf03-40c3-8933-4c2a85bedafa` handed approved work to
Default. Native Quick Spec session `sess_dc43fc56-1d1c-4167-adf6-27c5cb2227f2` generated
requirements, design, and tasks before an explicit same-conversation return to `pkstack`.
The Spec conversation was resumed after its terminal process ended during planning.
Both paths recorded a failing `node verify.mjs`, repaired only the fixture implementation,
and passed the unchanged four-assertion verifier on attempt two of four. The Spec goal
retained native provenance; verifier, native planning documents, and all 192 managed files
remained unchanged during execution. Their primary-profile SHA-256 matches the release:
`6438abbdc0cc7d9841872396eefa45fc8351ca5e778f2c38f124d57380ce0c3f`.

The exact-main 0.5.5 package consumer smoke separately passed fresh/repeated setup, local
feature and knowledge validation, and failing-then-passing goal verification with its
verifier unchanged. Its doctor reported 85 passes, no failures, and one warning.
Native Plan/Spec agents do not inherit primary-profile permissions; these results establish
the explicit handoff paths and bounded predicates above, not a full 0.5.5 native-runtime
run, new IDE execution, universal permission matching, or an OS sandbox. No new Linux live
retrieval or unattended maintenance-candidate lifecycle result is claimed.

## Verified publication: 0.5.4

[Version 0.5.4](https://github.com/njs14/pkstack/releases/tag/v0.5.4) was published in the
private repository on September 8, 2026 at 02:19:34 UTC from commit
`499b0d090bcafabbba0fcf8ae6ce245d66606352`, following
[PR #72](https://github.com/njs14/pkstack/pull/72). It ports the reviewed pstack and
Archify updates and repairs bounded upstream review batching, oversized repository-wide
comparisons, and aggregate-check latency. Per-file/blob/response limits, exact source
identities, one-source acceptance, and the shared network deadline remain enforced.
[Exact-main CI](https://github.com/njs14/pkstack/actions/runs/34179391369) passed all 12 jobs
on attempt 1. The [tag-bound release workflow](https://github.com/njs14/pkstack/actions/runs/34179618647)
passed verification and publication, promoting artifact `10038385441` from that run.
The downloaded 4,598,487-byte archive matched the pre-tag verified CI package byte-for-byte;
its checksum file, both release asset digests, and release notes also matched.
Release ID: `384406555`; archive asset ID: `549721834`; checksum asset ID: `549721837`.

Archive SHA-256: `51bc68bbd2570de3bb4f3341c8edf35f9e25def54907bc0c37bd60d4ab0a95bc`.
Artifact ZIP SHA-256: `c8c9de5b7859d25633981a27a3bf66079a7d3d32deabffa6aa617ad06ff640d8`.

The frozen candidate `3ffed89e8518f16285e87a18c0686ddddc00a810` passed the complete local
release gate: 1,091 product tests, 273 Python policy tests, 17 JavaScript policy tests,
and all ten validation lanes. [PR CI](https://github.com/njs14/pkstack/actions/runs/34178991264)
passed all 12 jobs. The merge tree `450ecd02033d8a216f24b01134f30a2481f1fc10` equals the
reviewed candidate tree. Independent native Kiro CLI v3 review session
`sess_bc439634-f3b4-4cdd-ac32-c824661c8803` returned correctness PASS and code-quality PASS
with no blockers. Kiro selected Auto; no effort value was reported. The reviewer inspected
the frozen diff and source using read-only tools, and did not execute tests or independently
fetch upstream bytes. All 620 snapshot entries retained their original hashes or symlink
targets after review. Its low-severity suggestion to assert temporary-directory cleanliness
for Archify layout validation was a testing preference, not an observed runtime defect.

The exact-main package consumer smoke passed fresh setup, repeated setup, feature and
local knowledge validation, and a failing-then-passing goal with its verifier unchanged.
Doctor reported 85 passes, no failures, and one warning. The Archify port's focused
regressions reproduced eight failures before the update and passed afterward.

The fresh [changed-main maintenance run](https://github.com/njs14/pkstack/actions/runs/34179404860)
completed successfully. Its detector validated all 13 configured sources with zero drift;
the controller returned `action: current`, so candidate generation and publication were
correctly skipped. Maintenance remains enabled. This closes the observed oversized-delta
and detector-latency failures described in the earlier record; a no-op does not establish
an unattended candidate-generation, substantive-review, or merge lifecycle. No new native
Kiro reasoning or Linux live retrieval result is claimed. Linux retrieval remains
undemonstrated and best effort, outside this release's required acceptance scope.

## Verified publication: 0.5.3

[Version 0.5.3](https://github.com/njs14/pkstack/releases/tag/v0.5.3) was published in the
private repository on September 8, 2026 at 00:37:46 UTC from commit
`b6ce841c178baf8e52cb4ca0d7697feb999abb0e`. It includes the safe maintenance diagnostics,
read-only PR continuation guidance and native evidence from
[PR #69](https://github.com/njs14/pkstack/pull/69), plus the bounded diagnostic follow-up in
[PR #70](https://github.com/njs14/pkstack/pull/70).
[Exact-main CI](https://github.com/njs14/pkstack/actions/runs/34173728243) passed all 12 jobs
on attempt 1. The [tag-bound release workflow](https://github.com/njs14/pkstack/actions/runs/34173901812)
passed verification and publication, promoting artifact `10036568884` from that run.
The downloaded 4,583,345-byte archive matched the pre-tag verified CI package byte-for-byte;
its checksum file, both release asset digests, and release notes also matched.
Release ID: `384377135`; archive asset ID: `549608907`; checksum asset ID: `549608908`.

Archive SHA-256: `da2308b5adb28fdfe7235a8ed719e7f6324b832dabd0472c79ad165b4df1325c`.
Artifact ZIP SHA-256: `f45619a01ccd6ef5c3e980a937b156b2cb7f12bcd0de00a7b48826bfdf8169ac`.

The original Fable session `270ac4ba-5584-4c07-a7a9-c0fc59deb6bb`, model `claude-fable-5-1`,
accepted PR #69 head `7deab123de6b4017f1d17f5e5d28adb6014a0a89`, tree
`94feb6af42bb5f9539752aa44e5695aeb627e87c`, after independently rerunning 107 guard tests
and 140 passing targeted tests. One Kiro login sentinel failed in its deliberately
unauthenticated HOME; this was an environment limitation, not a successful test.
It separately accepted PR #70 head `3d1bf2841cbe28bfccf269ed880c6adc73b785e1`, tree
`7d7965b0a01fdafb2ac541b6097aab589461ec70`, after another independent 107-test guard run.
Each merge tree equals its accepted candidate tree; the tagged source is PR #70's merge.
The initial reviewer attempt hit a session limit before a verdict; acceptance came only
after resuming that same session after its reported reset. No substitute reviewer was used.

The [native verification record](native-kiro-composition.md#september-7-bounded-native-verification)
retains the stored-verifier repair, scoped Impeccable refinement and read-only PR continuation.
The PR continuation regression preserved all 325 Git metadata path/hash entries across two
same-session snapshots. These observations establish their documented CLI scope, not general
model compliance, native Spec/IDE acceptance or an OS-enforced read-only sandbox. Full candidate
CI retained 1,063 product tests, 271 Python policy tests and 17 JavaScript policy tests.
Setup was unchanged on repeat and all 190 generated receipt entries matched.

Maintenance remains enabled but has not completed an unattended candidate lifecycle.
The first [changed-main run](https://github.com/njs14/pkstack/actions/runs/34173315294)
stopped with a generic UpstreamError; its initiating cause remains unproved. After the
fixed-message follow-up, [run 34173729134](https://github.com/njs14/pkstack/actions/runs/34173729134)
explicitly reported `upstream comparison patches exceed the 262144-byte limit` and stopped
before inventory, proposal or substantive review. A separate source-specific read-only check
identified the same bound for `cursor-pstack`; that source attribution is local evidence.
No size, schema, credential, retry or review controls were relaxed, and no upstream update
was accepted or rejected. Resolving that oversized source delta requires a separately reviewed
bounded transition; repeated identical dispatches do not close the gap. Linux live retrieval
remains undemonstrated and best effort, outside this release's required acceptance scope.

## Verified publication: 0.5.2

[Version 0.5.2](https://github.com/njs14/pkstack/releases/tag/v0.5.2) was published in the
private repository on September 7, 2026 at 19:37:14 UTC from commit
`071ab3a36da4d25f568e03c91606fc9c8e6986ad`. It includes the reviewed controller recovery,
setup, maintenance-schema, verifier-command, and documentation fixes from
[PR #66](https://github.com/njs14/pkstack/pull/66), with release metadata prepared in
[PR #67](https://github.com/njs14/pkstack/pull/67).
[Exact-main CI](https://github.com/njs14/pkstack/actions/runs/34155963367) passed all 12 jobs.
The [tag-bound release workflow](https://github.com/njs14/pkstack/actions/runs/34156227097)
passed verification and publication, promoting artifact `10030994738` from attempt 1.
The downloaded 4,582,590-byte archive matched that verified CI package byte-for-byte;
its checksum file, both release asset digests, and release notes also matched.
Release ID: `384285607`; archive asset ID: `549286561`; checksum asset ID: `549286562`.

Archive SHA-256: `19d5dd8b24ac0ad3eaac2f35bcae17fc56e639bb1279ff5c6f5ad9617376559c`.
Artifact ZIP SHA-256: `66b9b3721a79761219366ceef8eb2d311e18dbb077919bee3c0ff26da45cbfda`.

Codex reviewed Fable's original PR and reproduced three recovery defects: archiving
before acquiring the state lock, overwriting an earlier archive during a timestamp
collision, and failing to recover invalid UTF-8. Five added regression cases failed
against the original source and passed after correction; 368 goal/runner tests,
static checks, local fast checks, knowledge validation, and generated parity passed.
Fable accepted the corrections at `c34a392e40d1d2434cf267f59609376daca18f55`; PR #66's
merge tree is identical. The final PR CI passed all 12 jobs on attempt 3 after an
unrelated browser WebP timeout and a partial rerun that could not find its
attempt-specific execution plan. The isolated local browser check and full CI rerun
passed without browser source changes.

Fable separately accepted metadata candidate `fba3d32890bf36f3ff46416821f8c453dd9c40cb`;
the tagged release tree is identical. That review covered the complete eleven-file
metadata diff and supplied validation receipts without independently rerunning tests.
All 190 generated receipt hashes matched and setup had no pending changes. Every code
fix was reviewed by the reviewer who did not author it.

The exact-main package consumer smoke passed fresh setup, repeated setup, feature and
local knowledge validation, and a failing-then-passing goal with the verifier unchanged.
Doctor reported 83 passes, no failures, and one warning. This release establishes no
new native Kiro reasoning or Linux live retrieval evidence, and no completed unattended
maintenance run. Earlier native acceptance retains its recorded scope.

## Verified publication: 0.5.1

[Version 0.5.1](https://github.com/njs14/pkstack/releases/tag/v0.5.1) was published on
September 7, 2026 at 17:13:13 UTC from commit
`5f18ccf852c50da731ab2b82fa2763038343a189`, following
[PR #64](https://github.com/njs14/pkstack/pull/64). It includes the Impeccable and
PR-babysitting integration from [PR #63](https://github.com/njs14/pkstack/pull/63).
[Exact-main CI](https://github.com/njs14/pkstack/actions/runs/34146428974) passed all 12 jobs.
The [tag-bound release workflow](https://github.com/njs14/pkstack/actions/runs/34146629760)
passed verification and publication, promoting artifact `10027844982` from attempt 1.
The downloaded 4,579,346-byte archive matched that verified CI package byte-for-byte;
its checksum file and release asset digest also matched.

Archive SHA-256: `438e5db1b3ebc1eec6fa96090948bb229fdac3d50b6cd127bdc5114c1f600b27`.
Artifact ZIP SHA-256: `6f65432b6c6bc408f7dfeed0ecbff0bff81bda1bdb64d3f995de15860d7bcc32`.

Independent Codex reviewer `release_review` returned Ship for candidate
`759ce2f6ab667fcdbbab85106821863331c42c98`; the merged release tree is identical.
The review covered the accumulated diff from published 0.5.0, including provenance,
permissions, routing, version mirrors, and release notes. It independently checked
all 190 generated receipt hashes, both new bundles and inventory tree identities,
42 cached Impeccable and 5 cached babysit-pr source blobs, and all 254 hashed coverage
entries. Ten excluded or provenance-only source blobs lacked cached content; their
inventory tree binding was checked without independently hashing their contents.

The frozen candidate's full local gate passed 1,053 package tests, 269 repository
Python tests, 17 JavaScript policy tests, and static/documentation checks. Doctor
reported 89 pass, no failures or warnings; setup was idempotent. The reviewer inspected
these exact-candidate receipts rather than rerunning those suites. Initial stale
changelog/security coverage hashes were corrected before the passing frozen gate.

This release adds agent guidance and consolidates PR supervision; it does not install
the Impeccable runtime or upstream PR watcher. Live Kiro reasoning with the new skills
and a future unattended maintenance run remain unverified. Earlier native acceptance
retains its recorded scope; this release establishes no new Linux retrieval result.

## Verified publication: 0.5.0

[Version 0.5.0](https://github.com/njs14/pkstack/releases/tag/v0.5.0) was published on
September 7, 2026 at 12:58:32 UTC from commit
`e86f3227cf0eb2a91ed117e026c3a797a99893a1`, following
[PR #61](https://github.com/njs14/pkstack/pull/61).
[Exact-main CI](https://github.com/njs14/pkstack/actions/runs/34124465137) passed all 12 jobs.
The [release workflow](https://github.com/njs14/pkstack/actions/runs/34124731962) passed
verification and publication, promoting artifact `10019556676` from attempt 1.
The downloaded 4,557,563-byte archive matched the verified CI package byte-for-byte;
its checksum file and release asset digest also matched.

Archive SHA-256: `926c26ace2f797322c1ff0c83e1de2ff73082eebe99d1b87b2531a9dc17a928c`.
Artifact ZIP SHA-256: `1e6455153cd2785577a8403d8126e83781c8b62815882034eca71a0347990a3d`.

Independent review approved implementation `2fc3be9c59de7bed0be437c8727e7ae8dbcd64e2`;
the merged release tree is identical. The fixed-commit local full gate passed 1,046
package tests, 269 repository Python tests, 17 JavaScript policy tests, and static checks.
All 183 generated receipt hashes matched; all 258 tracked Markdown documents passed the
local link/anchor scan. Initial stale test fixtures and a root-wrapper retirement omission
were corrected before the passing fixed-commit gate.

Fresh native Kiro IDE 1.0.437 acceptance covered Power source selection, preview, setup,
doctor, local knowledge validation, and a repair by the workspace `pkstack` agent. The
stored verifier failed before implementation, then passed on attempt 2 with all four
original tests unchanged. Live bounded Mac knowledge retrieval passed with Kiro CLI
2.21.1 and validated citations. Canonical OKF network reproof passed. This campaign does
not refresh native Spec/Quick Spec evidence or establish Linux live retrieval.

The release removes standalone public commands and old receipt/goal compatibility.
Existing consumers need the reviewed [clean-install process](installation-and-upgrades.md)
that preserves user content and historical evidence. The upstream workflow remains active.

## Recorded publication: 0.4.4

[Version 0.4.4](https://github.com/njs14/pkstack/releases/tag/v0.4.4) was recorded published on
September 7, 2026 at 01:55:21 UTC, from commit
`4dce1479bb426ad586265e15b4b6cc410fa75bd6`. It includes the Astral tooling and uvx launcher.
[Exact-main CI](https://github.com/njs14/pkstack/actions/runs/34074325906) passed all 12 jobs;
[publication](https://github.com/njs14/pkstack/actions/runs/34074509479) promoted artifact
`10001545882` from attempt 1. The 4,564,043-byte archive matched the verified CI package
byte-for-byte; checksum and asset digest also matched.

Archive SHA-256: `5c380104ba7700aae65d07aea8e51626251e83c517c4da1913de059c51ce5c93`.
Artifact ZIP SHA-256: `361a5a7a1fd398b64ec92b012e77022427c1c4a4a1b958abf13ba44f88094f91`.

The metadata-only review approved `6a78b1910563854215e0b78232f9a39c74522749`. Native Astral
observations and deterministic uvx acceptance remain bound to their own source candidates;
this publication did not establish a new native campaign. The
[immutable publication record](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-status.md#published-release-044)
retains the full chronology and links.

## Earlier recorded publications

| Release | Published UTC | Archive SHA-256 |
| --- | --- | --- |
| [0.4.3](https://github.com/njs14/pkstack/releases/tag/v0.4.3) | 2026-09-06 22:32:43 | `88de74ba5ffb609947dd024713f99b9870561e5a24b2407f870aef4847993baa` |
| [0.4.2](https://github.com/njs14/pkstack/releases/tag/v0.4.2) | 2026-09-06 15:47:20 | `a5ad22271802055981607a954b3b9533264924319f07b1505a2f2cf55c9a5c32` |
| [0.4.1](https://github.com/njs14/pkstack/releases/tag/v0.4.1) | 2026-09-06 14:27:18 | `5f09ffa3006b91acdde54824aafd9700871004efe938b009aa79638f42560fd8` |
| [0.4.0](https://github.com/njs14/pkstack/releases/tag/v0.4.0) | 2026-09-06 12:15:50 | `6d94eebc69b4ab417aa915f350bf6e9994763a38dc3c180c7731fe1a43989716` |

The [frozen release history](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-status.md) binds each earlier publication to
its exact source, main run, promoted artifact, and byte comparison. Version 0.4.3 retains
operator-assisted planning and the unresolved Unicode reasoning limitation; 0.4.2 separates
native first-task repair from scripted installation checks; 0.4.1's performance results are
workload-specific; 0.4.0's live retrieval evidence is macOS-only. See
[native planning](native-kiro-composition.md), [installation](installation-and-upgrades.md),
[quality checks](quality-and-ci.md), and [knowledge lifecycle](knowledge-lifecycle.md).

## Review-directory retirement

Reusable findings are synthesized into the [Wiki topics](../index.md#lessons-synthesized-from-reviews).
The root `reviews/` directory is deleted, rather than copied to another report archive. Original
reports, transcripts, images, and fixture snapshots remain accessible through immutable Git links
at commit `9bb1cbbb52552f95f7ccc61e14c44283e526c80d`. Only four JSON records still consumed by tests or the runtime canary are
retained locally under `.github/fixtures/`; their bytes are unchanged. The separate shipped
`powers/pkstack/reviews/` review harness remains part of the Power.

New project understanding belongs in the Wiki. Keep release evidence identities here, executable
regressions in their test fixtures, and original historical source material in Git history.
