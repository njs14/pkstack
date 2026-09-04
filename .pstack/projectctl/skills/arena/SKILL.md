---
name: arena
description: Compare multiple structurally distinct solutions to one artifact under a shared rubric, select a base, coherently graft the strongest ideas, and verify the result. Use when a design or implementation has meaningful competing approaches.
---

# Run an arena

Treat the request text that activated this skill as the artifact or question.

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

After PK-Stack setup, use only the managed `.pstack/bin/projectctl` entrypoint.
Run the repository's executable verifier, preferably
`.pstack/bin/projectctl feature verify <slug> --output json` or
`.pstack/bin/projectctl verify <slug> --output json`. Do not select an ambient
`projectctl` or repository-owned `./projectctl`. Report the rubric, scorecard,
chosen base, grafted ideas, exact verifier, and unresolved uncertainty.
