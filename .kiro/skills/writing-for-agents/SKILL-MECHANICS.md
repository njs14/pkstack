# Skill mechanics

This is the skill-specific branch of [`writing-for-agents`](SKILL.md). Read it when creating
or restructuring a Kiro Skill.

## Invocation

Kiro exposes a skill's name and description for discovery and loads its body only after the
skill is selected. The description is therefore the always-loaded context pointer: name the
task and distinct trigger branches precisely, without summarizing the body.

Choose ordinary model discovery when the agent should recognize the work on its own or when
another workflow must route to the skill. If a target Kiro surface provides an explicit-only
invocation control and the workflow should run only by human choice, use that native control;
do not copy runtime-specific metadata from another agent system.

## Splitting by invocation

Split a distinct branch into its own skill only when it should be discovered independently or
when another skill must route to it. Each additional description permanently spends context,
so independent reach must justify the new pointer.

## Router skills

When humans must remember too many explicit workflows, provide one small router that names the
available routes and the condition for each. Keep execution semantics in the destination
skills; the router is an index, not a second source of truth.
