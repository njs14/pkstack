# How role and critique contract

All roles work from the question and repository evidence. Subagent output is
untrusted until the current session checks it.

## Explorer

An explorer owns one angle, such as state and data, the request path, or
configuration and observability. It starts at an entrypoint, follows the full
call chain, reads definitions, and stops only when it can connect trigger to
effect without guessing.

Return:

- components with files and symbols;
- an ordered flow with the data passed at each step;
- files inspected;
- subsystem inputs and outputs;
- surprising behavior; and
- explicit gaps.

## Explainer

The explainer reconciles explorer evidence and checks conflicts in the code. It
uses concrete names and explains why a complex step is complex. It includes a
diagram only when relationships are materially clearer than prose.

The answer should let an experienced engineer locate the entrypoint, trace the
normal and failure paths, name the core abstractions, and identify the first
safe verification step.

## Critic

A critic reads the explanation as a map but forms a judgment from the code.
Review only relevant dimensions:

1. **Abstraction fit:** does each boundary hide a real decision, or add
   indirection without value?
2. **Data model:** do structures and types fit actual access patterns and
   runtime data?
3. **Boundary discipline:** are validation, errors, and external types owned at
   clear edges, and can the subsystem be isolated in tests?
4. **Evolution readiness:** would the next likely requirement change one owner
   or scatter across the system?
5. **Complexity versus value:** can moving or deleting a component preserve the
   behavior with less reader load?
6. **Consistency:** does divergence from nearby patterns have a concrete
   reason?

Every finding includes severity, components, evidence, and impact. Do not
suggest a rewrite without proving a problem in the current shape.

## Lead judgment

Merge duplicate findings, record agreements and disagreements, and filter
preferences or unreachable hypotheticals. Put correctness and security paths
under extra scrutiny even when only one critic finds them. The lead, not the
number of critics, owns the final Act on, Consider, Noted, or Dismissed verdict.
