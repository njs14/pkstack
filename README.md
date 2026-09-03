# PK-Stack (Poteto Kiro)

<p align="center">
  <img src="powers/pk-stack/assets/logo.png" alt="A scholarly potato ghost, the PK-Stack mascot" width="260">
</p>

PK-Stack is a Kiro Power for development work that must finish with executable proof. It brings the useful workflow ideas from pstack into Kiro without replacing Kiro's agent runtime.

Kiro handles planning, tool use, model selection, and orchestration. PK-Stack supplies the working method. A repo-local `projectctl` records feature contracts, verification attempts, and evidence. OKF and `okn` provide the deeper project knowledge behind those contracts.

The primary surfaces are Kiro CLI v3 and the Kiro IDE agent panel. Kiro Crew can orchestrate a configured workspace. Kiro Web can consume committed workspace assets, but that path has not been tested end to end.

## What it adds

- Native Spec, Quick Spec, and Bug Fix planning stays in Kiro.
- `/setup-pstack` installs a reviewed set of workspace agents, skills, hooks, and steering files.
- `/verified-goal` runs a bounded implement, verify, diagnose, and repair loop in the current Kiro session.
- Feature contracts connect user-visible behavior to one exact verification command.
- `projectctl` stores the objective, contract digest, attempt budget, and result outside the prompt.
- OKF keeps architecture and decisions in source control; `okn` supplies the optional machine-readable knowledge interface.
- Permission profiles keep implementation, review, and verification roles distinct.

`/verified-goal` is a PK-Stack skill. It does not call or pretend to provide Kiro's native `/goal` command. Normal use stays inside `kiro-cli chat --v3` or the IDE agent panel. ACP is not the default entrypoint.

## Install

Clone this private repository and import [`powers/pk-stack/`](powers/pk-stack) from Kiro's Powers panel.

In a Kiro chat with Powers enabled, run:

```text
/setup-pstack
```

The setup skill previews managed changes before writing them. It will not overwrite conflicts or delete retired files. Review `pending_updates` and `stale_managed` before approving a managed refresh.

Setup creates a workspace agent named `pstack`. Select it from the IDE agent picker, or keep the same CLI conversation and run:

```text
/agent swap pstack
```

You can also start a later CLI session directly:

```sh
kiro-cli chat --v3 --agent pstack
```

The compatibility identifiers remain lowercase: the agent is `pstack`, the Python package is `pstack_kiro`, and local state lives under `.pstack/`. The product and Power are named PK-Stack.

## Use the workflow

Start nontrivial work with Kiro's planner. In CLI v3:

```text
/spec new account-lookup
```

Choose a standard Spec for unfamiliar or cross-boundary work. Choose Quick Spec for a bounded change whose shape is already clear. In the IDE, use the matching workflow from the agent panel.

When Kiro's plan is ready, return to the `pstack` agent in the same conversation. Bind the native plan to a feature contract:

```sh
.pstack/bin/projectctl goal bind-spec account-lookup \
  --feature account-lookup \
  --output json
```

Then run the goal skill:

```text
/verified-goal Implement the account lookup behavior described by the account-lookup spec.
```

The loop keeps one goal ID, one contract digest, and one attempt budget. A failed verification becomes evidence for the next repair. A pass ends the loop. Contract drift, an exhausted budget, or a genuine external dependency stops it with a recorded reason.

For smaller work, create a feature contract directly:

```sh
.pstack/bin/projectctl feature generate account-lookup \
  --title "Account lookup" \
  --behavior "A caller can retrieve account status." \
  --expected-path "CLI -> gateway -> account service -> response" \
  --command "uv run pytest tests/test_account_lookup.py -q" \
  --ready \
  --output json
```

`--ready` runs the verifier before publishing the contract.

## DO, PROVE, KNOW

PK-Stack separates three concerns that agents often blur together:

| Interface | Job |
| --- | --- |
| `.pstack/bin/projectctl` | **DO:** setup, diagnostics, goal state, feature operations, and upstream checks |
| `Wiki/features/*.md` | **PROVE:** user-visible behavior and its executable verifier |
| Other source-controlled OKF material, optionally indexed by `okn` | **KNOW:** architecture, decisions, concepts, and operations |

The feature map is the first context layer. The agent descends into broader OKF or `okn` knowledge only when the task needs it. Kiro's native `/knowledge` can index the same source-controlled material.

## Useful commands

```sh
.pstack/bin/projectctl doctor --output json
.pstack/bin/projectctl feature list --output json
.pstack/bin/projectctl feature validate --output json
.pstack/bin/projectctl goal status --output json
.pstack/bin/projectctl knowledge status --output json
```

See the [usage guide](powers/pk-stack/docs/usage.md) for setup recovery, goal commands, feature-map generation, and the full skill catalog.

## Repository layout

| Path | Purpose |
| --- | --- |
| `powers/pk-stack/` | Canonical installable Power and Python package |
| `.kiro/`, `.pstack/` | PK-Stack managing its own repository through the same installed interfaces |
| `Wiki/` | Self-maintenance feature contract and project knowledge |
| `.github/` | Scheduled upstream maintenance, candidate review, and Kiro runtime checks |
| `maintenance/` | Pinned upstream identities and review ledger |
| `reviews/` | Bounded release and compatibility evidence |

The Floci document-export application and its historical live campaigns live in the separate private [`njs14/pk-stack-floci-lab`](https://github.com/njs14/pk-stack-floci-lab) repository. The lab is a consumer of PK-Stack, not part of the Power or this repository's release artifact.

## Test the Power

```sh
cd powers/pk-stack
uv lock --check
uv run --frozen ruff check src tests skills/setup-pstack/scripts/setup_pstack.py
uv run --frozen ruff format --check src tests skills/setup-pstack/scripts/setup_pstack.py
uv run --frozen ty check
uv run --frozen pytest -q
```

Repository automation and trust-boundary tests use only the standard Python and Node runtimes:

```sh
python3 .github/scripts/test_pk_stack_maintenance_guard.py
python3 .github/scripts/test_kiro_runtime_canary.py
node --test .github/scripts/test_pk_stack_pr_policy.js
actionlint .github/workflows/*.yml
shellcheck .github/scripts/*.sh
```

## Self-maintenance

The scheduled workflow checks four pinned upstreams: Cursor pstack, `okf-skills`, the normative OKF specification, and the versioned `okn` CLI schema. A drift run handles one source at a time, produces a bounded candidate, reruns deterministic checks, and requires an exact-candidate Kiro review before merge.

GitHub Actions needs only `KIRO_API_KEY`. The pipeline has no Anthropic, OpenAI, xAI, or GitHub Copilot credential. The Kiro secret reaches only the bounded repair and review steps after the workflow verifies the pinned CLI binary and candidate identity.

The runtime canary tracks stable Kiro CLI behavior and records Nightly Kiro Crew metadata as a non-gating observation. Pin changes and workflow trust roots still require a reviewed repository change.

Read the [architecture](powers/pk-stack/docs/architecture.md), [Kiro compatibility matrix](powers/pk-stack/docs/kiro-v3-compatibility.md), [provenance](powers/pk-stack/docs/provenance.md), and [validation report](powers/pk-stack/docs/validation-report.md) for the detailed contracts and current limits.
