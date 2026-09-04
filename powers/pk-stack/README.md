# PK-Stack Power

<p align="center">
  <img src="assets/logo.png" alt="A scholarly potato ghost, the PK-Stack mascot" width="220">
</p>

**PK-Stack (Poteto Kiro)** is a Kiro-native Power for work that needs an
executable completion check. It supplies workflow instructions and a small
`projectctl` control surface; Kiro remains responsible for the agent runtime,
planning, model selection, tools, and orchestration.

Kiro CLI v3 and Kiro IDE 1.x are the primary surfaces. PK-Stack inherits the
model and effort already selected in Kiro; it does not hard-code Sol/max or
another provider-specific role. Kiro Crew is a compatible optional
orchestrator. Kiro Web can consume committed workspace assets, but that path is
supported by design and remains untested.

This package is version **0.2.0**. [`plugin.json`](plugin.json) is the release
metadata authority. `pyproject.toml`, `src/pstack_kiro/__init__.py`, and the
shipped lockfiles are mirrors and must equal that value. The compatibility
names `pstack-kiro`, `pstack_kiro`, `.pstack`, `projectctl`, and `pstack` are
intentional and remain stable.

## What is installed

The Power contains:

- the Power-local `/setup-pk-stack` bootstrap skill;
- workflow skills for architecture, investigation, OKF knowledge, review,
  verification, TDD, writing, and bounded principles;
- Kiro steering, custom-agent, and hook templates;
- the `pstack_kiro` package and `projectctl` command; and
- documentation and parity/provenance records.

`powers/pk-stack/` is the only source of Power-managed content. A successful
setup materializes selected files into a target project's `.kiro/` and caches a
controller under `.pstack/projectctl/`. The target's `.pstack/bin/projectctl`
wrapper is the stable project entrypoint. Generated files are an ownership
receipt and cache, not a second source tree.

## Quick start

Prerequisites: Kiro IDE or Kiro CLI v3, Python 3.11+, and `uv`.

1. Import this directory through Kiro's Power manager and review it.
2. In the target repository, invoke the Power-local skill:

   ```text
   /setup-pk-stack
   ```

   The skill previews managed changes before writing them. Review
   `pending_updates`, `stale_managed`, and `conflicts` before approving a
   refresh.
3. Select the generated `pstack` agent in the IDE, or launch a CLI v3 session:

   ```sh
   kiro-cli chat --v3 --agent pstack
   ```

   In an existing CLI conversation, `/agent swap pstack` performs the handoff.
4. Check the workspace:

   ```sh
   .pstack/bin/projectctl version --output json
   .pstack/bin/projectctl doctor --output json
   .pstack/bin/projectctl feature validate --output json
   ```

If Kiro cannot import a local Power, set `PK_STACK_POWER` to this checked-out
directory and use the explicit source fallback:

```sh
: "${PK_STACK_POWER:?Set PK_STACK_POWER to the PK-Stack Power directory}"
python3 "$PK_STACK_POWER/skills/setup-pk-stack/scripts/setup_pstack.py" \
  --root "$PWD" --dry-run --output json
python3 "$PK_STACK_POWER/skills/setup-pk-stack/scripts/setup_pstack.py" \
  --root "$PWD" --output json
```

The cached controller can operate the project, but it cannot identify its own
source as an upgrade authority. A refresh must use the Power-local script or a
reviewed `projectctl setup --power-root ...` invocation with explicit
`--update-managed` approval.

## Use native planning, then verify

For nontrivial work, let Kiro's native Spec, Quick Spec, Bug Fix, or Plan
workflow produce its requirements, design, and task artifacts. In CLI v3 use
`/spec new <name>` or `/spec <name>`; in the IDE use **Build with spec** or the
workflow picker. Return to `pstack` in the same conversation when the native
plan is ready.

Bind a native spec to a feature contract:

```sh
.pstack/bin/projectctl goal bind-spec account-lookup \
  --feature account-lookup --output json
```

Then run the current-session loop:

```text
/verified-goal Implement account lookup and make account-lookup pass.
```

For a small change, create a contract directly:

```sh
.pstack/bin/projectctl feature generate account-lookup \
  --title "Account lookup" \
  --behavior "A caller can retrieve account status." \
  --expected-path "CLI -> gateway -> account service -> response" \
  --command "uv run pytest tests/test_account_lookup.py -q" \
  --ready --output json
```

`--ready` proves the command before writing `draft: false`. A stored contract
is a predicate, not a permanent guarantee. The runner rejects common hazards
and placeholder commands without becoming an operating-system sandbox; review
the verifier and its project scope before approving it.

## Interfaces and boundaries

| Interface | Job |
| --- | --- |
| `.pstack/bin/projectctl` | **DO:** setup, diagnostics, feature/upstream operations, and goal state |
| `Wiki/features/*.md` | **PROVE:** user-visible behavior and its executable verifier |
| `Wiki/` plus optional canonical `okn` | **KNOW:** architecture, decisions, concepts, and operations |

Native Kiro planning remains authoritative. PK-Stack does not launch a nested
Kiro process, make ACP the default entrypoint, or claim that Kiro CLI v3
provides native `/goal`. Kiro Crew is an optional orchestrator. Kiro Web can
consume committed workspace assets, but its end-to-end path and IDE/CLI
approval behavior are untested.

The Floci document-export application and its live campaigns belong to the
separate private [pk-stack-floci-lab](https://github.com/njs14/pk-stack-floci-lab)
repository. Floci is a consumer of this Power, not part of this package.

## Documentation

- [Usage and recovery](docs/usage.md)
- [Architecture and trust boundaries](docs/architecture.md)
- [Upstream control loop](docs/upstream-control-loop.md)
- [Kiro surface compatibility](docs/kiro-v3-compatibility.md)
- [Upstream skill parity](docs/upstream-skill-parity.md)
- [OKF source and method provenance](docs/okf-skills-provenance.md),
  [spec provenance](docs/okf-spec-provenance.md), and [CLI contract provenance](docs/openknowledge-cli-contract-provenance.md)
- [Porting provenance](docs/provenance.md)
- [Validation report](docs/validation-report.md)
- [Review harness](reviews/README.md)

## Development

```sh
uv sync --all-groups
uv lock --check
uv run ruff check src tests skills/setup-pk-stack/scripts/setup_pstack.py
uv run ruff format --check src tests skills/setup-pk-stack/scripts/setup_pstack.py
uv run ty check
uv run pytest -q
```

The package is licensed under Apache-2.0. See [LICENSE](LICENSE),
[NOTICE](NOTICE), and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
