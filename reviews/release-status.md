---
release: "0.2.0"
status: tag-derived
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

**Candidate gates are green; publication remains tag-derived.** Git cannot put
a commit's own SHA inside that commit. The immutable release identity is
therefore the commit resolved by `v0.2.0^{commit}`. Before the tag exists this
tree is a candidate. After the private PR and exact-tag workflow pass, the tag
commit is the release record and the released artifact authority.

| Field | Value |
| --- | --- |
| Manifest authority | `powers/pk-stack/plugin.json` |
| Manifest version | `0.2.0` |
| Required tag | `v0.2.0` |
| Reviewed content baseline | `800ef927d8787477c2ac7efa68ce7b529038c929` |
| Release commit | `v0.2.0^{commit}` after publication; must equal default-branch HEAD |
| Release status | candidate until the tag workflow succeeds; released afterward |
| Floci status | separate private consumer repository |

## Required gates for the final candidate

| Gate | Required record | Status |
| --- | --- | --- |
| Metadata | `uv lock --check`; release-metadata regression | pass |
| Power checks | Ruff lint/format, ty, complete package suite | pass: 796 tests |
| Workspace checks | Managed refresh, doctor, generated-controller parity | pass |
| Feature and knowledge | Source map plus fresh consumer map; canonical `okn` 0.13.0 | pass; source Wiki retains 3 intentional cross-repository link warnings |
| Repository checks | 76 guard, 25 canary, 8 inventory, 6 stream, 17 policy tests; Actionlint; ShellCheck | pass |
| Kiro evidence | Kiro CLI 2.21.0 v3 Luna low current-session skill discovery | pass on content baseline; repeat after final freeze |
| Independent review | Fable unavailable; Opus 5 `xhigh` substitution and Grok 4.6 `xhigh` sweep | material findings remediated; exact-head Opus re-review required |
| Publication | Private PR head equals the reviewed candidate; tag points to that commit | pending |

The Fable 5.1 `xhigh` attempt ended before review because the subscription was
out of credits until Tuesday. It is an explicit external limitation, not an
acceptance result. The authorized Opus 5 `xhigh` substitute requested changes
on `800ef927...`; its documentation findings are fixed. Grok identified one
candidate-workflow secret-confinement guard gap; direct, alias, merge-key,
tag, quote-decoding, relocation, and computed-secret mutations are now
negative tests. A fresh Opus review must accept the final PR head before the
tag is created.

Use the exact command, commit, exit code, and limitation for each gate. A
historical artifact can explain provenance or a known boundary, but it cannot
close a gate for a different commit.

## Release sequence

1. Freeze a clean candidate and retain its exact commit in the PR and review evidence.
2. Verify `plugin.json` first, then compare every public/version mirror.
3. Run deterministic package, workspace, repository, feature, and knowledge
   checks. Keep missing optional tools as explicit limitations.
4. Run the required independent reviews against that exact candidate. Re-run
   affected checks after every material change.
5. Open the private pull request and confirm its head equals the reviewed
   candidate.
6. Create `v0.2.0` only after the recorded gates are complete. The release
   workflow requires the tag commit to equal default-branch HEAD and reruns the
   complete deterministic release gate before publishing.

No step in this document changes GitHub settings or enables a workflow.

## Historical evidence

Pre-0.2 evidence is indexed in
[`historical/pre-v0.2/`](historical/pre-v0.2/). Those records retain their
original source identities and limitations for provenance. The separate
private [pk-stack-floci-lab](https://github.com/njs14/pk-stack-floci-lab)
repository owns the Floci application and live campaigns; no Floci artifact is
part of this Power release.
