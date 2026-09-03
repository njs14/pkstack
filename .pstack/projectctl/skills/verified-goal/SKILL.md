---
name: verified-goal
description: Work toward a concrete objective in the current Kiro agent session and require deterministic projectctl verification before reporting success. Use for multi-step implementation, repair, migration, or refactoring with an executable acceptance check.
compatibility: Kiro IDE 1.x and Kiro CLI v3; Kiro Crew compatible; Kiro Web supported by design but untested; initialized PK-Stack workspace with projectctl.
---

# Run a verified goal

Stay in the current Kiro agent session on the selected surface. Do not start
another Kiro session or a parallel user session. Kiro Crew may own the session
and use ACP internally, but it remains optional and does not change the goal
contract. Native sub-agents may help with bounded diagnosis, but the primary
agent owns the goal and its evidence.

Treat the request text that activated this skill as the objective and acceptance context.

This is a PROVE + DO workflow. Start from the stored feature/spec verifier and its executable
evidence; do not run broad KNOW retrieval by default. Escalate to one bounded, targeted knowledge
query only when failure evidence exposes a concrete architecture, decision, concept, or operations
question that the feature record and its related links cannot answer. Record that reason.

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
3. Inspect `.kiro/specs/` as well as `<runner> feature list --output json`. A matching native Spec
   package is planning provenance, not proof. It is ready to bind only when it has non-empty
   `requirements.md` or `bugfix.md`, `design.md`, and `tasks.md`.
4. Prefer an existing published feature verifier after inspecting `<runner> feature show <slug>
   --output json`. If the request continues a matching native spec, bind that spec to the feature
   so the goal retains both proven feature and native planning provenance:

   ```text
   <runner> goal bind-spec <spec-name> --feature <slug> --output json
   ```

   Reusing an identical bridge is idempotent. Never pass `--overwrite` until the existing bridge
   and replacement have both been reviewed.
5. When no feature applies, use `create-verification-skill` or `maintain-verification-skill` to
   establish one. Only when a feature map would add no useful reusable behavior contract may a
   reviewed repository test, build, lint, type-check, or domain command be bound directly with
   `<runner> goal bind-spec <spec-name> --command "<command>" --output json` or used as an explicit
   goal command.
6. Do not create a fake spec directory, edit native requirements/design/tasks merely to make the
   bridge pass, infer Quick Spec provenance from filenames, or treat completed task checkboxes as
   executable evidence. Do not weaken a verifier to obtain a pass. If no checkable predicate can
   be established, ask one targeted question rather than claiming success.

Start new state with exactly one verifier:

```text
<runner> goal start "<objective>" --feature <slug> --max-attempts 4 --output json
<runner> goal start "<objective>" --spec <spec-name> --max-attempts 4 --output json
<runner> goal start "<objective>" --command "<verification command>" --max-attempts 4 --output json
```

Use `--spec` when a matching native package and bridge exist. That bridge should normally point to
the published feature verifier; it does not replace Kiro's planning artifacts or introduce another
task runner. If a native spec exists but has no executable bridge, stop and bind/prove its
verification contract instead of silently dropping its provenance.

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
