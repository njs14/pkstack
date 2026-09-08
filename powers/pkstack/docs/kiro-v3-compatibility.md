# Kiro surface compatibility

The product-documentation snapshot is dated **2026-09-04**; local runtime
evidence was refreshed on **2026-09-05**. This records the Kiro contract PKStack
targets and the observed behavior on the target Mac, not a guarantee for every
account or later release. Re-run the checks at the end after a Kiro update.

PKStack supports Kiro CLI v3 and the Kiro IDE 1.x chat panel as primary surfaces;
the IDE's Agent Focus Mode is a supported agent-first view but remains listed
by Kiro as experimental. Neither client is an exclusive runtime dependency.
Kiro Crew compatibility is required but Crew remains an optional orchestrator.
Kiro Web is supported through committed repository-local assets by design and
is explicitly untested. Mobile is outside this release contract.

## Support and evidence matrix

“First-class” identifies a primary product target; “exercised” identifies a
workflow actually run. Those are deliberately separate claims.

| Kiro surface | Product role | PKStack entry path | Current evidence | Status and limits |
| --- | --- | --- | --- | --- |
| CLI v3 (`kiro-cli` 2.21.1) | Primary | Ordinary `kiro-cli chat --v3`; select workspace agent `pkstack`; invoke `/pkstack-verified-goal` in that chat | September 5 Luna/Low campaigns completed native Standard and Quick Spec planning, same-conversation agent handoff, Spec-bound failure, implementation-only repair, and pass; tests and planning artifacts stayed unchanged | **First-class and exercised.** These were two four-test fixtures, not every Spec mode. ACP, classic/V2, nested Kiro, and `/spawn` were not used. The separate native-goal probe below used 2.21.0. |
| IDE 1.x (`Kiro.app` 1.0.437) | Primary | Import the Power, bootstrap the project, select the workspace `pkstack` agent in the chat picker, and invoke the skills | Import/setup/discovery passed; September 5 Luna/Low campaigns then completed native Standard and Quick Spec planning, same-tab agent handoff, Spec-bound failure, implementation-only repair, and pass; tests and planning artifacts stayed unchanged | **First-class with bounded GUI workflows.** These were two four-test fixtures, not every Spec mode or the Agent Focus view. Agent Focus Mode remains experimental. |
| Kiro Crew | Optional orchestrator | Open the trusted repository through Crew so its Kiro-backed session reads committed `.kiro`; keep one `/pkstack-verified-goal` loop in the Crew-owned session | Official Crew contract says it runs Kiro CLI over ACP and reads existing `.kiro` agents, skills, and steering; signed feed-current Sep. 3 Nightly passed `--version`, `--help`, and `doctor`; package assets avoid client-only argument substitution | **Compatibility required; orchestration optional.** The bounded smoke did not open a project or run PKStack. Crew's internal ACP transport does not make ACP PKStack's default entrypoint, and no Crew end-to-end goal campaign is claimed here. |
| Kiro Web (GA) | Supported secondary surface | Start from a repository that already commits the bootstrapped `.kiro` and `.pkstack` assets; invoke `/pkstack-verified-goal` from the Web session's primary agent | Official Web support for project skills, agents, hooks, steering, and MCP plus static repository/path tests | **Supported by design, explicitly untested.** Web cannot select a project custom agent as primary, does not provide the local permission/approval surface, and still needs Python 3.11+ plus `uv` in its sandbox. |
| External ACP client | Optional integration boundary | Client-owned `kiro-cli acp` integration | An external host is not tested; PKStack's own bounded knowledge-search worker invokes Kiro ACP separately | Not a primary or default PKStack path. Crew's use of ACP is a product implementation detail, not authorization to substitute an external host. |

The IDE and CLI wording above follows Kiro's current [one-harness,
many-surfaces model](https://kiro.dev/docs/how-kiro-works/). The Web limitation
follows the current [configuration-scope
matrix](https://kiro.dev/docs/configuration/) and [custom-agent surface
behavior](https://kiro.dev/docs/custom-agents/). Crew's boundary follows the
official [Kiro Crew product contract](https://kiro.dev/crew/).

Historical records retain the names and commands actually tested. The
[friends validation](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/friends-validation.md)
records the September 5 candidate and exact campaign scope; the
[release status](https://github.com/njs14/pkstack/blob/main/Wiki/knowledge/pkstack/release-record.md) distinguishes tested
behavior from a published release.

Kiro CLI 2.21.0 has one observed discovery compatibility quirk: a valid
read-only project agent without a top-level `toolsSettings` key can pass
`agent validate` yet be absent from `agent list`. PKStack therefore includes
an exact empty `toolsSettings: {}` sentinel on its architect, reviewer, and
verifier profiles. This is a point-in-time 2.21 compatibility measure, not a
claim that the key is a general V3 schema requirement; permissions remain
entirely in `permissions.rules`, and no shell or write authority is placed
under the sentinel. The sanitized controlled probe is recorded in
[`reviews/kiro-v3-agent-discovery-probe.json`](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/kiro-v3-agent-discovery-probe.json).

When Kiro CLI is installed, `projectctl doctor` now runs the local, no-model
`kiro-cli agent list` command from the actual project root before any
authenticated use. It derives the expected set from safe
`.kiro/agents/*.json` profiles and requires every name to appear as an exact
`Workspace` row after stripping terminal escapes. Missing rows, malformed
output, timeout, and nonzero exit are failures. The existing per-profile
`agent validate` checks remain separate because schema validity is not loader
discovery evidence.

## Automated product-drift canary

The source entries in `maintenance/upstreams.json` define PKStack's autonomous update sources.
Kiro product/runtime/documentation state is deliberately separate: the weekly and manually
dispatchable `.github/workflows/pk-stack-kiro-runtime-canary.yml` is read-only and never promotes a
pin or creates a candidate branch.

The canary resolves the official stable Kiro CLI manifest, selects exactly the x86_64 Linux
headless `tar.xz`, downloads and checksum-verifies the advertised binary, checks its reported
version, validates all workspace-agent files, requires their exact `Workspace` discovery, and
strictly validates the live `--list-models` inventory without sending a model turn. A newer stable
tuple or any runtime regression fails red. `KIRO_API_KEY` is available only to the inventory step
after version, SHA-256, derived URL, and size exactly match the reviewed pin; an advertised
unpinned binary never receives it. No Anthropic credential, external reviewer, or Kiro model turn is involved. IDE release metadata,
Kiro Crew Nightly feeds, the changelog, `llms.txt`, and already recorded relevant documentation
hashes are fetched under bounds and reported as non-gating observations.

Pin promotion remains a deliberate maintainer change because the workflow copies and protected
controller files are trust roots. This detector does not change the product composition: Kiro CLI
v3 and IDE chat/Agent Focus remain primary, Crew remains compatible and optional, and Web remains
supported by design but untested. Native Specs, Quick Specs, Skills, and Powers still drive the
workflow; `/pkstack-verified-goal` remains separate from native `/goal`.

## September 1-2, 2026 Kiro inventory

The following official changes were reviewed before this compatibility text
was updated:

| Official change | PKStack consequence |
| --- | --- |
| [Kiro Web became generally available](https://kiro.dev/changelog/web/kiro-web-is-now-generally-available/) on September 1 | Web is now an explicit supported-by-design surface, but no browser campaign is invented. |
| [Cloud configuration can apply to new local sessions](https://kiro.dev/changelog/web/use-cloud-configuration-in-local-sessions/) on September 1 | Cloud items may supplement new IDE and CLI sessions, but they do not write or replace local `.kiro` files. Repository-local PKStack assets and the bootstrap receipt remain authoritative. |
| [IDE 1.0.437 added Cloud configuration, synced Powers, and Agent Focus reliability](https://kiro.dev/changelog/ide/1-0-437/) on September 1 | IDE chat/Agent Focus is named as a primary PKStack surface; cloud-managed items must still be distinguished from repository-managed assets. |
| [CLI 2.21.0 added the V3 session dashboard, `/config`, and Cloud configuration](https://kiro.dev/changelog/cli/2-21/) on September 1 | The exercised CLI baseline advances to 2.21.0. `/config` can inspect source labels, but inspection is not installation or synchronization proof. |
| [Kiro entered the AWS ISO/IEC 27001:2022 scope](https://kiro.dev/changelog/general/kiro-covered-by-aws-iso-27001-certification/) on September 1 | This is a Kiro compliance change, not PKStack certification. The changelog explicitly excludes Fable, so independent Fable review is not described as covered. |
| [Administrators can export Kiro usage metrics through OpenTelemetry](https://kiro.dev/changelog/general/open-telemetry-exports/) on September 1 | No PKStack runtime or telemetry dependency is added; this account-level feature is outside the repository workflow. |
| [Native `/goal`](https://kiro.dev/docs/cli/chat/goal/) appears in the current CLI documentation | The documented five-iteration default is acknowledged, but `/pkstack-verified-goal` remains a separate projectctl-backed contract. A sterile interactive CLI 2.21.0 V3 probe did not recognize `/goal clear`, so docs and this installed runtime diverge. |
| [GPT-5.6 Sol, Terra, and Luna](https://kiro.dev/docs/models/available-models/) and [reasoning effort](https://kiro.dev/docs/models/effort/) are in the current model documentation | All three are experimental 272K models at 2.4x, 1.0x, and 0.1x respectively. Effort levels run from `none` through `max`, but user selection is exposed only in IDE and CLI, not Web. PKStack inherits the user's selection; the isolated scheduled maintainer is the only deliberate Sol/max pin. |
| [OpenAI and AWS published GPT-5.6-in-Kiro workflow guidance](https://openai.com/index/gpt-5-6-in-kiro/) on August 24 | Structured requirements, design, tasks, checkpoint review, and property-based testing are useful Kiro methods, not evidence that PKStack exercised every method on every surface. Kiro's current property-testing feature is optional, IDE-only, and not formal proof; projectctl's executable verifier remains the portable completion gate. |

Kiro's September 2 documentation also made the cross-surface distinctions
explicit: [workspace skills activate in IDE, CLI, and
Web](https://kiro.dev/docs/skills/), while [Configuration
Sync](https://kiro.dev/docs/web/cloud-configuration/) is personal
local-to-cloud configuration, not repository deployment.

## Configuration Sync and the repository-local Web path

Configuration Sync does not merge into or overwrite local `.kiro`. A cloud
copy can be loaded into a new local IDE or CLI session, and `/config` may label
active items as local, cloud, or both, but the managed files recorded by
`.pkstack/bootstrap.json` remain on-disk repository state.

Do not present a Configuration Sync upload as a complete PKStack Web install.
Kiro permits at most 50 files in a custom cloud Power and accepts text files
only. The complete PKStack Power exceeds that count and includes a PNG asset.
The honest Web path is to bootstrap locally, review and commit the generated
`.kiro` and `.pkstack` assets, and then let Kiro Web clone that repository. A
Web session can activate committed workspace skills, but its built-in primary
agent owns the turn; committed `pkstack-*` agents are available only for
sub-agent delegation, and the IDE/CLI permission profile is not claimed there.

## Primary-surface compatibility decision

PKStack can bootstrap through the ordinary interactive CLI v3 experience:

```bash
kiro-cli chat --v3
```

After setup, `/agent swap pkstack` attaches the generated repository-local
PKStack primary profile before the next workflow message. If Kiro has not
discovered it yet,
the fallback remains the same ordinary V3 runtime:

```bash
kiro-cli chat --v3 --agent pkstack
```

In Kiro IDE 1.x, the equivalent primary path is to open chat or Agent Focus and
choose the workspace `pkstack` agent from the agent selector. The selected
prompt, tools, and resources apply to the next message without changing the
user's global default agent.

The normal workflow remains in that selected Kiro agent session. Kiro owns
execution and native orchestration; PKStack supplies workflow skills and
conventions; the bootstrapped `.pkstack/bin/projectctl` supplies deterministic
project state and evidence. Setup does not mutate the user's global default
agent.

ACP, classic/V2, a nested Kiro process, and a separate `/spawn` session are not
the default path. Current docs describe native `/goal`, but the installed CLI
2.21.0 V3 runtime did not recognize `/goal clear` in a sterile interactive
probe. PKStack does not require or invoke that feature. `/pkstack-verified-goal` is a
skill that keeps the repair loop in that session and stores its verifier and
attempt history through the project-local controller.

The initial 2026-09-01 CLI snapshot reported application version `2.20.2`; the
selected-profile campaign on 2026-09-02 ran on Kiro CLI `2.21.0`. In both,
`--v3` selected the next-generation agent engine. “CLI v3” is the
engine/configuration generation, not Kiro IDE's
`CFBundleShortVersionString`.

## Observed local snapshot

| Item | Observed result |
| --- | --- |
| Executable | `~/.local/bin/kiro-cli`, a symlink into `/Applications/Kiro CLI.app` |
| Initial CLI/app version | `2.20.2` |
| Later selected-profile validation | Kiro CLI `2.21.0` on 2026-09-02 |
| Kiro CLI macOS app build | `20260831.180303` |
| Kiro IDE installation | `/Applications/Kiro.app`, version/build `1.0.437` |
| Kiro Crew installation | `/Applications/KiroCrew Nightly.app` version `0.6.0-nightly.20260903t061110`; official Nightly feed SHA-256 `0274b7299b26c292cb173685a546598f34f10e7af167f64dfe3a7fa2e4aef4f9`; downloaded DMG SHA-256 `d11e6e50925ae2cb1c824465352063664a492fe799789f4a612b58d2c1cca4fa`; exact bundle ID/version, deep/strict signature, and Gatekeeper notarization accepted; `--version`, `--help`, and `doctor` passed, but no PKStack workflow was exercised |
| Bundle identifier | `com.amazon.codewhisperer` |
| V3 selection | `kiro-cli chat --v3` or top-level `kiro-cli --v3` |
| V3 modes | `default`, `spec` |
| Effort names exposed by the CLI | `low`, `medium`, `high`, `xhigh`, `max` |
| Knowledge setting | `chat.enableKnowledge` is `true` on this Mac |
| Historical workflow setting | `chat.enableWorkflows` is rejected as invalid |
| Native goal in installed runtime | A sterile interactive CLI 2.21.0 V3 session treated `/goal clear` as ordinary prompt text, consumed 0.09 credits for that prompt, and exited normally after `/quit`; native `/goal` is not exposed by this tested runtime |
| Default model returned by the account | `auto` |
| GPT-5.6 family returned by the account | `gpt-5.6-sol`, `gpt-5.6-terra`, and `gpt-5.6-luna`; each reported 272,000 tokens and experimental-preview status, with 2.4x, 1.0x, and 0.1x credit multipliers |

The local inventory commands were:

```bash
command -v kiro-cli
kiro-cli --version
kiro-cli --help-all
kiro-cli chat --help
kiro-cli agent --help
kiro-cli agent validate --help
kiro-cli chat --list-models --format json-pretty
kiro-cli settings chat.enableKnowledge --format json
kiro-cli settings chat.enableWorkflows --format json
/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' \
  '/Applications/Kiro CLI.app/Contents/Info.plist'
/usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' \
  '/Applications/Kiro CLI.app/Contents/Info.plist'
/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' \
  '/Applications/Kiro.app/Contents/Info.plist'
/usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' \
  '/Applications/Kiro.app/Contents/Info.plist'
command -v kirocrew
kirocrew --version
```

The two settings commands returned `true` and
`chat.enableWorkflows is not a valid setting`, respectively.

## Kiro capability map

| Capability | Current Kiro contract | PKStack use |
| --- | --- | --- |
| Plan | `/plan <request>` produces a conversational plan; native Plan cannot write files, execute commands, or use MCP tools | Use the shared grilling method with native reading and search, retain pending knowledge capture in the conversation, and stop after a plan-only request; no `tasks.md` or prototype execution is required |
| Specs | Feature Spec, Bugfix Spec, Quick Spec, and parallel task execution span IDE, CLI, and Web; CLI exposes `/spec new <name>`, `/spec <name>`, and `/spec run <name>` | Use native requirements or bug analysis, design, tasks, and dependency waves as the planning spine; after a visible same-conversation return to `pkstack`, bind the native package to one published feature verifier rather than recreating a planner |
| Agent Skills | Workspace `.kiro/skills/<name>/SKILL.md` and global `~/.kiro/skills/`; slash invocation accepts trailing request text across IDE, CLI, and Web | Materialize `/pkstack-verified-goal`, architecture, arena, swarm, maintenance, and advisory council workflows without CLI-only placeholder substitution; keep `/pkstack-setup` Power-local as an IDE/CLI bootstrap exception |
| Powers | Agent Plugins layout with root `plugin.json`, optional `skills/`, `mcp.json`, and `dev.kiro/` | Package and distribute PKStack guidance and its Power-local setup shim |
| Custom agents | Workspace `.kiro/agents/` or global `~/.kiro/agents/`; current docs accept JSON and Markdown; IDE and CLI can select a primary agent while Web can only delegate to project agents | Ship four Power JSON profiles plus the repository's isolated CI maintainer; require both installed-CLI validation and exact Workspace discovery; select `pkstack` as primary only where Kiro supports it |
| Native subagents | Main agent delegates isolated work through the `subagent` tool; custom agents can be allow-listed | Bounded architecture, review, and verification assistance while the primary session owns edits/evidence |
| `/spawn` | User-driven command for a fresh parallel session | Not used for internal PKStack fanout or verified-goal iteration |
| Hooks | Standalone `.kiro/hooks/*.json`, `version: "v1"`, PascalCase triggers, command or agent actions | Static SessionStart orientation plus a disabled advisory Stop probe |
| Permissions | Capability rules with `allow`, `ask`, and `deny`; the most restrictive result wins | Allow workspace reads, leave Git/ordinary writes/projectctl authorization to ambient Kiro policy, and retain protected-file and destructive-command denies |
| Steering | `.kiro/steering/*.md` with `always`, `auto`, `fileMatch`, or `manual` inclusion | Three small always-on architecture/safety/prose invariants plus TypeScript guidance selected by `fileMatch` for `**/*.ts` and `**/*.tsx` |
| Knowledge | `/knowledge` and the `knowledge` tool are experimental; local knowledge is enabled | Keep the source-controlled OKF Wiki authoritative and use the spec-linked feature map first. `projectctl knowledge validate` checks metadata, Markdown links, and feature contracts locally; `knowledge search` retrieves bounded context through an isolated read-only Kiro ACP worker |
| Goal | Native `/goal` is documented as a self-verifying loop with five iterations by default and configurable `--max` | Keep `/pkstack-verified-goal` separate and projectctl-backed; do not depend on native availability or claim this Mac exposes it without an interactive probe |

Primary references:

- [What's new in Kiro CLI 3.0](https://kiro.dev/docs/cli/v3/)
- [Kiro IDE chat and agent selection](https://kiro.dev/docs/ide/chat/)
- [Experimental Agent Focus Mode](https://kiro.dev/docs/ide/experimental/focus-mode/)
- [How Kiro works across surfaces](https://kiro.dev/docs/how-kiro-works/)
- [Specs across Kiro surfaces](https://kiro.dev/docs/specs/) and [Quick Spec](https://kiro.dev/docs/specs/quick-spec/)
- [Plan mode](https://kiro.dev/docs/specs/plan/) and [Analyze Requirements](https://kiro.dev/docs/specs/analyze-requirements/)
- [Built-in Spec, Quick Spec, Bug Fix, and Plan agents](https://kiro.dev/docs/custom-agents/built-in/)
- [Agent Skills](https://kiro.dev/docs/skills/)
- [Powers](https://kiro.dev/docs/powers/) and [Create powers](https://kiro.dev/docs/powers/create/)
- [Custom agents](https://kiro.dev/docs/custom-agents/) and [configuration reference](https://kiro.dev/docs/cli/custom-agents/configuration-reference/)
- [Invoking custom agents as subagents](https://kiro.dev/docs/chat/subagents/)
- [Slash commands, including `/spawn`](https://kiro.dev/docs/cli/reference/slash-commands/)
- [Native goal loop](https://kiro.dev/docs/cli/chat/goal/)
- [Models](https://kiro.dev/docs/models/), [available models](https://kiro.dev/docs/models/available-models/), and [reasoning effort](https://kiro.dev/docs/models/effort/)
- [OpenAI/AWS GPT-5.6 in Kiro announcement](https://openai.com/index/gpt-5-6-in-kiro/) and [Kiro spec correctness](https://kiro.dev/docs/specs/correctness/)
- [Hooks](https://kiro.dev/docs/hooks/)
- [Permissions](https://kiro.dev/docs/cli/chat/permissions/)
- [Steering](https://kiro.dev/docs/steering/)
- [Experimental knowledge management](https://kiro.dev/docs/cli/experimental/knowledge-management/)
- [Kiro Web Configuration Sync](https://kiro.dev/docs/web/cloud-configuration/)
- [Kiro Crew](https://kiro.dev/crew/)

## Formats used by PKStack

### Power and skills

CLI v3 detects IDE-installed Powers and exposes `/powers` to list them; see
[Kiro's CLI Power guidance](https://kiro.dev/docs/powers/installation/#cli) and
[slash-command reference](https://kiro.dev/docs/reference/slash-commands/#powers).
On September 6, a `kiro-cli 2.21.1` local `--v3` session in a fresh directory
listed PKStack through `/powers`, while `/pkstack-setup` was absent from slash
completion. This confirms Power discovery, not a CLI installation or setup
execution. The probe made no Power configuration changes and ran no setup skill.
The [usage guide](usage.md#cli-powers-and-project-setup) separates Power
registration from project setup.

The root manifest uses Agent Plugins `plugin.json`. Skills are stored as
`skills/<lowercase-hyphenated-name>/SKILL.md` with exactly `name` and
`description` frontmatter; the asset tests reject other keys, including Kiro's
optional `compatibility` field. Kiro passes text following a skill name as
request context in IDE, CLI, and Web. Placeholder substitution such as
`$ARGUMENTS` is currently CLI-only, so PKStack skills refer to the activation
request directly and do not depend on that placeholder.

The setup skill resolves `scripts/setup_pkstack.py` relative to its loaded
Power. It always starts with a no-write preview. New managed content appears as
`pending_updates` until a reviewed run explicitly includes
`--update-managed`; user-modified files remain conflicts. Retired receipt-owned
paths appear as blocking `stale_managed` and are never pruned automatically.
After bootstrap, skills use `.pkstack/bin/projectctl`, never repository
`./projectctl` or ambient `uv run projectctl` resolution.

Setup remains Power-local; bootstrap deliberately does not copy
it to `.kiro/skills/`, where an older workspace copy could shadow an upgraded
Power. The remaining workflow skills are materialized in the workspace. Kiro's
current [Agent Skills documentation](https://kiro.dev/docs/skills/) describes
progressive disclosure: metadata is discovered first and the full skill body is
loaded only when activated. It documents workspace skills across IDE, CLI, Web,
and Mobile and gives no per-project skill-count cap; PKStack does not infer
from that absence that the catalog is unlimited.
The cached `projectctl setup` surface requires an explicit `--power-root` and
cannot silently use its own stale cache as upgrade authority. After selecting
`pkstack`, a managed refresh remains in the current chat. IDE users switch
through the agent picker. CLI v3 2.21.1 uses `/agent swap default` to leave the
restricted profile, but that swap does not make an imported Power discoverable.
Invoke `/pkstack-setup` only where the reviewed Power is available; otherwise
run its Power-local setup script from a terminal as documented in [usage](usage.md),
then use `/agent swap pkstack` in the same conversation. The native CLI campaign
observed all five installed command skills and an explicit missing-skill result
for Power-local setup; direct setup-script success is separate evidence.
Setup also validates its required source modules and Power assets before target
writes. Its deterministic repository discovery uses sorted root-relative paths
and refreshes as an owned observation rather than a managed code upgrade.

In CLI v3, Kiro can switch to the discovered PKStack primary agent in the
current chat with `/agent swap pkstack`. Use the bare `/agent` picker to inspect
agents and `/config skills` under the selected agent to inspect effective skills.
On September 6, the CLI 2.21.1 audit selected a newly added fixture agent without
restarting, while `/agent list` was interpreted as an agent named `list`. Agent
hot reload does not establish skill hot reload. In IDE 1.x, use the agent selector
in chat or Agent Focus and choose the workspace `pkstack` profile. Its prompt,
tools, and permissions apply beginning with the next message. If the agent is
missing, check setup and the project root before retrying selection. If newly
installed skills remain absent, use one fresh pre-goal chat in the same project.
Once `/pkstack-verified-goal` is loaded, the implement/verify loop stays in that current
Kiro agent session.

### Planning and native command guidance

All PKStack planning entry points use the shared `grilling` interview method.
They pass settled answers and remaining questions into native Plan or Specs and
explicitly direct that workflow to read the method. Kiro still owns planning
phases, Spec artifacts, approvals, and execution. PKStack does not modify built-in
agents or global settings to force inheritance.

`/grilling`, `/grill-me`, and `/grill-with-docs` retain their names. The last
requests knowledge capture during an interview when writes are permitted.
Every explicitly approved implementation plan also captures reusable definitions
and decisions through `domain-modeling` and `okf` at the first permitted write
step. Read-only Plan retains pending capture in the conversation and defers
commands, MCP, prototypes, and validation. Explicit no-write instructions take
precedence, repeated approval reuses existing knowledge entries, and denied writes
or failed validation leave capture incomplete. See the [planning guide](usage.md#plan-and-bind-work).

The [September 6 CLI audit](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/cli-native-command-audit/README.md)
separates native execution evidence from menu recognition and documentation:

- `/spec analyze_requirements <feature-name>` is an optional checkpoint when
  `requirements.md` exists; reuse its findings. `/spec view <feature-name>
  requirements`, `design`, or `tasks` opens the corresponding existing document.
  The menu exposed both subcommands; analysis and viewing were not executed in
  that audit. Analysis may update requirements; viewing establishes neither
  approval nor verifier binding. A Bug Fix package with only `bugfix.md` does
  not meet the analysis prerequisite.
- `/code status` opened workspace/LSP status. `/code overview` was present in the
  menu and is optional orientation. Keep `/code init` an explicit setup action
  because it can write `.kiro/settings/lsp.json` and start language servers.
  Native symbol/reference navigation can supplement source inspection when
  available. `/code summary` and `/code logs` were not in this audited v3 menu.
- `/model` and `/effort` were recognized native pickers; the audit changed no
  selection. Choices depend on runtime, account, and model. PKStack adds no
  model or effort default.

### Custom agents

PKStack uses JSON profiles because all shipped Power profiles validate with the
installed `kiro-cli agent validate`; the source repository also has the
separately constrained `pkstack-maintainer` and `pkstack-ci-reviewer` CI profiles. Every repository
workspace profile must both validate and appear in `agent list`. Each Power
profile explicitly declares:

- short V3 tool tags such as `read`, `write`, `shell`, `subagent`, and
  `knowledge`;
- `skill://.kiro/skills/*/SKILL.md` and
  `file://.kiro/steering/**/*.md` resources;
- capability-based permission rules;
- `includeMcpJson: false` and `includePowers: false`; and
- no hard-coded model, so the user's active model is inherited.

`includePowers: false` disables automatic Power inclusion. It does not establish
skill isolation: PKStack explicitly loads reviewed workspace skills, while Kiro
can merge other skill scopes. Inspect `/config skills` under the active agent;
see [configuration scopes](https://kiro.dev/docs/configuration/#resolving-conflicts).

The primary profile has the write tool and a subagent allow-list limited to
`pkstack-architect`, `pkstack-reviewer`, and `pkstack-verifier`. All three
delegated profiles expose only `read` and `knowledge`; they omit both `write`
and `shell` and deny `fs_write`. The verifier inspects a contract and recorded
evidence, then returns the exact command for the primary session to execute.

IDE and CLI can select `pkstack` as the primary session agent. Crew reads the
same `.kiro` configuration when it drives Kiro CLI, but remains an optional
orchestrator. Crew's direct KAS projection (Kiro Agent Specification) does not
preserve inline permission or native subagent parity: `permissions.rules` and
the subagent allow/trust settings are not claimed equivalent. Kiro Web reads
the project profiles only as delegation targets;
the Web primary session agent cannot be replaced with `pkstack`, so PKStack
does not claim the profile's primary-agent prompt or permissions there.

### Permissions

The templates use agent-scoped capability rules instead of broad trust. Kiro's
current rules combine scopes with `deny > ask > allow`. In the shipped primary
profile:

- workspace reads are allowed;
- Git, ordinary writes, and canonical `.pkstack/bin/projectctl` invocations add
  no agent-scoped ask or allow rules, so Kiro's defaults and the user's configured
  permissions determine authorization;
- direct writes to bootstrap-managed control-plane paths are denied;
- destructive shell patterns are denied; and
- only the three tool-limited PKStack subagents are allowed/trusted.

Kiro's documented V3 default allows a small set of common read-only Git and
system-information commands and asks for unmatched operations. Removing an
agent-scoped ask does not grant permission. It lets existing user, workspace,
and session allowances take effect, or leaves the operation to normal approval.
An explicit ask in any scope overrides an allow in another scope and cannot be
removed by saving another allow. The profile therefore does not use blanket asks
as a substitute for first-use consent. Kiro may offer a remembered approval for
an implicit ask when it can derive a working saved rule; Kiro-owned protected-path
asks and explicit user/workspace asks still require approval.

Installed Kiro 2.20.2 testing found that delegated child shell permission
effects did not reliably constrain a shell tool after parent-authorized spawn,
while omitting `shell` from the child tool set did. PKStack therefore does not
give any delegated profile a shell. Review `projectctl` verification commands
before authorizing them under the user's policy: the runner screens obvious
hazards but is not a sandbox and cannot prove an arbitrary project script is
read-only. The profile neither preapproves those scripts nor overrides a user's
existing shell allowance.

These rules apply only after selecting the `pkstack` profile; plain `--v3` uses
the ambient default agent and does not inherit them. Native Plan hands approved
work to Default; native Spec uses its own planning and task agents. Shared skills,
steering, and explicit acceptance context carry the PKStack workflow through those
transitions, not inheritance of the primary profile's prompt or permissions.
An explicit return to `pkstack` activates its profile again. Restrictions intended
to apply across all agents belong in user/workspace policy, which PKStack does not
silently edit. The installed help still
exposes `--trust-all-tools` and `--trust-tools`
compatibility switches even though V3 documentation emphasizes capability
permissions. PKStack does not depend on those broad switches.

The same permission profile is selectable in Kiro IDE 1.x. Kiro Web does not
offer the corresponding project permission YAML or interactive-approval
surface and cannot select `pkstack` as its primary agent, so Web support rests
on projectctl's deterministic checks rather than a claimed replication of the
IDE/CLI permission boundary. Crew adds its own orchestration and security
layers; those do not weaken or replace PKStack verification.

### Hooks

V3 hook files use standalone documents and PascalCase triggers:

```json
{
  "version": "v1",
  "hooks": [
    {
      "name": "example",
      "trigger": "SessionStart",
      "action": { "type": "command", "command": "printf '%s\\n' ready" }
    }
  ]
}
```

The enabled SessionStart hook prints static orientation and does not run
repository code. The Stop probe is disabled and advisory. Kiro's
[exit-code reference](https://kiro.dev/docs/cli/reference/exit-codes/) documents
blocking for PreToolUse, not Stop as an autonomous-loop controller. A Stop hook
therefore does not enforce verified-goal continuation.

### Repo-local projectctl runtime

Bootstrap ships a fixed `uv.lock` and generated runtime metadata with
`[tool.uv] package = false`. `.pkstack/bin/projectctl` changes to the repository
root, prepares the locked controller environment, and executes the source with:

```text
uv sync --quiet --locked --no-config --project .pkstack/projectctl
PYTHONPATH=.pkstack/projectctl/src \
  .pkstack/projectctl/.venv/bin/python -B -X pycache_prefix=/dev/null \
    -m pkstack
```

The control plane receives `.pkstack/projectctl/src` through `PYTHONPATH`, which
avoids ambient project packaging and dependency drift. Before a user verifier
starts, the runner restores the caller's original `PYTHONPATH` and strips its
private markers. Bytecode writes are disabled and the null cache prefix keeps
the interpreter from trusting a repository-local cache. Because `uv sync` is a
completed child rather than the parent runtime, controller `PATH`,
`VIRTUAL_ENV`, and `UV_*` values do not leak into proofs. Kiro still asks before
the selected profile's projectctl shell patterns.

## Why `/pkstack-verified-goal` is a current-session seam

The loop uses native Kiro execution without replacing it:

1. The user invokes `/pkstack-verified-goal <objective>` in the existing Kiro agent
   session.
2. The skill uses only `.pkstack/bin/projectctl`.
3. It inspects existing state and starts schema version 3 state with one
   executable contract and a bounded budget.
4. The same Kiro agent implements the smallest evidence-backed change and runs
   one `goal verify` attempt.
5. Projectctl owns the contract digest, attempt count, history, and the wire
   statuses `active`, `passed`, and `exhausted`.
6. Kiro reports completion only after the stored verifier reaches `passed`.

Native subagents may assist with bounded diagnosis or review. Their opinion is
not proof. `/spawn` would create another user session, and a nested Kiro process
or external ACP host would abandon ordinary current-session interaction, so
none is part of the primary IDE/CLI loop. Kiro Crew may communicate with its
Kiro runtime over ACP internally; when Crew owns the active session, that is
not a user-selected external host and does not change the verified-goal
contract. There is no state-replacement shortcut; any previous state must be
inspected and deliberately cleared.

## Native `/goal` and feature-gate drift

Kiro's current [Goal page](https://kiro.dev/docs/cli/chat/goal/) and
[slash-command reference](https://kiro.dev/docs/cli/reference/slash-commands/)
describe native `/goal`. The documented loop runs up to five iterations by
default and accepts `--max`.

The installed runtime disagrees. In a sterile disposable home/config workspace,
one real interactive Kiro CLI 2.21.0 V3 TUI received `/goal clear`. It entered
`Thinking...`, consumed 0.09 credits, and answered as if that text were an
ordinary prompt; `/quit` then exited normally. That is conclusive for this
tested build/account/session: native `/goal` is not exposed here. Top-level
help, implementation strings, and the rejected historical
`chat.enableWorkflows` setting are not substitutes for that interactive proof.
The sanitized observation and cryptographic hashes of the externally retained
raw session files are in
[`reviews/kiro-v3-native-goal-probe.json`](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/kiro-v3-native-goal-probe.json).

`/pkstack-verified-goal` remains a separate, portable repository-visible executable
acceptance contract even when native goal support becomes available. PKStack
neither invokes nor requires native `/goal`. Any future integration must
feature-detect behavior after Kiro updates and must not weaken the stored
verifier.

## ACP boundary

Normal planning, implementation, and verification stay in the current Kiro
session. Only `projectctl knowledge search` invokes `kiro-cli acp`, using an
isolated read-only worker for bounded retrieval. That command requires the
verified Kiro CLI runtime and the shipped Python ACP client. Local knowledge
validation and the current-session goal loop require no ACP worker or external
ACP host. See [knowledge usage](usage.md#use-project-knowledge) for runtime and
evidence limits.

Kiro Crew also runs Kiro CLI over ACP and reads the existing `.kiro`
configuration. PKStack is compatible with that optional Kiro product; Crew's
transport is separate from the bounded knowledge worker and does not change
the default interactive entry path.

The committed project `.kiro/skills/` tree is the portable skill authority;
PKStack does not require a second copy under Crew's global data directory.
Crew must trust and open the intended project before project-local resources
are treated as available. Crew's own memory, task runner, schedules, security
hooks, and gateway lifecycle remain Crew-owned features. They are not aliases
for Kiro's repository hooks, and PKStack does not add a lifecycle bridge
between them.

Kiro Crew [PR #5129](https://github.com/kirodotdev/KiroCrew/pull/5129)
fixed Task Runner compaction so the shared session path marks the skill index
for reinjection. The current Nightly postdates that merge, but this snapshot
does not promote source history into a live initial-skill, hook, or
post-compaction parity claim. Alternate Crew agent harnesses are likewise
capability-dependent; PKStack's required compatibility target is the current
Kiro CLI-backed path.

The bounded [KiroCrew Nightly smoke record](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/kirocrew-nightly-smoke-campaign.md)
verified the Sep. 3 package source, bundle identity, signature, notarization, public version/help
surface, and doctor dependencies. It did not exercise `.kiro` ingestion, Task Runner, skill
reinjection, Spec, or `/pkstack-verified-goal`. The smoke also found that a CLI invocation rewrote bundled
Python `.pyc` files and invalidated the post-launch signed seal despite
`PYTHONDONTWRITEBYTECODE=1`. The mutated copy was retained recoverably and a fresh exact signed
bundle was restored without another invocation. This is an upstream packaging limitation, not a
PKStack source mutation.

The selected-profile V3 campaign also exposed Kiro's internal implementation
naming: its logs label session creation/prompt and policy evaluation with ACP
terms, route ordinary `KIRO_CLI` turns through an `ACPEventAdapter`, and export
skill-disclosure and native-subagent-response records with `toolOrigin: "acp"`.
No turn shell command launched ACP, another Kiro process, or `/spawn`. That
campaign therefore proves the ordinary CLI v3 user-facing path and no external
ACP harness, not control over Kiro's private adapter names or every Kiro
surface.

## Models, effort, and verification methodology

The reviewed Kiro documentation lists all three GPT-5.6 tiers as experimental,
with 272,000-token context windows: Sol at a 2.4x credit multiplier, Terra at
1.0x, and Luna at 0.1x. The active account's 2026-09-03 live listing returned
all three exact IDs and `auto` as its default. That point-in-time evidence is
recorded in [`reviews/kiro-model-guidance-evidence.json`](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/kiro-model-guidance-evidence.json);
documentation is not substituted for account availability, and one listing is
not a promise that an experimental model will remain available.

PKStack's interactive policy follows Kiro's task-based guidance instead of
retaining a Cursor-era fixed-model role:

| Work | Starting choice | PKStack consequence |
| --- | --- | --- |
| General development | Auto | Inherit the user's normal Kiro choice. Organizations that must restrict processing to an approved model should block Auto and select that model explicitly because Auto may route to any generally available model in-region. |
| Hardest long-horizon or security-sensitive work | GPT-5.6 Sol | Select explicitly only when the task justifies its 2.4x multiplier and deeper reasoning. The real acceptance campaign used this tier. |
| Routine multi-step implementation | GPT-5.6 Terra | Prefer the balanced 1.0x tier when peak Sol capability is unnecessary. |
| High-frequency bounded work | GPT-5.6 Luna | Prefer the 0.1x tier when speed and credit efficiency matter most. |

### Auto as its own model selection

Auto is a first-class Kiro model choice with Kiro-managed routing and fallback. It is not an
alias for an unspecified user choice or a fixed underlying model. Kiro recommends it for general
development and lists a 1.0x credit multiplier. The model overview does not specify a fixed Auto
context window. Kiro describes Sonnet-class-or-better quality for free tiers and Opus-class-or-better
for paid tiers; those are provider positioning claims, not PKStack benchmark results.

Auto has its own allow/block governance setting. Its internal router can use generally available
models in-region regardless of an administrator's individual-model allowlist; experimental models
are excluded. Where an exact approved provider/model is required, select that approved model.

PKStack preserves the selected `auto` identity in retrieval receipts. The existing
`resolved_model: null` means **underlying model not disclosed**, not **selection unknown**.
Report the selection as **Auto (Kiro-managed routing)** and keep underlying identity and internal
token use unknown unless runtime evidence actually supplies them. Auto's effort capabilities must
come from the active Kiro picker; do not borrow Sol or Opus effort settings. Ordinary PKStack
work leaves the user's selection unchanged.

Verified 2026-09-06 against [Kiro's model overview](https://kiro.dev/docs/models/),
[Auto's description](https://kiro.dev/docs/models/available-models/#auto-recommended), and
[reasoning effort](https://kiro.dev/docs/models/effort/). This documentation establishes product
semantics, not which underlying model processed a particular native-session test.

### Explicit model effort

The GPT-5.6 effort schema documents `none`, `low`, `medium`, `high`, `xhigh`,
and `max`, with `high` as the default. This installed CLI's help exposed
`low` through `max`; it did not establish `none` locally. Kiro exposes effort
selection in IDE and CLI, not Web or Mobile. There is no documented Kiro
`ultra` value. Higher effort uses more credits, and the CLI automatically
persists a `/effort` or `--effort` choice in the user's settings. Ordinary
PKStack instructions therefore omit model and effort flags. The exact Sol/max
launches elsewhere in this repository are evidence from deliberate acceptance
campaigns, not a recommended default; users who opt into one should select
their desired normal level afterwards.

Custom PKStack agents contain no `model` field and inherit the active session
selection. The scheduled self-maintainer is a narrower exception: it pins Sol
and requests max for one bounded high-risk reconciliation inside disposable
HOME/KIRO_HOME state, destroys that state, and fails closed rather than silently
substituting another model. The hosted path must confirm the exact model is
currently listed before it spends a repair attempt. Availability, lifecycle,
context, cost, and supported effort are versioned product facts rather than
PKStack constants.

Kiro documents that GPT-5.6 requests are served from the US regardless of the
profile's geography. Because the models are experimental, processing may also
occur in commercial AWS Regions worldwide, including outside the profile's
geography. Kiro's current [data-protection
documentation](https://kiro.dev/docs/privacy-and-security/data-protection/)
says that global cross-region inference does not change the region where data
is stored. It separately says that, for OpenAI GPT models, only
classifier-flagged traffic may be retained for up to 30 days for automated
offline abuse detection, in the Region where that inference was processed.
This is a scoped possibility, not a claim that any PKStack traffic was flagged
or retained. Users must evaluate those terms before sending
geography-restricted repository content; PKStack makes no broader residency or
retention claim.

The [OpenAI/AWS launch guidance](https://openai.com/index/gpt-5-6-in-kiro/)
emphasizes Kiro's structured requirements, technical designs, executable tasks,
checkpoint review, and property-based testing. PKStack preserves native
`/spec` rather than copying a Cursor planner. Kiro's current
[property-based spec testing](https://kiro.dev/docs/specs/correctness/) is
optional, IDE-only, and evidence rather than formal verification. It can
strengthen an applicable IDE spec, but PKStack does not claim it was run here
or require it on CLI, Crew, or Web. The same stored projectctl verifier remains
the portable completion predicate on every supported path.

## Known documentation and surface differences

1. **Native goal:** current CLI docs describe `/goal` and its five-iteration
   default, while a sterile interactive CLI 2.21.0 V3 probe showed that this
   installed runtime does not recognize it as a slash command.
2. **Hook examples:** current V3/Hook pages use standalone `version: "v1"`
   PascalCase documents, while some custom-agent material has shown older
   embedded forms. PKStack uses standalone V3 files.
3. **Trust flags:** V3 docs emphasize capability permissions; 2.20.2 help still
   exposes older trust switches. PKStack uses explicit rules.
4. **Resource inheritance:** Kiro pages have differed on default skill and
   steering inheritance. The profiles declare both resource globs explicitly.
5. **Agent formats:** docs accept JSON and Markdown. The installed validator was
   reliable for these JSON profiles, so PKStack ships JSON.
6. **Primary-agent selection:** IDE and CLI can select workspace custom agents;
   Kiro Web can only use project custom agents for delegation. Web therefore
   invokes workspace skills from its built-in primary agent.
7. **Skill arguments:** trailing skill text is request context across IDE, CLI,
   and Web, but `$ARGUMENTS` placeholder replacement is currently CLI-only.
   PKStack does not depend on the placeholder.
8. **Cloud and local configuration:** cloud configuration may be loaded into a
   new local session, but it is not written into `.kiro` and does not replace
   the bootstrap receipt's local authority.

## Remaining limits

- CLI v3 was selected explicitly with `--v3` in both the initial 2.20.2 snapshot
  and the later 2.21.0 campaign. The weekly canary detects stable CLI drift, but
  a human must review and promote the trust-root version/SHA tuple.
- Native `/goal` is documented but not exposed by the sterile interactive CLI
  2.21.0 V3 probe for this build/account/session. Re-probe after Kiro updates;
  PKStack does not invoke or depend on it.
- The IDE 1.0.437 native importer, setup, generated-agent selection, and
  separate command approvals passed a bounded smoke. The September 5 Standard
  and Quick Spec campaigns also completed same-tab handoff, recorded failure,
  implementation-only repair, and pass. These were two four-test fixtures,
  not every Spec mode or the Agent Focus view; see the
  [IDE campaign evidence](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/friends-ide-validation.md).
- Crew compatibility is required, but Crew is optional. The current signed Nightly passed a
  bounded command-surface/doctor smoke; no Crew project, Spec, skill, or end-to-end verified-goal
  campaign is claimed. Invoking that package may also rewrite bundled `.pyc` files and invalidate
  its signed seal until upstream moves runtime caches outside the signed bundle.
- Kiro Web is supported through committed project assets by design and remains
  explicitly untested. Its primary-agent and permission differences apply.
- Full custom-Power upload through Configuration Sync is unsupported: custom
  cloud Powers are text-only and limited to 50 files, while PKStack exceeds
  that shape.
- CLI `/powers` lists installed Powers. Current Kiro docs direct installation
  through the IDE or manual Power configuration; no `/powers` install
  subcommand or portable Power-skill slash namespace is documented.
- Diagnose discovery with the bare `/agent` picker, same-conversation selection,
  and `/config skills` first. Newly materialized skills may still need one
  explicit `--agent pkstack` chat; agent hot reload alone does not prove otherwise.
  The loaded goal loop itself does not start a replacement session.
- Stop is advisory, not a continuation guarantee.
- Kiro permissions reduce accidental authority but do not sandbox approved
  subprocesses.
- External Fable and Grok review is advisory, not Kiro-native proof.
- Native Kiro knowledge remains experimental. PKStack's local metadata,
  Markdown-link, and feature checks do not establish full OKF conformance;
  bounded retrieval is separate and requires a supported Kiro runtime.

## Compatibility validation commands

Run the [shared deterministic gate](https://github.com/njs14/pkstack/blob/main/docs/validation-report.md#deterministic-local-checks)
from the repository root. It includes Kiro asset tests and static checks.

Separately validate custom-agent templates against the actual installed CLI:

```sh
for profile in powers/pkstack/templates/project/.kiro/agents/*.json; do
  kiro-cli agent validate --path "$profile"
done
```

Schema validation does not establish discovery, selection, permissions, or native
workflow execution. Record those observations with their exact candidate, client
build, commands, and limits using the [release evidence contract](https://github.com/njs14/pkstack/blob/main/docs/validation-report.md#release-gate-record).
