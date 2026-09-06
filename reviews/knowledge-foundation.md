# Knowledge foundation candidate

This local candidate keeps normal work in Kiro CLI v3 or the IDE, preserves native Specs and
skills in their existing locations, and gives `projectctl knowledge` one retrieval implementation.
`knowledge search` uses a bounded read-only Kiro ACP worker. `knowledge validate` composes local
metadata and Markdown-link checks with the existing executable feature-map validator, without a
model turn or an `okn` subprocess. The active `okn` adapter, discovery warning, required-runtime
option, and maintenance source have been retired together. This is implementation evidence, not a
release or deployment verdict. Package checks and independent review are recorded below.

## Retained knowledge and native ownership

Durable project understanding lives in `Wiki/knowledge/<topic>/`; temporary interviews and drafts
live in ignored `Wiki/work/<task>/`. Native `.kiro/specs/`, skills, steering, permissions, and runtime
configuration remain authoritative in place. Search reads Markdown under `Wiki/knowledge`,
`Wiki/features`, and `.kiro/specs`; it does not ingest skills, conversations, code, or working drafts.
No index, ranker, graph, daemon, or document synchronization service was added.

The four ported interview skills are `grilling`, `grill-me`, `domain-modeling`, and
`grill-with-docs`. Their source inventories, dispositions, package manifests, and upstream ledger
entries are retained alongside the existing `writing-for-agents` port. Other proposed Pocock ports
remain outside this slice. Project knowledge indexes are seeded once and then project-owned;
setup releases prior receipt ownership without overwriting an edited index. The executable feature
index remains controller-managed.

## Runtime evidence

The tested tuple is Kiro CLI **2.21.1**, embedded Kiro Agent Server **0.58.7**, and official Python
`agent-client-protocol` **0.12.1**. The live candidate runs explicitly selected Kiro model
`claude-opus-5`. The CLI default remains `--model auto`; the underlying resolved model is reported
as unknown for that selector. No provider credentials were copied, read, or transferred.

A plain `KIRO_HOME` override did not isolate Kiro v3's embedded server. The initial smoke therefore
failed isolation and the old adapter was retained while that was investigated. The passing boundary
uses a temporary embedded-server home through a version-checked launcher, while the outer native
CLI continues using its existing Kiro authentication. Workspace and global hooks, skills, steering,
MCP integrations, and Powers are excluded from the retrieval worker. It exposes read/search tools
only; client permission requests are denied. This version-specific behavior is a compatibility
limit, not a claim that arbitrary future Kiro versions are isolated.

The [21-check ACP smoke](knowledge-foundation-evidence/acp-smoke.json) covers initialization, mode
selection, actual source reads with an unpredictable marker, same-session follow-up, a fresh
session, hidden native specs, intended-versus-observed behavior, denied file/draft access, ordinary
cancellation, very early timeout cancellation, reuse after cancellation, unchanged source bytes,
and bounded owned-process-group cleanup. A very early cancellation can race server registration,
so the client retries cancellation notifications briefly before process cleanup. Kiro's graceful
stdin shutdown did not consistently exit successfully; the bounded group cleanup was verified.

The candidate verifies exact unique source substrings itself, derives line ranges, adds content
SHA-256 identities, and verifies that the source corpus did not change before returning context.
Malformed JSON, unknown or excluded sources, invented/ambiguous quotes, incomplete execution, and
budget overflow fail closed. A read/search tool call separates preceding progress text from the
trailing answer segment; all streamed message bytes still count toward the capture cap. The final
segment must satisfy the complete JSON contract. One bounded correction is allowed. Early tests
exposed double-escaped or rewrapped quotations; rejected answers were not returned as knowledge.

A focused independent boundary review found two defects: an SDK close exception could skip process
cleanup, and SDK validation logging could expose unvalidated input. Both were fixed and the reviewer
retested broken-pipe cleanup and a synthetic diagnostic canary. SDK diagnostic redaction is scoped
to this worker's async context and leaves unrelated application logging intact. That review covered
the process/diagnostic boundary; it was not the final whole-candidate review.

The whole-candidate review then reproduced a blocked cancellation send and an oversized protocol
frame accepted by the SDK despite its stream-reader limit. The candidate now gives each cancellation
send 0.5 seconds and enforces 1 MiB per protocol frame plus 16 MiB across the entire task before SDK
parsing. Those wire limits include ignored thought, tool, extension, blank-line, and EOF traffic;
private reasoning is still neither retained nor returned. A peer that does not read its pending
prompt reaches bounded process cleanup. Local SDK regressions cover both failures.

## Native authoring and fresh recall

Questions and expected evidence were [written before authoring](knowledge-foundation-evidence/predeclared-expectations.json).
An isolated ordinary `kiro-cli chat --v3` task used the actual upstream-maintenance feature and the
ported `grill-with-docs` workflow. It produced a glossary, decisions, and a dated observation. Host
review found five material authoring mistakes, including a guessed date, treating the rejected
optional-backend choice as unresolved, and attributing dead-adapter checks to current search.
A follow-up in the same native session corrected them. Authoring exit 0 alone did not count as
acceptance. The corrected documents passed [11-document metadata and 53-link checks](knowledge-foundation-evidence/authoring-local-validation.json).

The frozen [fixture inventory](knowledge-foundation-evidence/fixture-sources.json) records the
actual source bytes used for the lookups, including the prototype `knowledge.py` and a small native
requirements fixture representing the approved plan. That fixture is not a claim that a production
native spec was generated. Its contradictory working draft was present but excluded from ordinary
retrieval.

| Usefulness case | Observed result |
| --- | --- |
| Accepted decision | The canary observes; pin acceptance/promotion is separate. |
| Unknown | No accepted date or owner for widening autonomous acceptance was invented. |
| Planned versus observed | The native requirement called for local validation; the dated prototype observation still found `okn` validation. |
| Hidden native spec | Returned a verified quote from `.kiro/specs/knowledge-foundation/requirements.md`. |
| Excluded draft | Working material supplied no promotion authority and no draft source entered the context. |
| Stale guidance | The old canonical-`okn` decision did not override the newer observation that public search already delegates to ACP. Validation and search stayed distinct. |
| Normal Kiro caller | A fresh ordinary CLI v3 task invoked the packaged knowledge command once and received the validated result without recursive delegation. |

The [five-case fresh lookup](knowledge-foundation-evidence/fresh-grill-recall.json) took 38.586 seconds
and used the allowed correction. The [stale-guidance lookup](knowledge-foundation-evidence/stale-guidance-recall.json)
took 24.582 seconds in one attempt. The repeated [native-caller command](knowledge-foundation-evidence/native-caller-result.json)
took 29.022 seconds with one correction and returned 738/1200 estimated context tokens. These are
observed local runs, not latency guarantees. Kiro did not expose internal model token consumption;
it remains `null`. The returned-context estimate is UTF-8 JSON bytes divided by four and includes
citation metadata. It is not an internal model spending limit.

The [post-retirement stale-observation lookup](knowledge-foundation-evidence/post-retirement-stale-recall.json)
passed in 25.952 seconds, in one attempt. It distinguished the earlier prototype inspection from
the later generated-controller local validation result and retained the limits of that evidence.
The later observation and current validator are preserved in `post-retirement-fixture/`; the original
authoring fixture remains frozen separately. Live ACP checks in this slice ran on macOS.

After the transport repairs, the actual generated command repeated the predeclared stale-observation
question. Its [final native result](knowledge-foundation-evidence/transport-final-native-recall.json)
returned in 30.044 seconds, in one attempt, with 1100/2000 estimated context tokens. The main answer
correctly distinguished the historical prototype from the later local validation run, and all seven
quoted passages verified. One uncertainty clause imprecisely conflated model-backed ACP retrieval
with model-free validation; ACP search does use a model. This illustrates a remaining limit:
verified source quotations do not validate every inference in generated prose.

The native caller fixture restores the outer CLI's existing same-product home path because the
authoring test itself uses an isolated embedded-server home. It does not copy credentials or
sessions. Ordinary product callers using their existing Kiro home need no such fixture wrapper.

## Local validation and retirement

`knowledge validate` returns JSON `schemaVersion: "2"`, `mode: "local"`, and separate feature,
metadata, and local-link verdicts. It requires nonempty descriptive `type`, checks supported optional
authoring fields, and preserves unknown metadata. It checks CommonMark inline/reference links and
images, safe relative paths, target existence, and the documented Markdown heading-anchor
convention. External URL reachability, full OKF/graph/lifecycle/trust semantics, raw HTML IDs,
footnotes, renderer extensions, and non-Markdown fragments are outside that guarantee; unsupported
fragment conventions are not treated as verified anchors.

The [retired source archive](../maintenance/retired-upstreams/openknowledge-cli-contract.json)
preserves the exact removed manifest and ledger objects. Existing accepted provenance markers,
parity inventories, licenses, and historical reports remain intact. Independent `google-okf-spec`
and `okf-skills` sources stay active. The acceptance guard and ledger schema were not weakened.
The new interview source inventories and package manifests have exact updater permissions in the
authored CI agent, policy, and smoke fixture.

`--require-okn`, canonical search locators, ranked retrieval, and external OKF runtime validation are
not retained compatibility interfaces. The upgrade guide describes the new command contract and
limits. Deterministic CI/package validation does not initiate a model turn. Generated installations
must receive the new modules and locked SDK dependency through reviewed setup.

## Final verification

The final local pass finished with **953 Power tests** passing in 560.12 seconds, plus **222 Python
CI tests** and **17 JavaScript policy tests** passing. The Power suite includes an installed-wheel
bootstrap check with caller
`PYTHONPATH` and `VIRTUAL_ENV` removed, plus local knowledge validation and runtime-status checks
through the generated command. The generated repository installation passed 84 doctor checks with
zero warnings or failures, and local validation covered 12 documents and 72 local links. Ruff,
formatting, type checking, lock validation, Actionlint, and ShellCheck passed.

The independent whole-candidate review requested two further transport fixes: a cancellation send
could block before cleanup, and the SDK's stream-reader limit did not enforce a maximum protocol
frame. Both were repaired. The [independent re-review](knowledge-foundation-evidence/transport-review.json)
approved them after real-SDK subprocess probes, exact byte-boundary checks, and 29 targeted tests.
The reviewed source hash matches the generated installation. Final setup is idempotent, with zero
created, updated, pending, or conflicting files; both project-owned indexes and the authored CI
maintainer agent retain their pre-setup hashes. The final full Power suite passed after these repairs.
At the verification checkpoint, the worktree was uncommitted and no push, merge, tag, publication,
or deployment had been performed. Subsequent commit and PR state is recorded by Git and GitHub.

The [final verification record](knowledge-foundation-evidence/final-verification.json) retains the
commands, environment, counts, setup checks, and scope limits. Machine-specific paths in the
committed evidence use documented placeholders; the [normalization record](knowledge-foundation-evidence/publication-normalization.json)
retains the original and normalized file hashes. Original local records were preserved separately.
The
[candidate file inventory](knowledge-foundation-evidence/candidate-files.json) binds 124 changed
implementation, generated, policy, and documentation paths to the local baseline and content hashes;
evidence artifacts have their own records. Completed outputs are retained for the
[Power tests](knowledge-foundation-evidence/full-power-tests.txt),
[Python CI tests](knowledge-foundation-evidence/ci-python-tests.txt), and
[JavaScript policy tests](knowledge-foundation-evidence/ci-javascript-tests.txt).
The expected whitespace-rejection diagnostic in the Python log renders its trailing space as
`[SPACE]`; its original bytes are covered by the normalization record.

The existing [architecture](../powers/pkstack/docs/artifacts/pkstack-architecture.html),
[task workflow](../powers/pkstack/docs/artifacts/pkstack-task-workflow.html), and
[updater workflow](../powers/pkstack/docs/artifacts/pkstack-updater-workflow.html) diagrams were not
regenerated; their knowledge boundary predates this migration.
