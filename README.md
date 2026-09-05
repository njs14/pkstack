# PKStack & friends

<p align="center">
  <img src="powers/pkstack/assets/banner.png" alt="PKStack: From plan to proof. A scholarly potato ghost with an OKF knowledge tree in the background." width="600">
</p>

Poteto’s pstack workflows, adapted for Kiro, with a few friends along for the ride.

## What it does

Plan changes with Kiro’s native Specs, work through implementation and review,
and run a stored check before calling the task done. PKStack adds reusable
workflows, a local `projectctl` command, and a source-controlled Wiki for
feature contracts and project knowledge.

![Kiro plans and executes; PKStack guides the work; projectctl checks the result.](powers/pkstack/docs/artifacts/pkstack-architecture.png)

## Sources

- **Poteto / pstack:** engineering workflows, verification, and principles.
- **HumanLayer:** visual explanations and bounded automation design.
- **Matt Pocock:** instructions that agents can find and follow.
- **Archify and OKF/okn:** diagrams and project knowledge.

The [sources guide](powers/pkstack/docs/curated-skills.md) explains what we
ported, what we changed for Kiro, and what we left out.

## Why

Keep the next session from rediscovering how to run the project, what success
looks like, and why a decision was made. Your Kiro model and effort stay yours.

## Install

You need Kiro, Python 3.11+, `uv`, and GitHub access to this private repository.

```sh
git clone https://github.com/njs14/pkstack.git
```

1. In Kiro IDE, choose **Powers → Add Custom Power → Import power from a folder**
   and select `pkstack/powers/pkstack`.
2. Review the Power. Open your project and run `/pkstack-setup`; approve the
   previewed changes.
3. Select the workspace `pkstack` agent, then use `/pkstack <task>`.

[CLI setup and commands](powers/pkstack/docs/usage.md) ·
[Try a failing task](powers/pkstack/docs/first-task.md) ·
[How it works](powers/pkstack/docs/architecture.md)

CLI v3 and the IDE are primary; Crew is optional and Web is untested.
[Validation and release status](reviews/release-status.md) records the exact scope.
[Maintenance](powers/pkstack/docs/upstream-control-loop.md) is separate from installation.

Apache-2.0. [Third-party notices](powers/pkstack/THIRD_PARTY_NOTICES.md).
