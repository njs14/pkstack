---
name: setup-pk-stack
description: Initialize or repair repository-local PK-Stack scaffolding for a Kiro workspace. Use when adopting PK-Stack, refreshing its feature-map and knowledge layout, or checking whether projectctl is ready.
---

# Set up PK-Stack

Set up the current workspace without leaving the user's current Kiro agent session.

Treat the request text that activated this skill as the setup context.

This Kiro-native replacement does not enumerate or write Cursor-style per-role model slugs. Native
sub-agents inherit the current session's selected Kiro model and effort unless the user makes another
supported selection. Bootstrap never edits the user's global model, effort, or role settings.

## Resolve setup from this Power

Always resolve `scripts/setup_pk_stack.py` relative to this loaded `SKILL.md`.
That Power-local shim is the only pre-bootstrap and refresh entrypoint; never
execute a repository-supplied `./projectctl` to decide whether it belongs to PK-Stack.
Run the shim first as a no-write preflight against the current project root:

```text
python3 <resolved-skill-directory>/scripts/setup_pk_stack.py --root . --dry-run --output json
```

If preflight reports `pending_updates`, show them and use `--update-managed`
only after the user explicitly approves that reviewed upgrade. Conflicts are
never overwritten. Otherwise run the same shim without `--dry-run`.

After a successful bootstrap use `.pstack/bin/projectctl`. A root
`./projectctl` may belong to the host project and is never selected by this
skill. Do not guess a global Power path, silently install a package manager,
modify user-level Kiro settings, or widen permissions. If Python 3.11+ or `uv`
is missing, report that exact prerequisite and stop.

## Bootstrap and validate

1. Inspect the working tree and existing `.pstack/` and `.kiro/` files. Preserve user-authored files and unrelated dirty work.
2. Run the Power-local setup shim as described above.
3. Treat the JSON result as the authoritative inventory of created, updated, preserved, skipped, or conflicting paths.
4. Run `<runner> doctor --output json`.
5. Resolve only setup defects that are within the requested workspace. Re-run `doctor` after each material repair.
6. Report DO (`projectctl` and project levers), PROVE (feature records), and KNOW (`Wiki/`, canonical
   `okn` availability, and degraded mode) separately. Also report discovered `.kiro/specs/`.
   Existing native specs remain Kiro-owned planning artifacts; setup never rewrites them.
7. Run `<runner> feature validate --output json`. Whenever `Wiki/` exists, independently run
   `<runner> knowledge validate --output json`, even when no feature records exist. The knowledge
   result must compose the feature-map verdict with broader OKF conformance through canonical `okn`
   when available. Missing `okn` is an explicit degraded-mode warning; setup never installs it or
   edits global Kiro `/knowledge` settings.
8. If no project-local verification workflow covers the product's real user surface, offer
   `create-verification-skill` as the next explicit step. Do not silently generate one during setup;
   its repository interview and live proof need their own bounded run.

Setup must be idempotent. Never overwrite a conflicting file merely to make setup appear successful. Surface the conflict with its path and the smallest safe resolution.

## Handoff

Report:

- the runner used;
- paths created or changed;
- paths deliberately preserved;
- doctor and validation status;
- any approval or restart still required.

Kiro discovers newly copied workspace skills at session startup. After setup,
the generated Poteto Kiro (`pk-stack`) permission profile does not attach
retroactively. In Kiro IDE 1.x, use the agent selector in the chat panel or
Agent Focus and choose the workspace `pk-stack` agent before the next workflow
message. In Kiro CLI v3, stay in the same chat and run:

```text
/agent swap pk-stack
```

The selected prompt, tools, and permissions take effect on the next message.
For a later managed refresh, the `pk-stack` profile intentionally has no Powers.
Stay in the same chat, temporarily select the Power-enabled setup agent, invoke
this Power-local `/setup-pk-stack`, and select `pk-stack` again. In CLI v3 those
agent selections can be `/agent swap kiro_default` and `/agent swap pk-stack`;
if the Power-enabled agent has another name, use the agent that performed
initial setup.

If the newly scaffolded agent or `/verified-goal` is not discoverable in this
session, open one fresh session from the same repository before starting a
verified goal. In IDE 1.x, open a fresh chat/Agent Focus session and choose the
workspace `pk-stack` agent. In CLI v3, exit normally and run:

```text
kiro-cli chat --v3 --agent pk-stack
```

Kiro Crew and Kiro Web consume the resulting repository-local assets only
after this Power-local setup completes in IDE or CLI; neither uses this setup
skill as its entry path. Crew remains an optional orchestrator. Web must
receive the files through the cloned repository; Configuration Sync is not a
substitute for bootstrapping and committing the complete PK-Stack workspace
assets.

Do not run a nested Kiro process, change the user's global default agent, or
claim that the ambient setup agent received the generated ask/deny rules. Once
selected and discovered, the entire goal loop stays in the current Kiro agent
session.
