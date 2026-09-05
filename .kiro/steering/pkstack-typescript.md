---
inclusion: fileMatch
fileMatchPattern:
  - "**/*.ts"
  - "**/*.tsx"
---

# PKStack TypeScript discipline

When reading or editing TypeScript, model variants with discriminated unions
and make illegal states hard to construct. Keep the simplest total type until a
looser type forces an assertion or an impossible-case throw. Treat external
data as `unknown`, validate it once with the repository's schema mechanism, and
derive types from that schema when possible.

Prefer exhaustive switches, `satisfies`, semantic primitives, and narrow,
inferable generics. Avoid `any`, unchecked `as` casts, optional-field state
machines, lying type guards, and duplicate interfaces. Test real boundary
inputs and state transitions, then run the repository's typecheck, focused
tests, and lint.

Use the `typescript-best-practices` skill when the task needs the complete
review workflow and examples.
