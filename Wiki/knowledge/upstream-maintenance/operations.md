---
type: Guide
title: Upstream maintenance operation and recovery
description: Source-scoped proposals, trusted review, rejection budgets, and drift recovery.
tags: [upstream-maintenance, operations, review, safety]
---

# Upstream maintenance operation and recovery

## One source is one acceptance transaction

The [accepted decisions](decisions.md) separate observation, proposal, and authorized acceptance.
The deterministic controller selects one changed imported subtree. A remote commit outside that
subtree is informational and must not consume model credits or move its pin. A proposal accounts
for each changed path and its disposition; accepting it atomically advances only that source's
pin and review ledger. Other drifting sources remain deferred and byte-identical.

The source manifest, parity inventories, accepted ledger and latest rejection feedback have
different roles. Do not rewrite historical rationale or genesis markers when adding a transition.
`retrieved_on` comes from the trusted inventory retrieval date, not the model's clock or an old
baseline. When a proposed change only rephrases an unchanged safety exclusion, preserve the
existing rationale and place the new delta explanation in the new proposal/provenance entry.

## Credential and review boundary

The updater uses Kiro for hosted model work. Candidate code receives neither the Kiro credential
nor a GitHub write token. Trusted preparation constructs the exact bounded review bundle; the
isolated no-tool reviewer and secretless tests have separate authority. Approval must bind the
tested base/head, agent, source identities, patch and context digests. GitHub App acknowledgements
or missing comments cannot substitute for the mandatory review.

Skill review includes relevant neighbors, shared steering and trusted-base routing scenarios.
Missing coverage, invalid context, or exceeding the 64 KiB bundle cap stops automation; do not
silently truncate evidence to manufacture approval. Requested model effort is not independently
attested by stream metadata. A successful canary inventory is not a model task or a release gate.

## Stops and recovery

Three substantive rejections exhaust a source/content budget. Infrastructure failures and malformed
or unauthenticated reports do not spend that budget; an early rejection is persisted only once
candidate tests pass. Feedback retains one latest validated report and count, with immutable
source/candidate identity. Cleanup waits for active tests/review. If feedback cannot be persisted,
leave the candidate open rather than discarding its rejection history.

A fresh active candidate suppresses another run; stale or orphaned open candidates need operator
recovery. Generated-only drift produces `manual-parity`: regenerate from reviewed source rather
than ask a model to repair known output. Explicit retry requires the currently exhausted
`source-id@current-subtree-sha`; a generic request or different subtree is not authorization to
reset a budget. Inspect and address the latest failure before using that override.

The Kiro product canary is observation-only. It fails when the advertised runtime differs from
the reviewed tuple, withholding authenticated inventory until the pin matches. It does not
promote its own runtime or edit protected controls. Preserve the configured workflow filename as
its GitHub identity even though it retains older spelling. Schedule configuration does not prove
that a workflow is enabled or that the latest run completed.

## Knowledge changes travel with the source update

The updater may propose related durable Wiki Markdown and coverage entries alongside its allowed
source documentation edits. The trusted checker runs after finalizer regeneration and again in
candidate tests using the immutable base's implementation. It compares with the trusted base:
unrelated entries stay unchanged, existing classifications and mapped topics cannot be dropped,
and exclusions cannot be broadened. A changed topic must be linked from a changed mapped source.
New authored guides require mapped understanding; native skill resources keep native ownership.
The historical corpus inventory and migration report remain protected.

The agent has no shell tool for calculating hashes. Failed private verification reports the
observed `current_sha256` for each stale source, including regenerated copies. A later bounded
repair may use those values after reviewing the source and topic; the checker never rewrites
the manifest. Independent review assesses the changed source, Wiki explanation and coverage
summary together. Missing context is an unresolved finding, and matching hashes alone cannot
justify semantic approval. No broader runtime/code/policy permissions or spending budget is added.

## Historical diagnostics

The earlier proposal failure did not retain its initiating inner cause. A separate real prompt
defect referred to `drift_count` in the wrong JSON object; later code used the controller plan and
allowlisted diagnostic reasons. This explains the repair without inventing the original cause.
Other campaigns reproduced combined-context cap discrepancies, a trusted two-file cleanup error,
and retry/feedback handling failures. Keep each repair bound to its recorded test or live campaign.
The 0.3 live acceptance results and the earlier successful source-scoped goal do not establish
today's updater health. Check current runs only when live operational status is requested.


## Diagnose a completed workflow by its actual terminal outcome

The [0.3 pipeline audit](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-030-pipeline.md) records a successful candidate
workflow that *rejected and closed* PR #32. Feedback persistence and cleanup succeeded; merge was
skipped. It also records a later accepted candidate whose exact tree merged without an ordinary
push-main CI run. Therefore inspect the bound verdict, tested candidate, merge job, and resulting
commit separately. A green workflow badge can mean correct rejection handling, and an accepted
updater tree still lacks release eligibility until the required main artifact exists.

Two findings against PR #32 were disproved: short diff hunks hid the upstream record paths, causing
the reviewer to swap blob identities; a second inventory fetched on the same UTC day legitimately
kept the same retrieval date. The repair supplied complete changed records keyed by upstream path,
with exact base/head source identities. It retained the rejection history instead of rewriting it
as approval. Review context must make attribution possible, and the producer and consumer must
enforce the *combined* context cap rather than separate caps that fit only individually.

The [readiness campaign](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/pipeline-readiness-validation.md) distinguishes a third
outcome: the model process exited zero but stream validation rejected an unknown event kind.
There was no authenticated verdict and no substantive rejection-budget charge. A fresh minimal
probe reproduced the structural parser failure; missing private logs did not justify inventing
what happened in the original run. Validate session, agent and final report bindings before
interpreting prose, retain safe structural diagnostics, and keep rejected/unvalidated content
out of durable acceptance history.

## Detector execution errors are not source inventories

The September 7 verification campaign observed trusted-main maintenance run
[34158581533](https://github.com/njs14/pkstack/actions/runs/34158581533) fail in detection
at `3a370aa92d881ea8bab48c4b55c70cad347c49b7`. The log retained only a top-level schema
error; no detector artifact survived, so its initiating cause remains unknown. This differs
from historical run 34127637886's bootstrap-preview field mismatch, repaired before v0.5.2.

A separate local unauthenticated detector returned an HTTP 403 execution-error envelope.
The guard reproduced the same misleading top-level schema diagnostic for that envelope.
The bounded repair identifies known execution-error categories, exact HTTP status messages,
and the fixed network-budget exhaustion message. Arbitrary error text remains private;
malformed envelopes still fail validation. Neither form is a source inventory, no-change
result, proposal, or substantive review verdict. The local 403 does not establish the CI
failure's cause. Reproof through trusted-main maintenance requires independent acceptance
and merge of the repair first; the final review candidate itself remains held for review.

## Retry from preserved authority, not an edited history

The readiness review found provenance changes that rewrote unchanged safety rationale and guessed
retrieval dates. Keep prior rationale verbatim when the disposition is unchanged; put new delta
reasoning in the new proposal. The trusted detector supplies the UTC date and rejects a retrieval
crossing midnight, so neither a model's clock nor candidate content sets provenance authority.
A repeated same-day date is valid. These controls preserve what was accepted and why while still
recording the new transition. [Source and remediation](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/pipeline-readiness-validation.md#review-finding-remediation)

A subsequent [retry failure](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-030-pipeline.md#cleanup-follow-up-and-second-source-campaign)
was caused by trusted cleanup itself: deleting a pending final marker exposed a trailing blank
separator, making a previously clean staged diff fail. The regression ran the real preparation
path, then the repair removed only empty separators exposed at EOF. It preserved accepted markers,
prose after a marker, and the existing rejection of unrelated whitespace. Diagnose cleanup's
transformation separately from the original accept-preview failure, whose cause was not retained.

Finally, [cleanup review](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/cleanup-validation.md) removed model-driven repair of
known generated output. Regenerate reviewed assets deterministically and report manual parity
when that cannot proceed. Keep one latest validated rejection and count per source/content pair;
failed feedback persistence leaves the candidate open so its history is not lost. Branch
existence alone is not unfinished work: the [later branch audit](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/evidence-led-improvements/README.md#branch-triage-and-review-boundary)
found both superseded updater attempts and a deliberately unmergeable CI-failure demonstration.

## Source-specific retained knowledge

These summaries describe what is retained from each source. Historical observations keep their
original candidate and scope; they are not fresh verification of this checkout.

| Source | Retained guidance or bounded observation |
| --- | --- |
| [powers/pkstack/docs/upstream-control-loop.md](../../../powers/pkstack/docs/upstream-control-loop.md) | One-source proposals, isolated no-tool review, secretless tests, 64 KiB context and three-rejection budgets govern automation; stale candidates and failed feedback persistence stop safely. |
| [reviews/pk-stack-maintenance-campaign.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/pk-stack-maintenance-campaign.md) | A source-scoped goal recorded real drift then accepted-baseline pass with unchanged other sources; the two-path Cursor-only transition does not prove today's updater health. |
| [reviews/pipeline-readiness-validation.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/pipeline-readiness-validation.md) | Proposal diagnostics fixed a wrong drift_count prompt assumption without claiming the missing original cause; the canary pin mismatch correctly stopped authenticated work pending review. |
| [reviews/release-030-pipeline.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-030-pipeline.md) | The 0.3 audit repaired digest/context limits, trusted cleanup and retry accounting, and retained failed live campaigns before a bounded accepted source update. |
| [reviews/fable-fbl046-peer-review.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/fable-fbl046-peer-review.md) | FBL-046 review examined hosted reviewer readiness for checkpoint 347d461; source inspection and authenticated preflight are separate from full release acceptance. |
| [reviews/github-app-council-probe.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/github-app-council-probe.md) | GitHub App acknowledgements/no-response were insufficient deterministic review evidence; the shipped hosted authority uses exact-candidate Kiro review with isolated credentials. |
| [reviews/kiro-runtime-canary-campaign.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/kiro-runtime-canary-campaign.md) | The September 3 canary observed exact runtime/agent/model-inventory identity, without promoting pins, exercising a model task, or proving IDE/Web/maintenance acceptance. |

## Changed-main detector reproof, September 8

After [PR #69](https://github.com/njs14/pkstack/pull/69) merged, trusted-main run
[34173315294](https://github.com/njs14/pkstack/actions/runs/34173315294) stopped with
`UpstreamError`; no inventory, proposal or reviewer verdict was produced. A separate
local run of that exact controller returned `upstream comparison patches exceed the
262144-byte limit`. This local result is not yet proof of the CI failure cause.

The guard now permits that one fixed message in its diagnostic, with a regression
for the previously hidden bound and a newline-plus-secret counterexample. It still
rejects the error envelope and preserves the comparison byte limit, schema and
maintenance policy. A changed trusted-main run must establish the actual CI cause;
limits are not relaxed merely to obtain a passing maintenance run.
