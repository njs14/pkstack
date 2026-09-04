# Usage

PK-Stack keeps implementation and repair work in the current Kiro session.

This guide covers the current PK-Stack path: a Power-local bootstrap,
the generated `pk-stack` Kiro agent, a feature contract, and a verifier run in
the current Kiro session. Start with the [repository README](../../../README.md) if you
are deciding whether to install it.

## The short version

```text
import and review the Power
        |
        v
/setup-pk-stack  ->  review the dry run and bootstrap
        |
        v
select pk-stack  ->  use the IDE picker or /agent swap pk-stack
        |
        v
native Spec / Quick Spec / Bug Fix  ->  Kiro owns the plan
        |
        v
feature contract + verifier  ->  projectctl owns executable proof
        |
        v
/verified-goal <objective>  ->  current-session implement / verify / repair
```

Kiro CLI v3 and the Kiro IDE agent panel are the primary surfaces. Kiro Crew is
optional. Kiro Web can consume committed workspace assets, but its end-to-end
path and the IDE/CLI approval boundary are untested. PK-Stack does not launch
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

PK-Stack inherits the model and effort selected in Kiro. It does not store a
model choice in `projectctl` or require a particular provider for interactive
work.

The historical acceptance campaign used Sol at maximum effort. That is
evidence, not the interactive default; select the desired normal effort
afterwards because Kiro persists the choice. Cheap, fast models are usually a
better fit for repeatable mechanical smoke tests.

## Choose the Power source

The Power-local setup script is the only source and upgrade authority. When
using a source checkout, set one environment variable to the checkout's
`powers/pk-stack` directory:

```sh
: "${PK_STACK_POWER:?Set PK_STACK_POWER to the checked-out PK-Stack Power directory}"
test -f "$PK_STACK_POWER/plugin.json"
test -f "$PK_STACK_POWER/skills/setup-pk-stack/scripts/setup_pk_stack.py"
```

Do not infer this value from a target project's `.pk-stack/` cache. An installed
Power may be imported through Kiro's Power manager instead; the same
Power-local rule applies.

## Import and bootstrap

Import [`powers/pk-stack/`](../) through Kiro's Power manager and review the
package. In the target repository, use the current Kiro chat or Agent Focus
session and invoke:

```text
/setup-pk-stack
```

The skill first previews managed changes. Review `pending_updates`,
`stale_managed`, and `conflicts`; a non-empty list blocks writes. The direct
source-checkout equivalent is useful for troubleshooting and deterministic
tests:

```sh
python3 "$PK_STACK_POWER/skills/setup-pk-stack/scripts/setup_pk_stack.py" \
  --root "$PWD" --dry-run --output json
python3 "$PK_STACK_POWER/skills/setup-pk-stack/scripts/setup_pk_stack.py" \
  --root "$PWD" --output json
```

After a successful setup, use only the generated wrapper for project
operations:

```sh
.pk-stack/bin/projectctl version --output json
.pk-stack/bin/projectctl doctor --output json
.pk-stack/bin/projectctl feature validate --output json
```

Setup may create a root `projectctl` convenience wrapper when that name is
unowned. It is not the trusted entrypoint. The canonical wrapper uses the
shipped locked runtime under `.pk-stack/projectctl/`; its environment does not
become the verifier's environment.

### Refresh managed files

Return to the Power-enabled Kiro agent before refreshing. In CLI v3:

```text
/agent swap kiro_default
/setup-pk-stack
/agent swap pk-stack
```

Use the local setup-agent name if it differs. If the dry run reports
`pending_updates`, inspect the exact paths and preview the explicit upgrade:

```sh
python3 "$PK_STACK_POWER/skills/setup-pk-stack/scripts/setup_pk_stack.py" \
  --root "$PWD" --dry-run --update-managed --output json
python3 "$PK_STACK_POWER/skills/setup-pk-stack/scripts/setup_pk_stack.py" \
  --root "$PWD" --update-managed --output json
```

`--update-managed` replaces only a path that still matches its prior receipt
hash. It never overwrites a user edit. `stale_managed` paths are not deleted
automatically; preserve or remove each exact path by a separate project
decision. The cached controller's setup command fails unless an explicit,
reviewed `--power-root` is supplied.

For pre-0.3 installations, use a clean reinstall. Preserve project-owned
`Wiki/` content, native `.kiro/specs/`, user-authored settings, and any evidence
you want to retain. Inspect `.pk-stack/bootstrap.json` and remove only the
PK-Stack-managed paths whose bytes still match their receipt hashes, plus
the receipt itself. Remove retired cache paths explicitly; never delete an
entire `.kiro/` or Wiki directory. Then run fresh setup from the reviewed Power.
User-modified managed files need a deliberate keep-or-replace decision first.
Old goals and schema-1 feature records are not imported automatically.

### Attach the generated agent

The bootstrap conversation may not inherit the new profile. In the IDE choose
the workspace `pk-stack` agent. In CLI v3 use either:

```text
/agent swap pk-stack
```

or, when Kiro has not discovered the new assets yet:

```sh
kiro-cli chat --v3 --agent pk-stack
```

Keep the handoff in the same conversation when possible. The primary profile
asks before ordinary writes and canonical controller commands. Delegated
architect, reviewer, and verifier profiles omit `write` and `shell`; they
inspect and report to the primary session. These Kiro permissions complement
the controller's checks but are not an operating-system sandbox.

## Plan and bind work

For nontrivial work, use Kiro's native planner before the PK-Stack loop:

- CLI v3: `/spec new <name>`, then `/spec <name>` to resume;
- IDE: **Build with spec** or the workflow picker; and
- choose standard Spec for unfamiliar or high-risk work, or Quick Spec for a
  bounded change whose shape is already clear.

Kiro owns requirements or bug analysis, design, tasks, dependency waves, and
native task execution. When those artifacts are ready, return to `pk-stack` and
bind the native plan to an executable verifier. For a new, still-failing feature:

```sh
.pk-stack/bin/projectctl goal bind-spec account-lookup \
  --command "python3 -m unittest discover -s tests -v" --output json
.pk-stack/bin/projectctl goal start "Repair account lookup" \
  --spec account-lookup --max-attempts 4 --output json
.pk-stack/bin/projectctl goal verify --output json
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
.pk-stack/bin/projectctl feature generate account-lookup \
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
.pk-stack/bin/projectctl feature generate account-lookup \
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
.pk-stack/bin/projectctl feature show account-lookup --output json
.pk-stack/bin/projectctl feature list --output json
.pk-stack/bin/projectctl feature validate --output json
```

For one to five features, prepare one JSON plan and prove only the named
representative during generation:

```sh
.pk-stack/bin/projectctl feature generate-map feature-plan.json \
  --representative account-lookup --output json
```

The other records remain drafts until each verifier passes. Publish and verify
them separately:

```sh
.pk-stack/bin/projectctl feature publish account-lookup --output json
.pk-stack/bin/projectctl feature verify account-lookup --output json
```

Aim for the most useful three to five features when the project has that many;
a smaller application can start with one. Rewrite older schema-1 records as
reviewed schema-2 contracts. There is no migration command.

## Run a verified goal

In the selected `pk-stack` session:

```text
/verified-goal Implement account lookup and make account-lookup pass.
```

The skill inspects one contract, makes a bounded change, runs one verifier,
and repeats only while the stored goal remains `active`. Completion requires
stored status `passed`. Native subagents may help with bounded diagnosis, but
the primary session owns edits and final evidence.

For explicit CLI control, start one goal from exactly one source:

```sh
.pk-stack/bin/projectctl goal start \
  "Repair account lookup" \
  --feature account-lookup --max-attempts 4 --output json
```

Or supply one reviewed command:

```sh
.pk-stack/bin/projectctl goal start \
  "Repair account lookup" \
  --command "uv run pytest tests/test_account_lookup.py -q" \
  --max-attempts 4 --output json
```

Inspect and verify:

```sh
.pk-stack/bin/projectctl goal status --output json
.pk-stack/bin/projectctl goal verify --output json
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
.pk-stack/bin/projectctl goal clear --output json
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
.pk-stack/bin/projectctl knowledge status --output json
.pk-stack/bin/projectctl knowledge validate --output json
.pk-stack/bin/projectctl knowledge search "account suspension" --output json
```

When installed, canonical `okn` handles bounded Wiki validation and search.
Without it, status reports `feature-map-only`; `knowledge validate
--require-okn` and search fail rather than silently substituting another
runtime. Native Kiro `/knowledge` may index the same files but is not the
canonical checker. Use `/okf` to produce, maintain, or consume bounded
source-controlled knowledge.

## Upstream maintenance

In this repository, use `/maintain-pk-stack` or inspect the pinned sources with:

```sh
.pk-stack/bin/projectctl upstream check \
  --manifest maintenance/upstreams.json \
  --power-root powers/pk-stack \
  --output json
```

The command treats manifests, ledgers, remote responses, patches, and source
content as untrusted data. It proves fixed identities, bounded fast-forward
history, complete source-scoped inventories, and A/B/C dispositions without
executing upstream content. A proposal may advance one source only. Acceptance
requires a reviewed exact head and an explicit dry run before applying:

```sh
.pk-stack/bin/projectctl upstream accept \
  --manifest maintenance/upstreams.json \
  --power-root powers/pk-stack \
  --proposal .pk-stack-maintenance/proposal.json \
  --expected-head <exact-head-commit> \
  --dry-run --output json
```

Do not treat a drift result, historical campaign, or reviewer report as a
current release pass. See the [upstream feature contract](../../../Wiki/features/pk-stack-upstream-maintenance.md)
for the scope and [provenance](provenance.md) for source identities.

## Recovery

| Symptom | Safe response |
| --- | --- |
| `pending_updates` | Review the dry run, then repeat with explicit `--update-managed`. |
| `conflicts` | Preserve the user edit, compare it with the Power, and resolve it manually. |
| `stale_managed` | Review each exact retired path; do not let setup prune it. |
| Missing Power assets | Restore or reinstall the Power source; never use the target cache as authority. |
| Doctor drift | Inspect the receipt and rerun the Power-local dry run before applying a fix. |
| Missing `/verified-goal` | Select `pk-stack`; if needed, start a fresh `kiro-cli chat --v3 --agent pk-stack`. |
| Corrupt goal state | Preserve `.pk-stack/state/goal.json`, inspect it, and make an explicit clear/recovery decision. |
| Managed symlink | Replace it with an intended in-repository file or directory; setup rejects symlink components. |

There is no automatic uninstaller. Back up first, compare receipt hashes, and
remove only unchanged PK-Stack-owned paths one at a time. Never delete a broad
workspace or rewrite user-owned Wiki material as a cleanup shortcut.

## Related documentation

- [Architecture and trust boundaries](architecture.md)
- [Kiro surface compatibility](kiro-v3-compatibility.md)
- [Upstream skill parity](upstream-skill-parity.md)
- [Provenance and porting boundary](provenance.md)
- [Validation report](validation-report.md)
- [Review harness](../reviews/README.md)
- [Release status and validation evidence](../../../reviews/release-status.md)
