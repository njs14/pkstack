---
name: domain-modeling
description: Resolve ambiguous project terminology and domain relationships against concrete scenarios and code, and maintain the resulting glossary and consequential decisions.
---

# Domain modeling

Use this skill when changing or clarifying the domain model, including reusable definitions
and decisions from an approved implementation plan. Merely reading an existing glossary does
not require a modeling session. Read [`grilling`](../grilling/SKILL.md) for consequential
questions and native planning boundaries; consume its settled context instead of restarting the
interview. Read [`okf`](../okf/SKILL.md) for the shared knowledge lifecycle, bounded retrieval,
and validation before writing project documents.

## Start with the current understanding

Read `Wiki/index.md`, the relevant feature record, and linked topic knowledge or native specs.
Find the existing glossary and decisions before creating files. Prefer the established topic
location, including a legacy Wiki location pending migration; do not create a second glossary
for the same context. New topic knowledge belongs in `Wiki/knowledge/<topic>/`. Skills and
operational instructions remain in their native directories.

## Make meanings precise

- When a term conflicts with the glossary, identify both meanings and the consequence of the
  difference. Resolve the actual ambiguity rather than asking the user to restate settled terms.
- Propose a precise canonical term for an overloaded word. Preserve distinct meanings when
  they belong to different contexts instead of forcing a global definition.
- Test relationships with concrete scenarios: ownership transfers, partial operations, lifecycle
  transitions, and cases that distinguish adjacent concepts. Choose scenarios relevant to this
  domain rather than an exhaustive edge-case inventory.
- Inspect code and authoritative `.kiro/specs/` artifacts when they can substantiate a claim.
  Surface contradictions between desired behavior and observed behavior; neither silently
  overwrites the other.

## Capture what changes

When a definition settles, update the existing topic document under the user's knowledge-authoring
scope or the approved-plan capture checkpoint, once the active workflow permits writes. In native
Plan, keep candidate definitions and pending capture in the conversation; do not run shell commands,
MCP calls, or validation, or write even temporary files. An explicit no-write instruction takes
precedence. Reconcile existing entries before writing so repeated approval or helper composition
does not duplicate knowledge. For a new glossary use [`CONTEXT-FORMAT.md`](CONTEXT-FORMAT.md).
Keep implementation plans out of term definitions; link to their authoritative native specs.
When writes are permitted, optional draft interpretations and unfinished interview context may
use ignored `Wiki/work/<task>/`; otherwise retain them in the conversation. Keep unverified
hypotheses explicit when useful findings enter durable knowledge.

Record accepted decisions and their rationale separately from verified observations,
hypotheses, and open questions. A user accepting a design does not prove the code implements
it. Add an ADR when the choice has meaningful reversal cost, a non-obvious rationale, and
real alternatives. Otherwise a short update to the existing topic is sufficient. Read
[`ADR-FORMAT.md`](ADR-FORMAT.md) when a decision record is warranted.

For a changed definition or decision, update current guidance and mark the prior guidance
superseded with a replacement link. Retain useful rationale; do not leave contradictory
statements looking equally current. Preserve unrelated edits and unknown metadata.

After edits, check the updated links and run shared OKF validation when permitted. Denied writes
or failed/deferred validation leave capture incomplete; report that state explicitly. Report which
meanings changed, their supporting sources, and what remains unresolved. Knowledge maintenance
does not authorize edits to skills, steering, `AGENTS.md`, permissions, or native verifier
bindings. Hand accepted understanding to native Kiro planning through links and concise
context; do not create a second requirements or task graph.
