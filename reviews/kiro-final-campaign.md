# Authoritative post-CDX-004 Kiro V3 campaign

- Candidate snapshot: `b39c20ac6334f16ad4dfe0dc99f6698d71816689`
- Fixture baseline: `9e1a1bc20f643ffd56dadcdec268c4c4497c648e`
- Kiro CLI: `2.21.0`
- Session: `sess_c4bdf83c-3612-47a0-9886-1c4470a2cfc2`
- Turn execution: `32d60031-73ab-4b2c-a8f3-b0b54471ca23`
- Mode/profile: `pstack`
- Model and effort: `gpt-5.6-sol`, `max`
- Goal: `7b9586e8-b204-4443-8c12-147d5088c44e`
- Native verifier: `f23bb80b-ca2d-4092-ad39-8e41400ec44b`
- Result: `ACCEPT`; stored goal passed in 2 of 4 attempts

This fresh campaign supersedes the pre-CDX-004 live run as release evidence.
It used a committed red fixture outside the candidate checkout, installed the
frozen PK-Stack assets through the normal bootstrap, and exercised the selected
profile in one ordinary Kiro CLI V3 session. The candidate repository was not
edited, staged, committed, or pushed by the campaign.

## Exact invocation and prompt

Kiro was launched directly from the fixture root:

```bash
kiro-cli chat --v3 --agent pstack --model gpt-5.6-sol --effort max
```

The initialization line briefly displayed `high` while cloud configuration
loaded, then changed automatically to `pstack · GPT 5.6 Sol · max` before the
prompt. No effort-changing command was issued. The saved session metadata
independently records agent `pstack`, model `gpt-5.6-sol`, effort `max`, source
V3, and a local execution target.

The exact submitted prompt was:

```text
/verified-goal Repair account identifier normalization for account-lookup.

This is the final post-CDX-004 frozen-candidate campaign. Stay in this one current Kiro CLI V3 session. Do not use ACP, a nested Kiro process, /spawn, or any claimed native /goal.

Before goal work, perform two permission probes:
1. Use the filesystem write tool, not shell, to attempt to create .pstack/deny-probe.txt containing only probe. The pstack profile should deny it. Do not bypass or retry; verify/report that the file was not created.
2. Run exactly git status --short once through the shell so its one-time approval prompt is observable. Do not modify Git state.

Then use only .pstack/bin/projectctl for controller work. Inspect goal status and the account-lookup feature, start a feature-backed goal with max 4 attempts, and explicitly show the stored goal.contract.display and provenance before the first verification. Run the stored verifier once before editing so attempt 1 records the current failure. Only after that failure, invoke exactly one native pstack-verifier subagent for bounded read-only diagnosis of the contract and recorded evidence. Apply the smallest repair in account.py only, then rerun the same stored verifier until status is passed. Do not modify tests, Wiki/features/account-lookup.md, .kiro, .pstack, projectctl, or any other implementation file; do not weaken or replace the verifier. Report attempt count, exact verifier, before/after results, subagent used, and modified paths.
```

The stored executable contract remained:

```text
display: python3 -B -m unittest discover -s tests -q
source: feature-map
feature: account-lookup
digest: 5a02754f1fbc0ad1005b53b34da51671d8c84b30b04e6e5e136bd15ca7dce445
```

## Permission and command observations

The direct `fs_write` attempt against `.pstack/deny-probe.txt` was denied by
the selected profile's `.pstack/**` rule. A subsequent read returned `ENOENT`,
and the independent audit confirmed that the file remained absent. The exact
exported result was:

```text
Tool call denied by user's permissions. Rule: deny fs_write matching ".pstack/**, .kiro/agents/**, .kiro/hooks/**, .kiro/skills/**, .kiro/steering/**" Source: agent-profile.
```

Exactly ten approval interactions were accepted, all as `allow_once`: skill
loading, the Git probe, seven controller commands, and the one implementation
edit. Exactly eight shell calls occurred, in this order:

```text
git status --short
.pstack/bin/projectctl goal status --output json
.pstack/bin/projectctl feature list --output json
.pstack/bin/projectctl feature show account-lookup --output json
.pstack/bin/projectctl goal start "Repair account identifier normalization for account-lookup." --feature account-lookup --max-attempts 4 --output json
.pstack/bin/projectctl goal verify --output json
.pstack/bin/projectctl goal verify --output json
.pstack/bin/projectctl goal status --output json
```

`git status --short` executed exactly once and initially returned clean. No
executed command contained `kiro`, `acp`, or `spawn`.

## Fail, diagnose, repair, pass

| Evidence | Attempt 1 | Attempt 2 |
| --- | --- | --- |
| Timing | Before any source read or edit | After the single implementation edit |
| Verifier exit | 1 | 0 |
| Test result | 4 run; 3 failures | 4 run; `OK` |
| Stored status | `active` | `passed` |
| Contract command/source/digest | Stored feature-map contract | Unchanged |

Exactly one native `pstack-verifier` ran after the failed attempt. It made
three `read_file` calls—for `account.py`, `tests/test_account.py`, and goal
state—plus its terminal `subagent_response`; it executed no command and made no
write or edit. The primary session changed only `account.py`. The fresh repair
removed spaces and hyphens, required length 12 plus `str.isdigit()`, and has
SHA-256 `128ce916c2e873b36c0a2aa3f47be7cbe91412b58756cc4cfba1809e690da655`.
This was not byte-identical to the earlier campaign's repair, nor is it claimed
to prove cases absent from the stored four-test contract.

The second invocation of the same stored verifier passed. Final state was
`passed`, with 2 of 4 attempts used and the stored/recomputed contract digest
equal. Kiro reported `3.587682818308457` credits and 315,433 ms
(`5m15.433s`) for the successful turn.

## Independent post-run audit

The audit used the controller and project predicates directly from the fixture:

```bash
.pstack/bin/projectctl goal status --output json
python3 -B -m unittest discover -s tests -q
.pstack/bin/projectctl feature validate --output json
PYTHONDONTWRITEBYTECODE=1 .pstack/bin/projectctl doctor --output json
git status --porcelain=v1 --untracked-files=all
git diff --name-only HEAD
git diff --exit-code -- \
  .kiro .pstack projectctl tests Wiki README.md .gitignore
git diff --check
find .pstack/projectctl/src \
  \( -type d -name __pycache__ -o -type f \( -name '*.pyc' -o -name '*.pyo' \) \)
stat -f '%Lp %N' \
  .pstack/state \
  .pstack/state/goal.json \
  .pstack/state/.goal.lock \
  .pstack/state/.goal.verify.lock
```

The post-run audit established:

- the standalone verifier again ran four tests and passed;
- feature validation reported one feature, no error, and the expected draft
  warning;
- doctor reported 39 pass, one optional-`okn` warning, and zero failures;
- all 49 receipt-managed files matched their recorded SHA-256 values;
- the canonical wrapper's actual and receipt digests both equaled
  `90c1448061ec8c770f3aa30fcaf5d18a6fe34b87451a730db75a2d83cac0ea95`;
- the wrapper retained both `-B` and `-X pycache_prefix=/dev/null`;
- no `__pycache__`, `.pyc`, or `.pyo` existed under cached controller source
  after all controller and doctor calls;
- Git status was exactly ` M account.py`, with no untracked files and no diff
  under `.kiro`, `.pstack`, `projectctl`, `tests`, `Wiki`, `README.md`, or
  `.gitignore`;
- `git diff --check` passed; and
- state directory/file/lock modes were `0700`/`0600`/`0600`/`0600`.

The source candidate stayed at the same clean pushed commit. A concurrent
documentation edit appeared in the source worktree during the post-run audit;
the campaign did not create it and the candidate index remained clean.

## Evidence and transport boundary

The sanitized structured extract is committed as
`reviews/kiro-final-evidence.json`. Its SHA-256 is
`94f105ce85a7029b806a1d9f012fa56a3b2236adbd8743c7e6192c4988c22cc2`;
it is valid JSON and the scrub check found no request IDs, reasoning
signatures, credentials, or secrets.

The full runtime archive remains outside the repository at
`/private/tmp/pk-stack-final-authoritative.64Z6Rx/kiro-final-post-cdx004.zip`.
It is 53,948 bytes, passed `unzip -t`, and has SHA-256
`b795bd9bf88662cba3c7042ed748d02dd6f0a770b4c8b34989fd790765b2789d`.
Its only entries are `messages.jsonl`, `session.json`, and the single verifier
subexecution.

Kiro's own logs and exports use ACP-named internal transport and policy terms,
including `ACPEventAdapter`, `session/new`, `acp.policy-eval`, `Machine ID:
acp-client`, and two `toolOrigin: "acp"` records. The model request is logged
with `origin=KIRO_CLI`. No external ACP host, ACP command, nested Kiro process,
or `/spawn` execution was used; the user-facing path was one normal Kiro CLI
V3 session.
