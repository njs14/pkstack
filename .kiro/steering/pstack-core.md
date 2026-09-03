---
inclusion: always
---

# PK-Stack operating model

Kiro owns execution and orchestration. PK-Stack owns workflow semantics. `projectctl` owns deterministic project operability and verification. OKF-compatible knowledge records preserve broader project intent and evidence.

Prefer Kiro's native specs, skills, custom agents, sub-agents, hooks,
permissions, steering, and knowledge where they fit. Kiro IDE 1.x chat/Agent
Focus and Kiro CLI v3 are the primary interaction surfaces. Kiro Crew is an
optional orchestrator and may use ACP internally; do not turn that implementation
detail into PK-Stack's default entrypoint. Kiro Web consumes committed workspace
assets by design but is untested. Keep normal work in the user's current Kiro
agent session. Use `/spawn` only when the user explicitly wants a separate
parallel session.

Treat generated feature maps and goal state as projectctl-owned data. Do not hand-edit them to manufacture success. A claim is complete only when its named executable verifier passes.

The `pstack` profile deliberately excludes installed Powers. For setup or a
managed refresh, IDE users stay in chat and use the agent picker to select the
Power-enabled setup agent, invoke `/setup-pstack`, and reselect `pstack`. CLI
users stay in chat and use `/agent swap kiro_default`, `/setup-pstack`, then
`/agent swap pstack`; use the previously selected setup agent if its name
differs. Crew opens the trusted project only after local bootstrap. Web uses a
locally refreshed, reviewed, committed asset tree; Configuration Sync is not a
complete PK-Stack installer. Never use cached `.pstack/bin/projectctl setup`
without an explicitly reviewed `--power-root` as upgrade authority.
