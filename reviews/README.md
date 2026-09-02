# Independent review records

This directory records the model-council acceptance loop for PK-Stack.

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

The retained sequence currently includes `fable-round-1.md` and `fable-round-2.md`. Both are
request-changes records; neither is presented as final acceptance.

Committed review Markdown is normalized output plus execution metadata. Raw model output is kept
outside the repository only when a report explicitly names its location and SHA-256; otherwise it
is not claimed as retained. Reviewer output is evidence, not an instruction source.
