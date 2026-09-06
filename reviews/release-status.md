---
release: "0.4.0"
status: release-preparation
version_authority: powers/pkstack/plugin.json
---

# PKStack release status

The knowledge foundation is merged through [PR #42](https://github.com/njs14/pkstack/pull/42)
at `8439078f279f5980c1c5123c21223253d16393f0`. Its
[main CI](https://github.com/njs14/pkstack/actions/runs/34031372725) passed all
12 jobs. [v0.3.0](https://github.com/njs14/pkstack/releases/tag/v0.3.0) was
published September 5, 2026; the previous pre-publication checkpoint is retained
in [the historical report](historical/v0.3-release-status.md).

Version 0.4.0 packages that implementation with refreshed diagrams, matching
version mirrors, and a [0.4 upgrade guide](../powers/pkstack/docs/upgrade-0.4.md).
Publication is authorized by the owner. The release-preparation commit still
requires its own passing PR and main CI, followed by tag-bound promotion of
that exact main artifact. The release workflow rechecks the source run,
artifact identity, archive checksum, and version-specific notes before publishing.
The [v0.4.0 release record](https://github.com/njs14/pkstack/releases/tag/v0.4.0)
and its workflow are the authority for terminal publication status.

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
