---
name: swarm
description: Fan out bounded independent investigations or reviews across native Kiro sub-agents, then aggregate coverage, gaps, and evidence. Use for parallel research, repository inventory, test triage, or independent review tracks.
compatibility: Kiro CLI v3 with native sub-agents when parallel execution is available.
---

# Run a swarm

Swarm objective: $ARGUMENTS

## Declare the fanout

Before delegating, state:

- the coverage shape: how the work is partitioned and what complete coverage means;
- the race shape: which tracks are independent, which have dependencies, and whether any shared files exist;
- the selection rule: how returned evidence will be accepted, reconciled, or rejected.

Create standalone briefs with explicit scope, inputs, exclusions, expected evidence, and output format. Use native Kiro sub-agents for internal delegation. `/spawn` starts a separate user session and is not the swarm mechanism.

## Isolate work

The shipped delegated profiles are read-only and return their findings to the primary agent. If the user supplies a different writing agent, give each writer disjoint paths or an isolated worktree and reserve integration for the primary agent. Never allow parallel workers to race on the same file.

Each worker returns one status:

- `PASS` - assigned coverage completed with evidence;
- `ISSUES` - completed but found material problems or uncertainty;
- `BLOCKED` - could not complete, with the exact blocker and attempted checks.

## Aggregate

Wait for all required tracks or account explicitly for timeouts and dropouts. Deduplicate overlapping findings, reconcile disagreements against primary evidence, and produce a compact result containing:

- coverage completed;
- material findings;
- gaps, blocked tracks, and dropouts;
- conflicts that need a lead decision;
- exact verification commands or source paths.

The primary agent owns final integration and verification. Worker consensus alone is not proof.
