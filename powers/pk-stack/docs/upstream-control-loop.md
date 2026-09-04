# PK-Stack upstream control loop

The self-updater is an iterated agentic loop with discrete, locally runnable authorities.

| Part | PK-Stack implementation | Terminal evidence |
| --- | --- | --- |
| Set point | Every reviewed upstream pin is current; source parity and generated output are exact | Aggregate `projectctl upstream check` returns `ok: true` |
| Sensor | `projectctl upstream check` | Bounded JSON detector bound to the trusted base |
| Controller | `pk_stack_update_controller.py` | One source selection or a typed no-op/block decision |
| Actuator | Kiro with `maintain-pk-stack` | Authored Power delta plus proposal; no GitHub write authority |
| Feedback | `.github/agent-memory/pk-stack-upstream.md` plus per-attempt verifier feedback | Trusted-base standing rules and transient bounded evidence |
| Dampener | Secretless verification and the exact-SHA candidate workflow | Base/candidate gates, isolated Kiro peer review, mergeability reproof |
| Flow control | One open bot candidate, one source, four repair attempts | Policy and workflow guards |

The scheduled workflow senses before spending Kiro credits, chooses exactly one complete reviewable
drift, applies bounded repairs, verifies without the model credential, and passes only an immutable
data package to a publisher. The publisher never executes candidate code. The candidate workflow
reconstructs trust from the default-branch policy and binds testing, peer review, and merge to exact
commits.

Disturbances include upstream commits, concurrent default-branch changes, generated-copy drift,
model inventory changes, unavailable Kiro service, and stale candidate runs. Each becomes a typed
no-op, retryable failure, or hard blocker; none silently weakens the gate.
