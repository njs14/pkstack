---
type: Decision
title: Accepted upstream maintenance decisions
description: Settled scope, observation-only canary, and one-source acceptance rules for upstream maintenance.
tags: [upstream-maintenance, decision, provenance, kiro]
---

# Accepted upstream maintenance decisions

These choices are already accepted and are recorded here for reuse. Reusing them does not require a
new approval. Acceptance of a decision is not proof that the current implementation satisfies it;
see [observations](observations.md) for what inspected sources actually establish.

## The product canary observes only

The scheduled or manually dispatched `kiro-product-canary` run reports product, runtime, and
documentation drift and never edits the repository, a candidate branch, or a CLI pin. A newer stable
Kiro CLI deliberately fails the canary red until a human reviews and promotes the stable pin in the
workflow and protected controller files.

Rationale: workflow and protected controller files are trust roots, so a run that could advance them
would be promoting itself. Keeping the canary read-only also keeps `KIRO_API_KEY` scoped to live
model-inventory listing after the advertised tuple exactly matches the reviewed version, SHA-256,
derived URL, and size.

Alternative considered: letting the canary auto-promote a stable pin. Rejected because it collapses
the observation boundary into an acceptance path.

## Source acceptance is separately authorized, one source per transaction

An acceptance is a distinct authorized action from a check or a proposal. Each transaction covers
exactly one drifting source, freshly revalidates the exact proposal, then performs one atomic ledger
append and pin advance. A failed check moves neither baseline, and other sources' pins and ledgers
stay byte-identical. Multiple drifting sources are serialized.

Rationale: one source per transaction keeps the A/B/C evidence, semantic-patch reconciliation, and
ledger ordering attributable to a single reviewed candidate. Mixed proposals would make that
provenance ambiguous.

## Autonomous advance is scoped to configured GitHub source entries

Only the GitHub source entries in `maintenance/upstreams.json` advance autonomously. Kiro product
facts stay observations rather than becoming another self-updating source.

No date or owner has been accepted for widening this contract. That gap is preserved as an
[open question](glossary.md#open-questions), not resolved here.

## Related

- Executable contract and verification recipe: [upstream maintenance feature](../../features/pkstack-upstream-maintenance.md)
- Document ownership and claim types: [knowledge lifecycle](../pkstack/knowledge-lifecycle.md)
- Runtime and planning boundaries: [native planning and canonical okn](../pkstack/native-spec-and-okn.md),
  [native Kiro composition](../pkstack/native-kiro-composition.md)
- Bounded retrieval depth: [context-depth runbook](../pkstack/context-depth.md)
