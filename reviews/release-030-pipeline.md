# PKStack 0.3.0 pipeline audit

Inspected 2026-09-05 from base `3d4583a16fe2caca497d8b8fe7d5c860a12c1a2f`.
This records the pipeline investigation, reviewed repairs, merged-control
verification, and bounded live campaign. Desktop acceptance remains separate.

## Rejected candidate #32

[PR #32](https://github.com/njs14/pkstack/pull/32) is closed and unmerged. Its source
run [33968727837](https://github.com/njs14/pkstack/actions/runs/33968727837) began
2026-09-05T13:22:49Z. The exact candidate was
`ffe61777302f12812894ee38b5c80aaddeacb3bf`, based on
`f53f0931ef3a6748242d2dd569fe0cef0ddb2106`.

Candidate gate [33969018679](https://github.com/njs14/pkstack/actions/runs/33969018679)
reported success because rejection handling succeeded: resolve, both test jobs,
peer review, durable feedback publication, and exact-candidate closure passed;
merge was skipped. Cleanup closed the PR at 13:34:33Z after recording feedback.
This is correct handling of the received rejection, not approval of the candidate
or proof that the reviewer findings were accurate.

Both recorded findings are unsupported by the full candidate:

- The reviewer swapped the identities of the two changed backfill records. The
  exact candidate's `backfill/SKILL.md` pinned blob is
  `951e8a6f38ec90a59e70c2fee5864da5d395fe72` (10,577 bytes); the helper
  `backfill/scripts/okf_backfill_events.py` pinned blob is
  `5f63458991555ef4cd51bef7068ad1daf5358de3` (21,302 bytes). GitHub's upstream tree
  API for declared pinned commit `85db7fd0a8a66d07d984ac6c5f4fbb5063d00357`
  independently returns those exact path/blob/size tuples. The default short
  patch hunks omitted the record paths, making the supplied review context
  ambiguous. The inventory itself used the correct pinned baselines.
- `retrieved_on: 2026-09-05` is consistent with the new inventory's same-day
  retrieval. Requiring the date to change for a second retrieval that day is
  incorrect. No provenance or inventory change was justified by this finding.

The original rejection remains in the feedback history. This audit does not
rewrite reviewer history or reopen/merge the rejected PR.

## Repairs

- Internal review bundles use schema v3. The existing patch stays unchanged;
  `source_inventory` adds full source identity/date and complete changed records
  from the exact base/head JSON inventories, keyed by upstream path. Unchanged
  records are omitted. The inventory and skill context share the existing combined 64 KiB cap,
  with deterministic order,
  strict JSON input, and the existing bundle digest/commit binding. The consumer
  rejects old schemas, malformed context, unrelated or duplicate paths, and
  oversized context. Oversized context stops review instead of being clipped.
- The immutable reviewer contract directs the reviewer to those complete
  records, recognizes repeated retrievals on the same UTC date, and prohibits
  inventing omitted context.
- Candidate and base gates now execute the full Python policy suite and Node
  PR-policy suite and validate version/knowledge. The existing independent
  trusted-snapshot regressions remain in the candidate gate. Candidate tests
  still have no write token or Kiro key; the no-tool credential-bearing reviewer
  runs in a separate job against trusted controls and hash-bound data. Merge
  retains its exact base/head and reviewer attestation checks.
- Release publication extracts the exact version's reviewed `CHANGELOG.md` body
  into `--notes-file`, replacing the generic archive placeholder. Missing,
  duplicated, empty, or invalid version entries fail before publication. The
  heading suffix can remain `Unreleased` while preparing the candidate; the
  heading itself is not included in release notes. No tag or release was made.

## Verification

Executed locally with `/opt/homebrew/bin` on PATH:

```sh
python3 -B -m unittest discover -s .github/scripts -p 'test_*.py'
node --test .github/scripts/test_pkstack_pr_policy.js
actionlint .github/workflows/*.yml
shellcheck .github/scripts/*.sh
git diff --check
```

Results: 184 Python tests and 17 Node tests passed; Actionlint, ShellCheck, and
whitespace checks passed. New regression coverage reproduces omitted upstream
paths in short hunks, verifies correct complete record attribution and same-day
retrieval data, rejects tampered/oversized context, and verifies exact release
notes selection. Combined-cap regressions reject both producer and consumer
contexts that exceed the shared budget even when each section fits separately.
Release-note relative links bind to immutable repository blob URLs at the tagged
commit. During implementation, a fixture initially omitted Git-tree
mode/type fields and did not recreate the actual hunk ambiguity; it was corrected
rather than weakening the assertion. An existing workflow assertion caught
removal of the original trusted-snapshot test invocation; that invocation was
retained alongside the broader suite.

The current archive commands already fix the subtree archive timestamp and use
`gzip --no-name`. Two independent builds of the inspected base Power produced:

- Commit: `3d4583a16fe2caca497d8b8fe7d5c860a12c1a2f`.
- SHA-256: `4e6914c5ee75bbbd6566186f0ae3f69e767375f190b54aace0f31de15047ab6b`.
- 360 archive entries, all under `pkstack/`; manifest version `0.3.0`; no virtual
  environment or bytecode artifacts.

This establishes that the archive recipe is reproducible for the inspected
base. Packaging code was not changed.

The reviewed head `67b7e3631e8aecf79653321addbff24a8bc319db` and merged main
`3859f635e36b26d813802445cceb037cc26d0dfc` were each independently packaged twice
and installed into fresh consumers. The main archive is 4,478,207 bytes with
368 entries and SHA-256
`4d4a2bf4dfcc8c9aa32e13345be4348f7024fb9244a30ea1511716fd51cca09f`.
Both builds match. Version, contents, setup/idempotence, doctor, feature,
canonical `okn`, and a stored two-attempt failure/pass goal passed from the
extracted archive, preserving the test hash. This was a controller smoke with a
known implementation repair, not an additional native Kiro session.

## Executed bounded live campaign

The GitHub workflow API reported the existing maintenance workflow as `active`.
The schedule remains `17 13 * * *`. [PR #33](https://github.com/njs14/pkstack/pull/33)
merged only after exact-head CI `33976733214` passed. Main CI `33976929179` then
passed on `3859f635e36b26d813802445cceb037cc26d0dfc`.

One manual source run,
[33977108073](https://github.com/njs14/pkstack/actions/runs/33977108073), was
dispatched on that main commit without `retry_source`. The detector re-proved
all seven sources, found only OKF-skills drift, and selected
`d8393f329c97836980566c1cf4e4aa4fe47dc111` with one retained rejection and no retry
override. The initial failing goal was stored; repair 1 and secretless
verification 1 passed, and repairs 2–4 were skipped. The source workflow completed
and created [PR #34](https://github.com/njs14/pkstack/pull/34) at
`27fb0dec5ca538e6f3bb03ef1eb11499ca744f5f`.

The exact candidate workflow,
[33977500077](https://github.com/njs14/pkstack/actions/runs/33977500077), finished
with failure. Candidate tests passed (868 Power passed, one skipped); the base
job passed 867 Power tests with one skip and one failure. Both passed 184 Python
policy and 17 Node policy tests. The base failure was the first browser startup
CDP command in `test_archify_reader_layout_and_exports`:
`Target.getTargets: timed out after 15000ms`, on Node 22.23.2. It occurred before
navigation, geometry checks, or exports. The unchanged focused test subsequently
passed locally; the initiating timeout has not been isolated.

The independent no-tool Opus verdict approved the exact candidate with no
material findings. It correctly attributed the two full changed path records
and accepted the valid same-day retrieval date. A separate read-only reviewer
re-proved those identities against both complete upstream Git trees, recomputed
the bundle and attestation hashes, and checked the sanitized report and trusted
no-tool validator result. The combined context is 2,583 bytes; bundle digest
`226e9e6e4531184edff3e5efb98f1a6a4ae1891ce73d3e391f09ef5852dc501c` and report hash
`5ec67d26ee4583afea83b37071e63ae1efcde0a7b87de8b2a847b046b081b2be` bind that
observed approval. The prior false-context finding did not recur.

This was not an accepted update: the failed base gate blocked merge despite
approval, rejection feedback was skipped, and cleanup closed PR #34 unmerged at
2026-09-05T16:25:38Z. Main stayed `3859f635e36b26d813802445cceb037cc26d0dfc`.
No failed-job retry, review override, schedule change, or permission widening
occurred. Investigation identified a separate, definite startup-rejection
cleanup gap in the test harness; its repair must not be presented as proof of the
initiating timeout's cause. Any later accepted update requires final tests,
review, notes, and archive evidence bound to the resulting main commit.

The subsequent [browser-harness repair](release-030-browser-harness.md) moves
startup under existing cleanup ownership. Its injected failure regression fails
before the repair and passes afterward. The complete local follow-up passed
870 Power, 184 Python policy, and 17 Node policy tests, plus lint, formatting,
types, lockfile, workflow checks, doctor, feature validation, and canonical
`okn`. No timeout, layout threshold, or existing assertion was relaxed. Exact
patched-commit Linux CI and fresh campaigns are recorded below.

## Cleanup follow-up and second source campaign

[PR #35](https://github.com/njs14/pkstack/pull/35) merged the independently
approved harness repair at `9c3e6309076075010ab1d8dd9018f74aeba7348f` as main
`a1c0c9ad0f88963fb46cea6c9339ae55272922ee`. Exact PR CI `33978687069` and main CI
`33978845082` both passed on Ubuntu. This verifies the patched harness in those
runs; it does not establish the initiating cause of the earlier CDP timeout.

A fresh bounded source run,
[33979038750](https://github.com/njs14/pkstack/actions/runs/33979038750), used
that new main commit without a retry override. It failed before candidate
publication. Verification 1 failed at `accept-preview` with exit 2 and successful
cleanup; its detailed initiating error was not retained. Preparation for repair
2 then failed with `okf-skills-provenance.md:31: new blank line at EOF.` The
exact-title candidate workflow `33979242122` was entirely skipped. No candidate
package, PR, isolated browser test, or independent verdict was produced.

The guard runs pending-marker cleanup before its staged whitespace check. The
cleanup removes only the pending marker line, which can expose its preceding
paragraph separator as a new trailing blank line. A real Git/prepare-attempt
regression reproduced that refusal: the staged diff was whitespace-clean before
cleanup and failed afterward with the same EOF diagnostic. The narrow repair
removes only empty separator lines exposed when the deleted pending marker was
the final nonempty content. It preserves authored prose, accepted markers, and
prose after the marker; unrelated trailing spaces still fail the unchanged
staged guard. No write boundary, permission, or final validation was relaxed.

The three focused retry/integrity cases passed, including duplicate and altered
accepted-marker rejection. The complete local policy suite passed 185 Python
tests and 17 Node tests; Actionlint, ShellCheck, and whitespace checks passed.
The Power subtree is unchanged from the independently reviewed cleanup commit
whose 870 local Power tests and exact Ubuntu CI passed. Evidence is retained in
`provenance-eof-cleanup-before.log`, `provenance-eof-cleanup-after.log`, and
`post-provenance-root-tests.log` under the campaign evidence directory.

This proves the reproduced trusted cleanup defect and its repair. It does not
reconstruct the unavailable live candidate's initiating accept-preview error or
declare the failed second campaign accepted. Patched-commit review, CI, and the
fresh bounded campaign are recorded below.

## Reviewed retry repair and third campaign

[PR #36](https://github.com/njs14/pkstack/pull/36) merged the retry repair at
`e94c357502969e9d3e7fc9845855d2179ca78ecd` as main
`753363480954998dd383a42ded41d97d72657a08`. Independent security review approved
that exact five-file delta and independently ran all three focused cases. Exact
PR CI `33979933200` and main CI `33980155633` passed. The Power subtree,
workflows, and CI reviewer authority were unchanged by the retry repair.

The third fresh source run,
[33980370382](https://github.com/njs14/pkstack/actions/runs/33980370382), is bound
to that new main commit and used the existing bounded controls without a retry
override. Its initial goal failed, repair 1 and secretless verification 1 passed,
and repairs 2–4 were skipped. The stored goal passed at attempt 2 of 5. The source
run succeeded and opened [PR #37](https://github.com/njs14/pkstack/pull/37) at
`277b2ee5aff153c01632955060dae215d7fa4531`.

Exact candidate gate
[33980726626](https://github.com/njs14/pkstack/actions/runs/33980726626) succeeded.
Both isolated base and candidate jobs passed 185 Python policy tests, 17 Node
tests, and 869 Power tests with one skip because Kiro CLI was unavailable on the
test runner. The actual browser/render/export test passed in both jobs. The
independent Kiro-hosted Opus report approved with no material findings, correct
complete source-record identities, and valid same-day retrieval semantics.

Automatic exact-SHA merge succeeded at 2026-09-05T17:27:55Z, producing main
`23b34a7df75fcabd8998f174002aa175aecf0ad3`. The merge parent is `7533634` and its
tree `0e08295d1ea309a221a1b76fa478362dbf25c4cc` exactly matches the reviewed
candidate. Rejection and failure-cleanup jobs were skipped. A separate read-only
reviewer independently checked package identities, source Git trees, review
context, report binding, and the final merge. The earlier failed campaigns
remain unmodified and are not carried forward as acceptance of this run.

On the accepted main commit, authenticated `upstream check` and
`feature verify pkstack-upstream-maintenance` both passed. All seven configured
sources validated, no semantic drift was selected, and generated parity passed.
No ordinary push CI run was created for this automated merge; its exact tree is
covered by the isolated candidate gates. The final report PR and resulting main
require their own ordinary CI before the local handoff binds the final archive.
The updater remains active on its existing daily schedule.


## CI reduction and exact-main artifact promotion

PR #40 (`666396f`, merged as `832aa8d`) replaces serial ordinary CI with ten
execution lanes and a required aggregate. Fixed report paths receive a report-only
PR profile; unknown/mixed paths keep normal coverage. Every selected test has one
bound result, and missing, duplicate, cancelled or unexpected skipped results fail.
An actual deliberately failing test in draft PR #39 failed core shard 4; all other
execution lanes finished, evidence was retained, and aggregation refused the run.
PR #39 was closed unmerged. The actual infrastructure candidate passed all 12 jobs
in run 33985933815, followed by successful main run 33986118130.

The updater now builds and validates its trusted review bundle before candidate
tests and model review run concurrently. Base tests remain independent. Merge and
cleanup wait for all branches; review rejection counts retain their earlier
eligibility when candidate tests also fail. These changes passed independent
security review and focused workflow tests. The new overlap has not yet been
observed on a live updater candidate; campaign 3 remains the live acceptance record.

Main CI builds twice from the exact commit, installs the archive, and validates a
stored failure/repair/pass with an unchanged verifier. The promotion verifier
requires the exact successful main push run/current attempt, all mandatory jobs,
immutable artifact ID, API ZIP digest, inner hashes, matching notes and source/check
identities. It rechecks private-repository, current-main and tag authority before
publication. A read-only pre-tag verification of main 832aa8d passed and explicitly
returned non-publication-eligible evidence because no tag was created.

A source-updater merge without a push-main CI artifact remains ineligible for
release promotion. There is no fallback to candidate artifacts, tree-equivalent
commits or a rebuild during publication. The final report commit's main workflow
will produce the release artifact bound in the local handoff.
