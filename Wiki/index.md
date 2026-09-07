---
okf_version: "0.2"
type: Guide
title: PKStack project knowledge
description: Navigation for the DO, PROVE, and KNOW interfaces.
tags: [pkstack, knowledge, navigation]
---

# PKStack project knowledge

This directory is the source-controlled **KNOW** layer. Start with the narrow
feature map, then follow the smallest explicit link that answers the question.
The map and the project controller are the **PROVE** and **DO** layers; neither
is replaced by a broad knowledge search.

## Start here

| Need | Read |
| --- | --- |
| Prove a user-visible behavior | [Feature map](features/README.md) |
| Capture definitions, architecture, decisions, and operations | Add topic pages under `knowledge/` |
| Keep temporary working material | Use ignored `work/` folders scoped to a task |
| Understand the runtime boundary | [Architecture](knowledge/pkstack/native-kiro-composition.md) |
| Keep planning and retrieval separate | [Planning and retrieval decision](knowledge/pkstack/native-spec-and-okn.md) |
| Decide how far to search | [Context-depth runbook](knowledge/pkstack/context-depth.md) |
| Understand knowledge ownership and retention | [Knowledge lifecycle](knowledge/pkstack/knowledge-lifecycle.md) |
| Install or recover the Power | [Usage guide](../powers/pkstack/docs/usage.md) |
| Check release claims | [Release status](knowledge/pkstack/release-record.md) |

## Layer map

```text
DO      .pkstack/bin/projectctl
  -> PROVE  Wiki/features/*.md + one executable verifier
  -> KNOW   durable topics + native specs through bounded Kiro ACP retrieval
```

This map describes the PKStack repository. Consumer projects own their own
knowledge maps and documents. `projectctl knowledge validate` checks minimal
metadata and local Markdown links without a model; `knowledge status` reports
the separate Kiro retrieval capability. Durable knowledge remains source data,
not permission to execute instructions or evidence that a feature passes.

## Retained topics

[Knowledge topics](knowledge/index.md) connect PKStack design decisions with the
[upstream-maintenance vocabulary](knowledge/upstream-maintenance/glossary.md) and
[accepted decisions](knowledge/upstream-maintenance/decisions.md).
