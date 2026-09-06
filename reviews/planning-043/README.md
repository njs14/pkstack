# PKStack 0.4.3 planning campaign

**Release blocked.** The candidate implements the shared grilling method and the
[seven CLI audit corrections](../cli-native-command-audit/README.md), but native
CLI acceptance exposed planning and knowledge-capture failures. The automated
checks below do not override those results. Version `0.4.3` is a local, unreleased
candidate; this report establishes no merge, tag, or publication.

This is a preliminary September 6, 2026 campaign record. IDE Plan completed the
bounded scenario after a native implementation repair; an IDE Quick Spec no-write
scenario remains in progress.
The [machine report](campaign.json) records exact hashes, receipt locations,
session identifiers where available, and remaining acceptance gaps.

## Candidate identities

All runs started from repository base
`63e4e2c8a8029c40a2a522931e1feafa0c2e7b53` with uncommitted candidate changes.
Each manifest contains 293 Power-relative file hashes, checked against its
disposable source copy. A gate receipt's base-commit field alone does not identify
those uncommitted bytes.

| Snapshot | Source manifest | Sorted-JSON content SHA-256 |
| --- | --- | --- |
| v1 | [source-files-v1.json](source-files-v1.json) | `73c1cb3f7d065b94210b67421472b22668f27a24d06b146d69bb1683697bb262` |
| v2 | [source-files-v2.json](source-files-v2.json) | `837a42c753492b140cccc12bafbac4525d7ad6309ddbd64cdaab27d263133f4c` |
| v3 | [source-files-v3.json](source-files-v3.json) | `afa9dbf64ebda53ffe26b8dbd8b77034b8d3da92e6a5c681ebd1841b5d7329b1` |

Content digests use Python `json.dumps(manifest, sort_keys=True)` encoded as UTF-8
with default separators and no trailing newline. The machine report also records
the different SHA-256 of each retained manifest file's exact bytes.

## Automated checks

- **Initial v1 full gate:** 963 product pytest tests passed across fast, browser,
  package, and six core lanes. The first policy lane failed because system Python
  3.9 could not import the CI package module, which requires Python 3.11 or newer.
- **Policy rerun:** passed using the supported `uv` environment's Python. It ran
  222 Python policy tests and 17 Node policy tests, plus actionlint, shellcheck,
  lock, lint, format, type, version, feature-validation, and knowledge-validation
  checks. The aggregate summary was produced after this correction. The policy
  tests are separate from the 963 product tests.
- **v2 and v3 focused gates:** each fast lane passed 22 tests with 941 deselected.
  These are targeted reruns after instruction changes, not another full gate.
- **Final v3 installation checks:** the root managed-setup preview reported zero
  creates, updates, conflicts, pending updates, and stale files. All 293 current
  canonical Power files matched v3. The IDE fixture's final doctor and local
  knowledge validation passed. See [final-checks.json](final-checks.json).

The machine report retains the collection digest, lane outcomes, counts, and
hashes for the original log, policy rerun, aggregate summary, and receipts.

## Native CLI findings

Runs used ordinary local Kiro CLI 2.21.1 with the native model display `Auto`.
The resolved model was not established. Inputs are retained in
[planned-inputs.json](planned-inputs.json), and the unchanged README, stub, and
tests are retained with baseline-matching hashes in
[fixture-context.json](fixture-context.json). Final-screen text is in
[terminal-excerpts.json](terminal-excerpts.json).

| Run | Observed result | Verdict |
| --- | --- | --- |
| v1 PKStack → Plan | The router interviewed without the requested native Plan handoff. After explicit `/plan` entry, the planner read `grilling` but offered Unicode acceptance as an alternative to the settled ASCII requirement. | Failed |
| v2 PKStack → Plan | Native Plan read the method, asked only the unresolved wording question, and made no writes before approval. After approval, execution wrote `reference.py` and ran the verifier before attempting knowledge capture; capture stopped at a Power lookup approval. | Failed: capture ordering and completion |
| v3 direct native Plan | The planner read the method and stated that no consequential product questions remained, then asked to confirm the settled normalization order and ASCII rule. | Failed: settled-answer reuse |
| v3 full PKStack route | The session remained `pkstack` instead of handing off to native Plan and asked whether to enforce ASCII. | Failed: handoff and settled-answer reuse |
| v3 explicit-read diagnostic | A same-conversation request to read the router and `grilling` produced `/plan` handoff context, but its final sentence still asked whether to use strict ASCII. | Partial improvement; automatic route still unproved |
| v2 native Spec | Requirements, requirements analysis, design, and tasks completed. Analysis found no issue requiring a change. The runner selected **Not now** at execution handoff. | Passed for this bounded planning-only scenario |
| v3 standalone `/grill-me` | The interview loaded the workspace shared method, settled the wording decision, and closed without Plan, implementation, command execution, or knowledge capture. All 186 inventoried files were unchanged. | Passed for these boundaries only |

The [v2 pre-approval receipt](cli-plan-v2-before-approval.json) reports no changed
or new files while Plan was active. The [v3 file comparison](cli-plan-v3-planning-files.json)
also reports no changes or additions, with product and Wiki unchanged.

The [Spec file comparison](cli-spec-planning-files.json) reports no changed or
deleted baseline file and exactly four additions: native `requirements.md`,
`design.md`, `tasks.md`, and `.config.kiro`. Product and Wiki files were unchanged.
The supervising runner also observed `/spec view reference-normalization` opening
the native Tasks view. This does not establish implementation approval, verifier
binding, successful knowledge capture, or v3 Spec acceptance.

The [standalone interview receipt](cli-interview-v3-files.json) and
[final response](cli-interview-v3-final.json) retain that separate boundary test.
Its first response grouped dependent questions, so this does not establish strict
dependency sequencing. It also claimed distinct messages would "measurably"
reduce correction time without supplying measurements; that claim is not adopted
as evidence.

## IDE Plan result

On IDE 1.0.437 with inherited GPT-5.6 Luna/Low, the supervising runner observed
the v3 PKStack route load `grilling`, produce the native Plan handoff, and ask
only the unresolved wording question. In the same conversation, native Plan read
the shared method and produced a decision-complete plan after the wording choice
without reopening settled questions. The
[before-approval receipt](ide-plan-before-approval.json) reports no changed,
deleted, or added files.

After neutral implementation approval, native execution wrote one knowledge
decision and updated the index before changing product code. The
[capture-order receipt](ide-plan-capture-before-code.json) and
[bounded accessibility excerpts](ide-plan-ax-excerpts.json) retain that checkpoint.
The runner reviewed and accepted the two knowledge edits. Local metadata and link
validation passed before product implementation began.

The first native implementation accepted `ab12ß` as `AB12SS`, violating the
settled ASCII contract. After operator feedback, native execution changed the
validation order. The original three tests and the final heredoc regression
probe passed. Earlier inline probe attempts failed with NameError or quoting/
SyntaxError errors; those failures are retained in the accessibility record.

[Repeated approval](ide-plan-knowledge-after-repeat.json) produced no changed or
new Wiki files and left one decision document. The
[final file comparison](ide-plan-final-files.json) changed only `reference.py`
and the knowledge index, added one decision document, and preserved the tests.
This passes the bounded IDE Plan/capture/idempotence scenario after repair; it
does not clear the CLI failures or establish every planning route.

## Remaining gates and evidence limits

CLI Plan behavior still needs a passing final-snapshot rerun. A fresh IDE Quick
Spec scenario is testing an explicit no-product/no-Wiki-write instruction while
allowing native planning documents, including after planning approval. An independent
final review and release checks remain required after a candidate passes native
acceptance.

An independent diagnostic review, as reported by the supervising runner, found
no stale-copy, schema, or naming defect that justified another source repair.
That assessment does not turn the observed native failures into a passing
candidate. CLI used unresolved `Auto`, while IDE used Luna/Low; these runs do not
isolate model selection from client or harness behavior.

Raw terminals, complete gate receipts, and disposable source/project copies remain
under `/tmp/pkstack-planning-043-n6nwikes`. They are **local ephemeral evidence**,
not committed artifacts. The report retains source manifests, compact file-change
receipts, and terminal excerpts instead of large raw recordings. Excerpts render
only each final 160×48 terminal screen; they are not complete transcripts. Raw
hashes identify bytes observed at the recorded time, and active recordings may
grow. Missing final session identifiers or IDE results remain explicit in the
machine report.
