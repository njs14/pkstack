# Kiro CLI v3 compatibility

This is a point-in-time compatibility snapshot from **2026-09-01** on the
target Mac. It records the Kiro behavior used by PK-Stack, not a guarantee
for every account or later release. Re-run the checks at the end after a Kiro
upgrade.

## Compatibility decision

PK-Stack bootstraps through the ordinary interactive V3 experience:

```bash
kiro-cli chat --v3
```

After setup, `/agent swap pstack` attaches the generated repository-local
Poteto Kiro primary profile before the next workflow message. If Kiro has not
discovered it yet,
the fallback remains the same ordinary V3 runtime:

```bash
kiro-cli chat --v3 --agent pstack
```

The normal workflow remains in that selected session. Kiro owns execution and
native orchestration; PK-Stack supplies workflow skills and conventions; the
bootstrapped `.pstack/bin/projectctl` supplies deterministic project state and
evidence. Setup does not mutate the user's global default agent.

ACP, classic/V2, a nested Kiro process, and a separate `/spawn` session are not
the default path. The port also does not claim or require native `/goal` in V3.
`/verified-goal` is a thin current-session compatibility seam, not a recreated
runtime.

The initial 2026-09-01 snapshot reported application version `2.20.2`; the
selected-profile campaign on 2026-09-02 ran on Kiro CLI `2.21.0`. In both,
`--v3` selected the next-generation agent engine. “V3” is the
engine/configuration generation, not the macOS app's
`CFBundleShortVersionString`.

## Observed local snapshot

| Item | Observed result |
| --- | --- |
| Executable | `/Users/noahsutter/.local/bin/kiro-cli`, a symlink into `/Applications/Kiro CLI.app` |
| Initial CLI/app version | `2.20.2` |
| Later selected-profile validation | Kiro CLI `2.21.0` on 2026-09-02 |
| macOS app build | `20260831.180303` |
| Bundle identifier | `com.amazon.codewhisperer` |
| V3 selection | `kiro-cli chat --v3` or top-level `kiro-cli --v3` |
| V3 modes | `default`, `spec` |
| Effort names exposed by the CLI | `low`, `medium`, `high`, `xhigh`, `max` |
| Knowledge setting | `chat.enableKnowledge` is `true` on this Mac |
| Historical workflow setting | `chat.enableWorkflows` is rejected as invalid |
| Default model returned by the account | `auto` |
| GPT-5.6 Sol returned by the account | `gpt-5.6-sol`, 272,000-token context, 2.4x credit multiplier |

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
```

The two settings commands returned `true` and
`chat.enableWorkflows is not a valid setting`, respectively.

## V3 capability map

| Capability | Current V3 contract | PK-Stack use |
| --- | --- | --- |
| Specs | Native `/spec`, including `new`, `run`, `view`, and `analyze_requirements`; `--mode spec` is exposed by local help | Keep native requirements/design/task flow; accept only a small executable bridge for projectctl proof |
| Agent Skills | Workspace `.kiro/skills/<name>/SKILL.md` and global `~/.kiro/skills/`; slash invocation accepts trailing arguments | `/setup-pstack`, `/verified-goal`, architecture, arena, swarm, and advisory council workflows |
| Powers | Agent Plugins layout with root `plugin.json`, optional `skills/`, `mcp.json`, and `dev.kiro/` | Package and distribute PK-Stack guidance and its Power-local setup shim |
| Custom agents | Workspace `.kiro/agents/` or global `~/.kiro/agents/`; current docs accept JSON and Markdown | Ship four explicit JSON profiles validated by the installed CLI |
| Native subagents | Main agent delegates isolated work through the `subagent` tool; custom agents can be allow-listed | Bounded architecture, review, and verification assistance while the primary session owns edits/evidence |
| `/spawn` | User-driven command for a fresh parallel session | Not used for internal PK-Stack fanout or verified-goal iteration |
| Hooks | Standalone `.kiro/hooks/*.json`, `version: "v1"`, PascalCase triggers, command or agent actions | Static SessionStart orientation plus a disabled advisory Stop probe |
| Permissions | Capability rules with `allow`, `ask`, and `deny`; the most restrictive result wins | Allow workspace reads, ask for Git/writes/projectctl commands, and deny destructive patterns |
| Steering | `.kiro/steering/*.md` with `always`, `auto`, `fileMatch`, or `manual` inclusion | Two small always-on architecture/safety invariants |
| Knowledge | `/knowledge` and the `knowledge` tool are experimental; local knowledge is enabled | Preserve native knowledge as optional and delegate canonical Wiki operations to `okn` when installed |

Primary references:

- [What's new in Kiro CLI 3.0](https://kiro.dev/docs/cli/v3/)
- [Specs in CLI](https://kiro.dev/docs/cli/v3/specs/)
- [Agent Skills](https://kiro.dev/docs/cli/skills/)
- [Powers](https://kiro.dev/docs/powers/) and [Create powers](https://kiro.dev/docs/powers/create/)
- [Custom-agent configuration reference](https://kiro.dev/docs/cli/custom-agents/configuration-reference/)
- [Invoking custom agents as subagents](https://kiro.dev/docs/chat/subagents/)
- [Slash commands, including `/spawn`](https://kiro.dev/docs/cli/reference/slash-commands/)
- [Hooks](https://kiro.dev/docs/hooks/)
- [Permissions](https://kiro.dev/docs/cli/chat/permissions/)
- [Steering](https://kiro.dev/docs/steering/)
- [Experimental knowledge management](https://kiro.dev/docs/cli/experimental/knowledge-management/)

## Formats used by this port

### Power and skills

The root manifest uses Agent Plugins `plugin.json`. Skills are stored as
`skills/<lowercase-hyphenated-name>/SKILL.md` with `name`, `description`, and
optional `compatibility` frontmatter. `$ARGUMENTS` carries trailing slash-command
text.

The setup skill resolves `scripts/setup_pstack.py` relative to its loaded
Power. It always starts with a no-write preview. New managed content appears as
`pending_updates` until a reviewed run explicitly includes
`--update-managed`; user-modified files remain conflicts. Retired receipt-owned
paths appear as blocking `stale_managed` and are never pruned automatically.
After bootstrap, skills use `.pstack/bin/projectctl`, never repository
`./projectctl` or ambient `uv run projectctl` resolution.

Setup remains Power-local and is cached under
`.pstack/projectctl/skills/setup-pstack/`; bootstrap deliberately does not copy
it to `.kiro/skills/`, where an older workspace copy could shadow an upgraded
Power. The other five workflow skills are materialized in the workspace.
The cached `projectctl setup` surface requires an explicit `--power-root` and
cannot silently use its own stale cache as upgrade authority. After selecting
`pstack`, a managed refresh remains in the current chat: `/agent swap
kiro_default`, `/setup-pstack`, then `/agent swap pstack` (or use the local
Power-enabled agent name in place of `kiro_default`).
Setup also validates its required source modules and Power assets before target
writes. Its deterministic repository discovery uses sorted root-relative paths
and refreshes as an owned observation rather than a managed code upgrade.

Kiro can switch to the discovered Poteto Kiro primary agent in the current chat
with `/agent swap pstack`; its prompt, tools, and permissions apply beginning
with the next message. Newly copied workspace skills or agents may instead
require one `--agent pstack` restart for discovery. Once `/verified-goal` is
loaded, the implement/verify loop stays in that current session.

### Custom agents

The port uses JSON profiles because all four validate with the installed
`kiro-cli agent validate`. Each profile explicitly declares:

- short V3 tool tags such as `read`, `write`, `shell`, `subagent`, and
  `knowledge`;
- `skill://.kiro/skills/*/SKILL.md` and
  `file://.kiro/steering/**/*.md` resources;
- capability-based permission rules;
- `includeMcpJson: false` and `includePowers: false`; and
- no hard-coded model, so the user's active model is inherited.

The primary profile has the write tool and a subagent allow-list limited to
`pstack-architect`, `pstack-reviewer`, and `pstack-verifier`. All three
delegated profiles expose only `read` and `knowledge`; they omit both `write`
and `shell` and deny `fs_write`. The verifier inspects a contract and recorded
evidence, then returns the exact command for the primary session to execute.

### Permissions

The templates use agent-scoped capability rules instead of broad trust. Kiro's
current rules combine scopes with `deny > ask > allow`. In the shipped primary
profile:

- workspace reads are allowed, while every Git shell command asks;
- filesystem writes ask, while direct writes to bootstrap-managed control-plane
  paths are denied;
- every canonical `.pstack/bin/projectctl` invocation asks;
- destructive shell patterns are denied; and
- only the three tool-limited PK-Stack subagents are allowed/trusted.

Kiro's documented V3 default allows a small set of common read-only Git and
system-information commands and asks for unmatched shell operations. The
profile's explicit Git `ask` therefore overrides the ambient Git allow under
the same `deny > ask > allow` algorithm; other unmatched shell commands still
prompt rather than running silently.

Installed Kiro 2.20.2 testing found that delegated child shell permission
effects did not reliably constrain a shell tool after parent-authorized spawn,
while omitting `shell` from the child tool set did. PK-Stack therefore does not
give any delegated profile a shell. Primary-session `projectctl` commands still
ask, because the runner screens obvious hazards but is not a sandbox and cannot
prove an arbitrary project script is read-only.

These rules apply only after selecting the `pstack` profile; plain `--v3` uses
the ambient default agent and does not inherit them. The installed help still
exposes `--trust-all-tools` and `--trust-tools`
compatibility switches even though V3 documentation emphasizes capability
permissions. PK-Stack does not depend on those broad switches.

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
`[tool.uv] package = false`. `.pstack/bin/projectctl` changes to the repository
root, prepares the locked controller environment, and executes the source with:

```text
uv sync --quiet --locked --no-config --project .pstack/projectctl
PYTHONPATH=.pstack/projectctl/src \
  .pstack/projectctl/.venv/bin/python -B -X pycache_prefix=/dev/null \
    -m pstack_kiro
```

The control plane receives `.pstack/projectctl/src` through `PYTHONPATH`, which
avoids ambient project packaging and dependency drift. Before a user verifier
starts, the runner restores the caller's original `PYTHONPATH` and strips its
private markers. Bytecode writes are disabled and the null cache prefix keeps
the interpreter from trusting a repository-local cache. Because `uv sync` is a
completed child rather than the parent runtime, controller `PATH`,
`VIRTUAL_ENV`, and `UV_*` values do not leak into proofs. Kiro still asks before
the selected profile's projectctl shell patterns.

## Why `/verified-goal` is a current-session seam

The loop uses native Kiro execution without replacing it:

1. The user invokes `/verified-goal <objective>` in the existing V3 chat.
2. The skill uses only `.pstack/bin/projectctl`.
3. It inspects existing state and starts schema version 2 state with one
   executable contract and a bounded budget.
4. The same Kiro agent implements the smallest evidence-backed change and runs
   one `goal verify` attempt.
5. Projectctl owns the contract digest, attempt count, history, and the wire
   statuses `active`, `passed`, and `exhausted`.
6. Kiro reports completion only after the stored verifier reaches `passed`.

Native subagents may assist with bounded diagnosis or review. Their opinion is
not proof. `/spawn` would create another user session, and a nested Kiro process
or external ACP host would abandon ordinary current-session interaction, so
none is part of the loop. There is no state-replacement shortcut; any previous
state must be inspected and deliberately cleared.

## Native `/goal` and feature-gate drift

Kiro's current [Goal page](https://kiro.dev/docs/cli/chat/goal/) and
[slash-command reference](https://kiro.dev/docs/cli/reference/slash-commands/)
describe native `/goal`, and the installed application contains related
implementation strings. That is not enough to assert availability for this
specific V3 account/session:

- slash commands are resolved inside interactive sessions, not established by
  top-level help alone;
- the historical `chat.enableWorkflows` flag is invalid in this build; and
- documentation, account rollout, and engine selection can move separately.

Accordingly, PK-Stack does **not** claim or require native V3 `/goal`.
`/verified-goal` remains useful as a repository-visible executable acceptance
contract even if native goal support later becomes universal. Any future
integration must feature-detect native behavior and must not weaken the stored
verifier.

## ACP boundary

The binary exposes an `acp` subcommand and ACP-oriented stream output, but
PK-Stack does not invoke `kiro-cli acp` or require an external ACP host. ACP can
remain an option for an external host; it is not the normal Power experience
and is unnecessary for the current-session loop.

The selected-profile V3 campaign also exposed Kiro's internal implementation
naming: its logs label session creation/prompt and policy evaluation with ACP
terms, route ordinary `KIRO_CLI` turns through an `ACPEventAdapter`, and export
skill-disclosure and native-subagent-response records with `toolOrigin: "acp"`.
No turn shell command launched ACP, another Kiro process, or `/spawn`. PK-Stack
therefore promises the ordinary V3 user-facing path and no external ACP
harness, not control over Kiro's private adapter names.

## Models and effort

The account's live listing includes `gpt-5.6-sol` with a 272,000-token context
window and 2.4x credit multiplier. The installed help exposes `low`, `medium`,
`high`, `xhigh`, and `max`. There is no documented Kiro `ultra` value.

An explicit launch is:

```bash
kiro-cli chat --v3 --agent pstack --model gpt-5.6-sol --effort max
```

The runtime should validate a model/effort pair because account availability
and supported effort can change. Custom PK-Stack agents do not hard-code a
model.

## Known documentation and binary inconsistencies

1. **Native goal:** web docs describe `/goal`; local noninteractive evidence
   does not establish account/session exposure.
2. **Hook examples:** current V3/Hook pages use standalone `version: "v1"`
   PascalCase documents, while some custom-agent material has shown older
   embedded forms. This port uses standalone V3 files.
3. **Trust flags:** V3 docs emphasize capability permissions; 2.20.2 help still
   exposes older trust switches. This port uses explicit rules.
4. **Resource inheritance:** Kiro pages have differed on default skill and
   steering inheritance. The profiles declare both resource globs explicitly.
5. **Agent formats:** docs accept JSON and Markdown. The installed validator was
   reliable for these JSON profiles, so the port ships JSON.

## Remaining limits

- V3 was selected explicitly with `--v3` in both the initial 2.20.2 snapshot
  and the later 2.21.0 campaign. Recheck every Kiro update.
- Power installation UX may remain Kiro UI-mediated even though this repository
  is an Agent Plugins package.
- Newly materialized skills or agents may need one explicit `--agent pstack`
  chat for discovery; the loaded goal loop itself does not start a replacement
  session.
- Stop is advisory, not a continuation guarantee.
- Kiro permissions reduce accidental authority but do not sandbox approved
  subprocesses.
- External Fable and Grok review is advisory, not Kiro-native proof.
- Knowledge is experimental and broad OKF behavior requires canonical `okn`.

## Compatibility validation commands

Run the Kiro asset tests without inheriting this project's pytest coverage
options:

```bash
uvx --isolated --no-cache --no-config --with 'PyYAML>=6,<7' \
  pytest -o addopts='' -p no:cacheprovider tests/test_kiro_assets.py -q
```

Lint the asset checks:

```bash
uvx --isolated --no-cache --no-config \
  ruff check tests/test_kiro_assets.py
```

Validate every installed custom-agent template against the actual CLI:

```bash
for profile in templates/project/.kiro/agents/*.json; do
  kiro-cli agent validate --path "$profile"
done
```

Run Python integration tests and type/lint checks from the repository:

```bash
uv run ruff check src tests
uv run ty check
uv run pytest -q
```

The final exact outcomes, end-to-end commands, and remaining limitations belong
in the repository's validation report rather than being inferred from this
format contract.
