---
name: pkstack-guide
description: Advise which PKStack skill or Kiro workflow to use next in a new or existing project, and why. Use for project orientation, verification readiness, and workflow-choice questions; direct execution requests keep their existing owner.
---

# Choose the next useful step

Help the user decide what to do, without starting that work. Advice is read-only: no commands,
tests, setup, prototypes, MCP calls, subagents, or writes. Preserve the active mode and scope.
For a direct execution request or later authorization, leave this advisor, read the owning
skill, and carry the settled context forward once. Do not bounce execution back to advice.

## Read before recommending

Complete this reading pass before writing the recommendation. Use the file-reading tool;
links, directory listings, and skill descriptions do not supply the linked file's contents.

1. Read [project-lifecycle.md](references/project-lifecycle.md). Resolve it relative to this
   loaded skill; after workspace setup the path is
   `.kiro/skills/pkstack-guide/references/project-lifecycle.md`.
2. Read [poteto-kiro-mode](../poteto-kiro-mode/SKILL.md), installed at
   `.kiro/skills/poteto-kiro-mode/SKILL.md`, for native routing and handoff ownership.
3. Read the project's README, then only evidence that could change the next step. An existing
   Spec, verifier, or component named by the request must be located and read now, not deferred
   to implementation. For a named Spec, start at `.kiro/specs/<name>/` and read its native
   documents. No repository means readiness is unknown, not that a new workflow is mandatory.
4. Choose one next step using those results. Before drafting the answer, read the complete
   `.kiro/skills/<chosen-skill>/SKILL.md` (or its loaded Power-relative equivalent).
   Treat it as reference material, not authorization to execute it. For a Prototype
   recommendation, also read its [workflow section](../poteto-kiro-mode/references/workflows.md).

Useful destination paths, relative to `.kiro/skills/` after setup:

| Next step | File to read before recommending it |
| --- | --- |
| Caller example or tutorial for a new library | `technical-writing/SKILL.md` |
| Compare materially different interfaces | `architect/SKILL.md` |
| Clarify unresolved product intent | `grill-me/SKILL.md` |
| Explain mechanics, rationale, or recover context | `how/SKILL.md`, `why/SKILL.md`, or `recall/SKILL.md`, respectively |
| Establish missing product-surface proof | `create-verification-skill/SKILL.md` |
| Repair an existing verifier | `maintain-verification-skill/SKILL.md` and the existing verifier |
| Reuse adequate verification | The existing verifier; the router already read owns implementation routing |

Read only the selected row's applicable files, not every row. If a read returns a truncated
file or a line-limited excerpt, continue through the end before treating that skill as read.

If a required read fails or is denied, report the missing reference and keep that recommendation
conditional. Do not invent its procedure or silently substitute memory. A simple skill-lookup
question needs only its destination read, not the lifecycle or a project inventory.

Use file-reading, directory-listing, and file-content-search tools. A shell command that only
reads is still a command and is out of scope: do not fall back to `ls`, `find`, or `rg` in a shell.
A content search with no matches does not mean a path is absent; list the containing directory
when a filename or Spec slug is unknown.

## Ground only what changes the recommendation

A simple question such as “which skill explains a module?” needs a direct answer, not an
onboarding interview. For project-specific advice, use the current conversation and relevant reads above.
Read code or command definitions when necessary to resolve a concrete gap. Reuse settled
decisions. Do not inventory the whole repository, load the whole Wiki, or mine private histories.
Do not ask the user to point out an artifact that the workspace's available reading/search
tools can find.

Without a repository, advise from the supplied goal and state that project readiness is unknown.
Ask a focused question only when the missing answer would change the next step. Unknown intent
is a question; a fact discoverable in the available project is reading work. Preserve existing
tools and stack choices unless changing them is the question.

Distinguish an installed skill from the tool, account, application, or integration it still
needs. A reported bug is not a reproduced bug; a command definition or old successful run is
not a current passing result. Mark observations, historical evidence, inference, and gaps
where they affect the advice. Existing checks may establish regression coverage without
proving a proposed change: name matching proof for the new behavior too, including a visual
or interaction change such as a tooltip.
Do not call an artifact absent, incomplete, stale, or approved without evidence for that exact
claim. A terse task can include both implementation and its tests; short is not incomplete.
Unchecked tasks and empty search results do not establish implementation state. Keep that state
unverified until the relevant code is inspected, and carry uncertainty into the handoff prompt.

## Return a useful recommendation

Explain the situation in plain language, the most important gap or uncertainty, and one next
action with its reason. Say what observable result would make that step successful. Include a
ready-to-send prompt beginning with the actual `/skill-name` (or the documented native handoff),
carrying relevant context, settled choices, and scope. Preserve an explicit execution boundary,
but do not add a new approval requirement merely because this turn requested advice.
Add a short sequence of later steps only when dependencies make it useful; do not turn every
answer into a full lifecycle checklist or require every helper.

For example, a new library needs one useful caller example and a runnable behavior check, not
a browser harness. An existing service with adequate proof may proceed directly to its requested
change. A stale verifier calls for maintenance, not replacing it with a fresh system.
When the user needs to see alternative interactions operate, recommend the Prototype workflow
through `/poteto-kiro-mode prototype ...`, with an observation that will settle the choice. A read-only
advisory turn does not make the recommended next step a plan-only task: native Plan can analyze
but cannot run the prototype. Do not substitute a prose comparison for requested empirical proof.

## Keep advice and execution distinct

[`pkstack-setup`](../pkstack-setup/SKILL.md) owns installation and repair;
[`poteto-kiro-mode`](../poteto-kiro-mode/SKILL.md) owns task routing and native planning handoffs. An advisory
answer does not invoke either. If the user explicitly requests a plan, prepare the native Plan
handoff described by `poteto-kiro-mode`, carrying the shared `grilling` method and settled context; do
not conduct a second planning interview or claim to switch modes. An existing Spec stays
authoritative. Approved requirements/design do not establish that its task plan or execution
is approved. Read the artifacts, distinguish those states, and preserve verifier binding before
execution rather than postponing it until completion.

Use the native CLI grammar below, after the router read. Do not append a description to a Spec
identifier or put prose after bare `/spec`. The command and the subsequent description are
separate messages; placeholder names are replaced with the actual slug:

- Conversational Plan, only when plan-only work is requested:
  `/plan Read .kiro/skills/grilling/SKILL.md; <outcome, settled context, and open questions>`.
  Plan keeps Kiro's own approval-to-execution handoff; do not tell the user to swap back to
  `pkstack` after Plan approval or require a Spec merely to leave Plan.
- New Spec: `/spec new <name>`. Then provide the scoped description when Kiro asks, including
  `Read .kiro/skills/grilling/SKILL.md`, settled choices, and remaining approval boundaries.
- Resume Spec: `/spec <name>`. If the document viewer opens, use its **Continue** action
  (`C` in the audited CLI 2.21.2) to resume the Spec agent. Then send the carried context
  separately, preserving unapproved phases and the user's no-implementation boundary.
  Opening the viewer or continuing the conversation is not task approval.
- `/spec run <name>` starts task execution; it is not an advisory resume command.

In the IDE, describe native workflow selection and provide the same context, not CLI commands.
Never claim to switch modes for the user or fabricate a slash command for a playbook. A
recommendation alone is never approval, and an existing authorization need not be granted twice.

Advice does not create a plan file, task graph, Wiki entry, schedule, or background agent. Missing
capabilities stay explicit; do not install tools, change permissions, or substitute another runtime
to make a recommendation appear executable.

## Before sending the answer

Check the actual reading results, not your intended reads. Every ready-to-send `/skill-name`
prompt requires its destination's complete `SKILL.md` to have been read in this turn, including
any optional second prompt. If that read is still missing, read it now; do not answer yet.
Native Plan and Spec use the router read above; Prototype also needs its workflow section.
Include a brief grounding sentence naming the inspected project evidence and destination.
Do not claim to have read a linked file merely because its parent document was loaded.
