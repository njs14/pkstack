---
type: Runbook
title: Task-driven context depth
description: Bounded escalation from executable feature proof to broader project knowledge.
tags: [pk-stack, runbook, context, retrieval]
---

# Task-driven context depth

## Verify or repair

Start with the exact feature record and its project command. Use **PROVE** plus **DO** only. Do not
run a broad knowledge search unless failure evidence exposes an architecture, decision, concept, or
operations question that the feature record and its explicit links cannot answer.

## Explain or investigate

Read the relevant feature record and follow its explicit related links first. If that bounded packet
is insufficient, issue one targeted `projectctl knowledge search` query with a declared budget. Keep
the returned content-addressed locators and line ranges with the conclusion; do not inject the whole
Wiki.

## Architecture, rationale, or native planning

Retrieve targeted KNOW context early, then reconcile it with the current feature record and its
executable proof. Record the selected depth and the concrete reason for every escalation. Advisory
architecture findings must be applied back to Kiro's native `design.md`; a PK-Stack skill does not
create a second authoritative design package.

See the [composition architecture](../architecture/native-kiro-composition.md), the
[runtime decision](../decisions/native-spec-and-okn.md), and the
[upstream-maintenance feature](../features/pk-stack-upstream-maintenance.md).
