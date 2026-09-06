---
name: build-iterated-agentic-loop
description: Build a bounded, observable, repo-local agent loop from locally runnable sensor, controller, Kiro actuator, validation, memory, and flow-control components.
---

# Build an iterated agentic loop

Treat the request text that activated this skill as the loop objective. Stay in the current Kiro
session. Do not introduce ACP as the normal path, misrepresent `/pkstack-verified-goal` as a
native Kiro feature, or require a second model vendor's API key.

Use this method to build reusable automation. Use
[`pkstack-verified-goal`](../pkstack-verified-goal/SKILL.md) to complete a task in the current
session. If composing it with this build, bind its verifier to the loop's acceptance test suite,
not the current sample's set point: one successful sample cannot prove a reusable loop. A request to
"keep working until the tests pass" does not itself request a reusable loop. If the control
contract is unresolved, use [`design-control-loop`](../design-control-loop/SKILL.md) first;
reuse its decisions and evidence in step 2. Keep native Kiro Specs as the planning authority.
Creating a local workflow does not authorize enabling a schedule or publishing candidates.

Read `references/control-loop.md` relative to this installed skill directory before designing
the loop, and `references/github-actions-profile.md` before changing GitHub Actions.

For any planning portion, read [`grilling`](../grilling/SKILL.md), reuse settled answers and
open questions, and follow its native handoff and approved-plan capture checkpoint. In native
Plan, keep the contract in conversation and defer all implementation, shell, MCP, file writes,
prototypes, and validation until execution is permitted. An explicit no-write instruction prevails.

## 1. Discover before designing

Inspect the repository's instructions, package manager, validation commands, CI, existing skills,
automation, and security boundaries. Identify an existing golden change if one exists. Do not ask
the user for facts the repository already answers.

Completion criterion: name the local install and validation commands, writable scope, CI
conventions, and the evidence that will establish success.

## 2. Write the control contract

Define these explicitly:

- **set point**: the invariant, threshold, or direction the loop drives toward;
- **sensor**: a stable local command that measures the gap;
- **controller**: a deterministic or narrowly agentic rule selecting one reviewable increment;
- **actuator**: Kiro plus a repo-local skill that applies only that increment;
- **disturbances**: concurrent changes, upstream drift, flaky infrastructure, or generated files;
- **dampener**: the regression or candidate gate that prevents an unproved change from landing;
- **terminal states**: current/no-op, verified candidate, retryable failure, and hard blocker.

Fuse components when that matches reality, but document the fused boundary. Prefer one open
candidate per loop and a bounded attempt count. Name the code or trusted supervisor that enforces
the bound before actuation; emitting `maxAttempts` or stating a limit in prose does not enforce it.

Completion criterion: the contract can be read without the workflow and names every authority and
trust boundary.

## 3. Make every component local first

Write executable acceptance tests for the contract and the reference's negative cases before the
implementation. Give each case isolated input and run state; assertions must not depend on whether
the demonstration fixture is currently padded or already fixed. Record the initial failing suite,
then fix implementation against it. Keep the acceptance meaning fixed during repair.

Implement the sensor and controller as version-controlled local commands. Make the actuator a
repo-local Kiro skill with the smallest write scope that can complete its job. Store only durable
steering in a short version-controlled memory file; keep transient errors in run evidence.

Run sensor, controller, actuator, and validation separately before CI orchestration. Never make CI
the only way to diagnose the loop.

Before permitting an actuator, reserve an attempt and capture the selected unit and pre-actuation
baseline. Separately invoked commands must share authoritative run state; a process-local counter
does not survive the next invocation. Preserve state across restarts only when the contract promises
resumption, and fail closed on missing or invalid state during a resume. A failed actuator consumes
its attempt; observation and a valid no-op do not. Never reset the bound implicitly to retry.

Make baseline preservation part of ordinary increment verification, not an optional flag. Verify
the exact allowed change against the recorded pre-actuation selection, including unchanged keys
and values or paths outside that selection. Never derive permission from the post-edit eligible
list. Report increment verification separately from global completion; a valid small increment can
leave more work. Invalid input must fail before an empty eligible list can mean no-op.

Completion criterion: each component has a documented local invocation and machine-readable output
where it crosses a trust boundary.

## 4. Wire a thin, fail-closed workflow

Use GitHub Actions only as an orchestrator. Pin actions by immutable commit, use a fixed runner,
start with no permissions, grant each job the minimum permissions it needs, and do not persist
checkout credentials. Separate credential-bearing model work from secretless verification and from
the publisher that can write GitHub state. Treat all upstream content and agent output as untrusted
data.

Use only the user's approved Kiro credential for model work. Do not add Claude, OpenAI, Grok,
Copilot, OpenCode, or other paid API secrets. Do not copy an upstream workflow template over a more
restrictive repository policy.

Scheduled runs must no-op when the set point is already met or the one-candidate bound is occupied.
Manual dispatch may re-run observation, but must not bypass proof, scope, or publication gates.

Completion criterion: the workflow invokes the same local components, produces an immutable
candidate, and cannot publish unless secretless verification and the independent candidate gate
bind their verdicts to exact commits.

## 5. Validate the loop

Validate YAML, shell, policy fixtures, failure paths, path confinement, secret confinement, exact
commit binding, no-op behavior, attempt exhaustion, and stale-candidate recovery. Run the full local
gate once after focused tests. If credentials or hosted infrastructure are unavailable, report the
unperformed live smoke separately from deterministic proof.

For every local loop, actually test a valid increment, unchanged data outside its selection,
malformed/invalid input, remaining work after a valid increment, and rejection before an extra
actuator after exhaustion. Use separate invocations to expose counter resets. Test restart recovery
if promised. See the concrete negative cases in `references/control-loop.md`; syntax checks and a
single successful edit do not establish these properties. Apply hosted checks only when a hosted
workflow was selected.

Format the result with `references/response-template.md`. Never describe a candidate or historical
report as a current passing verdict.
