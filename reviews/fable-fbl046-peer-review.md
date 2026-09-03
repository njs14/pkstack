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

The remediation was implemented after this reviewed checkpoint. The `f6e3440` candidate carried
67 passing guard tests; that remains candidate evidence only until a fresh immutable Fable pass is
appended to this record.

## Remediation re-review attempts

The remediation target for both attempted re-reviews was immutable commit
`f6e3440c6a6c6faab1030501baa3c193535207e1`, tree
`f8f28bc5142e6ac67c06dfe0f7a60a9b9fdb752d`, with parent
`347d461a097f5d26e084f10958641fc4aa70ce07`. Its deterministic `git archive` SHA-256 was
`9c9ac3fe3dd48b71edbaf0055423a469e0de1ad9475e102b2597a68df76dfbaf`. Neither attempt is
admissible focused Fable acceptance evidence.

### Attempt 1 — rejected mixed-model report

The first snapshot was `/private/tmp/pk-stack-fable-fbl046r1-snapshot.lmA09s`; owner-only
controls remain in `/private/tmp/pk-stack-fable-fbl046r1-controls.ZBGxZp`. Claude Code 2.1.258
started with canonical `claude-fable-5-1` at caller-requested `xhigh` and used only 22 `Read` and
19 `Grep` calls. MCP, plugins, skills, slash commands, browser, shell, writes, web search,
subagents, and permission denials were absent.

After 44 Fable assistant events, a provider `model_refusal_fallback` in category `cyber` changed
the active model from `claude-fable-5-1` to `claude-opus-4-8`. The final 13 assistant events and
the report were therefore authored by Opus 4.8. Provider usage also recorded a 19-output-token
internal Haiku 4.5 companion, 7,052 Fable output tokens, 22,738 internal Opus 5 output tokens, and
5,852 Opus 4.8 output tokens. The run itself ended successfully with `end_turn`, but no identity
can repair the missing Fable-only final report. Although the rejected report ended with
`CLEAN_FOR_NEXT_STEP` and `MATERIAL_UNRESOLVED: 0`, that text is inadmissible as a Fable
acceptance verdict.

| Artifact | SHA-256 |
| --- | --- |
| External review contract | `0030cf3a4129e380e23e069ec5f5ff41dd9c585b78d14154da613cb313b4b137` |
| Invocation | `b90f23969d0c3bbd0ce3c91de7169b5bd60acdda5608de92fc0853a6b8a5bf66` |
| Mixed-model envelope | `250b9d471be73fcdae961d47d1ef5d6604fa4a9883304dd10581dc6ebba81d33` |
| Rejected mixed-model report | `15171b9ece9eed7759f24c8acf1fcb6921d85d8d1231e09fa1decda4f671a910` |
| Empty stderr | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

The rejected report supplied no material counterexample. Its three actionable LOW
defense-in-depth observations were implemented in the next local worktree state: the
YAML-indirection name model matched its stated contract; whole-`secrets`-context confinement became
self-contained in the structural scanner; and the scanner itself carried the exact execution-order
values rather than relying only on its companion pin test. That intermediate state passed 69 of 69
direct guard tests, `py_compile`, Ruff, actionlint, and diff checks without changing the production
workflow. It is retained as intermediate evidence rather than the current unnamed candidate. The
fourth LOW observation—that evidence committed in the child names its reviewed parent
tree—requires no new control; the existing evidence already discloses that historical
relationship.

### Attempt 2 — incomplete Fable-only run

The second snapshot was `/private/tmp/pk-stack-fable-fbl046r1-retry-snapshot.dPPJay`; owner-only
controls remain in `/private/tmp/pk-stack-fable-fbl046r1-retry-controls.9pPObb`. Claude Code
2.1.258 again started with canonical `claude-fable-5-1` at caller-requested `xhigh`. Its 25
substantive assistant events all named Fable, with one synthetic terminal-error event and a
14-output-token internal Haiku 4.5 companion; Fable produced 2,551 output tokens before the cap.
It used only 12 `Read`, three `Glob`, and two `Grep` calls, with no Opus use, MCP, plugins, skills,
slash commands, browser, shell, writes, web search, subagents, or permission denials.

This attempt exhausted the five-hour session window and ended with `stop_reason: stop_sequence`,
`terminal_reason: api_error`, and `is_error: true`; the service reported `You've hit your session
limit · resets 10:10am (America/New_York)` with reset epoch `1788444600`. It produced no report
and no verdict lines. Its Fable-only partial events therefore carry no acceptance value.

| Artifact | SHA-256 |
| --- | --- |
| External review contract | `0a086743b8fb9c5b76ad08e83f6b8e6c99cc249c5550148d4f21b95e4d109f60` |
| Invocation | `73398d8c5e043909b4e321e738adfa3c4ec251e950f65a8feb0c49e947ca6cbb` |
| Incomplete Fable envelope | `8e60fd3f60f3eb41b39e11ccbb2abfb40f5bdf9b398d5b9ee4630eb212c46900` |
| Empty stderr | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

## Parent conformance finding and remediation

### FBL-046-R2-C1 — HIGH — YAML quote decoding can synthesize a secret expression

Source: Codex read-only conformance review of the parent worktree after the rejected Fable
attempts. This is an independently reproduced implementation finding, not a Fable verdict.

Two actionlint-valid workflow mutations were false accepts before the fix:

- YAML double-quoted `"\u0024{{ toJSON(se\u0063rets) }}"` decodes to
  `${{ toJSON(secrets) }}`.
- YAML single-quoted `'${{ ''}}'' && toJSON(secrets) }}'` decodes to
  `${{ '}}' && toJSON(secrets) }}`.

The former raw scanner accepted both source forms because YAML scalar decoding changed the token
stream after its quote masking and expression extraction. Acceptance therefore required a
no-general-loader control that rejects scalar token-changing escape forms, retains exact
actionlint-valid reproductions as regressions, and still permits inert occurrences in comments,
plain scalars, and block scalars.

Disposition: **implemented locally on the current unnamed candidate; immutable Fable review
pending**. A stateful non-block YAML quote prepass now rejects double-quoted backslash escapes and
single-quoted doubled-quote escapes, including forms continued across lines. Codex independently
replayed both exact counterexamples and observed both rejects. The direct guard suite passes 70 of 70
tests; `py_compile`, Ruff, actionlint, and diff checks pass; and the production workflow remains
unchanged. No commit or tree is claimed for this current candidate yet.

An attempted post-fix auxiliary re-review was classifier-blocked. It produced no verdict and has
no focused or final acceptance value; it is not approval.

Focused Fable acceptance remains pending. Final 24-area release acceptance remains false and is
not implied by the original review, either rejected re-review attempt, or the locally implemented
post-hardening defenses, Codex conformance review, or classifier-blocked auxiliary attempt.
