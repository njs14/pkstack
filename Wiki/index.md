---
okf_version: "0.2"
type: Guide
title: PK-Stack project knowledge
description: Navigation for the DO, PROVE, and KNOW interfaces.
tags: [pk-stack, knowledge, navigation]
---

# PK-Stack project knowledge

This directory is the source-controlled **KNOW** layer. Start with the narrow
feature map, then follow the smallest explicit link that answers the question.
The map and the project controller are the **PROVE** and **DO** layers; neither
is replaced by a broad knowledge search.

## Start here

| Need | Read |
| --- | --- |
| Prove a user-visible behavior | [Feature map](features/README.md) |
| Capture architecture | Add project-owned pages under `architecture/` |
| Record decisions | Add project-owned pages under `decisions/` |
| Document operations | Add project-owned pages under `operations/` |
| Understand the runtime boundary | [Architecture](architecture/native-kiro-composition.md) |
| Keep planning and retrieval separate | [Planning decision](decisions/native-spec-and-okn.md) |
| Decide how far to search | [Context-depth runbook](operations/context-depth.md) |
| Install or recover the Power | [Usage guide](../powers/pk-stack/docs/usage.md) |
| Check release claims | [Release status](../reviews/release-status.md) |

## Layer map

```text
DO      .pstack/bin/projectctl
  -> PROVE  Wiki/features/*.md + one executable verifier
  -> KNOW   this Wiki + optional canonical `okn`
```

This scaffold is consumer-neutral: it does not link back into the PK-Stack
source repository or invent project knowledge. Add only pages owned by this
project, and keep their links relative to this Wiki.
