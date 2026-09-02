---
name: setup-pstack
description: Initialize or repair PK-Stack project scaffolding for Kiro CLI v3. Use when adopting PK-Stack in a repository, refreshing its feature-map and knowledge layout, or checking whether projectctl is ready.
compatibility: Kiro CLI v3; Python 3.11 or newer, or uv, available in the workspace.
---

# Set up PK-Stack

Set up the current workspace without leaving the user's current interactive Kiro session.

Requested setup context: $ARGUMENTS

## Resolve setup from this Power

Always resolve `scripts/setup_pstack.py` relative to this loaded `SKILL.md`.
That Power-local shim is the only pre-bootstrap and refresh entrypoint; never
execute a repository-supplied `./projectctl` to decide whether it belongs to PK-Stack.
Run the shim first as a no-write preflight against the current project root:

```text
python3 <resolved-skill-directory>/scripts/setup_pstack.py --root . --dry-run --output json
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
6. If the project already has features, run `<runner> feature validate --output json` and `<runner> knowledge validate --output json`.

Setup must be idempotent. Never overwrite a conflicting file merely to make setup appear successful. Surface the conflict with its path and the smallest safe resolution.

## Handoff

Report:

- the runner used;
- paths created or changed;
- paths deliberately preserved;
- doctor and validation status;
- any approval or restart still required.

Kiro discovers newly copied workspace skills at session startup. After setup,
the generated Poteto Kiro (`pstack`) permission profile does not attach
retroactively. Before
the next workflow message, instruct the user to run:

```text
/agent swap pstack
```

The selected prompt, tools, and permissions take effect on the next message.
For a later managed refresh, the `pstack` profile intentionally has no Powers.
Stay in the same chat, run `/agent swap kiro_default`, invoke this Power-local
`/setup-pstack`, and run `/agent swap pstack` again. If the local Power-enabled
agent has another name, use the agent that performed initial setup.
If the newly scaffolded agent or `/verified-goal` is not discoverable in this
session, instruct the user to exit and restart from the same repository with:

```text
kiro-cli chat --v3 --agent pstack
```

Do not run a nested Kiro process, change the user's global default agent, or
claim that the ambient setup agent received the generated ask/deny rules. Once
selected and discovered, the entire goal loop stays in that current V3 session.
