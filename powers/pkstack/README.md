# PKStack & friends

<p align="center">
  <img src="assets/banner.png" alt="PKStack: From plan to proof. A scholarly potato ghost with an OKF knowledge tree in the background." width="600">
</p>

Poteto’s pstack workflows, adapted for Kiro. This directory is the installable Power.

## What and why

Use Kiro’s native planning, follow repeatable engineering workflows, and check
the result with a repository-local `projectctl`. Keep feature contracts and
project knowledge in the Wiki so later sessions can reuse them.

## Sources

Poteto supplies the core workflows. HumanLayer adds visual explanations and
automation methods; Matt Pocock adds agent-facing writing. Archify handles
diagrams. OKF organizes durable knowledge; `projectctl` retrieves bounded context
through Kiro ACP and validates metadata and local links without a model.
See [what we ported and why](docs/curated-skills.md).

## Install

You need Kiro, Python 3.11+, and `uv`.

1. Import this folder through **Powers → Add Custom Power → Import power from a folder**.
2. Run `/pkstack-setup` in your project and review its preview before writes.
3. Select the workspace `pkstack` agent. Start with `/pkstack <task>`.

[CLI setup and commands](docs/usage.md) ·
[First failing task](docs/first-task.md) ·
[Architecture](docs/architecture.md)

CLI v3 and IDE are primary; Web is untested.
[Validation and release status](https://github.com/njs14/pkstack/blob/main/reviews/release-status.md)
records tested scope. [Maintenance](docs/upstream-control-loop.md) is separate.

Apache-2.0. [Third-party notices](THIRD_PARTY_NOTICES.md).
