---
type: Guide
title: Local checks, CI jobs, and evidence limits
description: Fast versus complete checks, static Python coverage, browser diagnostics, and knowledge coverage enforcement.
tags: [pkstack, ci, testing, python, knowledge]
---

# Local checks, CI jobs, and evidence limits

## Use the candidate's checked environment

Use a clean checkout/worktree of current PKStack, the locked root development environment, and reviewed setup
previews. Do not copy another worktree's virtual environment or generated controller. After
canonical asset changes, refresh only expected managed updates and confirm a second preview is
clean. A stale generated controller cannot validate a changed Power.

The shared `.github/scripts/pkstack_checks.py` driver retains `local fast` and `local full`.
Hosted verification calls the same execution functions. The `deterministic` job owns product
collection once, including applicable browser and package tests, static analysis, workflow/shell
policy tests, metadata, generated parity, and knowledge validation. One summary binds the source
commit, configuration digest, profile, collection and individual test phases. Missing tooling,
duplicate or incomplete execution, cancellation, and unexpected skips prevent success. Only the
exact installed-Kiro sentinel with its documented missing-CLI reason is allowed to skip.

The narrow reports-only PR path still validates knowledge coverage, links and diff integrity.
Normal PRs use browser smoke unless Archify, dependency or CI/browser changes require full
coverage. Main always uses full browser coverage. The only other CI job is `package`: it waits
for successful main `deterministic` verification, builds reproducible bytes and runs the
extracted-package consumer smoke. PRs do not produce release packages. Distributed shards,
execution-plan transfers, per-job receipts and aggregation have been removed. A local fast pass
covers only the explicitly selected contracts and is not a full-suite pass.

After an autonomous maintenance merge, the trusted merge job explicitly dispatches this same
two-job CI with the merged SHA. [GitHub suppresses push triggers caused by `GITHUB_TOKEN`](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow); the
dispatch supplies the next candidate's exact-base evidence and the release artifact. Dispatched
CI requires main and rejects a SHA mismatch before verification, including a branch-move race.
The verifier considers the newest main run across push and dispatch events without fallback.

Maintainer commands set `UV_PROJECT_ENVIRONMENT` to the repository's ignored `.venv`.
Root `pytest.ini` collects `tests/`; root Ruff/ty configurations cover the relocated
tests, benchmarks, installed source, examples, and setup. The root `pyproject.toml`
and `uv.lock` install the Power as an editable dependency and own pytest/Ruff/ty.
The independent Power lock contains runtime dependencies only; static verification
checks both locks, and the CI configuration digest includes both manifests/locks. `.coveragerc` retains branch measurement and the 85 percent threshold.
Pytest and Ruff caches stay at the repository root. The collected test IDs remain
`tests/...`, preserving the complete collection and the installed-Kiro skip sentinel.
Trusted-controller snapshots retain their own private `.venv`: each trusted `uv sync`
explicitly overrides the root environment setting before later steps invoke that
snapshot interpreter. The workflow regression exercises all four synchronization sites
without candidate code or network access.

## Hosted rollout and measurement

All seven PKStack workflows remain manually paused because of GitHub Actions usage limits.
Local implementation and validation do not resolve those limits or establish hosted execution.
Do not enable workflows, alter billing, change repository visibility or move credentials as part
of this rollout. After explicit resumption authorization, validate one PR/main cycle and one
updater lifecycle, including its candidate's terminal result. The first main cycle must create
compatible two-job CI evidence before a candidate can be admitted.

The baseline below was retrieved from GitHub run and job timestamps. Runner time is the sum of
job execution durations, excluding queue time; it is not an invoice or per-job billing rounding.
The CI baseline is a main push from the prior layout; measure the new PR and main runs separately.

| Reference execution | Elapsed | Runner time | Job count |
| --- | --- | --- | --- |
| [Prior CI](https://github.com/njs14/pkstack/actions/runs/34254995824) | 2m26s | 8m56s (8.93 minutes) | 12 |
| [Prior updater](https://github.com/njs14/pkstack/actions/runs/34254835687) | 49m52s | 49m32s (49.53 minutes) | 4 |
| Consolidated PR/main cycle | Pending authorized resumption | Pending | 1 verification job on PR; 2 jobs on main |
| Bounded updater lifecycle | Pending authorized resumption | Pending | Existing isolated stages retained |

The target is less repeated work and lower runner consumption. Fewer concurrent CI jobs can make
one run take longer. Local timing and isolated API fixtures do not predict hosted duration or
establish a live update/merge/publication result.

## Python coverage and browser failures

The shared static gate checks maintained Power code, tests, benchmarks, examples, setup scripts,
and repository Python. It also extracts recognized quoted Python heredocs into temporary files
for lint, format and type analysis without executing their bodies. Unsupported or ambiguous
forms fail with their origin. Generated mirrors and intentional historical fixtures have separate
ownership/parity checks; excluding them from static analysis does not exempt maintained scripts.

Use locked uv/Ruff/ty and preserve the pre-uv bootstrap guard. Static success does not establish
runtime behavior. A prior static cleanup accidentally changed malformed-input behavior from a
structured `StreamError` to `TypeError`; regression testing caught it. Check failure behavior as
well as type-checker output when narrowing untrusted JSON values.

For browser failures, separate the initiating symptom from defects reproduced during diagnosis.
The 0.3 investigation reproduced leaked startup processes/profiles and terminal process/pipe
handling defects. It did not reproduce the original Linux `Target.getTargets` startup timeout.
Cleanup fixes and bounded diagnostics do not establish that timeout's cause. Retain the first
failure and exact environment before changing retries or timing.

Cold-cache packaging tests matter: the uvx walkthrough failure occurred before any application
command because offline resolution lacked registry metadata despite a prior locked sync.
Warm-cache local results had hidden the prerequisite. See
[installation and upgrades](installation-and-upgrades.md#first-task-evidence-and-limits).

## Repository knowledge gate

`maintenance/knowledge-coverage.json` gives each Markdown path exactly one disposition. Canonical
Wiki documents use the local authoring profile. Mapped sources retain a SHA-256, useful summary,
and Wiki destinations with backlinks. Excluded native, generated, vendor, policy, fixture, or
historical files retain an exact path, SHA-256 and reason. There are no directory-wide exceptions:
a new file requires review even beside excluded resources. Locally, nonignored untracked Markdown
also participates so a new document cannot produce a misleading green pre-commit result.

Run the read-only gate from the repository root:

```sh
uv run --frozen --project . python -B .github/scripts/pkstack_knowledge_coverage.py
```

It rejects stale hashes, unclassified/obsolete/unsafe paths, invalid mappings, missing backlinks,
and local Wiki metadata/link errors. A Markdown link in a code block, comment, image, or plain path
does not satisfy a backlink. Native instruction alias `CLAUDE.md -> AGENTS.md` is the sole reviewed
symlink exception; its link bytes are hashed and its target must be safe. Other symlinks fail.

For a changed source, review the diff, update affected Wiki understanding or explain why none
changes, then refresh only that source's manifest entry. Do not mass-accept new hashes. The checker
has no write or refresh mode. Hash freshness and valid links cannot prove semantic completeness;
human or agent review must still check that the retained explanation is adequate and honest.

Both normal and reports-only CI run the gate using the locked environment. The exact Wiki release record retains lightweight report checks; adding a manifest or other
Wiki change selects normal CI
under the existing conservative classifier. Main also runs the gate. Consumer-project setup and
the public `projectctl` interface do not acquire this repository-specific policy.

The separate autonomous updater also runs the immutable base checker with `--base` before its
candidate can merge. That mode limits coverage changes to changed sources and their linked topics;
it cannot drop mappings, broaden exclusions, or change unrelated entries. The
[updater operations guide](../upstream-maintenance/operations.md#knowledge-changes-travel-with-the-source-update)
explains proposed Wiki updates, private hash diagnostics, and independent semantic review.


## Preserve the failure, then test the mechanism

The [browser investigation](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-030-browser-harness.md) began with an Ubuntu
CDP startup timeout that was not reproduced locally. It did reproduce a cleanup bug: awaiting
startup before entering `try/finally` left the child and temporary browser profile alive when
startup rejected. A fake browser that emitted malformed protocol JSON and stayed alive made the
failure deterministic. The repair had to produce the expected error, terminate the child, and
remove the profile. Increasing the timeout or retrying would not test that ownership obligation.

A later reproduction separated terminal transport failure from an ordinary request error. Pipe
EOF with a live child, and browser exit with a descendant holding pipes open, waited for the full
deadline. Terminal process/pipe errors now reject pending and future requests promptly, while
protocol errors and per-request timeouts remain recoverable. The test owns its descendant; it
does not establish general process-tree cleanup. Later Linux passes validate those repairs without
identifying the original timeout trigger.

The [uvx CI correction](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/uvx-entrypoint/grok-followup.md) illustrates a different
hidden prerequisite. Locked sync populated distribution files, but checkout-based uvx resolution
still needed registry metadata. A developer's warm cache masked an offline-only test environment.
The correction used empty per-test cache/tool directories, removed inherited uv configuration, and
put executable documentation walkthroughs in the existing network-capable package lane. It did
not change the launcher or grant additional workflow permissions. Preserve executable walkthroughs
when moving examples between documents; a text assertion cannot establish successful installation.

## Optimize repeated computation without caching trust decisions

The [performance campaign](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/evidence-led-improvements/README.md) cached heading
parsing by freshly read text, with an eight-entry LRU scoped to one validation. It continued to
check path containment, target existence, bounded reads, and decoding for every link. Tests changed
a target both within a validation and between calls to ensure freshness remained observable.
Caching a path's prior verdict or retaining the cache across calls would have a different contract.

Seven measured samples after a warm-up showed 12× speedup for a synthetic repeated-target corpus,
but only 11.5% less time for the then-small repository Wiki. Report both workloads and require
identical outputs; do not turn the synthetic result into a product latency guarantee or a brittle
CI timing threshold. Doctor's separate profile mostly waited for subprocess checks, which did not
justify deleting integrity checks or adding concurrency. The same review kept small containment
and strict-decoding helpers because their boundary role mattered more than their line count.

For static cleanup, the [Python coverage report](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/astral-python-auto/python-coverage.md)
records a concrete behavioral regression: type narrowing briefly let an unhashable title raise
`TypeError` instead of the structured `StreamError`. Keep malformed-input tests while satisfying
the type checker. Extracted heredocs are analyzed without executing them; unsupported syntax
stops the bounded extractor. The [campaign correction](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/astral-python-auto/README.md)
also fixes its raw review's shell claim: both single- and double-quoted heredoc delimiters disable
body expansion. A review approval does not make every explanatory sentence authoritative.

## Source-specific retained knowledge

These summaries describe what is retained from each source. Historical observations keep their
original candidate and scope; they are not fresh verification of this checkout.

| Source | Retained guidance or bounded observation |
| --- | --- |
| [CONTRIBUTING.md](../../../CONTRIBUTING.md) | Locked worktrees use shared fast/full checks and explicit knowledge mappings. Two CI jobs retain complete checks; release review and attached receipts avoid repeated local gates and publication-record PRs. |
| [reviews/astral-python-auto/python-coverage.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/astral-python-auto/python-coverage.md) | The shared static gate covers maintained Python and quoted heredocs without executing extracted bodies; malformed-input behavior needs regressions alongside type narrowing. |
| [reviews/astral-python-auto/independent-review.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/astral-python-auto/independent-review.md) | Read-only d36bb88 source review checked provenance, routing and maintained Python coverage; coordinator test results and native observations remain separately identified evidence. |
| [reviews/evidence-led-improvements/README.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/evidence-led-improvements/README.md) | Content-keyed per-validation heading caching preserves fresh bounded reads and path validation; performance observations and clean-worktree guidance do not justify speculative cleanup. |
| [reviews/release-030-browser-harness.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/release-030-browser-harness.md) | Startup cleanup and process/pipe lifecycle defects were reproduced, while the initiating Linux Target.getTargets timeout remained unexplained; retain that distinction. |
