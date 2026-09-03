# Fable reviewer-readiness peer loop

This record covers a focused Fable 5.1 peer review of PK-Stack's hosted-maintenance
reviewer-readiness boundary. It is not the final 24-area release review and does not accept a
release candidate.

## Reviewed checkpoint

- Commit: `347d461a097f5d26e084f10958641fc4aa70ce07`
- Tree: `78e5b4e3c1f934486ce2e24707c8ecbbdae7b92a`
- Parent: `dfbcfa82b37401e673b8441b25f1569a8fed51d4`
- Read-only snapshot: `/private/tmp/pk-stack-fable-fbl046-snapshot.c1nXvb`
- Snapshot archive SHA-256:
  `d9c874e95c8e1782caa3e3243463a532bdc402e520da7940cb4c6294715961a3`
- Reviewer: Claude Code 2.1.258, canonical model `claude-fable-5-1`, caller-requested effort
  `xhigh`
- Tools: `Read`, `Glob`, and `Grep`; MCP, browser, shell, writes, slash commands, persistence,
  web search, and subagents disabled

The caller retained the invocation, control prompt, raw envelope, normalized projection, raw
report, and reproduced counterexample outside the candidate:

| Artifact | SHA-256 |
| --- | --- |
| Invocation | `f81c9c6c1abb1f3c7f76c1750150228786501aa3c332643f197f4705f7ac4086` |
| External review contract | `5ad131d4ab5804cdf82b601152ff3a8eb6ada65a201ef456f02951310e4d8162` |
| Raw report | `ada1a37a8313d8c62f89a85e74669a2fd4b550702b6bc0bf6ef5bbd8e2e379da` |
| Raw envelope | `31c0d462194ae83ed9cae2f527250607222948551599661e687fa94b87855175` |
| Validated envelope projection | `50690e8799caa2e052c3e81f721e96b6e593e68cac76deacdeb80168fc149b88` |
| Counterexample patch | `69b99581daecdbd7c06243733acb5ad3c06a9eb9d8fd3e5d0c779e11eec86c5a` |
| Counterexample validation | `8d99ffdfb5256a8515898340060ea6d440e074ce5fc34f728411365928e05252` |

All 47 substantive assistant events named `claude-fable-5-1`. The provider also reported a
19-output-token internal `claude-haiku-4-5-20251001` companion that produced no review message.
The run ended successfully with `end_turn`, used only 15 `Read` and 16 `Grep` calls, emitted no
stderr, and had no MCP, plugin, skill, web, subagent, permission-denial, or write activity. The raw
report carried one harmless progress sentence before its required heading; the verdict and finding
below are normalized rather than treated as executable input.

## Peer verdict

```text
PREFLIGHT_VERDICT: REMEDIATE_FIRST
MATERIAL_UNRESOLVED: 1
```

Fable closed the execution-order portion of `FBL-046`: `maintain` explicitly requires
`reviewer_readiness` success, and no valid path was found that lets a Kiro credential-bearing step
run after readiness fails, is skipped, is cancelled, or does not run.

## Material finding and acceptance task

### FBL-046-R1 — MEDIUM — YAML alias can multiply a Kiro secret scope

GitHub Actions supports YAML anchors and aliases, including reuse of an environment mapping that
contains a secret. Anchoring repair 1's `env` mapping and assigning `env: *kiro_env` to another
step produced five effective `KIRO_API_KEY` scopes while the checkpoint's 64 text-oriented guard
tests still passed. An equivalent whole-step anchor and list-item alias has the same risk. The
finding does not reopen readiness execution ordering, but it invalidates the exact four-scope
confinement claim.

Acceptance task:

1. Reject YAML anchors, aliases, merge keys, and explicit mapping-key forms in this trust-root
   workflow while allowing those tokens when inert inside quoted text, comments, or block scalars.
2. Require bare environment mappings for protected steps and exact bytes for each credential
   mapping.
3. Close the property set of all five jobs and enumerate the exact step names/property sets in
   `reviewer_readiness`, `maintain`, and `publish`.
4. Assert that only the four named repair steps can contain `KIRO_API_KEY`.
5. Retain valid env-map and whole-step alias counterexamples that the former guard accepted and the
   hardened guard rejects.
6. Re-run the complete guard, actionlint, JSON consistency, and a fresh Fable 5.1 `xhigh` review
   against the immutable remediation commit.

GitHub's [workflow-reuse documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations)
shows the same secret-bearing `env` anchor/alias pattern, and the
[GitHub Actions changelog](https://github.blog/changelog/2025-09-18-actions-yaml-anchors-and-non-public-workflow-templates/)
states that anchors and aliases are enabled for all repositories.

## Evidence and limitations

Fable found the hosted fail-closed record, archive-versus-payload sizes, absent-credential output,
bootstrap receipt, and status language internally consistent. It did not verify GitHub run facts,
download artifacts, or cryptographic hashes because the peer was intentionally read-only and had
no shell or network. This review does not prove a valid hosted Fable credential, a successful Kiro
repair, candidate publication, Fable candidate review, exact-SHA merge, cron cadence, native Spec
campaign, or final model-council acceptance.

The remediation was implemented after this reviewed checkpoint. Its passing local tests are
candidate evidence only until a fresh immutable Fable pass is appended to this record.
