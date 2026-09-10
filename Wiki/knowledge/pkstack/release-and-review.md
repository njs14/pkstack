---
type: Guide
title: Release evidence and review decisions
description: How candidate identity, executable gates, independent review, and publication evidence differ.
tags: [pkstack, release, review, evidence, provenance]
---

# Release evidence and review decisions

## Evidence has an identity and a scope

The Power manifest supplies release version authority. Package metadata, source version, lockfiles,
and generated mirrors must agree with it. GitHub Releases and their attached publication receipts
are the publication record. The [Wiki release record](release-record.md) preserves historical
entries; older reports remain historical even if their original prose says “current,” “blocked,”
or “accepted.” Neither this Wiki nor a manifest hash is a release verdict. The coverage manifest
proves which source bytes were considered, not that the source's claims are true.

A useful evidence packet binds source commit or a complete content manifest, runtime/client,
commands, outputs and exit status, preservation hashes, reviewer scope, and unresolved limits.
A base commit does not identify uncommitted candidate bytes. Separate operator-authored actions
from native model actions and command execution from documentation or menu recognition. A
reviewer who only reads code has not rerun coordinator-provided tests.

## Consumer Power and maintainer material

The v0.5.6 cleanup keeps `powers/pkstack/` as the sole installable source. Tests and
fixtures live in root `tests/`, benchmarks in `benchmarks/`, review contracts and
preserved reports in `reviews/`, and maintainer explanations, diagrams, and historical
artwork in `docs/`. This relocates the former Power review harness; it does not restore
the older root archive retired during the knowledge migration. Existing historical
reports keep their bytes and scope, even where their original relative paths describe
the former package layout. Their Wiki summaries link to the relocated evidence.

The repository-owned [package-content contract](../../../maintenance/package-content.json)
lists every consumer file. Packaging checks all source files and directories, including
ignored clutter, and checks the archive against the same list. Missing skills, notices,
logo, or required runtime resources fail just as unexpected tests, reports, virtual
environments, and caches do. The approved archive still passes deterministic byte
comparison and the extracted-consumer setup, idempotence, doctor, feature/knowledge,
and stored fail-repair-pass checks. Consumer guides link repository-only material by
GitHub URL so release-local links stay within the extracted Power.

## Review and release procedure

Run applicable deterministic checks, review the frozen candidate, reproduce material findings,
make scoped corrections, and return the changed scope to checks and review. Preserve failed runs
and concrete diagnostics. Do not retry until green without explaining what changed. Missing,
cancelled, stale, or unexpectedly skipped checks are not passes. The
[quality and CI guide](quality-and-ci.md) explains the shared verification job and execution summary.

Reviewer output is untrusted analysis. Use tight source references, a failure mode, and an
acceptance test; investigate disagreements instead of treating model agreement as authority.
Historical Fable/Grok prompts demonstrate read-only review and finding-led remediation, but some
still name pre-0.3 paths, retired `okn`, or old product identities. Reuse the method only after
reconciling the contract with the current Power and caller's request. Do not load an old prompt as
current operational policy merely because it is linked here.

Put version changes and release notes in the change PR when a release is intended. Use focused
local checks during development. Successful hosted PR and main checks satisfy their corresponding
release requirements; do not rerun complete local gates on the candidate, release branch and
merged source. When hosting is unavailable, one complete local gate validates the finished scope,
but it does not create main-CI artifact evidence.

Obtain one independent review of the final changed scope. Carry that review across a squash merge
only after verifying identical complete Git source trees. Compare `git rev-parse <candidate>^{tree}`
and `git rev-parse <merged>^{tree}`; a Power-only comparison misses repository controls. Substantive
changes need review of the delta and appropriate checks. The
[contributor procedure](../../../CONTRIBUTING.md#releases) keeps these boundaries explicit.

Main CI builds the reproducible release archive after `deterministic` succeeds. Tag-bound
verification requires both jobs, the exact source/workflow/run attempt/artifact, matching version
authorities and a current tag/main identity. Publication promotes the verified artifact without
rebuilding it. `pkstack_ci_package.py verify-published` downloads the published archive and checksum,
compares bytes and SHA-256 to the approved CI package, rechecks the CI attempt, release, assets,
tag and main, then writes a successful publication receipt. The workflow attaches that receipt
to the release. Altered, absent or replaced assets cannot receive a successful receipt.

Release verification accepts the expected public or private repository, with consistent
visibility metadata. Repository ID, full name, default branch, and every source/run/tag/artifact
identity remain mandatory; public access does not make another repository a trusted producer.

For an explicitly owner-authorized manual release while Actions is unavailable, retain the
hosted gates as unavailable and attach a separately labeled `local-release-receipt.json`.
Bind the complete local gate and independent review to the frozen candidate, prove complete
tree equality with merged main, build identical archive bytes twice, and run the extracted
consumer checks. Compare the draft and published assets with those exact local bytes and
record the publication identities. This local provenance does not replace hosted main-CI
artifact evidence or allow the hosted verifier to accept a missing run. Usage limits and
fresh live Kiro behavior remain outside that local proof.

A GitHub Release without its successful attached receipt is incomplete publication evidence.
GitHub Releases and receipts replace the separate publication-record PR and extra CI cycle;
preserve historical Wiki entries. For example, the retained
[0.4.0 publication receipt](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-040-publication.json)
proves only that recorded publication. These instructions do not refresh its remote state.

Live Kiro diagnostics remain separate: new live evidence is required when a change affects the
behavior being claimed, rather than repeating the entire diagnostic campaign for every release.
Routine release work must not dispatch extra maintenance attempts after the two-repair budget is
exhausted. Daily scheduling and source-bound rejection feedback remain responsible for recovery.

## 0.7.0 guide and compatibility release scope

The [version notes](../../../CHANGELOG.md) combine the project-aware advisor and
empty primary-profile v3 compatibility marker with the already merged permission,
Wayfinder, router-renaming, and artwork work. The guide targets
`poteto-kiro-mode`; the selected workspace agent remains `pkstack`. Reconciliation
preserves the current upstream catalog and setup-owned generated files.

The release requires exact-candidate local checks, independent review, complete-tree
merge comparison, reproducible packaging, extracted-consumer checks, and downloaded
publication-byte verification. GitHub Actions remain manually disabled; this scope
does not assert a hosted pass or publication before those steps complete. The
[native guide observations](native-kiro-composition.md#september-10-guide-observations-and-limits)
retain their behavioral gaps and do not establish release-wide CLI or IDE acceptance.

## 0.6.0 engineering integration scope

The [version notes](../../../CHANGELOG.md) describe eight newly discoverable engineering skills,
four methods consolidated into existing owners, complete Pocock catalog accounting, and the
repository dependency refresh. Package version 0.6.0 expresses the added consumer capabilities.
The release still requires the frozen candidate's local checks, independent review, complete-tree
merge comparison, reproducible archive, extracted-consumer validation, and published-byte receipt.
These scope notes do not assert that those checks or publication have already completed.

## September 7 verification review candidate

[PR #69](https://github.com/njs14/pkstack/pull/69) holds a scoped 0.5.3 guidance, repository-control and evidence
candidate against `3a370aa92d881ea8bab48c4b55c70cad347c49b7`. Its
[structured packet](evidence/2026-09-07/verification.json) contains the initial diagnostic
reproduction, regression dispositions, executable consumer fixtures, native-session identities,
browser assertions and screenshot hashes. The PR description supplies the final commit/tree and
its exact CI run/attempt after packet preparation; the evidence file does not claim to contain
its own eventual commit identity.

The reproduced repair distinguishes safe detector execution errors from malformed inventories,
while preserving rejection and withholding arbitrary error text. That repair changes repository controls. A subsequent native continuation exposed a second
finding: `check` mode ran a metadata-writing Git fetch. The 0.5.3 Power clarifies that remote
freshness uses forge API reads, local status/diff disables optional locks, and fetch variants
remain writes. Its regression scenario covers continuation with stale or absent tracking refs.
The original diagnostic-only checkpoint is superseded; no tag or publication is implied.
Native demonstration implementations remain consumer evidence, not product changes. The packet distinguishes operator setup and predicates,
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
The [artwork guide](../../../docs/assets/creation-history.md) identifies the current
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
| [docs/validation-report.md](../../../docs/validation-report.md) | Release procedure requires candidate-bound metadata, checks, generated parity, native evidence where required, independent review and separate publication gates. |
| [reviews/README.md](../../../reviews/README.md) | The repository review harness separates source inspection from executable checks and recommends immutable evidence packets with bounded reviewer tools. |
| [reviews/fable-review-prompt.md](../../../reviews/fable-review-prompt.md) | The historical acceptance prompt supplies reproducible finding and trust-boundary methods, but its old brand/namespace assumptions are not current Power interfaces. |
| [reviews/grok-review-prompt.md](../../../reviews/grok-review-prompt.md) | Independent advisory review preserves dissent and exact findings without implementation or inherited verdicts; historical compatibility names must not override current code. |
| [reviews/fable-final.md](../../../reviews/fable-final.md) | The ACCEPT applies to snapshot 1a145d4 and records residual receipt/cache and non-sandbox limits; a reader-only review did not execute the claimed tests. |
| [reviews/historical/pre-v0.2/README.md](../../../reviews/historical/pre-v0.2/README.md) | Archived package review records retain original candidate/runtime scope and cannot stand in for a fresh review. |
