# OKF skills source parity

This is the human-readable view of the
[source-scoped machine inventory](okf-skills-parity.json) for
`scaccogatto/okf-skills` at commit `bf2448f03686a8348324e4741106697d30a867f9` and
`skills/` tree `8cc9ed3986cf6c942f718439e1ee8249eb17a2ad`. The JSON accounts for all 13
regular blobs by Git object identity, mode, size, and A/B/C disposition. No upstream file is
redistributed by these records.

| Disposition | Files | Meaning |
|---|---:|---|
| A | 4 | Adapt the durable workflow semantics into native Kiro and projectctl contracts. |
| B | 4 | Explicitly exclude unsafe or unready runtime behavior. |
| C | 5 | Retain as provenance or design evidence without copying or executing it. |

## Package decisions

| Package | Decision | PK-Stack treatment |
|---|---|---|
| `okf` | Native Kiro replacement | Adapt produce, maintain, consume, progressive-disclosure, index, and bounded-log ideas into the PK-Stack `okf` skill and `Wiki/` lifecycle. Google remains normative and `okn` remains the runtime. |
| `validate` | Native deterministic replacement | Preserve validate-before-completion behavior through `projectctl knowledge validate` and canonical `okn`; do not invoke or copy the upstream validator. |
| `visualize` | Deferred/excluded | Reconsider only after an offline, dependency-pinned, symlink-safe, hostile-Markdown-tested implementation exists. Never auto-open or publish its output. |
| `backfill` | Excluded by default | A future import must be separately authorized, bounded, redacted, resumable, and outside-repository by default. Do not crawl Claude, Kiro, Codex, home-directory, or transcript history implicitly. |

The upstream `backfill` skill refers to Claude-specific agent files outside the tracked `skills/`
tree. Because backfill is excluded, this artifact deliberately does not claim a runnable dependency
closure. Making it runnable would first require a new review and explicit pin for that dependency
boundary.

The upstream `okf/reference/SPEC.md` is an older vendored Google snapshot. It has disposition C and
cannot override the independently tracked [current Google OKF source](okf-spec-source-parity.md).
PK-Stack's examples follow the current explicit-offset datetime rules.
