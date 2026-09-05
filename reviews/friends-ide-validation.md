# PKStack friends IDE validation

Recorded September 5, 2026. Candidate source:
`151b9da6e0dd6fd295e81044c477f0d96ab0c0aa` at bootstrap; the exercised core hashes
remain unchanged through the final candidate
`f84585ae8f7e4c47006d972dbc6c780eabb80766`. This report records native Kiro IDE
behavior separately from the [CLI campaign](friends-cli-validation.md).

## Runtime and boundary

Kiro IDE **1.0.437** ran native model tasks through its agent panel. The inspected
header selected **GPT 5.6 Luna / Low**, with **Autopilot off**. Native UI actions
used CUA; no ACP host, nested CLI model session, new credential, global permission
change, or automatic-approval setting was used. Existing user guards, formatting,
gitleaks, notification, and memory hooks ran under their existing configuration.

The initial refreshed IDE account counter recorded by the initiating agent was
**341.59 of 1,000 credits**. At takeover the same value was already 12 minutes
old, so it was not treated as a fresh reading; the older cached 334.59 value was
excluded. Other campaigns share the account meter. Opening the Quick fixture
after Standard completion refreshed the meter to **343.94 of 1,000**, updated
just now; the +2.35 account delta is not attributable solely to this lane.
The target for this IDE lane is about two credits. Standard displays **0.39**
for planning and **0.06** for repair; Quick displays the same **0.39 + 0.06**.
The four displayed turns total **0.90 credits**, within that target. The final
native account dashboard refreshed to **348.68 of 1,000**, also confirmed in the
status bar as updated just now; **overages remained disabled**. The initial-to-
final shared-account delta is **7.09**, not a per-lane cost. The readings and turn
estimates have different scope, and no usage/permission setting was changed.

Disposable root: `/private/tmp/pkstack-friends-ide.a8XP9q`.
The `standard/` and `quick/` consumers were bootstrapped before this lane's
takeover. Each contains the canonical intentionally incomplete `account.py` and
the four original unittest cases. Baseline SHA-256 values:

- `account.py`: `c5be60a396b05f9bbd990ffef75c62a4dc463bdbe401e2b5c621234dd52b9a7b`.
- `tests/test_account.py`: `65932341be2d1b133366ec58e583f224751f1f89b9d8d26ebfeb897cab664974`.

Tests were read-only. These IDE baselines are distinct from the shorter CLI
fixture implementation. The seven exercised instruction/profile/controller
hashes independently match the corresponding generated hashes in the CLI report:
`pkstack`, `pkstack-verified-goal`, `pkstack-core`, the `pkstack` profile, `goal.py`,
`runner.py`, and the internal launcher. The unrelated later
`design-control-loop` wording change is outside this mechanical IDE lane.

## Standard native Spec

Workspace: `/private/tmp/pkstack-friends-ide.a8XP9q/standard`.
Conversation title: **Plan Account ID Normalization Spec**.
Native session: `sess_d504ac4d-916f-4757-bd8a-076d71dcd1fe`.
The read-only current-directory session metadata lookup matched that title and
workspace; it did not send any model request. The diagnostic was
`kiro-cli chat --v3 --list-sessions --format json`, run separately from each
fixture directory using CLI 2.21.1. IDE version was read with
`defaults read /Applications/Kiro.app/Contents/Info CFBundleShortVersionString`.

The initial native selection was **Spec → Build a Feature → Requirements**.
At takeover, the native `feature-requirements-first-workflow` was awaiting design
approval. The actual requirements/design documents were inspected, followed by
native **Accept** for design and the task plan. A second task approval accepted
Kiro's native format refinement adding the required Overview section. Both
source files retained their baseline hashes during planning.

Kiro completed the plan and stopped as requested. The panel displayed estimated
usage **0.39 credits** and elapsed time **14m 15s**, which includes time waiting
for UI access and approvals. Native `.config.kiro` records:

```json
{"specId":"82a8b26a-752e-4643-91e3-a555a78aae0c","workflowType":"requirements-first","specType":"feature"}
```

Completed planning artifacts under `.kiro/specs/normalize-account-id/`:

| Artifact | SHA-256 |
| --- | --- |
| `.config.kiro` | `dff75356c34e25d89548cebc426355eb021e7aa91be16acea8a744f757cd31f3` |
| `requirements.md` | `e5f5ed1d736244b2c6a31831bc6570485f462527f8e8cc8ba3ce974cca87f7fe` |
| `design.md` | `4fed3db118fdc935cba799ba2cd0ae96aa4e9d83016d740fd1d9858d69fe1ae1` |
| `tasks.md` | `1e82ca7f58adc47a1f09b04f5613d10af3dc0e9d7f4ab7d9d604f78468fd2428` |

The plan contains one `account.py` repair and verification of the existing four
tests. Its suggested test recipe is `python -m unittest tests/test_account.py`.
The subsequent user instruction explicitly selects the reviewed equivalent
discovery command `python3 -B -m unittest discover -s tests -v` for the stored
executable contract; no test or native planning document is changed to bind it.

The native agent picker listed **WORKSPACE → pkstack**. Selecting it changed the
picker from **Spec** to **pkstack** while keeping the same conversation tab and
history. Luna/Low and Autopilot off remained selected. The submitted prompt
invoked `/pkstack-verified-goal`, required the native Spec binding, four attempts,
the displayed stored predicate, a recorded pre-edit failure, repair of only
`account.py`, the unchanged verifier, and final goal-status readback.

### Recorded implementation loop

The Mac locked after the repair prompt; the turn was preserved pending
**Load skill: pkstack-verified-goal** approval. After manual unlock that skill
was allowed once. A stale native panel repaint was resolved by the window's
native zoom action, without restarting the model or changing permissions.

Expanded native tool cards showed goal-status read, feature-list read (empty),
Spec-directory listing, the actual test-file read, and these commands from the
Standard workspace:

```text
./.pkstack/bin/projectctl goal bind-spec normalize-account-id --command "python3 -B -m unittest discover -s tests -v" --output json
./.pkstack/bin/projectctl goal start "Implement native normalize-account-id" --spec normalize-account-id --max-attempts 4 --output json
./.pkstack/bin/projectctl goal verify --output json
# Native Replace in File: account.py, approved once
./.pkstack/bin/projectctl goal verify --output json
./.pkstack/bin/projectctl goal status --output json
```

Before the account.py approval, a scoped read independently confirmed attempt
one was already stored as exit **1**, with three failures among four tests;
account.py and tests still had their original hashes. The native file card
targeted only account.py. After approval, native verification and status
completed; the actual goal state is **passed**, **2/4** attempts:

- Goal ID: `3fa70d18-006e-43a6-80f8-41b0cac60fbc`.
- Contract digest: `c57c6cbf210161d165f6c602a040a326927f73e65f6c6e1524cd6a5d034a67fa`.
- Failure: `2026-09-05T13:15:21.847540+00:00`, exit 1, three failures.
- Pass: `2026-09-05T13:18:13.765084+00:00`, exit 0, all four tests OK.
- Repaired account.py SHA-256: `4c2ef94dce224112b712e2d6bd1bd8faa02de58e12eebb96d4e9f196b91064e3`.
- Final goal.json SHA-256: `7eddf6265bd01518bbe79ac69c2a7168a27bffcccf0c89dc70158ae9e1d73afa`.

Tests and all three native planning documents retained their hashes above.
The repair strips surrounding whitespace, removes literal spaces/hyphens, and
checks length 12 plus `isdigit()`. This proves the four reviewed tests, not
uncovered Unicode/ASCII edge cases. Native final UI displayed **0.06 credits**
and **30m 55s** elapsed, including locks, approvals, and UI recovery.

## Quick native Spec

Workspace: `/private/tmp/pkstack-friends-ide.a8XP9q/quick`.
Conversation title: **Plan Minimal Account ID Normalization Fix**. Native session:
`sess_d9a67cee-139d-4392-aaa5-0cfede63f4ed`, matched by the same scoped metadata-only
session listing used for Standard.
The native **Quick Spec** workflow tile was selected before the prompt, with
Luna/Low and Autopilot off. The implementation and immutable tests retained the
canonical baseline hashes before planning. The prompt requests only native
Spec artifacts and the same four-test verifier, then a stop for same-conversation
workspace-agent handoff. No CLI model session substitutes for this workflow.

Actual native reads targeted account.py and tests/test_account.py, followed by
the built-in `fast-task-workflow`. Three native clarification choices retained
minimal normalization, the existing ValueError/message contract, and a direct
implementation inside normalize_account_id. Native metadata is:

```json
{"specId":"5d0e26bb-4eb3-49d5-af49-fa32862cdabd","workflowType":"fast-task","specType":"feature"}
```

The four native phase invocations created requirements, design, tasks, then
reviewed the package. Scoped reads reviewed each artifact before native Accept;
the last review refined design headings without changing the behavior or scope.
The completed native plan stopped at **0.39 credits**, **5m 45s** elapsed.
Source and tests still had their baseline hashes. Final planning artifacts:

| Artifact | SHA-256 |
| --- | --- |
| `.config.kiro` | `885910dd2704eec6ae5b8337e60967a24af0f044bfd4a529fa3fef37a014e60f` |
| `requirements.md` | `03dee8dd1212da89af43c9ac2ad70e7c0d307355388675cc8b4850de980c3984` |
| `design.md` | `473a814c6179bd87818a1b3eed8d91bf8df0c97bd23410b2acc8e69d916bf900` |
| `tasks.md` | `78d7c2703636d5feea572409c80b45d54265844b54793671f4a68b356f31a597` |

The native picker then showed Quick Spec selected and listed **WORKSPACE →
pkstack**. Selecting pkstack retained the same title, tab, planning history,
Luna/Low, and Autopilot off. The repair prompt explicitly approved the plan and
requested its Spec binding, four-attempt budget, displayed predicate/provenance,
pre-edit failure, account.py-only repair, unchanged verification, and status.
The ensuing **Load skill: pkstack-verified-goal** request was allowed once and
the native panel confirmed **Loaded skill: pkstack-verified-goal**.

### Recorded implementation loop

Expanded native cards showed goal-status read (no goal yet), Spec-directory
listing, feature-list read (empty), then these commands from the Quick workspace:

```text
./.pkstack/bin/projectctl goal bind-spec normalize-account-id --command "python3 -B -m unittest discover -s tests -v" --output json
./.pkstack/bin/projectctl goal start "Repair normalize_account_id to normalize spaces/hyphens and reject invalid IDs" --spec normalize-account-id --max-attempts 4 --output json
./.pkstack/bin/projectctl goal verify --output json
# Native Replace in File: account.py, approved once
./.pkstack/bin/projectctl goal verify --output json
./.pkstack/bin/projectctl goal status --output json
```

Before approving the account.py replacement, independent scoped reads confirmed
the already-recorded failure and both original source/test hashes. The native
panel then performed its replacement, verification, and final status read in
the same conversation. The actual goal state is **passed**, **2/4** attempts:

- Goal ID: `ba596e09-f4cf-4577-90fe-9db89cce31c0`.
- Contract digest: `370f26fb535b91d86ba622c6c5d762eb30ef9b64a35fe67c9142512ccbe6478d`.
- Failure: `2026-09-05T13:26:43.830649+00:00`, exit 1, three failures.
- Pass: `2026-09-05T13:27:18.560679+00:00`, exit 0, all four tests OK.
- Repaired account.py SHA-256: `ac4d61de61b85c9561239ae169d34641ca16875a9ed34b7be8a5ce0d96285918`.
- Final goal.json SHA-256: `961317f4ed5daae93e5f4935f9aa783c61cabc98b9d6d1f4296669919456de44`.

The Quick repair uses the same normalization plus an explicit ASCII-range
check inside the existing function. Tests remained mode **0444** and retained
their baseline hash. All four native planning artifacts retained the table's
hashes. The final native turn displayed **0.06 credits**, **1m 9s** elapsed.
The metadata-only session listing still returned the original Quick session
ID/title, now idle; Standard likewise remained its original session, idle.

## Result and limits

Both actual native IDE paths pass the bounded mechanical acceptance gate:
native Standard/Quick planning, same-conversation generated-agent handoff,
skill load, reviewed Spec-backed immutable predicate, recorded failure before
edit, implementation-only repair, and passing status on attempt two. Both
bridges have SHA-256
`ca1e15b9e3095380796ba19383c627d6459d9455cd9267ae72ea567ec100f950`.
The seven exercised instruction/profile/controller hashes were rechecked after
the loops and remained unchanged. Supervisor diagnostics read artifacts and
session metadata; they did not run either model repair or inject verification
attempts outside the native conversation.

This is four-test acceptance evidence, not a blanket proof that all prose Spec
properties hold or that every Kiro permission path is hardened. In particular,
Standard's Unicode-aware predicate leaves the native prose ASCII edge case
outside the four-test guarantee. No broader skill campaign, timeout/exhaustion,
cross-version compatibility, or fresh Power-import claim is inferred here.

Native planning/sub-agent file reviews and single-action skill/file approvals
were exercised with Autopilot off. The user hooks ran as already configured;
the report does not equate Autopilot off with a separate prompt for every shell
command. Locks required manual unlock; the preserved Standard conversation
survived, and native window zoom recovered the stale panel paint. Quick needed
no such workaround. These UI delays account for Standard's long elapsed times,
not extra model retries.

The completed disposable workspace window was closed. The user's pre-existing
Kiro Power window was left intact; fixture files and native sessions remain
available for inspection. Zoom was confined to the disposable window, which
was closed rather than leaving its enlarged geometry on screen; no pre-existing
window was resized. No candidate product files, credentials, global settings,
overage settings, commits, or remote state were changed by this lane.
