# PKStack Power

<p align="center">
  <img src="assets/banner.png" alt="PKStack: From plan to proof. A scholarly potato ghost with an OKF knowledge tree in the background." width="600">
</p>

Poteto’s pstack workflows, adapted for Kiro.

This directory is the installable Power. PKStack combines Poteto's workflow
checkpoints with Kiro's native planning and tools. A repository-local
`projectctl` command records executable proof; OKF Wiki files and optional
canonical `okn` supply broader project context.

## Install and start

You need Kiro CLI v3 or Kiro IDE 1.x, Python 3.11+, and `uv`. In Kiro IDE,
use **Powers → Add Custom Power → Import power from a folder** and select
this directory. Review the Power, then run `/pkstack-setup` in your target
project. Approve the previewed changes and select the workspace `pkstack`
agent. In CLI v3, use `/agent swap pkstack`.

Start work with `/pkstack <task>`, or choose a focused command:

| Command | Purpose |
| --- | --- |
| `/pkstack` | Poteto's planning, implementation, and review workflow |
| `/pkstack-setup` | Preview setup or a managed refresh |
| `/pkstack-maintain` | Review upstream changes to the Power |
| `/pkstack-verified-goal` | Implement and repair against one stored verifier |
| `/pkstack-model-council` | Compare independent reviews |
| `/pkstack-principles` | Apply the engineering-principles catalog |

Imported skills retain their names, including `/archify`, `/show-me`, and
individual `/principle-*` skills. `/okf` is the knowledge-integration exception.
Kiro's native `/spec`, model choice, effort, and permissions remain Kiro-owned.

Follow the [executable failing-task walkthrough](https://github.com/njs14/pkstack#try-one-failing-task)
to record a failure, repair the example in the same Kiro conversation, and
confirm a passing stored result. The [usage guide](docs/usage.md) includes
terminal-only setup, feature contracts, and recovery.

`plugin.json` owns the release version. Setup materializes workspace assets
in `.kiro/` and a locked controller in `.pkstack/`; this Power remains the
source for future refreshes. It does not launch a replacement agent runtime.
Legacy managed installations need a reviewed clean reinstall; setup adds no
aliases, migrates no state, and deletes no user files.

CLI 2.21.0 has recorded fail → repair → pass evidence. IDE 1.0.437 has recorded
native import, setup, generated-profile selection, and command-approval proof;
IDE goal and Spec execution remain untested. Web is untested end to end.
The 0.3.0 release is withheld and the autonomous updater is disabled after a
proposal-validation failure. See the evidence links below before relying on
any broader claim.

## Package references

- [Usage and recovery](docs/usage.md)
- [Architecture and trust boundaries](docs/architecture.md)
- [Kiro surface support and validation limits](docs/kiro-v3-compatibility.md)
- [pstack workflow parity](docs/upstream-skill-parity.md) and [curated skills](docs/curated-skills.md)
- [Upstream update workflow](docs/upstream-control-loop.md)
- [Porting provenance](docs/provenance.md)
- [Repository validation evidence](https://github.com/njs14/pkstack/blob/main/reviews/release-status.md)

The package is licensed under Apache-2.0. See [LICENSE](LICENSE),
[NOTICE](NOTICE), and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
