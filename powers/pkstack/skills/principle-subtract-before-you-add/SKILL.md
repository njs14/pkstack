---
name: principle-subtract-before-you-add
description: Remove dead paths, duplicate checks, stale references, and speculative surface area before adding or reshaping behavior in a complex area.
---

# Simplify before building

Treat the request text that activated this skill as the addition or refactor to simplify first.

Apply [subtract before you add](../pkstack-principles/references/catalog.md#subtract-before-you-add).
Inventory dead or duplicated behavior, remove it in a separately verifiable unit, then design the
new behavior against the smaller surface. Do not add options or validators without an observed
requirement. Return the subtraction, its proof, and the smaller addition it enabled.
