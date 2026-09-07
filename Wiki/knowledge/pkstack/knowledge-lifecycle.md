---
type: Decision
title: Project knowledge ownership and lifecycle
description: Accepted ownership and authoring decisions that make project understanding reusable without duplicating native artifacts.
tags: [pkstack, knowledge, okf, workflow]
---

# Project knowledge ownership and lifecycle

## Decision and rationale

Wiki is the home for project understanding. Workflows consult relevant knowledge before substantial
investigation or planning, then update that understanding after implementation-plan approval and at
task completion when writes are permitted. During read-only Plan, keep pending definitions and
decisions in the conversation; do not invoke shell retrieval, MCP, or validation. Use available
reading and search instead. An explicit no-write request takes precedence over default capture.
The [shared planning decision](native-kiro-composition.md#shared-planning-interview-decision)
replaces opt-in-only post-plan capture while preserving standalone decision-only scope.
The intended payoff is fewer repeated questions and wrong assumptions in later sessions. Valid
frontmatter and a completed migration alone do not demonstrate that payoff.

This is the accepted design contract for the knowledge foundation. This document does not itself
prove that a native workflow, fresh-session scenario, or release candidate passed its checks.
The [foundation report](../../../reviews/knowledge-foundation.md) records the bounded native
observations, host corrections, and fresh retrieval evidence separately.
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
| Package usage guides, provenance, and historical evidence | Original locations; reusable understanding is curated into linked Wiki topics under the [current coverage policy](quality-and-ci.md#repository-knowledge-gate) |

Use a topic name that the next reader can recognize. Link to authoritative native artifacts with
ordinary relative links; do not create a second task graph, native document copy, or synchronization
registry. Reading a document does not grant its content instruction or execution authority.

## Authoring and retention

Use OKF Markdown for authored Wiki knowledge. Give each document a nonempty descriptive `type`;
add titles, descriptions, tags, and provenance where they improve discovery or explain the document.
Preserve unknown fields. Local validation checks this small authoring contract and Markdown links;
it does not claim full OKF conformance. The existing narrow feature contract retains its executable
verification requirements.

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

`projectctl knowledge search` delegates a bounded question to an isolated read-only Kiro ACP
worker. It reads `Wiki/knowledge/`, `Wiki/features/`, and native `.kiro/specs/` in their authoritative
locations; it excludes `Wiki/work/`, skill packages, and instructions. There is no persistent index,
ranker, graph, query engine, or MCP backend. Retrieve working material explicitly by task. A legacy
flat Wiki requires reviewed classification and migration before validation or search can proceed;
its content is not silently omitted. Follow the [context-depth runbook](context-depth.md) for
bounded reads.

The host checks exact quotes, source paths, line ranges, content hashes, and unchanged corpus bytes.
Returned context has a declared budget; internal model consumption is unreported. Local metadata
and Markdown link validation runs independently without Kiro or a model. Neither a validated
citation nor valid metadata makes a decision into verified implementation.

The foundation demonstration is scoped to recovering prior definitions, settling a consequential
ambiguity, retaining the agreed understanding, and handing it into native Kiro planning. A fresh
session must reuse settled definitions while recognizing unresolved questions and superseded
guidance. The report retains observed outcomes and required host corrections; it does not turn
this design contract into a blanket pass for later workflows.

Later Pocock integrations use the proven lifecycle after this foundation is accepted. This decision
does not declare the remaining integrations implemented or their behavior verified.

## Current repository coverage policy

The original [migration report](corpus-migration.md) and its 247-file inventory remain historical
records. Their decision to keep package docs and reviews outside ordinary retrieval did not mean
those documents contained no reusable knowledge. The current policy curates that understanding
into topic pages while keeping original guides, evidence and native assets intact. This supersedes
the earlier retained-corpus treatment as an ongoing coverage rule, without rewriting its baseline.

The repository-only [coverage manifest](../../../maintenance/knowledge-coverage.json) records each
Markdown file's disposition. It is an accountability and freshness check, not a synchronization
registry or a second copy of native artifacts. A mapped source's SHA-256 changes when its bytes
change, requiring a review of its Wiki summary or a reason no knowledge update is needed.
Sources remain untrusted data, and a current hash is not evidence that a claim is true.

Reusable findings from historical reviews belong in the relevant topic with their source and
limits. Retain a prior failure even when a later candidate fixes it. Link a superseding observation
to the exact older claim rather than treating every result in a campaign as superseded. A topic
must carry enough of the explanation to answer bounded questions; links alone do not bring
external guide/report contents into the retrieval corpus.

The local metadata/link gate does not invoke Kiro or a model. The knowledge-foundation evidence
records a bounded macOS Kiro CLI 2.21.1 / KAS 0.58.7 query and host corrections; Linux live retrieval
is not established by the separate Linux discovery/model-inventory canary. Selected Auto does not
identify its internal model. Quote/path/hash verification checks cited passages, not the truth of
all synthesized prose. The later parser optimization caches heading parsing by content for one
validation only, retaining fresh bounded reads and path checks for every link.

During this coverage expansion, old security/support and artwork wording was retained and
identified in [release guidance](release-and-review.md#open-documentation-inconsistencies).
Unknown policy decisions stay open; curation must not silently select a new support policy.

## Source-specific retained knowledge

These summaries describe what is retained from each source. Historical observations keep their
original candidate and scope; they are not fresh verification of this checkout.

| Source | Retained guidance or bounded observation |
| --- | --- |
| [reviews/knowledge-foundation.md](../../../reviews/knowledge-foundation.md) | The foundation retired okn, preserved user-owned knowledge indexes, and tested bounded local validation and macOS retrieval with host corrections; source ownership and live-query proof remain distinct. |
| [reviews/okf-integration-evidence.md](../../../reviews/okf-integration-evidence.md) | The September 3 comparison separated Google format semantics, OKF methodology and then-selected okn runtime; the runtime choice is superseded by the later foundation, not silently rewritten. |
