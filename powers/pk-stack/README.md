# PK-Stack

**PK-Stack** expands to **Poteto Kiro**. It is a Kiro CLI v3-first Power for
development that must end in executable evidence. It keeps implementation and
repair work in the user's current interactive Kiro session and adds a small
repo-local control surface; it does not launch an external ACP host or the
`kiro-cli acp` entrypoint, recreate an agent runtime, or claim that native
`/goal` is available in V3.

The ownership rule is:

> Kiro owns execution. PK-Stack owns workflow semantics. `projectctl` owns
> project operability and executable evidence. OKF, when installed, owns broad
> project knowledge.

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
| `.pstack/bin/projectctl` | **DO**: setup, diagnostics, feature operations, and bounded goal state |
| `Wiki/features/*.md` | **PROVE**: user-visible behavior bound to an executable verifier |
| Other `Wiki/`/OKF material | **KNOW**: architecture, decisions, concepts, and operations |

## Quick start

Prerequisites are Kiro CLI with V3, `uv`, and Python 3.11 or newer. Import this
package directory as a Kiro Power, review it, then use an ordinary V3 chat to
install the repository-local assets. In the combined PK-Stack repository the
package directory is `powers/pk-stack/`; do not import its generated
`.pstack/projectctl/` acceptance-fixture cache:

```bash
cd /path/to/project
kiro-cli chat --v3
```

Run the Power's setup skill in that session:

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
chat. Before the next workflow message, switch the current V3 session:

```text
/agent swap pstack
```

The Poteto Kiro primary profile retains the compatibility agent ID `pstack`
and excludes installed Powers. For a later managed refresh, stay in this same
chat and temporarily return to the Power-enabled setup agent:

```text
/agent swap kiro_default
/setup-pstack
/agent swap pstack
```

Use the previously selected Power-enabled agent if its local name differs.
The cached `.pstack/bin/projectctl setup` command is not upgrade authority and
fails unless a reviewed `--power-root` is supplied explicitly.

If the newly created profile or slash skills are not discoverable yet, exit and
restart the same repository explicitly with:

```bash
kiro-cli chat --v3 --agent pstack
```

Both paths use normal Kiro V3; neither launches an external ACP host,
`kiro-cli acp`, classic/V2, or a nested Kiro process. Setup never changes the
user's global default agent.

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

## Documentation

- [Usage and recovery](docs/usage.md)
- [Architecture and trust boundaries](docs/architecture.md)
- [Kiro CLI v3 compatibility](docs/kiro-v3-compatibility.md)
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
