---
name: principle-model-the-domain
description: Replace scattered state booleans, repeated shape assumptions, and branching with the smallest structure that encodes the real domain and its invariants.
---

# Encode the domain

Treat the request text that activated this skill as the domain behavior to model.

Apply [model the domain](../principles/references/catalog.md#model-the-domain). List valid states,
transitions, and access patterns, then choose a state machine, variant type, registry, command model,
or simpler local structure that makes invalid combinations difficult to construct. Return the model
and the branches or synchronized flags it replaces.
