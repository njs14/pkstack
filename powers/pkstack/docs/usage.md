# Usage

PKStack adds a repeatable finish to Kiro development: store the command that
checks a task, record the initial failure, repair in the current Kiro session,
and retain the passing result. Project knowledge stays in the repository for
later sessions. This guide works for CLI-only users and IDE users.

## Prerequisites

- Kiro CLI with v3 support or Kiro IDE, installed and signed in;
- [`uv`](https://docs.astral.sh/uv/) on `PATH`;
- a reviewed PKStack checkout or locally built wheel; and
- a project you are allowed to modify.

The launcher and locked controller require Python 3.11+. The explicit `--python ">=3.11"`
request keeps uvx from choosing an older system Python. uv can acquire a supported
interpreter without replacing macOS system Python. Initial setup may need network
access to download Python and dependencies; [uv documents automatic Python
acquisition](https://docs.astral.sh/uv/guides/install-python/). Resolve runtime acquisition
failures before continuing. The older Power-local `python3` setup script remains supported.

Check uv:

```sh
uv --version
```

For the CLI path, also check:

```sh
kiro-cli --version
kiro-cli chat --v3 --help
```

PKStack inherits the model and effort selected in Kiro. It does not store a
model choice in `projectctl` or require a particular provider for interactive
work. Historical acceptance model choices describe those runs, not a default.
Use the native `/model` and `/effort` pickers if you want to change that selection;
available choices depend on your runtime, account, and selected model.

## CLI Powers and project setup

CLI v3 supports Powers. Kiro documents [automatic pickup of IDE-installed
Powers](https://kiro.dev/docs/cli/v3/new-features/#powers-auto-pickup), and
[`/powers`](https://kiro.dev/docs/reference/slash-commands/#powers) lists them
inside a local v3 session. Start `kiro-cli chat --v3` with the default agent to
inspect that list.

The [CLI installation guide](https://kiro.dev/docs/powers/installation/#cli)
directs Power installation through the IDE or manual Power configuration. It
does not document an install subcommand for `/powers`. For PKStack's private
repository, use the [IDE folder import](#install-with-kiro-ide) to register the
reviewed Power, or use the terminal setup below to prepare a project directly.

Power registration makes the package available to Kiro. Project setup creates
the workspace agent, skills, controller, and Wiki. A Power appearing in
`/powers` does not prove that its setup skill is available in the current
session. Invoke `/pkstack-setup` where Kiro exposes that Power-local skill;
otherwise use the uvx terminal setup below. After setup, select the workspace
`pkstack` agent. Its `includePowers: false` setting disables automatic Power
inclusion; PKStack explicitly loads its reviewed workspace skills. Other skill
scopes may still contribute. Inspect the effective inventory with `/config skills`
under the selected agent; this setting does not establish skill isolation.

## Choose the Power source

The **source** is the reviewed Power containing the installer. The **target** is
your application, which will receive `.kiro/`, `.pkstack/`, and Wiki assets.
Keep the source available for later managed updates.

If you have not cloned PKStack, run:

```sh
git clone https://github.com/njs14/pkstack.git
cd pkstack
```

From the root of that checkout, capture the absolute Power path:

```sh
export PKSTACK_POWER="$PWD/powers/pkstack"
test -f "$PKSTACK_POWER/plugin.json"
test -f "$PKSTACK_POWER/skills/pkstack-setup/scripts/setup_pkstack.py"
export PKSTACK_PACKAGE="$PKSTACK_POWER"
```

For an unpacked standalone Power instead, open a terminal in the folder that
contains `plugin.json` and capture that folder:

```sh
export PKSTACK_POWER="$PWD"
test -f "$PKSTACK_POWER/plugin.json"
test -f "$PKSTACK_POWER/skills/pkstack-setup/scripts/setup_pkstack.py"
export PKSTACK_PACKAGE="$PKSTACK_POWER"
```

These variables last for this terminal session; restore the source path if you
open another.
Never derive the source from the target's `.pkstack/` cache. Review the Power
before running it through uvx, its setup script, or importing it in Kiro.

### Use a local wheel

From a reviewed repository checkout, build a wheel without publishing it:

```sh
uv build --wheel --no-sources --out-dir dist powers/pkstack
```

Set the absolute path to the wheel produced by that build, using its actual filename:

```sh
export PKSTACK_PACKAGE="/absolute/path/to/dist/pkstack-0.4.3-py3-none-any.whl"
test -f "$PKSTACK_PACKAGE"
```

A wheel includes the installer, workspace assets, and CLI. Keep the Power folder for
Kiro's folder-import flow and the first-task example; a wheel is not a Power folder.
The commands below accept either this wheel or the reviewed checkout directory through
`--from`. Do not use bare `uvx pkstack`: that would select a package from a registry.
No publishing or global tool installation is needed. Installing a wheel resolves its
package requirements; it does not install the development `uv.lock`. After setup, project
operations use the separately shipped, locked controller runtime.

<a id="import-and-bootstrap"></a>

## Install with Kiro CLI

No IDE import is required. In this same terminal, replace the example path below
with your application's root directory. Capture and check the target before
previewing changes:

```sh
cd "/absolute/path/to/your/project"
export PKSTACK_PROJECT="$PWD"
: "${PKSTACK_PACKAGE:?Select the reviewed checkout or local wheel first}"
printf 'Package: %s\nTarget: %s\n' "$PKSTACK_PACKAGE" "$PKSTACK_PROJECT"
```

Confirm the target shown is your application, not the PKStack checkout. To try
PKStack before changing an existing application, use the disposable project in
[the first-task guide](first-task.md) instead.

Preview setup:

```sh
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack --project "$PKSTACK_PROJECT" \
  setup --dry-run --output json
```

A dry run previews target changes without writing managed target files. It can
still populate runtime caches and acquire dependencies; it is not an offline
or cache-free operation. Review the target path and listed files. Non-empty
`pending_updates`, `stale_managed`, or `conflicts` block setup: inspect them
before proceeding; use the refresh section for an existing installation.

When the preview is acceptable, apply it:

```sh
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack --project "$PKSTACK_PROJECT" \
  setup --output json
```

From the target root, verify the installation:

```sh
cd "$PKSTACK_PROJECT"
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack version --output json
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack doctor --output json
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack knowledge validate --output json
```

Expect `ok: true` from doctor and knowledge validation. Doctor checks the
installation; knowledge validation checks local metadata and links without a
model. Neither proves that Kiro has repaired your application.

Launch Kiro from the target root:

```sh
kiro-cli chat --v3 --agent pkstack
```

## Install with Kiro IDE

1. Choose **Powers → Add Custom Power → Import power from a folder** and select
   the reviewed Power folder containing `plugin.json`. Review the package and
   choose **Install**.
2. Open your target application in Kiro. In its chat or Agent Focus session,
   invoke `/pkstack-setup`.
3. Review the preview and approve the intended changes. Setup reports doctor
   and local validation results; resolve failures before starting work.
4. Select the workspace `pkstack` agent before the next workflow message.

If the imported Power is not discoverable, use the terminal setup above. If the
new agent or skills are absent, follow [agent and skill discovery](#attach-the-generated-agent)
before opening a replacement chat.

## First success

Use `/pkstack <task>` for your own work, or [try one failing task](first-task.md)
with either surface. That example supplies a repeatable verifier and explains
how to inspect the failure, Kiro's repair, and the stored passing result.

Use `uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack <command>` for project operations. The
launcher forwards them to the selected project's `.pkstack/bin/projectctl`, which uses
the shipped locked runtime under `.pkstack/projectctl/`. Direct use of that wrapper and
the existing `projectctl` and `pkstack-setup` package entrypoints remains supported.
The root `./projectctl` convenience wrapper, when present, is not used for delegation.

The launcher defaults to the current directory and never searches parent directories.
To select another project, put `--project /absolute/path` before the command. A forwarded
`--root` is rejected: use `--project` so the runtime and operation target agree. Setup
and upgrade use the selected package's assets; other commands use the installed controller.
A missing or altered runtime fails before delegation, with no automatic install or upgrade.
The uvx tool environment's injected leading `PATH` entry is removed before delegation so
application verifiers retain their own executable and import environment.

```sh
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack --version
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack version --output json
```

The first command reports the launcher package version; the second reports the installed
project controller version. They may differ until an explicit managed upgrade. Existing
project command output, exit codes, and cancellation behavior remain unchanged.

### Attach the generated agent

The bootstrap conversation does not automatically select the new profile. In the
IDE use the agent picker to select the workspace `pkstack` agent. In CLI v3,
inspect the available agents and select it in the current conversation:

```text
/agent
/agent swap pkstack
/config skills
```

The bare `/agent` opens the picker; `/config skills` shows the selected session's
read-only skill inventory. On CLI 2.21.1, `/agent list` was interpreted as an
agent named `list`, so use the bare picker. Agent files added during the audit
were selectable without restarting; that does not prove skill hot reload.

If a new agent is still absent, check the setup report and project root. If
newly installed skills remain absent after selecting `pkstack`, open one fresh
chat in the same project and select it again. The CLI fallback is:

```sh
kiro-cli chat --v3 --agent pkstack
```

Prefer the same-conversation handoff. A managed refresh uses `/agent swap default`
before setup and `/agent swap pkstack` afterward. The primary profile
asks before ordinary writes and canonical controller commands. Delegated
architect, reviewer, and verifier profiles omit `write` and `shell`; they
inspect and report to the primary session. These Kiro permissions complement
the controller's checks but are not an operating-system sandbox.

## Commands

| Command | Use it for |
| --- | --- |
| `/pkstack` | Route a task through planning, implementation, verification, and review |
| `/pkstack-setup` | Preview installation or refresh when the imported Power is discoverable |
| `/pkstack-maintain` | Review upstream changes to the Power |
| `/pkstack-verified-goal` | Repair against one stored executable check |
| `/pkstack-model-council` | Compare independent reviews and resolve findings |
| `/pkstack-principles` | Apply the engineering-principles catalog |

Imported skills keep their names. The [sources guide](curated-skills.md) explains
their roles and handoffs. For a runnable example, [try one failing task](first-task.md).

## Save a recurring request in Kiro

Kiro documents saved prompts for requests you use repeatedly. A saved prompt
carries the task and its context; a PKStack skill supplies the workflow. For
example, you could save the complete account-ID request from the
[first-task guide](first-task.md) instead of retyping it.

The [CLI prompt guide](https://kiro.dev/docs/cli/chat/manage-prompts/) describes
workspace prompts in `.kiro/prompts/` and invocation with `@<name>`. File-based
prompts do not accept template arguments. Prefer a distinctive project-specific
name because workspace prompts take precedence over global prompts with the
same name.

Keep these prompts user-owned. PKStack does not install a prompt catalog or
manage your `.kiro/prompts/` files. Refer to the existing PKStack skill rather
than copying its verification loop into a prompt. A saved request does not
select the `pkstack` agent, bind a native Spec, or establish a passing result
by itself; confirm the intended skill actually loads and inspect the stored
verifier evidence.

**Installed CLI boundary:** on macOS with Kiro CLI 2.21.1 in v3 mode,
`/prompts` opened a selection menu that included skills, with a right-arrow
control to view details. The general guide's `/prompts details <name>` syntax
instead submitted an ordinary model request in our probe; do not use it as a
read-only preview on this build. Saved-file creation, `@name` expansion, and
skill activation through an expanded request have not been verified here.
Use the native controls exposed by your runtime and inspect the content before
submission. The [first-task guide](first-task.md) retains direct skill invocation;
local saved-prompt behavior in Kiro IDE is also unverified.

## The short version

![Return from native Kiro planning to PKStack, run the stored verifier, and repair while attempts remain.](artifacts/pkstack-task-workflow.png)

[Open the interactive workflow](artifacts/pkstack-task-workflow.html).

Kiro CLI v3 and the Kiro IDE agent panel are the primary surfaces. Kiro Crew is
optional. Kiro Web can consume committed workspace assets, but its end-to-end
path has not been tested. The selected IDE and CLI profiles have recorded
command-approval checks; that does not prove every permission rule. Normal work stays
in the current session. Only `projectctl knowledge search` starts an isolated,
read-only Kiro ACP worker for bounded retrieval. PKStack does not claim that
CLI v3 provides Kiro's native `/goal` command.

## Plan and bind work

All planning entered through PKStack uses the shared `grilling` interview method:
inspect available facts first, ask the unresolved questions in dependency order,
explain consequential trade-offs, recommend an option, and reuse settled answers.
Planning helpers consume that context instead of starting another mandatory
interview. `/grilling` exposes the method, `/grill-me` starts a focused interview,
and `/grill-with-docs` also requests knowledge capture during the interview when
writes are permitted. A standalone decision interview stays conversational unless
you ask for an implementation plan.

For nontrivial work, use Kiro's native planner before the PKStack loop. PKStack's
handoff carries the settled context and directs the native workflow to read
`.kiro/skills/grilling/SKILL.md`; an already active planning mode is reused.

- **Conversational Plan:** CLI v3 `/plan <request>`, or Plan in the IDE workflow
  picker. The plan stays in the conversation and has no required `tasks.md`.
- **Spec:** CLI v3 `/spec new <name>`, then `/spec <name>` to resume; IDE
  **Build with spec** or the workflow picker. Choose standard Spec for unfamiliar
  or high-risk work, or Quick Spec for a bounded change whose shape is clear.

Native [Plan is read-only](https://kiro.dev/docs/specs/plan/): use its available
reading, search, and code-intelligence tools. Defer file writes, shell commands,
MCP calls, prototypes, and knowledge validation. For a plan-only request, return
the conversational plan and stop. Kiro owns approval and the execution handoff;
presenting a plan does not authorize implementation.

For a Spec with an existing `requirements.md`, optionally inspect unclear or
complex requirements before moving on:

```text
/spec analyze_requirements <feature-name>
/spec view <feature-name> requirements
/spec view <feature-name> design
/spec view <feature-name> tasks
```

[Requirements analysis](https://kiro.dev/docs/specs/analyze-requirements/) may
update `requirements.md` as questions are resolved. Reuse those findings in the
shared interview; skip analysis for a Bug Fix package containing only `bugfix.md`.
View only documents that exist. Viewing a document does not approve it or bind
an executable verifier.

After explicit approval of an implementation plan, PKStack automatically uses
`domain-modeling` and `okf` to save reusable definitions and decisions at the first
permitted write step under normal Kiro permissions. Pending capture stays in the
conversation while Plan is read-only. An explicit no-write instruction takes
precedence. Capture references the planning context and updates existing entries
instead of copying the entire plan or duplicating records on repeated approval.
Denied writes or failed validation leave capture visibly incomplete.

Kiro owns requirements or bug analysis, design, tasks, dependency waves, and
native task execution. Only Spec-backed work refines the native task file. Once
the Spec is approved for implementation, return to `pkstack` and bind its artifacts
to an executable verifier. For a new, still-failing feature:

```sh
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack goal bind-spec account-lookup \
  --command "python3 -m unittest discover -s tests -v" --output json
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack goal start "Repair account lookup" \
  --spec account-lookup --max-attempts 4 --output json
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack goal verify --output json
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
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack feature generate account-lookup \
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
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack feature generate account-lookup \
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
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack feature show account-lookup --output json
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack feature list --output json
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack feature validate --output json
```

For one to five features, prepare one JSON plan and prove only the named
representative during generation:

```sh
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack feature generate-map feature-plan.json \
  --representative account-lookup --output json
```

The other records remain drafts until each verifier passes. Publish and verify
them separately:

```sh
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack feature publish account-lookup --output json
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack feature verify account-lookup --output json
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
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack goal start \
  "Repair account lookup" \
  --feature account-lookup --max-attempts 4 --output json
```

Or supply one reviewed command:

```sh
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack goal start \
  "Repair account lookup" \
  --command "uv run pytest tests/test_account_lookup.py -q" \
  --max-attempts 4 --output json
```

Inspect and verify:

```sh
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack goal status --output json
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack goal verify --output json
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
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack goal clear --output json
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
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack knowledge status --output json
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack knowledge validate --output json
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack knowledge search "account suspension" --budget 1200 --model auto --output json
```

`knowledge status` reports the corpus layout and Kiro retrieval availability.
`knowledge validate` runs locally without Kiro, a model, or `okn`. It composes
feature validation with minimal knowledge metadata and local Markdown links:
a nonempty `type`; nonempty `title` and `description` when present; `tags` as a
list of nonempty strings when present; and optional `okf_version: "0.2"`.
Unknown metadata is preserved. CommonMark inline/reference links and images,
local paths, and Markdown heading anchors are checked. External links are not
fetched; raw HTML IDs, footnotes, plugin-specific fragments, full OKF
conformance, and graph semantics are outside this check.

Search reads `Wiki/knowledge/`, `Wiki/features/`, and `.kiro/specs/`. It excludes
`Wiki/work/` and does not copy native skills or instructions into the corpus.
The worker uses native Kiro CLI authentication and the official Python ACP
client pinned to `agent-client-protocol==0.12.1`. The current adapter supports
POSIX and is gated to Kiro CLI 2.21.1 with embedded KAS 0.58.7; an unsupported
or unavailable runtime fails explicitly while local validation remains usable.
There is no alternate backend or silent model fallback. Optional `--model`
defaults to `auto`, a first-class selection using Kiro-managed routing. Receipts preserve
`model: "auto"`; `resolved_model: null` means the underlying model was not disclosed.
See [Auto model guidance](kiro-v3-compatibility.md#auto-as-its-own-model-selection).

`--budget` caps returned context using UTF-8 JSON bytes divided by four; it does
not cap or measure the worker's internal token use, which is unreported. A
successful search returns `schemaVersion: "2"` and `mode: "kiro-acp"`. The
`context` object contains `answer`, `sources` (each with `path`, `quote`,
`lineStart`, `lineEnd`, and `contentSha256`), `uncertainties`, and `incomplete`.
The host verifies unique exact quotes and an unchanged corpus. Invalid, excluded, over-budget, or incomplete results
are rejected after at most one bounded correction.

The host also limits protocol input before SDK parsing to 1 MiB per frame and
16 MiB per task, including messages that are not returned as context. A prompt
has a 120-second deadline; cancellation sends have a 0.5-second deadline and
brief retries before bounded process-group cleanup. These are execution limits,
separate from the returned-context budget.

Use `/okf` to produce, maintain, or consume durable knowledge. Native Kiro
`/knowledge` may index the same files; project files remain authoritative.
The earlier optional `okn` backend and `--require-okn` flag have been removed.
See the [knowledge runtime decision](../../../Wiki/knowledge/pkstack/native-spec-and-okn.md).

## Refresh managed files

Leave the restricted `pkstack` profile before refreshing. CLI v3 2.21.1 names
its bundled default agent `default`:

```text
/agent swap default
```

This swap does not make an imported Power available. Invoke `/pkstack-setup`
only if it is discovered in that context. Otherwise use uvx from a terminal, with `PKSTACK_PACKAGE` pointing to the reviewed
newer wheel or checkout. Preview the explicit upgrade:

```sh
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack upgrade --dry-run --output json
```

Review the explicit update preview before applying it:

```sh
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack upgrade --output json
```

After setup, return to the same conversation with `/agent swap pkstack`.
Do not add a cached setup skill to `.kiro/skills/` to force discovery.

`upgrade` uses the installer's `--update-managed` operation and replaces only a path that still matches its prior receipt
hash. It never overwrites a user edit. `stale_managed` paths are not deleted
automatically; preserve or remove each exact path by a separate project
decision. The cached controller's setup command fails unless an explicit,
reviewed `--power-root` is supplied.

The PKStack rename is a clean-install change. Setup blocks legacy managed
installations before writes; it adds no aliases and performs no automatic
migration. Follow the [0.3 upgrade guide](upgrade-0.3.md) for a separate-checkout
transition and rollback. An earlier installation may use a `.pk-stack/bootstrap.json`
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


## Upstream maintenance

Use the commands below for explicit, reviewed maintenance. The
[updater guide](upstream-control-loop.md) describes the hosted schedule and
its limits; the [release status](../../../Wiki/knowledge/pkstack/release-record.md) records
live validation and whether that schedule is enabled.

In this repository, use `/pkstack-maintain` or inspect the pinned sources with:

```sh
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack upstream check \
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
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack upstream accept \
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
| Missing agent | Inspect the bare `/agent` picker, setup report, and project root, then try `/agent swap pkstack` in the current conversation. |
| Missing `/pkstack-verified-goal` | Select `pkstack` and inspect `/config skills`; use the [fresh-chat fallback](#attach-the-generated-agent) only if newly installed skills remain absent. |
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
- [Release status and validation evidence](../../../Wiki/knowledge/pkstack/release-record.md)
