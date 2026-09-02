# Usage

## Workflow at a glance

PK-Stack keeps implementation in a normal interactive Kiro CLI V3 session
and makes an executable project verifier the completion gate:

```text
import and review Power
        |
        v
/setup-pstack -- Power-local dry run, then bootstrap
        |
        v
.pstack/bin/projectctl doctor
        |
        v
/agent swap pstack -- attach repo-local prompt, tools, and permissions
        |
        v
feature contract -- draft, or --ready after a passing proof
        |
        v
/verified-goal <objective> -- same-session implement/verify/repair loop
```

There is no nested Kiro process in that path. An external ACP host,
`kiro-cli acp`, classic/V2, `/spawn`, a Stop hook, and native `/goal` are not
the default execution mechanism. See
[Architecture](architecture.md) for the trust boundaries and
[Kiro CLI v3 compatibility](kiro-v3-compatibility.md) for the inspected Kiro
build.

## Prerequisites

You need:

1. A local project directory you are allowed to modify.
2. Kiro CLI with V3 available. The initial campaign used Kiro CLI `2.20.2`
   (app build `20260831.180303`); the selected-profile acceptance campaign used
   Kiro CLI `2.21.0`.
3. [`uv`](https://docs.astral.sh/uv/) on `PATH`.
4. Python 3.11 or newer. The setup shim can ask `uv` for a compatible Python
   when the invoking Python is older.
5. A repeatable test, build, lint, type-check, or domain command that proves the
   behavior being changed.

Inspect the local tools without changing a project:

```bash
kiro-cli --version
kiro-cli chat --help
kiro-cli chat --list-models --format json-pretty
uv --version
```

`max` is the highest Kiro effort name exposed by the tested CLI; there is no
documented Kiro `ultra` effort. Model selection is a session choice and is not
stored by projectctl.

## Import the Power and start V3

The package root is an Agent Plugins Power (`plugin.json`) with manifest ID
`pk-stack`. In the combined repository it is `powers/pk-stack/`. Import that local folder through
Kiro's Power management interface and review it before enabling it. An earlier pre-release
import under `pstack-kiro` may remain a separate Power and should be removed
through that interface before importing `pk-stack`. The project does not
install itself into global Kiro directories or change user-level settings.

Start the target repository in V3:

```bash
cd /path/to/project
kiro-cli chat --v3
```

An explicit high-effort launch, when supported by the account, is:

```bash
kiro-cli chat --v3 --model gpt-5.6-sol --effort max
```

After the project assets exist, select the primary custom profile for every
PK-Stack workflow session:

```bash
kiro-cli chat --v3 --agent pstack
```

The initial ambient V3 chat is only the bootstrap path because the workspace
agent does not exist before setup. The port deliberately leaves user-level
Kiro defaults unchanged.

## Set up a project

### Preferred current-session path

In the V3 session, invoke:

```text
/setup-pstack
```

The skill resolves `scripts/setup_pstack.py` relative to its own loaded
`SKILL.md`. It never executes a repository-supplied `./projectctl` as a setup
authority. Its first operation is equivalent to:

```bash
python3 /absolute/path/to/pstack-kiro/skills/setup-pstack/scripts/setup_pstack.py \
  --root "$PWD" \
  --dry-run \
  --output json
```

On a fresh project, review the preview and run the same Power-local shim without
`--dry-run`:

```bash
python3 /absolute/path/to/pstack-kiro/skills/setup-pstack/scripts/setup_pstack.py \
  --root "$PWD" \
  --output json
```

The slash skill performs those steps for the user. These direct commands are
the source-checkout fallback and the reproducible setup interface for testing.

After success, use this entrypoint for every project operation:

```bash
.pstack/bin/projectctl version --output json
```

Its stable `name` remains the Python distribution identifier `pstack-kiro`.
Both text and JSON output also report `display_name: PK-Stack`,
`expanded_name: Poteto Kiro`, and `power_id: pk-stack`; JSON consumers should
tolerate additive fields.

Bootstrap may create a root `projectctl` convenience wrapper when the name is
unowned, but the skills do not select or trust it. If the host project already
owns that name, setup preserves it.

### Refresh after selecting `pstack`

The `pstack` profile keeps `includePowers: false`, so the Power-local setup
skill is deliberately unavailable while that profile is selected. Keep the
same interactive V3 session and switch through the Power-enabled setup agent:

```text
/agent swap kiro_default
/setup-pstack
/agent swap pstack
```

If the local Power-enabled agent has a different name, swap back to the agent
used for initial setup. Do not ask the cached controller to discover its own
upgrade source: `.pstack/bin/projectctl setup` returns a structured error
unless `--power-root` is supplied explicitly. The normal authority remains the
Power-local shim resolved by `/setup-pstack`.

### Understand the setup result

The JSON payload reports:

| Field | Meaning |
| --- | --- |
| `created` | Absent managed paths that would be or were created |
| `updated` | Paths scheduled or applied for replacement; owned discovery may refresh as observation |
| `pending_updates` | Receipt-owned paths whose new Power content was not approved |
| `stale_managed` | Receipt-owned paths retired by the Power but still present; never pruned automatically |
| `unchanged` | Paths already matching desired content |
| `conflicts` | User-modified paths or filesystem-type blockers preserved as-is |
| `notes` | Preserved foreign names or absent optional sources |
| `discovery` | Read-only repository inventory |

The compatibility token `.gitignore:pstack-runtime-block` represents the
managed ignore block in those path-inventory arrays. Its spelling remains
stable even though the generated comment says PK-Stack.

`pending_updates`, `stale_managed`, and `conflicts` make `ok` false and exit 2.
Preflight is two-phase: if any of those lists is non-empty, no managed file or
new receipt is written. Setup holds a no-artifact project-directory lock across
preflight, apply, final hash verification, and receipt commit, so concurrent
setup processes serialize rather than producing a mixed runtime.

Setup appends ignore entries for:

```text
.pstack/state/
.pstack/tmp/
.pstack/projectctl/.venv/
```

It does not replace the rest of `.gitignore`, prune stale files, or delete any
project content.

Before target preflight, setup also verifies that the loaded Power contains all
required Python modules, six source skills including the setup shim, steering,
agent/hook templates, and the runtime lock. A missing required Power asset
returns a structured error before any target file is written.

Repository discovery records sorted project-relative paths and always stores
`"root": "."`; it does not record local `okn` availability. Discovery is an
owned observation, so it refreshes automatically when repository markers
change instead of becoming a managed upgrade. An applied idempotent setup also
normalizes managed executables to `0755` and managed text/receipt files to
`0644`; `--dry-run` never changes modes.

### Upgrade managed files explicitly

When an updated Power reports `pending_updates`, do not rerun blindly. Review
the paths and desired Power version, then preview the exact opt-in:

```bash
python3 /absolute/path/to/pstack-kiro/skills/setup-pstack/scripts/setup_pstack.py \
  --root "$PWD" \
  --dry-run \
  --update-managed \
  --output json
```

Only after explicit approval, apply the same reviewed operation:

```bash
python3 /absolute/path/to/pstack-kiro/skills/setup-pstack/scripts/setup_pstack.py \
  --root "$PWD" \
  --update-managed \
  --output json
```

`--update-managed` can replace only a target whose current hash still matches
the prior PK-Stack receipt. A user-modified target remains a conflict even with
the flag. There is no automatic managed-file upgrade.

### Run doctor

After setup or a reviewed upgrade:

```bash
.pstack/bin/projectctl doctor --output json
```

Doctor checks:

- project root and required `uv` availability;
- the ownership receipt plus every receipt-managed path and SHA-256 digest;
- the internal wrapper, `package = false` project metadata, live lock, and
  cached lock for exact runtime integrity;
- four agents, five live workspace skills, two steering files, and two hook
  files;
- live Kiro assets against their cached managed copies;
- JSON shape, plus `kiro-cli agent validate` when Kiro is installed;
- feature-map validity;
- the `.pstack/state/` ignore rule; and
- schema and semantic validity of any goal state.

Missing `kiro-cli` and optional canonical `okn` are warnings to the Python
control surface. Missing or changed receipt-owned files, an invalid receipt,
runtime drift, a broken feature map, unignored state, or corrupt goal state are
failures. The receipt is an unsigned drift detector, not proof against a writer
who can change both managed content and its recorded digest.

The setup skill is deliberately absent from the live workspace skill checks.
It remains supplied by the loaded Power and is cached for bootstrap packaging;
doctor checks the five skills that bootstrap actually materializes in
`.kiro/skills/`.

Also inspect the narrow and broad knowledge surfaces:

```bash
.pstack/bin/projectctl feature validate --output json
.pstack/bin/projectctl knowledge validate --output json
```

After setup, attach the generated profile before the next workflow message:

```text
/agent swap pstack
```

If Kiro has not discovered the new agent or slash skills in the current chat,
exit and restart the same repository with `kiro-cli chat --v3 --agent pstack`.
Once selected and loaded, the entire goal loop remains in that session.

## Kiro-native workflow and approvals

The installed skill entrypoints are:

```text
/architect <architecture problem>
/arena <artifact and gradeable criteria>
/swarm <bounded coverage or race request>
/model-council <intent, evidence, and review rubric>
/verified-goal <objective with a checkable definition of done>
```

Architecture, arena, swarm, and review flows can use native Kiro subagents.
`/spawn` starts a separate user session and is not their internal fanout path.
External Fable or Grok council members are optional advisory reviewers; their
opinions never replace executable project evidence.

The project installs these custom profiles:

| Agent | Intended use | Direct write access |
| --- | --- | --- |
| Poteto Kiro (`pstack`) | Primary implementation and orchestration | Workspace writes are `ask`; bootstrap-managed control-plane paths are `deny` |
| `pstack-architect` | Architecture comparison | `write` and `shell` omitted; `fs_write` denied |
| `pstack-reviewer` | Independent evidence review | `write` and `shell` omitted; `fs_write` denied |
| `pstack-verifier` | Contract and recorded-evidence inspection | `write` and `shell` omitted; `fs_write` denied |

Only the primary profile can execute shell commands. The complete canonical
`.pstack/bin/projectctl` prefix is `ask`, not `allow`; expect Kiro to request
approval before every invocation. Every Git shell command also asks; selected
destructive Git forms remain denied. Delegated profiles inspect code,
contracts, and recorded evidence, then return the exact proposed command to the
primary session. This tool omission is the read-only boundary; child permission
rules alone are not treated as a sandbox.

Do not bypass these prompts with broad trust switches. Review the exact argv,
especially when it comes from repository-controlled feature metadata.

## Create and prove feature contracts

Feature slugs use lowercase letters, digits, and single hyphens. A contract
describes user behavior, the expected system path, and an optional argv-style
verifier.

### Create a draft

```bash
.pstack/bin/projectctl feature generate account-lookup \
  --title "Account lookup" \
  --behavior "A caller can retrieve an account status." \
  --expected-path "CLI -> gateway -> account service -> response" \
  --command "uv run pytest tests/test_account_lookup.py -q" \
  --output json
```

This writes `Wiki/features/account-lookup.md` with `draft: true` without
running its command. An omitted command is allowed for a draft and produces a
validation warning. Add an existing knowledge link with, for example,
`--related ../architecture/account-boundary.md`; related paths resolve from the
feature file and must remain inside the project and exist at validation time.

Inspect the contract:

```bash
.pstack/bin/projectctl feature show account-lookup --output json
.pstack/bin/projectctl feature list --output json
.pstack/bin/projectctl feature validate --output json
```

`feature validate` checks strict frontmatter types, required sections, location
and slug consistency, related links, and the verifier hazard policy. It does
not run verifier commands.

### Generate a ready contract

Use `--ready` when the command should be run now as the initial proof:

```bash
.pstack/bin/projectctl feature generate account-lookup \
  --title "Account lookup" \
  --behavior "A caller can retrieve an account status." \
  --expected-path "CLI -> gateway -> account service -> response" \
  --command "uv run pytest tests/test_account_lookup.py -q" \
  --ready \
  --output json
```

Projectctl builds and parses the exact candidate Markdown before the verifier,
requiring the caller's title, behavior, expected path, command, and related
links to round-trip unchanged. Ready-contract related paths must already be
contained in the project and present. The command then runs from the project
root. On pass, projectctl repeats the candidate preflight, writes
`draft: false`, and returns `initial_verification`. Invalid input runs no proof;
a failed proof exits 1 with `created: false` and leaves a new target absent.

To replace an existing contract deliberately, add `--overwrite --ready`.
Overwrite refusal happens before proof, and a failed proof leaves the existing
file unchanged. Preserve any manual edits before approving an overwrite.

### Re-run a stored verifier

Only a published contract (`draft: false`) can be run here or selected by `goal start --feature`.
Draft rejection happens before its command executes or goal state is created.

```bash
.pstack/bin/projectctl feature verify account-lookup --output json
```

The alias is equivalent:

```bash
.pstack/bin/projectctl verify account-lookup --output json
```

The default timeout is 300 seconds. Override it explicitly when justified:

```bash
.pstack/bin/projectctl feature verify account-lookup \
  --timeout-seconds 600 \
  --output json
```

### Verifier safety boundary

Commands execute directly as argv with `shell=False`. Pipelines, redirection,
substitution, compound shell syntax, and every direct shell-interpreter form are
unsupported. An executable project shell script remains usable through its
shebang. Python must select an explicit script or module through a small set of
standard startup flags. Node, Ruby, Perl, PHP, and `osascript` must name the
script as their first operand; put required runtime configuration in a project
executable or use the project's test/package runner instead. These restrictions
reject stdin, inline evaluation, empty interpreters, and ambiguous leading
options instead of attempting to emulate each interpreter's grammar.

The supported `uv` seam is deliberately narrow: optional non-value global
flags, `run`, optional common non-value run flags or `--with`,
`--with-requirements`, `--python`, and `--env-file`, then an explicit nested
command. `uv --directory`, `uv --project`, module/script shorthand, attached
short option values, and unknown leading wrapper options fail closed. Projectctl
also rejects informational-only invocations, obvious destructive executables,
mutating Git/cloud/infrastructure/container patterns, context-free placeholder
commands, and direct projectctl self-verification.

That policy is an **obvious-hazard/evidence screen, not a sandbox or semantic
proof checker**. It rejects obvious placeholders but cannot distinguish a
renamed no-op or irrelevant project script from a real domain predicate. An
allowed test or project script inherits the caller's host-project environment,
not the projectctl control-plane venv, and retains the user's operating-system
permissions. It can write files, reach the network, or use available
credentials. The containment screen covers ordinary argv paths, `--name=path`
forms, local file URLs, and a documented set of attached path flags used by
`uv`, Git, make, pytest, Ruby, Go, pnpm, Cargo, and common C/C++ drivers. It
cannot infer a custom program's private option grammar or paths constructed
inside an allowed script. Select the `pstack` agent, confirm that the displayed
stored predicate covers the claimed behavior, review its `ask` decision, and
avoid broad trust flags. Captured verifier output is stored in goal state, so do
not print secrets.

## Run a verified goal

### Preferred current-session path

In the current Kiro V3 chat:

```text
/verified-goal Repair suspended-account lookup and make account-lookup pass.
```

The skill uses `.pstack/bin/projectctl` for the whole loop. It inspects state,
selects one executable contract, makes the smallest evidence-backed change,
runs one verification attempt, diagnoses the result, and repeats only while
status is `active`. It may use native subagents for bounded diagnosis, but the
current primary session owns edits and final evidence.

The skill does not invoke native `/goal`, start an external ACP host or
`kiro-cli acp`, open a nested Kiro CLI, or move the work to `/spawn`.
Completion requires stored status `passed`.

### Start state manually

Start with exactly one acceptance source:

```bash
# Existing feature contract
.pstack/bin/projectctl goal start \
  "Repair suspended-account lookup" \
  --feature account-lookup \
  --max-attempts 4 \
  --output json

# Or one explicit argv command
.pstack/bin/projectctl goal start \
  "Repair suspended-account lookup" \
  --command "uv run pytest tests/test_account_lookup.py -q" \
  --max-attempts 4 \
  --output json
```

A Kiro spec can supply a third bridge. Create
`.kiro/specs/account-lookup/pstack-verification.json`:

```json
{
  "command": ["uv", "run", "pytest", "tests/test_account_lookup.py", "-q"]
}
```

Then start it:

```bash
.pstack/bin/projectctl goal start \
  "Implement the account lookup spec" \
  --spec account-lookup \
  --max-attempts 4 \
  --output json
```

Do not combine `--feature`, `--command`, and `--spec`. Spec names cannot contain
path separators or traversal. Attempt budgets are 1 through 20.

Any existing goal state blocks a new start, including passed or exhausted
state. Projectctl has no state-replacement shortcut. Inspect and clear prior
terminal state deliberately before starting another objective.

### Inspect and verify

```bash
.pstack/bin/projectctl goal status --output json
.pstack/bin/projectctl goal verify --output json
```

One `goal verify` call consumes at most one attempt and records its evidence:

| Outcome | CLI exit | Stored status | Action |
| --- | ---: | --- | --- |
| Verifier passed | 0 | `passed` | Inspect status and report the exact command/result |
| Verifier failed with budget left | 1 | `active` | Diagnose, make one advancing change, verify again |
| Verifier failed on the final attempt | 1 | `exhausted` | Stop and request an explicit budget decision |
| State or command is invalid | 2 | unchanged or unavailable | Repair the state/setup defect; do not claim proof ran |

Nested verifier codes remain in JSON. A timeout records exit 124; an executable
launch failure records 127. The outer goal command exits 1 whenever the goal did
not pass.

Goal state schema version 2 stores the objective, immutable contract and
provenance, a contract digest, attempt budget, last result, and append-only
history. The digest and semantic checks detect command/history tampering; they
are integrity checks, not cryptographic authorization. State is mode `0600`
under ignored `.pstack/state/`. Never place credentials in objectives or
commands, and keep verifier output free of secrets.

`goal status` remains responsive while a verifier runs. Only one verifier runs
at a time. Status and tripwire reads do not create `.pstack/state/` when no goal
exists. If any goal state changes while proof is in flight, the result is
discarded.

The advisory probe is read-only:

```bash
.pstack/bin/projectctl goal tripwire --output json
```

It cannot block Stop, schedule another turn, or mark success. The shipped Stop
hook is disabled.

### Resume or clear deliberately

An exhausted goal needs an explicit larger budget:

```bash
.pstack/bin/projectctl goal resume --add-attempts 2 --output json
.pstack/bin/projectctl goal verify --output json
```

An absolute ceiling is also supported:

```bash
.pstack/bin/projectctl goal resume --max-attempts 6 --output json
```

The new maximum cannot be below attempts already used or above 20. An exhausted
goal must receive at least one new attempt; a passed goal cannot resume. The
`/verified-goal` skill never extends its own budget automatically.

Clear terminal state only after preserving the evidence you need:

```bash
.pstack/bin/projectctl goal clear --output json
```

Clearing an active goal is refused. Explicit abandonment requires:

```bash
.pstack/bin/projectctl goal clear --force --output json
```

`--force` removes goal JSON and history; it does not revert project edits. The
skill never force-clears automatically.

## Project knowledge

Check the integration mode:

```bash
.pstack/bin/projectctl knowledge status --output json
```

Without canonical `okn`, validation covers only the feature map and warns:

```bash
.pstack/bin/projectctl knowledge validate --output json
```

Require broad OKF validation when it is part of acceptance:

```bash
.pstack/bin/projectctl knowledge validate --require-okn --output json
```

With `okn` installed, validation delegates to `okn validate Wiki`. Broad search
also requires it:

```bash
.pstack/bin/projectctl knowledge search "account suspension" --output json
```

That delegates to `okn search Wiki <query>`. PK-Stack does not implement a
fallback OKF graph or broad text index.

## Recovery runbook

### Setup reports `pending_updates`

The installed content still matches its prior receipt, but the loaded Power has
new content. Nothing was written. Review the normal dry run, then use the two
`--update-managed` commands in
[Upgrade managed files explicitly](#upgrade-managed-files-explicitly).

### Setup reports `conflicts`

The named path was modified after PK-Stack installed it, is foreign, or has the
wrong filesystem type. `--update-managed` will not overwrite it. Preserve a
copy, compare it with the Power source and receipt, then merge or restore it by
an explicit project decision. Rerun the Power-local dry run afterward:

```bash
python3 /absolute/path/to/pstack-kiro/skills/setup-pstack/scripts/setup_pstack.py \
  --root "$PWD" \
  --dry-run \
  --output json
```

Do not remove `.pstack/bootstrap.json` to manufacture ownership. Without its
valid prior hashes, existing managed-looking files cannot be authorized for an
upgrade and will remain protected.

### Setup reports `stale_managed`

The loaded Power retired a path that the prior receipt still owns, and that
path still exists. Bootstrap detects it but never prunes it, even with
`--update-managed`. Review each listed path and preserve any adopted or modified
content. If the project explicitly decides to retire an unchanged asset, remove
only that exact listed path (and any separately listed cached copy), then rerun
the normal Power-local dry run. A successful subsequent setup drops absent
retired paths from the new receipt.

### Setup reports missing required Power assets

The loaded Power checkout or installed package is incomplete. The target was
not partially bootstrapped. Restore or reinstall the exact Power source and
runtime lock, then rerun the Power-local dry run. Do not substitute target-side
cached files for a missing Power-local setup authority.

### Doctor reports runtime or Kiro-asset drift

First inspect exact failing checks:

```bash
.pstack/bin/projectctl doctor --output json
```

Then use the Power-local setup dry run. A receipt-owned old version appears as
`pending_updates`; a local edit appears as `conflicts`. Apply only the reviewed
resolution, and rerun doctor. The cached lock and live lock must match, and the
internal runtime must retain `[tool.uv] package = false` and locked execution.

### Goal state is corrupt or uses schema version 1

Projectctl rejects unsupported or contradictory state and does not migrate it
automatically. Preserve the file before any recovery decision:

```bash
mkdir -p .pstack/recovery
cp .pstack/state/goal.json .pstack/recovery/goal.json.backup
```

If the evidence is still needed, inspect and migrate it deliberately outside
the active workflow. If the user explicitly abandons that state, move it out of
the active slot rather than deleting it:

```bash
mv .pstack/state/goal.json .pstack/recovery/goal.json.abandoned
```

Only then can a new `goal start` create schema version 2 state. Neither doctor
nor `/verified-goal` discards corrupt evidence automatically.

If the JSON and state invariants remain valid but a stored verifier is rejected
by a newer policy or a changed executable path, normal status continues to fail
closed. After preserving the evidence, an explicit
`.pstack/bin/projectctl goal clear --force` may clear that policy-invalid state;
`--force` does not make malformed JSON or contradictory evidence loadable.

### A managed path is a symlink

Bootstrap and state/knowledge paths reject symlink components. Inspect the
symlink and its target. Replace it with an in-repository real directory or file
only when that is the project's intended layout, then rerun setup dry-run. Do
not point managed paths outside the repository.
Repository discovery markers such as `package.json`, test directories, and
Kiro asset trees are subject to the same rule; symlinked markers are
intentionally unsupported even when their current target points back inside the
repository.

### `/verified-goal` is missing after setup

First run `/agent swap pstack`. If Kiro has not discovered the new workspace
agent or `.kiro/skills/`, start one new V3 chat in the same repository with
`kiro-cli chat --v3 --agent pstack`. Do not switch to V2, start an external ACP
host or `kiro-cli acp`, modify the global default agent, or invent prose-only
goal state. Once discovered, invoke `/verified-goal` normally in that current
session.

## Cleanup boundary

There is no automated uninstaller. Power removal and project cleanup are
separate:

- Disable or remove the Power through Kiro's management interface; that does
  not delete materialized project files.
- Treat `.pstack/bootstrap.json` as an inventory, never as an executable delete
  script.
- Feature contracts and broader `Wiki/` content are project-owned.
- A foreign root `projectctl` was never owned by PK-Stack.
- The `.gitignore` block was appended into a project-owned file.
- Use `goal clear` for valid state; do not recursively delete project state or
  managed files as a normal cleanup step.

For complete removal, back up the repository, compare every receipt path with
its recorded hash, remove only unchanged PK-Stack-owned content one path at a
time, and preserve all user-authored or conflicting material.
