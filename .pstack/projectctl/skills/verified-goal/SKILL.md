---
name: verified-goal
description: Work toward a concrete objective in the current Kiro CLI v3 session and require deterministic projectctl verification before reporting success. Use for multi-step implementation, repair, migration, or refactoring with an executable acceptance check.
compatibility: Kiro CLI v3; an initialized PK-Stack workspace with projectctl.
---

# Run a verified goal

Stay in the current interactive Kiro session. Do not start another Kiro session or a parallel user session. Native sub-agents may help with bounded diagnosis, but the primary agent owns the goal and its evidence.

Objective and acceptance context: $ARGUMENTS

## Resolve the controller once

Use `.pstack/bin/projectctl` for the entire loop. It is the bootstrap-managed
entrypoint and has a locked repo-local runtime. Do not select `./projectctl`:
bootstrap deliberately preserves that name when the host project already owns
it. Do not use ambient `uv run projectctl` package resolution.

If the internal runner is unavailable, stop with the exact missing prerequisite
and direct the user to `/setup-pstack`. Do not emulate goal state in prose or
create an ad hoc state file.

## Establish the acceptance contract

1. Run `<runner> goal status --output json` before starting anything.
   A structured `no goal state exists` error means there is no active state and
   a new goal may be started.
2. If another objective is active, do not overwrite or clear it. Continue only when it is the same objective and the stored verifier remains valid; otherwise report the conflict.
3. Prefer an existing feature verifier after inspecting `<runner> feature list --output json` and `<runner> feature show <slug> --output json`.
4. When no feature applies, identify one explicit, repeatable verification command from the repository's actual test, build, lint, type-check, or domain validation interface.
5. Do not weaken a verifier to obtain a pass. If no checkable predicate can be established, ask one targeted question rather than claiming success.

Start new state with exactly one verifier:

```text
<runner> goal start "<objective>" --feature <slug> --max-attempts 4 --output json
<runner> goal start "<objective>" --command "<verification command>" --max-attempts 4 --output json
```

Before the first verification attempt in every skill invocation, display
`goal.contract.display` and its provenance from the latest status or start
response to the user. This applies whether the goal was just created or was
already active when the invocation began. The shell approval UI is not a
substitute for showing the exact stored predicate in the workflow.

Never include credentials or other secrets in the objective or stored command.

## Iterate

For every attempt:

1. Read the current status and evidence.
2. Make the smallest evidence-backed change likely to advance the stored predicate.
3. Run `<runner> goal verify --output json`. This command owns the attempt increment and the transition to `active`, `passed`, or `exhausted`; do not duplicate those transitions manually.
4. On `passed`, inspect `<runner> goal status --output json` and report completion with the exact verifier and result.
5. On `active`, diagnose the new evidence. Discard a non-advancing approach instead of repeating the same-shaped change. Use `<runner> goal tripwire --output json` only as a read-only advisory signal.
6. On `exhausted`, stop and report the genuine dead end, attempts, last evidence, and next viable choices.

`goal verify` exits non-zero while the verifier is failing. That is expected for `active` and `exhausted`; read the JSON payload and follow its stored status instead of treating the shell exit alone as a tool failure.

Do not automatically run `goal resume`, add attempts, or run `goal clear --force`. Use `<runner> goal resume --add-attempts <N> --output json` only when the user explicitly extends an exhausted goal. Clear state only on an explicit request after preserving the final evidence.

## Completion standard

A plausible explanation, a clean diff, a sub-agent opinion, or an external review is not a pass. Completion requires `goal verify` to return `passed` for the stored executable verifier. Report any checks that were not run or any environment limitation separately.
