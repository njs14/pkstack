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

## Retained planning observations

The September 6 CLI audit distinguishes native conversational Plan from Spec task files and
command recognition from executed workflows. For an inactive, user-requested Plan, current
routing guidance returns a runnable `/plan Read .kiro/skills/grilling/SKILL.md; ...` handoff and
stops. It does not claim to select the mode itself. Native Specs keep their own artifact and
approval flow; conversational Plan does not acquire a `tasks.md` requirement.

The 0.4.3 evidence is a sequence, not one universal pass:

- The original v1-v3 campaign recorded missing handoffs, repeated settled questions, premature
  implementation before knowledge capture, and Unicode reasoning errors. IDE Quick Spec initially
  lacked the final no-write acknowledgement. These failures remain preserved.
- The v4 candidate `88bbe15b3858b6347f35dd975a6ecd35ffcadd93` recorded improved settled-answer
  reuse, capture before implementation, and recovered/observed no-write acknowledgements. Two
  CLI runs still failed to emit the exact runnable Plan line. Operator-assisted results remain
  distinguished from autonomous behavior.
- The v5 source `e4941073adf89a130e8ee268fb122c113cf8a409` corrected routing guidance and recorded
  one fresh successful command emission and stop. Its router still proposed uppercasing before
  rejecting non-ASCII input: `ab12ß` can become `AB12SS`. No implementation ran in that scenario.
  This result supersedes the command-emission gap only, not the earlier Unicode failures or a
  general autonomous reasoning limit. The v4 plan review corrected that ordering before execution.

The practical lesson is to carry settled constraints through handoffs, preserve unanswered choices
as questions, and verify transformations against counterexamples before treating them as derived
mechanics. A recommendation is not an accepted user decision. An approved plan is not proof of
implementation, and capture denial or failed validation remains an incomplete checkpoint.

Earlier 0.3 native Standard/Quick and builder-composition campaigns retain useful bounded
fail-repair-pass examples. Their preserved tests, source hashes and selected native conversations
show the specific handoff/verification scenarios; they do not erase later failures or certify all
client surfaces. The corresponding sources are listed below.

## Related knowledge

- The [native-spec composition decision](native-spec-and-okn.md) records why the seam is
  visible and why bounded Kiro retrieval supersedes the original `okn` runtime choice.
- The [context-depth runbook](context-depth.md) defines when an agent may expand from
  a feature record into broader knowledge.
- The [corpus inventory](corpus-migration.md) records the selective documentation migration and
  the native, packaged, and historical materials retained in their existing locations.
- The separate private `njs14/pk-stack-floci-lab` repository exercises this boundary against a
  deployed application without placing demo code in the Power repository.

## Source-specific retained knowledge

These summaries describe what is retained from each source. Historical observations keep their
original candidate and scope; they are not fresh verification of this checkout.

| Source | Retained guidance or bounded observation |
| --- | --- |
| [reviews/cli-native-command-audit/README.md](../../../reviews/cli-native-command-audit/README.md) | The CLI audit separates conversational Plan from Spec task files and command recognition from execution, motivating explicit native workflow handoffs. |
| [reviews/planning-043/README.md](../../../reviews/planning-043/README.md) | The initial 0.4.3 campaign retains failed handoffs, premature implementation/capture ordering, unanswered approval checks and Unicode constraint violations. |
| [reviews/planning-043-v4/README.md](../../../reviews/planning-043-v4/README.md) | v4 improved settled-answer reuse and capture ordering and recovered no-write evidence, but two exact-command handoffs still failed and v3 Unicode failures were not erased. |
| [reviews/planning-043-v5/README.md](../../../reviews/planning-043-v5/README.md) | v5 produced one exact Plan command and stopped, but still proposed incorrect uppercase-before-ASCII validation; no Plan or implementation ran in that router-only check. |
| [reviews/friends-cli-validation.md](../../../reviews/friends-cli-validation.md) | Historical native Standard/Quick fixture campaigns distinguish skill loading, same-conversation execution and exact verifier preservation; shared account deltas are not per-campaign costs. |
| [reviews/friends-ide-validation.md](../../../reviews/friends-ide-validation.md) | IDE Standard/Quick fixtures record agent-panel/model/approval context separately from CLI; Autopilot off did not imply a prompt for every command. |
| [reviews/release-030-cli.md](../../../reviews/release-030-cli.md) | Quick Spec followed by same-conversation agent swap and immutable verifier failure/repair/pass proves the bounded fixture, not every native route or release-wide correctness. |
| [reviews/release-030-composition.md](../../../reviews/release-030-composition.md) | A native generated-loop task composed the builder method with a stored verified goal, preserving fixed tests and passing at 2 of 4 within its explicit fixture scope. |
