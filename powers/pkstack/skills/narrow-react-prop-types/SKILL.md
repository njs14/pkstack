---
name: narrow-react-prop-types
description: Narrow React component prop types to the states used by live application call sites, then adapt stories, tests, and mocks to the stricter contract.
---

# Narrow React prop types

Treat the request text that activated this skill as the narrowing task. Treat production routes, wired components, providers, hooks, and exported production packages as the
contract. Stories, tests, fixtures, mocks, and demos are support code and must not widen it.

1. Find every import and usage of the component, its exported prop type, and affected child
   primitives. Classify each call site as live or support code.
2. From live call sites, classify each prop as required, meaningfully optional, nullable, or unused.
   Required nullable state is not an optional prop.
3. Tighten the exported type. Require handlers for always-rendered interactions and remove states
   no live path enters.
4. Prefer types derived from live APIs (`Parameters`, `ReturnType`, `Extract`, and React setter
   types) over duplicated approximations. Use explicit state generics when inference widens intent.
5. Tighten internal child props and remove fallbacks or optional calls that existed only for the
   widened contract.
6. Update all variants sharing the type. Make stories, tests, fixtures, and mocks supply realistic
   values; never loosen production types to reduce support-code setup.
7. Run the repository's formatter, package typecheck, affected consumer typechecks, and focused
   tests. Re-scan live call sites after the change.

Do not remove runtime states that real live call sites use. Report the components changed, live
evidence for each narrowing, support-code updates, exact checks, and risk.
