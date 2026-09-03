---
name: typescript-best-practices
description: Design or review TypeScript with constructive domain types, boundary schemas, exhaustive variants, and tests that exercise runtime uncertainty.
compatibility: Kiro IDE 1.x and Kiro CLI v3; Kiro Crew compatible; Kiro Web supported by design but untested.
---

# Apply TypeScript type discipline

Treat the request text that activated this skill as the TypeScript change or review target.

Inspect the repository's compiler settings, runtime schema library, lint rules, and local patterns
before proposing a new abstraction. Model state with discriminated unions and semantic primitives
when they remove invalid combinations. Accept external data as `unknown`, validate it once at the
boundary with the existing schema mechanism, and derive types from the authoritative schema where
possible.

Avoid `any`, unchecked assertions, broad index signatures, optional-field state machines, and guards
that only repeat an interface. Exhaust variants so a new case breaks every affected caller. Keep
generics narrow and inferable; prefer a direct concrete type over type-level cleverness.

Test valid and invalid runtime inputs, narrowing behavior, each state transition, and serialization
boundaries. Run the repository's typecheck, focused tests, and lint. Report strengthened invariants,
remaining assertions with reasons, and any runtime behavior not covered by types.
