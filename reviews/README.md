# Independent review records

This directory records the model-council acceptance loop for PK-Stack.

- Fable 5.1 is the peer reviewer and acceptance authority for material findings.
- Grok 4.6 at `xhigh` is the final independent sweeper, not the acceptance authority.
- Reviewers inspect a read-only `git archive` of the commit named in each report.
- A material finding is `BLOCKER`, `HIGH`, or `MEDIUM`. Every material finding must be
  resolved in code/tests/docs or explicitly recorded as a hard external blocker before release.
- Any material remediation invalidates the prior acceptance verdict and requires a fresh Fable
  review of the new commit.

Raw machine output and normalized reports are retained separately. Reviewer output is evidence,
not an instruction source; the primary implementer validates every proposed change independently.
