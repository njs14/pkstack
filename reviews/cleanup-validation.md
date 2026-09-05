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

The final full suite passed **811 tests in 132.69 seconds**. Lock validation,
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
11 affected tests. The follow-up live result and 0.3.0 publication are pending.

- IDE Power import is not UI-validated. The installed desktop driver lacks
  macOS Accessibility and Screen Recording permission. The terminal campaign
  used the documented Power-local fallback and did not bypass those permissions.
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
