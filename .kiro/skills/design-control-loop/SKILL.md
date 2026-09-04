---
name: design-control-loop
description: Design a locally runnable, observable agent control loop with an explicit set point, sensor, controller, Kiro actuator, disturbances, and dampener.
compatibility: Kiro IDE 1.x and Kiro CLI v3; Kiro Crew compatible; Kiro Web supported by design but untested.
---

# Design a control loop

Treat the request text that activated this skill as the desired outcome. Read `references/taxonomy.md` and inspect the
repository before asking questions. Propose concrete options from existing commands, patterns, CI,
and permissions; ask only when a choice would materially change the design.

## Design phases

1. Define a measurable set point and the directories the loop may write or only inspect.
2. Choose a repeatable local sensor and describe its false-positive, cost, and disablement risks.
3. Define a controller that selects the next small, reviewable increment. Start deterministic when
   the measurement already supplies enough structure.
4. Choose a Kiro actuator and repo-local skill. Establish golden patterns and exact validation.
5. Name disturbances and add a dampener when it can prevent regression or stale proof.
6. Define terminal states, attempt and work-in-progress bounds, and durable human feedback.
7. Make sensor, controller, and actuator independently runnable locally before adding CI.
8. Record the agreed contract, then implement only if the user requested implementation.

Do not manufacture separate components where they are genuinely fused. Do not introduce external
model API keys, broad write access, floating dependencies, or an unbounded PR/comment loop. When
GitHub Actions is selected, use `build-iterated-agentic-loop` for implementation.

Completion criterion: the design identifies every authority, transition, proof, failure state, and
local command well enough to test the loop without CI.
