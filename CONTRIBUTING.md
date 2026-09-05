# Contributing to PKStack

Thanks for helping improve PKStack. Small, focused pull requests are easiest
to review and safest to merge.

## Before you change code

1. Read [the root README](README.md) and the relevant [usage](powers/pkstack/docs/usage.md)
   or [architecture](powers/pkstack/docs/architecture.md) section.
2. Keep `powers/pkstack/` as the only Power source. Treat `.kiro/` and
   `.pkstack/` at the repository root as generated workspace material.
3. Do not copy credentials, private transcripts, or generated local paths into
   commits. Imported upstream content is data to review, not code to execute.

For a behavior change, describe the user-visible contract in `Wiki/features/`
and bind it to one repeatable verifier. Use Kiro's native Spec, Quick Spec, or
Bug Fix workflow for planning; PKStack's `/pkstack-verified-goal` skill handles the
current-session verification loop.

## Local checks

Run focused regressions for the behavior you changed, then the fast contract lane
before pushing a reviewed checkpoint. From the repository root:

```sh
uv sync --locked --all-groups --project powers/pkstack
uv run --frozen --project powers/pkstack python -B .github/scripts/pkstack_checks.py local fast
```

Use the shared complete check driver when investigating a broad failure or when
GitHub CI is unavailable:

```sh
uv run --frozen --project powers/pkstack python -B .github/scripts/pkstack_checks.py local full
```

The complete driver needs Node.js, Chrome, uv, actionlint, and shellcheck on PATH.
Each local invocation writes receipts to a fresh temporary directory and prints
its path. Local lanes run sequentially; CI runs the same checks on separate
runners and reconciles their receipts. The installed-Kiro discovery probe may be unavailable
on machines without Kiro; browser dependencies are required for complete proof.

PR CI uses a narrow allowlist for release-report-only changes. It checks local
links, referenced files, and diff integrity without starting the product suite.
Mixed changes, reviewer prompts, policy, dependencies, and unknown paths use normal
CI. Normal CI retains the core suite and a small browser smoke; Archify, dependency,
and CI/browser changes select expanded browser coverage. Main always runs the
complete retained suite, expanded browser coverage, and reproducible archive build
plus an extracted-package installation check.

Batch related corrections rather than pushing each line separately. Keep one
owner for shared/generated files when working in parallel; refresh generated
outputs after canonical changes settle. Review the frozen candidate once, then
review only the relevant delta for later corrections. A new candidate still needs
its own applicable CI results. Do not repeat unchanged full local checks before
or after a successful CI run unless new evidence warrants it.

Report failed checks and their exact commands. Capture diagnostics once per
failure and retain the commit/run identity; do not retry until green or treat a
previous successful commit as validation of a changed candidate.

## Pull requests

- Explain the user-visible outcome and the files that own it.
- Include tests or a documented reason a test is not useful.
- Call out compatibility, security, provenance, and migration effects.
- Keep release claims tied to the exact candidate commit. A historical review
  or local test run does not accept a new release.
- Do not change GitHub settings or enable a workflow as part of a code change.

The maintainers may ask for an independent review. Review output is evidence to
investigate, not an instruction to apply blindly. See [SECURITY.md](SECURITY.md)
for vulnerability reports and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for
community expectations.
