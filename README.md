# PK-Stack (Poteto Kiro)

<p align="center">
  <img src="powers/pk-stack/assets/logo.png" alt="A scholarly potato ghost, the PK-Stack mascot" width="260">
</p>

PK-Stack helps Kiro finish development work with a check you can run again.
Plan with Kiro, give the task an executable verifier, and use
`/verified-goal` to work through failures in the same conversation.

The Power ports [Poteto's pstack workflows](powers/pk-stack/docs/upstream-skill-parity.md)
to Kiro and adds a repository-local `projectctl` command. Feature contracts
live in `Wiki/features/`; broader architecture and decisions live alongside
them in the Wiki, with optional `okn` retrieval.

## Where it works

| Surface | Support and evidence |
| --- | --- |
| Kiro CLI v3 | Primary runtime; exercised in real terminal sessions |
| Kiro IDE 1.x agent panel | Primary target; profiles and assets validated, full UI walkthrough still required |
| Kiro Crew | Optional orchestrator over the installed workspace assets |
| Kiro Web | Supported through committed workspace assets; untested end to end |

Kiro owns Specs, Quick Specs, tools, permissions, subagents, and model choice.
PK-Stack inherits your selected model and effort. `/verified-goal` is a
PK-Stack skill, not a native Kiro `/goal` command. Normal use needs no ACP host.
See the [compatibility guide](powers/pk-stack/docs/kiro-v3-compatibility.md)
for the tested versions and surface-specific limits.

## Install

You need Kiro, Python 3.11 or newer, and [uv](https://docs.astral.sh/uv/)
on your path. GitHub access to this repository is required while it is private.

Clone the source and keep its Power path for setup and later refreshes:

```sh
git clone https://github.com/njs14/pk-stack.git
export PK_STACK_POWER="$PWD/pk-stack/powers/pk-stack"
```

In Kiro IDE, open **Powers → Add Custom Power → Import power from a folder**
and select `powers/pk-stack` from that clone. Review the Power before installing.
Kiro CLI v3 can then use the installed Power.
([Kiro installation instructions](https://kiro.dev/docs/powers/installation/))

Open your target project in Kiro and run:

```text
/setup-pk-stack
```

Review the setup preview before allowing writes. Then select the workspace
`pk-stack` agent in the IDE, or use `/agent swap pk-stack` in CLI v3.
If the new skills are not discovered yet, start one fresh session:

```sh
kiro-cli chat --v3 --agent pk-stack
```

For terminal-only setup, run the same Power-local script from your target project:

```sh
python3 "$PK_STACK_POWER/skills/setup-pk-stack/scripts/setup_pk_stack.py" \
  --root "$PWD" --dry-run --output json
python3 "$PK_STACK_POWER/skills/setup-pk-stack/scripts/setup_pk_stack.py" \
  --root "$PWD" --output json
.pk-stack/bin/projectctl doctor --output json
```

Setup preserves conflicting user files and reports their paths. It does not
change global Kiro settings or install optional knowledge tools.

## Try one failing task

The included account-ID example starts broken. Use a disposable copy so the
fixture in the Power stays unchanged. These commands use only Python's standard
library for the verifier:

```sh
PK_STACK_DEMO=$(mktemp -d "${TMPDIR:-/tmp}/pk-stack-demo.XXXXXX")
cp -R "$PK_STACK_POWER/examples/verified-goal-demo/." "$PK_STACK_DEMO/"
cd "$PK_STACK_DEMO"
git init -q
python3 "$PK_STACK_POWER/skills/setup-pk-stack/scripts/setup_pk_stack.py" \
  --root "$PWD" --dry-run --output json
python3 "$PK_STACK_POWER/skills/setup-pk-stack/scripts/setup_pk_stack.py" \
  --root "$PWD" --output json
.pk-stack/bin/projectctl doctor --output json
.pk-stack/bin/projectctl goal start "Repair account ID normalization" \
  --command "python3 -m unittest discover -s tests -v" \
  --max-attempts 4 --output json
.pk-stack/bin/projectctl goal verify --output json
```

The last command should exit **1**, report failed tests, and leave the goal
`active`. That is the starting evidence. Do not fix the tests to make them pass.

Start Kiro in that directory:

```sh
kiro-cli chat --v3 --agent pk-stack
```

Then ask:

```text
/verified-goal Repair account ID normalization using the existing goal. Keep the tests unchanged. Remove spaces and hyphens, accept exactly twelve decimal digits, and raise ValueError otherwise. Rerun the stored verifier until it passes or the attempt budget is exhausted.
```

Kiro should edit `account.py` and rerun the stored command in this conversation.
Check the result yourself:

```sh
.pk-stack/bin/projectctl goal status --output json
python3 -m unittest discover -s tests -v
```

Success means stored status `passed`, a failing attempt followed by a passing
attempt, and all four tests passing. An `exhausted` goal is unfinished; inspect
the failure before explicitly adding attempts. The runner screens common
hazards but is not an OS sandbox. Review verifiers before approving execution.

For larger work, start with Kiro's native `/spec` or Quick Spec. Bind its
artifacts to a command, record the failure, and repair it before publishing a
reusable feature contract. The [usage guide](powers/pk-stack/docs/usage.md)
covers that sequence and the current schema-2 feature format.

## Pick a workflow

| Task | Start here |
| --- | --- |
| Adopt PK-Stack or refresh installed files | `/setup-pk-stack` |
| Plan a feature or bug fix | Kiro's native Spec, Quick Spec, or Bug Fix workflow |
| Implement against a concrete check | `/verified-goal` |
| Map and prove the project's user-facing features | `/create-verification-skill` |
| Update an existing verification workflow | `/maintain-verification-skill` |
| Read or maintain architecture and decisions | `/okf`, then optional canonical `okn` |
| Explain architecture visually | `/archify` or `/show-me` |
| Write concise agent instructions | `/writing-for-agents` |
| Apply the broader Poteto workflow | `/poteto-mode` |

The [skill catalog and provenance](powers/pk-stack/docs/upstream-skill-parity.md)
describe the pstack ports. [Curated additions](powers/pk-stack/docs/curated-skills.md)
cover HumanLayer, Archify, and writing-for-agents.

## Installed files and updates

Setup installs skills, steering, hooks, and agents in `.kiro/`, and the
controller, lockfile, and ownership receipt in `.pk-stack/`. Goal state is
local and ignored by Git. Keep your feature contracts and Wiki under version
control. The controller does not retain a second copy of the installed skills.

Use the reviewed Power source to preview a refresh:

```sh
python3 "$PK_STACK_POWER/skills/setup-pk-stack/scripts/setup_pk_stack.py" \
  --root "$PWD" --dry-run --update-managed --output json
```

After reviewing the paths, repeat without `--dry-run`. User edits are never
overwritten. Retired managed files require explicit removal; see
[refresh and clean reinstall](powers/pk-stack/docs/usage.md#refresh-managed-files).
Pre-0.3 installations and schema-1 feature files have no automatic migration path.

This repository checks upstream sources on a GitHub Actions schedule. Kiro
proposes one content update at a time; deterministic checks and independent
review gate its merge. Runtime or workflow changes still require a maintainer.
All model calls in that pipeline use Kiro, with no separate provider API keys.
See the [updater guide](powers/pk-stack/docs/upstream-control-loop.md).

## Further reading

- [Usage, feature authoring, and recovery](powers/pk-stack/docs/usage.md)
- [Architecture and trust boundaries](powers/pk-stack/docs/architecture.md)
- [Interactive architecture diagram](powers/pk-stack/docs/artifacts/pk-stack-architecture.html)
- [Validation evidence](reviews/release-status.md)
- [Contributing and test commands](CONTRIBUTING.md)
- [Security](SECURITY.md) and [code of conduct](CODE_OF_CONDUCT.md)

The [Floci test lab](https://github.com/njs14/pk-stack-floci-lab) is a separate
private repository. It is not included in this Power.

PK-Stack is licensed under Apache-2.0.
[Third-party notices](powers/pk-stack/THIRD_PARTY_NOTICES.md) preserve upstream attribution.
