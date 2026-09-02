# Validation report

Date: 2026-09-02

Candidate: PK-Stack (Poteto Kiro), a Kiro-native verified-development Power

Source lineage: private `njs14/pstack-kiro`

> Historical source report: this file records acceptance of source commit `1919975`. The combined
> repository subsequently added the centralized draft-publication guard. The current combined
> release is accepted only by the root `reviews/` sequence; this historical verdict is not a
> verdict on later changes.

## Final release result

`ACCEPT`. The implementation froze at
`b39c20ac6334f16ad4dfe0dc99f6698d71816689`; subsequent commits add only
audited runtime/reviewer evidence and its disposition. The complete 508-test
suite, 89.22% branch-coverage gate, lint, format, types, lock, plugin schema,
four Kiro agent schemas, reproducible package/install audit, and authoritative
one-session Kiro V3 campaign all pass. Fable 5.1 at `max` reviewed the full
evidence-bearing snapshot and returned `ACCEPT` with no material finding. Its
one LOW item is reproduced, bounded, and retained under Remaining limitations.

## Result at initial candidate freeze

The primary Codex implementation gates pass, and a fresh real Kiro CLI V3
session completed the intended current-session repair loop: the stored verifier
failed before any edit, one native subagent performed a bounded diagnosis, the
primary session changed one implementation file, and the same stored verifier
then passed. The flow did not invoke an external ACP host, `kiro-cli acp`,
classic/V2, a nested Kiro process, `/spawn`, or a claimed native V3 `/goal`
command.

The official Grok Build advisory council subsequently found four material
issues. Codex independently reproduced each supported claim, remediated it, and
expanded the suite from 130 to 148 tests. Further Grok and Fable rounds then
produced the remediation history recorded below; this initial-freeze result is
retained as provenance rather than presented as the current release decision.

## Environment

Observed locally on the user's Apple-silicon Mac:

| Component | Observed value |
| --- | --- |
| Kiro CLI | `2.20.2` in the initial campaign; `2.21.0` for current profile validation |
| Kiro runtime | V3, local execution target |
| Kiro model | `gpt-5.6-sol` |
| Kiro effort | `max` |
| Python used to invoke setup | `3.14.7` |
| uv | `0.12.6` |
| Grok Build CLI | `1.0.13` |
| Claude Code | `2.1.252` |

The tested setup shim also has an automated older-Python fallback test; this
machine-level campaign did not replace the system Python with an older runtime.

## Primary release gates

All commands ran from the repository root. Timings are wall-clock measurements
from the recorded run.

| Gate | Exact command | Observed result |
| --- | --- | --- |
| Lock integrity | `/usr/bin/time -p uv lock --check` | Exit 0; 20 packages resolved; 0.01s |
| Lint | `/usr/bin/time -p uv run ruff check src tests` | Exit 0; all checks passed; 0.04s |
| Format | `/usr/bin/time -p uv run ruff format --check src tests` | Exit 0; 24 files already formatted; 0.03s |
| Types | `/usr/bin/time -p uv run ty check` | Exit 0; all checks passed; 0.08s |
| Tests | `/usr/bin/time -p uv run pytest -q` | Exit 0; 130 passed in 17.60s; 18.58s wall |
| Branch coverage | `COVERAGE_FILE=/tmp/pstack-release-coverage.imeRFA /usr/bin/time -p uv run pytest -p no:cacheprovider --cov=pstack_kiro --cov-branch --cov-config=/Users/noahsutter/git-projects/codex/pyproject.toml --cov-report=term-missing -q` | Exit 0; 130 passed; 87.44%; configured 85% threshold met; 19.34s wall |

Coverage data was written outside the candidate repository. The suite includes
fresh/repeated/conflicting/concurrent bootstrap, source and target symlink
rejection, receipt integrity and managed upgrade behavior, feature-map parsing
and proof-before-write, verifier hazards and process cleanup, goal transitions
and concurrency, JSON error shape, Kiro asset contracts, optional OKF behavior,
and offline wheel/bootstrap checks.

### Post-Grok remediation gates

After the first advisory round, the same release gates passed with the expanded
suite:

| Gate | Exact command | Observed result |
| --- | --- | --- |
| Lock integrity | `uv lock --check` | Exit 0; 20 packages resolved |
| Lint | `uv run ruff check src tests` | Exit 0; all checks passed |
| Format | `uv run ruff format --check src tests` | Exit 0; 24 files already formatted |
| Types | `uv run ty check` | Exit 0; all checks passed |
| Tests | `uv run pytest -q` | Exit 0; 148 passed in 22.05s |
| Branch coverage | `COVERAGE_FILE=/tmp/pstack-post-grok-coverage uv run pytest -p no:cacheprovider --cov=pstack_kiro --cov-branch --cov-config=/Users/noahsutter/git-projects/codex/pyproject.toml --cov-report=term-missing -q` | 148 passed; 88.06%; configured 85% threshold met |

New release regressions execute the freshly bootstrapped wrapper and prove that
host `PATH`, `PYTHONPATH`, `VIRTUAL_ENV`, `UV_*`, executable, and prefix values
match a clean direct run for both ready generation and repeated feature proof.
They also pin exact malformed-feature JSON exit/key contracts through the real
wrapper, reject external/symlinked verifier operands before goal state exists,
fail goal locking closed without `fcntl`, require explicit `draft`, reject
option-shaped `okn` queries, and require a post-setup pstack-agent handoff.

### Post-round-2 hardening gates

After independently reproducing GRK-011 through GRK-013 and closing the four
round-2 low-risk items, the expanded candidate passed:

| Gate | Exact command | Observed result |
| --- | --- | --- |
| Lock integrity | `uv lock --check` | Exit 0; 20 packages resolved |
| Lint | `uv run ruff check src tests` | Exit 0; all checks passed |
| Format | `uv run ruff format --check src tests` | Exit 0; 24 files already formatted |
| Types | `uv run ty check` | Exit 0; all checks passed |
| Tests | `uv run pytest -q` | Exit 0; 185 passed in 24.15s |
| Branch coverage | `PSTACK_COV_DIR=$(mktemp -d /private/tmp/pstack-coverage.XXXXXX); COVERAGE_FILE="$PSTACK_COV_DIR/.coverage" uv run pytest --cov=pstack_kiro --cov-report=term -q` | Exit 0; 185 passed in 32.99s; 88.43%; configured 85% threshold met |
| Kiro agent schemas | `for agent in templates/project/.kiro/agents/*.json; do kiro-cli agent validate --path "$agent"; done` | Exit 0 for all four profiles on Kiro CLI 2.20.2 |

The new regressions include same-basename PATH executable identity through a
fresh wrapper, rejection before goal/feature persistence, a Power v1-to-v2
dry-run and approved managed upgrade, no-shell delegated agent assets,
comment/subpath `.gitignore` impostors, reserved `readme` load/lookup/generation,
and direct/nested attached or clustered shell/interpreter evaluation flags.

### Post-Fable-round-1 remediation gates

Fable's first peer pass rejected frozen commit `6b72a71` with four material
findings. Codex independently reproduced all four, implemented their acceptance
criteria, and ran the following candidate checks:

| Gate | Exact command | Observed result |
| --- | --- | --- |
| Lock integrity | `uv lock --check` | Exit 0; 20 packages resolved |
| Lint | `uv run ruff check src tests` | Exit 0; all checks passed |
| Format | `uv run ruff format --check src tests` | Exit 0; 24 files already formatted |
| Types | `uv run ty check` | Exit 0; all checks passed |
| Tests | `uv run pytest -q` | Exit 0; 208 passed in 23.91s |
| Branch coverage | `uv run pytest -q --cov=pstack_kiro --cov-report=term-missing --cov-fail-under=85` | 208 tests collected; coverage data reports 88.12%; configured 85% threshold met |
| Kiro agent schemas | `for profile in templates/project/.kiro/agents/*.json; do kiro-cli agent validate --path "$profile"; done` | Exit 0 for all four profiles on Kiro CLI 2.21.0 |

The new regressions reject obvious placeholder and controller-self-reference
proofs through service and freshly bootstrapped CLI boundaries; prove rejected
feature generation is side-effect-free; reject target-local cached setup
authority through both copied entrypoints; preserve valid active goal state
after an invalid resume; validate serialized/schema/semantic invariants before
every goal-state save; cover every canonical controller route with `ask`; and
align direct-write, delegated-role, and stored-predicate disclosures with the
shipped profile.

### Pre-Fable-round-2 closure gates

Codex then applied a bounded adversarial and compatibility audit to the
FBL-001 verifier seam. The audit closed direct and nested shell/interpreter
delegation, controller aliases and cached bytecode, `uv` context relocation,
Git helper/output/help paths, pytest option indirection, recognized response
files, compiler attached output paths, non-finite timeouts, and false positives
after `--` or for ordinary `@` data. The frozen candidate passed:

| Gate | Exact command | Observed result |
| --- | --- | --- |
| Lock integrity | `uv lock --check` | Exit 0; 20 packages resolved |
| Lint | `uv run ruff check src tests` | Exit 0; all checks passed |
| Format | `uv run ruff format --check src tests` | Exit 0; 24 files already formatted |
| Types | `uv run ty check` | Exit 0; all checks passed |
| Tests | `uv run pytest -q` | Exit 0; 463 passed in 27.16s |
| Branch coverage | `PSTACK_COV_DIR=$(mktemp -d /private/tmp/pk-stack-coverage.XXXXXX); COVERAGE_FILE="$PSTACK_COV_DIR/.coverage" /usr/bin/time -p uv run pytest -p no:cacheprovider --cov=pstack_kiro --cov-branch --cov-config=/Users/noahsutter/git-projects/codex/pyproject.toml --cov-report=term-missing -q` | Exit 0; 463 passed in 36.13s; 88.98%; configured 85% threshold met; 36.40s wall |
| Kiro agent schemas | `for profile in templates/project/.kiro/agents/*.json; do kiro-cli agent validate --path "$profile"; done` | Exit 0 for all four profiles on Kiro CLI 2.21.0 |
| Diff whitespace | `git diff --check` | Exit 0 |

Coverage data was written to a fresh directory outside the repository. The
full policy boundary and the remaining arbitrary-script/non-sandbox limitation
are recorded in `docs/usage.md`, `docs/architecture.md`, and
`reviews/acceptance-criteria.md`.

## Fresh setup and real Kiro V3 campaign

### Isolated fixture construction

The committed fixture under `examples/verified-goal-demo/` intentionally starts
red. It was copied to a new temporary Git repository so Kiro's repair could not
change the candidate source:

```bash
demo_root="$(mktemp -d /tmp/pstack-kiro-e2e.XXXXXX)"
demo_dir="$demo_root/demo"
cp -R examples/verified-goal-demo "$demo_dir"
git -C "$demo_dir" init -b main
git -C "$demo_dir" config user.name "pstack Kiro validation"
git -C "$demo_dir" config user.email "pstack-validation@invalid.example"

python3 skills/setup-pstack/scripts/setup_pstack.py \
  --root "$demo_dir" --dry-run --output json
python3 skills/setup-pstack/scripts/setup_pstack.py \
  --root "$demo_dir" --output json

"$demo_dir/.pstack/bin/projectctl" feature generate account-lookup \
  --title "Account identifier normalization" \
  --behavior "Account identifiers normalize spaces and hyphens into exactly twelve decimal digits, rejecting every other input." \
  --expected-path "Kiro current session -> account.py -> unittest verifier -> stored goal evidence" \
  --command "python3 -m unittest discover -s tests -q" \
  --output json

git -C "$demo_dir" add -A
git -C "$demo_dir" commit -m "Create intentionally failing verified-goal fixture"
```

Both setup preview and apply returned `ok: true`, with no conflicts,
`pending_updates`, or `stale_managed` paths. The baseline fixture commit was
`db0dc38`. The observed campaign directory was
`/private/tmp/pstack-kiro-e2e.1F9H1G/demo`.

### Current-session invocation

Kiro was started through ordinary chat rather than `kiro-cli acp` or an
external ACP host:

```bash
cd "$demo_dir"
kiro-cli chat --v3 --model gpt-5.6-sol --effort max
```

The initial status line showed `high` despite the launch option, so `/effort
max` was issued inside the same session; Kiro then displayed `Effort set to
max` and the status line showed `GPT 5.6 Sol · max` before the goal request.
The exact skill invocation was:

```text
/verified-goal Repair account identifier normalization for account-lookup. In this same current V3 session, start the goal from feature account-lookup, then run the stored verifier once before editing so attempt 1 records the existing failure. After that failure, use one native subagent for a bounded diagnosis, apply the smallest repair in account.py only, and rerun until stored status is passed. Do not modify tests or the feature contract, do not weaken the verifier, and do not start a nested session or ACP.
```

Kiro requested and received one-time approval to load the workspace skill. It
then used `.pstack/bin/projectctl` throughout the loop.

This first campaign launched before the GRK-004 finding and did not select
`--agent pstack`; it proves the current-session repair mechanics, but it does
not prove that the generated pstack permission profile was active. The final
post-remediation campaign must explicitly select that profile before
`/verified-goal`; its evidence is not claimed in this initial-campaign section.

### Before and after

| Evidence | Before repair | After repair |
| --- | --- | --- |
| Stored goal status | `active` | `passed` |
| Attempt count | 1 of 4 | 2 of 4 |
| Stored verifier | `python3 -m unittest discover -s tests -q` | Unchanged |
| Verifier result | Exit 1; 3 failures, 1 pass | Exit 0; 4 tests passed |
| Diagnosis | Native `context-gatherer` subagent found missing normalization and validation | Primary session applied the diagnosis |
| Tracked implementation diff | None before attempt 1 | `account.py` only |
| Tests | Unchanged | Unchanged |
| Feature contract | Unchanged | Unchanged |

The final goal ID was `df0561d4-2fa1-4762-94a1-17d633b1796c`. History retained
both results with exit codes 1 and 0 and a stable contract digest. The state
directory and goal file had modes `0700` and `0600`, respectively. Kiro
reported 4.90 credits and 3m50s for the turn. The V3 session ID was
`sess_4612653a-ca99-4165-b019-8db82e692b86`; session listing reported source
`v3`, local execution, and idle status after completion.

The post-run audit used:

```bash
.pstack/bin/projectctl goal status --output json
git status --short
git diff --name-only
git diff --exit-code -- tests/test_account.py Wiki/features/account-lookup.md
stat -f '%Lp %N' .pstack/state .pstack/state/goal.json
kiro-cli chat --list-sessions --format json-pretty
```

`git diff --name-only` returned only `account.py`, and the explicit test and
feature-contract diff check exited 0. Python created untracked `__pycache__/`
directories while running the verifier; they were ignored runtime artifacts,
not Kiro edits or candidate evidence.

## Independent review rounds

### Official Grok Build council, round 1

The candidate commit `d14dd439a393c397a0a5956ad366a2009e4aa9c8` was exported
to a read-only temporary snapshot. The installed official Grok Build CLI ran
`grok-4.6` at `xhigh` with strict sandboxing, plan permissions, web search and
subagents disabled, and only `read_file`, `grep`, and `list_dir` enabled. The
exact harness is recorded in `reviews/README.md`; the verbatim report is
`reviews/grok-round-1.md`.

Its `ADVISORY_CONCERNS` result contained four material findings:

| ID | Independent result | Remediation |
| --- | --- | --- |
| GRK-001 | Confirmed: the controller environment changed a real host pytest predicate from pass to fail. | The wrapper now syncs then directly executes its locked Python; the runner restores caller `PYTHONPATH` and strips private markers. |
| GRK-002 | Confirmed: malformed commands and invalid UTF-8 broke list/show JSON with tracebacks. | Feature loading normalizes both to path-qualified `FeatureMapError`; exact direct/wrapper JSON contracts are tested. |
| GRK-003 | Confirmed: interpreter path operands could escape the workspace. | Every path-shaped operand, including option assignments and symlink targets, is checked before persistence/execution. |
| GRK-004 | Confirmed: plain V3 kept `kiro_default`, so generated permission rules were inactive. | Setup requires `/agent swap pstack`, with `kiro-cli chat --v3 --agent pstack` as the discovery fallback; no global default is changed. |

The full Codex-owned reproduction, criterion, test, and disposition ledger is
`reviews/acceptance-criteria.md`. Four low-risk findings were also closed. The
council's semicolon-bypass hypothesis was rejected against Kiro's documented
per-subcommand permission parsing rather than accepted as a finding.

### Official Grok Build council, round 2 remediation

Round 2 reviewed frozen commit
`d67ae0fe8ec96b0720acc4f19c39e132861eb742` with the same official Grok
4.6/xhigh read-only harness. It returned `ADVISORY_CONCERNS` with GRK-011
(absolute argv[0] containment), GRK-012 (read-only profiles with general
shell), and GRK-013 (post-swap Power-local upgrade authority). The exact report
is `reviews/grok-round-2.md`. Codex independently confirmed all three. The
runner now permits an outside absolute executable only when it canonically
matches the current PATH selection; every delegated profile omits `shell` and
`write`; cached `projectctl setup` requires an explicit reviewed `--power-root`;
and always-loaded steering gives the same-session Power-enabled refresh path.
GRK-014 through GRK-017 were also closed as low-risk hardening. The full
criteria and regressions are in `reviews/acceptance-criteria.md`. At that
checkpoint, the remaining order was a Fable 5.1/max peer pass, the Grok residual
sweep, the selected-profile Kiro campaign, and a final evidence-bearing Fable
acceptance pass. Any material change returns to Fable.

### Fable peer review, round 1 remediation

Claude Code executed canonical `claude-fable-5-1` at `max` against frozen commit
`6b72a713bb9966cc6325381b91ea44e961e869e4` with only read, glob, and grep tools.
It returned `REJECT` with FBL-001 through FBL-004: empty/self-referential proof,
incomplete controller permission coverage, an active-resume state invariant
failure, and cached setup self-authority. The first event envelope was truncated
after the reviewer traversed `.venv`; `reviews/fable-round-1.md` explicitly
preserves the material ledger as a Codex extraction rather than claiming a
verbatim transcript. The harness now uses a clean read-only Git archive and
emits only the final Markdown result. All four findings and seven low items have
Codex-owned dispositions in `reviews/acceptance-criteria.md`. The next checkpoint
was another Fable peer pass; Grok remained downstream as the residual sweeper.

### Fable peer review, round 2 remediation

Fable 5.1/max reviewed frozen commit `f96df36` and returned `REJECT` with one
source blocker and one intentionally pending evidence gate. FBL-012 correctly
found that unconditional `git diff*`, `git log*`, and `git show*` shell allows
also matched helper execution, output-file writes, and outside-workspace reads.
Codex reproduced the matcher behavior, removed all Git shell allows, made
`git` and `git *` explicit `ask` forms, retained the destructive `deny` rules,
and added hostile/safe matcher regressions. At that checkpoint, FBL-013
recorded the still-pending selected-profile campaign; the later campaign below
closes it with live evidence.

The same pass reported six low items and notes. Codex removed the unreachable
goal branch, allowed explicit force-clear recovery for structurally valid but
policy-invalid state, made status/tripwire reads artifact-free, replaced an
ambient test interpreter, and added `--no-config` to the locked cached-runtime
sync. A snapshot-relative coverage command replaced the portability gap for the
current checkpoint. Exact dispositions are in
`reviews/acceptance-criteria.md`; the verbatim reviewer result is
`reviews/fable-round-2.md`.

| Gate | Exact command | Observed result |
| --- | --- | --- |
| Lock integrity | `uv lock --check` | Exit 0; 20 packages resolved |
| Lint | `uv run ruff check src tests` | Exit 0; all checks passed |
| Format | `uv run ruff format --check src tests` | Exit 0; 24 files already formatted |
| Types | `uv run ty check` | Exit 0; all checks passed |
| Focused remediation | `uv run pytest tests/test_goal.py tests/test_bootstrap.py tests/test_kiro_assets.py tests/test_packaging.py -q` | Exit 0; 56 passed in 17.89s |
| Tests | `uv run pytest -q` | Exit 0; 465 passed in 25.62s |
| Snapshot-relative branch coverage | `PSTACK_COV_DIR=$(mktemp -d /private/tmp/pk-stack-coverage.XXXXXX); COVERAGE_FILE="$PSTACK_COV_DIR/.coverage" /usr/bin/time -p uv run pytest -p no:cacheprovider --cov=pstack_kiro --cov-branch --cov-config=pyproject.toml --cov-report=term-missing -q` | Exit 0; 465 passed in 34.64s; 89.01%; configured 85% threshold met; 36.55s wall |
| Kiro agent schemas | `for profile in templates/project/.kiro/agents/*.json; do kiro-cli agent validate --path "$profile"; done` | Exit 0 for all four profiles on Kiro CLI 2.21.0 |

An immediate Fable source re-review was attempted against frozen commit
`61c6e0c`, but Claude Code returned its session-limit message before inspecting
the repository; the local CLI reported a 5:00 a.m. Eastern reset. This is
recorded as a temporary reviewer-availability constraint, not an acceptance.
Codex used the interval for the already-planned bounded sweeper and retains the
requirement for a complete final Fable pass.

### Official Grok Build council, round 3 sweep

The official Grok Build 1.0.13 harness reviewed commit `61c6e0c` with
`grok-4.6` at `xhigh` in the read-only strict sandbox. Ambient Grok, Claude, and
Cursor configuration reads were denied at startup. The exact output is
`reviews/grok-round-3.md`.

Grok reported GRK-021 as a medium feature-YAML round-trip defect. Codex and a
separate auditor ran the exact generate/show/validate scenario plus the full
YAML 1.1 ambiguous-scalar set under both pinned PyYAML 6.0.3 locks. The claim
did not reproduce: `safe_dump` quoted the strings, every value reloaded with its
exact type/value, and validation returned `ok: true`. A 15-case parametrized
regression now makes that producer/consumer contract explicit.

Two valid low items were closed: spec-bridge argv now rejects non-string JSON
elements centrally instead of stringifying them, and the legacy setup shim no
longer uses a fixed incorrect parent depth when locating a project controller.
The `git checkout *` deny remains an intentional safety bias; current-session
instructional limits, the then-pending selected-profile evidence gate, and
arbitrary-script semantics were disclosed boundaries at that checkpoint.
Kiro's official V3 permission contract
confirms that unmatched shell commands ask by default, while the profile's
explicit Git `ask` overrides ambient read-only Git allows.

| Gate | Exact command | Observed result |
| --- | --- | --- |
| Lock integrity | `uv lock --check` | Exit 0; 20 packages resolved |
| Lint | `uv run ruff check src tests skills/setup-pstack/scripts/setup_pstack.py` | Exit 0; all checks passed |
| Format | `uv run ruff format --check src tests skills/setup-pstack/scripts/setup_pstack.py` | Exit 0; 25 files already formatted |
| Types | `uv run ty check` | Exit 0; all checks passed |
| Focused sweep checks | `uv run pytest tests/test_features.py tests/test_goal.py tests/test_runner.py tests/test_kiro_assets.py -q` | Exit 0; 376 passed in 1.66s |
| Tests | `uv run pytest -q` | Exit 0; 482 passed in 29.73s |
| Kiro agent schemas | `for profile in templates/project/.kiro/agents/*.json; do kiro-cli agent validate --path "$profile"; done` | Exit 0 for all four profiles on Kiro CLI 2.21.0 |
| Diff whitespace | `git diff --check` | Exit 0 |

### PK-Stack naming and DRY pass

The final product pass establishes **PK-Stack** as the display name, expands it
as **Poteto Kiro**, and changes the pre-release Agent Plugins manifest ID to
`pk-stack`. Runtime code reads those values from
`src/pstack_kiro/branding.py`. The `pstack-kiro` Python
distribution/repository/receipt manager, `pstack_kiro` package, `pstack*`
agent and skill routes, `.pstack` paths, and `projectctl` commands remain
compatibility interfaces. Static Kiro assets stay readable source files and
are pinned to that split by focused tests instead of being generated from a
second template system. Historical council outputs and command transcripts
were not rewritten.

Because the Power ID changed, an earlier pre-release `pstack-kiro` import may
remain as a separate Kiro entry. README and usage documentation direct the user
to remove that old Power through Kiro's management interface before importing
`pk-stack`; project files are not removed or renamed.

| Gate | Exact command | Observed result |
| --- | --- | --- |
| Lock integrity | `uv lock --check` | Exit 0; 20 packages resolved |
| Lint | `uv run ruff check src tests skills/setup-pstack/scripts/setup_pstack.py` | Exit 0; all checks passed |
| Format | `uv run ruff format --check src tests skills/setup-pstack/scripts/setup_pstack.py` | Exit 0; 27 files already formatted |
| Types | `uv run ty check` | Exit 0; all checks passed |
| Focused brand/bootstrap/package checks | `uv run pytest tests/test_branding.py tests/test_cli_direct.py tests/test_bootstrap.py tests/test_edge_cases.py tests/test_doctor.py tests/test_hardening.py tests/test_kiro_assets.py tests/test_packaging.py -q` | Exit 0; 127 passed in 23.53s |
| Tests | `uv run pytest -q` | Exit 0; 488 passed in 24.38s |
| Snapshot-relative branch coverage | `PSTACK_COV_DIR=$(mktemp -d /private/tmp/pk-stack-coverage.XXXXXX); COVERAGE_FILE="$PSTACK_COV_DIR/.coverage" /usr/bin/time -p uv run pytest -p no:cacheprovider --cov=pstack_kiro --cov-branch --cov-config=pyproject.toml --cov-report=term-missing -q` | Exit 0; 488 passed in 35.37s; 89.04%; configured 85% threshold met; 37.37s wall |
| Kiro agent schemas | `for profile in templates/project/.kiro/agents/*.json; do kiro-cli agent validate --path "$profile"; done` | Exit 0 for all four profiles on Kiro CLI 2.21.0 |
| Manifest identity and compatibility split | `uv run pytest tests/test_branding.py -q` | Exit 0; 6 passed; manifest ID is `pk-stack`, no unsupported `displayName` field is present, and runtime compatibility names remain pinned |
| Diff whitespace | `git diff --check` | Exit 0 |

## First selected-profile Kiro V3 campaign

The post-remediation campaign ran a committed fresh fixture against snapshot
`bc6e79a` and selected the installed primary profile explicitly:

```bash
cd /private/tmp/pk-stack-selected-profile.v5fnSx/demo
kiro-cli chat --v3 --agent pstack --model gpt-5.6-sol --effort max
```

The saved session and the independent session listing identify session
`sess_3cebc0c9-ac7a-42d1-a898-9251ac6bb3f8` as source `v3`, mode `pstack`,
model `gpt-5.6-sol`, effort `max`, local execution, and idle after success. The
baseline fixture commit was `d0104adb4a5d60a854ec59cf2296b2799139054f`.

Before starting goal state, Kiro attempted the requested direct filesystem
write to `.pstack/deny-probe.txt`. The `pstack` agent profile denied it with the
rule matching `.pstack/**`, and both Kiro file search and the independent
post-run check confirmed that the file did not exist. The exact
`git status --short` probe ran once after one-time approval and returned clean.
Each of the seven subsequent `.pstack/bin/projectctl` commands also required a
one-time approval. This closes the live path-normalization and selected-profile
evidence gates FBL-013, FBL-023, and GRK-026.

The workflow started goal `9bc07fe8-8bc1-4c62-826d-3f2bb2beaf93` from the
`account-lookup` feature with four allowed attempts and displayed the stored
contract before verification:

```text
python3 -B -m unittest discover -s tests -q
source=feature-map
feature=account-lookup
digest=5a02754f1fbc0ad1005b53b34da51671d8c84b30b04e6e5e136bd15ca7dce445
```

Attempt 1 ran before any edit, exited 1, and recorded three failures among four
tests. Exactly one native `pstack-verifier` subagent then performed bounded
read-only diagnosis: it read goal state, `account.py`, the relevant test, and
the feature map; it ran no command and made no edit. The primary session made
the smallest repair in `account.py` only. Attempt 2 ran the unchanged stored
contract, exited 0 with four tests `OK`, and transitioned the goal to `passed`
with two attempts remaining. Kiro recorded 3.158119776318408 credits and
369441 ms (6m 9.441s).

The independent post-run audit reran the verifier successfully and checked:

```bash
.pstack/bin/projectctl goal status --output json
python3 -B -m unittest discover -s tests -q
git status --short
git diff --name-only
git diff --exit-code -- tests/test_account.py Wiki/features/account-lookup.md .kiro projectctl
test ! -e .pstack/deny-probe.txt
stat -f '%Lp %N' \
  .pstack/state \
  .pstack/state/goal.json \
  .pstack/state/.goal.lock \
  .pstack/state/.goal.verify.lock
kiro-cli --version
kiro-cli chat --list-sessions --format json-pretty

set -u
mismatch_count=0
while IFS=$'\t' read -r asset_path expected_hash; do
  if [ ! -f "$asset_path" ]; then
    echo "MISSING $asset_path"
    mismatch_count=$((mismatch_count + 1))
    continue
  fi

  actual_hash=$(shasum -a 256 "$asset_path" | awk '{print $1}')
  if [ "$actual_hash" != "$expected_hash" ]; then
    printf 'MISMATCH\t%s\texpected=%s\tactual=%s\n' \
      "$asset_path" "$expected_hash" "$actual_hash"
    mismatch_count=$((mismatch_count + 1))
  fi
done < <(
  jq -r '.files | to_entries[] | [.key, .value] | @tsv' \
    .pstack/bootstrap.json
)
printf 'managed_files=%s mismatches=%s\n' \
  "$(jq '.files | length' .pstack/bootstrap.json)" \
  "$mismatch_count"
```

The only tracked project implementation diff was `account.py`; `projectctl`
also made the expected controller-owned updates to `goal.json`, `.goal.lock`,
and `.goal.verify.lock`. The protected-path diff exited 0; all 49
bootstrap-managed files still matched the receipt; state and goal modes were
`0700` and `0600`; the receipt loop printed
`managed_files=49 mismatches=0`; and the saved history retained the
exit-1/exit-0 pair under one immutable digest. The exact prompt, permission
result, before/after record, hashes, audit provenance, extraction commands, and
sanitized structured evidence are in
`reviews/kiro-selected-profile-campaign.md` and
`reviews/kiro-selected-profile-evidence.json`.

No shell command launched an ACP harness, a nested Kiro process, or `/spawn`;
the recorded execution origin is `KIRO_CLI`. Kiro logs nevertheless use ACP
terms for session creation/prompt and policy evaluation, route events through
an internal `ACPEventAdapter`, and attach `toolOrigin: "acp"` metadata to
exported skill-disclosure and native-subagent-response records. That observed
implementation detail is disclosed rather than used to claim that ACP was the
user-facing or default path: the whole workflow stayed in one normal Kiro V3
session.

### Observed before/after Kiro usage

The campaigns exercised the same red fixture behavior, but they were not a
controlled performance benchmark. The comparison is useful for runtime
provenance only:

| Observation | Initial campaign | First selected-profile campaign | Authoritative post-CDX-004 campaign |
| --- | --- | --- | --- |
| Candidate stage | Before GRK-004 and later hardening | Branded/remediated snapshot `bc6e79a` | Frozen source snapshot `b39c20a` |
| Launch/profile | Ordinary `--v3`; ambient `kiro_default` | `--v3 --agent pstack` | `--v3 --agent pstack` |
| Effort | Launch displayed `high`; changed to `max` in session | `max` from launch and saved metadata | Startup briefly displayed `high`, then automatically settled on saved `max` before the prompt |
| Goal result | Fail then pass in 2 of 4 attempts | Fail then pass in 2 of 4 attempts | Fail then pass in 2 of 4 attempts |
| Native diagnosis | One `context-gatherer` | One bounded `pstack-verifier` | One bounded `pstack-verifier` |
| Permissions proved | Skill approval only; selected profile not proved | Direct `.pstack/**` deny plus Git/controller/edit one-time approvals | Same selected-profile boundaries, freshly repeated after CDX-004 |
| Controller bytecode audit | Not performed | Found 13 receipt-owned cache files in a later repeat; not release evidence | Zero cache directories or files after all commands |
| Reported usage | 4.90 credits; 3m50s | 3.158119776318408 credits; 6m9.441s | 3.587682818308457 credits; 5m15.433s |

### Selected-profile snapshot gates

The `5e90f09` selected-profile evidence snapshot passed these gates before the
later Codex preflight and remediation. They remain historical provenance, not
the final release totals:

| Gate | Exact command | Observed result |
| --- | --- | --- |
| Lock integrity | `uv lock --check` | Exit 0; 20 packages resolved |
| Lint and format | `uv run ruff check src tests skills/setup-pstack/scripts/setup_pstack.py && uv run ruff format --check src tests skills/setup-pstack/scripts/setup_pstack.py` | Exit 0; all checks passed; 27 files already formatted |
| Types | `uv run ty check` | Exit 0; all checks passed |
| Tests | `uv run pytest -q` | Exit 0; 488 passed in 27.48s |
| Snapshot-relative branch coverage | `PSTACK_COV_DIR=$(mktemp -d /private/tmp/pk-stack-coverage.XXXXXX); COVERAGE_FILE="$PSTACK_COV_DIR/.coverage" /usr/bin/time -p uv run pytest -p no:cacheprovider --cov=pstack_kiro --cov-branch --cov-config=pyproject.toml --cov-report=term-missing -q` | Exit 0; 488 passed in 35.96s; 89.04%; configured 85% threshold met; 36.69s wall |
| Kiro agent schemas | `for profile in templates/project/.kiro/agents/*.json; do kiro-cli agent validate --path "$profile" || exit; done` | Exit 0 for all four profiles on Kiro CLI 2.21.0 |
| Structured evidence and diff whitespace | `jq empty reviews/kiro-selected-profile-evidence.json && git diff --check` | Exit 0 |

A final Codex source preflight then reproduced two medium gaps before the Fable
window reopened: receipt-owned drift could leave `doctor` false-green, and a
ready feature could be invalid or semantically changed by body-heading input.
Both are closed in CDX-001/CDX-002; the stricter draft-path cleanup is recorded
as CDX-003. The final frozen gates below supersede these snapshot totals.

### Final Codex remediation and DRY sweep

Doctor now validates the schema, manager, non-empty inventory, safe path, and
SHA-256 digest of every entry in `.pstack/bootstrap.json`. The four exact
pre-fix fixtures—cached controller drift, synchronized live/cached profile
drift, a missing cached skill, and an invalid receipt—all returned `ok: true`
with 38 passes, one warning, and no receipt check. Against the same fixtures,
the remediated doctor returns `ok: false` with one precise
`bootstrap-receipt-integrity` failure. A clean setup remains green with all 49
receipt-managed files matching, 39 passes, and one optional-tool warning.

Feature generation now builds and parses its exact Markdown candidate before
proof. A ready contract must preserve all requested semantics and have safe,
present related paths; invalid input runs no verifier and writes nothing, or
preserves the existing overwrite target. Drafts may defer only the existence
of a contained future document—not empty, absolute, escaping, or unresolvable
paths. The candidate is checked again immediately before its atomic write.

A final naming audit found no remaining product-label drift.
`projectctl version` derives both text and JSON identity from
`identity_payload()`, so both report `PK-Stack`, `Poteto Kiro`, and `pk-stack`
while retaining compatibility `name: pstack-kiro`. Manifest, package, NOTICE,
and LICENSE attribution consistently use `PK-Stack contributors`. All four
agent profiles and both hook fallback payloads are checked against the
canonical branding values. Remaining legacy-form literals are documented
compatibility interfaces or exact historical/provenance evidence.

The first frozen-candidate repeat on commit `421f6e3` functionally completed
the selected-profile goal in two attempts, but its independent audit found 13
untracked bytecode files under receipt-owned controller source. That run is not
release acceptance. CDX-004 changes the wrapper to
`python -B -X pycache_prefix=/dev/null -m pstack_kiro`: it writes no controller
cache and does not trust a pre-existing local unchecked-hash cache. A real
installed-wrapper regression proves both the `-B`-only failure mode and the
canonical wrapper protection. A fresh post-fix package and live campaign are
required below.

### Final frozen source gates

| Gate | Exact command | Observed result |
| --- | --- | --- |
| Lock integrity | `uv lock --check` | Exit 0; 20 packages resolved |
| Lint | `uv run --frozen ruff check src tests skills/setup-pstack/scripts/setup_pstack.py` | Exit 0; all checks passed |
| Format | `uv run --frozen ruff format --check src tests skills/setup-pstack/scripts/setup_pstack.py` | Exit 0; 27 files already formatted |
| Types | `uv run --frozen ty check` | Exit 0; all checks passed |
| Tests | `uv run --frozen pytest -q` | Exit 0; 508 passed in 34.62s |
| Snapshot-relative branch coverage | `PKSTACK_COV_DIR=$(mktemp -d /private/tmp/pk-stack-final2-coverage.XXXXXX); COVERAGE_FILE="$PKSTACK_COV_DIR/.coverage" /usr/bin/time -p uv run --frozen pytest -p no:cacheprovider --cov=pstack_kiro --cov-branch --cov-config=pyproject.toml --cov-report=term-missing -q` | Exit 0; 508 passed in 45.01s; 89.22%; configured 85% threshold met; 47.86s wall |
| Independent combined-diff audit | Codex read-only review plus focused feature/doctor/CLI/branding and bytecode-boundary tests | `ACCEPT`; no blocker, high, or medium finding; bytecode delta passed 44 focused tests and the full 508-test suite |
| Naming/DRY audit | Canonical-value scan, 43 focused tests, hook/agent checks, and direct text version probe | `ACCEPT`; one runtime identity source plus one complete identity-tuple test anchor; static human/Kiro assets are mechanically pinned and compatibility names are preserved |

### Final package and isolated-install audit

Post-CDX-004 commit `b39c20ac6334f16ad4dfe0dc99f6698d71816689`
was copied to `/private/tmp/pk-stack-final-smoke-b39.WSeSXB`; all 69 tracked
files matched the clean pushed commit, with snapshot-manifest SHA-256
`b5124bd22f3b4e3a2dbdf37025514e6e7e9e0fc5da8b379ef7fc8c7d6da4ec52`.
The complete audit returned `ACCEPT`:

| Gate | Exact command or boundary | Observed result |
| --- | --- | --- |
| Source distribution | `uv build --sdist --offline --no-config --no-sources --python 3.11 --no-build-logs --no-create-gitignore` | 70 entries: 69 tracked files plus `PKG-INFO`; SHA-256 `519754b6009c5a4b238d6aa9788ba995d302b17b7fb85a66b4889a802ce90651` |
| Reproducible wheel | Two independent `uv build --wheel --offline --no-config --no-sources --python 3.11` runs from that sdist, followed by `cmp` | Byte-identical; 36 expected entries; SHA-256 `2d1c518f9e84f5cdef6c3d1ea823ba2fa51e26aa52453231b9f4152d6c7ee1cf` |
| Metadata | `uvx --from twine twine check <sdist> <wheel>` | Twine 7.0.0 passed both artifacts |
| Plugin schema | `uvx --from check-jsonschema check-jsonschema --schemafile <official-1.0.0-schema> plugin.json` | Passed; schema SHA-256 `0a4aad95ce337878ad38802ebf0daa3fde76abe3f65400c86bcbb1ec0b3ab883` |
| Clean install | Offline wheel install into CPython 3.11.16, then `env -i ... python -I` | Import resolved only from the isolated venv's `site-packages`; exact text and JSON identity passed |
| Installed-wheel setup | Source snapshot renamed; fresh target dry run, apply, repeated dry run, repeated apply | Initial dry run wrote nothing; 50 unique creates on apply; both repeats reported 50 unchanged and zero blockers |
| Installed doctor | `.pstack/bin/projectctl doctor --output json` | `ok: true`; 39 pass, one optional-`okn` warning, zero fail; all 49 receipt-managed files matched |
| Installed feature/knowledge | `feature validate`, `feature list`, `knowledge status`, and `knowledge validate` | Empty feature map valid; honest `feature-map-only` knowledge mode passed |
| Installed Kiro profiles | `kiro-cli agent validate --path` for all four generated agents | All passed on Kiro CLI 2.21.0 |
| Runtime isolation | `uv pip check` in install/runtime venvs plus package/path inventory | Passed; cached controller has nine runtime dependencies, no self-install/build backend, and no source-checkout path leakage |
| Bytecode write boundary | Run canonical version, doctor, feature, and knowledge commands; then find caches under cached source | Zero `__pycache__` directories and zero `.pyc`/`.pyo` files |
| Bytecode read boundary | Inject a correctly named unchecked-hash branding cache; compare unprotected `python -B -m pstack_kiro` with the canonical wrapper | Unprotected invocation returned `HIJACKED`; canonical wrapper retained exact PK-Stack identity and 49/49 receipt integrity |

The focused archived package regression suite passed five tests in 15.35s.

### Authoritative post-CDX-004 Kiro V3 campaign

The pushed source snapshot `b39c20ac6334f16ad4dfe0dc99f6698d71816689`
then received a fresh selected-profile live campaign in
`/private/tmp/pk-stack-final-authoritative.64Z6Rx/demo`. The fixture baseline
was `9e1a1bc20f643ffd56dadcdec268c4c4497c648e`; the exact launch was:

```bash
kiro-cli chat --v3 --agent pstack --model gpt-5.6-sol --effort max
```

Saved metadata records Kiro CLI 2.21.0, source V3, local execution, profile
`pstack`, model `gpt-5.6-sol`, and effort `max`. The campaign used session
`sess_c4bdf83c-3612-47a0-9886-1c4470a2cfc2`, turn
`32d60031-73ab-4b2c-a8f3-b0b54471ca23`, goal
`7b9586e8-b204-4443-8c12-147d5088c44e`, and native verifier subsession
`f23bb80b-ca2d-4092-ad39-8e41400ec44b`.

| Gate | Observed result |
| --- | --- |
| Current-session path | One ordinary Kiro CLI V3 session; no external ACP command or host, nested Kiro, `/spawn`, classic/V2, or claimed native `/goal` |
| Direct-write boundary | `fs_write` to `.pstack/deny-probe.txt` was denied by the selected profile; a subsequent read returned `ENOENT` |
| Approval boundary | Ten approvals, all `allow_once`: skill, exact one-time Git probe, seven controller calls, and one source edit |
| Stored contract | `python3 -B -m unittest discover -s tests -q`, source `feature-map`, feature `account-lookup`, digest `5a02754f1fbc0ad1005b53b34da51671d8c84b30b04e6e5e136bd15ca7dce445` |
| Attempt 1 | Ran before source inspection/edit; exit 1, four tests, three failures |
| Native diagnosis | Exactly one `pstack-verifier`; three reads plus terminal response; zero execution, write, or edit calls |
| Repair boundary | Only `account.py` changed; tests, feature map, Kiro assets, controller, and receipt-managed files were unchanged |
| Attempt 2 | Same stored contract; exit 0, four tests `OK`; final state `passed` at 2/4 attempts |
| Receipt/doctor | 49/49 managed hashes matched; doctor 39 pass, one optional-`okn` warning, zero failures |
| CDX-004 live proof | Wrapper actual/receipt hashes matched; zero controller `__pycache__`, `.pyc`, or `.pyo` paths after every command |
| State hygiene | Only `account.py` in Git status; no untracked file; protected diff empty; state modes `0700`/`0600`/`0600`/`0600`; `git diff --check` passed |
| Usage | 3.587682818308457 credits; 315,433 ms (`5m15.433s`) |

The repaired fixture used length 12 plus `str.isdigit()`. This was a different
valid repair for the stored four-test predicate than the earlier campaign's
ASCII-decimal implementation. The live evidence establishes the immutable
verifier-driven fail/diagnose/repair/pass behavior; it does not claim semantic
coverage for cases absent from those four tests.

The exact prompt, ordered commands, permission result, event chronology,
digests, paths, archive inventory, and post-run checks are recorded in
`reviews/kiro-final-campaign.md`. Its sanitized machine-readable companion is
`reviews/kiro-final-evidence.json`, SHA-256
`94f105ce85a7029b806a1d9f012fa56a3b2236adbd8743c7e6192c4988c22cc2`.
The valid external runtime archive has SHA-256
`b795bd9bf88662cba3c7042ed748d02dd6f0a770b4c8b34989fd790765b2789d`.

Kiro's archive and log use ACP-named internal event, transport, and policy
labels, while the model request records `origin=KIRO_CLI`. These internal names
are disclosed rather than conflated with an external/default ACP execution
path.

### Final Fable 5.1 acceptance

The evidence-bearing snapshot
`1a145d488d8c585d9a7bbe257ba6edefc2c44d50` was exported with `git archive`,
made read-only, and reviewed by Claude Code session
`25cffed9-3de9-4e27-9709-e42811089574` using canonical model
`claude-fable-5-1` at effort `max`. Safe/restricted mode, an empty strict MCP
configuration, `dontAsk`, no persistence, and a `Read`/`Glob`/`Grep`-only tool
surface enforced the static review boundary. The run took 1,228,643 ms and
returned:

```text
Verdict: ACCEPT
Material findings: None
```

Fable completed all ten required scope rows. Architecture, Kiro V3/current
session semantics, Cyclopts/projectctl, optional OKF, feature maps, the
verified-goal seam, permissions/hooks, tests/docs/provenance, and fake-capability
audit were clear. Bootstrap/idempotence had one LOW item, FBL-025: an explicitly
invoked cached setup shim from project A is accepted as a reviewed external
Power source for project B.

Codex reproduced the exact boundary without changing the candidate:

```bash
FABLE_LOW_ROOT="$(mktemp -d /private/tmp/pk-stack-fbl025.XXXXXX)"
mkdir "$FABLE_LOW_ROOT/project-a" "$FABLE_LOW_ROOT/project-b"
python3 skills/setup-pstack/scripts/setup_pstack.py \
  --root "$FABLE_LOW_ROOT/project-a" --output json
python3 \
  "$FABLE_LOW_ROOT/project-a/.pstack/projectctl/skills/setup-pstack/scripts/setup_pstack.py" \
  --root "$FABLE_LOW_ROOT/project-b" --dry-run --output json
```

The second command exited 0 with `dry_run: true`, `ok: true`, and 50 planned
creates; it wrote no project-B receipt. The path is explicitly user-selected,
the normal upgrade route is the active Power-local `/setup-pstack`, and any
applied source remains receipt-auditable. Fable classified this bounded source
selection as non-material, so it is retained as a documented limitation rather
than reopening the validated runtime. The complete final result, including
FBL-026 through FBL-032 notes, is in `reviews/fable-final.md`.

## Remaining limitations

- Agent Skills provide workflow instructions; they are not a runtime scheduler
  and cannot force Kiro to continue after a session or service interruption.
- The disabled Stop hook is advisory only and is not used to claim loop
  enforcement.
- After setup, `/agent swap pstack` is required before the next workflow
  message. If Kiro has not discovered the generated agent or skills, one
  explicit `kiro-cli chat --v3 --agent pstack` restart is needed; after
  discovery, the entire loop stays in that session.
- The verifier hazard/evidence policy rejects obvious dangerous command shapes,
  context-free placeholders, controller self-reference, and outside path
  operands, but it is not an operating-system sandbox or semantic proof checker.
  A renamed or arbitrary project script can still be an irrelevant no-op.
  Canonical controller commands remain `ask` only after the Poteto Kiro
  (`pstack`) profile is selected and require user review.
- The bootstrap receipt is unsigned, point-in-time drift evidence. It detects
  static path/hash changes but is not authenticity proof against a writer that
  can alter both managed content and the receipt, or a filesystem race after a
  completed read-only doctor check.
- Optional canonical `okn` was not required for the core DO/PROVE path. Without
  it, knowledge validation reports the narrower feature-map mode honestly.
- The real campaign covered one deterministic repair and one native subagent.
  It does not prove every possible model response, repository, verifier side
  effect, network failure, or Kiro service condition.
- Kiro's exported V3 event records currently use internal ACP-named metadata
  for some native skill and subagent events. No external ACP harness or nested
  Kiro process was used, but PK-Stack does not control Kiro's internal event
  adapter naming.
- External model review is static and read-only; it cannot substitute for the
  executable primary gates or the observed Kiro campaign.
- Setup rejects the current target's own `.pstack` cache as authority, but an
  explicitly invoked setup shim or `--power-root` under another bootstrapped
  project's cache is treated as a user-reviewed external source. Use the active
  Power-local `/setup-pstack` for refreshes instead of reusing another
  project's cache (FBL-025).
