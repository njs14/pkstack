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

### Fresh checkout or worktree

Start from current `main` in this repository (`njs14/pkstack`). Keep earlier
legacy checkouts separate. For isolated work, create a new worktree from
the refreshed remote branch; do not copy another worktree's virtual environment
or generated runtime:

```sh
git fetch origin
git worktree add -b my-change ../pkstack-my-change origin/main
cd ../pkstack-my-change
uv sync --locked --all-groups --project powers/pkstack
```

Read the Power-local setup script before running it. Preview setup from the
repository root, then apply only a conflict-free preview:

```sh
uv run --frozen --project powers/pkstack python powers/pkstack/skills/pkstack-setup/scripts/setup_pkstack.py --root . --dry-run
uv run --frozen --project powers/pkstack python powers/pkstack/skills/pkstack-setup/scripts/setup_pkstack.py --root .
./projectctl doctor --output json
./projectctl feature validate --output json
./projectctl knowledge validate --output json
```

After canonical Power changes, repeat the preview. If it lists only expected
`pending_updates`, apply with `--update-managed` and inspect the generated diff.
Conflicts and stale managed paths require investigation; do not overwrite them.
Repeat setup to confirm zero created/updated files. The generated controller
must match the candidate source before using its results as proof.

### Focused and complete verification

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

### Measuring local link validation

```sh
uv run --frozen --project powers/pkstack python powers/pkstack/benchmarks/knowledge_links.py
```

This secretless benchmark measures the repository Wiki and a temporary fixture
with 1,600 links to a shared Markdown target. It reports seven samples after a
warm-up and requires identical validation results between samples. Compare the
same fixture, interpreter, and machine before and after a change. Timing is
diagnostic evidence, not a CI pass/fail threshold; retain the individual samples.

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
