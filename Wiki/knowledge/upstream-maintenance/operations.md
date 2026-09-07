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


## Source-specific retained knowledge

These summaries describe what is retained from each source. Historical observations keep their
original candidate and scope; they are not fresh verification of this checkout.

| Source | Retained guidance or bounded observation |
| --- | --- |
| [powers/pkstack/docs/upstream-control-loop.md](../../../powers/pkstack/docs/upstream-control-loop.md) | One-source proposals, isolated no-tool review, secretless tests, 64 KiB context and three-rejection budgets govern automation; stale candidates and failed feedback persistence stop safely. |
| [reviews/pk-stack-maintenance-campaign.md](../../../reviews/pk-stack-maintenance-campaign.md) | A source-scoped goal recorded real drift then accepted-baseline pass with unchanged other sources; the two-path Cursor-only transition does not prove today's updater health. |
| [reviews/pipeline-readiness-validation.md](../../../reviews/pipeline-readiness-validation.md) | Proposal diagnostics fixed a wrong drift_count prompt assumption without claiming the missing original cause; the canary pin mismatch correctly stopped authenticated work pending review. |
| [reviews/release-030-pipeline.md](../../../reviews/release-030-pipeline.md) | The 0.3 audit repaired digest/context limits, trusted cleanup and retry accounting, and retained failed live campaigns before a bounded accepted source update. |
| [reviews/fable-fbl046-peer-review.md](../../../reviews/fable-fbl046-peer-review.md) | FBL-046 review examined hosted reviewer readiness for checkpoint 347d461; source inspection and authenticated preflight are separate from full release acceptance. |
| [reviews/github-app-council-probe.md](../../../reviews/github-app-council-probe.md) | GitHub App acknowledgements/no-response were insufficient deterministic review evidence; the shipped hosted authority uses exact-candidate Kiro review with isolated credentials. |
| [reviews/kiro-runtime-canary-campaign.md](../../../reviews/kiro-runtime-canary-campaign.md) | The September 3 canary observed exact runtime/agent/model-inventory identity, without promoting pins, exercising a model task, or proving IDE/Web/maintenance acceptance. |
