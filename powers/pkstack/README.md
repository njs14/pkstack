# PKStack & friends

<p align="center">
  <img src="assets/logo.png" alt="PKStack: Kiro and three ghost friends above an open book, framed by an OKF knowledge tree. Kiro wears a graduation cap." width="360">
</p>

Engineering workflows, repeatable checks, and project knowledge for Kiro.

PKStack brings Poteto's pstack workflows and a curated set of development skills
to Kiro CLI and IDE. Investigate a codebase, compare designs, implement a change,
review it, and keep the decisions for the next task. A project-local command
runner records the checks you ran and their results.

Install PKStack as a Kiro Power and work through the workspace `pkstack` agent.
Kiro handles the conversation, native Specs, model selection, tools, and approvals.
PKStack adds the workflows, verification records, and repository Wiki.

[Quick start](#quick-start) · [Why PKStack](#why-pkstack) ·
[Capabilities](#what-pkstack-does) · [How it works](#how-it-works) ·
[Sources](#sources-and-friends) · [Docs](#docs-and-contributing)

## Quick start

You need Kiro CLI with v3 support or Kiro IDE, installed and signed in;
[`uv`](https://docs.astral.sh/uv/) on your `PATH`; and a `python3` launcher.
The controller runs on Python 3.11+. The installer also supports the tested
macOS Python 3.9 launcher through `uv`, so you can keep the system Python.
First use may download Python and dependencies.

This folder is the installable Power. Open a terminal in the folder containing
`plugin.json` and save its path:

```sh
export PKSTACK_POWER="$PWD"
test -f "$PKSTACK_POWER/plugin.json"
```

Keep this terminal open. `PKSTACK_POWER` points to the installer; the target
project is the application you want Kiro to work on. Choose the CLI or IDE
path below.

### Kiro CLI

CLI v3 also picks up Powers installed through the IDE. In a default CLI session,
`/powers` lists installed Powers. Registering the Power and setting up a target
project are separate steps; the terminal workflow below handles project setup
without an IDE import. See [CLI Power discovery](docs/usage.md#cli-powers-and-project-setup).

Replace the example path with your application's root directory, then preview
what setup will add:

```sh
cd "/absolute/path/to/your/project"
export PKSTACK_PROJECT="$PWD"
python3 "$PKSTACK_POWER/skills/pkstack-setup/scripts/setup_pkstack.py" \
  --root "$PKSTACK_PROJECT" --dry-run --output json
```

Confirm the target path and listed files. The preview leaves managed target
files unchanged, though preparing the runtime can populate caches or download
dependencies. If setup reports conflicts, inspect those files before continuing.

Apply the installation and check it:

```sh
python3 "$PKSTACK_POWER/skills/pkstack-setup/scripts/setup_pkstack.py" \
  --root "$PKSTACK_PROJECT" --output json
.pkstack/bin/projectctl version --output json
.pkstack/bin/projectctl doctor --output json
.pkstack/bin/projectctl knowledge validate --output json
```

When the checks pass, start Kiro from the target project:

```sh
kiro-cli chat --v3 --agent pkstack
```

Send `/pkstack <task>` with the work you want done. You can also invoke a specific
skill from the [capability table](#what-pkstack-does).

### Kiro IDE

1. Open **Powers → Add Custom Power → Import power from a folder**. Select
   this Power folder, which contains `plugin.json`, and choose **Install**.
2. Open your target application in Kiro and run `/pkstack-setup` in chat or an
   Agent Focus session.
3. Review the preview, approve the intended changes, and resolve any failed
   installation checks.
4. Select the workspace `pkstack` agent and send `/pkstack <task>`. If assets are
   absent, follow [agent and skill discovery](docs/usage.md#attach-the-generated-agent).

For a first run, [try the included failing task](docs/first-task.md) in a
disposable project. Kiro repairs an account-ID function while its four tests
stay unchanged. You can inspect the failed attempt, the repair, and the stored
passing result.

The [installation guide](docs/usage.md) covers source selection, agent
attachment, offline prerequisites, and troubleshooting. Existing installations
use the [managed refresh guide](docs/upgrade-0.4.md).

## Why PKStack

Development work leaves more than a code diff: a test command, an explanation
of the failure, a design choice, and a few things the next person needs to know.
PKStack gives those details a place in the project. The task's check and attempt
history stay together. Reusable behavior checks live in feature records.
Decisions and domain knowledge live in Markdown that you can review with the
code.

You keep Kiro's native planning, selected model, effort, and permission controls.
Use a single helper for a small question or connect a native Spec to a stored
check for a larger change.

## What PKStack does

| Capability | What you can do |
| --- | --- |
| Plan and implement | `/pkstack` applies the shared grilling interview within native Plan, Spec, or Quick Spec, then routes approved work through implementation, verification, and review. Link a Spec to the command that checks the result. |
| Verify a repair | Work against one stored command with `/pkstack-verified-goal`. Set an attempt limit and inspect the failed and passing output. |
| Build reusable checks | Give a feature an executable check and a recipe for driving its real CLI, UI, or service with `create-verification-skill`. Audit it later with `maintain-verification-skill`. |
| Compare designs | Sketch API and module alternatives with `architect`, compare candidates with `arena`, and trace the effects of a change with `blast-radius`. |
| Investigate and teach | Trace behavior with `how`, recover design rationale with `why`, or work through both with `teach`. Ground the explanation in code and available evidence. |
| Review in parallel | Split investigations with `swarm` and reconcile independent reviews with `pkstack-model-council`. The shipped delegated profiles inspect and report; the primary agent makes edits. |
| Retain project knowledge | Maintain topic documents, decisions, and references with `/okf`. Retrieve relevant context for later work with `recall`. |
| Improve Python code and scripts | `/uv`, `/ruff`, and `/ty` apply project-aware dependency, formatting, lint, and type-check guidance. |
| Work through decisions | `/grilling` supplies the shared interview method; `/grill-me` starts a focused interview; `/grill-with-docs` also requests knowledge capture during the interview when writes are permitted. |
| Explain visually | Ask `show-me` for call trees, pseudocode, and visual explanations. `archify` produces interactive architecture, sequence, workflow, and lifecycle diagrams; it needs Node.js 18+. |
| Write documentation | Draft and edit human-facing prose with `technical-writing` and `unslop`. Use `writing-for-agents` for instructions an agent will consume. |
| Build an automation | Define the measurements, actions, attempt limits, and failure handling with `design-control-loop`, then implement the agreed design with `build-iterated-agentic-loop`. |

For example, ask `/how Trace this request from the API handler to storage`, or
`/grill-with-docs Help define what suspended and closed mean in this account model`.
The [skill catalog](docs/curated-skills.md)
explains which helpers to combine and what each one contributes.

Planning reuses settled answers and leaves Kiro in charge of native artifacts,
approval, and execution. After you approve an implementation plan, PKStack saves
reusable definitions and decisions at the first permitted write step. Read-only
Plan defers capture, and an explicit no-write request takes precedence. See
[planning and knowledge capture](docs/usage.md#plan-and-bind-work).

## How it works

![Kiro plans and executes; PKStack guides the work; projectctl checks the result.](docs/artifacts/pkstack-architecture.png)

Kiro runs the agent session. PKStack's skills tell it how to approach a task,
when to seek independent review, and what evidence to collect. The local
`.pkstack/bin/projectctl` command handles installation checks, feature records,
goal state, and verification results.

For a verified goal, you choose a command that checks the behavior you need.
The controller stores that command and an attempt limit. Kiro inspects a failed
result, changes the implementation, and reruns the stored command. A passing
exit code completes that goal; exhausting the attempts leaves the work unfinished.

The default layout for a project with a new Wiki is:

```text
.kiro/             Agent profiles, skills, hooks, and steering
.pkstack/          Local controller, installation receipt, and task state
Wiki/features/     Reusable behavior contracts and executable checks
Wiki/knowledge/    Project topics, definitions, decisions, and references
```

Native Specs stay in Kiro's own files. Knowledge searches use a bounded,
read-only Kiro worker to retrieve relevant source material; local knowledge
validation checks metadata and links without a model. The
[architecture guide](docs/architecture.md) explains the process and ownership
boundaries.

Saved prompts can hold recurring requests you choose to submit. Keep them
user-owned and refer to the appropriate skill. See the
[saved-prompt guidance](docs/usage.md#save-a-recurring-request-in-kiro) for the
observed CLI syntax limits and what remains unverified.

## Control and compatibility

The workspace profile asks before ordinary writes and controller commands.
Setup records the files it manages and reports conflicts during upgrades.
The command runner limits execution time and captured output; review the
verification command before approving it because it runs with your local access.

Kiro CLI v3 and Kiro IDE are the primary surfaces. Kiro Crew is optional;
Kiro Web is untested. The [validation and release status](https://github.com/njs14/pkstack/blob/main/reviews/release-status.md)
records the specific CLI, IDE, platform, and retrieval paths that have been
exercised. Setup checks establish installation health; the failing-task guide
shows how to verify a repair.

## Sources and friends

PKStack started with Poteto's pstack. The additional skills have specific jobs:

| Source | What it contributes |
| --- | --- |
| [Poteto's pstack](https://github.com/cursor/plugins/tree/main/pstack) | Engineering workflows, architecture, investigation, review, verification, and development principles. |
| [HumanLayer](https://github.com/humanlayer/skills) | Visual explanations, control-loop design and implementation, and React prop narrowing. |
| [Matt Pocock](https://github.com/mattpocock/skills) | Agent-facing writing, decision interviews, domain modeling, and knowledge capture. |
| [Astral](https://github.com/astral-sh/claude-code-plugins) | Python environments and scripting with uv, lint/format with Ruff, and type checking with ty. |
| [Archify](https://github.com/tt-a1i/archify) | The diagram skill and its bundled renderer. |
| [OKF skills](https://github.com/scaccogatto/okf-skills) | Methods for creating, maintaining, and using project knowledge. |
| [Google's OKF specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) | The knowledge format that informs the Wiki structure. |

These are reviewed adaptations for Kiro. The
[port inventory](docs/upstream-skill-parity.md) records the original workflows,
Kiro replacements, and exclusions; the [third-party notices](THIRD_PARTY_NOTICES.md) retain
attribution. [Upstream maintenance](docs/upstream-control-loop.md) has its own
review and acceptance process.

## Docs and contributing

| Read this | For |
| --- | --- |
| [First task](docs/first-task.md) | A disposable failure, Kiro repair, and passing check. |
| [Architecture](docs/architecture.md) | Runtime components, native planning, and file ownership. |
| [Knowledge guide](docs/usage.md#use-project-knowledge) | Wiki authoring, retrieval, and local validation. |
| [Changelog](https://github.com/njs14/pkstack/blob/main/CHANGELOG.md) | Changes in each release. |
| [Contributing](https://github.com/njs14/pkstack/blob/main/CONTRIBUTING.md) | Development setup, focused checks, and pull requests. |
| [Security policy](https://github.com/njs14/pkstack/blob/main/SECURITY.md) | Reporting a vulnerability. |

PKStack is licensed under [Apache-2.0](https://github.com/njs14/pkstack/blob/main/LICENSE).
