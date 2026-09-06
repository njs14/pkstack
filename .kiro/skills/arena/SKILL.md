---
name: arena
description: Compare multiple structurally distinct solutions to one artifact under a shared rubric, select a base, coherently graft the strongest ideas, and verify the result. Use when a design or implementation has meaningful competing approaches.
---

# Run an arena

Treat the request text that activated this skill as the artifact or question. For planning,
read [`grilling`](../grilling/SKILL.md) and reuse its settled answers and remaining questions.
The contest compares candidates; it does not start a second interview. Follow the shared native
Plan boundaries: conversational candidates only, permitted reading/search, and no shell, MCP,
file writes, prototypes, or validation commands during read-only analysis.

Use [`architect`](../architect/SKILL.md) when the work needs architecture grounding and a
usage-first scaffold; its built-in arena already compares those candidates. Use
[`design-control-loop`](../design-control-loop/SKILL.md) to define a loop's control contract.
Run this contest only for a distinct unresolved choice, with the existing brief and evidence.
Do not start a second contest for a decision that the selected method already settled.

## Frame one contest

Define exactly one artifact and 3-6 gradeable criteria. Include correctness and verification; add safety, maintainability, operability, or performance only when relevant. State the selection rule before generating candidates.

## Generate candidates

Create 2-4 structurally distinct candidates from the same brief. Native Kiro sub-agents may produce candidate analyses in parallel, but `/spawn` is not the internal fanout path. The shipped delegated profiles are read-only; they return candidate text and the primary agent materializes any selected artifact.

Keep candidate work read-only. If the user supplies a different writing agent, give each writer a disjoint isolated output path and do not let parallel agents edit the same implementation paths. A candidate must be independently understandable and must identify its assumptions, failure modes, and proof plan.

## Judge after all candidates finish

Use a separate read-only judging pass with the original artifact, the same rubric, and all candidate outputs. The primary agent must read the candidates and judge report rather than accepting a sub-agent's winner blindly.

For each candidate, record evidence and a status:

- `PASS` - satisfies the rubric with credible verification;
- `ISSUES` - useful but has material correctable gaps;
- `BLOCKED` - cannot be assessed with available evidence.

Select one candidate as the base. Hand-graft only the strongest compatible ideas from other candidates; do not concatenate solutions or average away a coherent design.

## Prove the result

For a design-only contest, report candidate evidence, proposed checks, and remaining uncertainty;
do not execute or materialize a candidate merely to satisfy this section. Approved implementation
plans use the shared capture checkpoint when writes become permitted. If implementation and
execution are authorized, after setup use only the managed `.pkstack/bin/projectctl` entrypoint.
Run the repository's executable verifier, preferably
`.pkstack/bin/projectctl feature verify <slug> --output json` or
`.pkstack/bin/projectctl verify <slug> --output json`. Do not select an ambient
`projectctl` or repository-owned `./projectctl`. Report the rubric, scorecard,
chosen base, grafted ideas, exact verifier, and unresolved uncertainty.
