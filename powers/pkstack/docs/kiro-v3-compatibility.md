# Kiro compatibility

PKStack targets Kiro CLI v3 and the Kiro IDE agent panel. Install the Power,
run `/pkstack-setup` in the target workspace, and select its `pkstack` agent
where Kiro supports selecting a primary project agent.

## Power format

PKStack uses the current [Agent Plugins format](https://kiro.dev/docs/powers/create/):
`plugin.json` identifies the Power, `skills/` contains its workflows, and
`dev.kiro/steering/` contains Kiro-specific steering. `dev.kiro` is Kiro's
reverse-domain namespace, not a development-only folder. Setup copies those
steering files into the project's `.kiro/steering/` directory.

Kiro also supports the legacy `POWER.md` format (singular), as described in its
[installation guide](https://kiro.dev/docs/powers/installation/). It is an
alternative to `plugin.json`; PKStack does not require a second manifest.
`POWERS.md` is not a documented manifest filename. Neither the current manifest
schema nor Kiro's creation guide defines a custom JPG field. Repository artwork
is separate from the installable Power.

## Surfaces and limits

| Surface | PKStack support |
| --- | --- |
| Kiro CLI v3 | Primary. Use an ordinary v3 chat and the workspace `pkstack` agent. Native Standard and Quick Spec repair campaigns were exercised on September 5, 2026 with CLI 2.21.1. |
| Kiro IDE | Primary. Folder import, setup, agent discovery, and bounded Standard and Quick Spec repair workflows were exercised with IDE 1.0.437. |
| Kiro Crew | Optional. Use its supported Kiro CLI path. Crew's direct KAS projection does not preserve inline permission or native subagent parity. |
| Kiro Web | Supported by design, explicitly untested. It needs a repository with the generated workspace assets and Python 3.11+ plus uv in its sandbox. It cannot select a project custom agent as primary. |
| Mobile and Windows | Outside the exercised PKStack support contract. |

These are dated observations, not proof for every later Kiro build or workflow.
The repository retains the [detailed compatibility evidence](https://github.com/njs14/pkstack/blob/main/docs/kiro-v3-compatibility.md)
and [release status](https://github.com/njs14/pkstack/blob/main/Wiki/knowledge/pkstack/release-record.md).

## Runtime and workflow ownership

The controller requires Python 3.11+ and uv. The Power-local setup shim can
start with the tested macOS Python 3.9 launcher and ask uv for the locked runtime.
That path can download an interpreter or dependencies; offline use requires a
populated cache. Archify's bundled renderer requires Node.js 18+.

Kiro owns native Specs, Quick Specs, model and effort selection, subagents,
hooks, permissions, and conversation state. `/pkstack-verified-goal` records a
bounded verification loop in the current conversation; it is not Kiro's native
`/goal` command. ACP is used only for bounded knowledge retrieval, not ordinary
planning or implementation. Kiro's permission controls remain authoritative.

After setup or an approved managed refresh, run `.pkstack/bin/projectctl doctor
--output json`. Setup health does not prove an application repair; use the
[first-task guide](first-task.md) for a failure-to-pass walkthrough. See the
[usage guide](usage.md) for model selection, native planning, permissions,
knowledge retrieval, and upgrades.
