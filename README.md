# PK-Stack (Poteto Kiro)

<p align="center">
  <img src="powers/pk-stack/assets/logo.png" alt="A scholarly potato ghost, the PK-Stack mascot" width="260">
</p>

PK-Stack is a Kiro Power for development work that should finish with
executable evidence. It keeps planning, tool use, model choice, and
orchestration in Kiro, then adds a small repository-local control surface for
feature contracts, bounded verification, and project state.

The current release candidate is **0.2.0**. The `version` field in
[`powers/pk-stack/plugin.json`](powers/pk-stack/plugin.json) is the release
metadata authority. The Python package and lockfile mirror it; a release tag
must be `v0.2.0` and point at the reviewed commit. See the [current release
status](reviews/release-status.md) for the gate record.

## What it provides

- Native Kiro Spec, Quick Spec, Bug Fix, and Plan workflows remain the planning
  source of truth.
- `/setup-pk-stack` installs a reviewed workspace profile, steering, hooks, and
  skills from the Power.
- `/verified-goal` runs a bounded implement, verify, diagnose, and repair loop
  in the current Kiro session.
- `projectctl` records feature contracts, verification attempts, and bounded
  evidence outside the prompt.
- The source-controlled Wiki keeps architecture and decisions close to the
  project. Optional canonical `okn` provides deeper knowledge retrieval.

`/verified-goal` is a PK-Stack skill. It is not Kiro's native `/goal`, and it
does not require a user-launched ACP process. Kiro CLI v3 and the Kiro IDE
agent panel are the primary surfaces. Crew is optional; the committed Web
workspace path is supported by design but has not been tested end to end.

## Quick start

1. Import [`powers/pk-stack/`](powers/pk-stack) through Kiro's Power manager.
   Review the package before enabling it.
2. Open the target repository in Kiro and run the Power-local setup skill:

   ```text
   /setup-pk-stack
   ```

3. Review the dry-run result. Then select the generated `pstack` agent in the
   IDE picker, or start a CLI v3 session with:

   ```sh
   kiro-cli chat --v3 --agent pstack
   ```

   In an existing CLI conversation, `/agent swap pstack` performs the same
   handoff. A fresh session may be needed for Kiro to discover new assets.
4. Check the installation through the canonical wrapper:

   ```sh
   .pstack/bin/projectctl doctor --output json
   .pstack/bin/projectctl feature validate --output json
   ```

For a source-checkout fallback, set `PK_STACK_POWER` to the checked-out
`powers/pk-stack` directory and run the same Power-local script explicitly:

```sh
: "${PK_STACK_POWER:?Set PK_STACK_POWER to the PK-Stack Power directory}"
python3 "$PK_STACK_POWER/skills/setup-pk-stack/scripts/setup_pstack.py" \
  --root "$PWD" --dry-run --output json
python3 "$PK_STACK_POWER/skills/setup-pk-stack/scripts/setup_pstack.py" \
  --root "$PWD" --output json
```

The cached controller is not setup authority. A managed refresh requires the
same Power-local source and an explicit `--update-managed` approval. See the
[usage guide](powers/pk-stack/docs/usage.md) for the full recovery path.

## The working model

PK-Stack separates three concerns:

| Interface | Responsibility |
| --- | --- |
| `.pstack/bin/projectctl` | **DO** — setup, diagnostics, feature operations, upstream checks, and goal state |
| `Wiki/features/*.md` | **PROVE** — user-visible behavior bound to an executable verifier |
| `Wiki/` and optional `okn` | **KNOW** — architecture, decisions, concepts, and operations |

For nontrivial work, let Kiro complete its native plan first. In CLI v3 use
`/spec new <name>` or resume with `/spec <name>`; in the IDE use **Build with
spec** or the workflow picker. Then return to `pstack` in the same conversation
and bind the plan to a feature contract:

```sh
.pstack/bin/projectctl goal bind-spec account-lookup \
  --feature account-lookup --output json
```

Start the bounded loop only after a concrete verifier exists:

```text
/verified-goal Implement account lookup and make account-lookup pass.
```

For a smaller change, create a contract directly:

```sh
.pstack/bin/projectctl feature generate account-lookup \
  --title "Account lookup" \
  --behavior "A caller can retrieve account status." \
  --expected-path "CLI -> gateway -> account service -> response" \
  --command "uv run pytest tests/test_account_lookup.py -q" \
  --ready --output json
```

`--ready` runs the command before writing a ready contract. The verifier
screen is a bounded hazard check, not an operating-system sandbox or proof
that arbitrary project code is relevant. Human review remains part of the
acceptance boundary.

## Repository layout

| Path | Purpose |
| --- | --- |
| `powers/pk-stack/` | Canonical installable Power, package, skills, templates, and docs |
| `.kiro/` | Generated workspace agents, hooks, skills, and steering |
| `.pstack/` | Generated wrapper, receipt, cached controller, and ignored runtime state |
| `Wiki/` | Feature contracts and source-controlled project knowledge |
| `maintenance/` | Pinned upstream identities and review ledger |
| `reviews/` | Current release status and historical evidence |
| `.github/` | Repository automation and policy; change settings separately |

The private [pk-stack-floci-lab](https://github.com/njs14/pk-stack-floci-lab)
repository contains the Floci document-export application and its live
campaigns. Floci consumes PK-Stack; it is not part of this Power or release
artifact.

## Test the Power

```sh
cd powers/pk-stack
uv lock --check
uv run --frozen ruff check src tests skills/setup-pk-stack/scripts/setup_pstack.py
uv run --frozen ruff format --check src tests skills/setup-pk-stack/scripts/setup_pstack.py
uv run --frozen ty check
uv run --frozen pytest -q
```

Repository-level guard and documentation commands are listed in
[CONTRIBUTING.md](CONTRIBUTING.md) and the [release status](reviews/release-status.md).

## Self-maintenance

GitHub Actions checks the pinned upstream sources on a schedule and processes
one drift source at a time. Its explicit control loop uses `projectctl upstream
check` as the sensor, a deterministic one-source controller, Kiro plus
`maintain-pk-stack` as the actuator, and the exact-SHA candidate gate as the
dampener. Durable steering lives in a short trusted-base memory file. The Kiro maintainer may update only reviewed
Markdown, source-parity records, and the matching curated bundle manifest. A
secretless finalizer reproves the source identity, regenerates managed files,
runs the deterministic gates, and opens or merges only its own exact candidate.

The pipeline uses `KIRO_API_KEY` for Kiro-hosted maintenance and review. It has
no Anthropic, OpenAI, xAI, or GitHub Copilot key. Executable vendored runtime
changes, workflow changes, and controller changes fail closed for a human
release review rather than receiving autonomous write authority.

The Power also ships a reviewed portable subset of
[HumanLayer skills](https://github.com/humanlayer/skills):
`build-iterated-agentic-loop`, `design-control-loop`,
`narrow-react-prop-types`, and `show-me`. It adds Matt Pocock's
[`writing-for-agents`](https://github.com/mattpocock/skills/tree/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76/skills/productivity/writing-for-agents)
method for `AGENTS.md`, Kiro Skills, steering, and pointer-linked references.
Runtime-specific registration and unsafe generic CI examples remain provenance-only.

## Documentation and community

- [Power README](powers/pk-stack/README.md)
- [Usage and recovery](powers/pk-stack/docs/usage.md)
- [Architecture and trust boundaries](powers/pk-stack/docs/architecture.md)
- [Interactive architecture artifact](powers/pk-stack/docs/artifacts/pk-stack-architecture.html)
- [Kiro surface compatibility](powers/pk-stack/docs/kiro-v3-compatibility.md)
- [Provenance and porting boundary](powers/pk-stack/docs/provenance.md)
- [Validation report](powers/pk-stack/docs/validation-report.md)
- [Wiki navigation](Wiki/index.md)
- [Contributing](CONTRIBUTING.md), [security](SECURITY.md), and [code of conduct](CODE_OF_CONDUCT.md)

PK-Stack is licensed under Apache-2.0. Third-party attribution is in
[`powers/pk-stack/THIRD_PARTY_NOTICES.md`](powers/pk-stack/THIRD_PARTY_NOTICES.md).
