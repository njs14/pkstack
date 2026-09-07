---
release: "0.4.4"
status: published
version_authority: powers/pkstack/plugin.json
---

# PKStack release status

## Published release: 0.4.4

**[PKStack v0.4.4](https://github.com/njs14/pkstack/releases/tag/v0.4.4) was published
on September 7, 2026 at 01:55:21 UTC.** It contains the Astral tooling and uvx launcher
changes from [PR #53](https://github.com/njs14/pkstack/pull/53) and
[PR #54](https://github.com/njs14/pkstack/pull/54). See the
[changelog](../CHANGELOG.md#044--2026-09-06).

[Release PR #55](https://github.com/njs14/pkstack/pull/55) merged at
`4dce1479bb426ad586265e15b4b6cc410fa75bd6`; tag `v0.4.4` resolves to that commit.
The [independent Grok 4.6 / xhigh review](release-044-review.md) approved the
metadata-only preparation at `6a78b1910563854215e0b78232f9a39c74522749`.
The final PR and main trees matched. Both
[PR CI](https://github.com/njs14/pkstack/actions/runs/34074174258) and
[exact-main CI](https://github.com/njs14/pkstack/actions/runs/34074325906) passed all
12 jobs. Six metadata/distribution tests, four release-note tests, and the full
static gate passed locally. Reviewed setup updated only the three generated
version files and ended with an idempotent preview.

The [Astral report](astral-python-auto/README.md) retains bounded native Kiro
observations; the [uvx report](uvx-entrypoint/README.md) retains deterministic CLI
acceptance and independent approvals, including the cold-cache CI correction.
The uvx full local gate passed 1,016 Power tests and 235 repository tests. These
results are bound to their recorded commits; this metadata-only version update
does not claim a fresh native campaign.

The [release workflow](https://github.com/njs14/pkstack/actions/runs/34074509479)
passed both verification and publication. It promoted artifact `10001545882` from
main run `34074325906`, attempt 1. The pre-tag verifier checked the live repository,
absent proposed tag, exact main run, artifact identity, outer ZIP digest, inner file
checksums, version mirrors, and notes. Artifact ZIP SHA-256:
`361a5a7a1fd398b64ec92b012e77022427c1c4a4a1b958abf13ba44f88094f91`.

The published **4,564,043-byte** archive was downloaded and compared byte-for-byte
with the verified CI package. Its checksum file and GitHub asset digest matched.
Archive SHA-256:

```text
5c380104ba7700aae65d07aea8e51626251e83c517c4da1913de059c51ce5c93
```

The repository remains private. The existing v0.4.3 release remains available;
no rollback ran, and no package registry publication was added.

## Previous publication: 0.4.3

**[PKStack v0.4.3](https://github.com/njs14/pkstack/releases/tag/v0.4.3) was
published on September 6, 2026 at 22:32:43 UTC.** Planning uses one shared grilling
method with Kiro's native Plan and Specs. The release corrects the seven CLI audit
findings, places approved-plan knowledge capture before implementation, and makes
the runnable native Plan handoff explicit on the routing surfaces. See the
[changelog](../CHANGELOG.md#043--2026-09-06).

[PR #51](https://github.com/njs14/pkstack/pull/51) merged at
`e76b88c696da85b627170ece28d168012cddc4cf`; tag `v0.4.3` resolves to that commit.
External Claude Code **Opus 5 / xhigh** authored the repairs. External Grok CLI
**Grok 4.6 / xhigh** independently approved source and bounded native acceptance
at `e4941073adf89a130e8ee268fb122c113cf8a409`, then approved the report and changelog
deltas through final PR head `383c94c5fdc9822a4a761d53442656538cb47e67`.
The final PR and merged Git trees were identical:
`637755a7557cd8cf8a2e4b2d7506ea158fa2746c`.

Both [final PR CI](https://github.com/njs14/pkstack/actions/runs/34063925769) and
[exact main CI](https://github.com/njs14/pkstack/actions/runs/34064077156) passed all
12 jobs. The full v4 local gate passed 965 product tests and policy checks under
supported Python. The final routing-only change passed 22 fast checks and two
coordinator boundary checks; the author reported 131 focused asset/Pocock tests.
Managed setup ended with an idempotent preview.

The [v5 routing report](planning-043-v5/README.md) records the passing first native
CLI response with the exact `/plan Read .kiro/skills/grilling/SKILL.md;` prefix,
settled context, an open question for Plan, and no file changes. It supersedes two
retained v4 command-emission failures. The [v4 workflow report](planning-043-v4/README.md)
records native Plan loading the method, neutral approval, knowledge capture before
code, preserved tests and passing regression probes, repeated approval without
duplicate knowledge, and IDE Quick Spec acknowledgement of explicit no-write
approval with zero subsequent fixture changes. The
[original campaign](planning-043/README.md) remains the historical record of earlier
failures. Independent review approved composing these bounded observations because
v5 changed routing guidance without changing the interview or capture method.

**Acceptance limits remain explicit.** CLI `Auto` did not identify its resolved
model. Ordinary plan review corrected a Unicode validation-order mistake; the v5
router still proposed that wrong ordering, and autonomous Unicode correctness is
not claimed. The v5 command was emitted but not executed in that router-only test.
The IDE v4 check reused native-created v3 Spec artifacts; it was not a fresh v4
creation or implementation run. Native capture-validation output was truncated:
its timing evidence is tool order, the agent's success statement and file events;
a separate later host check verifies final knowledge state. These are bounded
workflow checks, not a guarantee across models and runs.

The [release workflow](https://github.com/njs14/pkstack/actions/runs/34064285201)
passed verification and publication. It promoted artifact `9998393035` from main
run `34064077156`, attempt 1. The verified artifact ZIP SHA-256 was
`136195a30851f7972bc053d2730d168c723df2a9cf83e7ac82f77a198c2f5ea0`.
The published **4,539,732-byte** archive was downloaded and compared byte-for-byte
with that verified CI package. Its checksum file and GitHub asset digest matched.
Archive SHA-256:

```text
88de74ba5ffb609947dd024713f99b9870561e5a24b2407f870aef4847993baa
```

The extracted-package consumer passed setup, idempotence, feature and local
knowledge validation, and a scripted fixed-verifier failure/repair/pass smoke.
Its doctor reported 78 passes, zero failures and one warning. This mechanical
package smoke is separate from the native model observations above. Local pre-tag
verification ran with uv-managed Python 3.12.14; an initial wrapper rejected the
older system Python before package verification began.

The previous v0.4.2 archive remains available for reverting an installation through
the reviewed setup path. No rollback ran. The repository remains private; no global
model defaults, permission settings or hooks were changed for this work.

## Previous publication: 0.4.2

**[PKStack v0.4.2](https://github.com/njs14/pkstack/releases/tag/v0.4.2) was
published on September 6, 2026 at 15:47:20 UTC.** It adds benefit-led
introductions, complete CLI and IDE installation paths, executable onboarding
regressions, and a first-task guide verified through an ordinary Kiro CLI v3
repair. It also documents user-owned saved requests and the observed native
prompt-menu syntax limit. See the [changelog](../CHANGELOG.md#042--2026-09-06).

[PR #48](https://github.com/njs14/pkstack/pull/48) merged at
`c7c3bb6f06f863502084333a63d6fdd258a20119`; tag `v0.4.2` points to that commit.
Independent reviewer `onboarding_final_review` approved final candidate
`b829720ee0f43e543279acecc69cb8a6a1f8989e`, and the merged tree was identical.
Both the [final PR CI](https://github.com/njs14/pkstack/actions/runs/34043105774)
and [exact main CI](https://github.com/njs14/pkstack/actions/runs/34043224626)
passed all 12 jobs. This review used a Codex reviewer; no new external Fable or
Grok review is claimed.

The [fresh native CLI campaign](onboarding-042/README.md) passed on macOS with
Kiro CLI 2.21.1, v3, workspace agent `pkstack`, and displayed model **Auto**.
Effort was not displayed. Kiro loaded the skill, displayed the explicit stored
verifier, repaired `account.py`, and reran that verifier in one conversation.
The tests, goal, contract digest, and attempt budget stayed unchanged. Stored
history records failure then pass on attempt **2 of 4**, and all four tests
passed independently. The observer supplied no repair or passing goal attempt.
The campaign receipt preserves the tested commit and Power tree, then binds
13 unchanged Git objects across the later conceptual documentation edits.
The whole released Power tree differs from the campaign tree; the tested
runtime, setup, skills, fixture, and first-task instructions are unchanged.

Local checks passed: seven final focused onboarding/release-metadata tests
in 29.28 seconds, the earlier 22-test fast contract, and setup fallback checks.
The live disposable setup reported **84 pass / 0 fail / 0 warn**, passing local
knowledge validation, and idempotence. The reviewer verified all 178 receipt
hashes and 59 local links/anchors; the final setup preview reported zero changes.
The [campaign report](onboarding-042/README.md#local-regressions) discloses the
corrected obsolete documentation assertion and the aborted input-harness probe.
The preserved unified implementation-diff artifact contains normal single-space
context lines; excluding that artifact, the final diff whitespace check is clean.

The [release workflow](https://github.com/njs14/pkstack/actions/runs/34043366532)
passed verification and publication, promoting artifact `9992323291` from main
run `34043224626`, attempt 1. Its artifact ZIP SHA-256 was
`60ed21dc9841cadc53f6cdd06bd54dffe2ec7c795dca9ffc08caa1250bdd9e0e`.
The published 4,596,302-byte archive was downloaded and compared byte-for-byte
with the verified CI package. The checksum matched the digest and published
asset filename. The archive SHA-256 is:

```text
a5ad22271802055981607a954b3b9533264924319f07b1505a2f2cf55c9a5c32
```

The extracted-package consumer passed setup, idempotence, feature and local
knowledge validation, and its separate scripted failure/repair/pass smoke.
Its doctor reported 78 passes, zero failures, and one warning because the
secretless package job does not install optional Kiro CLI. That mechanical
smoke is distinct from the native model-authored repair above.

Saved-file creation, `@name` expansion, and skill activation through saved
requests remain unverified. The installed v3 `/prompts details` probe became
an ordinary model request and was cancelled without tools or writes; the
direct first-task skill invocation remains the verified path. No fresh IDE GUI
repair or knowledge-retrieval campaign was run. Existing 0.4 compatibility
limits and retained historical evidence below still apply.

## Previous publication: 0.4.1

**[PKStack v0.4.1](https://github.com/njs14/pkstack/releases/tag/v0.4.1) was
published on September 6, 2026 at 14:27:18 UTC.** It includes the measured
knowledge-link parsing improvement and corrects stale knowledge-runtime,
IDE-evidence, diagram, and release-tag guidance. Public interfaces and 0.4
compatibility limits are unchanged. See the
[changelog](../CHANGELOG.md#041--2026-09-06).

[PR #46](https://github.com/njs14/pkstack/pull/46) merged the release preparation
at `db80f37d5f5d5934076b53da449cf726eac09b39`; tag `v0.4.1` points to that commit.
Independent reviewer `release_041_review` approved candidate
`70e92d3675299550b6ea659a53137578cefcdc37` with no unresolved findings, and the
merged tree was byte-identical. Both the
[final PR CI](https://github.com/njs14/pkstack/actions/runs/34038811915) and
[exact main CI](https://github.com/njs14/pkstack/actions/runs/34038973111) passed
all 12 jobs. This review used a Codex reviewer; no new external Fable or Grok
review is claimed.

Local checks passed: 22 fast-contract tests, 4 release-metadata tests, and 13
branding/walkthrough tests. The additional release-guide correction passed all
12 branding tests. Reviewed setup refreshed only the three expected version
files and their receipt hashes; the next setup preview reported zero changes.
Doctor reported 84 passes, zero failures, and zero warnings. Feature and local
knowledge validation passed. The reviewer checked all eight version mirrors,
all 178 bootstrap hashes, the diagram delivery hashes, and changed local links.

The [release workflow](https://github.com/njs14/pkstack/actions/runs/34039169146)
passed verification and publication, promoting artifact `9991083814` from main
run `34038973111`, attempt 1. Its artifact ZIP SHA-256 was
`b940c00590dbd25fdb2ce4ad51913cfe35e136f3cdd0f9fd38c4fa7a310f8ee1`.
The published 4,590,538-byte archive was downloaded and compared byte-for-byte
with the verified CI package; its checksum file also matched. The archive
SHA-256 is:

```text
5f09ffa3006b91acdde54824aafd9700871004efe938b009aa79638f42560fd8
```

The extracted-package consumer passed setup, idempotence, version checks,
feature and local knowledge validation, and a fixed-verifier failure/repair/pass
loop. Its doctor reported 78 passes, zero failures, and one warning because the
secretless package job does not install optional Kiro CLI. The local pre-tag
verification passed after correcting its output argument to a new path; the
first invocation rejected an already-created output directory. The package
bytes were unchanged. No new live Kiro retrieval campaign was run for this
patch; the retained 0.4 compatibility evidence and limits below still apply.

## Previous publication: 0.4.0

The knowledge foundation is merged through [PR #42](https://github.com/njs14/pkstack/pull/42)
at `8439078f279f5980c1c5123c21223253d16393f0`. Its
[main CI](https://github.com/njs14/pkstack/actions/runs/34031372725) passed all
12 jobs. [v0.3.0](https://github.com/njs14/pkstack/releases/tag/v0.3.0) was
published September 5, 2026; the previous pre-publication checkpoint is retained
in [the historical report](historical/v0.3-release-status.md).

**[PKStack v0.4.0](https://github.com/njs14/pkstack/releases/tag/v0.4.0) was
published on September 6, 2026 at 12:15:50 UTC.** It packages the knowledge
foundation with refreshed diagrams, matching version mirrors, and the
[0.4 upgrade guide](../powers/pkstack/docs/upgrade-0.4.md).

[PR #43](https://github.com/njs14/pkstack/pull/43) merged the release preparation
at `12ecc1abe6a59c57bb91260d9f4a8cb06651291a`. Both its
[corrected PR CI](https://github.com/njs14/pkstack/actions/runs/34032262810) and
[exact main CI](https://github.com/njs14/pkstack/actions/runs/34032394630) passed
all 12 jobs. Two packaging expectations that hard-coded 0.3.0 were corrected to
read the Power manifest before those passing runs.

The [release workflow](https://github.com/njs14/pkstack/actions/runs/34032537285)
passed both verification and publication. It promoted CI artifact `9989055024`
from main run `34032394630`, attempt 1. The published 4,589,525-byte archive was
downloaded and compared byte-for-byte with the verified CI package; its checksum
file also matched. The archive SHA-256 is:

```text
6d94eebc69b4ab417aa915f350bf6e9994763a38dc3c180c7731fe1a43989716
```

The [publication receipt](release-040-publication.json) records the immutable
commit, run, artifact, and digest bindings. The extracted consumer passed setup,
idempotence, feature and local knowledge validation, and a fixed-verifier
failure/repair/pass loop. Its doctor summary reported 78 passes, zero failures,
and one warning; this secretless package job does not install optional Kiro CLI.
The original full repository doctor result below is a separate environment.

### Retained 0.4 compatibility evidence

- The [knowledge acceptance report](knowledge-foundation.md) records 953 passing
  Power tests, 222 repository Python tests, 17 Node tests, 84 doctor checks,
  generated parity, local knowledge validation, and independent final approval.
- The [Linux canary](https://github.com/njs14/pkstack/actions/runs/34031637810)
  passed on the merged foundation with official stable Kiro CLI 2.21.1. It checks
  exact version, native workspace-agent discovery, and authenticated model
  inventory without a model turn.
- Live knowledge retrieval remains verified on macOS with Kiro CLI 2.21.1 and
  KAS 0.58.7. Linux controller/process tests and the runtime canary do not prove
  a complete Linux knowledge query. A Linux-native authenticated retrieval and
  isolation campaign remains required before making that broader claim.
- The [official stable CLI manifest](https://prod.download.cli.kiro.dev/stable/latest/manifest.json) still reports 2.21.1 as of September 6, 2026.
  No newer stable version exists to qualify at this checkpoint. Windows lacks
  the POSIX process-isolation contract and remains unsupported for retrieval.
- Quotations are checked against snapshots; generated prose and inference can
  still be imperfect. Local validation checks structure and links without a model.

The repository remains private. The autonomous updater stays enabled with its
existing isolated-test, independent-review, and exact-commit merge gates.
