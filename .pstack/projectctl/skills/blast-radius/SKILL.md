---
name: blast-radius
description: Trace one proposed change or suspected defect through callers, state, boundaries, and executable behavior to establish its real blast radius.
compatibility: Kiro IDE 1.x and Kiro CLI v3; Kiro Crew compatible; Kiro Web supported by design but untested.
---

# Establish the blast radius

Treat the request text that activated this skill as the change or safety claim to investigate.

Start with one falsifiable risk statement. Identify the changed symbol, value, state transition, or
external contract, then trace it in both directions: where it originates and every meaningful place
it is consumed. Search is discovery, not proof; follow aliases, generated artifacts, registries,
configuration, persistence, retries, cleanup, and user-visible entrypoints.

## Prove the boundary

1. Build a compact caller-and-state map with confirmed edges and explicit gaps.
2. Select the smallest executable observations that would fail if the risk were real.
3. Exercise the actual code path where safe, including one sibling path likely to share the defect.
4. Inspect outputs and side effects, not only exit status.
5. Do not widen the investigation after the original risk and plausible siblings are bounded.

Report **confirmed affected**, **confirmed clear**, and **not yet proven** separately. Include exact
evidence and the narrowest safe remediation boundary; do not claim that a text search alone cleared
a path.
