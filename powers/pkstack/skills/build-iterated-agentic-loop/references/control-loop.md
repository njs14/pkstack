# Control-loop contract

Use the smallest real loop:

```text
set point -> compare <- sensor <- repository + disturbances
                 |
                 v
             controller -> actuator -> candidate -> dampener -> repository
```

The sensor measures; it does not mutate. The controller selects the next bounded unit and records
why. The actuator changes only its assigned scope. The dampener independently rejects regressions,
stale evidence, unauthorized paths, and unbound verdicts. A feedback file contains durable steering,
not secrets, one-run logs, or duplicated policy.

## Increment and attempt proof

Record the pre-actuation baseline, selected unit, and consumed attempt together before allowing a
write. For commands invoked in separate processes, retain this record in run state or use an
existing trusted supervisor. Keep it outside actuator write scope. Reserve at most one pending
increment, and reject a second reservation while it is unresolved. If a process stops after
reservation, do not assume no write happened or grant an uncounted retry. A resumable contract must
reconcile the pending baseline and current candidate before allowing another increment.
Persist the reconciliation result: a verified or proven-unapplied increment must leave the pending
slot before selecting more work, while its consumed attempt remains recorded. Reject malformed
state values as well as malformed JSON. An existing but incomplete state object is not a fresh run.

The ordinary verifier must require that record. A matching global set point cannot substitute for
preservation proof. For a one-label trim, select the key from the baseline and require its new value
to equal exactly the baseline value's trim. Require the same key set and identical values for every
other key. The post-edit eligible list may be empty, so it cannot identify the permitted change.
Malformed JSON, wrong container/value types, and empty labels fail validation; a valid input with
no remaining eligible labels is a no-op. Other domains should use their actual input contract.

Exercise the generated implementation, not just its instructions:

- Accept one exact trim; reject a renamed, added, or removed key, a changed unrelated value, a
  non-trim replacement of the selected value, and more than one changed value.
- Accept one verified increment when another padded label remains, while reporting incomplete
  global work. Do not reject valid progress merely because the set point needs another increment.
- Reject verification without its required baseline, and refuse actuation on stale selection or
  invalid input. Test malformed JSON and invalid labels even when the eligible list is empty.
- Consume failed attempts as well as successful attempts; exhaust the budget across separate
  command invocations and prove the next attempted reservation cannot authorize an actuator.
- If restart support is promised, restart with a pending attempt and after exhaustion; neither may
  reset the budget or silently replace the baseline. Corrupt state must stop the run.

Retain exact commands and outcomes. If writable scope cannot accommodate required run state or
verification evidence, report the conflict instead of delivering a loop with a prose-only bound.

For PKStack's own updater, the set point is that every reviewed upstream pin is current and all
canonical/generated parity is exact. `projectctl upstream check` is the sensor. The controller
selects the lexicographically first complete, reviewable drift and permits at most one candidate.
Kiro with `pkstack-maintain` is the actuator. Secretless verification plus the exact-SHA candidate
workflow is the dampener.
