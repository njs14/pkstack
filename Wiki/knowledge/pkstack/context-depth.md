---
type: Runbook
title: Task-driven context depth
description: Bounded escalation from executable feature proof to broader project knowledge.
tags: [pkstack, runbook, context, retrieval]
---

# Task-driven context depth

## Verify or repair

Start with the exact feature record and its project command. Use **PROVE** plus **DO** only. Do not
run a broad knowledge search unless failure evidence exposes an architecture, decision, concept, or
operations question that the feature record and its explicit links cannot answer.

## Explain or investigate

Read the relevant feature record and follow its explicit related links first. If that bounded packet
is insufficient, issue one targeted query:

```sh
.pkstack/bin/projectctl knowledge search "<specific question>" --budget 1200 --model auto --output json
```

Keep the returned source paths, exact quotes, SHA-256 values, line ranges, and uncertainties with
the conclusion; do not inject the whole Wiki. The isolated read-only Kiro ACP worker searches
`Wiki/knowledge/`, `Wiki/features/`, and `.kiro/specs/`. Native specs remain authoritative in place;
`Wiki/work/`, skills, and instructions are excluded. Open working material only for the identified
task.

The budget bounds returned UTF-8 JSON bytes divided by four, not internal model token use.
`--model` is optional and defaults to `auto`; its resolved model is unknown. Check
`knowledge status` for retrieval availability. Unsupported runtimes and model selections fail
explicitly; local metadata/link validation still works. Preserve incomplete or invalid retrieval
as a failure instead of silently changing the backend or model.

## Architecture, rationale, or native planning

Retrieve targeted KNOW context early, then reconcile it with the current feature record and its
executable proof. Record the selected depth and the concrete reason for every escalation. Advisory
architecture findings must be applied back to Kiro's native `design.md`; a PKStack skill does not
create a second authoritative design package.

## Capture and reuse

Before substantial investigation or planning, read the relevant topic's established definitions,
decisions, and open questions. Resolve consequential ambiguity before expanding the document set;
`grill-with-docs` supports this interview and domain-modeling workflow.

At a planning handoff or task completion, update changed definitions and decisions in the relevant
topic under `Wiki/knowledge/`. Link evidence and native planning artifacts, preserve unresolved
questions, and mark earlier guidance as superseded when it changed. Keep temporary notes in
`Wiki/work/`; a passing task does not make every note worth retaining. A fresh session should be
able to reuse settled understanding without repeating the interview. Follow the
[knowledge lifecycle](knowledge-lifecycle.md) when distinguishing decisions from verified behavior.

See the [composition architecture](native-kiro-composition.md), the
[runtime decision](native-spec-and-okn.md), and the
[upstream-maintenance feature](../../features/pkstack-upstream-maintenance.md).
