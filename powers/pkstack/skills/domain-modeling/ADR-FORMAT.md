# Topic decision format

Use an existing decision record or topic document when it can hold the change clearly.
Create a separate record under `Wiki/knowledge/<topic>/decisions/` only for a consequential
choice whose reversal cost, non-obvious rationale, and alternatives merit future explanation.
Follow existing names and numbering within that topic; otherwise use a descriptive slug.

```markdown
---
type: decision
title: Ordering owns cancellation eligibility
---

# Ordering owns cancellation eligibility

Accepted decision: Ordering decides whether an order can be cancelled. Fulfillment reports
whether work has begun. Keeping the decision with the order lifecycle avoids conflicting
eligibility rules across the two contexts.

We considered letting Fulfillment decide, but it lacks the order's commercial constraints.

Implementation status: proposed behavior; not yet verified in code.

Related: [Vocabulary](../glossary.md), [native design](../../../../.kiro/specs/order-cancellation/design.md).
```

Use only links that exist in the actual project; the example path illustrates a native
artifact reference, not a file to generate. An ADR can be a short paragraph with valid OKF
frontmatter. Add alternatives, consequences, and evidence only when they explain the choice.
Record sources actually inspected. Keep acceptance, observation, and verification distinct.

When the choice changes, mark the old record superseded and link the replacement; the new
record explains what changed and why. Preserve useful historical rationale without leaving
obsolete advice apparently current. If the old guidance was a section in a topic document,
update that section and link retained decision history rather than duplicating the document.

Do not turn interview notes, routine implementation choices, or every rejected idea into
ADRs. Keep temporary discussion in ignored `Wiki/work/<task>/`; retain only useful knowledge.
