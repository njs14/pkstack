# PKStack friends CLI validation

Recorded September 5, 2026. This report covers a bounded native terminal campaign;
an unfinished workflow is not a passing acceptance result.

## Runtime and budget

- Installed runtime: `kiro-cli 2.21.1` (`kiro-cli --version`).
- Native CLI help confirms interactive `chat --v3`, `--model`, and `--effort`.
- Selected model/effort: `gpt-5.6-luna`, `low`; both native headers confirmed it.
- Initial native `/usage`: **340.44 of 1,000 covered credits**, reset October 1,
  2026. This is an estimated account-wide counter, not a campaign-specific meter.
- The `/usage` view did not display the overage setting. No overage, global
  permission, OAuth, or account setting was changed; model and effort selection
  was limited to these sessions.
- Budget target: approximately 0.5 credits across the two small workflows.
  Native planning exceeded that estimate. Kiro's displayed turn costs total
  **1.21 credits**: Standard planning 0.47, Quick planning 0.61, each repair
  0.06, and the summary observation 0.01. These are rounded displayed values.
- Final native `/usage`: **343.46 of 1,000**, an account-wide increase of **3.02**
  from the initial reading. Other CLI validation work ran concurrently, so the
  account difference cannot be attributed exclusively to this campaign.
- The initial slash-command-only session was
  `sess_8b017028-f3bf-4275-b99b-ffb28f2dc0d6`; it made no model request and ended
  normally before candidate setup.

No ACP host, headless mode, trust-all option, credential inspection/copy, or new
API key is part of this campaign. Each requested native tool approval is
reviewed in the terminal. Native Spec agents may perform actions already
permitted by Kiro's own profile.

## Disposable fixtures

Campaign root: `/private/tmp/pkstack-friends-cli.OWqdyU`.

| Workflow | Consumer directory | Native spec name |
| --- | --- | --- |
| Standard Spec | `standard/` | `account-standard` |
| Quick Spec | `quick/` | `account-quick` |

Both independent Git workspaces contain an intentionally incomplete
`normalize_account_id` implementation and the same four account-ID acceptance
tests as the canonical example. Expected behavior removes spaces and hyphens,
accepts exactly twelve digits, and raises `ValueError` mentioning `12 digits`
for invalid input. Tests are read-only and must remain unchanged.

```sh
python3 -B -m unittest discover -s tests -v
shasum -a 256 account.py tests/test_account.py
```

Both baselines ran four tests with three failures. Initial implementation SHA-256:
`842fa46ea0e490b70d652f09e0c86ed6963c81c0cfeb73cf5ab26f219fb704aa`.
Acceptance test SHA-256:
`65932341be2d1b133366ec58e583f224751f1f89b9d8d26ebfeb897cab664974`.

## Campaign result

**Both workflows passed** their stored Spec-bound verifier after the required
failure and one implementation-only repair. Each remained in its original
interactive conversation through native planning, `/agent swap pkstack`,
`/pkstack-verified-goal`, failure, repair, and pass.

The command used in each consumer was:

```sh
env PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  kiro-cli chat --v3 --agent pkstack --model gpt-5.6-luna --effort low
```

Both sessions ended normally after their final readbacks:

| Workflow | Native conversation ID | PTY session ID |
| --- | --- | --- |
| Standard | `sess_ce125139-11e4-48ca-8a2f-531db9191112` | `43984` |
| Quick | `sess_22fd7a09-b24c-4859-9450-ee7e0df77ce3` | `40513` |

### Native planning

Standard used `/spec new account-standard`, selected **Build a Feature**, then
**Requirements**, and continued through the native requirements/design/tasks
review checkpoints. Kiro used `feature-requirements-first-workflow` and four
`requirement-detailer` subagents. The design checkpoint caught an out-of-scope
property-testing proposal; native feedback revised it to defer property tests
outside this immutable four-test campaign. The final task checkpoint selected
**Not now**. Kiro's `.config.kiro` records `workflowType: requirements-first`,
`specType: feature`, and spec ID `f7c67fd6-71fe-41b8-abc4-d56fa009dcde`.

Quick used `/spec new account-quick`, explicitly selected native **Quick Spec**,
and used `fast-task-workflow`. Native clarification confirmed removal of every
space/hyphen and an error message containing `12 digits`. Kiro repaired its own
requirements/design format-validation issues before producing the task plan.
The offered execution checkpoint was cancelled before any application edit;
all three planning documents were complete. Its `.config.kiro` records
`workflowType: fast-task`, `specType: feature`, and spec ID
`6810c258-4600-4c1c-99c0-ab5170be59d9`. The route is established by the native
selection, observed subagent, and native metadata, not inferred from filenames.

Both planning paths read the actual account implementation and tests. Independent
SHA-256 checks after planning confirmed that both implementation and tests still
matched their failing baselines. No Spec directory or planning document was
authored by the supervising Codex agent.

### Same-conversation verification

After `/agent swap pkstack`, each request invoked `/pkstack-verified-goal` and
explicitly preserved tests, native planning artifacts, managed files, and the
acceptance command. Kiro disclosed the actual skill, read the fixture and Spec
package, inspected goal status and the empty feature registry, bound the native
Spec, and displayed the stored command and Spec provenance before verification.

These are the commands run by Kiro; Standard quoted the runner path and combined
its bind/start calls with `&&`:

```sh
.pkstack/bin/projectctl goal status --output json
.pkstack/bin/projectctl feature list --output json
.pkstack/bin/projectctl goal bind-spec account-standard \
  --command "python3 -B -m unittest discover -s tests -v" --output json
.pkstack/bin/projectctl goal start "Implement account-standard" \
  --spec account-standard --max-attempts 4 --output json
.pkstack/bin/projectctl goal verify --output json
# After the recorded failure, Kiro edited account.py only.
.pkstack/bin/projectctl goal verify --output json
.pkstack/bin/projectctl goal status --output json
```

The Quick consumer ran the corresponding `account-quick` bind/start commands and
the same status/list/verify commands. Before its first status call, Kiro also
used `test -x .pkstack/bin/projectctl`. No goal clear, resume, overwrite, feature
publication, or commit was used.

| Workflow | Goal ID | Recorded attempts | Terminal result |
| --- | --- | --- | --- |
| Standard | `553dbfea-bab5-40c0-b4c4-b5b86ab3178a` | 1: exit 1, three failures; 2: exit 0, four tests pass | `passed`, 2 of 4 |
| Quick | `dca42991-99af-4020-bc9f-477a678424bb` | 1: exit 1, three failures; 2: exit 0, four tests pass | `passed`, 2 of 4 |

Stored histories reside in each consumer's `.pkstack/state/goal.json`. Standard's
failure/pass timestamps are `2026-09-05T12:33:24.543608+00:00` and
`2026-09-05T12:34:03.609028+00:00`; Quick's are
`2026-09-05T12:35:23.546298+00:00` and
`2026-09-05T12:36:44.867070+00:00`. Both failures were independently read while the
implementation write was still pending approval and its hash still matched the
initial failing fixture.

The contract has `source: spec` with the correct native spec name in each case.
The digest stayed unchanged from recorded failure through pass:

- Standard: `8351409d06b421b503db86c61ba16538c8ace22f138e5897e5ff35efb89348aa`.
- Quick: `3779abf581c76be9502a3c5d899ca530fcd18330552444d4fc6f47c4134605aa`.

Both repairs remove literal spaces/hyphens, validate length/digit content, and
raise the required `ValueError`. Standard uses message `12 digits`; Quick uses
`account ID must contain 12 digits`. The final implementation hashes are
`52d5e759718f19107a591bae4f2fc475b44bebc6d176ac76460d38bd07e73f6e`
and `8a56132733e0e940408f6a892b64181472f19af0f482386cf64da046980b9f9e`,
respectively. The immutable test hash remains
`65932341be2d1b133366ec58e583f224751f1f89b9d8d26ebfeb897cab664974` in both.

The three planning-document hashes also stayed unchanged across each repair:

| Workflow / document | SHA-256 |
| --- | --- |
| Standard `requirements.md` | `c8aa27395448cc79dbcf5b47bdf55380a98e9194937502c192c4636cf33360db` |
| Standard `design.md` | `aeb8d1c1fcdbced693770ddb682a76268966d0b6bcb122bac3fa654cb188f14c` |
| Standard `tasks.md` | `788f0f4ef417b8763a7432ae8ddc33db7d563477a2b8a447795848f2a75d8f9e` |
| Quick `requirements.md` | `60cad029d102dbb3672ad0248827c67cbe97e41d8b13e9887ba0d02bad2635b2` |
| Quick `design.md` | `f096421361a1be7efd0a7d7c15b606f6a99947a66a51ef0a0d50bed8b7c0d8c0` |
| Quick `tasks.md` | `6be7c53fa68154d870bfabd88e43ae654e889a6dbd5f9b52bde34f61699c617d` |

### Ambiguous existing-evidence routing

In the completed Standard conversation, the exact request **Show me what you
did.** caused actual `git diff -- account.py`, `git status --short`, and an
`account.py` read. Kiro returned the repaired function and existing four-test
result. It correctly explained that `git diff` was empty because the disposable
fixture files were untracked. No `show-me`, `show-me-your-work`, Archify, new
evidence-log, or write tool was activated.

The complete relevant consumer inventory, including file paths and SHA-256
content hashes, was identical before and after this observation:
`4553a5953557561457fb927a485c460291f5352c2c44a11abe8c41c82211e62a`.
The inventory excluded only `.git/`, the generated `.venv/`, and Python caches:

```sh
rg --files --hidden -g '!.git/**' -g '!.pkstack/projectctl/.venv/**' \
  -g '!**/__pycache__/**' . | LC_ALL=C sort | xargs shasum -a 256 | shasum -a 256
```

This is one observed ambiguous request in a seeded conversation, not a measured
success rate for all 30 routing fixtures. The explicit `/show-me` observation
belongs to the separate curated-skill campaign.

## Frozen consumer setup

The campaign used the source at
`/private/tmp/pkstack-friends.a1lG4m/powers/pkstack` after the skill/steering freeze.
Bare `python3` resolved to macOS Python 3.9.6 and the default PATH omitted `uv`;
the initial preview stopped with `PKStack setup requires Python 3.11+ or uv` and
made no setup writes. A process-local PATH containing Homebrew fixed that
prerequisite. Homebrew supplied Python 3.14.7 and `uv` 0.12.9.

```sh
env PATH=/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  python3 /private/tmp/pkstack-friends.a1lG4m/powers/pkstack/skills/pkstack-setup/scripts/setup_pkstack.py \
  --root /private/tmp/pkstack-friends-cli.OWqdyU/standard --dry-run --output json
# Repeat without --dry-run, then repeat preview and apply for quick/.
env PATH=/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  .pkstack/bin/projectctl doctor --output json
```

Both previews and installs succeeded, creating 170 files with zero conflicts or
stale managed files. Both consumers returned doctor **80 pass, zero fail, one
warning**: optional `okn` was unavailable in the scoped PATH. The campaign did
not install or otherwise alter `okn`.

These SHA-256 values were independently identical in both generated consumers.
The exercised PKStack instructions, profile, launcher, and controller hashes
were rechecked after repair:

| Consumer path | SHA-256 |
| --- | --- |
| `.kiro/skills/pkstack/SKILL.md` | `bc8301c2b629bf8f663706480d1ad47f1cbc3a3e04d9dac92142218c42f700da` |
| `.kiro/skills/pkstack-verified-goal/SKILL.md` | `1b00e371c3c7e253a481c06480eac419a8626a4045edd7bc688ba352c9d696d0` |
| `.kiro/skills/show-me/SKILL.md` | `70655d39c58b8d4716c70a827f1d2c93600f3192bdc20c427d078dcd87ae5e81` |
| `.kiro/steering/pkstack-core.md` | `012c1b2b55468d07ca02c5098ac5c88245dade3563a917306f22d82c5a7dceb9` |
| `.kiro/agents/pkstack.json` | `efcfe1a6ecbf9734289a3e452a9694f4121e38da9163bebb0c1d7219fca65bcc` |
| `.pkstack/projectctl/src/pkstack/goal.py` | `653b2a5b8990ff13974b3d40b11c0ff674ff5f7b6249ca0db1eab582fe4f9674` |
| `.pkstack/projectctl/src/pkstack/runner.py` | `4d9316dba9731bde157b79a8b7b875842ab2452c4c6dfcb8899f38853e432f8c` |
| `.pkstack/bin/projectctl` | `d90aadc9468a12b099f71f19c43353741f62f8884dc95a681d16acd1b0400b6f` |

After both campaigns, the generated controller source trees matched the
candidate's generated source tree byte-for-byte, excluding Python caches.
The later whole-skill-tree comparison found a `design-control-loop` instruction
change in the candidate after the initial freeze. That skill was not exercised
by this lane; its separate curated-skill campaign owns that validation. The
exercised PKStack/verified-goal/core instructions stayed at the hashes above.

## Limits and runtime observations

These are two small four-test consumer campaigns, not proof of every native
Spec mode, IDE execution, Unicode normalization case, permission boundary,
upstream updater run, or production release. Kiro's top-level headers confirmed
Luna/Low; this campaign did not separately attest the provider/model choice of
every built-in native subagent.

The requested tool approvals were reviewed without enabling future automatic
approvals. The two sessions nevertheless exposed a prompt difference: Quick's
unquoted `.pkstack/bin/projectctl ...` calls asked for command approval, while
Standard's quoted `".pkstack/bin/projectctl" ...` calls executed without a
separate prompt. Both implementation writes prompted, as did Standard's later
`git diff` and `git status` calls. This records the observed native runtime/profile
behavior; it does not establish the exact matching cause or claim that every
controller spelling is approval-gated. No destructive command was tested.

The only repository file authored by this lane is this report. All repair and
Spec artifacts remain in the disposable consumers. No product implementation,
acceptance test, public service, repository commit, or upstream state was changed
by this lane. No raw private reasoning or credential material was tracked.
