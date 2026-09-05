---
name: principle-laziness-protocol
description: Prefer deletion and the smallest direct maintainable change when a refactor starts adding wrappers, layers, duplicated decisions, or signal threading.
---

# Keep the solution small

Treat the request text that activated this skill as a complexity budget.

Apply [the laziness protocol](../pkstack-principles/references/catalog.md#laziness-protocol). Search for
deletion first, collapse pass-through layers, and keep one source of truth for each decision. Add an
abstraction only when it hides real complexity or removes repeated policy. Return what was removed,
what remains, and why the final path is easier to trace.
