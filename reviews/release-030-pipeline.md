# PKStack 0.3.0 pipeline audit

Inspected 2026-09-05 from base `3d4583a16fe2caca497d8b8fe7d5c860a12c1a2f`.
This records the pipeline investigation and local repairs. A fresh campaign on
merged controls and final-candidate archive verification remain acceptance gates.

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
base. It does not substitute for rebuilding and installing the final frozen
release candidate. Packaging code was not changed.

## Bounded live campaign handoff

The GitHub workflow API reported the existing maintenance workflow as `active`.
The schedule remains `17 13 * * *`. No live updater dispatch was performed by
this audit.

After reviewed fixes are merged and main's CI passes, invoke exactly one existing
manual source run:

```sh
gh workflow run pk-stack-upstream-maintenance-kiro.yml --repo njs14/pkstack --ref main
```

Do not pass `retry_source` for this campaign: the retained source currently has
one rejection, below the three-rejection stop. The immutable controller chooses
one eligible source and one candidate, with five verifier attempts (one baseline
failure plus at most four repair invocations). The maintenance job is bounded
by 150 minutes; the isolated independent review job by 45 minutes, with its model
invocation bounded at 30 minutes. Use existing repository Kiro authentication.

Bind the observed source run to the merged main SHA, then locate the candidate
workflow by its exact source-run title and identities. Follow it to terminal
base/candidate tests, valid no-tool Opus verdict, and merge or durable rejection
plus closure. Inspect each material rejection against the exact bundle before
calling it a valid negative result. Do not repeatedly dispatch, weaken the
review gate, manually override a rejection, purchase capacity, or change the
schedule. If an accepted update advances main, rebind final release tests,
independent review, notes, and archive evidence to the resulting main commit.
