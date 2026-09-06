---
name: pkstack
description: Route broad Poteto workflow requests into PKStack's Kiro-native skills, project interfaces, and current-session verification loop.
---

# Use PKStack mode

Treat the request text that activated this skill as the outcome to route through PKStack.

This is PKStack's entry point for the broader Poteto workflow. Keep execution in the
current Kiro agent session. First classify the request against
[`references/workflows.md`](references/workflows.md), read the matching section, and preserve its
ordered checkpoints. If a checkpoint truly does not apply, keep it visible as
`<checkpoint> skipped: <specific reason>` instead of silently collapsing the workflow.

## Use Kiro's native planning spine

For a user-requested native Plan, select that mode before asking planning questions. If native
Plan is not already active, return a concrete same-conversation handoff and stop for native
selection: in CLI, `/plan Read .kiro/skills/grilling/SKILL.md; <requested outcome and settled
context>`; in the IDE, select native Plan with the same instruction and context. Include settled
choices, rationale, evidence links, and open questions. Do not conduct the planning interview
under `pkstack` first. This explicit mode request overrides the trivial-change skip below;
standalone decision interviews remain exempt.

For all planning entered through PKStack, read and apply [`grilling`](../grilling/SKILL.md)
as the shared interview method. Inspect available facts, reuse settled answers and rationale,
then settle only consequential open choices. Planning helpers consume that context rather than
starting another mandatory interview. Kiro still owns modes, phase approvals, and execution.

Before reproducing planning inside a PKStack skill, select Kiro's native workflow:

- use a standard **Spec** for an unfamiliar, cross-boundary, high-risk, or requirements-sensitive
  feature;
- use **Quick Spec** for a bounded, well-understood feature whose requirements and design do not
  need phase-by-phase approval;
- use **Bug Fix** for a reproducible defect; and
- use native **Plan** for a plan-only request.

An obvious one- or two-file change may remain in the default `pkstack` flow, but state the concrete
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
Feature, Quick Spec, or Bug, or `/spec <name>` to resume. After native approval
and when execution is permitted, return with `/agent swap pkstack`. In the IDE, use **Build with spec** or the Spec, Quick Spec, or Bug
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
