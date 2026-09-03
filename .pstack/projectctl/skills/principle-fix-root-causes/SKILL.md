---
name: principle-fix-root-causes
description: Reproduce a failure, trace the first incorrect value or state, fix that origin, and prove the nearby class of symptoms cannot return through another path.
compatibility: Kiro IDE 1.x and Kiro CLI v3; Kiro Crew compatible; Kiro Web supported by design but untested.
---

# Fix the cause

Treat the request text that activated this skill as the failure to diagnose.

Apply [fix root causes](../principles/references/catalog.md#fix-root-causes). Reproduce first, follow
the state backward to where it becomes wrong, and instrument uncertainty instead of guessing.
Inspect persisted state for restart-only bugs. Reject a guard that merely hides the symptom. Return
the cause, the smallest causal fix, and the regression evidence.
