# PKStack 0.3.0 loop-helper verification

This lane changes the two curated loop methods and tests their native use in
disposable consumers. It is not a general automation or release verdict.

## Confirmed defects and source repairs

The retained original fixture at `/private/tmp/pkstack-curated-smoke.fyhM5s`
reproduces both builder failures recorded in `friends-curated-validation.md`:

- Ordinary verification succeeds without preservation evidence. Supplying the
  actual pre-edit baseline rejects the correct trim with exit 1 and
  `unchanged value changed: alpha` because it chooses permission from the
  post-edit eligible list.
- Three independent controller invocations against the same padded baseline all
  return `terminal: candidate` and exit 0 despite `maxAttempts: 2`.

The bundled builder required bounded attempts and failure tests but did not
define reservation timing, authoritative state between commands, or mandatory
pre-actuation selection and baseline proof. Its composition guidance also let a
one-sample set-point verifier substitute for the reusable loop's acceptance suite.

The revised method requires an executable acceptance suite with isolated fixtures
before implementation, preserves its acceptance meaning during repair, and binds
any composed verified goal to that suite. It requires attempt reservation before
actuation, mandatory baseline preservation, durable state between independent
invocations, explicit reconciliation when restart support is promised, and
separate increment/global-completion reporting. The reference gives exact negative
cases and distinguishes malformed state values from a new run.

The design method now includes all eight short taxonomy definitions directly in
the natively loaded skill. The existing reference remains available. This removes
the earlier fragile separate-read dependency without omitting the method. The
design phases now name attempt enforcement and pre-actuation proof explicitly.

## Native runtime and fixture boundary

- Kiro CLI 2.21.1, interactive `chat --v3 --agent pkstack`, `gpt-5.6-luna`, `low`.
- Existing Kiro authentication only. Native per-action approvals used **Allow**;
  no trust override, permission-profile change, external model, schedule, push,
  publication, or account-setting change.
- Reviewed source starts from `3d4583a` in `/private/tmp/pkstack-release-030`.
  The helper smoke used a frozen Power copy while the parallel Archify repair was
  in progress; only its unrelated Archify subtree and manifest came from `HEAD`.
  This isolates the helper evidence and does not validate that Archify candidate.
- Setup returned `ok: true`, no conflicts, no pending updates, and no stale managed
  assets in each fresh consumer.
- Fixture data: `{"alpha":"  Alpha ","beta":"Beta"}`. One increment may trim
  exactly one padded nonempty value; every key and other value must be preserved.
  A run has two attempts and supports restart reconciliation. The builder write
  scope includes its script, a local actuator skill, tests, `.labels-loop/` run
  state, and one real trim. Tests must use isolated fixtures.

## First revised-method counterexample

Consumer: `/var/folders/ns/6ms4sgcd3jbc071v7_b2j2640000gp/T/pkstack-release-loop-smoke.sbr379uv`.
Native session: `sess_5cb91020-be26-4cea-a0f3-6a8b78f06418`, exited normally after
the coordinator cancelled the unfinished builder draft on independently reproduced
failures. The visible turn displays were 0.04, 0.03, and 0.15 credits; these are
rounded per-turn measurements, not an attributable account-wide delta.

Observed native `disclose_context` events loaded design (3,551 characters) and
builder (6,252 characters). The builder read its installed control-loop and
response-template references. The design gave counted, baseline-bound transitions
and explicitly labeled its command interfaces proposed and unexecuted.

The first terminal omitted Homebrew from `PATH`; the design's controller help and
initial builder status therefore failed with `uv: command not found`. This was a
harness condition, corrected by supplying command-local `PATH`; it was not a
missing installation. No product change was made for that condition.

After correction, Kiro composed `pkstack-verified-goal`, recorded an initial
`MODULE_NOT_FOUND` failure for `node labels-loop.mjs verify`, wrote a draft, and
ran its initial four tests (two passed, two failed). Those tests depended on the
real fixture's state and omitted required adversarial cases. The coordinator did
not accept that suite or its stored goal as reusable-loop proof.

Independent tests copied draft SHA-256
`89f0c0886b3faa0052b2617612f1449a2199e06da7df7084d171a8efb09e3c5b`
into isolated cases under
`/var/folders/ns/6ms4sgcd3jbc071v7_b2j2640000gp/T/pkstack-loop-adversarial.01jwns11`.
The directory retains the exact `candidate.mjs` and sanitized `result.json`.

| Case | Observed result |
| --- | --- |
| Correct selected trim against pre-actuation baseline | Pass |
| Added/removed key, unrelated value, non-trim replacement | Rejected |
| Malformed JSON, blank/non-string label, wrong container | Rejected |
| Verify already-trimmed data without baseline/state | Incorrectly accepted |
| Verify valid first trim with more work, then reserve second increment | Stuck on uncleared pending state |
| Existing state `{}` | Incorrectly reserves with null attempt |

These failures motivated the final acceptance-first/composition clarification and
the explicit reconciliation/state-validation requirements. This historical draft
is retained as a counterexample, not repaired into the passing evidence.

## Final fresh run

Consumer: `/var/folders/ns/6ms4sgcd3jbc071v7_b2j2640000gp/T/pkstack-release-loop-final.amox67n5`.
Native session: `sess_4982d779-891e-4c41-8b2d-045bd7eaf134`, exited normally.
The original design and builder prompts were repeated in a fresh conversation,
without the first draft's counterexamples or corrective steering. The launch
provided the correct local `PATH` and `UV_OFFLINE=1` from the start:

```sh
env PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  UV_OFFLINE=1 /Users/noahsutter/.local/bin/kiro-cli chat --v3 \
  --agent pkstack --model gpt-5.6-luna --effort low
```

Native disclosure loaded the final design wrapper (3,551 characters) and builder
wrapper (6,742 characters); Kiro also read the installed builder control-loop and
response-template references. The final design supplied the complete taxonomy,
distinguished invalid input from no-op, and labeled its command sequence proposed
and unexecuted. No write tool ran during the design.

The builder wrote isolated acceptance tests **before** the implementation and ran
them to an initial missing-module failure. Its first implementation failed the
blank-label and optional restart-reservation cases. Kiro repaired the implementation
against the unchanged tests, then passed all five tests and its syntax check. No
corrective user message or coordinator edit was supplied to this generation.

The generated suite's hash remained
`087a3b3c4a76f4785ad3881ed5d405a1ad0aa8bc615145cb0b680a6db84d3876`
from before implementation through the final independent rerun. Its five tests
use isolated files but call an exported function in one process. Its test title
mentions malformed state without exercising that case. The coordinator supplied
actual separate-process and malformed-state checks below; the native summary
alone is not evidence of either property.

The native demonstration ran these separate commands, with the returned
reservation ID `b27d3b7a-886a-4959-afa9-0ff7c48206c8` for the last two:

```sh
node --test tests/labels-loop.test.mjs
node --check labels-loop.mjs
node labels-loop.mjs sensor --data data/labels.json --state .labels-loop/state.json
node labels-loop.mjs reserve --data data/labels.json --state .labels-loop/state.json
node labels-loop.mjs actuate --data data/labels.json --state .labels-loop/state.json \
  --reservation b27d3b7a-886a-4959-afa9-0ff7c48206c8
node labels-loop.mjs verify --data data/labels.json --state .labels-loop/state.json \
  --reservation b27d3b7a-886a-4959-afa9-0ff7c48206c8
```

All exited successfully. The final verifier returned
`{"status":"complete","attemptsUsed":1}`. The real data changed only `alpha`
from `"  Alpha "` to `"Alpha"`; the keys and `beta: "Beta"` are unchanged. The
state retains one verified increment, `attemptsUsed: 1`, and `pending: null`.
Kiro remained the actuator by invoking the reserved deterministic local write
through its generated skill. No additional model session was launched by Kiro.

The final design and builder turns displayed 0.05 and 0.14 credits, respectively.
The builder took 9m 17s, including interactive approval time. These are bounded
per-turn displays and do not establish account-wide attribution.

## Independent final acceptance

After the native session ended, the coordinator reran all five generated tests
and the syntax check successfully. The independent harness copied the final
script into a separate directory and invoked a new Node process for every
command. It retains its source, exact candidate, all test inputs/state, exact
command arguments, exit codes, stdout, and stderr at:

`/var/folders/ns/6ms4sgcd3jbc071v7_b2j2640000gp/T/pkstack-loop-final-check.mp9jkbhh`.

The exact repeatable command is:

```sh
/opt/homebrew/bin/python3 \
  /var/folders/ns/6ms4sgcd3jbc071v7_b2j2640000gp/T/pkstack-loop-final-check.mp9jkbhh/check.py \
  /var/folders/ns/6ms4sgcd3jbc071v7_b2j2640000gp/T/pkstack-release-loop-final.amox67n5/labels-loop.mjs
```

Result: **24 of 24 cases passed**, exit 0, against script SHA-256
`162a6305aa1a39e5bf107ac0a98599a896e5fbc48fe09bd7a45adf054f127d05`.

| Behavior | Independent result |
| --- | --- |
| Correct selected trim with mandatory baseline, including empty existing key | Passed |
| Added, removed, renamed key; unrelated, non-trim, or two changed values | Rejected |
| Malformed JSON, blank/non-string value, array/null container | Rejected without state creation |
| Verification without its required baseline/state | Rejected |
| Two verified increments across processes, then third reservation | First two pass; third rejected with count 2 |
| Two unapplied reservations reconciled across restarts, then third attempt | Attempts remain consumed; third rejected |
| Restart after applied pending increment, then next reservation | Proof persisted and next reservation succeeds |
| Malformed JSON state, incomplete `{}` state, negative attempt count | Rejected without changing state |
| Resume with missing state | Rejected without creating replacement state |
| Stale baseline before actuator | Rejected without changing data |
| A second reservation while one is pending | Rejected without changing state |
| Valid no-op input | Succeeds without consuming an attempt |

Both installed helper directories match the final source byte-for-byte. All 169
bootstrap-managed file hashes still match the consumer receipt. `README.md` and
`AGENTS.md` are unchanged. The only additional nonmanaged files are the requested
script, acceptance suite, actuator skill, and `.labels-loop/state.json`.

Final retained artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| `labels-loop.mjs` | `162a6305aa1a39e5bf107ac0a98599a896e5fbc48fe09bd7a45adf054f127d05` |
| `tests/labels-loop.test.mjs` | `087a3b3c4a76f4785ad3881ed5d405a1ad0aa8bc615145cb0b680a6db84d3876` |
| `.kiro/skills/trim-label/SKILL.md` | `94c77d7eacc00a210793fc4c01cb431fa07e0ff690213091a78eecc8598aba6b` |
| `.labels-loop/state.json` | `25d752050080abbebc84a604de3cf9be1aaf789f5794d7f06b3e06b8a167cb0f` |
| `data/labels.json` | `aaf8c94c420cccc494381e765b2d5ce14e3c49cae134e9142fa6c24c2a6942e5` |

## Integration and limits

The parent refreshed the two curated bundle manifests for the final source
changes. The lane did not modify shared generated assets, upstream identity or
provenance, product command routes, release docs, or existing broad tests.
`git diff --check` passes for the owned source/report changes. No phrase-matching
unit test was added for the prose; acceptance uses actual generated behavior.

This establishes the repaired method on the bounded local fixture and its
independent adversarial cases. It does not promise every model generation will
be correct, validate simultaneous competing controllers, or establish hosted
workflow, publication, credential-confinement, or broad semantic-routing
acceptance. Those require their own applicable contract and checks. No native
model session remains running.
