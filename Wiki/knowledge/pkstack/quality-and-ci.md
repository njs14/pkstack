---
type: Guide
title: Local checks, CI lanes, and evidence limits
description: Fast versus complete checks, static Python coverage, browser diagnostics, and knowledge coverage enforcement.
tags: [pkstack, ci, testing, python, knowledge]
---

# Local checks, CI lanes, and evidence limits

## Use the candidate's checked environment

Use a clean checkout/worktree of current PKStack, the locked Power environment, and reviewed setup
previews. Do not copy another worktree's virtual environment or generated controller. After
canonical asset changes, refresh only expected managed updates and confirm a second preview is
clean. A stale generated controller cannot validate a changed Power.

The shared `.github/scripts/pkstack_checks.py` driver runs fast or full local checks. Normal CI
uses the same deterministic partitions on separate runners. Receipts bind the execution plan,
commit, configuration digest, collection and individual test phases. Aggregation rejects missing,
duplicate, cancelled, incomplete, or unexpected skipped results. PR browser coverage is selected
by the change; main retains the complete suite, expanded browser coverage, and reproducible
packaging plus extracted-package installation checks. A local fast pass is not a full-suite pass.

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
uv run --frozen --project powers/pkstack python -B .github/scripts/pkstack_knowledge_coverage.py
```

It rejects stale hashes, unclassified/obsolete/unsafe paths, invalid mappings, missing backlinks,
and local Wiki metadata/link errors. A Markdown link in a code block, comment, image, or plain path
does not satisfy a backlink. Native instruction alias `CLAUDE.md -> AGENTS.md` is the sole reviewed
symlink exception; its link bytes are hashed and its target must be safe. Other symlinks fail.

For a changed source, review the diff, update affected Wiki understanding or explain why none
changes, then refresh only that source's manifest entry. Do not mass-accept new hashes. The checker
has no write or refresh mode. Hash freshness and valid links cannot prove semantic completeness;
human or agent review must still check that the retained explanation is adequate and honest.

Both normal and report-only fast CI run the gate using the locked environment. Report-only
changes retain lightweight report checks; adding a manifest or Wiki change selects normal CI
under the existing conservative classifier. Main also runs the gate. Consumer-project setup and
the public `projectctl` interface do not acquire this repository-specific policy.

The separate autonomous updater also runs the immutable base checker with `--base` before its
candidate can merge. That mode limits coverage changes to changed sources and their linked topics;
it cannot drop mappings, broaden exclusions, or change unrelated entries. The
[updater operations guide](../upstream-maintenance/operations.md#knowledge-changes-travel-with-the-source-update)
explains proposed Wiki updates, private hash diagnostics, and independent semantic review.


## Source-specific retained knowledge

These summaries describe what is retained from each source. Historical observations keep their
original candidate and scope; they are not fresh verification of this checkout.

| Source | Retained guidance or bounded observation |
| --- | --- |
| [CONTRIBUTING.md](../../../CONTRIBUTING.md) | Fresh worktrees use locked environments and reviewed setup; fast/full checks and explicit knowledge mappings preserve evidence scope and fail rather than hide missing coverage. |
| [reviews/astral-python-auto/python-coverage.md](../../../reviews/astral-python-auto/python-coverage.md) | The shared static gate covers maintained Python and quoted heredocs without executing extracted bodies; malformed-input behavior needs regressions alongside type narrowing. |
| [reviews/astral-python-auto/independent-review.md](../../../reviews/astral-python-auto/independent-review.md) | Read-only d36bb88 source review checked provenance, routing and maintained Python coverage; coordinator test results and native observations remain separately identified evidence. |
| [reviews/evidence-led-improvements/README.md](../../../reviews/evidence-led-improvements/README.md) | Content-keyed per-validation heading caching preserves fresh bounded reads and path validation; performance observations and clean-worktree guidance do not justify speculative cleanup. |
| [reviews/release-030-browser-harness.md](../../../reviews/release-030-browser-harness.md) | Startup cleanup and process/pipe lifecycle defects were reproduced, while the initiating Linux Target.getTargets timeout remained unexplained; retain that distinction. |
