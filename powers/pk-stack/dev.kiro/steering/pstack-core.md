---
inclusion: always
---

# PK-Stack operating model

Kiro owns execution and orchestration. PK-Stack owns workflow semantics. `projectctl` owns deterministic project operability and verification. OKF-compatible knowledge records preserve broader project intent and evidence.

Prefer Kiro CLI v3's native specs, skills, custom agents, sub-agents, hooks, permissions, steering, and knowledge where they fit. Keep normal work in the user's current interactive session. Use `/spawn` only when the user explicitly wants a separate parallel session.

Treat generated feature maps and goal state as projectctl-owned data. Do not hand-edit them to manufacture success. A claim is complete only when its named executable verifier passes.

The `pstack` profile deliberately excludes installed Powers. If setup or a
managed refresh is needed after selecting it, stay in the same session: run
`/agent swap kiro_default`, invoke the Power-local `/setup-pstack`, then run
`/agent swap pstack` before the next workflow message. If `kiro_default` is not
the Power-enabled agent in the local installation, swap to the previously used
Power-enabled setup agent instead. Never use cached
`.pstack/bin/projectctl setup` without an explicitly reviewed `--power-root`
as upgrade authority.
