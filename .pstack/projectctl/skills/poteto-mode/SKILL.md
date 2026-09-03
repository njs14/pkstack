---
name: poteto-mode
description: Route broad Poteto workflow requests into PK-Stack's Kiro-native skills, project interfaces, and current-session verification loop.
compatibility: Kiro IDE 1.x and Kiro CLI v3; Kiro Crew compatible; Kiro Web supported by design but untested; projectctl is used after setup.
---

# Use PK-Stack mode

Treat the request text that activated this skill as the outcome to route through PK-Stack.

This is the discoverable compatibility name for the broader Poteto workflow. Keep execution in the
current Kiro agent session. First classify the request against
[`references/workflows.md`](references/workflows.md), read the matching section, and preserve its
ordered checkpoints. If a checkpoint truly does not apply, keep it visible as
`<checkpoint> skipped: <specific reason>` instead of silently collapsing the workflow.

Then select the narrowest shipped skill:

- architecture or alternatives: `architect` or `arena`
- investigation, explanation, or teaching: `blast-radius`, `how`, `why`, `figure-it-out`, or
  `teach`
- repeatable practice and context: `automate-me`, `recall`, or approval-gated `reflect`
- verification design and upkeep: `create-verification-skill` or `maintain-verification-skill`
- implementation discipline: `tdd`, `typescript-best-practices`, `technical-writing`, `unslop`, or
  a named `principle-*` skill
- plain restatement or evidence trail: `bro` or `show-me-your-work`
- bounded parallel work or independent challenge: `swarm`, `interrogate`, or `model-council`
- completion: `verified-goal` with `.pstack/bin/projectctl`

Use DO for project commands, PROVE for executable feature contracts, and KNOW for broader project
knowledge. A long autonomous task uses `verified-goal`, an explicit checkable predicate, and the
product's supported wait or monitoring mechanism. It never assumes native goal or loop slash
commands.
Use native Kiro sub-agents for independent investigation, implementation, or review, without fixed
model slugs.

Do not introduce a second runtime, editor-task metadata, automatic branch machinery, or an
alternate completion predicate. A workflow that would publish, merge, push, install software,
change networking, delete a worktree, or discard changes requires exact authorization for that
action. Return the selected workflow and skill route, skipped checkpoints, and direct evidence.
