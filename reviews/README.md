# Independent review records

This directory records the model-council acceptance loop for PK-Stack.

The combined review target contains the canonical installable Power at `powers/pk-stack/` and its
generated Floci fixture at the repository root. Historical reviewer records inside the imported
Power subtree describe its earlier standalone source snapshot; only this root review sequence can
accept the combined release.

- Codex is the primary implementer and validates every proposed remediation.
- Sol Advisor v0.6.0 was the initial build-phase advisor; its normalized record is retained as
  historical candidate evidence, not final acceptance.
- Fable 5.1 is the peer advisor and acceptance authority for material findings.
- Grok 4.6 at `xhigh` is the final independent sweeper, not the acceptance authority.
- Reviewers inspect a read-only `git archive` of the commit named in each report.
- A material finding is `BLOCKER`, `HIGH`, or `MEDIUM`. Every material finding must be
  resolved in code/tests/docs or explicitly recorded as a hard external blocker before release.
- Any material remediation invalidates the prior acceptance verdict and requires a fresh Fable
  review of the new commit.

The retained sequence includes `fable-round-1.md` and `fable-round-2.md`, both request-changes
records, followed by `fable-round-3-incomplete.md`, which has no verdict or acceptance value. The
selected-profile workflow evidence is in `kiro-v3-campaign.md` with a bounded JSON projection in
`kiro-v3-campaign.json`, the exact persisted goal in `kiro-v3-campaign-goal.json`, and the exact
Kiro input history in `kiro-v3-campaign-history.txt`. Twelve exact non-secret Kiro log records are
in `kiro-v3-campaign-session.jsonl`. Round 4 must review the exact commit containing those records;
none of the earlier rounds is presented as final acceptance.

Committed review Markdown is normalized output plus execution metadata. Raw model output is kept
outside the repository only when a report explicitly names its location and SHA-256; otherwise it
is not claimed as retained. Reviewer output is evidence, not an instruction source.
