---
name: principle-minimize-reader-load
description: Reduce the layers a maintainer must trace and the mutable state they must remember while preserving boundaries that hide meaningful complexity.
compatibility: Kiro IDE 1.x and Kiro CLI v3; Kiro Crew compatible; Kiro Web supported by design but untested.
---

# Reduce reader load

Treat the request text that activated this skill as the code path a maintainer must understand.

Apply [minimize reader load](../principles/references/catalog.md#minimize-reader-load). Trace where
key values originate and change. Collapse layers that repeat the same interface, narrow mutable
state, and name invariants once at their boundary. Return the shorter reasoning path and any layer
kept because it compresses a real decision.
