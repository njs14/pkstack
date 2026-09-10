# Keep standards and specification review separate

Pin the requested base, exact head/tree, and dirty diff if included. Derive a merge base for branch
review, but inspect working changes too when the user requested work in progress. Verify the refs
resolve and explain an empty scope. Recover specification intent from the request, active native
Spec, linked issue, and commits. Identify applicable repository standards and their authority.

In the bounded review packet, include the same candidate identity, scope, acceptance criteria,
and sources for independent reviewers. Report these two axes independently alongside interrogate's
correctness and quality lenses:

- Specification: missing, partial, incorrect, or unrequested behavior, with the requirement and
  reachable evidence. If no specification can be recovered, report unavailable scope and the
  explicit intent used; do not call missing evidence a pass.
- Repository standards: violations of documented rules with the rule's source and affected path.
  Design smells are labeled judgment calls, never invented hard rules. Relevant smells include
  obscure names, duplication, feature envy, data clumps, primitive obsession, repeated switches,
  scattered changes, divergent responsibilities, speculative abstractions, message chains,
  pass-through layers, and inheritance that rejects its contract. Repository rules and actual
  needs govern; tooling findings need not be re-proved manually.

Preserve each axis's finding, severity, evidence, and result before lead synthesis. A passing axis
cannot erase a failure in the other. Deduplication can link the same underlying cause while keeping
both consequences visible. Independent findings still receive the lead's Act on / Consider / Noted /
Dismissed judgment; review consensus remains advisory and never replaces executable validation.
