# Usage

PKStack keeps implementation and repair work in the current Kiro session.

This guide covers the current PKStack path: a Power-local bootstrap,
the generated `pkstack` Kiro agent, a feature contract, and a verifier run in
the current Kiro session. Start with the [repository README](../../../README.md) if you
are deciding whether to install it.

## The short version

```text
import and review the Power
        |
        v
/pkstack-setup  ->  review the dry run and bootstrap
        |
        v
select pkstack  ->  use the IDE picker or /agent swap pkstack
        |
        v
/pkstack <task>  ->  choose the Poteto workflow and its checkpoints
        |
        v
native Spec / Quick Spec / Bug Fix  ->  Kiro owns the plan
        |
        v
feature contract + verifier  ->  projectctl owns executable proof
        |
        v
/pkstack-verified-goal <objective>  ->  current-session implement / verify / repair
```

Kiro CLI v3 and the Kiro IDE agent panel are the primary surfaces. Kiro Crew is
optional. Kiro Web can consume committed workspace assets, but its end-to-end
path has not been tested. The selected IDE and CLI profiles have recorded
command-approval checks; that does not prove every permission rule. PKStack does not launch
an external ACP host, invoke `kiro-cli acp`, or claim that CLI v3 provides
Kiro's native `/goal` command.

## Prerequisites

- Kiro IDE or Kiro CLI with v3 support;
- Python 3.11 or newer;
- [`uv`](https://docs.astral.sh/uv/) on `PATH`; and
- a project directory you are allowed to modify, with a repeatable command
  that can check the behavior you are changing.

Check tools without changing the project:

```sh
kiro-cli --version
kiro-cli chat --v3 --help
uv --version
python3 --version
```

PKStack inherits the model and effort selected in Kiro. It does not store a
model choice in `projectctl` or require a particular provider for interactive
work.

The historical acceptance campaign used Sol at maximum effort. That is
evidence, not the interactive default; select the desired normal effort
afterwards because Kiro persists the choice. Cheap, fast models are usually a
better fit for repeatable mechanical smoke tests.

## Choose the Power source

The Power-local setup script is the only source and upgrade authority. When
using a source checkout, set one environment variable to the checkout's
`powers/pkstack` directory:

```sh
: "${PKSTACK_POWER:?Set PKSTACK_POWER to the checked-out PKStack Power directory}"
test -f "$PKSTACK_POWER/plugin.json"
test -f "$PKSTACK_POWER/skills/pkstack-setup/scripts/setup_pkstack.py"
```

Do not infer this value from a target project's `.pkstack/` cache. An installed
Power may be imported through Kiro's Power manager instead; the same
Power-local rule applies.

## Import and bootstrap

Import [`powers/pkstack/`](../) through Kiro's Power manager and review the
package. In the target repository, use the current Kiro chat or Agent Focus
session and invoke:

```text
/pkstack-setup
```

The skill first previews managed changes. Review `pending_updates`,
`stale_managed`, and `conflicts`; a non-empty list blocks writes. The direct
source-checkout equivalent is useful for troubleshooting and deterministic
tests:

```sh
python3 "$PKSTACK_POWER/skills/pkstack-setup/scripts/setup_pkstack.py" \
  --root "$PWD" --dry-run --output json
python3 "$PKSTACK_POWER/skills/pkstack-setup/scripts/setup_pkstack.py" \
  --root "$PWD" --output json
```

After a successful setup, use only the generated wrapper for project
operations:

```sh
.pkstack/bin/projectctl version --output json
.pkstack/bin/projectctl doctor --output json
.pkstack/bin/projectctl feature validate --output json
```

Setup may create a root `projectctl` convenience wrapper when that name is
unowned. It is not the trusted entrypoint. The canonical wrapper uses the
shipped locked runtime under `.pkstack/projectctl/`; its environment does not
become the verifier's environment.

### Refresh managed files

Return to the Power-enabled Kiro agent before refreshing. In CLI v3:

```text
/agent swap kiro_default
/pkstack-setup
/agent swap pkstack
```

Use the local setup-agent name if it differs. If the dry run reports
`pending_updates`, inspect the exact paths and preview the explicit upgrade:

```sh
python3 "$PKSTACK_POWER/skills/pkstack-setup/scripts/setup_pkstack.py" \
  --root "$PWD" --dry-run --update-managed --output json
python3 "$PKSTACK_POWER/skills/pkstack-setup/scripts/setup_pkstack.py" \
  --root "$PWD" --update-managed --output json
```

`--update-managed` replaces only a path that still matches its prior receipt
hash. It never overwrites a user edit. `stale_managed` paths are not deleted
automatically; preserve or remove each exact path by a separate project
decision. The cached controller's setup command fails unless an explicit,
reviewed `--power-root` is supplied.

The PKStack rename is a clean-install change. Setup blocks legacy managed
installations before writes; it adds no aliases and performs no automatic
migration. An earlier installation may use a `.pk-stack/bootstrap.json`
receipt and `pk-stack`-named agent files. Those names identify old files to
review, not supported entry points.

Before reinstalling, preserve project-owned `Wiki/` content, native
`.kiro/specs/`, user-authored settings, and any evidence you want to retain.
Inspect the old receipt and compare its hashes with the files on disk. With
explicit approval, remove only the unchanged managed paths and the old receipt
after that comparison. Review retired cache paths individually; never delete
an entire `.kiro/` or Wiki directory. User-modified managed files need a
deliberate keep-or-replace decision first. Then run fresh setup from the
reviewed Power. Old goals and schema-1 feature records are not imported.

### Attach the generated agent

The bootstrap conversation may not inherit the new profile. In the IDE choose
the workspace `pkstack` agent. In CLI v3 use either:

```text
/agent swap pkstack
```

or, when Kiro has not discovered the new assets yet:

```sh
kiro-cli chat --v3 --agent pkstack
```

Keep the handoff in the same conversation when possible. The primary profile
asks before ordinary writes and canonical controller commands. Delegated
architect, reviewer, and verifier profiles omit `write` and `shell`; they
inspect and report to the primary session. These Kiro permissions complement
the controller's checks but are not an operating-system sandbox.

## Plan and bind work

For nontrivial work, use Kiro's native planner before the PKStack loop:

- CLI v3: `/spec new <name>`, then `/spec <name>` to resume;
- IDE: **Build with spec** or the workflow picker; and
- choose standard Spec for unfamiliar or high-risk work, or Quick Spec for a
  bounded change whose shape is already clear.

Kiro owns requirements or bug analysis, design, tasks, dependency waves, and
native task execution. When those artifacts are ready, return to `pkstack` and
bind the native plan to an executable verifier. For a new, still-failing feature:

```sh
.pkstack/bin/projectctl goal bind-spec account-lookup \
  --command "python3 -m unittest discover -s tests -v" --output json
.pkstack/bin/projectctl goal start "Repair account lookup" \
  --spec account-lookup --max-attempts 4 --output json
.pkstack/bin/projectctl goal verify --output json
```

Record that initial failure before editing, repair in the same Kiro session,
and run `goal verify` again. Publish a reusable feature only when useful and
after its command passes. For an already published feature, bind with
`--feature account-lookup` instead of `--command`. The bridge records native
spec provenance without copying a task graph or treating a checked task as proof.

## Create and prove feature contracts

Feature contracts live in `Wiki/features/`. A schema-2 contract describes the
user behavior, expected path, entrypoints, observable proof, gotchas, and
evidence/cleanup boundaries. Slugs use lowercase letters, digits, and single
hyphens.

Create a draft without running its command:

```sh
.pkstack/bin/projectctl feature generate account-lookup \
  --title "Account lookup" \
  --behavior "A caller can retrieve account status." \
  --expected-path "CLI -> gateway -> account service -> response" \
  --sub-feature "lookup-status=Return the current account status." \
  --entrypoint "cli=Run the account lookup command." \
  --drive "cli=Run the public command from the project root." \
  --entrypoint-proof "cli=Exit zero and print the expected status." \
  --gotcha "A zero exit without the expected status is insufficient." \
  --evidence-boundary "Retain bounded output and exit status." \
  --cleanup-boundary "Remove only verifier-owned temporary state." \
  --command "uv run pytest tests/test_account_lookup.py -q" \
  --output json
```

Add `--ready` to run the command before writing `draft: false`:

```sh
.pkstack/bin/projectctl feature generate account-lookup \
  --title "Account lookup" \
  --behavior "A caller can retrieve account status." \
  --expected-path "CLI -> gateway -> account service -> response" \
  --sub-feature "lookup-status=Return the current account status." \
  --entrypoint "cli=Run the account lookup command." \
  --drive "cli=Run the public account lookup command." \
  --entrypoint-proof "cli=Exit zero and print the expected status." \
  --gotcha "The public command must be exercised." \
  --evidence-boundary "Retain bounded verifier output." \
  --cleanup-boundary "Remove only temporary fixture state." \
  --command "uv run pytest tests/test_account_lookup.py -q" \
  --ready --output json
```

Schema 2 is the only supported format; all its structured fields are required.
A failed proof leaves a new target absent or leaves an
existing target unchanged. `feature validate` checks syntax, links, location,
duplicate slugs, and command policy; it does not prove the behavior:

```sh
.pkstack/bin/projectctl feature show account-lookup --output json
.pkstack/bin/projectctl feature list --output json
.pkstack/bin/projectctl feature validate --output json
```

For one to five features, prepare one JSON plan and prove only the named
representative during generation:

```sh
.pkstack/bin/projectctl feature generate-map feature-plan.json \
  --representative account-lookup --output json
```

The other records remain drafts until each verifier passes. Publish and verify
them separately:

```sh
.pkstack/bin/projectctl feature publish account-lookup --output json
.pkstack/bin/projectctl feature verify account-lookup --output json
```

Aim for the most useful three to five features when the project has that many;
a smaller application can start with one. Rewrite older schema-1 records as
reviewed schema-2 contracts. There is no migration command.

## Run a verified goal

In the selected `pkstack` session:

```text
/pkstack-verified-goal Implement account lookup and make account-lookup pass.
```

The skill inspects one contract, makes a bounded change, runs one verifier,
and repeats only while the stored goal remains `active`. Completion requires
stored status `passed`. Native subagents may help with bounded diagnosis, but
the primary session owns edits and final evidence.

For explicit CLI control, start one goal from exactly one source:

```sh
.pkstack/bin/projectctl goal start \
  "Repair account lookup" \
  --feature account-lookup --max-attempts 4 --output json
```

Or supply one reviewed command:

```sh
.pkstack/bin/projectctl goal start \
  "Repair account lookup" \
  --command "uv run pytest tests/test_account_lookup.py -q" \
  --max-attempts 4 --output json
```

Inspect and verify:

```sh
.pkstack/bin/projectctl goal status --output json
.pkstack/bin/projectctl goal verify --output json
```

| Result | Exit | Stored status |
| --- | ---: | --- |
| Verifier passed | 0 | `passed` |
| Verifier failed with attempts left | 1 | `active` |
| Verifier failed on the final attempt | 1 | `exhausted` |
| Invalid state or command | 2 | unchanged or unavailable |

There is one goal slot per project. A new goal cannot replace an existing
one. An exhausted goal needs an explicit larger budget (`goal resume
--add-attempts 2`); the total maximum is 20. Clear terminal state only after
preserving evidence:

```sh
.pkstack/bin/projectctl goal clear --output json
```

Active state requires the explicit `--force` abandonment option. Clearing
state does not revert project edits. `goal tripwire` is an advisory read and
cannot schedule another turn or mark success.

Ctrl-C or SIGTERM stops the verifier's process group and releases the goal
lock. Cancellation never records a passing result. Inspect `goal status`
before deciding whether to retry.

### Verifier boundary

Commands run as argv with `shell=False`. Pipelines, redirects, substitutions,
direct shell interpreters, obvious placeholders, destructive operations, and
known path escapes are rejected. The policy is an evidence screen, not a
sandbox or a semantic proof checker. A permitted project script can still
write files, access the network, or use credentials available to its process.
Review the displayed command, its project scope, and its output before
approving it. Never put credentials in a contract, objective, or evidence
record.

## Use project knowledge

The feature map is the first context layer. Check the broader integration only
when the feature and its explicit links do not answer the question:

```sh
.pkstack/bin/projectctl knowledge status --output json
.pkstack/bin/projectctl knowledge validate --output json
.pkstack/bin/projectctl knowledge search "account suspension" --output json
```

When installed, canonical `okn` handles bounded Wiki validation and search.
Without it, status reports `feature-map-only`; `knowledge validate
--require-okn` and search fail rather than silently substituting another
runtime. Native Kiro `/knowledge` may index the same files but is not the
canonical checker. Use `/okf` to produce, maintain, or consume bounded
source-controlled knowledge.

## Upstream maintenance

The hosted updater is disabled after a live proposal-validation failure.
The commands below remain available for explicit, reviewed maintenance; they
do not imply scheduled updates are currently shipping. See the
[updater guide](upstream-control-loop.md) and
[release status](../../../reviews/release-status.md).

In this repository, use `/pkstack-maintain` or inspect the pinned sources with:

```sh
.pkstack/bin/projectctl upstream check \
  --manifest maintenance/upstreams.json \
  --power-root powers/pkstack \
  --output json
```

The command treats manifests, ledgers, remote responses, patches, and source
content as untrusted data. It proves fixed identities, bounded fast-forward
history, complete source-scoped inventories, and A/B/C dispositions without
executing upstream content. A proposal may advance one source only. Acceptance
requires a reviewed exact head and an explicit dry run before applying:

```sh
.pkstack/bin/projectctl upstream accept \
  --manifest maintenance/upstreams.json \
  --power-root powers/pkstack \
  --proposal .pkstack-maintenance/proposal.json \
  --expected-head <exact-head-commit> \
  --dry-run --output json
```

Do not treat a drift result, historical campaign, or reviewer report as a
current release pass. See the [upstream feature contract](../../../Wiki/features/pkstack-upstream-maintenance.md)
for the scope and [provenance](provenance.md) for source identities.

## Recovery

| Symptom | Safe response |
| --- | --- |
| `pending_updates` | Review the dry run, then repeat with explicit `--update-managed`. |
| `conflicts` | Preserve the user edit, compare it with the Power, and resolve it manually. |
| `stale_managed` | Review each exact retired path; do not let setup prune it. |
| Legacy managed installation | Preserve project files, review the old receipt, and follow the clean-reinstall procedure above. |
| Missing Power assets | Restore or reinstall the Power source; never use the target cache as authority. |
| Doctor drift | Inspect the receipt and rerun the Power-local dry run before applying a fix. |
| Missing `/pkstack-verified-goal` | Select `pkstack`; if needed, start a fresh `kiro-cli chat --v3 --agent pkstack`. |
| Corrupt goal state | Preserve `.pkstack/state/goal.json`, inspect it, and make an explicit clear/recovery decision. |
| Managed symlink | Replace it with an intended in-repository file or directory; setup rejects symlink components. |

There is no automatic uninstaller. Back up first, compare receipt hashes, and
remove only unchanged PKStack-owned paths one at a time. Never delete a broad
workspace or rewrite user-owned Wiki material as a cleanup shortcut.

## Related documentation

- [Architecture and trust boundaries](architecture.md)
- [Kiro surface compatibility](kiro-v3-compatibility.md)
- [Upstream skill parity](upstream-skill-parity.md)
- [Provenance and porting boundary](provenance.md)
- [Validation report](validation-report.md)
- [Review harness](../reviews/README.md)
- [Release status and validation evidence](../../../reviews/release-status.md)
