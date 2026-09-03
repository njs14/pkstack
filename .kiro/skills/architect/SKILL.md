---
name: architect
description: Design or revise a component through grounded architecture analysis, structurally distinct alternatives, explicit tradeoffs, and executable verification. Use for system boundaries, APIs, data models, migrations, or high-impact refactors.
compatibility: Kiro IDE 1.x and Kiro CLI v3; Kiro Crew compatible; Kiro Web supported by design but untested; projectctl knowledge and feature commands are optional but preferred.
---

# Architect a change

Treat the request text that activated this skill as the architecture request.

After PK-Stack setup, `<runner>` means exactly `.pstack/bin/projectctl`. Do not
select an ambient `projectctl` or repository-owned `./projectctl`.

Use Kiro's native execution and context. This skill supplies decision
semantics; it is not a separate planner runtime. Read
[`references/design-contract.md`](references/design-contract.md) before
comparing candidates.

## Ground the decision

1. Inspect the relevant code, tests, feature record, and repository guidance.
   If the request is already backed by `.kiro/specs/<name>/`, treat its requirements or bug
   analysis, design, and tasks as Kiro's planning authority. Challenge or refine that design in the
   native spec workflow; do not create a competing architecture plan inside this skill.
2. Record the context depth and why it is needed. For an architecture decision, issue at most one
   targeted `<runner> knowledge search "<specific decision>" --budget 1200 --output json` when
   canonical `okn` is available, then reconcile that KNOW result with `<runner> feature list` and
   `<runner> feature show <slug>`. Follow explicit related links; never inject the whole Wiki.
3. Use `how` to trace the affected runtime. Use `why` when the proposal changes
   an existing ownership or layering decision. Mark inferred rationale.
4. At each external-data boundary, find the repository's existing runtime
   schema mechanism before hand-writing property guards. Prefer one source for
   validation and type derivation; do not add a dependency to avoid a small,
   honest parser.
5. Define the decision, constraints, non-goals, and three to six gradeable
   criteria before proposing a solution.

Skip this grounding only for genuinely isolated greenfield work.

## Produce the scaffold before code

Every viable candidate must be an inspectable usage-first scaffold:

1. Write the caller's usage first, including imports and two or three realistic
   call sites.
2. Derive the core data types from that usage. State invariants and show that
   the structures support the dominant access patterns.
3. Sketch public function and method signatures, class or protocol shapes, and
   failure results. Use explicit `not implemented` bodies and short pseudocode
   only where a tricky algorithm needs orientation.
4. Draw the module map: each module's owned knowledge, public surface,
   dependencies, state, and boundary validation.
5. Write the rationale: problem and constraints, chosen shape, accepted
   tradeoffs, concrete alternatives, open risks, and first implementation step.

The usage, types, signatures, module map, and rationale are one contract. If
they disagree, reconcile the scaffold to the caller's experience before code.
When a native spec exists, this output is an advisory delta against its `design.md`, not a second
design package. Apply each accepted delta back to the native design before Kiro's tasks proceed.

## Run the architecture arena

Produce at least two structurally distinct, usage-first scaffolds. Native Kiro
sub-agents may create isolated read-only candidates, but the current session
owns the comparison and decision. Renaming the same structure does not create
another candidate.

Screen every candidate for these red flags before scoring it:

- a shallow module with a large surface that hides little complexity;
- information leakage that makes several modules know one private decision;
- temporal decomposition into stages that share one representation; and
- pass-through methods that add no policy, adaptation, or abstraction.

Then score the survivors against the criteria and call out irreversible
consequences. Recommend one with decisive reasoning. Preserve an idea from a
losing candidate only when it fits the selected shape coherently.

## Enforce interface depth

Prefer the smallest public surface that hides the most policy and complexity.
A deep module is not a deep call chain: concentrate capability behind a simple
interface and keep the normal flow traceable through at most a few files.

- Keep transport, storage, and wire types behind their owning boundary.
- Validate once at entry, then use honest domain types internally.
- Put business rules in testable domain functions and keep integration shells
  thin.
- Give each invariant one owner; derive secondary views instead of syncing them.
- If several actors can write state, prefer separate ownership and merge at a
  read boundary unless serialization is a proved requirement.
- Specify retry, crash, and repeated-call behavior for state transitions.

The rationale must state what the interface hides, what callers still need to
know, and why each exposed operation earns its place.

Create an explicit checkpoint only when the user requested one or the decision
would authorize an external, destructive, public, paid, or account-level
action.

## Implement and verify

When implementation is in scope:

1. Fill in the selected scaffold rather than silently redesigning it while
   coding. Record every signature, type, or module deviation and its reason.
2. Make the smallest coherent change that realizes the selected boundary.
3. Generate or update the relevant feature map through `<runner>` rather than
   hand-editing generated output.
4. Verify the feature with `<runner> feature verify <slug> --output json` or
   `<runner> verify <slug> --output json`.
5. If two or more deviations repeat the same structural shape, scrap the
   scaffold, re-ground with the implementation evidence, and run the arena
   again instead of patching symptoms.

Return the usage-first scaffold, rationale and rejected alternatives, changed
boundaries, recorded deviations, exact verification evidence, and remaining
risks.
