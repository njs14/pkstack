---
name: figure-it-out
description: Solve an unfamiliar, ambiguous technical problem by turning it into bounded hypotheses, verifiable phases, and an auditable evidence trail.
compatibility: Kiro IDE 1.x and Kiro CLI v3; Kiro Crew compatible; Kiro Web supported by design but untested.
---

# Figure out an unfamiliar problem

Treat the request text that activated this skill as the outcome to make true.

Use this when no narrower PK-Stack workflow fits, or when a migration or
cross-cutting change is large enough that a human will review it after stepping
away. Route a focused bug, performance issue, feature, visual comparison, or
evaluation to its narrower playbook.

The first deliverable is the designed workflow, before code. Bias rigor upward
when uncertainty, blast radius, or reversibility demands it; rigor means gates
and evidence, not longer prose.

## Frame and choose rigor

Before starting implementation, return a framing block with:

- a falsifiable definition of done and explicit non-goals;
- quantified scope: approximate components, call sites, data sets, migrations,
  or user flows plus an effort range;
- known constraints, blockers, and highest-risk unknowns;
- a rigor level—bounded, standard, high, or critical—and the gates and
  artifacts that justify it; and
- one explicit checkpoint before any multi-hour autonomous run, including what
  evidence the user will see there.

Reversible investigation can continue while the framing is reviewed. Stop for
authority when the workflow would cross an external, destructive, public,
paid, or account-level boundary.

## Design the playbook

Write risk-first phases as atomic, independently landable units. Put the
highest-value unknown, scaffold, and verification harness before feature volume
so a failed premise is cheap to discard. For each phase, name:

1. the hypothesis or outcome;
2. inputs and owned files;
3. the smallest coherent change;
4. its verifier and expected evidence;
5. rollback or recovery; and
6. the condition for advancing.

Capture a baseline with the verifier against the pre-change state. If the
baseline cannot distinguish old from desired behavior, repair the observation
before implementation. Parallelize only genuinely independent phases and keep
their state separate until a deliberate merge.

Present the complete playbook and rigor choice before putting it into motion.
Update the playbook when evidence changes the plan; do not silently erase a
phase.

## Work in verifiable phases

For each unit:

1. State the smallest hypothesis that unlocks the next decision.
2. Choose the cheapest real-artifact observation that can disprove it.
3. Record the observation and update the working model before editing.
4. Make one reversible change and run its phase verifier.
5. Record one explicit verdict: **VERIFIED**, **NOT VERIFIED**, or
   **INCONCLUSIVE**. Inconclusive is not a pass.
6. Keep the change only when evidence advances the predicate. Revert or
   redesign when it does not; never weaken the gate to make work pass.
7. Run the multi-hour checkpoint at the designed boundary, then continue only
   under the agreed scope and authority.

Finish with the end-to-end predicate on the real product and nearby regression
checks proportional to risk. Delegated work remains untrusted until the current
session inspects its artifact and executes the verifier.

## Keep the audit trail

Activate [`show-me-your-work`](../show-me-your-work/SKILL.md) at the start and
append each material hypothesis, decision, phase result, and evidence pointer
as it occurs. A retrospective narrative is not equivalent. The work log stays
uncommitted by default; commit it only when the user explicitly requests a
review trail.

Use native Kiro sub-agents only for independent, bounded research or review.
Keep final synthesis and state ownership in the current Kiro session.

Return the designed playbook, selected rigor and why, checkpoint result,
decision-trail path, phase verdicts, achieved predicate and baseline
comparison, discarded hypotheses, and unresolved uncertainty.
