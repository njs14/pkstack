---
name: principle-boundary-discipline
description: Concentrate parsing, validation, and error translation at real system boundaries while keeping typed internal business logic small and direct.
compatibility: Kiro IDE 1.x and Kiro CLI v3; Kiro Crew compatible; Kiro Web supported by design but untested.
---

# Keep guards at boundaries

Treat the request text that activated this skill as the boundary decision to inspect.

Apply [boundary discipline](../principles/references/catalog.md#boundary-discipline). Identify the
exact CLI, file, configuration, network, database, or external API crossing. Parse once into a
domain value, translate errors there, and remove redundant internal guards only when the parsed
type truly carries the invariant. Return the boundary, the trusted internal shape, and its focused
test.
