# PK-Stack principle catalog

This file is the canonical wording behind the individually discoverable `principle-*` skills.
Apply a principle only when its trigger fits the work.

## Boundary discipline

Trigger: data crosses a CLI, configuration, file, network, database, or external API boundary.

- Parse and validate once at the boundary into a domain value.
- Keep framework and transport representations out of the core.
- Put business decisions in small functions that can be tested without the boundary.
- Do not scatter defensive checks through already validated internal paths.

Test: Is this value crossing a boundary now? If not, explain why another guard is necessary.

## Build the lever

Trigger: non-trivial repeated work, a migration, a sweep, or a claim that needs repeatable proof.

- Learn the recipe on one unit, then encode the smallest rerunnable script, generator, check, or
  delegated-work contract.
- Prefer one deterministic lever to many hand edits.
- Make reruns safe and keep the lever when the work will recur.

Test: Can a reviewer rerun one artifact instead of redoing the work by hand?

## Encode lessons in structure

Trigger: the same correction or instruction appears more than once.

- Prefer an unrepresentable invalid state, compiler check, lint, CI gate, canonical helper, or
  runtime validation over another reminder.
- Keep prose only where judgment is unavoidable.
- Prove the structural guard catches the observed failure.

Test: Would the next agent fail automatically if it repeated this mistake?

## Exhaust the design space

Trigger: a novel interaction or architectural decision has several viable shapes and no local
precedent.

- Produce two or three structurally distinct sketches or prototypes.
- Compare them against the same explicit criteria.
- Stop once constraints or evidence identify a winner; do not multiply cosmetic variants.

Test: Do the alternatives differ in boundaries or user experience, not only names?

## Experience first

Trigger: product scope, interface, or workflow convenience conflicts with the user experience.

- Optimize the core user loop before adding surface area.
- Prefer fewer complete behaviors to many rough ones.
- Include failure, feedback, accessibility, and maintenance experience in the design.

Test: Explain the decision from the consuming user's position.

## Fix root causes

Trigger: debugging, regressions, or a proposed guard that merely suppresses a symptom.

- Reproduce before editing.
- Trace the failing value or state to where it first becomes wrong.
- Instrument uncertainty and search for sibling instances of the same pattern.
- Treat restart-only failures as a reason to inspect persisted state before adding code guards.

Test: Would the original symptom return through a nearby path after this fix?

## Foundational thinking

Trigger: choosing core data structures, state ownership, concurrency boundaries, or phase order.

- Model data and access patterns before writing orchestration.
- Build shared verification and scaffolding before dependent features.
- Isolate mutable state before concurrent work.
- Keep explicit code until an abstraction removes a real repeated decision.

Test: Does this early structure reduce later branches and preserve options?

## Guard the context window

Trigger: large outputs, long files, repeated reads, or broad parallel exploration threaten useful
working context.

- Read only material needed for the current decision.
- Give bounded independent research to sub-agents when available and retain compact findings.
- Keep frequently used rules close; load detailed references only when triggered.
- Cap each phase and summarize before moving on.

Test: Will this input change the next decision? If not, leave it out.

## Laziness protocol

Trigger: a refactor or feature starts adding wrappers, layers, duplicated decisions, or signal
threading.

- Look for deletion and direct paths first.
- Collapse one-caller pass-throughs and interfaces that hide no complexity.
- Keep mutable state narrow and one source of truth for each decision.
- Build the smallest maintainable solution that proves the requirement.

Test: Would a maintainer find this shape tiring to trace or change?

## Make operations idempotent

Trigger: commands, lifecycle steps, scheduled jobs, or loops can be retried after interruption.

- Detect and reconcile existing state.
- Use atomic writes or transactions for coupled state.
- Make cleanup target exact owned resources.
- Test a second run and interruption at each write boundary.

Test: Does every starting partial state converge to the same valid result?

## Migrate callers, then delete legacy APIs

Trigger: an internal API is being replaced and coordinated callers can move together.

- Inventory callers and external compatibility obligations first.
- Move internal callers and remove the old path in the same bounded wave.
- Time-box a temporary adapter only when a real external consumer requires it.
- Remove tests that protect only the retired implementation.

Test: Is any retained compatibility path serving a verified consumer?

## Minimize reader load

Trigger: code is hard to trace because of indirection or hidden mutable state.

- Collapse layers that do not change the abstraction.
- Prefer locals and returned values over wider synchronized state.
- Name each invariant once at its boundary.
- Require every interface to hide a meaningful decision or implementation burden.

Test: Can a new reader find where a value comes from and what changes it quickly?

## Model the domain

Trigger: stateful logic accumulates booleans, repeated shape assumptions, or branching across files.

- Use a state machine, sum type, registry, command model, or another structure that matches the
  actual domain.
- Encode invariants in construction rather than scattered conditionals.
- Do not add abstraction when the local explicit shape is already clear.

Test: Which invalid states or repeated branches does the new model remove?

## Never block on the human

Trigger: routine reversible work is about to pause for a preference the request already implies.

- Make a reasonable, visible choice and proceed on reversible in-scope work.
- Ask only when missing intent materially changes the result or new authority is required.
- Always stop for destructive, irreversible, public, paid, privileged, or account-level action
  unless the user already authorized that exact action.

Test: Is the question necessary for safety or scope, or only reassurance?

## Outcome-oriented execution

Trigger: a planned migration or rewrite has explicit phases and a verifiable target architecture.

- Optimize for the declared end state rather than permanent temporary compatibility.
- Declare where intermediate breakage is allowed and keep it reversible.
- Run high-signal checks at phase boundaries and full verification at completion.

Test: Does each temporary step have an owner, boundary, and removal condition?

## Prove it works

Trigger: before claiming a task, change, or feature is complete.

- Exercise the real artifact and user-visible path.
- Inspect outputs and side effects, not only compilation or a self-report.
- Prefer a deterministic rerunnable check and keep important evidence visible.
- Mark missing direct proof as inconclusive rather than passing.

Test: What observation would fail if the claim were false?

## Redesign from first principles

Trigger: a new requirement cuts across an existing design and a bolt-on would duplicate policy.

- Understand the whole affected boundary first.
- Design the shape that would exist if the requirement had been present from the start.
- Propagate the decision through types, callers, tests, docs, and examples.
- Deliver the coherent redesign in verifiable increments.

Test: Does the final structure contain one integrated rule or an old path plus exceptions?

## Separate before serializing shared state

Trigger: concurrent actors can write the same file, branch, key, or mutable object.

- Give actors independent outputs whenever one shared object is not a true invariant.
- Merge independent facts at a read boundary.
- When sharing is essential, use a single writer, lock, transaction, or compare-and-swap.
- Never treat instructions to take turns as concurrency control.

Test: Can separate ownership remove the race before a lock is introduced?

## Sequence verifiable units

Trigger: a sweep, migration, or delivery contains several dependent changes.

- Make each unit small enough to end in a meaningful check.
- Verify each unit before building on it.
- Order delivery so the evidence tells the story: baseline before treatment, failing regression
  before fix, scaffold before dependent feature.

Test: If this unit fails, can it be identified and reversed without untangling later work?

## Subtract before you add

Trigger: an addition, rewrite, or refactor is landing in an already complex area.

- Remove dead paths, duplicated checks, and stale references first.
- Build against the smaller surface.
- Avoid speculative options and validators with no observed requirement.

Test: What can disappear before the new behavior is introduced?

## Type-system discipline

Trigger: designing types or function boundaries in a statically typed language.

- Make illegal states unrepresentable with variants and constructive types.
- Give semantic primitives distinct types.
- Parse external data once, derive types from authoritative schemas, and exhaust variants.
- Do not hide uncertainty with unsafe casts or assertions.
- Strengthen a type only where it makes an operation total or enforces a real invariant.

Test: Would the compiler identify every caller affected by a new variant or invalid combination?
