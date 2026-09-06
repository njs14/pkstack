---
name: how
description: Explain how a subsystem works from evidence, connecting entrypoints, data flow, state, boundaries, failure behavior, and verification seams.
---

# Explain how it works

Treat the request text that activated this skill as the subsystem or behavior to explain.

Use **Explain** mode by default. Use **Critique** mode only when the request
asks whether the design is sound or how it should improve. `how` explains
mechanics; use `why` to investigate motivation.

Use [`teach`](../teach/SKILL.md) when the requested outcome combines mechanics and rationale
into a lesson. Use [`show-me`](../show-me/SKILL.md) to present inspected findings visually;
pass the same evidence packet forward and keep inferred rationale labeled.

Read [`references/roles-and-critique.md`](references/roles-and-critique.md)
before delegating or critiquing.

Start with the matching feature record and follow its explicit related links. If those do not
explain the runtime boundary, record the missing question and issue one bounded, targeted
`.pkstack/bin/projectctl knowledge search "<specific mechanism>" --budget 1200 --output json` query.
Record the selected depth and escalation reason; never inject the whole Wiki.

## Choose the path

1. Interpret the question and state a reasonable scope when it is ambiguous.
2. For one module or a narrow symbol, let the **explainer** inspect and answer
   directly.
3. For a cross-cutting subsystem, assign two to four independent **explorers**
   to distinct slices, then give their evidence to one **explainer**.

Use native Kiro sub-agents as read-only investigators. Do not pin a model or
start a separate agent runtime. The current session owns the question,
evidence packet, reconciliation, and final answer.

## Explorer role

For CLI orientation, `/code status` reports workspace and language-server status;
`/code overview` is optional when available. Use native symbol and reference
navigation when the current profile exposes it, otherwise read and search source.
Keep `/code init` a separate, explicit setup action: it can write
`.kiro/settings/lsp.json` and start language servers. Do not initialize merely to
answer an explanation request. The audited CLI 2.21.1 menu exposed `status`, `init`,
and `overview`; do not promise `/code summary` or `/code logs` on that basis.

Each explorer follows one slice deeply:

1. Find the real entrypoint instead of guessing from names.
2. Trace callers, callees, decisions, data transformations, state, and effects.
3. Read the central types, interfaces, services, and configuration.
4. Map inputs, outputs, ownership boundaries, and failure behavior.
5. Return components, ordered flow, files and symbols inspected, boundaries,
   non-obvious behavior, and unresolved gaps.

Explorer overlap is useful for checking facts, but every assigned angle needs a
distinct purpose.

## Explainer role

The explainer checks claims against code, resolves contradictions, and produces
a senior-engineer mental model rather than an annotated directory tour. Start
at the user-visible trigger and explain, in order: input, boundary validation,
orchestration, domain work, state or external effects, output, and failure
handling.

Use this output shape when the question warrants each section:

- **Overview:** what the subsystem is and what it does.
- **Key concepts:** only the types and abstractions needed for the flow.
- **How it works:** the ordered runtime path and decision points.
- **Where things live:** a short map of load-bearing files and symbols.
- **Gotchas and gaps:** surprising behavior, conflicts, and what could not be
  traced.

Separate observed behavior from inferred rationale. Verify project knowledge
and feature records against current code. End with the shortest practical
check that could falsify the explanation.

## Critique mode

Explain first. Then give the neutral explanation and relevant file map to at
least two independent read-only **critics**. Each critic must inspect the code
and apply the same rubric:

- abstraction fit;
- data-model fit;
- boundary discipline and isolation;
- readiness for likely evolution;
- complexity compared with user value; and
- consistency with established repository patterns.

Each finding names `structural`, `concern`, or `observation` severity, the
specific components, code evidence, and practical impact. A preference without
a demonstrated cost is not a finding.

The current session acts as lead. Categorize each result as **Act on**,
**Consider**, **Noted**, or **Dismissed**. Trace at least one failure path,
compare one credible alternative, separate defects from taste, and give every
accepted recommendation an executable improvement check. Present this verdict
after the standalone explanation so a reader can stop before the critique.
