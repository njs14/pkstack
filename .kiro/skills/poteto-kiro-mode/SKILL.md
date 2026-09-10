---
name: poteto-kiro-mode
description: Route broad Poteto workflow requests into PKStack's Kiro-native skills, project interfaces, and current-session verification loop.
---

# Use Poteto Kiro mode

Treat the request text that activated this skill as the outcome to route through PKStack.

For advice about where to start, verification readiness, or which workflow to use next, read
[`pkstack-guide`](../pkstack-guide/SKILL.md) before entering execution checkpoints or a planning
interview. Return its contextual recommendation without starting the recommended work. Direct
execution requests, explicit leaf-skill invocations, and requests for native planning retain
their existing routes below. A later authorization of the recommendation proceeds through its
owner with the settled context; do not route that execution back to the advisor.

This is PKStack's entry point for the broader Poteto workflow. Keep execution in the
current Kiro agent session. First classify the request against
[`references/workflows.md`](references/workflows.md), read the matching section, and preserve its
ordered checkpoints. If a checkpoint truly does not apply, keep it visible as
`<checkpoint> skipped: <specific reason>` instead of silently collapsing the workflow.

## Use Kiro's native planning spine

Selecting the requested native planning mode is the user's action; `poteto-kiro-mode` cannot enter it for
them. Kiro's own approval and execution handoffs still move between its modes and agents on their
own terms. When the user asks for native Plan and it is not already active, `poteto-kiro-mode` packages the
handoff and stops for that selection. Gather the requested outcome, settled choices, rationale,
and evidence links by reading only, and list every remaining open choice as a question for native
Plan to ask. In CLI that conversational-Plan handoff is itself one runnable line the user can send
unchanged, beginning `/plan Read .kiro/skills/grilling/SKILL.md;` and continuing with that context;
do not paraphrase it into a request to switch modes, and do not leave the user to compose the
prompt. In the IDE, use native Plan selection with the same instruction and context. A requested
Spec, Quick Spec, or Bug Fix keeps its own `/spec` route below. Carry derived mechanics as
derived choices naming the requirement each satisfies, not as constraints the sources fix. Do not
conduct the planning interview under `poteto-kiro-mode`, and do not offer to answer those questions here
instead. This explicit mode request overrides the trivial-change skip below; standalone decision
interviews remain exempt.

For all planning entered through PKStack, read and apply [`grilling`](../grilling/SKILL.md)
as the shared interview method. Inspect available facts and reuse settled answers and rationale.
The mode that runs the plan runs the interview: native Plan or the matching Spec once selected,
or `poteto-kiro-mode` itself for the trivial-change route and standalone interviews. Planning helpers
consume that context rather than starting another mandatory interview. Kiro still owns modes,
phase approvals, and execution.

Before reproducing planning inside a PKStack skill, select Kiro's native workflow:

- use a standard **Spec** for an unfamiliar, cross-boundary, high-risk, or requirements-sensitive
  feature;
- use **Quick Spec** for a bounded, well-understood feature whose requirements and design do not
  need phase-by-phase approval;
- use **Bug Fix** for a reproducible defect; and
- use native **Plan** for a plan-only request.

An obvious one- or two-file change may remain in the default `poteto-kiro-mode` flow, but state the concrete
reason that a native planning artifact would add no useful decision or review boundary. Resume an
existing `.kiro/specs/<name>/` package instead of starting a competing plan.

Kiro does not document a supported Agent Skill or custom-agent tool for changing the active
workflow. PKStack therefore does not invoke or emulate Spec, Quick Spec, or Bug Fix, and does not
use ACP or a nested Kiro process to hide the boundary. Make it visible as one same-conversation
handoff only when the appropriate mode is not already active. Carry the requested outcome,
settled choices, rationale, evidence links, and open questions forward, and explicitly direct the
native workflow to read `.kiro/skills/grilling/SKILL.md`. Do not assume built-in agents inherit
this profile's loaded skills. Do not change built-in agents or global configuration to force it.
In CLI v3, use `/plan <request>` for a conversational plan, or `/spec new <name>` and choose
Feature, Quick Spec, or Bug, or `/spec <name>` to resume. If that opens the document viewer,
choose its **Continue** action (`C` in the audited CLI 2.21.2) to resume the Spec agent before
sending the carried context. Viewing or continuing a conversation is not task approval.
For Spec-backed execution, return with
`/agent swap pkstack` after native approval and when execution is permitted. Conversational Plan
keeps Kiro's own approval-to-execution handoff, so do not direct a return to `pkstack` after Plan
approval. In the IDE, use **Build with spec** or the Spec, Quick Spec, or Bug
Fix workflow in the agent picker, then reselect `pkstack` in the same conversation. Web uses its
native Spec picker and built-in primary agent; it does not claim the CLI slash command or a
selectable project primary agent. Crew may consume committed spec artifacts through its Task
Runner, but PKStack does not claim Crew can switch to Kiro's built-in Spec agent.

For complex or unclear Spec requirements, optionally use `/spec analyze_requirements <name>`
once `requirements.md` exists, then reuse its findings. A Bug Fix containing only `bugfix.md`
does not meet that prerequisite. Inspect native documents with `/spec view <name> requirements`,
`/spec view <name> design`, or `/spec view <name> tasks`; viewing is not approval or verifier binding.

Native Plan is conversational and read-only during analysis. Use available reading and search,
keep the plan and pending knowledge in the conversation, and defer shell commands, MCP, file
writes, prototypes, and validation. Do not require `tasks.md` or create one for Plan.
Native Specs own `requirements.md` or `bugfix.md`, `design.md`, `tasks.md`, task dependency analysis,
and native parallel task execution. Once an implementation plan is approved and execution is
permitted, perform the shared approved-plan knowledge capture checkpoint, then wrap the plan with the relevant
upstream-derived workflow skills, a narrow feature contract, deeper OKF context when needed, and a
current-session `/pkstack-verified-goal`. It never creates a second task graph or marks a Kiro task checkbox
as executable proof.

Then select the narrowest shipped skill. An explicit invocation selects that skill; it does not
broaden the user's authority. Read the selected leaf before acting, and compose helpers only for
distinct parts of the outcome. Pass existing evidence forward instead of repeating investigations.

For an explicitly requested `/wayfinder` map, read [Wayfinder](../wayfinder/SKILL.md).
It resolves uncertainty across sessions with GitHub Cloud or local Markdown decision
tickets, curates reusable understanding into OKF, then hands the cleared direction
to native planning. It does not replace a Spec's task graph.

- architecture or alternatives: `architect` or `arena`
- investigation, explanation, or teaching: `blast-radius`, `how`, `why`, `figure-it-out`, or
  `teach`
- repeatable practice and context: `automate-me`, `recall`, or approval-gated `reflect`
- durable project knowledge: `okf`
- decision-focused interviews: [`grill-me`](../grill-me/SKILL.md), using the
  [`grilling`](../grilling/SKILL.md) method; interviews that capture project knowledge:
  [`grill-with-docs`](../grill-with-docs/SKILL.md); sharpening domain terminology:
  [`domain-modeling`](../domain-modeling/SKILL.md)
- verification design and upkeep: `create-verification-skill` or `maintain-verification-skill`
- implementation discipline: `tdd`, `typescript-best-practices`, `technical-writing`, `unslop`, or
  a named `principle-*` skill
- plain restatement or evidence trail: `bro` or `show-me-your-work`
- bounded parallel work or independent challenge: `swarm`, `interrogate`, or `pkstack-model-council`
- completion: `pkstack-verified-goal` with `.pkstack/bin/projectctl`

Use the curated skills where their output fits the task:

- visual explanation: [`show-me`](../show-me/SKILL.md); polished interactive diagrams:
  [`archify`](../archify/SKILL.md)
- agent instructions: [`writing-for-agents`](../writing-for-agents/SKILL.md)
- primary-source research and reports: [`research`](../research/SKILL.md)
- bug or performance diagnosis: [`diagnosing-bugs`](../diagnosing-bugs/SKILL.md)
- refactoring surveys: [`improve-codebase-architecture`](../improve-codebase-architecture/SKILL.md),
  then `architect` for the selected interface design
- pause and resume documents: [`handoff`](../handoff/SKILL.md)
- in-progress Git conflicts: [`resolving-merge-conflicts`](../resolving-merge-conflicts/SKILL.md)
- another person's missing knowledge: [`to-questionnaire`](../to-questionnaire/SKILL.md)
- issue and external-PR classification: [`triage`](../triage/SKILL.md)
- human-only setup guides: [`wizard`](../wizard/SKILL.md)
- frontend design and refinement: [`impeccable`](../impeccable/SKILL.md)
- PR checks and supervision: [`babysit-pr`](../babysit-pr/SKILL.md), also used by the Babysit workflow
- React props broader than live callers need:
  [`narrow-react-prop-types`](../narrow-react-prop-types/SKILL.md)
- a reusable automation contract: [`design-control-loop`](../design-control-loop/SKILL.md);
  its implementation: [`build-iterated-agentic-loop`](../build-iterated-agentic-loop/SKILL.md)

When the active workflow permits commands, use DO for project commands, PROVE for executable
feature contracts, and KNOW for broader project knowledge through `projectctl knowledge search`. Start with the spec-linked feature record; use
its bounded read-only Kiro ACP worker only when architecture, decisions, concepts, or operations
require deeper context. `knowledge validate` checks metadata and links locally without a model.
A long autonomous task uses `pkstack-verified-goal`, an explicit checkable predicate, and the product's supported wait or
monitoring mechanism. It never assumes native goal or loop slash commands.
Use native Kiro sub-agents for independent investigation, implementation, or review, without fixed
model slugs.

Before substantial investigation or planning, reuse relevant definitions and decisions through
the feature map and its links. After every explicitly approved implementation plan, and at task
completion, reconcile reusable understanding through
[`okf`'s document lifecycle](../okf/references/document-lifecycle.md) and `domain-modeling`.
Capture at the first permitted execution step, update existing topics idempotently, preserve
uncertainty, and reference planning context. Keep pending capture in conversation while read-only;
an explicit no-write instruction overrides capture. Denied writes or failed validation are
incomplete capture, not success. A pre-approval planning handoff alone does not authorize Wiki
writes. Skills and operational instructions remain native; no document synchronization occurs.

Keep the bounded knowledge worker separate from normal Kiro planning and execution. Do not
introduce another planner, editor-task metadata, automatic branch machinery, or an
alternate completion predicate. A workflow that would publish, merge, push, install software,
change networking, delete a worktree, or discard changes requires exact authorization for that
action. Return the selected workflow and skill route, skipped checkpoints, and direct evidence.

## Python tooling

For Python work, use [uv](../uv/SKILL.md) for dependencies and script environments,
[ruff](../ruff/SKILL.md) for lint/format, and [ty](../ty/SKILL.md) for typing.
Read only the helpers relevant to the task and preserve the chosen toolchain unless migration
is requested. These checks complement the existing behavioral tests and projectctl verification.

Every material claim carries its evidence or an explicit observed, inferred, or unknown label
where the claim is made. Run checks that are available and authorized instead of assigning them
to the human. In native Plan or where access/permissions prevent execution, state the limitation
and carry the proposed check into the permitted next step without claiming a result.
