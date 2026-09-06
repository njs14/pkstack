---
type: Architecture
title: Native Kiro and PKStack composition
description: Ownership boundaries joining native Kiro planning, PKStack workflows, executable proof, and OKF knowledge.
tags: [pkstack, kiro, architecture, okf]
---

# Native Kiro and PKStack composition

This page explains the boundary behind the [project knowledge index](../../index.md).
For installation and recovery, use the [Power usage guide](../../../powers/pkstack/docs/usage.md).

## Ownership

Kiro owns execution and orchestration. Its native Spec, Quick Spec, Bug Fix, and Plan workflows own
requirements or bug analysis, design, tasks, dependency analysis, and native task execution.
PKStack consumes those artifacts and layers the upstream Poteto workflow semantics around them; it
does not create a competing planner or runtime.

The repository-local `projectctl` is the executable API. Its stable project levers are **DO** and
its published feature contracts are the narrow **PROVE** surface. Source-controlled OKF material in
`Wiki/knowledge/` is the broader **KNOW** surface, queried through canonical `okn`. Working material
lives separately in `Wiki/work/`. Kiro's native `/knowledge` may index the durable material but is
not the source of truth.

Skills and their bundled resources remain native packages. Agent instructions and steering remain
native operational assets. Native specs stay authoritative in `.kiro/specs/`; Wiki documents link
to them rather than maintain synchronized copies. The [knowledge lifecycle decision](knowledge-lifecycle.md)
defines how workflows retrieve and improve the project understanding around those artifacts.

## Native workflow handoff

Kiro documents native planning workflows as client-selected workflows. It does not document a
supported Agent Skill or custom-agent tool for changing the active workflow. PKStack therefore
does not invoke or emulate Spec, Quick Spec, or Bug Fix, and it does not use ACP or a nested Kiro
process to hide the transition.

In CLI v3, the operator enters or resumes the native workflow with `/spec`; in the IDE, the operator
uses **Build with spec** or the workflow picker. After Kiro produces its native artifacts, the same
conversation returns to the `pkstack` agent and binds the spec to an executable verifier. Web support
uses committed workspace assets but remains untested. Crew compatibility is artifact-level through
its Task Runner and does not imply the local IDE/CLI same-session transition.

## Related knowledge

- The [native-spec composition decision](native-spec-and-okn.md) records why the seam is
  visible and why canonical `okn` remains the KNOW runtime.
- The [context-depth runbook](context-depth.md) defines when an agent may expand from
  a feature record into broader knowledge.
- The [corpus inventory](corpus-migration.md) records the selective documentation migration and
  the native, packaged, and historical materials retained in their existing locations.
- The separate private `njs14/pk-stack-floci-lab` repository exercises this boundary against a
  deployed application without placing demo code in the Power repository.
