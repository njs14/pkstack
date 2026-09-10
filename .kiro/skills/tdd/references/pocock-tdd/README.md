# Test behavior through useful interfaces

Reuse the repository's settled framework, seam, and integration decisions. Inspect existing tests
before choosing a boundary. Derive a straightforward compatible choice from those constraints;
ask only when consequential allowed alternatives remain. Do not require confirmation before each
test or restart a settled testing strategy.

Work vertically: one meaningful failing example, the smallest implementation, then the next
behavior learned from that cycle. Independent expected values come from the specification or a
worked example, not a second copy of the implementation. Keep refactoring distinct from red/green.
Use [examples](tests.md) and [boundary substitution guidance](mocking.md). Architect owns unresolved
interface design. A public-interface preference does not forbid targeted guard or security tests.
