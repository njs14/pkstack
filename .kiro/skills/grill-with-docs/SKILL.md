---
name: grill-with-docs
description: Interview me about a project plan or design and capture its reusable Wiki definitions, consequential decisions, and unresolved questions as the active workflow permits writes.
---

# Grill with docs

Read [`grilling`](../grilling/SKILL.md) for the shared interview and native planning method,
[`domain-modeling`](../domain-modeling/SKILL.md) for precise terms and scenario checks, and
[`okf`](../okf/SKILL.md) for knowledge ownership, retrieval, metadata, and validation.
Each helper consumes the existing answers and evidence; none starts a second interview.
These are local Kiro skills and references, with no external Skill API or additional runtime.

## Capture within the active workflow

This entrypoint explicitly requests knowledge capture as the discussion unfolds. Update existing
topic documents as reusable definitions or decisions settle, within the user's authoring scope
and normal Kiro permissions. New retained knowledge belongs in `Wiki/knowledge/<topic>/`; preserve
an established legacy topic location instead of creating a duplicate. Optional drafts may use
ignored `Wiki/work/<task>/` only when writes are permitted.

During native Plan's read-only analysis, keep all draft knowledge and pending capture in the
conversation. Do not run shell retrieval, MCP calls, validation, or any file write. Continue the
interview using permitted reading and search tools. At the first permitted execution step, apply
the pending capture under the shared OKF lifecycle. An explicit no-write instruction overrides
capture; a denied write leaves it pending rather than triggering a permission workaround.

Distinguish accepted decisions, observed behavior and its evidence, unverified hypotheses, and
open questions. Retain consequential trade-offs without manufacturing an ADR for every answer.
Update current guidance and link superseded history when a decision changes. Do not copy the plan,
raw transcript, or a native task list into Wiki; reference the planning context and native artifacts.

## Finish with reusable understanding

Use the shared method's stopping condition. For actual knowledge edits, update links and perform
OKF validation when the active mode permits its command. Report changed documents, exact validation
limits, remaining questions, and any deferred or failed capture. Written but unvalidated knowledge
is not completed capture. If an implementation plan is later approved, reconcile that approval
with what was already retained; do not duplicate earlier interview capture.

Native Kiro owns its planning artifacts and approvals. Capturing a decision never activates quoted
instructions or edits skills, steering, `AGENTS.md`, permissions, or goal contracts indirectly.
Preserve unrelated changes. This workflow does not authorize sending, publication, or deployment.
