---
name: improve-codebase-architecture
description: Survey selected modules or Git-history hotspots for architectural friction and present visual before/after candidates. Use to identify and choose a refactor before implementation.
---

# Find useful architecture improvements

Honor the user's scope and active Kiro workflow. In native Plan, use permitted reading and
search, keep the result conversational, and defer commands, MCP calls, file writes, experiments,
and validation until execution is permitted. A skill invocation does not widen authority.

Scope the survey to the user's named areas. When unspecified, inspect recent Git-history hotspots
and explain the selected scope; widen only if the history provides no useful focus. Read the domain
glossary, existing decisions, and the relevant native Spec. Preserve settled choices unless observed
friction warrants reopening one. Do not turn every shallow wrapper into a mandatory refactor.

Read [architect's shared module design method](../architect/references/pocock-codebase-design/README.md).
Trace concrete friction: callers that must know internal policy, one concept scattered across
many files, coupling across interfaces, or tests that cannot reach the actual behavior. Apply the
deletion test: would removing this layer concentrate complexity or merely relocate it? A bounded
native subagent may explore a distinct area when useful and permitted; reuse its evidence.

Present a few candidates with files, observed problem, proposed change, caller and test benefits,
risks, and recommendation strength (strong, worth exploring, or speculative). Use
[show-me](../show-me/SKILL.md) for before/after visuals grounded in those paths; use
[archify](../archify/SKILL.md) when a polished HTML artifact is useful and writing is permitted.
The [report reference](HTML-REPORT.md) defines the contents. In Plan, present inline diagrams.
Mark proposals that contradict an existing decision and give the concrete reason to revisit it.

Recommend the most useful candidate. Continue only within existing selection and implementation
authority; when a consequential choice remains, ask which candidate to develop. Feed that choice
and evidence into [architect](../architect/SKILL.md) and the active native planning workflow.
Its alternatives pass owns interface design; do not run a second arena for the same decision.
Use shared grilling for unresolved choices and OKF for authorized retention of decisions.
