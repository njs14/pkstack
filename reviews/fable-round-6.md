# Fable 5.1 review — round 6

## Execution metadata

- Candidate: `b5084487c8bca35f4809f5e6e2f3f00001e2db2f`, tree
  `5194fc14fe49163ed093e1263a4532091377f12d`
- Reviewer: Claude Code 2.1.258, canonical `claude-fable-5-1`, requested effort `xhigh`
- Session: `9d783c44-f104-4e16-9f13-4f8bbd13ad58`
- Isolation: chmod-read-only Git archive; tools limited to `Read`, `Glob`, and `Grep`
- Prompt SHA-256: `2412a7dd25d8d39a811ec120941b2d722e9a357f3b53e4332e08e8afe78e1dca`
- Owner-only envelope SHA-256:
  `49309aa1802a21da2786bdbc4513f99f58309ad9ff5bc57cc3cbc18c0be12f97`
- Extracted report SHA-256:
  `2c23846d65542d8b5663687b39679f5d1aabbb8cb310c8dc210165320a01eae8`
- Observed work: 891.740 seconds, 208 turns, 41,982 Fable thinking tokens, 71,654
  Fable output tokens, zero web requests, and reported cost about $24.23
- Verdict: `REQUEST CHANGES`; `MATERIAL_UNRESOLVED: 4`

The provider envelope also reports the expected bounded Haiku companion: 917 input tokens, 16
output tokens, and no thinking or web requests. The substantive review model was canonical Fable
5.1. Effort is caller-bound because the result envelope has no independent effort field.

## Material findings and disposition

- `FBL-047` — Candidate-writable nested reviewer-memory files could be auto-loaded during the
  mandatory Fable gate. **Remediation:** protect the reviewer-instruction basenames and hidden
  configuration components everywhere, mirror them into Kiro's deny matrix, pass empty
  `--setting-sources`, and add boundary regressions.
- `FBL-048` — The newest native Kiro campaign lacked the previous campaign's raw evidence chain.
  **Remediation:** bind the Kiro-owned session JSON, 244-line message stream, per-launch log,
  exact input history, bounded action trace, and ambient memory-hook disclosure. Preserve the
  honest absence of a `script(1)` typescript and PID sidecar.
- `FBL-037` — The first 27-path maintenance transition retained only a summary while its older
  attempt data had been overwritten. **Remediation:** bind transition 0's identities, inventory,
  path count, A/B/C counts, and dispositions digest; retract rather than reconstruct the missing
  attempt details. The later campaign remains the executable fail-then-pass proof.
- `FBL-049` — No hosted candidate has reached Fable and merge because no accepted Fable Actions
  secret is configured. **External prerequisite:** provision exactly one of
  `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY`, then run the authenticated lifecycle. Local
  Claude credentials are never transferred.

Fable also reported seven low-severity polish items. They are retained in the owner-only raw
report but are not release blockers for this bounded candidate.

## Decision

Round 6 is not an acceptance verdict. The locally actionable material items above require a new
exact-commit review. The hosted credential remains a fail-closed external activation prerequisite.

`MATERIAL_UNRESOLVED: 4`
