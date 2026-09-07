# uvx launcher acceptance

This candidate adds the `pkstack` console entrypoint for reviewed local wheels or checkouts.
Setup and explicit upgrades use the downloaded package; project commands delegate to the
project's checked, receipt-managed `.pkstack/bin/projectctl`. Existing entrypoints remain valid.
Publishing, release workflow changes, merging, and tagging are outside this change.

The external Claude Opus 5 implementation session reached its usage limit before its final report.
The coordinator completed integration and reviewed the code, corrected explicit source selection
in help, preserved an adjacent caller PATH entry, structured execution errors, and added the new
command to the existing verifier self-evidence guard. No usage reset or global installation occurred.

Targeted checks passed: 39 documentation/launcher cases, 313 verifier policy cases, 3 real-wheel
uvx acceptance cases, and 11 packaging/distribution/release-metadata cases. The wheel exercise uses
isolated uv tool/cache directories and covers preview/idempotency, conflicts, distinct launcher and
controller versions, an explicit upgrade, goal fail-repair-pass, cancellation with verifier-process
cleanup, and a real application virtualenv with a dependency available only in that environment.
These are deterministic CLI checks, not a new native Kiro model or IDE acceptance campaign.

The test harness initially disabled managed Python without selecting a supported interpreter,
which selected macOS Python 3.9. It now selects its test interpreter explicitly. Documented commands
request Python >=3.11. A cancellation-test diagnostic was repaired without suppressing type checks.

[Previous-controller compatibility](previous-controller-compatibility.json) records real version
and doctor calls through the new launcher against a project installed from PR #53. All managed
files stayed unchanged, and the older controller did not gain the new launcher module.

CI now checks pull requests targeting branches other than main, allowing this stacked PR to be
validated. Both release-artifact production and retention remain restricted to main pushes;
release workflows are unchanged. The uvx acceptance and documentation walkthrough modules stay together in the packaging lane.

The [full local gate](full-gate-summary.json) passed against frozen candidate
`9e9f3277a1a960870697b15fd0735aa771bf8331`: all 10 lane receipts passed, covering 1,016 Power
tests, 235 repository tests, actionlint, shellcheck, Ruff, ty, doctor, and knowledge validation.

[Grok 4.6 with xhigh reasoning approved](grok-review.md) the same candidate against base
`2fe0babf05f753f732312b1187986ca5b0533e70`, with no requested changes. The review inspected
source and coordinator-provided evidence; it did not execute candidate code. Its final log read
preceded full-gate aggregation, which subsequently completed successfully. See
[review metadata](grok-review-metadata.json). The initial follow-up commit recorded evidence only. Hosted CI on the final stacked PR head is reported in the PR checks.


## Hosted CI remediation

The first hosted run, [34072770497](https://github.com/njs14/pkstack/actions/runs/34072770497),
failed the three documentation walkthrough tests. They inherited an offline-only harness from the
previous direct-bootstrap path. A locked `uv sync` had cached distribution files but not the
registry metadata required by `uvx --from` resolution. The coordinator's populated local cache
had masked this prerequisite. Other executable jobs, including the real-wheel packaging tests,
passed that run.

Commit `f218172` changes only test configuration and lane assignment. Each walkthrough now uses
empty, isolated uv cache/tool directories and resolves dependencies in the existing packaging
lane, whose network allowlist already supports those dependencies. Runtime code, documentation,
workflow permissions, release workflows, and artifact gates are unchanged. All three cold-cache
walkthroughs passed in 58.01 seconds; all 16 check-plan tests and the complete static gate passed.
The original full local gate remains bound to `9e9f327`; this test-only correction receives
independent follow-up review and full hosted checks rather than a second local full run.

[Grok approved the bounded correction](grok-followup.md), preserving its original approval of the
unchanged launcher implementation. [Follow-up metadata](grok-followup-metadata.json) records the
review session and candidate. The following commit changes review evidence only.
