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
`Wiki/knowledge/` is the broader **KNOW** surface. Bounded `projectctl knowledge search` uses an
isolated read-only Kiro ACP worker over durable topics, `Wiki/features/`, and `.kiro/specs/`.
Working material lives separately in `Wiki/work/` and is excluded from search. Kiro's native
`/knowledge` may index the same files; source-controlled documents remain authoritative.

Skills and their bundled resources remain native packages. Agent instructions and steering remain
native operational assets. Native specs stay authoritative in `.kiro/specs/`; Wiki documents link
to them rather than maintain synchronized copies. The [knowledge lifecycle decision](knowledge-lifecycle.md)
defines how workflows retrieve and improve the project understanding around those artifacts.

`knowledge validate` composes feature checks with minimal metadata and local Markdown links
without invoking Kiro, a model, or `okn`. It does not establish full OKF conformance or the truth
of a document. `knowledge status` reports layout and retrieval availability separately. The
current retrieval adapter supports POSIX with Kiro CLI 2.21.1 and embedded KAS 0.58.7, using
native CLI authentication and the official Python ACP client pinned to 0.12.1. Unsupported
runtime or model selections fail explicitly. The [usage guide](../../../powers/pkstack/docs/usage.md#use-project-knowledge)
records the response contract and budget limits.

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
  visible and why bounded Kiro retrieval supersedes the original `okn` runtime choice.
- The [context-depth runbook](context-depth.md) defines when an agent may expand from
  a feature record into broader knowledge.
- The [corpus inventory](corpus-migration.md) records the selective documentation migration and
  the native, packaged, and historical materials retained in their existing locations.
- The separate private `njs14/pk-stack-floci-lab` repository exercises this boundary against a
  deployed application without placing demo code in the Power repository.
