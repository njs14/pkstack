---
type: Report
title: Selective knowledge corpus migration
description: Baseline Markdown inventory, reviewed document moves, and explicit native, package, and historical exceptions.
tags: [pkstack, knowledge, migration, provenance]
---

# Selective knowledge corpus migration

## Scope and evidence boundary

The [machine-readable inventory](corpus-inventory.json) accounts for all **247 tracked Markdown
files** at commit `ca9f3e9b7984049b8b52b8d9e4aa95587ee12afa`. It records each original path exactly
once, the selected category, and the disposition. New files added by this knowledge-foundation
delivery are outside that baseline inventory.

This is the review record for a selective repository migration. It is not an executable manifest,
an automatic consumer-project migration, or evidence that the current implementation passes its
acceptance checks. Git history retains the original documents at the baseline commit.

## Selected moves

The three existing durable Wiki documents remain useful project knowledge. Their content moves to
one recognizable topic, with relative links repaired and the accepted ownership decision connected:

| Baseline location | Canonical location |
| --- | --- |
| `Wiki/architecture/native-kiro-composition.md` | [Native Kiro composition](native-kiro-composition.md) |
| `Wiki/decisions/native-spec-and-okn.md` | [Native planning and bounded Kiro retrieval](native-spec-and-okn.md) |
| `Wiki/operations/context-depth.md` | [Context-depth runbook](context-depth.md) |

The [knowledge lifecycle decision](knowledge-lifecycle.md) records the accepted authoring and
retrieval contract. It does not turn earlier release reports or native product observations into
fresh verification. The feature map retains its narrow executable contracts and links to these
durable explanations. The filename `native-spec-and-okn.md` remains stable for link continuity;
its current decision supersedes `okn` with bounded Kiro ACP retrieval and local validation while
retaining the original rationale as history.

## Retained corpus

| Category | Baseline files | Treatment |
| --- | ---: | --- |
| Durable project knowledge | 3 | Move to `Wiki/knowledge/pkstack/` |
| Feature contracts and navigation | 2 | Preserve `Wiki/features/` |
| Wiki navigation | 1 | Update links in place |
| Canonical native skill packages | 78 | Preserve definitions and bundled resources in the Power |
| Generated native skill packages | 77 | Preserve setup ownership; regenerate through setup |
| Native operational assets | 13 | Preserve agent instructions, steering, workflow memory, and GitHub templates |
| Repository entrypoints and policy | 5 | Preserve conventional discovery and policy locations |
| Package documentation | 12 | Preserve shipped usage, compatibility, architecture, examples, and artifact guides |
| Package provenance | 11 | Preserve attribution, upstream pins, and parity/source-accounting documents |
| Release process and navigation | 10 | Preserve review contracts, validation procedure, and release-record entrypoints |
| Historical evidence | 35 | Preserve original reports and their scope; exclude from ordinary durable retrieval |

Skill Markdown is part of an executable workflow package, not a project-knowledge document.
Canonical skill source remains under `powers/pkstack/skills/`; setup-owned copies remain under
`.kiro/skills/`. Vendored notices and references keep their packaging and provenance boundaries.
Steering, `AGENTS.md`, and native specs likewise do not become knowledge projections.

Ordinary retrieval reads only `Wiki/knowledge/`, `Wiki/features/`, and `.kiro/specs/`.
Native specs are read in place without a second authoritative copy. Working notes, instructions,
skills, and historical reports are excluded from that corpus. The retired
`openknowledge-cli-contract` source retains its historical provenance and paired manifest/ledger
archive; the independent Google OKF and OKF skills sources remain active.

Package documentation stays with the code and assets it explains. The
[usage guide](../../../powers/pkstack/docs/usage.md),
[package architecture](../../../powers/pkstack/docs/architecture.md), and
[source provenance](../../../powers/pkstack/docs/provenance.md) remain linked native package
references, outside the ordinary project-knowledge search root. No copied versions are introduced.

Historical evidence means a recorded result for its original candidate, runtime, and test scope.
It does not mean the report is inaccurate, and it does not mean its result still holds. This
classification preserves the historical documents' bytes. The
[release-record entrypoint](../../../reviews/release-status.md) can identify the candidate it
actually evaluates; it does not establish acceptance of this migration. Reusable review prompts
and validation procedures are classified separately from past result reports.

## Existing-project handling

Fresh setup creates the durable and working structure without inventing project knowledge.
Existing-project setup preserves user-owned documents and reports managed-file conflicts through
its normal preview. It does not replay this repository's three-document move on another project.
For an existing project's corpus, inventory and classify its own documents first, review the
selected moves and affected links, then migrate only its current useful knowledge. Local
validation and search reject legacy Markdown that would otherwise be omitted; setup does not
silently relocate it. Keep unrelated edits, original provenance, and historical evidence intact.
