# Pipeline repair and release readiness

Recorded September 5, 2026 UTC. The [identity cleanup, PR #18](https://github.com/njs14/pkstack/pull/18)
merged as `a6bcdb8f64a0765494d55140825af42a2d53eb25` after final CI passed.
[PR #19](https://github.com/njs14/pkstack/pull/19) merged the pipeline repairs as
`d81af3280b948f8d69faa6f132473c723f49ca47` after its final CI passed.

## Proposal contract

The previous live maintenance run stopped at proposal validation without
retaining the inner reason. Its exact cause remains unproven. Code inspection
did identify a real prompt defect: it referred to `drift_count` in raw detector
JSON, which has no such field. The validated controller plan supplies the
selected action; `reconcile-source` now unambiguously requires one proposal.

The guard and secretless verifier now publish fixed, allowlisted reason codes
for missing/invalid proposals, detector failures, source binding, dispositions,
and provenance markers. Private retry feedback retains the reason. Candidate
text and arbitrary exception messages are not promoted into public diagnostics.
This adds diagnostics, not a bypass: rejected input still fails, invokes cleanup,
and records `passed=false`.

Real guard-CLI and `jq` tests cover a coherent proposal and 17 rejection cases,
including duplicate JSON keys, parser-depth and oversized-integer limits, wrong
identities, missing dispositions, and missing/noncanonical markers. Real shell
wrapper tests cover failure propagation and allowlisted publication.

## Reviewed runtime refresh

The [live canary](https://github.com/njs14/pkstack/actions/runs/33942828872)
correctly failed when stable Kiro moved from the reviewed 2.21.0 pin to 2.21.1.
It downloaded the advertised archive, validated all six renamed agent profiles,
and proved workspace discovery. It withheld authenticated model inventory
because the pin did not match; that run is not a passing acceptance result.

The [official stable manifest](https://prod.download.cli.kiro.dev/stable/latest/manifest.json)
and an independent local archive download confirmed:

```text
version: 2.21.1
target: x86_64-unknown-linux-gnu, headless, tar.xz
archive bytes: 536509056
archive SHA-256: 7fc0564fd02295a64470c4bf52752f5475f3280be3fa4dd9db255162e07e9825
kirocli/bin/kiro-cli bytes: 113925216
kirocli/bin/kiro-cli-chat bytes: 838626440
```

```sh
curl --proto '=https' --tlsv1.2 --fail --location \
  --output kirocli-2.21.1.tar.xz \
  https://prod.download.cli.kiro.dev/stable/2.21.1/kirocli-x86_64-linux.tar.xz
shasum -a 256 kirocli-2.21.1.tar.xz
tar -tvJf kirocli-2.21.1.tar.xz kirocli/bin/kiro-cli kirocli/bin/kiro-cli-chat
```

All active download URLs, hashes, cache keys, version checks, archive sizes,
and exact executable-size limits changed together. General size limits,
permissions, model IDs, and effort policy did not change. Historical 2.21.0
fixtures and the credential stream validator remain intact.

No separate 2.21.1 release notes were found in the
[official changelog feed](https://kiro.dev/changelog/feed.atom); this is a
manifest/runtime-verified promotion, not a claim about undocumented fixes.
Fresh model/index observations were reviewed without changing the methodology:

```text
https://kiro.dev/llms.txt
SHA-256 c6dc1c473e6250eace1bb28a1d327fbe8b71a38f8eb6ffafb79bf0f1bdc84f69

https://kiro.dev/docs/models/available-models.md
SHA-256 91bc22bb071d8f39f35df5071da398de27bf33ed7f6ec3c79a52a602253a0de7
```

These observations append evidence; they do not rewrite earlier source snapshots.

## Deterministic and independent checks

```sh
python3 -B -m unittest discover -s .github/scripts -p 'test_*.py'
node --test .github/scripts/test_pkstack_pr_policy.js
actionlint .github/workflows/*.yml
shellcheck .github/scripts/*.sh
git diff --check
```

After the proposal and pin fixes: **141 Python policy tests and 17 Node tests passed**.
After adding safe permission-preview diagnostics: **143 Python tests passed**.
After the denied-preview compatibility fix: **144 Python tests passed**.
With both preview stages and their presence summaries covered: **145 passed**.
Final implementation [CI](https://github.com/njs14/pkstack/actions/runs/33944611100)
at `439d816` passed **146 repository Python tests, 17 Node tests, and
826 Power tests with one skipped**, plus lint, formatting, types, lockfile,
Actionlint, and ShellCheck. Fourteen local branding/release-metadata tests
also passed after the documentation-status cleanup.
Actionlint, ShellCheck, and diff checks passed. Independent read-only reviews
approved the final proposal-repair delta and the separate runtime-pin delta.
The reviewer independently checked the downloaded archive's size and digest.
Full package tests, lint, formatting, types, and lockfile gates run in PR CI;
the Power runtime itself is unchanged from the 827-test identity candidate.

## Release packaging dry run

A local package built with `HEAD` at
`cc7ea9b2050a3c2bd0d8817651e730e98d196829`:

```sh
git archive --format=tar --prefix=pkstack/ --output pkstack-v0.3.0.tar HEAD:powers/pkstack
gzip --no-name --stdout pkstack-v0.3.0.tar > pkstack-v0.3.0.tar.gz
shasum -a 256 pkstack-v0.3.0.tar.gz
```

The archive SHA-256 was
`a1f277a18c3b3654f74979b43e4fda051a55b29c0c96c7f614c1e39a70414bce`.
All ten expected manifest, README, mascot, banner, and six skill entries were
present among 350 entries; no `.venv`, `__pycache__`, or `.git` entries were
included. This proves local packaging only. The tag-driven release workflow
has not run, and no release was created.

The same packaging check passed again on merged commit `d81af3280b948f8d69faa6f132473c723f49ca47`.
Its updated Power archive SHA-256 is
`ac5c363bab7bea7af3887858e5bfd215a137c53e32155d0633a2191f272b2010`;
the 350-entry inventory and required-file/cache checks also passed.

## Live gate ledger

| Gate | Exact scope | Result |
| --- | --- | --- |
| Identity PR CI | `217685ec66140523c2637b26616beeef58c54672` | [Passed](https://github.com/njs14/pkstack/actions/runs/33942690853) |
| Prior-pin credential smoke | Renamed repository, Kiro 2.21.0 | [Passed](https://github.com/njs14/pkstack/actions/runs/33942827063) |
| Prior-pin permission smoke | Renamed repository, Kiro 2.21.0 | [Passed](https://github.com/njs14/pkstack/actions/runs/33942828031) |
| First stable canary | Official 2.21.1 versus old 2.21.0 pin | [Failed closed on pin drift](https://github.com/njs14/pkstack/actions/runs/33942828872) |
| Pipeline implementation CI | `cc7ea9b2050a3c2bd0d8817651e730e98d196829` | [Passed](https://github.com/njs14/pkstack/actions/runs/33943085490) |
| 2.21.1 credential smoke | `cc7ea9b2050a3c2bd0d8817651e730e98d196829` | [Passed](https://github.com/njs14/pkstack/actions/runs/33943105390) |
| 2.21.1 permission smoke | `cc7ea9b2050a3c2bd0d8817651e730e98d196829` | [Failed stream-preview contract validation](https://github.com/njs14/pkstack/actions/runs/33943106362) |
| Permission diagnostic rerun | `6e39a19`, unchanged acceptance predicate | [Confirmed omitted `originalContent`](https://github.com/njs14/pkstack/actions/runs/33943659119) |
| Start-preview compatibility rerun | `7df46d3` | [Start passed; terminal preview mismatch](https://github.com/njs14/pkstack/actions/runs/33943940381) |
| Full-preview compatibility rerun | `8015689` | [Policy denial passed; diff original mismatch](https://github.com/njs14/pkstack/actions/runs/33944226318) |
| Final 2.21.1 permission smoke | `439d816` | [Passed all allowed operations and six denied paths](https://github.com/njs14/pkstack/actions/runs/33944622193) |
| Final PR #19 CI | `eee8898` | [Passed](https://github.com/njs14/pkstack/actions/runs/33944941658) |
| Updated stable canary | Merged `d81af328` controls | [Passed](https://github.com/njs14/pkstack/actions/runs/33945088250) |
| First re-enabled upstream campaign | Merged `d81af328` controls | [Failed proposal/marker checks; no candidate published](https://github.com/njs14/pkstack/actions/runs/33945088358) |

The 2.21.1 permission smoke passed its allowed-write case and the following
protected-file integrity checks. The first deny case then failed in the stream
validator with `Kiro write start preview is invalid`. The failure means the
observed event did not satisfy the validator's expected preview contract; it
does not establish a permission bypass or a successful denial. Later deny
cases were not validated.

The diagnostic-only rerun established the mismatch: the denied start preview
contains exactly the expected `file` and `modifiedContent`, but omits
`originalContent`. The diagnostic publishes only fixed field names, type/path
enums, and booleans, bounded to 4 KiB. Negative tests and independent review
confirmed that it neither prints untrusted values nor changes acceptance.
The corrected contract permits that omission while still requiring an
exact baseline if the field is present. Terminal policy-denial binding and
post-call filesystem integrity checks remain required.

The next run passed the start check but exposed the companion terminal-preview
check. The final fix covers both stages: an original may be omitted, but if
present must be the exact protected baseline at start and exactly empty at
termination. The successful stream summary reports only two presence booleans
to establish the live format without retaining model output.

Independent read-only review approved both compatibility changes. Complete
synthetic denied lifecycles cover all four presence combinations across six
protected resources. Historical previews and rejection of malformed originals,
extra keys, and wrong paths/content remain covered. Allowed-write validation
did not change.

The remaining mismatch was the diff's `oldText`. A disposable local Kiro
2.21.1 session, using existing OAuth authentication and Luna / Low, established
the complete wire shape: both previews omit `originalContent`, and the denied
diff uses `oldText: null`. The actual captured stream passed the corrected full
validator: 27 events, exactly one user tool call, and the protected baseline
unchanged. This cost 0.003987049651741294 credits. The local run had no
`KIRO_API_KEY`, so its API-key leak scan was not applicable; CI authentication
and isolation still require the Linux campaign.

```sh
kiro-cli chat --v3 --agent pkstack-permission-fixture \
  --model gpt-5.6-luna --effort low --no-interactive \
  --trust-tools=fs_read,fs_write,grep --output-format stream-json \
  'Attempt exactly one Write File operation: replace .github/protected.txt with exact UTF-8 content BLOCKED followed by one newline. Do not perform any other operation, do not retry after denial, and emit no prose.'
```

The final diff validator accepts null or historical empty originals only for
denied writes. Allowed writes remain exact-empty. Twelve focused test methods
cover 48 complete valid combinations and malformed-preview/diff rejection;
independent review approved the final change. Live summaries expose only
presence booleans and the fixed `unknown`/`empty` original-content enum.

The final Linux run passed in 4m40s: one allowed campaign (read, grep, and seven
writes), six isolated denied writes, exact matched-rule provenance, every
protected-file checksum, exact file/directory inventories, and cleanup. All six
denials reported both preview originals absent and a null diff original. This
establishes the observed 2.21.1 Linux format and the complete tested boundary.
Its seven validated turn summaries total 0.7500153854726368 credits. This is
the successful campaign only, not a total for earlier failed probes.

The existing Kiro secret is the only model-provider credential used by these
workflows. No key values or session state were copied between products.
Local rename validation reported 0.04 credits across its two Luna/Low turns;
the account snapshot changed from 294.49 to 294.55 of 1,000. Pipeline credit
consumption is not yet attributed by a separate before/after account snapshot.

The merged canary confirmed the 2.21.1 pin, all six agent schemas and workspace
discovery, authenticated model inventory without a model turn, and cleanup.
Eleven recorded documentation hashes matched; `models/available-models.md` and
`llms.txt` differed from historical snapshots. The reviewed fresh observations
above retain those changes without inventing their semantic impact. IDE and
Crew feed versions are observations, not new IDE/Crew end-to-end tests.

After explicit owner approval, the autonomous updater was re-enabled following
the repair merge on September 5, 2026. GitHub reported workflow `349041529` as
`active`; its existing daily 13:17 UTC schedule is unchanged. The first manual
acceptance run uses the same main-branch workflow, bounds, Kiro credential,
and peer-review gate as that cadence. It failed after four attempts: attempts
one and two reported `proposal-missing`; three and four reported
`proposal-marker-missing`. All four reported cleanup exit 0. No candidate was
published, no peer-review turn ran, and no tag or release was created.

```sh
gh pr merge 19 --repo njs14/pkstack --squash \
  --match-head-commit eee8898a045d33e671c6e735997e82871c29cf1c
gh workflow enable pk-stack-upstream-maintenance-kiro.yml --repo njs14/pkstack
gh workflow run pk-stack-upstream-maintenance-kiro.yml --repo njs14/pkstack --ref main
gh workflow run pk-stack-kiro-runtime-canary.yml --repo njs14/pkstack --ref main
```

## Global-agent loading defect

A local Kiro CLI 2.21.1 / Luna / Low discovery probe reproduced a configuration
mismatch. `kiro-cli agent list` listed the trusted `pkstack-maintainer` profile
under an isolated `KIRO_HOME`. In the same environment, v3 chat reported
`agent "pkstack-maintainer" not found, using "default"`. Every direct mode event
selected `vibe`; the requested agent was absent from the advertised choices.
The probe workspace had no `.kiro` directory.

```sh
KIRO_HOME="$probe_root/kiro-home" kiro-cli agent list
KIRO_HOME="$probe_root/kiro-home" kiro-cli chat --v3 \
  --agent pkstack-maintainer --model gpt-5.6-luna --effort low \
  --no-interactive --trust-tools= --output-format stream-json \
  'This is a discovery-only probe with no maintenance requested. Do not use tools, edit files, or write a proposal. Reply exactly GLOBAL_AGENT_OK.'
```

The production preparer used the same split between `KIRO_HOME` and
`HOME/.kiro`; its runner accepted any nonempty JSON-object stream, even `{}`.
That explains how fallback could go undetected. Production raw streams were
deleted as designed, so they cannot establish the earlier runs' selected agent.
The passing runtime canary tested workspace agents, not this global layout.

After reproducing the defect, the updater was temporarily disabled with
`gh workflow disable pk-stack-upstream-maintenance-kiro.yml --repo njs14/pkstack`;
GitHub confirmed `disabled_manually`. Owner approval to re-enable it remains
in effect. The fix uses one isolated `HOME/.kiro` directory for both maintenance
and review, and rejects unbound or fallback maintenance streams.

A second local probe used an isolated `HOME` with the aligned layout. It could
not authenticate without the user's existing home state, so no model turn ran
and it does not prove successful discovery. No credentials were copied. Linux
acceptance must prove the corrected global-agent path using the existing Kiro
workflow secret.

The corrected Power gate passed 828 tests on the Mac, plus Ruff lint and
formatting, `ty check`, and `uv lock --check`. The initial root-directory pytest
invocation incorrectly collected the standalone failing-demo fixture. A later
run lacked Homebrew on `PATH`, causing 16 subprocess failures because `uv` was
not found. Running from `powers/pkstack` with Homebrew and the installed Kiro
CLI on `PATH` passed. These were test-invocation errors, not product changes.

The maintenance stream tests cover direct global identity, session binding,
selection before model/user-tool activity, later fallback, nested or
advertised-only identities, strict JSON, bounded evidence, and secret-safe
errors. The real captured fallback stream returns `maintenance-agent-fallback`.
The shell regression proves `{}` is rejected and private output is cleaned.
Nested-home tests execute preparation and cleanup guards against valid,
symlinked, sibling, traversal, and out-of-runner paths; invalid layouts delete
nothing. Linux live discovery remains the outstanding proof.

The final local repository gate passed 158 Python policy/stream tests and
17 Node policy tests. Actionlint, ShellCheck, and `git diff --check` passed.
A separate read-only reviewer approved the four attestation/runner files with
no material finding; the root agent independently reviewed the nested-home
preparer, workflow bindings, and cleanup changes. These are code and
deterministic-test approvals, not a completed live updater verdict.

GitHub confirmed the repository remains private, uses `main`, and automatically
deletes merged branches. Its branch-protection API returned HTTP 403 with a
GitHub Pro requirement for this private repository. No account plan or privacy
setting was changed. This task checks exact-head CI before merging, and the
autonomous candidate workflow has its own exact-candidate acceptance gate;
neither substitutes for server-enforced protection against an owner's direct push.

## Source-inventory ordering correction

The detector also reported an invalid Matt Pocock source inventory despite no
upstream change. GitHub's complete tree at
`ad2925850efb8973a72d2e666f7a975f9a2d4a9b` confirmed all three recorded objects,
hashes, modes, types, and sizes. Only their array order violated the existing
case-insensitive sort contract. The correction reorders those entries without
changing any source fact, pin, disposition, or history. A regression checks the
canonical order and unique paths in all six manifest-referenced inventories;
it failed before the correction and passed afterward. Independent review
confirmed that the parsed artifact is otherwise unchanged.

## Corrected updater acceptance

[PR #20](https://github.com/njs14/pkstack/pull/20), head
`5e2470cdd9fe7f915f3166be111bb1fbdbdd0b0e`, passed
[CI 33946675881](https://github.com/njs14/pkstack/actions/runs/33946675881):
158 repository tests, 17 Node tests, 827 Power tests with one installed-CLI test
skipped, and all static gates. It merged as
`43e70c868cda60fed9915adde1269c03a2e8470a`; its
[post-merge CI](https://github.com/njs14/pkstack/actions/runs/33946809672)
also passed.

```sh
gh pr merge 20 --repo njs14/pkstack --squash \
  --match-head-commit 5e2470cdd9fe7f915f3166be111bb1fbdbdd0b0e
gh workflow enable pk-stack-upstream-maintenance-kiro.yml --repo njs14/pkstack
gh workflow run pk-stack-upstream-maintenance-kiro.yml --repo njs14/pkstack --ref main
```

GitHub confirmed workflow `349041529` is active again. The
[corrected run 33946810878](https://github.com/njs14/pkstack/actions/runs/33946810878)
uses the merged controls. Its detector found all seven inventories valid and
two genuine upstream drifts: OKF Skills and Archify. Repair one completed
successfully in 72 seconds, including the new direct global-agent attestation.
That proves Linux v3 selected the trusted maintainer from the aligned home.
Secretless verification passed on attempt one with `stage=complete`, exit 0,
and cleanup exit 0. The maintenance workflow succeeded and published
[PR #21](https://github.com/njs14/pkstack/pull/21), head
`e3a14b1192a6c1bdd3843f46a637aae79c07e0f5`. It changed only four source-accounting
files; an independent read-only check found no material semantic or safety
issue and confirmed that backfill remains excluded.

The [candidate gate 33947094756](https://github.com/njs14/pkstack/actions/runs/33947094756)
passed its base tests but failed while constructing the immutable candidate
controls. Its archive command omitted `.github/agent-memory/pkstack-upstream.md`,
which `validate-trusted-snapshot` requires. The guard rejected the missing file
before candidate tests or Opus review. Failed-candidate cleanup succeeded and
closed PR #21 without merging. No review-rejection budget was consumed.

The follow-up restores that required archive input and tests archive coverage
against the existing trusted-prefix contract. It does not change the guard's
acceptance rules. The human-readable OKF catalog also labels its original
commit/tree as baseline evidence and links current identities to the JSON
inventory, so future accepted transitions do not leave a stale current-version
claim in that introduction.

The snapshot correction passed 159 repository policy/stream tests, 135 focused
Power upstream/branding/release-metadata tests, Actionlint, ShellCheck, and
`git diff --check`. The archive-prefix regression failed on the missing file
before the one-line workflow fix, then passed. Full deterministic CI is required
on the repair PR before the next acceptance campaign.
