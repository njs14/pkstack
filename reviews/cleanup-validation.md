# PK-Stack 0.3 cleanup validation

Validation started on September 4, 2026, against the cleanup branch based on
`af757c76dfe2c9163a919baee645c66e6c207d0f`. This report describes this cleanup,
not a rerun of every historical port acceptance test. Release and live workflow
results are recorded separately below; an unfinished gate is not a pass.

## What changed from the earlier plan

The first-principles pass kept the original direction: Kiro owns planning and
execution; PK-Stack supplies workflow instructions and executable proof.
It removed port-owned machinery that did not support that boundary:

- Removed schema-1 feature parsing, migration commands, and legacy extensions.
  Feature contracts now have one format: schema 2.
- Removed 149 redundant controller-cache files after checking their ownership
  receipt hashes. Canonical Power assets and their live `.kiro/` copies remain.
  Git retains the deleted files; fresh targets no longer receive the duplicate
  2.45 MB cache.
- Allowed one to five features per authoring batch while retaining the upstream
  preference for three to five. Removed mandatory duplicate proof passes added
  by the port, not the upstream requirement to prove work after a fix.
- Rebuilt the README around installation, one real failing task, and recovery.
  A test executes its shell walkthrough in a fresh consumer without source-path
  leakage.
- Made the deterministic updater plan the only source-selection authority.
  Ref-only movement outside an imported subtree no longer spends model credits.
- Deleted model-driven generated-parity repair. Known generated output is
  regenerated from reviewed source; a cadence reports `manual-parity` instead.
- Kept one durable latest reviewer report and rejection count per source. A
  source/content pair stops after three substantive rejections. Failed feedback
  persistence leaves the candidate open and blocks the next cadence.

The pass also fixed verifier cancellation, a hanging pipe-close edge case,
relative virtualenv interpreter selection, correction of stale evidence, and
the updater's invalid two-file `unlink` invocation.

## Interactive Kiro CLI

The live campaign used Kiro CLI **2.21.0**, **GPT-5.6 Luna**, and **low** effort in
a real PTY. Its disposable project path included a space. It was not an ACP or
headless session. Every requested shell write/command was inspected and approved
in the terminal; no blanket permission setting was enabled.

```sh
kiro-cli chat --v3 --model gpt-5.6-luna --effort low
```

The session read the Power-local setup skill, previewed setup, applied it, and
ran the generated controller. Setup created 170 files; the repeat preview was
a no-op. Doctor reported 81 passes and no warnings. Feature validation and
knowledge validation passed. The profile switch used `/agent swap pk-stack`
without replacing the conversation.

The `/verified-goal` skill repaired the included account-ID example using:

```sh
.pk-stack/bin/projectctl goal start "Repair account ID normalization" \
  --command "python3 -m unittest discover -s tests -v" \
  --max-attempts 4 --output json
.pk-stack/bin/projectctl goal verify --output json
.pk-stack/bin/projectctl goal status --output json
```

Stored goal `21ac52cf-3eda-4d7e-9cb2-1d6e3e4c571c` recorded:

| Attempt | Result | Evidence |
| --- | --- | --- |
| 1 | Fail | Three failing tests before an implementation edit |
| 2 | Fail | Normalization repaired; two error-message assertions still failed |
| 3 | Pass | All four original tests passed; stored status `passed` |

The tests remained byte-for-byte unchanged during this campaign. The canonical
Power example also remained broken; only the disposable consumer was repaired.

The next native command was `/spec new account-whitespace`. Kiro offered the
native Quick Spec choice and used its `fast-task-workflow` subagent to generate
`requirements.md`, `design.md`, and `tasks.md`. No application or test file was
edited during planning. After `/agent swap pk-stack`, a second `/verified-goal`
invocation added one regression containing embedded tab/newline characters,
preserved the four original tests, and ran:

```sh
.pk-stack/bin/projectctl goal clear --force --output json
.pk-stack/bin/projectctl goal bind-spec account-whitespace \
  --command "python3 -m unittest discover -s tests -v" --output json
.pk-stack/bin/projectctl goal start "Implement account-whitespace Quick Spec" \
  --spec account-whitespace --max-attempts 4 --output json
.pk-stack/bin/projectctl goal verify --output json
# After the recorded failure, Kiro changed only account.py.
.pk-stack/bin/projectctl goal verify --output json
```

The clear was explicitly authorized after preserving the terminal first goal's
evidence; force was unnecessary for its `passed` state. Goal
`634d3f8c-1c02-49ac-b8d1-c4bcc9bd48aa` recorded failure at attempt 1 and pass at
attempt 2, with five tests passing. Its contract has `source: spec` and
`spec: account-whitespace`. The three native planning documents remained
unchanged. No feature was published before implementing this new behavior.

The same PTY then refreshed the consumer from the final reviewed Power source
and ran doctor, all five application tests, knowledge validation, and Archify
doctor in one approved command group. All five commands succeeded. The refreshed
runner, bootstrap code, and verified-goal skill matched the candidate byte for
byte. The only runner difference before that refresh was a removed unused helper.

Baseline `/usage`: **257.82 of 1,000 credits used**. The post-campaign reading
was **258.80**, a difference of **0.98 credits**, resetting October 1, 2026.
This is an account-wide counter, not a per-task meter. Native Quick Spec reported
0.50 credits; the two repair turns reported 0.11 and 0.12 credits respectively.

## Deterministic checks

Run from the repository root unless a directory is specified:

```sh
python3 -B -m unittest discover -s .github/scripts -p 'test_*.py'
node --test .github/scripts/test_pk_stack_pr_policy.js
actionlint .github/workflows/*.yml
shellcheck .github/scripts/*.sh
git diff --check
```

The updater lane recorded 128 Python repository-policy tests and 17 JavaScript
tests passing, plus Actionlint and ShellCheck. Its targeted upstream and release
tests recorded 122 passes. These include executed stub-Kiro shell preflight,
content-only drift, deferred-source preservation, report validation, durable
feedback limits, and generic release-version handling. Stubbed calls are not
evidence of a live provider response.

Run inside `powers/pk-stack`:

```sh
uv lock --check
uv run --frozen ruff check src tests skills/setup-pk-stack/scripts/setup_pk_stack.py
uv run --frozen ruff format --check src tests skills/setup-pk-stack/scripts/setup_pk_stack.py
uv run --frozen ty check
uv run --frozen pytest -q
```

The cleanup suite first passed 811 tests. The follow-up's full suite passed
**813 tests in 146.36 seconds** after the two OpenKnowledge regressions were
added. Lock validation,
Ruff lint and formatting, and type checks passed. This includes runtime/evidence
tests, wheel/offline setup, the README walkthrough, and the detached-stdout test.
The latter proves a bounded error when a separately detached writer keeps the
pipe open; it does not claim process groups contain arbitrary child processes.

Generated-controller checks:

```sh
.pk-stack/bin/projectctl doctor --output json
.pk-stack/bin/projectctl feature validate --output json
.pk-stack/bin/projectctl knowledge validate --output json
.pk-stack/bin/projectctl knowledge search architecture --output json
node .kiro/skills/archify/upstream/bin/archify.mjs doctor
env PATH=/opt/homebrew/bin:/usr/bin:/bin \
  .pk-stack/bin/projectctl knowledge status --output json
env PATH=/opt/homebrew/bin:/usr/bin:/bin \
  .pk-stack/bin/projectctl knowledge validate --require-okn --output json
```

Doctor passed 81 checks. Archify passed 15 checks. Installed `okn` was 0.13.0;
the bounded architecture search succeeded at 1,178 of 1,200 tokens. With `okn`
removed from the test PATH, feature-map-only status succeeded and `--require-okn`
failed with the expected exit code 2. The repository Wiki still has three
cross-Wiki-boundary link warnings; the disposable consumer had none.

## Independent review

The bounded non-pipeline review accepted runner/evidence, bootstrap/doctor, and
the root README changes with no material finding. It excluded that reviewer's
own feature implementation and did not claim independent live-Kiro testing.

The updater review initially requested changes for five cases: feedback-write
failure bypassing the cadence cap, escaped credentials in decoded review output,
parity-only budget bypass, old-subtree reports replacing newer feedback, and an
incorrect approval flag for rejected reports. The final Astra rereview accepted
all five fixes and independently reran 32 passing tests (feedback 6, review-stream
9, PR policy 17). No material finding remains in that reviewed scope. Live GitHub
transport and provider behavior were outside this local rereview.

## Release gate and limitations

[PR #13](https://github.com/njs14/pk-stack/pull/13) contains the implementation
at `3cc2f814f239336c1d7baca41da64363f0666d33` plus subsequent evidence-only edits.
Its first [GitHub CI run](https://github.com/njs14/pk-stack/actions/runs/33930968676)
passed: 128 policy tests, 17 JavaScript tests, and 810 Power tests with the local
Kiro-agent CLI check skipped because Kiro was not installed in that CI job.
Hosted knowledge validation used feature-map-only
mode because canonical `okn` was unavailable. The final evidence-only head
`2a587c8418a84f23c1f3661e50a1b5d781a58357` passed
[CI run 33931307329](https://github.com/njs14/pk-stack/actions/runs/33931307329).
PR #13 merged at `91d1370f9db8e5f3e996648033a4b5fd557fd5c6` on September 4,
2026 at 23:59 UTC. Its
[post-merge CI](https://github.com/njs14/pk-stack/actions/runs/33931443123)
also passed. One bounded
[main-branch maintenance run](https://github.com/njs14/pk-stack/actions/runs/33931459393)
was then dispatched. The live detector found two changed sources and selected
`okf-skills` (`backfill/SKILL.md`), leaving the Archify executable/test changes
deferred. The first Kiro repair completed, but secretless verification rejected
an unexpected immutable control file before any candidate was published.

The failure reproduced in an isolated Python 3.12 archive: running the trusted
model-inventory regression test wrote
`.github/scripts/__pycache__/validate_kiro_model_inventory.cpython-312.pyc` inside
the frozen snapshot. The system Python on this Mac uses a different cache
location, which had masked that integration error locally. The fix disables
bytecode writes for trusted preflight tests and checks snapshot integrity again
immediately afterwards, before a paid model call. The regression forces Linux's
in-tree cache behavior even on this Mac and verifies unchanged inventory/hashes.
The revised policy suite passed 129 tests; JavaScript 17, Actionlint, and
ShellCheck passed. Astra accepted the targeted fix and independently reran its
11 affected tests. [PR #14](https://github.com/njs14/pk-stack/pull/14) passed
[CI](https://github.com/njs14/pk-stack/actions/runs/33932025631) and merged at
`5d8d7079476c6084b683229106aa0c16cf98fbbf`. Its
[post-merge CI](https://github.com/njs14/pk-stack/actions/runs/33932178264) passed.
The corrected [live run](https://github.com/njs14/pk-stack/actions/runs/33932190028)
passed the new Linux preflight and completed four Kiro repair turns. All four
secretless verifier wrappers returned `passed=false`; the terminal candidate
check failed and publication was skipped. The
[candidate gate](https://github.com/njs14/pk-stack/actions/runs/33932778985) was
skipped, so no independent peer review or automatic merge occurred.

The actual failed inner gate was not retained: the existing script deleted its
raw verifier log after creating temporary model feedback, and uploaded only
the detector. Each verifier stopped in roughly two to three seconds, before
the full test stage, but that timing does not establish the failing invariant.
These are four deterministic verifier failures, not four material peer-review
rejections and not evidence of provider unavailability. Release remains gated
while this integration result is unresolved.

The follow-up prints a small per-attempt diagnostic in the retained GitHub
step log: fixed gate name, exit codes, attempt, base commit, and source run ID.
It does not print command output, model transcripts, arbitrary error text, or
environment values. Executable shell regressions cover success, a failed gate,
finalizer failure, and output redaction. No diagnostic artifact collector or
upload is needed.

A separate test had frozen the OpenKnowledge CLI contract's original commit,
empty review history, and 63-file inventory. That would reject a legitimate
future upstream update. The corrected test checks active/prior ledger identity,
complete sorted inventories, derived counts, and the same read-only versus
runtime classifications. Pending and accepted update regressions cover added,
removed, and modified files. Production acceptance validation is unchanged.
This later test blocker does not explain the earlier `okf-skills` failures.
OpenKnowledge's parity JSON was also missing from the maintainer's exact write
allowlist and finalizer boundary, although the controller could select that
source. The fix adds that one path to the policy, profile, and permission
fixture; it does not grant general JSON write access. A manifest-driven check
guards parity-path coverage across all tracked sources.
The permission-smoke fixture's two pinned checksum references were refreshed
to its computed SHA-256. The first full policy rerun caught those stale hashes;
the fixture integrity check was preserved, not bypassed.

Astra accepted the log-only diagnostics, dynamic contract test, and exact-path
permission correction. Its independent focused rerun passed eight tests:
three shell diagnostics, three OpenKnowledge scope tests, and two source-path
coverage tests.
The final local follow-up gates passed 134 repository-policy tests in 12.05
seconds and 17 JavaScript tests, with Actionlint, ShellCheck, and diff checks
clean. The separate full Power gate passed 813 tests as recorded above.

A secretless local reproduction used an archive of `5d8d707` and the saved
detector from run 33931459393. It authored a coherent proposal for the one
changed `okf-skills` path, an exact provenance marker, and the corresponding
13-file parity inventory. Proposal validation, trusted setup, feature validation,
and a repeat no-change setup all passed. The production source-parity helper
returned `candidate-ready`. The changed source identity was commit
`85db7fd0a8a66d07d984ac6c5f4fbb5063d00357`, subtree
`2f9170d6937027c2b1c487ef698f0c000bb47745`.

The guard invocation was:

```sh
python3 -B /private/tmp/pk-stack-cleanup.kOHcaP/.github/scripts/pk_stack_maintenance_guard.py \
  --root . validate-proposal \
  --detector /private/tmp/pk-stack-updater-evidence.lb2cDc/upstream-check.json \
  --proposal .pk-stack-maintenance/proposal.json --selected-source-id okf-skills
```

The controller invocations used the immutable controller's `src` on `PYTHONPATH`
with Python `-B -X pycache_prefix=/dev/null -m pk_stack`, followed by the same
setup/apply, feature validation, and setup/dry-run arguments shown earlier.
This check proves the saved data can satisfy those local gates; it does not
prove fresh remote acceptance, the complete Git boundary, or a model-produced
candidate. The executable shell success regression uses test doubles and is
not a live provider result.

Before the final instrumented campaign, `/usage` showed **283.77 of 1,000**
credits used. That is **25.95** above the initial reading, including the
interactive checks and two live pipeline campaigns. The value is account-wide
and may include concurrent usage; it is not exact task billing.

[PR #15](https://github.com/njs14/pk-stack/pull/15) merged the follow-up at
`f7022d6309e17f70d812817de6bfacc2363e3c25` after
[CI run 33934118636](https://github.com/njs14/pk-stack/actions/runs/33934118636)
passed 134 policy tests, 17 JavaScript tests, and 812 Power tests with the same
one Kiro-not-installed skip. Its
[post-merge CI](https://github.com/njs14/pk-stack/actions/runs/33934250137)
also passed. The final instrumented campaign is
[run 33934250700](https://github.com/njs14/pk-stack/actions/runs/33934250700),
dispatched from that exact main commit. Its detector selected the same
`okf-skills` commit above and deferred Archify.

The first repair completed. The first secretless verifier passed setup,
feature-contract, and generated-parity stages, then recorded this fixed result:

```json
{"attempt":1,"base_sha":"f7022d6309e17f70d812817de6bfacc2363e3c25","cleanup_exit_code":0,"exit_code":1,"passed":false,"schema_version":1,"source_run_id":33934250700,"stage":"proposal"}
```

The failed stage covers proposal presence, proposal/provenance validation, and
binding to the selected source/head. It does not identify which of those inner
checks failed. No raw model output or candidate patch was retained, so this
report does not assign an unproven root cause. The trusted failure cleanup
succeeded. Once the workflow advanced to repair two, the operator requested
cancellation; repair two was cancelled and turns three/four never ran. No
candidate was published, peer-reviewed, or merged. The final workflow status
is `cancelled`, not success and not exhaustion of all four turns.

A bounded local follow-up confirmed preparation and cleanup preserve proposal
bytes, and the coherent saved-detector proposal passes the exact guard CLI
plus selected-source/head `jq` predicate used in CI. Two preparation/source
tests also passed. That rules out a guaranteed interface mismatch in those
local cases; it does not establish why the hosted proposal failed.

The paid **PK-Stack Upstream Maintenance (Kiro)** workflow is now
`disabled_manually` to prevent the daily cadence from repeatedly spending on
this unresolved gate. Deterministic CI remains enabled. Resume only after the
proposal-stage issue is reproduced and corrected:

```sh
gh workflow enable pk-stack-upstream-maintenance-kiro.yml --repo njs14/pk-stack
gh workflow run pk-stack-upstream-maintenance-kiro.yml --repo njs14/pk-stack --ref main
```

The final `/usage` reading was **294.32 of 1,000**: **10.55** above the final
campaign's baseline and **36.50** above the cleanup's initial reading. It is an
estimated account-wide counter, not exact task billing. No additional-credit
purchase or separate provider API credential was used. The live updater gate
remains unresolved; **0.3.0 was not tagged or released**.

- Native IDE Power import, setup, and generated-agent validation passed the
  September 4 smoke test below. An IDE verified-goal repair loop was not run;
  the recorded fail/repair/pass loops above are CLI evidence.
- Kiro Web remains untested; Kiro Crew Nightly was not rerun in this cleanup.
- Kiro owns the native planning behavior. This work does not claim native
  `/goal` support or restore v2-only commands in v3.
- The controller screens commands and isolates their runtime environment; it
  is not an operating-system sandbox.
- The private repository's GitHub plan does not permit the desired main-branch
  ruleset. Application checks and exact-SHA workflow gates remain important;
  neither is described as an administrator-proof branch protection rule.
- No separate Anthropic, OpenAI, xAI, or Copilot API credential was introduced.
  Fable/Grok capacity was not substituted with paid provider API calls.
- Floci remains in its separate private lab repository and was not part of this
  cleanup's runtime campaign.

If the candidate fails a release gate, do not tag it. If a released cleanup
regresses a core flow, use the prior v0.2.0 archive in a clean consumer and revert
the cleanup through a reviewed PR. Do not overwrite user-modified installations
or migrate old goal/schema-1 state implicitly.

## Native IDE smoke test — September 4, 2026

Kiro IDE **1.0.437** accepted the Power through **Powers → Add Custom Power →
Import power from a folder**. The selected folder was
`/private/tmp/pk-stack-cleanup.kOHcaP/powers/pk-stack`, not the repository root.
The UI confirmed `Power "pk-stack" installed successfully.` This validates the
current `plugin.json` package format without adding a legacy `POWER.md`.
The imported source tree was `5fe30be3bad9cc34bf6f26c0b45b5164bd0d8758`,
identical to main commit `1c5f9df6b98bb7219e378278b2510ff2ac900a07`.

The test used a new empty workspace, `/private/tmp/pk-stack-ide-smoke.Is5Xlm`,
with **GPT 5.6 Luna / Low**. The Default agent activated the installed Power,
read `setup-pk-stack`, located its installed script without being given that
path, and executed this no-write preview:

```sh
python3 /Users/noahsutter/.kiro/powers/installed/pk-stack/skills/setup-pk-stack/scripts/setup_pk_stack.py --root . --dry-run --output json
```

The result was `ok: true`, with 168 proposed paths and no conflicts or pending
updates. An independent filesystem check confirmed the workspace remained
empty. The installed shim's SHA-256 matched the source shim. After an explicit
scratch-only setup instruction, the IDE agent ran:

```sh
python3 /Users/noahsutter/.kiro/powers/installed/pk-stack/skills/setup-pk-stack/scripts/setup_pk_stack.py --root /private/tmp/pk-stack-ide-smoke.Is5Xlm --output json
./.pk-stack/bin/projectctl doctor --output json
./.pk-stack/bin/projectctl feature validate --output json
./.pk-stack/bin/projectctl knowledge validate --output json
```

Setup succeeded without conflicts or pending updates. In a fresh chat, the
IDE agent selector listed all four generated workspace agents. Selecting
`pk-stack` and sending a read-only validation request loaded its orientation
hook and steering. Each of these commands required a separate **Allow**:

```sh
.pk-stack/bin/projectctl doctor --output json
.pk-stack/bin/projectctl feature validate --output json
.pk-stack/bin/projectctl knowledge validate --output json
```

Both validation turns reported exit 0 for all three commands:

| Check | Observed result |
| --- | --- |
| Doctor | 81 passed; no failures or warnings; runtime and receipt integrity passed |
| Feature map | `ok: true`; zero contracts, errors, or warnings in the empty consumer |
| Knowledge | `canonical-okn`; `okn` 0.13.0, OKF 0.2; all 10 checks passed; no errors or warnings |

Independent file inspection confirmed the executable runner, managed receipt,
workspace skills, steering, and four agent profiles. The primary profile has
no model/effort override, `includeMcpJson: false`, and `includePowers: false`.
Its controller commands and ordinary writes are `ask`; managed assets have
write denials. This test observed the command approval boundary, not every
denial rule. Autopilot was off for each submitted test turn. No nested Kiro
chat, optional-tool installation, or billing change was performed.

The account dashboard increased from **294.32 to 294.49 of 1,000 credits**
(**0.17** account-wide); individual turn estimates were 0.05, 0.06, and 0.01.
The account counter is not exact task billing. Overages remained disabled.

Desktop capture and accessibility state intermittently disagreed; refreshing
the window layout restored consistent controls. No PK-Stack code change was
needed for this smoke test. Native Spec/Quick Spec choices were visible, but
their IDE execution and the IDE verified-goal loop remain untested. This
result does not clear the paused updater's proposal-stage release blocker.
