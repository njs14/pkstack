---
name: architect
description: Design or revise a component through grounded architecture analysis, structurally distinct alternatives, explicit tradeoffs, and executable verification. Use for system boundaries, APIs, data models, migrations, or high-impact refactors.
compatibility: Kiro CLI v3; projectctl knowledge and feature commands are optional but preferred.
---

# Architect a change

Architecture request: $ARGUMENTS

After PK-Stack setup, `<runner>` means exactly `.pstack/bin/projectctl`. Do not
select an ambient `projectctl` or repository-owned `./projectctl`.

Use Kiro's native execution and context. This skill supplies decision semantics; it is not a separate planner runtime.

## Ground the decision

1. Inspect the relevant code, tests, feature record, and repository guidance.
2. When `<runner>` is available, use `<runner> knowledge search`, `<runner> feature list`, and `<runner> feature show <slug>` to recover existing intent and evidence.
3. State both **how** the current system works and **why** its boundaries appear to exist. Mark inference as inference.
4. Define the decision, constraints, non-goals, and 3-6 gradeable criteria before proposing a solution.

## Run the architecture arena

Produce at least two structurally distinct, usage-first sketches. Each sketch should show the public call shape, main types or modules, ownership boundaries, failure behavior, and verification seam. Renaming the same structure does not create another candidate.

Score the candidates against the stated criteria, call out irreversible consequences, and recommend one with the decisive reasoning. Preserve useful ideas from losing candidates only when they fit the chosen design coherently.

Create an explicit checkpoint or request approval only when the user asked for one or the decision would authorize an external, destructive, public, paid, or account-level action.

## Implement and verify

When implementation is in scope:

1. Make the smallest coherent change that realizes the chosen boundary.
2. Generate or update the relevant feature map through `<runner>` rather than hand-editing generated output.
3. Verify the feature with `<runner> feature verify <slug> --output json` or `<runner> verify <slug> --output json`.
4. If repeated deviations have the same structural shape, scrap that approach and re-run the arena instead of patching symptoms.

Return the decision, rejected alternatives, changed boundaries, exact verification evidence, and remaining risks.
