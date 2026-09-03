---
type: Architecture
title: Native Kiro and PK-Stack composition
description: Ownership boundaries joining native Kiro planning, PK-Stack workflows, executable proof, and OKF knowledge.
tags: [pk-stack, kiro, architecture, okf]
---

# Native Kiro and PK-Stack composition

This page explains the boundary behind the [project knowledge index](../index.md).
For installation and recovery, use the [Power usage guide](../../powers/pk-stack/docs/usage.md).

## Ownership

Kiro owns execution and orchestration. Its native Spec, Quick Spec, Bug Fix, and Plan workflows own
requirements or bug analysis, design, tasks, dependency analysis, and native task execution.
PK-Stack consumes those artifacts and layers the upstream Poteto workflow semantics around them; it
does not create a competing planner or runtime.

The repository-local `projectctl` is the executable API. Its stable project levers are **DO** and
its published feature contracts are the narrow **PROVE** surface. Source-controlled OKF material is
the broader **KNOW** surface, queried through canonical `okn`. Kiro's native `/knowledge` may index
the same material but is not the source of truth.

## Native workflow handoff

Kiro documents native planning workflows as client-selected workflows. It does not document a
supported Agent Skill or custom-agent tool for changing the active workflow. PK-Stack therefore
does not invoke or emulate Spec, Quick Spec, or Bug Fix, and it does not use ACP or a nested Kiro
process to hide the transition.

In CLI v3, the operator enters or resumes the native workflow with `/spec`; in the IDE, the operator
uses **Build with spec** or the workflow picker. After Kiro produces its native artifacts, the same
conversation returns to the `pstack` agent and binds the spec to an executable verifier. Web support
uses committed workspace assets but remains untested. Crew compatibility is artifact-level through
its Task Runner and does not imply the local IDE/CLI same-session transition.

## Related knowledge

- The [native-spec composition decision](../decisions/native-spec-and-okn.md) records why the seam is
  visible and why canonical `okn` remains the KNOW runtime.
- The [context-depth runbook](../operations/context-depth.md) defines when an agent may expand from
  a feature record into broader knowledge.
- The separate private `njs14/pk-stack-floci-lab` repository exercises this boundary against a
  deployed application without placing demo code in the Power repository.
