# Architecture design contract

Use this contract for every architecture candidate and for the lead decision.

## Candidate package

Write these sections in order:

1. **Problem and constraints.** Name the decision, existing behavior,
   compatibility constraints, non-goals, and gradeable criteria.
2. **Caller's usage.** Show the import and two or three realistic call sites.
   This is the specification for the public interface.
3. **Types and data structures.** Put data first. State invariants and trace the
   dominant reads and writes through the proposed structure.
4. **Signatures and scaffold.** Show functions, methods, classes, protocols,
   errors, and results. Bodies say `not implemented`; pseudocode explains only
   load-bearing logic.
5. **Module map.** For each module, name the knowledge it owns, what it exposes,
   what it depends on, where validation occurs, and how state moves.
6. **Rationale.** Explain the selected shape, interface depth, accepted
   tradeoffs, at least one concrete alternative, open risks, and the first
   implementation step.

The sections must agree. Do not change usage to make an awkward type sketch
look acceptable.

## Red-flag screen

Reject or revise a candidate when it has one of these shapes:

- **Shallow module:** callers coordinate a large surface but still need to know
  the implementation's rules.
- **Information leakage:** representation, protocol, or policy details have
  multiple owners and require synchronized edits.
- **Temporal decomposition:** load, validate, transform, and save modules repeat
  one representation instead of owning distinct knowledge.
- **Pass-through method:** a method forwards the same arguments without adding
  policy, adaptation, or a real abstraction.

Do not confuse interface depth with call depth. A deep interface hides policy
behind few operations. A deep call chain spreads policy across files.

## Lead comparison

For each candidate, answer:

- What complexity disappears from the caller?
- Which decisions remain exposed, and why must they be exposed?
- Are wire and storage representations private?
- Does one boundary validate each external input?
- Does each invariant have one owner?
- Can a normal flow be understood without chasing a long call chain?
- What happens on retry, partial failure, or two writers?
- Which criterion makes this shape better than each alternative?

Record the selected base, useful ideas incorporated from another candidate,
and rejected ideas with concrete reasons. Agreement among candidates is a
signal, not executable proof.
