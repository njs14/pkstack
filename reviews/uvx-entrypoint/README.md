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
release workflows are unchanged. The uvx acceptance module stays together in the packaging lane.

The [full local gate](full-gate-summary.json) passed against frozen candidate
`9e9f3277a1a960870697b15fd0735aa771bf8331`: all 10 lane receipts passed, covering 1,016 Power
tests, 235 repository tests, actionlint, shellcheck, Ruff, ty, doctor, and knowledge validation.

[Grok 4.6 with xhigh reasoning approved](grok-review.md) the same candidate against base
`2fe0babf05f753f732312b1187986ca5b0533e70`, with no requested changes. The review inspected
source and coordinator-provided evidence; it did not execute candidate code. Its final log read
preceded full-gate aggregation, which subsequently completed successfully. See
[review metadata](grok-review-metadata.json). The following commit records evidence only;
implementation, tests, configuration, documentation, and generated assets remain at the reviewed
candidate. Hosted CI on the final stacked PR head is reported in the PR checks.
