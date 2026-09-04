---
name: principle-make-operations-idempotent
description: Make commands, lifecycle steps, scheduled jobs, and retry loops converge safely after repeat runs and interruption at any write boundary.
---

# Make reruns converge

Treat the request text that activated this skill as the operation to make retry-safe.

Apply [make operations idempotent](../principles/references/catalog.md#make-operations-idempotent).
Inventory partial states, reconcile before writing, use atomic changes for coupled state, and target
cleanup only at exact owned resources. Test a second run and interruption around writes. Return the
state model and convergence evidence.
