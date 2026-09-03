---
name: principle-separate-before-serializing-shared-state
description: Remove unnecessary shared write targets between concurrent actors before adding structural serialization for state that truly requires one writer.
compatibility: Kiro IDE 1.x and Kiro CLI v3; Kiro Crew compatible; Kiro Web supported by design but untested.
---

# Separate shared writes

Treat the request text that activated this skill as the concurrent state boundary.

Apply [separate before serializing shared state](../principles/references/catalog.md#separate-before-serializing-shared-state).
List every actor and write target. Give independent facts separate files, branches, keys, or state
objects and merge them at a read boundary. Where one canonical writer is real, use a lock,
transaction, compare-and-swap, or single-writer phase. Return the ownership map and race proof.
