# PKStack 0.3.0 native builder and verified-goal composition

The final generated label loop completed a bounded native composition check:
`build-iterated-agentic-loop` supplied the reusable-loop method, and
`pkstack-verified-goal` stored and enforced the full fixed acceptance suite in
the same Kiro CLI conversation. The goal recorded a real initial failure,
an implementation-only repair, and terminal pass at **attempt 2 of 4**.

## Fixture and command contract

A fresh disposable consumer was installed from canonical Power commit
`23b34a7df75fcabd8998f174002aa175aecf0ad3`. The retained implementation and
five-test suite came from the [final loop-helper acceptance](release-030-loop-helpers.md).
The coordinator first proved the original suite passed, then introduced one
controlled implementation fault: `MAX_ATTEMPTS = 2` became `MAX_ATTEMPTS = 1`.
The unchanged suite then ran all five tests and returned nonzero: four passed,
while the two-attempt case failed at its second reservation.

| Artifact | SHA-256 |
| --- | --- |
| Fixed `tests/labels-loop.test.mjs` | `087a3b3c4a76f4785ad3881ed5d405a1ad0aa8bc615145cb0b680a6db84d3876` |
| Original passing `labels-loop.mjs` | `162a6305aa1a39e5bf107ac0a98599a896e5fbc48fe09bd7a45adf054f127d05` |
| Injected fault | `3eb40e7ec93b800947dce83121e9c5f6117c6fc0f115cc3b79e38c3261c94360` |
| Native repaired implementation | `162a6305aa1a39e5bf107ac0a98599a896e5fbc48fe09bd7a45adf054f127d05` |

The initial native `goal start` rejected `node --test tests/labels-loop.test.mjs`
with `CommandRejected`: `node must select a project script directly; leading
runtime options are unsupported`. Kiro stopped before editing or creating goal
state. This is a runner command-contract limit; no runner repair or policy
exception was made.

The coordinator then proved that supported direct execution,
`node tests/labels-loop.test.mjs`, runs the exact same immutable file and counts
all five tests: the original implementation passed 5/5; the fault left four
passing and one failing, with exit 1. That spelling was explicitly approved and recorded in the
composition contract before any goal existed. The contract was frozen again
before binding. No acceptance assertion changed.

## Native execution

The fresh interactive session used existing Kiro authentication and CLI 2.21.1:

```sh
env PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  UV_OFFLINE=1 /Users/noahsutter/.local/bin/kiro-cli chat --v3 \
  --agent pkstack --model gpt-5.6-luna --effort low
```

Session `sess_1169f621-24b2-4a2d-84c7-e89d21ab1db3` natively disclosed both
`build-iterated-agentic-loop` (6,742 characters) and `pkstack-verified-goal`
(7,051 characters). It read the builder's control-loop reference, fixture
contract, existing implementation and tests, and exact local actuator skill.
A failed initial glob had incorrectly suggested the actuator skill was absent;
the follow-up supplied its existing `.kiro/skills/trim-label/SKILL.md` path.
No new actuator or replacement skill was created.

The same conversation confirmed there was no goal and inspected native
Spec/feature availability. No matching native Spec or published feature existed.
It used the supported explicit verifier without creating a synthetic Spec:

```sh
.pkstack/bin/projectctl goal status --output json
.pkstack/bin/projectctl feature list --output json
.pkstack/bin/projectctl goal start \
  "Continue the same bounded builder composition. Complete the bounded composition acceptance in COMPOSITION-CONTRACT.md." \
  --command "node tests/labels-loop.test.mjs" --max-attempts 4 --output json
.pkstack/bin/projectctl goal verify --output json
# Native, individually approved repair: MAX_ATTEMPTS = 1 -> MAX_ATTEMPTS = 2.
.pkstack/bin/projectctl goal verify --output json
.pkstack/bin/projectctl goal status --output json
```

Kiro displayed the stored predicate and its explicit provenance before its
first goal verification. Goal `f223b5ea-8344-4f29-804f-988d5708993c` retained
contract digest `47e9e2840c1822f93e94a024e3f4a8b8f049026427abefde94299bbb20d9a416`.
Attempt 1 exited 1 with the genuine 4/5 result while the faulted implementation
was still present. Only then did Kiro propose and apply the one-line repair.
Attempt 2 exited 0 with 5/5; terminal status was `passed`, with two attempts
remaining. The goal was never cleared, rebound, resumed, or given more attempts.
The native session exited normally with `/quit` and process exit 0.

The two skill disclosures and the exact implementation replacement each
received one inspected, per-action approval. No persistent trust or permission
setting changed. The coordinator's read-only goal inspection captured attempt 1
before approving the implementation edit; the verifier and repair themselves
were invoked by the native session.

## Preservation, retained evidence, and scope

After session exit, all **169 bootstrap-managed file hashes** and six protected
input hashes matched the pre-binding baseline. The protected inputs are the
fixed suite, README, AGENTS, explicit composition contract, label data, and
actuator skill. These are existing/coordinator-provided planning inputs, not
newly generated native Spec artifacts. Only `labels-loop.mjs` changed among
existing files. Added files were `goal.json`, `.goal.lock`, and
`.goal.verify.lock` under the controller's normal `.pkstack/state/` directory.
The inventory excludes dependency-runtime and Python bytecode cache directories.

The repaired implementation is byte-identical to the retained original that
passed the independent 24-case process/state harness. That existing evidence
therefore applies by exact identity; the broader harness was not rerun. The
five fixed native tests still call the exported loop function in one process,
and their malformed-state title still exceeds the case actually implemented.
This composition check does not upgrade those tests' coverage.

An independent read-only evidence audit approved this bounded composition. It
checked the stored goal against both receipts, exact suite and implementation
identities, all protected/managed hashes, the changed-path inventory, and the
prior 24-case result. It ran no tests, edited no files, and read no raw capture.

Sanitized receipts and fixture artifacts are retained under
`/private/tmp/pkstack-release-030-evidence/composition-bnbdlvw1/`:

- `composition-receipt.json` and `native-observations.json`: session, disclosure,
  command, approval, result, and scope facts without private model reasoning.
- `goal-baseline.json` and `goal-terminal.json`: the unchanged contract and both
  durable verifier attempts, including genuine test stdout/stderr.
- `before-goal.json` and `after-native.json`: protected/managed hashes and the
  complete changed-path inventory within the stated cache exclusions.
- `predicate-parity.json`, original/fault direct-suite logs, and original,
  faulted, and repaired implementation copies alongside the immutable suite.
- `composition-review.json`: the independent audit's bounded approval and scope.

The temporary raw interactive capture was removed after extracting the
sanitized facts. This is a controlled repair of an existing reusable loop,
following an approved pre-binding command adjustment. It is not a new native
loop-generation campaign, a GUI test, or evidence of hosted execution,
publication, broad routing, unassisted writing compliance, rendered Mermaid,
or React browser behavior.
