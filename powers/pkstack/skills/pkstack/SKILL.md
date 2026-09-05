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
handoff. In CLI v3, ask the user to run `/spec new <name>` and
choose Feature, Quick Spec, or Bug, or `/spec <name>` to resume; after the native artifacts are
ready, use `/agent swap pkstack`. In the IDE, use **Build with spec** or the Spec, Quick Spec, or Bug
Fix workflow in the agent picker, then reselect `pkstack` in the same conversation. Web uses its
native Spec picker and built-in primary agent; it does not claim the CLI slash command or a
selectable project primary agent. Crew may consume committed spec artifacts through its Task
Runner, but PKStack does not claim Crew can switch to Kiro's built-in Spec agent.

Kiro owns `requirements.md` or `bugfix.md`, `design.md`, `tasks.md`, task dependency analysis, and
native parallel task execution. Once that native plan is ready, PKStack wraps it with the relevant
upstream-derived workflow skills, a narrow feature contract, deeper OKF context when needed, and a
current-session `/pkstack-verified-goal`. It never creates a second task graph or marks a Kiro task checkbox
as executable proof.

Then select the narrowest shipped skill:

- architecture or alternatives: `architect` or `arena`
- investigation, explanation, or teaching: `blast-radius`, `how`, `why`, `figure-it-out`, or
  `teach`
- repeatable practice and context: `automate-me`, `recall`, or approval-gated `reflect`
- durable project knowledge: `okf`
- verification design and upkeep: `create-verification-skill` or `maintain-verification-skill`
- implementation discipline: `tdd`, `typescript-best-practices`, `technical-writing`, `unslop`, or
  a named `principle-*` skill
- plain restatement or evidence trail: `bro` or `show-me-your-work`
- bounded parallel work or independent challenge: `swarm`, `interrogate`, or `pkstack-model-council`
- completion: `pkstack-verified-goal` with `.pkstack/bin/projectctl`

Use DO for project commands, PROVE for executable feature contracts, and KNOW for broader project
knowledge through canonical `okn`. Start with the spec-linked feature record; use `okn` only when
architecture, decisions, concepts, or operations require deeper context. A long autonomous task
uses `pkstack-verified-goal`, an explicit checkable predicate, and the product's supported wait or
monitoring mechanism. It never assumes native goal or loop slash commands.
Use native Kiro sub-agents for independent investigation, implementation, or review, without fixed
model slugs.

Do not introduce a second runtime, editor-task metadata, automatic branch machinery, or an
alternate completion predicate. A workflow that would publish, merge, push, install software,
change networking, delete a worktree, or discard changes requires exact authorization for that
action. Return the selected workflow and skill route, skipped checkpoints, and direct evidence.
