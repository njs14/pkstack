# PKStack friends IDE validation

Recorded September 5, 2026. Candidate source:
`151b9da6e0dd6fd295e81044c477f0d96ab0c0aa`. This report records native Kiro IDE
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
excluded. Other campaigns share the account meter. No final refreshed reading
is available while the Mac is locked. The target for this IDE lane is about two
credits; the completed Standard planning turn displays 0.39 so far.

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
workspace; it did not send any model request.

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

## Current result and remaining work

At the next CUA observation the Mac locked, and automatic unlock failed. The
native UI requires manual unlock before any pending tool approval can be
inspected or operated. No `.pkstack/state/goal.json` existed at the last scoped
read; the implementation and tests still had their original hashes. Therefore
the Standard IDE repair loop is **not yet a pass**.

The `quick/` consumer has no native Spec package yet. Its native Quick Spec
planning and same-conversation verification loop remain pending. This report
does not substitute the successful CLI workflows for either unfinished IDE gate.
