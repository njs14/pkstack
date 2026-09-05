---
name: principle-type-system-discipline
description: Use variants, constructive types, branded primitives, parsed boundaries, schema derivation, and exhaustive matching to make invalid typed states hard to express.
---

# Let types carry invariants

Treat the request text that activated this skill as the typed boundary or data model to strengthen.

Apply [type-system discipline](../pkstack-principles/references/catalog.md#type-system-discipline). Identify
invalid combinations, semantically distinct primitives, external untyped input, and variants the
compiler does not exhaust. Redesign only where it makes an operation total or enforces a real
invariant; do not add precision for ceremony. Return the compiler-enforced property and type-check
evidence.
