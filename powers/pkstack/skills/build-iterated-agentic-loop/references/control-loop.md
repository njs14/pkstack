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

For PKStack's own updater, the set point is that every reviewed upstream pin is current and all
canonical/generated parity is exact. `projectctl upstream check` is the sensor. The controller
selects the lexicographically first complete, reviewable drift and permits at most one candidate.
Kiro with `pkstack-maintain` is the actuator. Secretless verification plus the exact-SHA candidate
workflow is the dampener.
