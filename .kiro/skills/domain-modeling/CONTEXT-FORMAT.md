# Topic glossary format

Keep one glossary for each coherent domain context. Use an existing topic's glossary if it
exists. For a new context create `Wiki/knowledge/<topic>/glossary.md` only when there is a term
to retain, and link it from the relevant topic or feature entry. Use the shared OKF lifecycle
for metadata and validation.

```markdown
---
type: glossary
title: Ordering vocabulary
---

# Ordering vocabulary

Terms used when a customer places and changes an order.

**Order**: The customer's accepted request for a set of items.
Avoid using “purchase” for this concept; payment is a separate event.

**Cancellation**: Ending an order before fulfillment begins.
Partial item removal is an **amendment**, not a cancellation.

## Open questions

Whether an amendment can increase quantity after acceptance remains undecided.
```

Keep definitions short and specific to this context. Name misleading synonyms when the
contrast prevents ambiguity. General programming vocabulary needs no glossary entry unless
this project assigns it a particular meaning. Group terms only when useful clusters emerge.
Separate unresolved meanings from settled definitions.

When two contexts intentionally use a word differently, preserve both qualified meanings
and link their topic glossaries. Add context relationships to an existing Wiki navigation or
topic document when they help a reader find the right meaning. A new root `CONTEXT.md` or
`CONTEXT-MAP.md` is not required.

Link to code, evidence, or native specs when needed to support a claim; keep implementation
design out of the glossary. Existing legacy context documents are inspected and reconciled
within the user's migration scope, not silently copied into a competing glossary.
