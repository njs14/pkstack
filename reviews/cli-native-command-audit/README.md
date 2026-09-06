# Kiro CLI command audit — 2026-09-06

Three independent runners audited session/configuration workflows, Powers/skills/prompts, and planning/code/knowledge workflows. The supervising runner checked selected commands in the installed native CLI. The result is six command/workflow improvements and one adjacent wording correction. No product implementation was changed by this audit.

## Scope and evidence

- Repository base: `63e4e2c8a8029c40a2a522931e1feafa0c2e7b53`.
- Audited branch: `codex/cli-power-discovery-docs`, including its four existing uncommitted Power-discovery documentation changes. Those files were preserved unchanged during this audit.
- Runtime: `kiro-cli 2.21.1`, ordinary local `kiro-cli chat --v3`, default agent, a disposable workspace.
- Native actions inspected configuration, command completion, agent selection, and code-intelligence status. A minimal no-tools agent was created only in the disposable workspace after the session started, validated with `kiro-cli agent validate --path <fixture>`, and selected to test discovery without restarting. The session returned to the default agent and exited normally.
- No model task, Spec analysis, code initialization, Power installation, or global configuration edit was performed. The raw terminal recording remains outside the repository; the [compact receipt](native-probe.json) retains selected output and its SHA-256.
- Documentation support is distinguished from command recognition and actual execution. A menu entry does not prove the full workflow works.

## Findings

### F1 — P2: the Plan-only workflow incorrectly assumes a Spec task file

[The multi-phase workflow](../../powers/pkstack/skills/pkstack/references/workflows.md) selects native Plan for a plan-only request at line 276, then unconditionally requires refinement of native `tasks.md` at line 283. [The router skill](../../powers/pkstack/skills/pkstack/SKILL.md) chooses Plan at line 25 but its CLI handoff at lines 34–36 only describes Spec commands.

Kiro documents `/plan <request>` as a conversational planning route, distinct from the formal requirements/design/tasks files created by Specs. Plan's analysis phase cannot write files or execute commands. The installed CLI exposes `/plan` in completion; a Plan session was not executed. Sources: [Plan](https://kiro.dev/docs/specs/plan/), [native Plan command](https://kiro.dev/docs/reference/slash-commands/#plan).

**Recommended correction:** add the explicit native Plan handoff; make `tasks.md` refinement conditional on a Spec-backed route. A plan-only request should return the conversational plan and stop. Do not require a prototype to execute inside read-only Plan, and preserve the requirement for explicit implementation authorization before approving execution.

### F2 — P2: discovery troubleshooting skips native diagnostics and agent hot reload

[First task](../../powers/pkstack/docs/first-task.md), line 75, and [setup](../../powers/pkstack/skills/pkstack-setup/SKILL.md), lines 109–115, group missing agents and missing skills into one fresh-session fallback. [Usage](../../powers/pkstack/docs/usage.md), lines 181–196, offers switching or restarting without the targeted inventory.

These native routes worked in the installed CLI:

```text
/config skills
/agent
/agent swap <name>
```

The first opened a read-only skill inventory. The second opened the agent picker. After a validated no-tools agent was added to the workspace while the session was already running, `/agent swap pkstack-audit-probe` succeeded without a restart. Returning with `/agent swap default` also succeeded.

**Recommended correction:** inspect skills with `/config skills`, inspect agents with the bare `/agent` picker, and try the intended same-conversation swap before restarting. Treat agent discovery separately from skill discovery. Retain a conditional fallback for a client/session that still fails to discover newly generated skills; this fixture did not test skill hot reload or a full PKStack bootstrap. Sources: [configuration inspection](https://kiro.dev/docs/configuration/#inspect-configuration-in-v3), [agent/MCP hot reload](https://kiro.dev/docs/mcp/configuration/#hot-reload).

**Version trap:** although current shared documentation lists `/agent list`, this runtime interpreted it as an agent named `list` and returned `Agent 'list' not available`. Use the observed bare picker syntax for this build. [Agent reference](https://kiro.dev/docs/reference/slash-commands/#agent).

### F3 — P3: native Spec analysis and document viewing are missing from the handoff

[The router skill](../../powers/pkstack/skills/pkstack/SKILL.md), lines 34–36, documents creation/resume but omits the native review commands. [Usage](../../powers/pkstack/docs/usage.md), around lines 262–269, goes from native planning to binding; [architect](../../powers/pkstack/skills/architect/SKILL.md), line 27, asks for refinement without mentioning Kiro's requirements analysis.

```text
/spec analyze_requirements <feature-name>
/spec view <feature-name> requirements
/spec view <feature-name> design
/spec view <feature-name> tasks
```

The installed `/spec` subcommand menu includes both `view` and `analyze_requirements`. No action was executed. Kiro documents requirements analysis for ambiguity, conflict, missing details, and Quick Specs; it can present choices and update `requirements.md`. Sources: [Analyze Requirements](https://kiro.dev/docs/specs/analyze-requirements/), [Spec commands](https://kiro.dev/docs/reference/slash-commands/#spec).

**Recommended correction:** offer analysis as an optional checkpoint for complex or unclear requirements, then reuse its findings rather than repeat the same analysis. Add document-view examples beside the handoff. Do not promise requirements analysis for a Bug Fix package containing only `bugfix.md`; viewing a document does not establish approval or verifier binding.

### F4 — P3: investigation guidance omits native code-intelligence orientation

[How](../../powers/pkstack/skills/how/SKILL.md), line 42, asks explorers to trace entrypoints/callers/callees; [architect](../../powers/pkstack/skills/architect/SKILL.md), line 26, asks for source inspection. The audited guidance does not point to native code-intelligence status or orientation.

The installed subcommand menu exposes exactly `status`, `init`, and `overview`. Executing `/code status` opened the workspace/LSP status panel and reported the disposable workspace as uninitialized.

**Recommended correction:** document `/code status` and optional `/code overview` as orientation tools, and encourage native symbol/reference navigation when available. Keep `/code init` an explicit setup action: it can write `.kiro/settings/lsp.json` and start language servers. Do not advertise `/code summary` or `/code logs` as verified v3 commands merely because the broader documentation lists them. [Code intelligence](https://kiro.dev/docs/tools/code-intelligence/).

### F5 — P3: the upgrade guide omits the command for its required agent switch

[Upgrade 0.4](../../powers/pkstack/docs/upgrade-0.4.md), lines 15–16, tells the user to leave the restricted workspace agent, then immediately shows the terminal preview. Its return step at line 47 supplies `/agent swap pkstack`.

**Recommended correction:** show the missing initial `/agent swap default` or link to the existing managed-refresh instructions. This exact command succeeded on installed 2.21.1. Do not replace `default` with a legacy built-in identifier from a different documentation version. [Agent reference](https://kiro.dev/docs/reference/slash-commands/#agent).

### F6 — P3: model/effort ownership lacks an actionable native picker hint

[Usage](../../powers/pkstack/docs/usage.md), line 36, explains that PKStack inherits Kiro's selected model and effort, but does not show how to select them.

**Recommended correction:** add one optional sentence naming `/model` and `/effort`. Both commands appeared in native completion; no selection was changed. Available choices depend on runtime, account, and model. Do not bake a model slug or effort default into PKStack. Sources: [model command](https://kiro.dev/docs/reference/slash-commands/#model), [effort preferences](https://kiro.dev/docs/models/effort/#persisting-your-effort-level-cli).

### F7 — P2 wording correction: disabling Powers is not proof of skill isolation

The pending [usage clarification](../../powers/pkstack/docs/usage.md), lines 59–60, says `includePowers: false` “keeps workflows on the reviewed workspace skills.” This is stronger than that setting's documented scope.

The [shipped primary profile](../../powers/pkstack/templates/project/.kiro/agents/pkstack.json) disables automatic Powers and explicitly loads workspace skills. Kiro separately documents skill/default-resource inheritance and merged configuration scopes. This audit did not test the actual `pkstack` agent's inherited skill inventory and does not claim a runtime isolation defect. Sources: [CLI inheritance notes](https://kiro.dev/changelog/cli/2-10/), [configuration conflicts](https://kiro.dev/docs/configuration/#resolving-conflicts).

**Recommended correction:** say the setting disables automatic Power inclusion while PKStack explicitly loads reviewed workspace skills. Use `/config skills` under the selected agent to inspect the effective inventory. No user setting needs to be changed for this prose correction.

## Keep the existing boundaries

- Native `/goal` is not a replacement for PKStack's stored executable verifier, Spec-snapshot checks, attempt history, and pass/fail state. The current native startup tip advertised `/goal`, but typing it produced no completion; it was not submitted. Preserve the version/session-qualified uncertainty rather than claim universal absence or availability. [Native goal documentation](https://kiro.dev/docs/cli/chat/goal/), [PKStack goal implementation](../../powers/pkstack/src/pkstack/goal.py).
- Native `/knowledge` indexing/search does not establish PKStack's host-validated quotations, source hashes, context budget, or local knowledge/link checks. No indexing or experimental-setting change is recommended. [Native reference](https://kiro.dev/docs/reference/slash-commands/#knowledge), [host validation](../../powers/pkstack/src/pkstack/knowledge_payload.py).
- The previous `/powers` clarification already covers Power discovery versus registration/project bootstrap; it is not counted as a new miss.
- Saved-prompt creation/editing/expansion remains version-sensitive. `/prompts` appeared in completion, but Tab exposed no creation/edit/details menu. The prior recorded `/prompts details` dispatch mismatch is not resolved by this audit. Retain the existing user-owned prompt guidance without promising an untested shortcut. [Prompt documentation](https://kiro.dev/docs/cli/chat/manage-prompts/).
- A skill named `pr-review` can expose `/pr-review`; this is not evidence for a built-in universal `/review` command. Native commands do not replace PKStack's independent-review contract.
- No useful replacement was established for receipt-aware setup/migration, permission policy, durable verification evidence, or bounded retrieval. General session/compaction conveniences may be useful, but did not correspond to a concrete missing replacement in this audit.

## Recommended follow-up

Fix F1 and F7, then add F2's native diagnostics and conditional discovery flow. Add the compact optional command examples in F3–F6 to the relevant detailed guides instead of enlarging the quick start into a complete Kiro command catalog. Revalidate any changed skill instructions and generated copies through the normal reviewed setup workflow. This audit itself makes no such implementation change.
