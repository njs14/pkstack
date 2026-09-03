# Usage

## Workflow at a glance

PK-Stack keeps implementation in the current Kiro agent session and makes an
executable project verifier the completion gate. Kiro IDE 1.x chat/Agent Focus
and Kiro CLI v3 are the primary surfaces:

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
IDE agent picker or CLI /agent swap pstack
        -- attach repo-local prompt, tools, and permissions
        |
        v
native Spec / Quick Spec / Bug Fix -- Kiro owns requirements, design, tasks
        |
        v
CLI /agent swap pstack or IDE reselect pstack
        |
        v
feature contract + goal bind-spec -- executable proof and dual provenance
        |
        v
/verified-goal <objective> -- same-session implement/verify/repair loop
```

There is no nested Kiro process in that path. A user-launched external ACP host,
`kiro-cli acp`, classic/V2, `/spawn`, and a Stop hook are not the default
execution mechanism. Kiro documents native `/goal`, but the installed CLI
2.21.0 V3 runtime did not recognize it in a sterile interactive probe;
PK-Stack neither invokes nor depends on it. See
[Architecture](architecture.md) for the trust boundaries and
[Kiro surface compatibility](kiro-v3-compatibility.md) for the support/evidence
matrix, September 1-2, 2026 change inventory, and inspected builds.

The native transition is deliberately visible: Kiro does not document a supported Agent Skill or
custom-agent tool for changing the active workflow. In CLI v3, use `/spec new <name>` (Feature,
Quick Spec, or Bug), `/spec <name>`
to resume, and `/spec run <name>` for Kiro's native task execution, then `/agent swap pstack`. In
the IDE, use **Build with spec** or the workflow picker, then reselect `pstack` in the same
conversation. Standard Spec is preferred for unfamiliar, cross-boundary, high-risk, or
requirements-sensitive work; Quick Spec is for bounded, well-understood work. Web uses its native
Spec picker and built-in primary agent. Crew may consume committed specs in its Task Runner, but
PK-Stack does not claim Crew reproduces the local built-in-agent transition.

## Prerequisites

You need:

1. A local project directory you are allowed to modify.
2. Kiro IDE 1.x or Kiro CLI with v3 available. The installed IDE baseline is
   `1.0.437`; the initial CLI campaign used `2.20.2` (app build
   `20260831.180303`) and the selected-profile acceptance campaign used CLI
   `2.21.0`.
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
/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' \
  '/Applications/Kiro.app/Contents/Info.plist'
uv --version
```

`max` is the highest Kiro effort name exposed by the tested CLI; there is no
documented Kiro `ultra` effort. PK-Stack agents do not pin a model or store the
selection in projectctl. Kiro itself automatically persists a CLI `/effort` or
`--effort` choice for that model in the user's settings, and higher effort uses
more credits. Ordinary usage should therefore inherit the user's existing
choice. Kiro recommends Auto for general development, Sol for the hardest
long-horizon work, Terra for routine multi-step work, and Luna for repeated
high-frequency work. See the [versioned model policy and data-processing
boundary](kiro-v3-compatibility.md#models-effort-and-verification-methodology).

## Import the Power and start a primary surface

The package root is an Agent Plugins Power (`plugin.json`) with manifest ID
`pk-stack`. In the combined repository it is `powers/pk-stack/`. Import that local folder through
Kiro's Power management interface and review it before enabling it. An earlier pre-release
import under `pstack-kiro` may remain a separate Power and should be removed
through that interface before importing `pk-stack`. The project does not
install itself into global Kiro directories or change user-level settings.

In Kiro IDE 1.x, open the target repository and then open chat or Agent Focus.
In Kiro CLI, start the target repository in v3:

```bash
cd /path/to/project
kiro-cli chat --v3
```

The acceptance campaign deliberately used the following high-cost
configuration. It is evidence, not the interactive default; select the desired
normal effort afterwards because Kiro persists the choice:

```bash
kiro-cli chat --v3 --model gpt-5.6-sol --effort max
```

To return to Kiro's GPT-5.6 built-in default after that deliberate campaign,
run `/effort high`; use the `/effort` picker instead if another level was your
intended normal setting. `kiro-cli settings open` shows the persisted CLI
configuration.

After the project assets exist, select the workspace `pstack` profile for every
PK-Stack workflow session. Use the IDE agent picker, or launch CLI v3 with:

```bash
kiro-cli chat --v3 --agent pstack
```

In an existing CLI chat, `/agent swap pstack` is equivalent. The initial
ambient IDE or CLI chat is only the bootstrap path because the workspace agent
does not exist before setup. PK-Stack deliberately leaves user-level Kiro
defaults unchanged.

### Optional Crew and supported-by-design Web paths

Kiro Crew can open the repository and consume its `.kiro` agents, skills, and
steering. Crew runs Kiro CLI over ACP internally, but it is an optional
orchestrator and does not make ACP PK-Stack's default entry path.

Kiro Web must start from a repository that already commits the bootstrapped
`.kiro` and `.pstack` assets. Its built-in agent remains primary; project
`pstack-*` agents are delegation-only, and the IDE/CLI permission boundary is
not claimed. The controller also requires Python 3.11+ and `uv` in the Web
sandbox. This path is supported by design and explicitly untested. Do not use
Configuration Sync as a complete Power installer: custom cloud Powers accept
text only and at most 50 files, while PK-Stack exceeds that shape.

## Set up a project

### Preferred current-session path

In a current Kiro IDE or CLI session, invoke:

```text
/setup-pstack
```

The skill resolves `scripts/setup_pstack.py` relative to its own loaded
`SKILL.md`. It never executes a repository-supplied `./projectctl` as a setup
authority. Its first operation is equivalent to:

```bash
python3 /absolute/path/to/pk-stack-power/skills/setup-pstack/scripts/setup_pstack.py \
  --root "$PWD" \
  --dry-run \
  --output json
```

On a fresh project, review the preview and run the same Power-local shim without
`--dry-run`:

```bash
python3 /absolute/path/to/pk-stack-power/skills/setup-pstack/scripts/setup_pstack.py \
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
same Kiro agent session and switch through the Power-enabled setup agent. Use
the IDE agent picker, or in CLI v3 run:

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
required Python modules, the complete inventory-bound source skill catalog,
steering, agent/hook templates, and the runtime lock. The current catalog has
49 source skill directories. A missing required Power asset returns a
structured error before any target file is written.

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
python3 /absolute/path/to/pk-stack-power/skills/setup-pstack/scripts/setup_pstack.py \
  --root "$PWD" \
  --dry-run \
  --update-managed \
  --output json
```

Only after explicit approval, apply the same reviewed operation:

```bash
python3 /absolute/path/to/pk-stack-power/skills/setup-pstack/scripts/setup_pstack.py \
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
- four Power-managed agents, all 48 live workspace skills, four steering files,
  and two hook files; the PK-Stack repository separately carries the
  `pstack-maintainer` CI agent outside the reusable Power;
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
doctor checks every one of the other 48 skills materialized in `.kiro/skills/`.
The controller cache retains the complete 49-skill source tree, including the
setup shim.

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

The installed skill entrypoints are grouped below; the [complete 45/45 upstream
mapping](upstream-skill-parity.md) names every route and its disposition.

```text
/architect <architecture problem>
/arena <artifact and gradeable criteria>
/how <subsystem>
/why <decision or behavior>
/tdd <behavior change>
/technical-writing <reader and task>
/maintain-pk-stack <upstream maintenance request>
/swarm <bounded coverage or race request>
/model-council <intent, evidence, and review rubric>
/principles <engineering decision>
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

## Check the pinned upstreams

In the combined PK-Stack source repository, requested or scheduled maintenance stays in the
current session through `/maintain-pk-stack`. Its deterministic first predicate is:

```bash
.pstack/bin/projectctl upstream check \
  --manifest maintenance/upstreams.json \
  --power-root powers/pk-stack \
  --output json
```

The command reads one strict local manifest and its required
`maintenance/upstream-reviews.json` ledger, contacts only `https://api.github.com`, and uses an
optional `GITHUB_TOKEN` only as the HTTP Authorization value. The ledger binds the exact source
identity, genesis, a contiguous prior/new commit-and-subtree chain, each transition's
`inventory_sha256`, and one A/B/C disposition with a nonempty bounded rationale for every changed
path. A pin-only manifest edit, stale chain, wrong identity or digest, or missing, duplicate, extra,
or malformed disposition fails before it can claim a source is current. The aggregate response
accounts for every configured source and deterministically names the first source eligible for a
serialized maintenance transaction. A focused reproof uses that exact identifier:

```bash
.pstack/bin/projectctl upstream check \
  --manifest maintenance/upstreams.json \
  --power-root powers/pk-stack \
  --source-id <source-id> \
  --output json
```

Each source owns a distinct pin, parity artifact, genesis/transition chain, and provenance file.
One proposal and acceptance transaction may advance only one source; every other source remains
byte-for-byte unchanged. A later run selects the next drifted source.

For each selected source, the service reproofs the pinned and current commit/subtree identities,
requires a bounded
fast-forward, reconciles GitHub's compare records against exact recursive subtree trees, and
returns a bounded untrusted text-patch inventory. A canonical `inventory_sha256` binds that
inventory to its base and head. Unified patch hunk and body counts must exactly match GitHub's
additions/deletions. Each text patch is then applied to the fetched, Git-OID-verified pinned blob;
the resulting bytes must hash to the exact current subtree blob (added text starts empty and
removed text ends empty). Every changed path exposes old/new type, mode, SHA, and size. Regular
`100644` and `100755` blobs are supported, including executable-mode changes; symlinks and
submodules fail closed. A missing patch is rejected for semantic content changes; only zero-count
top-level raster assets, exact-blob pure renames, and exact-blob mode-only changes are permitted. The detector
lists unavailable raster paths under `review_constraints.unavailable_binary_paths`, and acceptance
requires disposition B for each. No upstream content is fetched outside the bounded API evidence or
executed. The whole ledger chain is checked locally and only its latest transition is remotely re-proved, so the
request budget stays constant; committed Git history is the older-ledger tamper authority.
The 100-file review ceiling applies to the exact changed paths in the configured source subtree,
not unrelated repository-wide compare records. Those unrelated records are ignored only after the
exact pinned/current subtree inventories establish the source-scoped path set. GitHub exposes at
most 300 files for a comparison; a response at that ceiling is ambiguous and fails closed, as does
any response that omits one of the independently derived source paths or its required patch.
The ledger is capped at both 8 MiB and 512 transitions. The representative 27-path, 400-byte-rationale
shape supports the full 512 entries (about 9.8 years weekly); maximum-length rationales can reach
the byte limit around 2.7 years. An explicit reviewed, tamper-evident archive migration is required
before either limit—PK-Stack never silently discards review history.
Supplying `--power-root` also runs an
ownership-aware `--dry-run --update-managed` bootstrap preview and reports canonical/generated
parity without writing.

Drift exits 1 and is the expected baseline for a source-scoped maintenance goal. Malformed or oversized data,
truncation, a missing comparison page, identity disagreement, non-fast-forward history, unsafe
paths, a network failure, or generated drift fails closed. The skill classifies every path as
adapt, exclude, or provenance-only, updates canonical sources before regeneration, and stages
provenance only after that implementation passes. It writes the exact transition object to
`.pk-stack-maintenance/proposal.json` and appends a canonical
`pk-stack-upstream-review` JSON comment to provenance. That final comment binds the source,
repository/path, prior/new commit and subtree identities, and inventory digest; its marker count
and full ordered marker list must match the ledger transitions 1:1. The ledger and markers are the
machine-authoritative transition record; surrounding provenance prose is descriptive. Ordinary
checks require exact marker/ledger equality. Acceptance alone permits exactly one proposal-bound
tail marker during its preproof; extra, replaced, or reordered markers fail closed. Then the
skill previews acceptance:

```bash
.pstack/bin/projectctl upstream accept \
  --manifest maintenance/upstreams.json \
  --power-root powers/pk-stack \
  --proposal .pk-stack-maintenance/proposal.json \
  --expected-head <exact-head-commit> \
  --dry-run \
  --output json
```

After reviewing the preview, omit `--dry-run` to apply the same expected-head-bound operation. The
service re-fetches the proof, appends the normalized transition and advances the manifest pin as a
recoverable journaled update, then removes `.pk-stack-maintenance`. It does not edit provenance or
Power files. A stale, replayed, future, malformed, or symlinked proposal fails closed. The
five-attempt goal budget uses attempt 1 for the mandatory pre-edit failure, leaving four bounded
repair-and-secretless-verify pairs. Only a later pass of the same source-bound command permits a
claim that selected source is current. The aggregate command must pass before claiming that all
configured sources are current.

## Create and prove feature contracts

Feature slugs use lowercase letters, digits, and single hyphens. A contract
describes observable user behavior, the expected system path, every user
entrypoint and its drive recipe, proof and cleanup boundaries, gotchas, and an
optional argv-style verifier.

### Create one structured draft

```bash
.pstack/bin/projectctl feature generate account-lookup \
  --title "Account lookup" \
  --behavior "A caller can retrieve an account status." \
  --expected-path "CLI -> gateway -> account service -> response" \
  --command "uv run pytest tests/test_account_lookup.py -q" \
  --sub-feature "lookup-status=Return the current account status." \
  --sub-feature "missing-account=Return the public not-found result." \
  --entrypoint "cli=Run the account lookup CLI command." \
  --drive "cli=Run account lookup <id> --format json in the isolated fixture." \
  --entrypoint-proof "cli=Exit zero and JSON contain the requested account status." \
  --gotcha "A database read alone does not exercise the public CLI." \
  --evidence-boundary "Retain bounded argv, exit status, and redacted JSON output." \
  --cleanup-boundary "Remove only the fixture account; retain proof artifacts." \
  --output json
```

This writes `Wiki/features/account-lookup.md` with `draft: true` without
running its command. Repeatable structured values use `identifier=text`.
Every `--entrypoint` ID must have one same-order `--drive` and
`--entrypoint-proof`; there must also be at least one sub-feature and gotcha.
An omitted command is allowed for a draft and produces a validation warning.
Add an existing knowledge link with, for example, `--related
../architecture/account-boundary.md`; related paths resolve from the feature
file and must remain inside the project and exist at validation time.

For compatibility, a call that omits *all* structured fields still creates a
readable schema-1 record and returns `migration_required: true`. New workflows
should not use that fallback. `feature validate` keeps legacy records valid but
warns until they are migrated.

Inspect the contract:

```bash
.pstack/bin/projectctl feature show account-lookup --output json
.pstack/bin/projectctl feature list --output json
.pstack/bin/projectctl feature validate --output json
```

`feature validate` checks strict frontmatter types, duplicate YAML keys, the
exact ordered required sections and headings, location and slug consistency,
related links, and the verifier hazard policy. It does not run verifier
commands. Feature Markdown is capped at 512 KiB and read as bounded strict
UTF-8 with concurrent size and identity checks.

### Prove one record now

Add `--ready` to the complete structured command when its verifier should run
now. Projectctl builds and parses the exact candidate Markdown before the
verifier, requiring every field and entrypoint pairing to round-trip unchanged.
Ready-contract related paths must already be contained in the project and
present. On pass, projectctl repeats candidate preflight, writes `draft: false`,
and returns `initial_verification`. Invalid input runs no proof; a failed proof
exits 1 with `created: false` and leaves a new target absent.

To replace an existing contract deliberately, add `--overwrite --ready`.
Overwrite refusal happens before proof, and a failed proof leaves the existing
file unchanged. Preserve any manual edits before approving an overwrite.

### Seed the initial three-to-five-feature map

The creation workflow should interview the repository and write a bounded JSON
definition with exactly one top-level `features` array and three to five
records. Every record has exactly these keys:

| Key | Exact value |
| --- | --- |
| `slug`, `title`, `behavior`, `expected_path` | Non-empty strings |
| `command` | A command string or non-empty argv string list |
| `related` | A list of feature-relative path strings |
| `sub_features` | Non-empty `{identifier, behavior}` objects |
| `entrypoints` | Non-empty `{identifier, user_path, drive, observable}` objects |
| `gotchas` | Non-empty single-line string list |
| `evidence_boundary`, `cleanup_boundary` | Non-empty strings |

Unknown or duplicate JSON keys, duplicate slugs, malformed UTF-8, an unsafe
path or command, and files over 256 KiB fail closed. Generate the map and name
the one representative behavior to prove during creation:

```bash
.pstack/bin/projectctl feature generate-map feature-plan.json \
  --representative account-lookup \
  --output json
```

Projectctl validates all records, runs exactly the representative verifier
once, revalidates the definitions, writes that record published, and leaves
the other two to four records draft. One representative proof is enough to
prove the newly created harness can run; it is not evidence that the rest of
the map works. Projectctl snapshots every target before proof, then stages the
full batch under the shared feature mutation lock. Inside that lock it compares
the exact bytes, rechecks workspace and symlink containment, and uses atomic
no-clobber creation for new targets. A later replacement or directory-sync
error rolls every earlier target back instead of leaving a mixed initial map.
`/maintain-verification-skill` must exercise every feature and entrypoint.
As each remaining contract passes, publish it without re-entering its content:

```bash
.pstack/bin/projectctl feature publish account-update --output json
.pstack/bin/projectctl feature publish account-delete --output json
.pstack/bin/projectctl feature validate --output json
```

Each `feature publish` runs only that draft's stored verifier and changes
`draft` to `false` only on pass.

### Migrate a legacy record

`feature migrate` preserves the legacy title, user behavior, expected path,
command, related paths, and draft state. Supply only the new structural fields:

```bash
.pstack/bin/projectctl feature migrate account-lookup \
  --sub-feature "lookup-status=Return the current account status." \
  --entrypoint "cli=Run the account lookup CLI command." \
  --drive "cli=Run account lookup <id> --format json in the isolated fixture." \
  --entrypoint-proof "cli=Exit zero and JSON contain the requested status." \
  --gotcha "A database read alone does not exercise the public CLI." \
  --evidence-boundary "Retain bounded argv, exit status, and redacted JSON." \
  --cleanup-boundary "Remove only fixture state; retain proof artifacts." \
  --output json
```

A published legacy record is re-proved before replacement. Failure or any
exact byte change during proof preserves the observed legacy file. A draft
migrates without running its command and still needs `feature publish` later.
Automatic migration accepts only a byte-canonical projectctl schema-1 record.
It refuses duplicate known sections, pre-H2 prose, custom Verification prose,
YAML comments or formatting, unmodeled frontmatter or verification keys, and
extra level-2 sections so operator-authored content cannot be silently
discarded; preserve those bytes in a manual schema-2 migration.

`feature publish` snapshots exact bytes around its verifier and changes only
the YAML `draft` scalar while holding the shared feature mutation lock.
Accepted operator preamble and Verification prose stay byte-for-byte intact;
a concurrent edit makes publication fail rather than overwrite that edit.

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

## Record and audit a decision trail

The default evidence trail is local runtime state and remains ignored:

```bash
.pstack/bin/projectctl evidence append account-repair \
  --requirement "Suspended accounts return their status through the public CLI." \
  --evidence "The isolated CLI drive returned suspended with exit code zero." \
  --decision "Keep the status mapping and remove the obsolete rejection branch." \
  --verification "The account-lookup verifier passed twice after repair." \
  --verdict VERIFIED \
  --artifact artifacts/account-repair/result.json \
  --output json

.pstack/bin/projectctl evidence audit account-repair --output json
```

The first append creates
`.pstack/state/evidence/account-repair/decision-log.jsonl`. Each later append
receives the next contiguous sequence and a strictly increasing UTC timestamp.
`--verdict` accepts exactly `VERIFIED`, `NOT VERIFIED`, or `INCONCLUSIVE`.
`--artifact` must be a canonical workspace-relative existing regular file.
Optionally add `--artifact-sha256` with a previously inspected 64-character
lowercase digest to bind the event to those exact bytes; audit detects later
artifact drift. Bulky evidence stays in that named artifact rather than in the
JSONL field. Dot/dotdot aliases, backslashes, and other noncanonical spellings
are rejected even when they happen to resolve inside the workspace.

The event schema and encoding are exact. Text fields are non-empty and bounded;
known private-key, provider-token, bearer-token, credential-URL, and
secret-assignment shapes are rejected without echo. That is a safety screen,
not a complete secret detector. Redact credentials and personal data before
calling the command. Record requirements, visible evidence, decisions, and
verification—not private chain-of-thought, model transcripts, or unrelated
conversation history.

Committed evidence is never inferred from the slug or a target path. It needs
both opt-ins and the one exact Wiki location:

```bash
.pstack/bin/projectctl evidence append account-repair \
  --requirement "The release has an independent acceptance verdict." \
  --evidence "The immutable review artifact returned ACCEPT." \
  --decision "Release the accepted snapshot." \
  --verification "The final acceptance suite passed on the reviewed tree." \
  --verdict VERIFIED \
  --committed \
  --target Wiki/evidence/account-repair/decision-log.jsonl \
  --output json

.pstack/bin/projectctl evidence audit account-repair \
  --committed \
  --target Wiki/evidence/account-repair/decision-log.jsonl \
  --output json
```

The audit checks strict UTF-8 canonical JSONL, the exact key set, the 4 KiB
field, 24 KiB event, 2,048-event, and 4 MiB file bounds, monotonic sequence and
timestamps, current reference containment/existence, and optional hashes. The
append path is lock-serialized and durably atomically replaced. A planted
empty file is invalid rather than a successful zero-event audit. Parsing uses
raw LF bytes: CRLF and mixed separators fail, while a Unicode line separator
inside one JSON string remains content in that event. The trail is
append-only by workflow convention but is not signed or tamper-proof; preserve
superseded decisions as later events rather than rewriting history.

## Run a verified goal

### Preferred current-session path

In the current Kiro agent session:

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

A completed native Kiro spec can supply a third bridge after it has non-empty requirements or bug
analysis, design, and tasks. Prefer binding it to an already published feature verifier:

```bash
.pstack/bin/projectctl goal bind-spec account-lookup \
  --feature account-lookup \
  --output json
```

That creates `.kiro/specs/account-lookup/pstack-verification.json`:

```json
{
  "feature": "account-lookup",
  "schema_version": 1
}
```

If no reusable feature applies, bind one reviewed command with `goal bind-spec --command`; do not
choose that shortcut merely to avoid creating the feature map. An identical binding is idempotent,
while replacement requires `--overwrite` after reviewing both contracts.

Then start it:

```bash
.pstack/bin/projectctl goal start \
  "Implement the account lookup spec" \
  --spec account-lookup \
  --max-attempts 4 \
  --output json
```

Do not combine `--feature`, `--command`, and `--spec`. Spec names cannot contain
path separators or traversal. At start, projectctl snapshots the selected intent artifact
(`requirements.md` or `bugfix.md`), `design.md`, and the bridge. It checks all three before and
after every verifier invocation; drift rejects or discards proof without consuming an attempt.
`tasks.md` must exist and be non-empty at binding time but is deliberately not hashed, so Kiro can
continue updating its native task state. Attempt budgets are 1 through 20.

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
provenance, spec artifact snapshots when applicable, a contract digest, attempt budget, last
result, and append-only history. The digest and semantic checks detect command/history tampering; they
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

With `okn` installed, validation composes feature-map validation with `okn validate Wiki`; a pass
requires both. Broad search
also requires it:

```bash
.pstack/bin/projectctl knowledge search "account suspension" --output json
```

That delegates to `okn search Wiki <query>`. PK-Stack does not implement a
fallback OKF graph or broad text index. The feature map is the first context layer; use broad OKF
search only for architecture, decisions, concepts, or operations that the narrow record cannot
answer. Native `/knowledge` may index the same Wiki, but it is not the canonical source or checker.
`okfcli/okf` is an optional explicitly named advisory CI/SARIF oracle over a disposable,
immutable, symlink-free copy, never a transparent runtime fallback for `okn` validation, search,
provenance, or lifecycle behavior. Version 0.5.0 rejects the authoritative OKF 0.2 explicit-offset
`stale_after` form, so its result cannot gate normative conformance.

PK-Stack accepts the pinned `okn` 0.13.0 search response, which has no top-level management status,
and newer compatible responses only when an emitted `status` is exactly `managed`. An explicit
`unmanaged` or unknown status fails before returned sources are trusted. Self-maintenance tracks
OpenKnowledge's versioned `packages/cli/schemas/v1` tree as `openknowledge-cli-contract`; it does
not track or import the broader runtime implementation. Validation, search-context, common, and
CLI-error schemas may inform the process boundary, while deployment, job, runtime, and release
interfaces remain excluded.

Use `/okf` for one explicit Wiki mode: produce new durable knowledge, maintain concepts affected by
a current change, or consume bounded context. The skill adapts the method from
`scaccogatto/okf-skills` to Kiro and PK-Stack's trust boundary. It does not execute the upstream
Claude hooks, mine agent transcripts, or install a second validator, MCP server, or visualizer.

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
python3 /absolute/path/to/pk-stack-power/skills/setup-pstack/scripts/setup_pstack.py \
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

First select the workspace `pstack` agent with the Kiro IDE agent picker or CLI
`/agent swap pstack`. If Kiro has not discovered the new workspace agent or
`.kiro/skills/`, open one fresh pre-goal IDE chat/Agent Focus session, or start
one new CLI v3 chat in the same repository with `kiro-cli chat --v3 --agent
pstack`. Do not switch to V2, start an external ACP host or `kiro-cli acp`,
modify the global default agent, or invent prose-only goal state. Once
discovered, invoke `/verified-goal` normally in that current Kiro agent
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
