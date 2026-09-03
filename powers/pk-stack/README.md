# PK-Stack

<p align="center">
  <img src="assets/logo.png" alt="PK-Stack: the Kiro ghost reimagined as a scholarly golden potato" width="220">
</p>

**PK-Stack** expands to **Poteto Kiro**. It is a Kiro-native Power for
development that must end in executable evidence. Kiro CLI v3 and Kiro IDE
1.x chat/Agent Focus are its first-class primary surfaces. Kiro Crew is a
compatible optional orchestrator, and Kiro Web is supported through committed
workspace assets by design but remains untested. PK-Stack keeps implementation
and repair work in the user's current Kiro agent session and adds a small
repo-local control surface; it does not launch an external ACP host or the
`kiro-cli acp` entrypoint, recreate an agent runtime, or claim that native
`/goal` is available in CLI v3.

The ownership rule is:

> Kiro owns execution and native planning. PK-Stack owns workflow semantics.
> `projectctl` owns project operability and executable evidence. Source-controlled
> OKF plus canonical `okn` owns broad project knowledge.

## Names and compatibility

PK-Stack is the human-facing Power name. This final pre-release rename changes
the Power manifest identifier from the earlier candidate's `pstack-kiro` to
`pk-stack`; the implementation keeps its existing runtime, package, path, and
command interfaces stable so bootstrapped projects do not need a cosmetic
migration:

| Role | Name |
| --- | --- |
| Display name | **PK-Stack** |
| Expansion | **Poteto Kiro** |
| Power manifest identifier | `pk-stack` |
| Python distribution and receipt manager | `pstack-kiro` |
| Combined repository | `pk-stack` |
| Python package | `pstack_kiro` |
| Primary agent and delegated-agent prefix | `pstack` |
| State/cache directory | `.pstack` |
| Controller | `projectctl` |
| Setup skill | `/setup-pstack` |
| Bootstrap inventory token | `.gitignore:pstack-runtime-block` |

Those compatibility identifiers are intentional API and path names, not stale
display branding.

If an earlier candidate was already imported as a Power, Kiro may retain it as
a separate `pstack-kiro` entry because the manifest identifier changed. Remove
that old candidate through Kiro's Power management UI before importing
`pk-stack`; this does not remove or rewrite project files.

That produces three deliberately separate interfaces:

| Interface | Purpose |
| --- | --- |
| `.pstack/bin/projectctl` | **DO**: setup, diagnostics, feature and upstream operations, and bounded goal state |
| `Wiki/features/*.md` | **PROVE**: user-visible behavior bound to an executable verifier |
| Other `Wiki/`/OKF material | **KNOW**: architecture, decisions, concepts, and operations |

## Quick start on the primary surfaces

Prerequisites are Kiro IDE 1.x or Kiro CLI with v3, `uv`, and Python 3.11 or
newer. Import this package directory as a Kiro Power and review it. In the
combined PK-Stack repository the package directory is `powers/pk-stack/`; do
not import its generated `.pstack/projectctl/` acceptance-fixture cache.

In Kiro IDE, open the repository and use the chat panel or Agent Focus. In
Kiro CLI, start an ordinary v3 chat:

```bash
cd /path/to/project
kiro-cli chat --v3
```

PK-Stack inherits the model and effort already selected in Kiro. It does not
hard-code Sol/max or another Cursor-era role. See [models, effort, and
verification methodology](docs/kiro-v3-compatibility.md#models-effort-and-verification-methodology)
before deliberately changing that session choice.

Run the Power's setup skill in that Kiro agent session:

```text
/setup-pstack
```

The skill resolves its own `scripts/setup_pstack.py`, previews every managed
change, and then bootstraps the workspace. A managed upgrade is never applied
implicitly: `pending_updates` must be reviewed before the skill may rerun with
`--update-managed`. Conflicts and retired `stale_managed` paths block all
writes and are never overwritten or pruned. After setup, the workflow always
uses the locked repo-local entrypoint:

```bash
.pstack/bin/projectctl doctor --output json
.pstack/bin/projectctl feature validate --output json
```

The generated permission profile cannot attach retroactively to the setup
chat. Before the next workflow message, use the IDE agent picker to choose the
workspace **pstack** agent, or in CLI v3 stay in the same chat and run:

```text
/agent swap pstack
```

The Poteto Kiro primary profile retains the compatibility agent ID `pstack`
and excludes installed Powers. For a later managed refresh, stay in this same
chat and temporarily return to the Power-enabled setup agent. Use the IDE agent
picker, or in CLI v3 run:

```text
/agent swap kiro_default
/setup-pstack
/agent swap pstack
```

Use the previously selected Power-enabled agent if its local name differs.
The cached `.pstack/bin/projectctl setup` command is not upgrade authority and
fails unless a reviewed `--power-root` is supplied explicitly.

For a nontrivial feature or bug, let Kiro create the plan before PK-Stack drives implementation.
In CLI v3, run `/spec new <name>` and choose Feature, Quick Spec, or Bug, or resume with `/spec
<name>`. In the IDE, use **Build with spec** or the Spec, Quick Spec, or Bug Fix workflow in the
agent picker. Use standard Spec for unfamiliar, cross-boundary, high-risk, or requirements-sensitive
work and Quick Spec for a bounded, well-understood change. Kiro owns the requirements or bug
analysis, design, tasks, dependency waves, and native parallel execution.

After those artifacts are ready, reselect `pstack` in the same IDE/CLI conversation. Kiro does not
document a supported Agent Skill or custom-agent tool for changing the active workflow, so this is
an explicit same-conversation handoff. PK-Stack then applies its upstream-derived skills, creates or maintains the narrow feature
contract, and binds the native package to it:

```bash
.pstack/bin/projectctl goal bind-spec account-lookup \
  --feature account-lookup \
  --output json
```

The bridge retains both native-spec and feature provenance; it does not copy the plan, create a
second task graph, or treat checked tasks as executable proof. Starting the goal snapshots the
native intent, design, and verification bridge; verification rejects drift before consuming an
attempt and rechecks after the command. `tasks.md` remains mutable so Kiro can own task progress.
Start with the feature record for context and use `.pstack/bin/projectctl knowledge search` only
for deeper architecture, decisions, concepts, or operations. Use `/okf` to produce, maintain, or
consume that source-controlled knowledge through the same bounded interfaces.

If the newly created profile or slash skills are not discoverable yet, open
one fresh pre-goal IDE chat/Agent Focus session and choose the workspace
**pstack** agent. In CLI v3, exit normally and restart the same repository
explicitly with:

```bash
kiro-cli chat --v3 --agent pstack
```

Both primary paths use Kiro's native agent harness; neither launches an
external ACP host, `kiro-cli acp`, classic/V2, or a nested Kiro process. Setup
never changes the user's global default agent. Once `/verified-goal` is loaded,
the whole loop remains in that current Kiro agent session.

Create a ready feature contract only when its verifier can prove the behavior:

```bash
.pstack/bin/projectctl feature generate account-lookup \
  --title "Account lookup" \
  --behavior "A caller can retrieve account status." \
  --expected-path "CLI -> gateway -> account service -> response" \
  --command "uv run pytest tests/test_account_lookup.py -q" \
  --ready \
  --output json
```

`--ready` runs the command before writing the contract. A failed proof leaves
the target absent or unchanged. Verifiers are executed without a shell and pass
a deliberately fail-closed obvious-hazard and obvious-placeholder screen. Shell
interpreters and ambiguous interpreter/wrapper startup options are unsupported;
use a direct project executable, a supported explicit interpreter target, or
`uv run <command>`. The screen is not a sandbox and cannot establish that an
arbitrary script is relevant. After
selecting the `pstack` agent, its shipped permissions keep every invocation of
the canonical `.pstack/bin/projectctl` entrypoint at `ask`.

Run a bounded repair loop without leaving the current chat:

```text
/verified-goal Repair suspended-account lookup and make account-lookup pass.
```

The skill reports completion only after the stored verifier reaches `passed`.
Native subagents can help with bounded diagnosis, but a reviewer opinion is not
completion evidence.

## Workflow catalog

The Power contains 49 source skill directories. Setup remains Power-local; the
other 48 are installed into `.kiro/skills`, while the controller cache retains
all 49. They cover architecture, investigation and explanation, verification
lifecycle, TDD, technical writing, TypeScript, cleanup, teaching, context
recovery, advisory review, and individually discoverable engineering
principles. See the [complete upstream skill parity
matrix](docs/upstream-skill-parity.md) for every upstream name, Kiro-native
route, and the one explicit safety exclusion.

Kiro discovers skill metadata first and loads a full body only on activation.
The current Kiro documentation gives no per-project skill-count cap; this is not
a claim that the catalog is unlimited.

Two portable upstream behaviors are also pervasive. An always-included prose
steering file carries the concise `unslop` core, and native `fileMatch` steering
loads TypeScript discipline for `**/*.ts` and `**/*.tsx`. The full skills remain
available on demand for deeper review workflows.

## Crew and Web

Kiro Crew may open the repository and consume the generated `.kiro` agents,
skills, and steering. Crew drives Kiro CLI over ACP internally; that is an
optional Kiro product integration, not PK-Stack's default entrypoint and not a
reason to launch `kiro-cli acp` yourself.

For Kiro Web, bootstrap and review PK-Stack locally, then commit the generated
`.kiro` and `.pstack` assets before opening the repository in Web. Invoke
`/verified-goal` from Web's primary session agent. Project custom agents are
delegation-only on Web, and the IDE/CLI permission profile is not available
there. Do not upload this complete custom Power as a Configuration Sync
substitute: custom cloud Powers are text-only and capped at 50 files, while
PK-Stack exceeds that shape. This Web route is supported by design and has not
been exercised end to end.

See the [Kiro surface support and evidence
matrix](docs/kiro-v3-compatibility.md) for the exact tested/untested boundary
and the September 1-2, 2026 Kiro change inventory.

## Documentation

- [Usage and recovery](docs/usage.md)
- [Architecture and trust boundaries](docs/architecture.md)
- [Kiro surface compatibility](docs/kiro-v3-compatibility.md)
- [Upstream skill parity catalog](docs/upstream-skill-parity.md)
- [OKF-skills methodology inventory](docs/okf-skills-parity.md)
- [Authoritative OKF source inventory](docs/okf-spec-source-parity.md)
- [Provenance and porting boundary](docs/provenance.md)
- [Validation report](docs/validation-report.md)

## Development

```bash
uv sync --all-groups
uv run ruff check src tests
uv run ty check
uv run pytest -q
```

The project is licensed under Apache-2.0. See [LICENSE](LICENSE) and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
