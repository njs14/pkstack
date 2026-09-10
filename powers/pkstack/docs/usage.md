# Usage

PKStack adds a repeatable finish to Kiro development: store the command that
checks a task, record the initial failure, repair in the current Kiro session,
and retain the passing result. Project knowledge stays in the repository for
later sessions. This guide works for CLI-only users and IDE users.

## Install the Power

Use Kiro's [official Power installation flow](https://kiro.dev/docs/powers/installation/).
To install from a local checkout:

1. Clone `https://github.com/njs14/pkstack.git` locally. The repository is public; cloning over HTTPS requires no GitHub account.
2. Review `powers/pkstack/` inside the checkout before importing it. This folder contains the Power's `plugin.json`.
3. Open **Powers → Add Custom Power → Import power from a folder** in Kiro.
4. Choose the reviewed folder and click **Select Folder**. In the installed Power details, verify that `pkstack` points to that exact source folder. If an older import is still selected, uninstall that Power entry and install the reviewed folder again.

The observed local-folder flow installs when you select the folder. Installation
ends with that confirmation.

## CLI Powers and project setup

Kiro CLI v3 [automatically detects IDE-installed Powers](https://kiro.dev/docs/cli/v3/new-features/#powers-auto-pickup).
Use Kiro's Power installation flow for both surfaces.

## Initialize a workspace

Open the application you want Kiro to work on and invoke the installed Power's
`/pkstack-setup` skill where Kiro exposes it. Review its preview and approve the
intended workspace changes. The skill creates the local controller, workspace
skills, agent profiles, and Wiki, then reports validation results.

Workspace setup needs [`uv`](https://docs.astral.sh/uv/) on `PATH` and Python
3.11 or newer; runtime preparation may download dependencies. These are runtime
requirements of the Power's setup skill. No package-selection environment
variables or separate terminal installer are needed for Power installation.

If the Power or setup skill is missing, check its installation in Kiro's Powers
panel. After setup, [select the workspace agent](#attach-the-generated-agent)
before starting a task.

## First success

Use `/pkstack <task>` for your own work, or [try one failing task](first-task.md)
with either surface. That example supplies a repeatable verifier and explains
how to inspect the failure, Kiro's repair, and the stored passing result.

For explicit project commands, run `.pkstack/bin/projectctl` from the target
project root. It uses the project's locked controller runtime. The Power's
setup skill manages workspace initialization and reviewed updates.

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
before setup and `/agent swap pkstack` afterward so setup can discover the Power.
The primary profile exposes all built-in tools and inherits Kiro's defaults and
your user, workspace, and session permissions. All four consumer profiles omit
inline permission rules. Delegated architect, reviewer, and verifier profiles
retain only `read` and `knowledge`; they inspect and report to the primary session.
The primary retains an empty `permissions.rules` block as a v3 compatibility
marker; it contributes no rules or grants.
The [global permissions guide](permissions.md) includes an optional, manually
installed preset for broad built-in access with targeted destructive-command
denies. Normal setup never changes your global policy.

Kiro combines permission scopes with `deny > ask > allow`. An explicit `ask`
cannot be overridden by a saved `allow`, so the profile does not force repeated
approval for routine work you already trust. Review the executable verifier
before authorizing it: a controller command can run project code with your local
access. Kiro's own protected-path prompts and your other explicit asks still apply.
Native Plan and Spec select their own agents and retain their workflow approvals;
user-level permission rules continue to apply across these handoffs. Tool approval
and the controller's evidence checks are not an operating-system sandbox. See the
[permission guide](permissions.md) for scope and limits.

## Commands

| Command | Use it for |
| --- | --- |
| `/pkstack` | Route a task through planning, implementation, verification, and review |
| `/pkstack-guide` | Decide the next useful step for a new or existing project without starting it |
| `/pkstack-setup` | Preview installation or refresh when the imported Power is discoverable |
| `/pkstack-maintain` | Review upstream changes to the Power |
| `/pkstack-verified-goal` | Repair against one stored executable check |
| `/pkstack-model-council` | Compare independent reviews and resolve findings |
| `/pkstack-principles` | Apply the engineering-principles catalog |

Imported skills keep their names. The [sources guide](curated-skills.md) explains
their roles and handoffs. For a runnable example, [try one failing task](first-task.md).

## Ask what to do next

Use `/pkstack-guide <situation or question>` when you want advice before choosing a workflow.
It reads relevant project context, recommends one next action with its reason and success
evidence, and gives you a ready-to-send prompt. It can also answer a simple skill-choice
question without surveying the project. `/pkstack` routes advisory questions to the same guide.

```text
/pkstack-guide I'm starting a new service. Where should I begin?
/pkstack-guide This repo has tests, but agents still need constant supervision.
/pkstack-guide We have an approved design. What should happen next?
```

The guide does not run setup, tests, prototypes, or writes merely to give advice. It reuses
existing tools and Specs, distinguishes old evidence from a current successful run, and names
missing capabilities. When you authorize the next step, its existing workflow takes over with
the settled context. Kiro still owns native mode selection and approval. Setup may offer the
guide after installation, but does not run it automatically.

The [lifecycle reference](../skills/pkstack-guide/references/project-lifecycle.md) explains its
decision criteria and source adaptations. Guidance is not a new planner or a replacement for
the actual execution skills.

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

![Return from native Kiro planning to PKStack, run the stored verifier, and repair while attempts remain.](https://github.com/njs14/pkstack/blob/main/docs/artifacts/pkstack-task-workflow.png)

[Open the interactive workflow](https://github.com/njs14/pkstack/blob/main/docs/artifacts/pkstack-task-workflow.html).

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

For corrupt state, `goal clear --force` takes the state lock and reloads the
slot before acting. If it is still unreadable, the command archives the exact
bytes in a unique `goal.<timestamp>[.<counter>].unreadable.json` file beside the
slot, then frees the slot. Earlier archives are never overwritten. This also
handles invalid UTF-8. Unsupported schema versions remain rejected untouched;
use a clean consumer installation and preserve that evidence separately.

Ctrl-C or SIGTERM stops the verifier's process group and releases the goal
lock. Cancellation never records a passing result. Inspect `goal status`
before deciding whether to retry.

### Verifier boundary

Commands run as argv with `shell=False`. Pipelines, redirects, substitutions,
the named shell and inline-program interpreters, obvious placeholders, a short
list of destructive patterns, and known path escapes are rejected. The
interpreter lists are closed name lists in the runner, not a general
interpreter detector, and network tools, remote shells, and package installers
are not screened. The policy is an evidence screen, not a
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
.pkstack/bin/projectctl knowledge search "account suspension" --budget 1200 --model auto --output json
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
The no-model `knowledge status` probe reports `cli_compatible` separately from
`isolation_verified` and `search_verified`, which remain false until those stages
are verified. A compatible CLI version does not prove isolation, authentication,
or successful search. There is no alternate backend or silent model fallback. Optional `--model`
defaults to `auto`, which lets Kiro route the request. Receipts preserve
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
See the [knowledge runtime decision](https://github.com/njs14/pkstack/blob/main/Wiki/knowledge/pkstack/native-spec-and-okn.md).

## Refresh managed files

Leave the restricted `pkstack` profile before refreshing. CLI v3 2.21.1 names
its bundled default agent `default`:

```text
/agent swap default
```

Invoke `/pkstack-setup` from the installed, reviewed Power in a context where
Kiro exposes it. If it is missing, check Power installation and skill discovery
in Kiro. Review any pending managed updates before approving them, then return
to the workspace `pkstack` agent.

Managed updates replace only files that still match their prior receipt hashes.
User edits remain conflicts, and retired managed paths are never deleted
automatically. Do not add a cached setup skill to `.kiro/skills/` to force discovery.

### Clean reinstall

Current setup uses receipt schema 2 and rejects older receipts and legacy managed
namespaces. The goal controller uses schema 3 and rejects older goal state. Neither
converts old content or evidence. Feature schema 2 and spec-bridge schema 1 remain separate contracts.
`--update-managed` does not bypass an incompatible receipt.

Keep the existing checkout as a rollback copy, including uncommitted work, the old
receipt, goals, native `.kiro/specs/`, Wiki documents, settings, and evidence.
Prepare a separate clean consumer copy. Compare every old receipt entry with its
file's SHA-256 before excluding that exact unchanged managed path from the new
copy. Preserve changed managed files for deliberate reconciliation. Never remove
an entire `.kiro/` or Wiki directory based on its name. Keep Wiki navigation seeds
and other user-owned content even if an old receipt once claimed them.

Run `/pkstack-setup` from the reviewed Power against the clean copy. Review the
preview, apply the intended changes, then check version, doctor, local knowledge
validation, and knowledge status. A second preview should report no pending
updates. Retain old goal records as historical evidence outside the active state
slot; create and verify a new goal instead of importing old proof. Its command
record always includes explicit nullable provenance and an artifacts list.

Select the workspace `pkstack` agent and verify a representative task before
replacing the original checkout in daily use. Power-manager removal does not
migrate workspace files.


## Upstream maintenance

Use the commands below for explicit, reviewed maintenance. The
[updater guide](https://github.com/njs14/pkstack/blob/main/docs/upstream-control-loop.md) describes the hosted schedule and
its limits; the [release status](https://github.com/njs14/pkstack/blob/main/Wiki/knowledge/pkstack/release-record.md) records
live validation and whether that schedule is enabled.

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
current release pass. See the [upstream feature contract](https://github.com/njs14/pkstack/blob/main/Wiki/features/pkstack-upstream-maintenance.md)
for the scope and [provenance](../provenance/provenance.md) for source identities.

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

- [Architecture and trust boundaries](https://github.com/njs14/pkstack/blob/main/docs/architecture.md)
- [Kiro surface compatibility](kiro-v3-compatibility.md)
- [Upstream skill parity](../provenance/upstream-skill-parity.md)
- [Provenance and porting boundary](../provenance/provenance.md)
- [Validation report](https://github.com/njs14/pkstack/blob/main/docs/validation-report.md)
- [Review harness](https://github.com/njs14/pkstack/blob/main/reviews/README.md)
- [Release status and validation evidence](https://github.com/njs14/pkstack/blob/main/Wiki/knowledge/pkstack/release-record.md)
