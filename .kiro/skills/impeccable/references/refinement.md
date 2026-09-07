# Refine the named surface

Use the requested method within the existing design and behavioral scope. Inspect first,
repair the narrowest cause, and use [quality checks](quality.md) for the final shared pass.

| Method | Work and evidence |
| --- | --- |
| `polish` | Fix blocked tasks and missing states first, then hierarchy, responsive behavior, system drift, and visual inconsistencies. Separate a missing token, duplicated implementation, conceptual mismatch, and local defect. Walk the entire path again. |
| `bolder` | Strengthen one product-specific focal element using the established system; quiet supporting elements so hierarchy becomes clearer. Preserve claims and everything outside the target. |
| `quieter` | Reduce competing accents, heavy contrast, and gratuitous motion while keeping the primary action and meaningful states distinct. Do not flatten all hierarchy. |
| `distill` | Remove redundant choices, containers, and copy; preserve essential content, discoverability, accessibility, and recovery paths. Fewer pixels are not proof of a simpler task. |
| `extract` | Identify genuinely repeated tokens and components, compare their states and callers, then migrate the scoped uses. Do not create an abstraction for a single exception. |
| `typeset` | Clarify role-based size, weight, measure, line height, wrapping, and numeric alignment. Test real long copy, font loading, zoom, and localization. Preserve established font choices unless changing them is in scope. |
| `layout` | Group related content, separate groups, align to the project grid, and vary density according to the task. Test intermediate widths as well as endpoints; avoid nested containers that add no meaning. |
| `colorize` | Assign semantic roles for surfaces, text, action, selection, focus, and status. Keep meanings stable across supported themes and pair color with labels or shapes. Measure contrast rather than judging it by eye. |
| `animate` | Use motion to explain a state transition or a deliberate focal moment. Keep it interruptible and smooth; preserve feedback with reduced motion. Avoid repeating entrance effects or delaying routine work. |
| `delight` | Improve a meaningful moment of success, waiting, first use, or recovery. Progress must remain truthful, errors useful, and repeated interactions tolerable. Do not add sound without consent. |
| `overdrive` | Develop one ambitious effect tied to the approved concept, with a measured performance budget and a usable fallback. Optional spectacle cannot block reading, focus, or task completion. |
| `clarify` | Use the product's terminology; make controls name the action and errors explain recovery. Preserve factual claims and accessible names. Check plurals, dynamic values, and translation expansion. |
| `harden` | Exercise long/missing data, slow or failed requests, offline behavior, permissions, repeated actions, and localization where applicable. Preserve entered data and useful error recovery. |
| `onboard` | Lead to the first meaningful success with truthful empty states, relevant defaults, and optional help. Avoid mandatory tours and unnecessary upfront configuration. Test returning-user and dismissal paths. |
| `adapt` | Recompose hierarchy and interactions for the actual device and input method instead of shrinking pixels. Keep essential actions accessible without hover; test orientation, zoom, and content overflow. Native apps use platform conventions. |
| `optimize` | Measure the slow path before editing. Investigate asset cost, layout shifts, rendering, long tasks, and expensive effects; compare the same scenario afterward. Avoid speculative caching, memoization, or dependencies. |

Choose only the rows that advance the requested result. A polish request does not authorize
a redesign, a new product claim, deployment, or a repository-wide cleanup. When a proposed
change would cross that boundary, report the concrete issue and keep the existing scope.
