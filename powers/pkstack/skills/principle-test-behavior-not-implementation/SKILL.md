---
name: principle-test-behavior-not-implementation
description: Write tests that invoke the real subject through its supported interface and assert an independently specified output or effect, rather than restating implementation details.
---

# Test observable behavior

Treat the request text that activated this skill as the test or behavior to verify.

Apply [test behavior, not implementation](../pkstack-principles/references/catalog.md#test-behavior-not-implementation).
Call the subject with a concrete input through the interface its users rely on. Assert a literal
expected result or an independently specified observable effect. Ask which defect would make the
test fail, and whether replacing the subject with a no-op would be detected.

Replace self-comparisons, fixtures that never invoke the subject, and assertions that merely
repeat constants or prompt text. For mocks, check the meaningful payload or resulting state.
For an expected absence, also exercise the contrasting input that must produce a result. Test
the mechanism that consumes a configuration value, including its permitted and rejected cases.

Keep useful type checks, relationships across registries, and security or packaging contracts.
An empty result or a rejected action can be the required behavior. Do not delete those tests
because of assertion syntax alone. Use [tdd](../tdd/SKILL.md) when a failing example can guide
implementation, and keep the existing feature and projectctl verification contract.
