---
type: glossary
title: Upstream maintenance vocabulary
description: Terms used when comparing, reviewing, and accepting upstream source drift in PKStack.
tags: [upstream-maintenance, glossary, provenance]
---

# Upstream maintenance vocabulary

Terms for the [upstream-maintenance feature contract](../../features/pkstack-upstream-maintenance.md).
Definitions below are settled unless listed under open questions.

**Configured source**: A GitHub upstream entry in `maintenance/upstreams.json`. Only these entries
are eligible for the autonomous acceptance path. Kiro product facts are not configured sources.

**Accepted pin (baseline)**: The immutable commit and tree identity currently accepted for one
source. "Current ref" is the upstream state being compared against it, not a new baseline.

**Drift**: An accepted pin that is behind its current configured ref. Drift is an expected candidate
state that returns nonzero; it is not a passing check and not a defect in the contract.

**Genesis marker**: The one canonical marker per source that binds ledger genesis. It precedes every
transition marker.

**Transition marker**: An immutable, ordered record of one accepted pin advance. Prior markers stay
byte-for-byte.

**Transaction**: One atomic acceptance covering exactly one drifting source: fresh revalidation, one
ledger append, one pin advance. Multiple drifting sources are serialized, never mixed.

**A/B/C disposition**: The exact content-addressed review outcome recorded for every changed path of
an accepted transition. Unavailable raster assets are excluded with disposition B.

**Semantic patch**: A complete, count-reconciled change applied from a Git-OID-verified old blob to
the exact current blob, with explicit old/new regular-blob modes.

**Product canary**: The separate weekly or manually dispatched read-only run
(`kiro-product-canary`). It observes product, runtime, and documentation drift. It is not an
acceptance path and never edits a pin, candidate branch, workflow, or controller file.

**Gate vs observation**: A gate can fail the run (advertised-binary checksum/version, six-agent
validation and discovery, strict model inventory). An observation is bounded and non-gating (IDE
metadata, Kiro Crew Nightly feeds, changelog, `llms.txt`, tracked documentation hashes). An
observation is evidence, not verification.

**Fail-closed**: Missing credentials, incomplete pagination, or indeterminate identity evidence stop
the run without acceptance and leave both baselines intact.

**Trust root**: The workflow and protected controller files that constrain the canary. The canary
cannot edit them, and a human promotes a stable CLI pin in them separately, so no automated canary
run promotes itself. This term is about that canary boundary; it does not restrict what an ordinary
authorized upstream acceptance may change, including regenerated or bootstrap-managed assets.

## Open questions

Widening the autonomous acceptance contract beyond the configured GitHub source entries has no
accepted target date and no accepted owner. This remains unresolved, not a decision. Until it is
settled, the scope in [the accepted decisions](decisions.md) stands as written.

Deterministic local-only `projectctl knowledge validate` is already required by the accepted plan,
which also rejects shipping an optional `okn` backend. What remains unresolved is completion of that
migration in the current prototype, tracked as an [observation](observations.md).
