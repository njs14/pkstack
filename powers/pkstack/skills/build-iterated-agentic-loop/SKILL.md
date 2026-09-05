---
name: build-iterated-agentic-loop
description: Build a bounded, observable, repo-local agent loop from locally runnable sensor, controller, Kiro actuator, validation, memory, and flow-control components.
---

# Build an iterated agentic loop

Treat the request text that activated this skill as the loop objective. Stay in the current Kiro
session. Do not introduce ACP as the normal path, misrepresent `/pkstack-verified-goal` as a
native Kiro feature, or require a second model vendor's API key.

Read `references/control-loop.md` before designing the loop and
`references/github-actions-profile.md` before changing GitHub Actions.

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
candidate per loop and a bounded attempt count.

Completion criterion: the contract can be read without the workflow and names every authority and
trust boundary.

## 3. Make every component local first

Implement the sensor and controller as version-controlled local commands. Make the actuator a
repo-local Kiro skill with the smallest write scope that can complete its job. Store only durable
steering in a short version-controlled memory file; keep transient errors in run evidence.

Run sensor, controller, actuator, and validation separately before CI orchestration. Never make CI
the only way to diagnose the loop.

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

Format the result with `references/response-template.md`. Never describe a candidate or historical
report as a current passing verdict.
