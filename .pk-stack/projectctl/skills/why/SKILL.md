---
name: why
description: Explain why a system or decision exists using code, tests, history, and documentation while separating direct evidence from plausible inference.
---

# Explain why it is this way

Treat the request text that activated this skill as the design decision or behavior whose rationale
should be recovered.

Investigate motivation, tradeoffs, and historical constraints. Use `how` for
runtime mechanics. Code shows what exists; code shape alone does not establish
author intent.

Read [`references/evidence-contract.md`](references/evidence-contract.md)
before delegating.

## Anchor the investigation

1. State the exact question and target files, line ranges, and symbols.
2. Explain the current mechanics briefly so evidence searches use the right
   vocabulary.
3. Inspect project history and code: blame, file history through renames,
   commits, pull requests, tests, and comments that name a constraint.
4. Extract linked issue IDs, document names, incident IDs, error fingerprints,
   metrics, flags, and analytics events as search seeds.

Before broad retrieval, inspect the matching feature record and follow its explicit related links.
When rationale remains unresolved, record that escalation reason and issue one bounded, targeted
`.pk-stack/bin/projectctl knowledge search "<specific rationale>" --budget 1200 --output json` query.
Verify every returned section against its content-addressed source and current implementation; do
not inject the whole Wiki.

## Discover and cover the source categories

Inventory the read-only tools and sources currently available. Build a coverage
ledger for every category before choosing a narrative:

1. **Project history and code:** commits, pull requests, reviews, blame, tests,
   and reason-bearing comments.
2. **Issues and tickets:** product need, customer constraint, compliance,
   deadline, and scope changes.
3. **Long-form documents:** specifications, decision records, design docs,
   meeting notes, and postmortems.
4. **Project team chat:** real-time deliberation and incident discussion that
   never reached a durable document.
5. **Infrastructure observability:** metrics, monitors, logs, traces, and
   runtime incidents.
6. **Error tracking:** exceptions, stack traces, releases, first-seen and
   last-seen evidence.
7. **Product analytics:** events, experiments, feature flags, usage
   distributions, migrations, and warehouse evidence.
Apply **incident and postmortem evidence** as a cross-cutting lens when the
target is defensive or reliability-related. Search timelines, triggering
conditions, mitigations, and action items inside every relevant category; this
lens is not a separate connector and must not duplicate those investigations.

For each category, record `checked`, `checked-empty`, `unavailable`, or
`not-applicable`. A null result is evidence only when the exact query and scope
are recorded. Mark a category not applicable only when the target has no
possible path to that evidence; otherwise search it or call it unavailable.
Never crawl private transcript stores or unrelated conversations. Search only
project sources the user placed in scope and respect each connector's access
boundary.

PK-Stack's shipped custom-agent profiles set `includeMcpJson: false`. Do not
tell a read-only reviewer to query project MCP servers or external connectors
it cannot access. The primary session may gather external evidence only through
tools actually available on the selected Kiro surface and within the user's
scope, then pass a bounded evidence packet with source locations to reviewers.
If the primary cannot retrieve a category, record it as `unavailable` rather
than implying a connector search occurred.

## Investigate in parallel

For a non-trivial question, have the primary session gather the exact bounded
source packet for each available category. Assign one independent native Kiro
sub-agent to analyze each packet. Give all investigators the same question and
code anchor, then give each only its category evidence and playbook. Run
categories in parallel without sharing conclusions. Reviewers may read
repository files exposed by their profile, but external evidence is passed to
them; they do not fetch it through MCP or connector calls.

Investigators record searches, direct evidence with precise source locations,
indirect evidence and its inference chain, contradictions, empty results,
gaps, and cross-source leads. They do not write files, modify external systems,
or turn the evidence into a story. The current session spot-checks citations,
reconciles conflicts, and owns synthesis.

## Calibrate the answer

Classify every claim:

- **Direct:** a source explicitly states the reason; cite it adjacent to the
  claim.
- **Supported:** several independent sources converge; cite each contribution.
- **Inferred:** indirect evidence supports a likely reading; show the inference
  and hedge it.
- **Speculative:** a plausible hypothesis lacks supporting evidence; label it.
- **Unknown:** the searched record does not answer the question.

Do not use confident causal language for inferred claims. Surface competing
hypotheses and contradictions instead of choosing the tidiest account. Do not
convert historical behavior into a current requirement without present-day
confirmation.

Return: the question and code anchor; direct and supported findings;
inferences; competing hypotheses; concrete unknowns; a source-coverage ledger
with queries, null results, and gaps; an evidence timeline when relevant; and a
confidence summary. If a change will follow, add **Preserve**, **Change**,
**Avoid**, and **Risk** constraints grounded in that evidence.
