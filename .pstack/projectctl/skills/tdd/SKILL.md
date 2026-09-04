---
name: tdd
description: Implement a behavior change with a focused failing regression first, the smallest coherent fix, and layered executable evidence.
---

# Develop from a failing behavior

Treat the request text that activated this skill as the behavior to add or repair.

Define the externally meaningful contract before editing production code. Locate the closest test
surface and write the smallest regression that fails for the intended reason. Run it and inspect the
failure; a syntax error, bad fixture, or unrelated failure is not a valid red phase.

Implement the smallest coherent production change that makes the contract true. Keep refactoring
separate until the test passes. Then run the focused test, nearby suite, static checks, and an
end-to-end observation proportional to risk. Add boundary cases discovered during implementation,
not speculative combinatorics.

If a failing-first test is impractical because the only surface is destructive, external, or not
locally reproducible, say why and establish the safest executable characterization available before
editing. Return red evidence, change, green evidence, and remaining untested risk.
