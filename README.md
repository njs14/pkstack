# PKStack

<p align="center">
  <img src="powers/pkstack/assets/banner.png" alt="PKStack: From plan to proof. A scholarly potato ghost with an OKF knowledge tree in the background." width="600">
</p>

Poteto’s pstack workflows, adapted for Kiro.

Start with `/pkstack`. It brings Poteto's planning, implementation, and review
checkpoints into your Kiro conversation. Kiro handles native Specs, Quick Specs,
tools, and subagents; PKStack adds workflows and a local `projectctl` command
that records whether your verifier passed.

Feature contracts live in `Wiki/features/`. The wider Wiki holds architecture
and decisions in OKF, with optional canonical `okn` validation and retrieval.
Your selected Kiro model and effort carry through unchanged.

The current source targets 0.3.0, which is **not released**. See the
[release status](reviews/release-status.md) for validation results and updater
status. Installation and interactive use do not depend on that pipeline.

## Install

You need Kiro, Python 3.11 or newer, and [uv](https://docs.astral.sh/uv/)
on your path. GitHub access to this repository is required while it is private.

Clone the source and keep its Power path for setup and later refreshes:

```sh
git clone https://github.com/njs14/pkstack.git
export PKSTACK_POWER="$PWD/pkstack/powers/pkstack"
```

In Kiro IDE, open **Powers → Add Custom Power → Import power from a folder**
and select `powers/pkstack` from that clone. Review the Power before installing.
The installed Power is also available to Kiro CLI v3.
([Kiro installation instructions](https://kiro.dev/docs/powers/installation/))

Open your target project in Kiro and run:

```text
/pkstack-setup
```

Review the setup preview before allowing writes. Then select the workspace
`pkstack` agent in the IDE, or use `/agent swap pkstack` in CLI v3.
If the new skills are not discovered yet, start one fresh session:

```sh
kiro-cli chat --v3 --agent pkstack
```

For terminal-only setup, run the same Power-local script from your target project:

```sh
python3 "$PKSTACK_POWER/skills/pkstack-setup/scripts/setup_pkstack.py" \
  --root "$PWD" --dry-run --output json
python3 "$PKSTACK_POWER/skills/pkstack-setup/scripts/setup_pkstack.py" \
  --root "$PWD" --output json
.pkstack/bin/projectctl doctor --output json
```

Setup installs skills, steering, hooks, and agents in `.kiro/`, plus the
controller and ownership receipt in `.pkstack/`. It preserves conflicting
user files, leaves global Kiro settings alone, and does not install optional
knowledge tools. Old managed installations require a
[reviewed clean reinstall](powers/pkstack/docs/usage.md#refresh-managed-files);
setup does not migrate or delete them.

## Start with `/pkstack`

Use `/pkstack <task>` for the full workflow. It chooses the relevant Poteto
playbook, keeps its review checkpoints, and hands planning to Kiro's native
Spec or Quick Spec when appropriate. You can also invoke a focused workflow:

| Command | Use it to |
| --- | --- |
| `/pkstack` | Plan, implement, verify, and prepare work for review |
| `/pkstack-setup` | Preview setup or refresh files from the reviewed Power |
| `/pkstack-maintain` | Review upstream changes to this Power |
| `/pkstack-verified-goal` | Repair a task until its stored verifier passes or its budget ends |
| `/pkstack-model-council` | Compare independent reviews and resolve their findings |
| `/pkstack-principles` | Apply Poteto's engineering principles to a concrete decision |

These are PKStack's six named entry points. Imported skills keep their names,
including `/create-verification-skill`, `/archify`, `/show-me`,
`/writing-for-agents`, and individual `/principle-*` skills. `/okf` is the
explicit knowledge-integration exception. See the
[pstack mapping](powers/pkstack/docs/upstream-skill-parity.md) and
[curated catalog](powers/pkstack/docs/curated-skills.md) for their origins.

`/pkstack-verified-goal` is a PKStack skill, not Kiro's native `/goal`.
Its repair loop stays in the current conversation; normal use needs no ACP host.

## Try one failing task

The included account-ID example starts broken. Use a disposable copy so the
fixture in the Power stays unchanged. These commands use only Python's standard
library for the verifier:

```sh
PKSTACK_DEMO=$(mktemp -d "${TMPDIR:-/tmp}/pkstack-demo.XXXXXX")
cp -R "$PKSTACK_POWER/examples/verified-goal-demo/." "$PKSTACK_DEMO/"
cd "$PKSTACK_DEMO"
git init -q
python3 "$PKSTACK_POWER/skills/pkstack-setup/scripts/setup_pkstack.py" \
  --root "$PWD" --dry-run --output json
python3 "$PKSTACK_POWER/skills/pkstack-setup/scripts/setup_pkstack.py" \
  --root "$PWD" --output json
.pkstack/bin/projectctl doctor --output json
.pkstack/bin/projectctl goal start "Repair account ID normalization" \
  --command "python3 -m unittest discover -s tests -v" \
  --max-attempts 4 --output json
.pkstack/bin/projectctl goal verify --output json
```

The last command should exit **1**, report failed tests, and leave the goal
`active`. That is the starting evidence. Do not fix the tests to make them pass.

Start Kiro in that directory:

```sh
kiro-cli chat --v3 --agent pkstack
```

Then ask:

```text
/pkstack-verified-goal Repair account ID normalization using the existing goal. Keep the tests unchanged. Remove spaces and hyphens, accept exactly twelve decimal digits, and raise ValueError otherwise. Rerun the stored verifier until it passes or the attempt budget is exhausted.
```

Kiro should edit `account.py` and rerun the stored command in this conversation.
Check the result yourself:

```sh
.pkstack/bin/projectctl goal status --output json
python3 -m unittest discover -s tests -v
```

Success means stored status `passed`, a failing attempt followed by a passing
attempt, and all four tests passing. An `exhausted` goal is unfinished; inspect
the failure before explicitly adding attempts. The runner screens common
hazards but is not an OS sandbox. Review verifiers before approving execution.

For larger work, start with Kiro's native `/spec` or Quick Spec. Bind its
artifacts to a command, record the failure, and repair it before publishing a
reusable feature contract. The [usage guide](powers/pkstack/docs/usage.md)
covers that sequence and the current schema-2 feature format.

## Tested surfaces and limits

| Surface | Recorded evidence |
| --- | --- |
| Kiro CLI v3, CLI 2.21.0 | Real Luna / Low fail → repair → pass sessions, including a native Quick Spec handoff |
| Kiro IDE 1.0.437 agent panel | Native Power import, setup, generated-agent selection, and separately approved controller checks passed; doctor reported 81 passed checks |
| Kiro Crew Nightly | Optional orchestrator; bounded version/help/doctor smoke only |
| Kiro Web | Supported through committed workspace assets by design; untested end to end |

The IDE goal-repair and Spec/Quick Spec execution paths have not received an
end-to-end campaign. The table records prior runtime evidence, not proof of
every later change. The [compatibility guide](powers/pkstack/docs/kiro-v3-compatibility.md)
and [validation reports](reviews/release-status.md) identify exact scope and commits.

Keep the feature contracts and Wiki under version control; goal state stays
local and ignored. The [usage guide](powers/pkstack/docs/usage.md#refresh-managed-files)
covers managed refreshes, clean reinstalls, and recovery. The
[updater guide](powers/pkstack/docs/upstream-control-loop.md) explains the
GitHub Actions schedule, automatic-update limits, and Kiro-only model boundary.

## Further reading

- [Usage, feature authoring, and recovery](powers/pkstack/docs/usage.md)
- [Architecture and trust boundaries](powers/pkstack/docs/architecture.md)
- [Interactive architecture diagram](powers/pkstack/docs/artifacts/pkstack-architecture.html)
- [Porting provenance](powers/pkstack/docs/provenance.md)
- [Validation evidence](reviews/release-status.md)
- [Contributing and test commands](CONTRIBUTING.md)
- [Security](SECURITY.md) and [code of conduct](CODE_OF_CONDUCT.md)

The [Floci test lab](https://github.com/njs14/pk-stack-floci-lab) is a separate
private repository. It is not included in this Power.

PKStack is licensed under Apache-2.0.
[Third-party notices](powers/pkstack/THIRD_PARTY_NOTICES.md) preserve upstream attribution.
