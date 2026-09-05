# PKStack 0.3.0 native CLI acceptance

## Result

The clean native Quick Spec campaign reached `passed` at attempt 2 of 4 in one Kiro CLI conversation: native Quick Spec generation, same-conversation `/agent swap pkstack`, spec-bound failing verifier, `account.py` repair, then passing verifier. The original tests and native planning package remained byte-for-byte unchanged through the handoff and repair. This is proof for the bounded account-ID fixture, not a release-wide verdict.

Native CLI: `/opt/homebrew/bin/kiro-cli` 2.21.1, `chat --v3 --agent pkstack --model gpt-5.6-luna --effort low`; interactive PTY captured by `/usr/bin/script`. No headless call, ACP bridge, or nested Kiro runtime supplied this proof. Workspace: `/private/tmp/pkstack-release-030-evidence/quick-clean`. Raw transcript: `/private/tmp/pkstack-release-030-evidence/quick-clean-native.typescript`. Clean native session ID: `sess_a0170c80-1139-4fd2-8df8-cce7bea7a5f5`; exited normally after route coverage and reselecting `pkstack`.

## Native planning and current-session retry

1. `/spec new release-account-quick-clean` opened the native workflow choice; **Quick Spec** was selected. Native `.config.kiro` records `workflowType: fast-task` and `specType: feature`. Kiro generated `requirements.md`, `design.md`, and `tasks.md`. Its native questions selected literal ASCII space/hyphen normalization and string-only inputs. A task-graph sequencing issue was corrected in native planning before the package was frozen; no implementation or test execution occurred during planning.
2. At the native idle prompt, `/agent swap pkstack` reselected the generated project agent in the same conversation. `/pkstack-verified-goal` loaded via native `disclose_context`, and the native agent inspected existing goal state, published features, native artifacts, and the baseline fixture.
3. The agent invoked `.pkstack/bin/projectctl goal bind-spec release-account-quick-clean --command "python3 -B -m unittest discover -s tests -v" --output json`, creating the narrow `pkstack-verification.json` bridge. It started the same spec-backed goal with a four-attempt budget and displayed the stored contract before executing the verifier.
4. First native `.pkstack/bin/projectctl goal verify --output json`: exit 1, four tests, three failures. The unchanged baseline returned separators and failed to reject non-digits/wrong length. Goal state persisted attempt 1 and the complete genuine stderr.
5. A follow-up invocation resumed that active goal without clearing, rebinding, restarting, or rerunning the baseline. The agent read goal status, modified only `account.py`, and invoked the existing verifier once. It removes literal ASCII spaces and hyphens, requires twelve ASCII digits, and raises `ValueError` containing `12 digits` on failure.
6. Second native verifier: exit 0, all four tests passed. Native `goal status` then reported `passed`, attempt 2/4, two remaining. Contract digest: `0a755d895b0ea6cecb77fd523701e9fe4a4a5ee7ec38d41a869a065047e140be`; goal ID: `2c756118-c764-4652-b06a-9a265c392819`.

Structured evidence under `/private/tmp/pkstack-release-030-evidence/`:

- `quick-clean-before-handoff.json`: baseline and native artifact SHA-256 hashes.
- `quick-clean-goal-baseline.json`: persisted first failure and contract.
- `quick-clean-goal-terminal.json`: final goal, immutable contract, both attempt records and stderr.
- `quick-clean-after-terminal.json`: post-pass artifact hashes.
- `quick-clean-after-routes.json`: all seven post-pass artifact hashes still equal and the complete terminal goal JSON unchanged after route coverage; raw transcript SHA-256 `00a8e29ef463db2ba72ad82a949b8a5bd94aa101f2cad1995832d965146cd472`.
- `quick-clean-native-readable.txt`: ANSI-stripped native transcript companion; raw typescript remains authoritative.
- `quick-clean-final-preview.json`, `quick-clean-final-setup.json`, `quick-clean-final-parity.json`: reviewed final-helper refresh and empty second parity preview.
- `final-cli-power.sha256.json`: exact frozen Power inventory; aggregate digest `c6eef823f15bb1f23e4a5b3e72e049e713bb1b979775100091a4a7acdd57947c` (259 files).

Before the native handoff, final reviewed helper files were applied through the Power-local ownership-aware setup shim after inspecting an exact six-path preview with no conflicts, pending paths, or stale paths. The refreshed files were the Archify skill/template/sequence renderer and the two loop helper skills plus control-loop reference. Baseline/tests/native artifacts stayed unchanged and the second preview was empty. The route, goal implementation, and primary-agent bytes used at this checkpoint were unchanged from the starting candidate; later candidate changes require separate scope-specific evidence.

Preservation proof: SHA-256 equality holds for `tests/test_account.py`, native `.config.kiro`, `requirements.md`, `design.md`, and `tasks.md` across freeze/handoff/terminal pass. The bridge remained `ca1e15b9e3095380796ba19383c627d6459d9455cd9267ae72ea567ec100f950` after creation. Only `account.py` changed among those frozen inputs.

## Permission observations and limits

Every clean-run native approval was inspected and allowed once. No always-allow, global tool trust, account permission, or policy widening was used. The PTY was resized for readable approval visibility only. A native Quick Spec nested-agent approval initially showed a pending count without an actionable request even after expansion. That request was not approved; native cancellation of that subagent let the workflow recover. A later visible `technical-writing` disclosure request was reviewed and allowed once. This is a native approval-visibility caveat, not evidence of a PKStack policy bypass.

An earlier exploratory Quick run at `/private/tmp/pkstack-release-030-evidence/quick` was retired and excluded from clean permission acceptance because mid-turn steering coincided with a native approval menu. It was exited normally, with baseline files unchanged. Its transcript and `quick-interrupted.json` remain for provenance; native session ID `sess_f0670e04-1d7e-4ce0-a2cf-78d49a63716a`. Only the clean run above supports this acceptance.

## Bounded PKStack route coverage

Route smoke is captured in the same clean native conversation after its terminal goal. These read-only invocations preserve the finished goal and fixture.

| Route | Native evidence and outcome |
| --- | --- |
| `pkstack-verified-goal` | Native skill load; full spec-bound genuine failure, repair, passing verifier, and terminal status described above. |
| `pkstack` | Native skill load and workflow-reference read. Classified the existing Quick package as Feature, selected the already completed verified-goal leaf, and explicitly skipped new planning, implementation, dispatch, binding, verification, and external action with reasons. |
| `pkstack-principles` | Native skill load, complete catalog read, and boundary-discipline leaf read. Applied the boundary test to actual account implementation and preserved tests/native requirements/design; chose one local normalization/validation boundary without additional helpers, callers, dependencies, or broader whitespace rules. |
| `pkstack-maintain` | Native skill load; native glob inspection found no `maintenance/upstreams.json` or `powers/pkstack/`. Returned concrete not-applicable result and stopped without network, verification, goal mutation, or file writes. This proves the consumer guard, not a full upstream maintenance transaction. |
| `pkstack-model-council` | Native skill load and two native `kiro` subagent calls with the same artifact packet and exact four-item rubric. Both reviewed read-only, agreed on the implementation and bounded four-test scope, and reported no material finding. They explicitly treated supplied attempt/hash metadata as metadata because the four source artifacts alone cannot prove historical byte preservation. No model-diversity claim was made. The coordinator refreshed read-only goal status once; no verifier, goal mutation, or artifact edit ran. |
| `pkstack-setup` | Native discovery tested on actual bundled Default after the same-conversation swap. Native `disclose_context` returned `No skill or auto inclusion steering file found with name "pkstack-setup"`; the other five PKStack routes appeared in the available list. Stopped without plain-file fallback activation, shim execution, edits, or settings changes. This CLI environment has no discoverable Power-local setup skill; the outer Power-local shim refresh above is separate evidence and is not native setup activation proof. |

Council reporting detail: the native final sentence said no commands ran, but the coordinator did invoke read-only `goal status` while preparing the packet. The reviewers themselves ran no commands. This report preserves that distinction and relies on captured command evidence.

## Current CLI agent-name finding

On this live Kiro CLI 2.21.1 build, the documented `/agent swap kiro_default` command produced:

```text
Agent changing to kiro_default
Agent 'kiro_default' not available
agent "kiro_default" not found, using "default"
```

The native `/agent` picker showed the bundled **Default** agent active. Selecting it reported `Switched to default`. A separate exact command `/agent swap default` then succeeded with `Agent changing to default` and `Switched to default`. `/agent swap pkstack` also succeeded, followed by a normal `/quit`.

Recommended current CLI command: `/agent swap default`. This corrects the live agent name; it does not itself install/import a Power or make `pkstack-setup` discoverable. Shared docs/steering/tests were left for the coordinating release owner to correct. The clean native campaign did not change global agents, model defaults, permissions, or Power inclusion to force coverage.

Post-route audit preserved all seven tracked post-pass files and the entire terminal goal JSON, including the two-attempt history and immutable contract. Five routes have bounded native behavioral evidence; setup has concrete native discovery-failure evidence. No broader CLI setup success, external model diversity, exhaustive account-input coverage, or overall release acceptance is claimed.
