---
type: Index
okf_version: "0.2"
title: Retained project knowledge
description: Topic navigation for PKStack installation, design, verification, maintenance, and release evidence.
tags: [pkstack, knowledge, navigation]
---

# Retained project knowledge

Start with the relevant [feature contract](../features/README.md), then follow its related sources.
These topic documents explain decisions and observations; executable checks remain the proof.
This is PKStack's own repository documentation layer, separate from the installable Power and
from the knowledge each consumer project authors for itself.

- PKStack: [native composition](pkstack/native-kiro-composition.md),
  [runtime decision](pkstack/native-spec-and-okn.md),
  [document lifecycle](pkstack/knowledge-lifecycle.md),
  [context depth](pkstack/context-depth.md), and [corpus migration](pkstack/corpus-migration.md).
- Practical guides: [installation and upgrades](pkstack/installation-and-upgrades.md),
  [runtime and verification](pkstack/runtime-and-verification.md),
  [skill composition and provenance](pkstack/skill-composition-and-provenance.md),
  [visual artifacts](pkstack/visual-artifacts.md),
  [local checks and CI](pkstack/quality-and-ci.md), and
  [release and review evidence](pkstack/release-and-review.md), with the
  [maintained release record](pkstack/release-record.md).
- Upstream maintenance: [vocabulary](upstream-maintenance/glossary.md),
  [accepted decisions](upstream-maintenance/decisions.md), and
  [historical prototype observation](upstream-maintenance/observations.md), plus
  [operation and recovery](upstream-maintenance/operations.md).

## Lessons synthesized from reviews

Original review reports are retained in Git history. Their reusable conclusions live in these topics,
including failure mechanisms, counterexamples, remediation, and limits:

| Question | Retained explanation |
| --- | --- |
| Why can a loop pass once but exceed its budget after restart? | [Durable reservations, baseline proof, and independent process tests](pkstack/skill-composition-and-provenance.md#reusable-loops-need-a-durable-transition-contract) |
| How can native planning pass its tests but violate a settled requirement? | [Derived mechanics, counterexamples, and capture ordering](pkstack/native-kiro-composition.md#carry-constraints-through-the-handoff-without-turning-recommendations-into-decisions) |
| Why are schema validation and a listed agent insufficient permission evidence? | [Discovery, selection, action, and ordinary controls](pkstack/runtime-and-verification.md#schema-discovery-selection-and-action-are-separate-gates) |
| What does a green updater run actually mean? | [Rejection handling, complete review context, and candidate identity](upstream-maintenance/operations.md#diagnose-a-completed-workflow-by-its-actual-terminal-outcome) |
| What can still be wrong when every citation verifies? | [Source attribution versus inference, freshness, and transport limits](pkstack/knowledge-lifecycle.md#what-the-foundations-retrieval-tests-actually-established) |
| How should a regression repair preserve the original acceptance question? | [Deterministic failure reproduction and environment isolation](pkstack/quality-and-ci.md#preserve-the-failure-then-test-the-mechanism), [unchanged visual inputs](pkstack/visual-artifacts.md#keep-input-facts-fixed-while-repairing-presentation) |

Temporary drafts belong under ignored `Wiki/work/` and are excluded from ordinary retrieval.
