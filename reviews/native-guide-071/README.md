# Native CLI acceptance for the 0.7.1 patch

September 10, 2026. **Mixed native acceptance; no aggregate pass.** This packet records
successful profile/policy and native command-transition checks, corrected advisory
handoffs, and remaining model-compliance failures. It is not a release approval.

[evidence.json](evidence.json) binds synthetic prompts, observed tool requests, visible
answers, and preservation results to exact source hashes. Raw local transcripts retain
their own hashes; this public packet excludes private native session metadata and
reasoning fields. The [guide feature contract](../../Wiki/features/pkstack-guide.md)
separately checks installation and instruction declarations.

## Method and source identity

- Native `kiro-cli chat --v3 --agent pkstack`, Kiro CLI 2.21.2, embedded KAS 0.58.7,
  unchanged `auto` model selection. The automated cases used `--output-format stream-json`;
  the interactive checks used the terminal UI. ACP was not the working-session entry.
- Every fixture received complete reviewed Power-local setup, preview then apply, including
  consumer profiles, steering, skills, controller, and the orientation hook. The model
  did not perform that setup. Inputs were synthetic; no real application was exercised.
- Temporary native user policy allowed reading and skill disclosure, denied one named
  test file, and left shell/writes requiring approval. Subagents, Powers, MCP, and web
  tools were denied. No blanket trust override, credential copying, global policy change,
  or model-setting change was used. Runtime content collection remained enabled.
- Each automated case captured all fixture-file bytes/modes, including Git metadata,
  before and after. Source hashing covered the complete Power. Each process had a
  four-minute timeout, a hard termination bound, and bounded stdout/stderr.
- Source base was released commit `4cabe1b1ebefe4f0ba2bbdcae4862835241d89e9`.
  Uncommitted guide/router revisions are identified by content hashes, not attributed to
  that commit. Final guide SHA-256 is
  `3c4b88e3a4d5bd20f681b58bbbeacdda783d3fbb038c65355ab12b9ec324ad23`;
  router is `b07e27cb7950ba4bca9a305ce60219f48e8474ab2356e4c0a05d2bf6445fbae4`.
  Later version metadata does not alter these observed skill bytes.

## Failure and correction sequence

The released 0.7.0 baseline selected the shipped profile and honored the explicit read
denial. Its guide emitted malformed Spec prompts and skipped required linked references.
Three targeted revisions corrected command grammar, added literal paths and task-approval
distinctions, then clarified file-tool-only lookup and named-Spec paths. Those revisions
improved selected cases but did not establish complete acceptance.

An eleven-case candidate campaign still skipped destinations, partly read one skill,
deferred reading the healthy verifier, and imposed an unnecessary Plan-to-Spec sequence.
The same empty-library prompt in the interactive terminal also skipped its destination.
That comparison does not support blaming noninteractive entry alone.

The final revision orders project grounding before the destination read, gives a compact
path table, requires full skill contents, and preserves authorization in the suggested
next task. It was tested once across the eleven scenarios below. No final failure was
silently rerun or reclassified as a pass.

## Final observations

All eleven automated sessions selected `pkstack`, exited normally, and left their fixture
files unchanged. That does not imply all tool requests or answers obeyed the advisor.

| Scenario | Observation |
| --- | --- |
| Profile and user policy | Read `allowed.txt`; `blocked.txt` was denied once, with no retry or alternate tool. |
| Empty Python library | Read lifecycle, router, README, and complete technical-writing skill; preserved uv/pytest and proposed a caller example plus behavior proof. |
| Existing queue Spec | Read all three native documents; distinguished task approval and unknown implementation state; emitted `/spec queue`, Continue, and separate context without implementation. |
| Interaction uncertainty | Read lifecycle, router, workflow and prototype-method reference; recommended observing both interactions with a disposable prototype, without running it. |
| No repository | Identified unresolved comparison semantics and read `grill-me`; handled missing setup skill explicitly. Source-integrity diagnostic is described below. |
| Unfamiliar codebase | Failed: requested `echo skip`, rejected by native policy; recommended `/why` without reading its skill. Evidence/inference separation in the answer does not cure those violations. |
| Unit tests without surface proof | Read README and complete create-verification skill; proposed save/reload/persistence proof without executing it. The reported bug was not reproduced in this advisory test. |
| Stale verifier | Read README, existing verifier, and maintenance owner; preserved persistence expectations and separated product defects. Its broader setup/binding absence claims were not established by inspecting only the skill directory. |
| Healthy harness | Failed: read the router but skipped lifecycle, README, and existing verifier; asked the user for a discoverable artifact and deferred the needed inspection. |
| Explicit explanation | Answered the code question directly without advisory interception. Explicit `how` skill activation was not observed, and its broad non-integer-input statement was not a complete Python type-edge-case analysis. |
| Missing Slack capability | Disclosed missing access and read `recall`, but then recommended `/grill-me` without reading that new destination. Failed the destination-read contract. |

The no-repository run recorded `sourceUnchanged=false` because an operator's concurrent
focused pytest invocation created eight bytecode files in the Power source. The native
fixture itself was unchanged. Those generated caches were moved outside the source, and
the complete source bytes/modes again hashed exactly to the recorded pre-run digest
`876afa60279b58d21e23dc16578212f39ba556681225d6956bdfcae6c3fac0e9`.
The original failure result is retained, not overwritten. Later checks used bytecode-disabled
execution and did not repeat that source contamination.

## Interactive native handoffs

In a separate disposable fixture, `/plan Read .kiro/skills/grilling/SKILL.md; ...` entered
native Plan, read that method and the README, and returned a read-only conversational plan.
`/spec queue` opened the native document viewer. Its `C` Continue action resumed the Spec
agent, which read requirements, design, and tasks and preserved the unapproved execution
boundary. Separate carried context did not trigger writes or implementation.
`/spec new acceptance-library` reached the native description prompt and was cancelled.

These checks establish transitions, reads, and conversation behavior, not completed new-Spec
generation or approval-to-implementation. No complete before/after snapshot was taken for
this interactive fixture; all 223 setup receipt hashes still matched afterward, and captured
model tool requests were only reading/listing. Do not upgrade that to whole-tree preservation.

## Asset verification and release boundary

The subsequent read-only verification of published v0.7.0 downloaded the archive, checksum,
and local release receipt and compared them with the approved local package. All three were
byte-identical; release, asset, tag, and main identities were unchanged across the check.
The selected publication fields are in the evidence packet. No new receipt was uploaded
to v0.7.0 and this check is not GitHub Actions evidence.

The patch's deterministic checks and independent review remain separate release gates.
The final guide still has native compliance failures; publication must not imply they are
resolved. This campaign does not establish IDE, Crew, Web, unattended maintenance,
unrestricted-tool obedience, all-skill quality, or hosted CI acceptance.
