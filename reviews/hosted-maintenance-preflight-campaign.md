# Hosted maintenance reviewer-readiness campaign

This record preserves the first manual dispatch of PK-Stack's private-repository Kiro maintenance
workflow, whose other trigger is a daily schedule. It is a deliberate fail-closed result, not a
successful maintenance lifecycle: authenticated detection found one bounded upstream transition,
then the workflow stopped before Kiro because no Fable CI credential was configured.

## Immutable target

- Repository: private `njs14/pk-stack`
- Commit: `6e8d4bbe25d549faa5f07378139d92de60294410`
- Tree: `c4360f55963437d70079d7566997e20b047e2a60`
- Kiro maintenance workflow SHA-256:
  `e0c4fd4d097820812f2ff3920f37d599a1ceb110c56a41997c53298859296e41`
- Candidate workflow SHA-256:
  `45141f0ed5338184262413c07865dbee0f343f0cd67da9c3c55a020fb86a7019`
- Maintenance guard SHA-256:
  `bf0b98522b85f6115757b4efe25f8b3620fbfaac62d0a0bbe1820917b444eef1`
- Maintenance policy SHA-256:
  `a2adf480781117499f33cfcbd2a490257ebd370eeeae70a8341de251b426d3b6`

## Hosted result

[GitHub Actions run 33743730700](https://github.com/njs14/pk-stack/actions/runs/33743730700)
ran from `main` on 2026-09-03. `plan` and `detect` passed. The detector used its read-only GitHub
token and uploaded bounded artifact `9888782482`, named
`pk-stack-detector-33743730700`, with a 4,842-byte archive and one-day retention. The
`reviewer_readiness` job then took its absent-credential branch and emitted exactly:

```text
Fable review is mandatory; provision ANTHROPIC_API_KEY or CLAUDE_CODE_OAUTH_TOKEN before spending Kiro credits.
```

Because readiness failed, both `maintain` and `publish` were skipped. No Kiro model turn ran, no
Kiro credit was spent, no candidate branch or PK-Stack maintenance pull request was created, and
the unrelated Dependabot pull requests were untouched. The downstream
[candidate run 33743818713](https://github.com/njs14/pk-stack/actions/runs/33743818713)
was created by `workflow_run` but every job was skipped because the source workflow did not
succeed.

GitHub recorded the exact source-job conclusions as follows:

| Job | Conclusion |
| --- | --- |
| `plan` | `success` |
| `detect` | `success` |
| `reviewer_readiness` | `failure` |
| `maintain` | `skipped` |
| `publish` | `skipped` |

## Detected transition

Exactly one of four configured sources had drift:

- source: `okf-skills` (`scaccogatto/okf-skills`, subtree `skills`);
- prior: commit `bf2448f03686a8348324e4741106697d30a867f9`, subtree
  `8cc9ed3986cf6c942f718439e1ee8249eb17a2ad`;
- current: commit `85db7fd0a8a66d07d984ac6c5f4fbb5063d00357`, subtree
  `2f9170d6937027c2b1c487ef698f0c000bb47745`;
- comparison: complete fast-forward, 28 repository commits, one tracked path, four changed lines;
- path: `backfill/SKILL.md`, with two examples changing `okf-backfill/0.9.2` to `0.9.3`;
- inventory SHA-256:
  `625b339711cc4cdcfaac516f986d895e79ebff074a2da856981c93bcdc4558b9`.

PK-Stack already classifies transcript backfill as excluded. The likely semantic disposition is
therefore B, but this campaign did not advance the pin: that decision remains for the normal
Kiro-author, secretless-finalizer, exact-candidate Fable pipeline after reviewer authentication is
available.

## Boundary and remaining prerequisite

This run proves private-repository manual-dispatch controls, authenticated four-source drift
detection, artifact handoff, and fail-fast reviewer readiness. The committed workflow also contains
the daily schedule, but this dispatch did not exercise it. It does not prove the Kiro repair
invocation, secretless acceptance/finalization, candidate publication, Fable review, or exact-SHA
merge.

The current workflow also requires
`needs.reviewer_readiness.result == 'success'` before `maintain`. That explicit success condition
postdates the immutable hosted target above and has passed local static validation, but it has not
yet run in hosted Actions.

The one external prerequisite is one valid CI-capable Fable credential configured under exactly one
accepted repository-secret name. Readiness checks only presence and exclusivity; validity is proven
later by the candidate's Fable invocation, so an invalid or revoked value would still fail closed
but might do so after Kiro spends repair credits. Local Claude login state is intentionally not
copied into GitHub. Once the credential is provisioned, preserving this natural one-file drift gives
the hosted workflow a real bounded transition to process end to end. A no-drift run would skip
reviewer readiness and therefore would not prove this credential path. This manual dispatch is not
cron-cadence proof.

The downloaded `upstream-check.json` payload was 29,170 bytes with SHA-256
`311bc1cc1e260356dcfde329748be875d623177c73ef00b29606c529e052b3b3`; the GitHub artifact archive
reported 4,842 bytes. A local maintenance-guard replay was reported as passing before the payload
was discarded, but no machine-readable validator result was retained. This record therefore does
not claim durable local validation proof.

The machine-readable companion is
[`hosted-maintenance-preflight-campaign.json`](hosted-maintenance-preflight-campaign.json).
