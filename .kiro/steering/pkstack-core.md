---
inclusion: always
---

# PKStack operating model

Kiro owns execution. PKStack owns workflow semantics. `projectctl` owns deterministic operations
and proof; source-controlled OKF preserves broader intent.

Use native specs, skills, custom agents, sub-agents, hooks, permissions, steering, and knowledge.
Nontrivial work begins in native Spec, Quick Spec, or Bug Fix. Kiro owns its intent, design, tasks,
dependency waves, and execution. Return to `pkstack` in the same IDE or CLI conversation and bind
the spec to a reviewed command or published feature verifier. Record an initial failure before
repairing new behavior. Do not recreate its planner or treat tasks as proof.

Use DO through `projectctl`, PROVE through the narrow spec-linked feature map, and KNOW through
canonical `okn` over `Wiki/`. Start with PROVE; enter KNOW only for a concrete architecture,
decision, concept, or operations question. Native `/knowledge` may index the Wiki but is not a
second source of truth.

Kiro IDE chat/Agent Focus and Kiro CLI v3 are primary. Crew is optional and may use ACP internally;
ACP is not PKStack's default. Web consumes committed assets by design but is untested. Keep work in
the current session. Use `/spawn` only when the user requests a separate session.

Treat feature maps and goal state as projectctl-owned. Never hand-edit them to manufacture success;
completion requires the named executable verifier to pass.

The `pkstack` profile excludes installed Powers. For setup or refresh, use the IDE agent picker
or CLI `/agent swap default` to leave the restricted profile. A default-agent swap alone does not
make a Power discoverable. Invoke `/pkstack-setup` only when the reviewed Power is available;
otherwise run its reviewed Power-local setup script from a terminal as documented in usage.md.
Return with `/agent swap pkstack` or the IDE picker. Crew opens only locally bootstrapped projects.
Web uses reviewed, committed assets; Configuration Sync does not install PKStack.
Cached `.pkstack/bin/projectctl setup` requires an explicitly reviewed `--power-root`.
