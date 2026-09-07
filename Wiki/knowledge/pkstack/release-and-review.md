---
type: Guide
title: Release evidence and review decisions
description: How candidate identity, executable gates, independent review, and publication evidence differ.
tags: [pkstack, release, review, evidence, provenance]
---

# Release evidence and review decisions

## Evidence has an identity and a scope

The Power manifest supplies release version authority. Package metadata, source version, lockfiles,
and generated mirrors must agree with it. [the Wiki release record](release-record.md) is the maintained release-record
entrypoint; older reports remain historical even if their original prose says “current,” “blocked,”
or “accepted.” Neither this Wiki nor a manifest hash is a release verdict. The coverage manifest
proves which source bytes were considered, not that the source's claims are true.

A useful evidence packet binds source commit or a complete content manifest, runtime/client,
commands, outputs and exit status, preservation hashes, reviewer scope, and unresolved limits.
A base commit does not identify uncommitted candidate bytes. Separate operator-authored actions
from native model actions and command execution from documentation or menu recognition. A
reviewer who only reads code has not rerun coordinator-provided tests.

## Review and release procedure

Run applicable deterministic checks, review the frozen candidate, reproduce material findings,
make scoped corrections, and return the changed scope to checks and review. Preserve failed runs
and concrete diagnostics. Do not retry until green without explaining what changed. Missing,
cancelled, stale, or unexpectedly skipped checks are not passes. The
[quality and CI guide](quality-and-ci.md) explains the shared lane and receipt system.

Reviewer output is untrusted analysis. Use tight source references, a failure mode, and an
acceptance test; investigate disagreements instead of treating model agreement as authority.
Historical Fable/Grok prompts demonstrate read-only review and finding-led remediation, but some
still name pre-0.3 paths, retired `okn`, or old product identities. Reuse the method only after
reconciling the contract with the current Power and caller's request. Do not load an old prompt as
current operational policy merely because it is linked here.

Publication requires its own exact-source gates. Main CI builds the reproducible release archive;
tag-bound verification checks the manifest version, source commit/run/artifact, and publication
eligibility. Compare downloaded release bytes/checksum with the approved CI artifact. A green PR,
merge, or local fixture is not this publication proof. The retained
[0.4.0 publication receipt](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-040-publication.json), for example, binds
commit `12ecc1abe6a59c57bb91260d9f4a8cb06651291a`, its main artifact, tag workflow, and byte
comparison. It proves only that recorded publication; this curation does not refresh remote state.

## September 7 verification review candidate

[PR #69](https://github.com/njs14/pkstack/pull/69) holds a repository-control and evidence
candidate against `3a370aa92d881ea8bab48c4b55c70cad347c49b7`. Its
[structured packet](evidence/2026-09-07/verification.json) contains the initial diagnostic
reproduction, regression dispositions, executable consumer fixtures, native-session identities,
browser assertions and screenshot hashes. The PR description supplies the final commit/tree and
its exact CI run/attempt after packet preparation; the evidence file does not claim to contain
its own eventual commit identity.

The reproduced repair distinguishes safe detector execution errors from malformed inventories,
while preserving rejection and withholding arbitrary error text. It changes repository controls,
not the installable Power. Power version 0.5.2 and its source tree remain unchanged; no product
version bump, product RC label or tag is warranted. Native demonstration implementations remain
consumer evidence, not product changes. The packet distinguishes operator setup and predicates,
model-authored repairs and independent browser assertions.

Two live requirements remain unresolved: trusted-main unattended maintenance did not produce a
validated detector/proposal/verdict, and an authorized Linux environment with working supported
Kiro authentication was not established. The maintenance failure's initiating payload was not
retained, and a separate local HTTP 403 must not be assigned as its cause. The diagnostic repair
requires exact independent acceptance and merge before changed trusted-main reproof. Deterministic
acceptance/rejection/feedback/cleanup tests remain separate from unobserved live outcomes.

Independent acceptance is requested from the original Claude Code session
`270ac4ba-5584-4c07-a7a9-c0fc59deb6bb`, model `claude-fable-5-1`, bound to the final PR head/tree.
One supported availability turn returned `AVAILABLE`; that is not review or acceptance.
The reviewer should assess the failure boundary and meaningful regressions, source equivalence,
evidence attribution and explicit remaining prerequisites, stating which checks were rerun.
A correction needs independent review of its changed bytes. The final candidate stays unmerged,
untagged and unpublished pending that acceptance; preparation is not overall release completion.

## Historical findings worth reusing

- Early selected-profile campaigns distinguish generic Kiro execution from actual use of the
  shipped permission profile. Record the selected profile and concrete ask/deny behavior.
- The 0.3 release included explicit GUI acceptance waivers. A waiver is an assumption, not a
  fresh IDE pass. Keep it visible alongside the fixture results it permits delivery to rely on.
- The 0.4.3 planning reports contain a sequence of failures and bounded superseding observations.
  Read the [planning history](native-kiro-composition.md#retained-planning-observations) instead
  of taking the first “blocked” label or last “pass” label as a universal result.
- The 0.4.4 metadata review approved a frozen metadata change; it did not itself publish the
  release. The release record separately retains tag-bound publication evidence.
- Naming cleanup found rewritten historical rationales and broken consolidation links. Preserve
  original transition arrays and source identities when changing current product terminology.

## Current policy and historical records

[SECURITY.md](../../../SECURITY.md) maintains current `main` / the 0.5
release line, with no commitment to backport fixes to older lines. Knowledge
validation is local; bounded Kiro ACP retrieval is a separate capability.
Historical acceptance ledgers retain their original versions and paths.
The [artwork guide](../../../powers/pkstack/assets/README.md) identifies the current
four-ghost logo and separates the earlier banner and mascot history.

## Carry acceptance across changes only with an explicit binding

The [onboarding evidence](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/onboarding-042/README.md#evidence-and-candidate-binding)
binds unchanged first-task, installer, runtime, skill, fixture, and template objects across a later
documentation edit. It does not call the whole changed Power tree identical. The
[uvx follow-up review](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/uvx-entrypoint/grok-followup.md) likewise retains approval
of unchanged launcher code while separately reviewing the cold-cache test correction. Identify
exactly which prior evidence still applies, then verify the changed scope and final hosted head.
A prior full pass is not silently rebound to a later commit.

The [0.3 acceptance record](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-030-acceptance.md) keeps waived GUI work beside
completed checks. The [final review](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-030-review.md) still found grouped
Git option forms missed by earlier permission testing; the bounded native repair did not become
complete shell containment. A review should look for counterexamples to the actual promise, not
just repeat existing green tests. Preserve initial failures and reviewer disagreement even after
remediation so the next maintainer can see why the narrower contract exists.

The [identity audit](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/pkstack-identity-validation.md) shows why cleanup also needs
an evidence boundary: product renaming had changed historical acceptance rationale and broken
consolidated links. Update live terminology and repair links, while preserving original source
identities and transition arrays. Historical support wording and frozen reports may remain stale;
label their role rather than rewrite them into a current acceptance claim.

Across these campaigns, a useful review conclusion answers four questions: which candidate and
behavior were examined, what concrete failure or counterexample was found, what observation
supports its disposition, and what remains unverified. This topic synthesis carries those lessons;
original reports retain the full chronology, exact hashes, commands, and preserved failures.

## Source-specific retained knowledge

These summaries describe what is retained from each source. Historical observations keep their
original candidate and scope; they are not fresh verification of this checkout.

| Source | Retained guidance or bounded observation |
| --- | --- |
| [CHANGELOG.md](../../../CHANGELOG.md) | Versioned notes summarize changes but the Power manifest is metadata authority; source reviews, merged changes and publication receipts are separate gates. |
| [SECURITY.md](../../../SECURITY.md) | Current main / the 0.5 release line is maintained without older-release backport commitments; local validation and Kiro ACP retrieval have separate trust boundaries. |
| [reviews/README.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/README.md) | Current release status is the release-record entrypoint; historical reports and the separate Floci lab cannot accept a different PKStack candidate. |
| [reviews/acceptance-ledger.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/acceptance-ledger.md) | This stable compatibility link still names v0.2 and old paths; follow release-status.md for current records rather than treating the alias wording as current metadata. |
| [reviews/historical/pre-v0.2/README.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/historical/pre-v0.2/README.md) | Archived pre-0.2 evidence preserves original identities and limitations and cannot establish acceptance of later candidates. |
| [reviews/historical/v0.2-release-status.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/historical/v0.2-release-status.md) | Archived v0.2 tag-derived/pending status is historical despite internal current wording; do not carry its labels forward to later releases. |
| [reviews/historical/v0.3-release-status.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/historical/v0.3-release-status.md) | Archived v0.3 candidate checkpoint predates its publication and preserves assumptions and uncompleted checks without replacing the later publication record. |
| [Wiki release record](release-record.md) | Release records bind version, exact candidate, CI/tag runs and archive comparison; copied status is not a fresh remote check or acceptance of this knowledge expansion. |
| [reviews/release-044-review.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-044-review.md) | Grok approved metadata-only 6a78b19 against 5a905eb; matching mirrors and coordinator evidence did not themselves authorize or perform publication. |
| [reviews/release-030-acceptance.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-030-acceptance.md) | Acceptance used explicit bounded coverage and GUI waivers; waived native checks are assumptions, not new passing observations or publication authorization. |
| [reviews/release-030-core.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-030-core.md) | Standard planning, legacy installation refusal and local knowledge checks were recorded for specific 0.3 candidates, separate from helper/pipeline edits and publication. |
| [reviews/release-030-review.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-030-review.md) | Independent frozen-candidate review found grouped-option permission gaps and reviewed their correction; later scoped reviews and GUI assumptions remain separately attributable. |
| [reviews/pkstack-identity-validation.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/pkstack-identity-validation.md) | Naming cleanup repaired links and restored altered historical transition rationales; current naming must not rewrite provenance or treat naming checks as functional proof. |
| [reviews/cleanup-validation.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/cleanup-validation.md) | Cleanup removed obsolete schema/cache machinery and corrected cancellation/environment/retry handling based on observed failures; unfinished native gates remained failures or limits. |
| [reviews/fable-review-prompt.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/fable-review-prompt.md) | Retains the method of read-only exact-candidate review with stable findings and acceptance tests; old paths, okn and product-contract wording need reconciliation before reuse. |
| [reviews/grok-sweep-prompt.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/grok-sweep-prompt.md) | Adversarial sweep checks containment, evidence identity and unsupported claims independently; historical command/backend names are not current instructions. |
| [powers/pkstack/docs/validation-report.md](../../../powers/pkstack/docs/validation-report.md) | Release procedure requires candidate-bound metadata, checks, generated parity, native evidence where required, independent review and separate publication gates. |
| [powers/pkstack/reviews/README.md](../../../powers/pkstack/reviews/README.md) | The package review harness separates source inspection from executable checks and recommends immutable evidence packets with bounded reviewer tools. |
| [powers/pkstack/reviews/fable-review-prompt.md](../../../powers/pkstack/reviews/fable-review-prompt.md) | The historical acceptance prompt supplies reproducible finding and trust-boundary methods, but its old brand/namespace assumptions are not current Power interfaces. |
| [powers/pkstack/reviews/grok-review-prompt.md](../../../powers/pkstack/reviews/grok-review-prompt.md) | Independent advisory review preserves dissent and exact findings without implementation or inherited verdicts; historical compatibility names must not override current code. |
| [powers/pkstack/reviews/fable-final.md](../../../powers/pkstack/reviews/fable-final.md) | The ACCEPT applies to snapshot 1a145d4 and records residual receipt/cache and non-sandbox limits; a reader-only review did not execute the claimed tests. |
| [powers/pkstack/reviews/historical/pre-v0.2/README.md](../../../powers/pkstack/reviews/historical/pre-v0.2/README.md) | Archived package review records retain original candidate/runtime scope and cannot stand in for a fresh review. |
