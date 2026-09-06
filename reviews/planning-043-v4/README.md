# PKStack 0.4.3 native planning follow-up — v4 candidate

**Source approved by two independent reviews. Merge, tag and publication remain
blocked.** The written CLI handoff contract requires the router to return one runnable
line beginning `` /plan Read .kiro/skills/grilling/SKILL.md; ``. Native `Auto` did not
emit it, in two separate runs. Everything else the earlier campaign blocked on was
cleared, some of it with an operator in the loop.

This is a follow-up to `reviews/planning-043`, which stays intact as the committed
blocked baseline for v1–v3. It is intended to land as `reviews/planning-043-v4`, at
which point `../planning-043/README.md` resolves; until then, `reviews/…` paths here
are canonical-repository paths, not links. Links to files in this directory are
relative and resolve.

## What this supersedes

| Historical observation | Status |
| --- | --- |
| CLI stayed in `pkstack` and re-asked the settled ASCII rule | Superseded: both v4 router runs packaged a handoff and stopped, asking no settled question |
| Approved-plan execution wrote code and ran the verifier before capture | Superseded: capture and validation completed before the product edit |
| IDE Quick Spec post-approval no-write acknowledgement never captured | Superseded twice: recovered for v3 in `ide-spec-v3-recovered-ack.json`, and captured in v4 with an empty post-approval delta |
| v3 IDE accepted `AB12SS` for `ab12ß`; v3 CLI offered a forbidden Unicode option | **Not** superseded. Both remain recorded v3 failures |
| v3 Quick Spec recorded its own recommendation as settled before an explicit choice | **Not** superseded |
| Everything else in `reviews/planning-043` | Unchanged and still authoritative |

No v3 failure is rewritten as a pass here, and no v3 source evidence is altered.

## Candidate identity and binding

| Item | Value |
| --- | --- |
| Base commit | `cbabee7d3813ef9eb166afedd7b09ffca22fb4ce` |
| Candidate commit | `88bbe15b3858b6347f35dd975a6ecd35ffcadd93` (2026-09-06T21:43:28Z, branch `codex/cli-power-discovery-docs`) |
| Power version | `0.4.3`, unreleased |
| Source manifest | [source-files-v4.json](source-files-v4.json), 293 Power-relative hashes |
| Manifest file SHA-256 | `7fd53ba542b8de7842fbd302e83395b75f1041dc755382ed5190c3e184790803` |
| Manifest sorted-JSON SHA-256 | `4da4bb85d8cff460ac537ce4c1bfcf1743d02300c8af3a4b84c4c56edbe002b1` |
| Reviewed patch manifest | [opus-source-review-manifest.json](opus-source-review-manifest.json), 9 canonical files |

Digests use `json.dumps(manifest, sort_keys=True)`, UTF-8, default separators, no
trailing newline, as in the historical report.

**v4 is bound to the frozen copy at `power-v4/` and to commit `88bbe15`, not to the
authoring worker's checkout.** Verified for this report: all 293 manifest entries match
`power-v4/` and `powers/pkstack/` at `88bbe15` with 0 mismatches, 0 missing and 0 extra
files; all 9 reviewed-patch hashes match `power-v4/` and `git show 88bbe15:…`. The
worker worktree has since been reopened for separate routing work and 5 of those 9 paths
already differ there, so it is no longer authoritative for anything in this report. No
work from that later effort is included here.

`88bbe15` carries the 9 canonical files plus 5 generated files refreshed through reviewed
setup: the four managed mirrors `.kiro/skills/grilling/SKILL.md`,
`.kiro/skills/pkstack/SKILL.md`, `.kiro/steering/pkstack-core.md`,
`.kiro/agents/pkstack.json`, and the setup receipt `.pkstack/bootstrap.json`, which setup
rewrites and its inventory does not count as a managed update.

## Source change and reviews

Nine canonical files under `powers/pkstack/`, authored by an external Claude Opus 5
`xhigh` worker (**FIX_CANDIDATE**) and reviewed twice by independent Grok 4.6 `xhigh`
workers in read-only sandboxes. Both returned **APPROVE_SOURCE_CANDIDATE**. The change
is a contract, not more injunctions: the mode that runs the plan runs the interview;
mechanics determined by a settled constraint are stated rather than asked; the knowledge
checkpoint is step one of the plan's own ordered steps.

The **final review**, run against the committed candidate and the native evidence, splits
its verdict explicitly:

> **Verdict:** source **APPROVE_SOURCE_CANDIDATE**. Release/merge of 0.4.3 as
> native-accepted **BLOCKED**. Those two results are different.

The exact-line requirement predates v4: v3 demanded it and `Auto` already failed to emit
it, so accepting an operator-typed `/plan` would lower a written, tested contract. The
same review lists what is no longer independently blocking: CLI interviewing instead of
handing off, settled ASCII re-asked, capture after code, and the missing Quick Spec
acknowledgement. Quoted findings, declared limits and the one non-blocking residual are in
[review-verdicts.json](review-verdicts.json).

All three reviews are static. None ran a native session. The new tests in
`tests/test_kiro_assets.py` are substring assertions over instruction text and prove only
that the text is present.

## Automated checks

Local full gate on the canonical repository with the patch applied
([gate-v4.json](gate-v4.json)): **965 product pytest tests passed**, all ten lanes
`passed`, zero issues, collection digest
`035acc619b577f05d8fd1cf6f50002651d28d5d22dabda8b2dd03b172586eb28`. The policy lane ran
under the supported uv-managed interpreter (`powers/pkstack/.venv/bin/python3`): 222
Python policy tests OK, 17 Node policy tests passing, plus lock, lint, format, type,
version, feature and knowledge checks. The planning-043 system-Python-3.9 policy failure
did not recur. Policy tests are separate from the 965 and are not added to that count.
The gate plan records `cbabee7` because it ran on working-tree bytes; those bytes were
committed as `88bbe15` six minutes later.

Targeted fast lane: **22 passed, 943 deselected** — a rerun after the instruction change,
not a second full gate.

Hosted CI on `88bbe15` ([hosted-ci-88bbe15.json](hosted-ci-88bbe15.json)): all **12 jobs
successful**, run `34061930185`. A draft-PR product run; release-package steps are not
part of it and it proves nothing about native planning.

Managed setup ([setup-v4.json](setup-v4.json)): the root install updated the four managed
mirrors, then a fresh preview reported zero creates, updates, conflicts, pending updates
and stale files. That clears the author worker's declared consequence that the
canonical/generated parity test would fail on a canonical-only patch.

## Native CLI

One full session plus one router-only repeat, both `pkstack · Auto`. The resolved model
behind `Auto` was **not established** and the CLI semver was not captured. Excerpts:
[cli-plan-v4-excerpts.json](cli-plan-v4-excerpts.json). Fixture install clean:
[cli-plan-v4-doctor.json](cli-plan-v4-doctor.json), 84 checks, 0 fail, 0 warn.

**Router — half met.** It read the three files, separated settled requirements from the
one open choice, packaged a native Plan handoff and stopped:

> Select native Plan and run that. I'll stop here for that selection rather than
> answering the open question myself.

No settled question, no option permitting non-ASCII input. That is the v3 interview
failure repaired.

**Router — exact syntax not met, twice.** The string `/plan` appears **zero times** in the
main recording; the handoff body begins `Read .kiro/skills/grilling/SKILL.md and use its
interview method…`, and the coordinator prepended the documented `/plan` prefix by hand.
An independent router-only repeat ([cli-router-v4-repeat.json](cli-router-v4-repeat.json))
reproduced the omission — *"Please switch to native Plan mode"* instead of a runnable line
— so this is a repeatable defect, not a one-off. That repeat also stated
strip → uppercase → validate as settled by the contract, the same wrong mechanic an
operator corrected in the main run, and told the user to return to `pkstack` after
approval without distinguishing Kiro's own execution handoff. The observable evidence of
mode entry in the main run is the banner moving `pkstack · Auto` → `Plan · Auto` and the
client's `Switched to kiro_planner`. Assisted mode entry is not a zero-intervention route.

**Plan — correct after review, not autonomously correct.** Native Plan read the installed
shared method, stated the derived mechanics instead of asking, and asked exactly one
question, the unresolved error wording. Its first stated ordering was wrong:

> - Order: `value.strip()` first, then `.upper()`, then validate the result.

That accepts `ab12ß` as `AB12SS`, the v3 IDE defect. Ordinary plan review chose the uniform
message and supplied the counterexample; Plan then moved validation before uppercasing and
listed the knowledge checkpoint as Task 0. What improved against v3 is the shape of the
interview, not the model's Unicode reasoning. No wrong implementation ever reached
`reference.py`.

**Approval and execution.** The approval was neutral, with no capture or ordering
instruction: *"I approve this plan. Implement it in this fixture and preserve the existing
tests."* Kiro's own approval handoff then moved `Plan · Auto` → `Default · Auto`, carrying
Task 0. PKStack did not perform that handoff.

**Capture before code.** A polling file watcher recorded three events
([cli-plan-v4-file-events.jsonl](cli-plan-v4-file-events.jsonl)):

| Observed (UTC) | Change | Product matches baseline | Tests match baseline |
| --- | --- | --- | --- |
| 21:25:04.830 | `Wiki/knowledge/reference-normalization/index.md` created | yes | yes |
| 21:25:07.986 | `Wiki/knowledge/index.md` updated | yes | yes |
| 21:25:14.288 | `reference.py` changed | **no** | yes |

Capture finished 6.3 s before the product edit, with validation between them. Watcher
times are observation times, not exact write times; the ordering is corroborated by the
transcript order. Task 0 resolved its methods from installed workspace paths, with no
global Power lookup.

**Knowledge validation — three distinct records, corrected.**
[cli-plan-v4-knowledge-validation.json](cli-plan-v4-knowledge-validation.json) separates
them, because an earlier draft of this report conflated the first with the second:

1. **Pre-flight**, 21:17:43 UTC, coordinator, *before* the CLI session launched: 3
   documents, `ok: true`. Baseline health only; it says nothing about the native run.
2. **Native capture validation**, the invocation whose timing matters: evidenced only by
   the recording, which shows the command, a **truncated** output pane and the agent's
   statement *"Knowledge validation passes … Task 0 complete"*, all before the product
   edit. No machine receipt of that specific invocation was retained.
3. **Host final state**, 21:56:53 UTC, coordinator, after the session: exit 0, 4 documents,
   7 local links, `ok: true`. It verifies the final captured state, **not** capture timing.

**Idempotence and verification.**
[cli-plan-v4-before-approval.json](cli-plan-v4-before-approval.json) records no file
changes while Plan was active.
[cli-plan-v4-final-files.json](cli-plan-v4-final-files.json) records two changed files and
one addition with `tests_unchanged: true`. A second neutral approval changed nothing and
duplicated no topic ([cli-plan-v4-before-repeat.json](cli-plan-v4-before-repeat.json),
[cli-plan-v4-after-repeat.json](cli-plan-v4-after-repeat.json)). The coordinator's
independent host rerun reports 3/3 tests passing and 3 non-ASCII cases rejected with the
uniform message ([cli-plan-v4-host-checks.json](cli-plan-v4-host-checks.json)); that
receipt records the summary line, not the three exact input strings. `README.md` and
`tests/test_reference.py` still hash to baseline; only `reference.py` changed
([fixture-context-v4.json](fixture-context-v4.json)). Three fixture tests and a few probes
are a fixture check, not a product gate.

## Native IDE Quick Spec

Kiro IDE 1.0.437, Quick Spec in Agent Focus, autopilot off, inherited **GPT 5.6 Luna /
Low**, no model or global configuration change. Coordinator-observed:
[ide-spec-v4-final-evidence.json](ide-spec-v4-final-evidence.json),
[ide-spec-v4-receipts.json](ide-spec-v4-receipts.json).

**Provenance.** The fixture reused the four Spec documents the *v3* native run created;
only the installed PKStack method was refreshed to v4. This is v4 method loading, settled-
decision reuse, artifact review and no-write evidence — **not fresh all-v4 Spec
creation** — and it carries no implementation or test evidence.

The workflow loaded `grilling` after a one-time Allow, reused the settled decisions without
re-interviewing them, and corrected the defect the operator named: tasks 1.1 and 1.2 both
edit `reference.py` and had shared one parallel wave; they now sit in separate waves. On an
approval that explicitly forbade execution, commands and any file or Wiki write, the agent
answered:

> The Spec is complete and your approval is recorded. I will not execute tasks, run
> commands, or change any files.

Receipts recomputed here agree with the coordinator's: two Spec files changed against the
v3 baseline, nothing added or deleted, product, tests, README and Wiki untouched, and the
post-approval delta empty in all three categories. That empty delta is the gate
planning-043 could not capture.

Limits: no implementation or tests ran; the acknowledgement named implementation as pending
but not pending knowledge capture; observations cover the fixture and visible agent actions,
not a machine-wide hook audit; the corrected graph was reviewed, not executed; and the
pre-correction v3 bytes of `design.md` and `tasks.md` are not retained here, only their
baseline hashes.

## Operator interventions

1. **Assisted mode entry.** The router returned no runnable `/plan` line; the coordinator
   typed the prefix. Reproduced as a failure in the router-only repeat.
2. **Reviewed plan correction.** The coordinator chose the uniform message and supplied the
   `ß` counterexample after Plan proposed uppercasing before validation.
3. **Operator-raised IDE defect.** The same-file parallel-wave problem was named in the
   review prompt, not detected unprompted.

Approvals themselves were neutral. No further operator input followed either approval, so
the capture ordering, the idempotent repeat and the IDE no-write hold are unassisted
results.

## Still blocking, and still not established

Blocking merge, tag or publication:

- The CLI exact-line handoff contract is not natively satisfied, in two runs.
- Therefore unqualified 0.4.3 native-planning acceptance is not available.

Not established by anything here:

- A zero-intervention CLI planning route.
- Autonomous Unicode correctness during planning.
- Separation of model behaviour from client behaviour: CLI ran unresolved `Auto`, IDE ran
  Luna/Low, and the CLI semver was not captured.
- Fresh v4 Spec creation, v4 IDE Plan, IDE implementation, or execution of the corrected
  task graph.
- A v4 standalone `/grill-me` boundary rerun; v3 passed that and it was not repeated.
- Generalisation beyond one fixture contract and three native observations.
- That the substring asset tests constrain native behaviour rather than text.

## Evidence index

Every retained file, with byte counts and full hashes, is listed in
[campaign.json](campaign.json) under `retained_files`; the machine report also carries the
identities, checks, native cases and limits in structured form.

Retained alongside this report: [source-files-v4.json](source-files-v4.json), [opus-source-review-manifest.json](opus-source-review-manifest.json), [review-verdicts.json](review-verdicts.json), [gate-v4.json](gate-v4.json), [hosted-ci-88bbe15.json](hosted-ci-88bbe15.json), [setup-v4.json](setup-v4.json), [cli-plan-v4-excerpts.json](cli-plan-v4-excerpts.json), [cli-plan-v4-knowledge-validation.json](cli-plan-v4-knowledge-validation.json), [cli-plan-v4-file-events.jsonl](cli-plan-v4-file-events.jsonl), [cli-plan-v4-before-approval.json](cli-plan-v4-before-approval.json), [cli-plan-v4-final-files.json](cli-plan-v4-final-files.json), [cli-plan-v4-before-repeat.json](cli-plan-v4-before-repeat.json), [cli-plan-v4-after-repeat.json](cli-plan-v4-after-repeat.json), [cli-plan-v4-doctor.json](cli-plan-v4-doctor.json), [cli-plan-v4-host-checks.json](cli-plan-v4-host-checks.json), [cli-router-v4-repeat.json](cli-router-v4-repeat.json), [fixture-context-v4.json](fixture-context-v4.json), [ide-spec-v4-final-evidence.json](ide-spec-v4-final-evidence.json), [ide-spec-v4-receipts.json](ide-spec-v4-receipts.json), [ide-spec-v3-recovered-ack.json](ide-spec-v3-recovered-ack.json), [raw-evidence.json](raw-evidence.json).

## Preparation and retention

Written from local evidence only: no UI, no Kiro CLI, no network, no source changes. File
comparisons quoted here were recomputed from the retained manifests and agree with the
coordinator's recorded fields. Raw recordings, full gate receipts and both disposable
fixtures stay local under the temporary task root and are not committed; `native-cli-v4.raw`
is 491871 bytes, SHA-256
`4bec66963253ee67906c1e0719f9045a888fc739cb57bf8ca2921333cc3bdf11`. The CLI excerpts are
selected regions of that recording after ANSI stripping and redraw collapsing, not a
continuous transcript; line breaks inside quoted blocks are terminal wrapping. Worker stream
logs were read only for their final `type=result` text. No secrets or user configuration are
reproduced.
