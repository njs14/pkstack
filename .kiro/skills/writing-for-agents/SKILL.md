---
name: writing-for-agents
description: Write or revise agent-facing instructions, including AGENTS.md, Kiro Skills, steering files, and pointer-linked reference documents.
---

# Writing for agents

Treat the request text that activated this skill as the agent-facing writing task.
Use this method for any document an agent consumes: `AGENTS.md`, a Kiro Skill,
`.kiro/steering/`, or a reference reached through one of those files. Preserve the
repository's intent and safety boundaries while making the agent's path predictable.

Use [`technical-writing`](../technical-writing/SKILL.md) for human-facing documentation.
If both audiences need the same facts, link their distinct instructions to one authoritative
reference. Finish prose with [`unslop`](../unslop/SKILL.md), preserving exact triggers,
checkpoints, permissions, and completion criteria.

For skill frontmatter, invocation, and router decisions, read
[`SKILL-MECHANICS.md`](SKILL-MECHANICS.md).

## Context pointers

A context pointer names material outside the current context and states when to load it.
A skill description and an `AGENTS.md` link are both pointers. Their wording determines
whether the agent reaches the target.

- Front-load the leading term that should trigger the pointer.
- Name each genuinely distinct trigger branch once; collapse synonyms.
- Remove identity or explanation already carried by the target.
- Sharpen a weak pointer before moving must-have content into always-loaded context.

## Spend the right load

- **Context load** is always-loaded text competing for the agent's attention and window.
- **Cognitive load** is what a human must remember or choose explicitly.

Spend context on rules that apply broadly. Spend cognitive load where human judgement or
explicit invocation matters. Material reached only through a pointer avoids most context
load, while material with no pointer relies entirely on human memory.

## Protect the information hierarchy

Place content on the lowest tier that still makes it reliably available:

1. **In-file step**: ordered action required on this path.
2. **In-file reference**: definitions or rules consulted during that path.
3. **Disclosed reference**: branch-specific material loaded through a precise pointer.

Inline what every branch needs. Disclose what only some branches need. Keep a concept's
definition, rules, and caveats together under one heading. When a document is long even
after duplication is removed, split it by invocation branch or execution sequence rather
than scattering related rules.

## Give steps completion criteria

End each step with a condition that is both checkable and demanding. Prefer "every modified
interface is accounted for and its gate is green" over "review the interfaces." A clear
bound resists premature completion; an exhaustive bound drives the necessary legwork.

Sharpen a vague bound first. If a genuinely fuzzy step is still rushed because later steps
are visible, isolate the later sequence behind a real context boundary such as a handoff or
subagent task.

## Use leading words and positive targets

A leading word is a compact, established concept that anchors repeated behavior. Reuse the
term, not its full definition, after defining it once. Prefer familiar terms that recruit
useful prior knowledge.

State the target behavior directly. Reserve prohibitions for hard guardrails, and pair each
one with the positive action the agent should take so attention lands on the desired path.

## Prune sediment

- Keep each meaning in one source of truth.
- Treat scripts, configuration, directory layout, and `--help` output as authoritative.
  Document a lookup only when it is expensive or the reason and gotcha are otherwise hidden.
- Remove stale branches, exposition that does not change execution, and instructions the
  target model already follows by default.
- When a sentence is a no-op, delete it rather than polishing it.

Finish by verifying every pointer resolves, each trigger is discriminating, required safety
rules remain, completion criteria are observable, and the edited document contains no
duplicated source of truth.
