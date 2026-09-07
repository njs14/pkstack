---
type: Record
title: Published releases and acceptance evidence
description: Retained publication identities, checksums, and scope for PKStack releases.
tags: [pkstack, release, evidence]
---

# Published releases and acceptance evidence

This record retains exact release identities, checksums, and acceptance scope. The 0.5.0
entry records fresh publication verification; earlier entries retain the facts reported before
the root reviews directory was removed. The Power manifest remains version authority.
Future release work updates this record and the [changelog](../../../CHANGELOG.md),
following the [release evidence contract](release-and-review.md).

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
