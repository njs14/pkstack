# Contributing to PKStack

Thanks for helping improve PKStack. Small, focused pull requests are easiest
to review and safest to merge.

## Before you change code

1. Read [the root README](README.md) and the relevant [usage](powers/pkstack/docs/usage.md)
   or [architecture](docs/architecture.md) section.
2. Keep `powers/pkstack/` as the only Power source. Treat `.kiro/` and
   `.pkstack/` at the repository root as generated workspace material.
3. Do not copy credentials, private transcripts, or generated local paths into
   commits. Imported upstream content is data to review, not code to execute.

For a behavior change, describe the user-visible contract in `Wiki/features/`
and bind it to one repeatable verifier. Use Kiro's native Spec, Quick Spec, or
Bug Fix workflow for planning; PKStack's `/pkstack-verified-goal` skill handles the
current-session verification loop.

## Local checks

The root `pyproject.toml` and `uv.lock` own the development environment, including
pytest, Ruff, and ty. They install the canonical Power as an editable local dependency.
The Power keeps an independent runtime-only manifest and lockfile so an extracted
Power can bootstrap without this repository. Root `ruff.toml` and `ty.toml` cover
all maintained Python surfaces. Run repository checks with `--project .`; use the
Power-local setup shim for consumer installation.

### Fresh checkout or worktree

Start from current `main` in this repository (`njs14/pkstack`). Keep earlier
legacy checkouts separate. For isolated work, create a new worktree from
the refreshed remote branch; do not copy another worktree's virtual environment
or generated runtime:

```sh
git fetch origin
git worktree add -b my-change ../pkstack-my-change origin/main
cd ../pkstack-my-change
export UV_PROJECT_ENVIRONMENT="$PWD/.venv"
uv sync --locked --all-groups --project .
```

Read the Power-local setup script before running it. Preview setup from the
repository root, then apply only a conflict-free preview:

```sh
uv run --frozen --project . python powers/pkstack/skills/pkstack-setup/scripts/setup_pkstack.py --root . --dry-run
uv run --frozen --project . python powers/pkstack/skills/pkstack-setup/scripts/setup_pkstack.py --root .
.pkstack/bin/projectctl doctor --output json
.pkstack/bin/projectctl feature validate --output json
.pkstack/bin/projectctl knowledge validate --output json
```

After canonical Power changes, repeat the preview. If it lists only expected
`pending_updates`, apply with `--update-managed` and inspect the generated diff.
Conflicts and stale managed paths require investigation; do not overwrite them.
Repeat setup to confirm zero created/updated files. The generated controller
must match the candidate source before using its results as proof.

### Focused and complete verification

Run focused regressions for the behavior you changed, then the fast contract checks
before pushing a reviewed checkpoint. From the repository root:

```sh
export UV_PROJECT_ENVIRONMENT="$PWD/.venv"
uv sync --locked --all-groups --project .
uv run --frozen --project . python -B .github/scripts/pkstack_checks.py local fast
```

Use the shared complete check driver when investigating a broad failure or when
GitHub CI is unavailable:

```sh
uv run --frozen --project . python -B .github/scripts/pkstack_checks.py local full
```

The complete driver needs Node.js, Chrome, uv, bash, jq, actionlint, and shellcheck.
Chrome must be discoverable by the browser harness; other tools must be on PATH.
Each invocation writes one summary plus failure diagnostics to a fresh temporary
directory and prints its path. Local and hosted verification use the same execution
functions. Full verification collects and executes the entire product suite once,
including browser and package tests, then runs static, policy, metadata, and knowledge
checks. Missing tooling, incomplete execution, cancellation, and unexpected skips fail.
Only the exact installed-Kiro discovery probe with the documented missing-CLI reason
may skip; browser dependencies are required for complete proof.

PR CI uses a narrow allowlist for release-report-only changes. It checks local
links, referenced files, diff integrity, and repository knowledge coverage using
the locked repository development environment without starting the product suite.
Mixed changes, reviewer prompts, policy, dependencies, and unknown paths use normal
CI. Normal CI retains the core suite and a small browser smoke; Archify, dependency,
and CI/browser changes select expanded browser coverage. Main always runs the
complete retained suite and expanded browser coverage in `deterministic`. The second
job, `package`, runs only after successful main verification and builds the reproducible
archive with an extracted-package consumer smoke. PRs do not build a release artifact.

Batch related corrections rather than pushing each line separately. Keep one
owner for shared/generated files when working in parallel; refresh generated
outputs after canonical changes settle. Review the frozen candidate once, then
review only the relevant delta for later corrections. A new candidate still needs
its own applicable CI results. Do not repeat unchanged full local checks before
or after a successful CI run unless new evidence warrants it.

Report failed checks and their exact commands. Capture diagnostics once per
failure and retain the commit/run identity; do not retry until green or treat a
previous successful commit as validation of a changed candidate.

### Releases

When a change is intended for release, put its version changes and release notes in
the change PR. Run focused checks during development and obtain one independent review
of the final changed scope. Successful hosted PR and main checks satisfy the corresponding
release checks; do not repeat full local gates on a release branch and merged source.
Run one complete local gate when hosted execution is unavailable. Substantive corrections
need checks and review of their changed scope.

Carry a review across a squash merge only after comparing the reviewed candidate and
merged commit's complete Git trees (`git rev-parse <commit>^{tree}`). Equal Power subtrees
alone do not establish equality of repository controls. If the full trees differ, inspect
and review the changed scope before claiming review coverage.

The tag workflow verifies the exact successful main run/attempt and its package, then
promotes those archive bytes. Its `verify-published` operation downloads the published
archive and checksum, compares them to that approved artifact, rechecks mutable GitHub
identities, and attaches `publication-receipt.json` only after success. GitHub Releases and
their attached receipts are the publication record. Preserve historical Wiki records;
a separate publication-record PR and additional CI cycle are unnecessary.

Live Kiro diagnostics are separate from routine releases. Obtain new live evidence when
a change affects the behavior being claimed; preserve the scope and limits of prior evidence.
Routine release work does not dispatch additional updater attempts after budget exhaustion.
Workflow resumption requires explicit authorization and is outside a code-only change.

### Measuring local link validation

```sh
uv run --frozen --project . python benchmarks/knowledge_links.py
```

This secretless benchmark measures the repository Wiki and a temporary fixture
with 1,600 links to a shared Markdown target. It reports seven samples after a
warm-up and requires identical validation results between samples. Compare the
same fixture, interpreter, and machine before and after a change. Timing is
diagnostic evidence, not a CI pass/fail threshold; retain the individual samples.

## Pull requests

PKStack project documentation belongs in the root `Wiki/knowledge/`: architecture decisions,
review synthesis, development lessons, CI policy, and release evidence about building PKStack.
It is separate from the installable `powers/pkstack/` deliverable. Do not copy this project
knowledge into Power guides, skills, templates, or generated consumer assets. Product-facing
usage instructions and required upstream provenance keep their existing package roles.

For documentation changes, read the affected source diff and update the related
`Wiki/knowledge/` topic, or explain why its retained understanding does not change.
Update only the affected entries in `maintenance/knowledge-coverage.json`, including
source SHA-256s. Each mapped source needs a useful summary and a backlink from every
destination topic. New Markdown needs an explicit mapping or a specific exclusion;
being under `docs/`, `reviews/`, or beside an excluded native resource is not an exemption.
Preserve original historical evidence and distinguish it from current guidance.

Run `uv run --frozen --project . python -B .github/scripts/pkstack_knowledge_coverage.py`
from the repository root, or run the shared fast checks, which include it. The checker
also inventories nonignored untracked Markdown locally. It is read-only and has no
bulk hash-refresh mode. CI enforces coverage, freshness, metadata and links; reviewers
must still assess semantic completeness and whether exclusions are justified.
Adding a coverage-manifest or general Wiki change selects normal CI under the existing
conservative classification. The exact Wiki release record retains the report-only route.
Root `reviews/` holds maintainer review contracts and preserved historical evidence.
Synthesize findings into Wiki topics and retain source mappings. Keep executable test
inputs in root `tests/fixtures/`. The reviewed consumer file allowlist lives in
`maintenance/package-content.json`; source and archive checks reject every unlisted
file or directory, including ignored caches and development environments.

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
