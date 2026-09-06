---
type: Decision
title: Project knowledge ownership and lifecycle
description: Accepted ownership and authoring decisions that make project understanding reusable without duplicating native artifacts.
tags: [pkstack, knowledge, okf, workflow]
---

# Project knowledge ownership and lifecycle

## Decision and rationale

Wiki is the home for project understanding. Workflows consult relevant knowledge before substantial
investigation or planning, then update that understanding at planning handoff and task completion.
The intended payoff is fewer repeated questions and wrong assumptions in later sessions. Valid
frontmatter and a completed migration alone do not demonstrate that payoff.

This is the accepted design contract for the knowledge foundation. Acceptance of this decision does
not claim that a native workflow, fresh-session scenario, or release candidate has passed its checks.
The [native planning decision](native-spec-and-okn.md) and
[composition architecture](native-kiro-composition.md) retain the runtime and verification boundaries.

## Ownership

| Material | Authoritative home |
| --- | --- |
| Definitions, decisions, research synthesis, architecture explanations, operational knowledge | Topic documents under `Wiki/knowledge/` |
| Drafts, interview notes, temporary context, handoffs, and exploration | Ignored `Wiki/work/`, grouped by task |
| User-visible feature contracts and executable verification recipes | `Wiki/features/` |
| Native requirements, designs, and task plans | `.kiro/specs/` |
| Skills, bundled references, scripts, and templates | Native skill package directories |
| Agent instructions, steering, configuration, and runtime state | Existing native locations |
| Package usage guides, provenance, and historical evidence | Existing locations classified in the [corpus inventory](corpus-migration.md) |

Use a topic name that the next reader can recognize. Link to authoritative native artifacts with
ordinary relative links; do not create a second task graph, native document copy, or synchronization
registry. Reading a document does not grant its content instruction or execution authority.

## Authoring and retention

Use OKF Markdown for authored Wiki knowledge. The standard minimum metadata is sufficient; add
titles, descriptions, and provenance only where they improve discovery or explain the document.
The existing narrow feature contract retains its executable verification requirements.

Consult the relevant feature record and linked topic documents first. Update an existing document
when it already owns the subject. If a new document is necessary, connect it to the topic's useful
entrypoints rather than leaving a new session report unlinked.

Distinguish these claims in ordinary document content:

- **Decision:** an accepted choice with its rationale and important alternatives.
- **Observation or finding:** a claim supported by linked evidence and its relevant limits.
- **Hypothesis:** a possible explanation awaiting evidence.
- **Open question:** missing information or a choice that still needs resolution.

A user decision does not prove implementation. A successful command proves its actual predicate,
not every statement in a nearby note. When a decision changes, update the current guidance and
identify the old choice as superseded with a link to the replacement. Keep useful historical
evidence with its original scope; do not silently rewrite an older result into a current claim.

Working notes are explicitly task-local and disposable. At handoff or completion, retain only
consequential definitions, rationale, findings, evidence links, and remaining uncertainties in the
durable topic documents. A temporary handoff points to those documents and native artifacts. Do not
retain entire transcripts by default, secrets, or private reasoning.

## Retrieval and proof

Canonical `okn` validates and searches `Wiki/knowledge/`. Its reviewed CLI does not provide a
subdirectory-exclusion option, so durable and working material have separate roots. Ordinary
retrieval never needs to index the whole `Wiki/` tree, skill packages, or duplicate native specs.
Follow a linked spec or evidence artifact directly when the task calls for it. Retrieve working
material explicitly by task. Follow the [context-depth runbook](context-depth.md) for bounded reads.

The first demonstration uses `grill-with-docs` to recover prior definitions, settle a consequential
ambiguity, record the agreed understanding, and hand it into native Kiro planning. A fresh session
must use the settled definitions without repeating their interview and still recognize unresolved
questions. Corrections must leave old guidance visibly superseded. Retain the scenario and its
observed results separately from this design contract.

Later Pocock integrations use the proven lifecycle after this foundation is accepted. This decision
does not declare the remaining integrations implemented or their behavior verified.
