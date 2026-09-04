---
name: principle-foundational-thinking
description: Choose core data structures, state ownership, concurrency boundaries, and shared verification before dependent feature logic closes design options.
---

# Put foundations first

Treat the request text that activated this skill as a structural decision to make before feature logic.

Apply [foundational thinking](../principles/references/catalog.md#foundational-thinking). Model the
data and dominant access paths, isolate shared mutable state, and sequence common verification or
scaffolding ahead of dependents. Avoid abstractions that remove no decision. Return the chosen
foundation and the downstream branches or risks it eliminates.
