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

### Project advice is separate from execution

The September 10 conversational plan, explicitly approved for implementation, adds
`pkstack-guide` as a project-aware advisor across new and existing projects. A separate
entry point makes advice discoverable without changing the primary router into another planner or
expanding setup into automatic onboarding. The guide recommends a next action, explains
the evidence and expected proof, and prepares a prompt for the owning workflow. Advice
alone does not authorize execution or knowledge writes. A subsequent execution request
uses the existing owner and native handoff, carrying settled context forward.

Verification readiness is relative to the real user or caller surface: an empty repository
needs a small runnable slice with a feedback loop, while an existing project may need no
new harness. The maintainer's pstack guides inform the method, not a requirement for Cursor
cloud agents, a daily schedule, or every workflow on every task. This records an accepted
design; structural and native behavioral checks must establish its implementation separately.
The [guide entry point](../../../powers/pkstack/skills/pkstack-guide/SKILL.md) owns advice;
its [lifecycle reference](../../../powers/pkstack/skills/pkstack-guide/references/project-lifecycle.md)
records the decision criteria and source adaptations. Execution remains in the
[primary router](../../../powers/pkstack/skills/poteto-kiro-mode/SKILL.md), and
[setup](../../../powers/pkstack/skills/pkstack-setup/SKILL.md) only offers orientation when useful.
The [guide installation contract](../../features/pkstack-guide.md) checks registration,
resource installation, conflict preservation, and declared routes; it is not native behavior proof.

Release 0.7.0 reconciles the guide with the already merged `poteto-kiro-mode` router
and Wayfinder catalog. The guide's links and ready-to-send prototype route now use
the renamed owner, while the workspace agent remains `pkstack`. The observations
below stay bound to their recorded guide bytes; they are not a fresh acceptance
campaign for the reconciled guide. The primary compatibility profile is unchanged.

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

## September 10 guide observations and limits

Native CLI v3 testing used Kiro CLI 2.21.2, embedded KAS 0.58.7, and the session's `auto`
model selection. These are diagnostic observations, not an unmodified-profile acceptance pass.
The pre-repair primary profile was rejected at chat startup as needing a legacy-agent upgrade,
despite structural validation and listing. A disposable fixture adding only
`"permissions": {"rules": []}` selected `pkstack` in the runtime event stream. No canonical
agent, global configuration, or permission grant was changed for this guide implementation.
The subsequent explicitly approved compatibility repair is recorded under
[permission ownership](runtime-and-verification.md#permission-ownership-and-evidence).
That repair does not turn these earlier diagnostic runs into unmodified-profile evidence;
an agent-list result alone cannot establish selected-agent behavior.

The fixture copied reviewed skills, steering, and consumer profiles, but omitted setup, hooks,
and the project controller. Temporary native policy allowed file reads and skill disclosure;
it denied shell, writes, subagents, Powers, MCP, and web calls. This isolates advisory behavior;
it does not prove obedience with unrestricted tools or installed-project integration.
Kiro still used its native authentication. No IDE, Crew, Web, live app, or hosted-CI result follows.

A ten-case revision covered no repository, an empty library, unfamiliar code, unit tests without
surface proof, a stale verifier, a healthy harness, an approved Spec, interaction uncertainty,
an explicit `/how` request, and unavailable Slack context. All ten exited normally with unchanged
fixture files and no model-requested execution tools. Advice was mixed: the stale verifier was
read and routed to maintenance, the explicit explanation was not intercepted, and missing Slack
context was not fabricated. Other answers skipped required references, treated an unverified
inference as rationale, proposed malformed Spec handoffs, or replaced requested interaction
proof with a prose plan. No aggregate behavioral pass is claimed.

That campaign tested entry SHA-256
`2356b2a5a2b2fa630e998f7131fb13b7e6b0c9054554e60fa5153630e3b856a7`.
After the observed corrections, three fresh runs tested entry
`4d3a10c2584f180f6bb50053312ef003471a1b40f9cacaffa9b6577317ed072d`.
Both used lifecycle-reference SHA-256
`36ee0b724743bb7f509a9e90bb35fbd7fd2fac30cb550cb2edd49ef298aa69e9`.

| Final targeted scenario | Observation and remaining limit |
| --- | --- |
| Empty Python library | Preserved uv/pytest, proposed a small public-API slice and a valid Plan prompt; still proposed a return to PKStack after conversational Plan, contrary to its native handoff ownership. |
| Approved queue Spec | Read requirements, design, tasks, and the router; emitted `/spec queue` and carried retry-once/same-job-ID proof into pre-implementation verifier binding. Did not inspect controller or runner availability. |
| Interaction uncertainty | Recommended `/pkstack prototype` with both interactions and an observation that settles the choice. Still skipped the lifecycle and destination reference reads. |

The three reruns also left fixture files unchanged. They supersede the specific malformed-resume
and prose-instead-of-prototype observations, not every earlier case or remaining grounding gap.
The useful distinction is advice scope versus recommended-work scope: a read-only recommendation
may point to an executable experiment without conducting it. Structural installation proof stays
in the [guide feature contract](../../features/pkstack-guide.md); native acceptance remains limited.

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

## Carry constraints through the handoff without turning recommendations into decisions

The [v4 planning review](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/planning-043-v4/README.md) separates two improvements:
the router stopped re-asking settled constraints, and the plan placed knowledge capture before
implementation. Neither repaired the model's reasoning about a derived transformation. The
settled ASCII-only input rule still produced the proposed sequence strip → uppercase → validate;
`ab12ß` becomes `AB12SS`, so validating afterward loses the evidence that the original input was
forbidden. Ordinary plan review supplied the counterexample and moved validation before case
conversion. Keep tests for the input contract, rather than only examples of the desired output.

A handoff should carry three distinct things: settled requirements, mechanics justified by those
requirements, and genuinely open choices. Check derived mechanics against counterexamples before
labeling them settled. Ask for a choice when one is needed; the earlier Quick Spec run's preferred
answer was not an accepted decision merely because the model recommended it. The
[v1–v3 record](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/planning-043/README.md) remains evidence of those failures.

Place capture and its validation in the approved plan's ordered steps, then inspect their order
relative to the first product edit. A later Wiki file does not prove capture happened first. For
a no-write request, inspect the post-approval delta and acknowledge pending knowledge rather than
manufacture a capture result. Repeated approval should reuse existing accepted knowledge without
duplicate records. v4's file events and no-write receipts support these bounded observations;
its operator-assisted Plan entry remains distinct from v5's autonomous command emission.

The [CLI](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/friends-cli-validation.md) and
[IDE](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/friends-ide-validation.md) Spec campaigns demonstrate another boundary:
same-conversation planning, immutable tests, genuine failure, implementation-only repair, and
stored pass can all work while the prose contract exceeds what four tests establish. IDE Standard's
ASCII edge case was outside that predicate. Keep native artifacts and test identities unchanged,
but inspect whether their acceptance meaning covers the requirement; a green predicate cannot
retroactively resolve a mismatch in the approved prose.

## September 7 bounded native verification

The [verification evidence](evidence/2026-09-07/verification.json) records new normal Kiro CLI
v3 demonstrations using CLI 2.21.1, the generated `pkstack` agent, and selected
`claude-opus-5` / high. The Power tree `b6ade2ad26bb1b204c745db9d6cda1eab0978bb2` is
the original unchanged trusted-main `3a370aa` source for those observations. The later 0.5.3
correction changes PR-supervision guidance and version metadata. Stored-verifier, Impeccable
and controller-implementation evidence carries forward only through explicit per-file source
equivalence; corrected PR-supervision guidance has its own new native proof. The final PR binds the containing tree.

For stored verification, the operator predeclared a string-normalization contract and tests,
installed the reviewed Power, and retained a genuine failing `node acceptance.mjs` result.
Kiro read the shipped method and contract, displayed the stored predicate, edited only the
implementation, and ran the same stored verifier to `passed` at attempt 2 of 4. Contract,
acceptance-test bytes and stored command were unchanged. Tests include type errors, length
boundaries, invalid ASCII punctuation and Unicode expansion before casing. This is bounded
command-bound repair evidence; no new native Spec, Quick Spec or IDE result is claimed.

For Impeccable, Kiro read the shipped guidance and refined only the stylesheet of an existing
cream/forest, serif reading-list fixture. It captured and viewed narrow/wide rendered evidence
before and after, exercised toggle/progress behavior and keyboard focus, and stopped after one
confirmation pass. A separate operator browser check confirmed exact content, reversible toggles,
Tab/Enter/Space operation, pressed state, polite progress, visible focus, 44px targets and no
overflow at 390 and 1280 pixels. The fixture sources and screenshot hashes are in the evidence.
This establishes Chromium behavior only, without a screen-reader, full WCAG or real-device claim;
no absent upstream runtime, hooks or live variants were installed.

PR supervision uses the real scoped PR in `check` mode, with the independent-review hold and
zero retries carried in session context. Its snapshot and any correction are retained separately
from an acceptance verdict. The initial check miscounted 12 jobs as 13 and corrected that
through fresh structured reads. A later continuation ran `git fetch --no-write-fetch-head`:
no worktree changes were observed, but it was not a strictly read-only operation. The 0.5.3
guidance addresses that metadata boundary explicitly and retains the failure as regression
context. A fresh 0.5.3 consumer then completed a check and a same-session continuation
using forge reads and local Git commands with optional locks disabled. The operator compared
all 325 Git metadata file hashes and path sets after each snapshot: no changes. Both snapshots
retained zero retries and the independent-review hold. The remote PR was the earlier checkpoint;
the loaded guidance was the repaired candidate. A successful read-only check does not prove failure repair, flaky
retry handling, substantive reviewer-response work or merge-ready status.

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
| [reviews/cli-native-command-audit/README.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/cli-native-command-audit/README.md) | The CLI audit separates conversational Plan from Spec task files and command recognition from execution, motivating explicit native workflow handoffs. |
| [reviews/planning-043/README.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/planning-043/README.md) | The initial 0.4.3 campaign retains failed handoffs, premature implementation/capture ordering, unanswered approval checks and Unicode constraint violations. |
| [reviews/planning-043-v4/README.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/planning-043-v4/README.md) | v4 improved settled-answer reuse and capture ordering and recovered no-write evidence, but two exact-command handoffs still failed and v3 Unicode failures were not erased. |
| [reviews/planning-043-v5/README.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/planning-043-v5/README.md) | v5 produced one exact Plan command and stopped, but still proposed incorrect uppercase-before-ASCII validation; no Plan or implementation ran in that router-only check. |
| [reviews/friends-cli-validation.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/friends-cli-validation.md) | Historical native Standard/Quick fixture campaigns distinguish skill loading, same-conversation execution and exact verifier preservation; shared account deltas are not per-campaign costs. |
| [reviews/friends-ide-validation.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/friends-ide-validation.md) | IDE Standard/Quick fixtures record agent-panel/model/approval context separately from CLI; Autopilot off did not imply a prompt for every command. |
| [reviews/release-030-cli.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-030-cli.md) | Quick Spec followed by same-conversation agent swap and immutable verifier failure/repair/pass proves the bounded fixture, not every native route or release-wide correctness. |
| [reviews/release-030-composition.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-030-composition.md) | A native generated-loop task composed the builder method with a stored verified goal, preserving fixed tests and passing at 2 of 4 within its explicit fixture scope. |
