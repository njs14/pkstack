---
inclusion: always
---

# PK-Stack operating model

Kiro owns execution. PK-Stack owns workflow semantics. `projectctl` owns deterministic operations
and proof; source-controlled OKF preserves broader intent.

Use native specs, skills, custom agents, sub-agents, hooks, permissions, steering, and knowledge.
Nontrivial work begins in native Spec, Quick Spec, or Bug Fix. Kiro owns its intent, design, tasks,
dependency waves, and execution. Return to `pk-stack` in the same IDE or CLI conversation and bind
the spec to a published feature verifier. Do not recreate its planner or treat tasks as proof.

Use DO through `projectctl`, PROVE through the narrow spec-linked feature map, and KNOW through
canonical `okn` over `Wiki/`. Start with PROVE; enter KNOW only for a concrete architecture,
decision, concept, or operations question. Native `/knowledge` may index the Wiki but is not a
second source of truth.

Kiro IDE chat/Agent Focus and Kiro CLI v3 are primary. Crew is optional and may use ACP internally;
ACP is not PK-Stack's default. Web consumes committed assets by design but is untested. Keep normal
work in the current session. Use `/spawn` only when the user requests a separate session.

Treat feature maps and goal state as projectctl-owned. Never hand-edit them to manufacture success;
completion requires the named executable verifier to pass.

The `pk-stack` profile excludes installed Powers. For setup or managed refresh, IDE users stay in chat
and use the agent picker to select the Power-enabled setup agent, invoke `/setup-pk-stack`, and
reselect `pk-stack`. CLI users stay in chat and use `/agent swap kiro_default`, `/setup-pk-stack`, then
`/agent swap pk-stack`; use the prior setup agent if named differently. Crew opens the trusted project
only after local bootstrap. Web uses a locally refreshed, reviewed, committed asset tree;
Configuration Sync is not a complete PK-Stack installer. Cached `.pstack/bin/projectctl setup`
requires an explicitly reviewed `--power-root` as upgrade authority.
