---
name: pkstack-setup
description: Initialize or repair repository-local PKStack scaffolding for a Kiro workspace. Use when adopting PKStack, refreshing its feature-map and knowledge layout, or checking whether projectctl is ready.
---

# Set up PKStack

Set up the current workspace without leaving the user's current Kiro agent session.

Treat the request text that activated this skill as the setup context.

This Kiro-native replacement does not enumerate or write Cursor-style per-role model slugs. Native
sub-agents inherit the current session's selected Kiro model and effort unless the user makes another
supported selection. Bootstrap never edits the user's global model, effort, or role settings.

## Resolve setup from this Power

Always resolve `scripts/setup_pkstack.py` relative to this loaded `SKILL.md`.
That Power-local shim is the only pre-bootstrap and refresh entrypoint; never
execute a repository-supplied `./projectctl` to decide whether it belongs to PKStack.
Run the shim first as a no-write preflight against the current project root:

```text
python3 <resolved-skill-directory>/scripts/setup_pkstack.py --root . --dry-run --output json
```

If preflight reports `pending_updates`, show them and use `--update-managed`
only after the user explicitly approves that reviewed upgrade. Conflicts are
never overwritten. Otherwise run the same shim without `--dry-run`.

After a successful bootstrap use `.pkstack/bin/projectctl`. A root
`./projectctl` may belong to the host project and is never selected by this
skill. Do not guess a global Power path, silently install a package manager,
modify user-level Kiro settings, or widen permissions. A Python launcher and
`uv` must be available. The locked controller requires Python 3.11+; the shim
can start with the tested macOS Python 3.9 launcher and use `uv` to obtain a
supported runtime. Do not reject that path solely because `python3 --version`
reports 3.9. Report a missing launcher, missing `uv`, or a runtime acquisition
failure with its actual error and stop; do not install tools silently.

The preview makes no target-project changes. The older-Python delegation may
prepare an isolated environment and download Python or dependencies, and the
installed controller prepares its locked runtime on first use. Offline use
requires the needed interpreter and packages in the local cache. Successful
scaffolding alone does not establish that the controller works; complete the
version, doctor, and local validation checks below.

## Bootstrap and validate

1. Inspect the working tree and existing `.pkstack/` and `.kiro/` files. Preserve user-authored files and unrelated dirty work.
2. Run the Power-local setup shim as described above.
3. Treat the JSON result as the authoritative inventory of created, updated, preserved, skipped, or conflicting paths.
4. Run `<runner> version --output json`, then `<runner> doctor --output json`.
5. Resolve only setup defects that are within the requested workspace. Re-run `doctor` after each material repair.
6. Report DO (`projectctl` and project levers), PROVE (feature records), and KNOW (durable Wiki
   layout, local validation, and Kiro ACP retrieval availability) separately. Use
   `<runner> knowledge status --output json` and also report discovered `.kiro/specs/`.
   Existing native specs remain Kiro-owned planning artifacts; setup never rewrites them.
7. Whenever `Wiki/` exists, run `<runner> knowledge validate --output json`, even when no feature
   records exist. Its result composes the feature-map verdict with minimal metadata and local
   Markdown links, so a second feature-only validation is unnecessary. Without `Wiki/`, use
   `<runner> feature validate --output json`. Knowledge validation
   runs without Kiro, a model, or `okn` and does not claim full OKF conformance. Retrieval runtime
   unavailability is separate from local validation; setup never installs a replacement backend
   or edits global Kiro `/knowledge` settings.
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

Setup ends with installation, checks, and this report. Offer one relevant next step from the
user's context: [`show-me`](../show-me/SKILL.md) for a visual tour,
[`writing-for-agents`](../writing-for-agents/SKILL.md) for existing agent instructions, or
[`create-verification-skill`](../create-verification-skill/SKILL.md) for missing live proof.
Do not start onboarding, a diagram, a documentation rewrite, or a verification workflow merely
because setup succeeded. An explicitly requested follow-up may proceed within its own scope.

After setup, select the generated Poteto Kiro (`pkstack`) permission profile;
copying its files does not select it. In Kiro IDE 1.x, use the agent selector in
the chat panel or Agent Focus and choose the workspace `pkstack` agent before the next workflow
message. In Kiro CLI v3, inspect the agent picker and stay in the same chat:

```text
/agent
/agent swap pkstack
/config skills
```

The bare `/agent` opens the picker; do not substitute `/agent list`, which the
audited CLI 2.21.1 interpreted as an agent named `list`. `/config skills` shows
the effective skill inventory under the selected agent. The selected prompt,
tools, and permissions take effect on the next message. Native agent hot reload
was observed for a newly added fixture agent; that does not prove skill hot reload.
For a later managed refresh, `pkstack` disables automatic Power inclusion with
`includePowers: false` and explicitly loads reviewed workspace skills. This does
not establish isolation from skills inherited through other configuration scopes.
Stay in the same chat, temporarily select the agent that can discover the reviewed
Power, invoke this Power-local `/pkstack-setup`, and select `pkstack` again.
CLI v3 2.21.1 names its bundled default agent `default`; use `/agent swap default`
to leave the restricted profile, then `/agent swap pkstack` when setup is complete.
The swap alone does not register or discover a Power. If this skill is unavailable,
use the reviewed Power-local script from a terminal as documented in usage.md;
do not copy setup into managed workspace skills or change global Power settings.

If the newly scaffolded agent is absent, inspect the setup result and project
root, then retry the picker and same-conversation swap. If newly installed skills
such as `/pkstack-verified-goal` remain absent from `/config skills` after selection,
use one fresh session from the same repository before starting a verified goal.
In IDE 1.x, open a fresh chat/Agent Focus session and choose the workspace `pkstack`
agent. In CLI v3, exit normally and run:

```text
kiro-cli chat --v3 --agent pkstack
```

Kiro Crew and Kiro Web consume the resulting repository-local assets only
after this Power-local setup completes in IDE or CLI; neither uses this setup
skill as its entry path. Crew remains an optional orchestrator. Web must
receive the files through the cloned repository; Configuration Sync is not a
substitute for bootstrapping and committing the complete PKStack workspace
assets.

Do not run a nested Kiro process, change the user's global default agent, or
claim that the ambient setup agent received the generated ask/deny rules. Once
selected and discovered, the entire goal loop stays in the current Kiro agent
session.
