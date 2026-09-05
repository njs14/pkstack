---
name: design-control-loop
description: Design a locally runnable, observable agent control loop with an explicit set point, sensor, controller, Kiro actuator, disturbances, and dampener.
---

# Design a control loop

Treat the request text that activated this skill as the desired outcome. Inspect the repository
before asking questions. Propose concrete options from existing commands, patterns, CI,
and permissions; ask only when a choice would materially change the design.

## Required control vocabulary

Use these definitions in the contract; they are included here so native skill loading supplies
the complete method. `references/taxonomy.md` is a separate copy for reference.

- **Set point:** the invariant, threshold, or direction to maintain.
- **Sensor:** a repeatable measurement of the repository and its gap from the set point.
- **Controller:** the rule choosing what to do now and what to defer.
- **Actuator:** Kiro plus a skill applying one bounded change.
- **Disturbance:** an external change such as upstream drift or concurrent development.
- **Dampener:** an independent gate that prevents regression or stale proof.
- **Feedback:** durable human steering that changes future selection or behavior.
- **Flow control:** attempt, batch, time, and open-candidate bounds.

Components may be fused. Each must remain locally runnable, observable, and replaceable.

This method defines reusable automation. For completing the current task, use
[`pkstack-verified-goal`](../pkstack-verified-goal/SKILL.md). Use
[`architect`](../architect/SKILL.md) for an unresolved component boundary or
[`arena`](../arena/SKILL.md) for a distinct contested artifact, passing the agreed control
contract forward. Do not repeat a completed alternatives comparison. Keep any native Kiro
Spec as the planning authority.

## Design phases

1. Define a measurable set point and the directories the loop may write or only inspect.
2. Choose a repeatable local sensor and describe its false-positive, cost, and disablement risks.
3. Define a controller that selects the next small, reviewable increment. Start deterministic when
   the measurement already supplies enough structure.
4. Choose a Kiro actuator and repo-local skill. Establish golden patterns and exact validation.
5. Name disturbances and add a dampener when it can prevent regression or stale proof.
6. Define terminal states, attempt and work-in-progress bounds, and durable human feedback.
   Name who enforces the attempt count before actuation and how separately invoked commands or
   promised restarts retain it. Invalid input is a failure even when nothing is eligible.
   Bind each increment to its pre-actuation selection and baseline; distinguish a verified
   increment from the global set point, which may require further increments.
7. Make sensor, controller, and actuator independently runnable locally before adding CI.
8. Record the agreed contract, then implement only if the user requested implementation.

Do not manufacture separate components where they are genuinely fused. Do not introduce external
model API keys, broad write access, floating dependencies, or an unbounded PR/comment loop. When
implementation is requested, pass the agreed contract to
[`build-iterated-agentic-loop`](../build-iterated-agentic-loop/SKILL.md), including when
GitHub Actions is selected. A design request does not authorize wiring or enabling automation.

Completion criterion: the design identifies every authority, transition, proof, failure state, and
local command well enough to test the loop without CI.

Label proposed commands and hypothetical transitions as unexecuted. Call a result observed only
when an actual run supplies evidence; a worked example is not a run.
