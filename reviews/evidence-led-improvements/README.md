# PKStack improvement campaign — September 6, 2026

The candidate reduces repeated Markdown parsing while retaining fresh bounded
reads and path validation. It also removes duplicate ignore rules and documents
fresh-checkout/worktree verification. No public CLI, JSON, state, permission,
model-selection, or release interface changes.

Baseline: `9c57301c9d7c1be5a6b32a66001f4325ee379a49`.
Implementation tested: `8889057c351e823bc952946b28fe441caafa8f2d`.
This report and its evidence files are added after that implementation commit.

## Findings and disposition

| Area | Finding | Disposition |
| --- | --- | --- |
| Workspace | The task started in an older repository. | Created a clean clone of current `njs14/pkstack` in the canonical `pkstack` folder. App project selection remains manual because Computer Use denied access to Codex. Older checkouts and worktrees are preserved. |
| Code cleanup | Root ignore rules repeated the generated runtime block. | Removed six redundant lines; every ignore pattern remains present. |
| Wrapper/test audit | Small helpers generally encapsulate containment, serialization, diagnostics, or test seams. | Retained these helpers and existing tests; no speculative deletion or coverage reduction. |
| Performance | Each repeated Markdown fragment target was reparsed despite identical freshly read content. | Added a per-validation, eight-entry LRU for heading parsing keyed by text. Every link still performs containment, existence, bounded-read, and decoding checks. Nothing is cached between validation calls. |
| Agent setup | Contributor instructions did not describe setup/refresh and generated-runtime parity in fresh worktrees. | Added a reviewed-preview workflow, idempotence checks, and benchmark instructions to the existing contributor guide. Reused the shared check driver. |
| PRs/issues | No open PRs or issues at inspection. | No closure or merge candidate manufactured. |
| Stalled work | Nine retained non-main remote branches refer to closed or merged work. | Inspected PR intent/history; no current acceptance failure established that warrants taking over a branch. |
| Controlled delivery | User selected gated delivery. | Local commits and this review package only. No push, new PR, merge, closure, branch deletion, workflow change, or release. |

The wrapper pass inspected single-return helpers across first-party runtime and
repository Python scripts. In particular, discovery containment wrappers,
bounded feature reads, strict JSON decoding, and redirect/proxy controls are
intentional boundaries. This is a conservative audit, not a claim that every
line is optimal or that no defects remain.

## Performance evidence

Measured on macOS arm64 with Python 3.12.14 and the locked Power environment.
One warm-up followed by seven measurements per fixture, with identical outputs
required throughout. All samples are retained in [benchmark.json](benchmark.json).

| Fixture | Result | Before median | After median | Improvement |
| --- | --- | ---: | ---: | ---: |
| Repository Wiki | 12 documents, 72 local links, no issues | 25.05 ms | 22.18 ms | 11.5% less time |
| Shared Markdown target | 20 documents, 1,600 local links, no issues | 3.151 s | 0.262 s | 91.7% less time; 12.0× faster |

The small real-Wiki result and the larger synthetic result are separate claims.
Neither is a production latency guarantee. The new
[benchmark script](../../powers/pkstack/benchmarks/knowledge_links.py) performs no
network access and imposes no wall-clock CI threshold.

[Runtime profiles](runtime-profiles.json) also examined bootstrap preview and
doctor. Bootstrap preview spent most time reading/validating assets; doctor
spent about 4.0 of 4.1 profiled seconds waiting for subprocess checks. These
single profiled runs overlapped test activity and are diagnostic attribution,
not controlled before/after benchmarks. No integrity checks were removed and
no concurrency was added to doctor.

## Verification

- The repeated-target regression failed on the baseline: two heading parses
  instead of one. After implementation, all 20 local-link/metadata tests passed.
- Tests confirm fresh reads for repeated links and detection of target edits
  within a validation and across subsequent validations.
- Locked setup preview identified exactly one expected managed source update;
  reviewed refresh updated it and its receipt. Repeated setup produced zero
  created/updated files, conflicts, stale paths, or pending updates.
- A separate fresh worktree at the tested implementation commit passed locked
  environment setup, setup preview, repeated setup, doctor, feature validation,
  and local knowledge validation. Doctor reported 84 passes, zero warnings,
  zero failures. The worktree stayed clean. See [fresh-worktree.json](fresh-worktree.json).
- Ruff (including the benchmark), formatting, and the Power-scoped type check
  passed. The corrected fast profile passed 22 tests.

The complete shared run exited zero on the tested implementation commit:
955 Power tests across all required partitions, 222 repository Python tests,
and 17 Node policy tests passed. Browser and isolated wheel/bootstrap tests
passed. Policy checks also passed actionlint, shellcheck, lock validation,
Ruff, formatting, type checks, and generated-controller feature/knowledge
validation. No test partitions were omitted or duplicated. The
[execution plan](checks-plan.json) binds the commit and configuration; the
[aggregate summary](checks-summary.json) records the collection digest and
lane timings. The sum of lane durations was about 239 seconds.

Commands are documented in [CONTRIBUTING.md](../../CONTRIBUTING.md). The complete
check command for this candidate is:

```sh
uv run --frozen --project powers/pkstack python -B .github/scripts/pkstack_checks.py local full
```

Failures retained in the chronology: an initial benchmark fixture needed its
temporary root resolved on macOS; this was fixed before baseline measurements.
An ad hoc type-check invocation from repository root selected the wrong scope
and produced 190 diagnostics; the documented Power-scoped check passed. The
first full run caught retired-name wording introduced in the contributor guide.
That run was interrupted, the wording was corrected without changing the test,
the fast profile passed, and a fresh complete run was started on `8889057`.

## Branch triage and review boundary

[Branch details](branch-triage.json) retain inspected commit identities and PR
states. The updater branches map to closed PRs #21, #23, #25, #27, #32, #34 and
merged PRs #29, #37. The latest merged reconciliation uses the same upstream
identities as the last closed attempt. Remaining branch divergence alone is
not evidence of unfinished work.

The other branch, `codex/pkstack-ci-failure-proof`, contains a deliberately
failing test. Its [closed PR #39](https://github.com/njs14/pkstack/pull/39)
explicitly identifies it as an unmergeable CI refusal demonstration. It remains
untouched. The upstream maintenance workflow was observed `active` and is
unchanged by this campaign.

This work has local verification, not new hosted CI or an independent reviewer
verdict. Native checks were exercised on macOS; no new Linux retrieval or IDE
acceptance claim is made. Adding/selecting the canonical folder in the app is
still required; the current task was not silently rebound to a different project.

## Proposed PR

**Title:** Reduce repeated knowledge-link parsing and document fresh-worktree checks

**Description:** Knowledge validation reparsed a shared Markdown target for every
fragment link. Reuse heading parsing within a validation when freshly read text
is identical, retaining all bounded reads and path checks. The representative
shared-target benchmark improves from 3.151 s to 0.262 s; the repository Wiki
improves from 25.05 ms to 22.18 ms, with unchanged results. Also document fresh
worktree setup/managed refresh and remove duplicate ignore rules.

Validation: repeated-target and edit-detection regressions, reproducible benchmark
samples, fresh-worktree setup/idempotence, doctor and local validators, and the
retained shared-check results. This is a proposed description only; no PR has
been opened. Approval is still required before publication or merging.
