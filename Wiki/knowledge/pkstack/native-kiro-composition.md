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
requirements or bug analysis, design, tasks, dependency analysis, and native task execution
when using Specs. Plan owns a conversational plan and has no Spec task-file requirement.
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

In CLI v3, the operator enters or resumes Specs with `/spec`, or conversational Plan with
`/plan <request>`; in the IDE, the operator
uses **Build with spec** or the workflow picker. After Kiro produces its native artifacts, the same
conversation returns to the `pkstack` agent and binds the spec to an executable verifier. Web support
uses committed workspace assets but remains untested. Crew compatibility is artifact-level through
its Task Runner and does not imply the local IDE/CLI same-session transition.

## Shared planning interview decision

The approved 0.4.3 design makes `grilling` the shared interview method for planning entered
through PKStack. It supplies fact-first questions, dependent decision ordering, recommendations,
and settled-answer reuse. Kiro supplies the native workflow, permissions, approval, and execution.
`grill-me` starts a focused interview; `grill-with-docs` additionally requests capture while
interviewing when writes are permitted. `interrogate` remains a separate proposal review.

The handoff explicitly asks native Plan or Specs to read the shared method and carries forward
settled answers and open questions. This avoids assuming that built-in workflows inherit every
custom-agent resource. Native Plan uses permitted reading and search, with no shell, MCP,
prototype execution, or knowledge writes. It keeps pending knowledge in the conversation.
After explicit implementation-plan approval, the first permitted execution step captures reusable
definitions and decisions through the existing knowledge lifecycle. Explicit no-write scope wins;
repeated approval updates existing knowledge instead of creating copies. Denied writes or failed
validation remain incomplete. Approval is a design decision, not implementation proof.

This replaces separate mandatory planning interviews and opt-in-only post-plan knowledge capture.
A standalone decision conversation does not automatically authorize file updates. The accepted
plan is the source of this decision; native acceptance must separately establish candidate behavior.

## Related knowledge

- The [native-spec composition decision](native-spec-and-okn.md) records why the seam is
  visible and why bounded Kiro retrieval supersedes the original `okn` runtime choice.
- The [context-depth runbook](context-depth.md) defines when an agent may expand from
  a feature record into broader knowledge.
- The [corpus inventory](corpus-migration.md) records the selective documentation migration and
  the native, packaged, and historical materials retained in their existing locations.
- The separate private `njs14/pk-stack-floci-lab` repository exercises this boundary against a
  deployed application without placing demo code in the Power repository.
