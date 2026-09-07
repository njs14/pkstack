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

Full local and independent review results will be recorded against the frozen candidate. Hosted
CI must pass on the final stacked PR head before delivery.
