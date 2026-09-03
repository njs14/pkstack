---
release: "0.2.0"
status: pending
version_authority: powers/pk-stack/plugin.json
tag: v0.2.0
---

# PK-Stack v0.2.0 release status

This is the single current release-status surface for the repository. It is
keyed to the `version` field in [`powers/pk-stack/plugin.json`](../powers/pk-stack/plugin.json).
The package metadata, source `__version__`, and shipped lockfiles must equal
that value. The release is not accepted until the exact reviewed commit is
tagged `v0.2.0`.

## Current state

**Pending final candidate review.** This document intentionally does not turn
older test runs, Kiro sessions, upstream campaigns, or reviewer reports into a
new release verdict. Set the candidate commit below only after the final tree
is frozen and its gates have run.

| Field | Value |
| --- | --- |
| Manifest authority | `powers/pk-stack/plugin.json` |
| Manifest version | `0.2.0` |
| Required tag | `v0.2.0` |
| Candidate commit | pending final freeze |
| Release status | pending |
| Floci status | separate private consumer repository |

## Required gates for the final candidate

| Gate | Required record | Status |
| --- | --- | --- |
| Metadata | Manifest, package metadata, source version, and lock mirrors are equal | rerun on final candidate |
| Power checks | Lock, lint, format, type check, and complete package tests | rerun on final candidate |
| Workspace checks | Clean setup/doctor and generated-byte parity | rerun on final candidate |
| Feature and knowledge | `feature validate`; optional `okn` result clearly labeled | rerun on final candidate |
| Repository checks | Guard, policy, Actionlint, ShellCheck, and documentation/link checks | rerun on final candidate |
| Kiro evidence | Exact-candidate credential/runtime evidence where required | pending |
| Independent review | Fable 5.1 `xhigh`; Grok 4.6 `xhigh` sweep or explicit blocker | pending |
| Publication | Private PR head equals the reviewed candidate; tag points to that commit | pending |

Use the exact command, commit, exit code, and limitation for each gate. A
historical artifact can explain provenance or a known boundary, but it cannot
close a gate for a different commit.

## Release sequence

1. Freeze a clean candidate and record its commit here.
2. Verify `plugin.json` first, then compare every public/version mirror.
3. Run deterministic package, workspace, repository, feature, and knowledge
   checks. Keep missing optional tools as explicit limitations.
4. Run the required independent reviews against that exact candidate. Re-run
   affected checks after every material change.
5. Open the private pull request and confirm its head equals the reviewed
   candidate.
6. Create `v0.2.0` only after the recorded gates are complete; then update this
   document with the tag commit and final verdict.

No step in this document changes GitHub settings or enables a workflow.

## Historical evidence

Pre-0.2 evidence is indexed in
[`historical/pre-v0.2/`](historical/pre-v0.2/). Those records retain their
original source identities and limitations for provenance. The separate
private [pk-stack-floci-lab](https://github.com/njs14/pk-stack-floci-lab)
repository owns the Floci application and live campaigns; no Floci artifact is
part of this Power release.
