---
release: "0.4.1"
status: candidate
version_authority: powers/pkstack/plugin.json
---

# PKStack release status

PKStack 0.4.1 is the current release candidate. It includes the measured
knowledge-link parsing improvement and corrects stale knowledge-runtime,
IDE-evidence, and diagram guidance. Public interfaces and 0.4 compatibility
limits are unchanged. See the [changelog](../CHANGELOG.md#041--2026-09-06).

Publication requires passing PR and exact-main CI, independent review, and the
existing release workflow's verification of the unchanged main CI package.
The candidate is not yet published. The current published release remains 0.4.0.

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

## Evidence and compatibility

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
