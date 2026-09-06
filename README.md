# PKStack & friends

<p align="center">
  <img src="powers/pkstack/assets/banner.png" alt="PKStack: From plan to proof. A scholarly potato ghost with an OKF knowledge tree in the background." width="600">
</p>

PKStack helps Kiro finish development tasks with a repeatable check: record what
fails, repair the code, and keep the passing result. It also keeps project
instructions and decisions in the repository for later sessions.

## What you get

- **Plan with Kiro.** Keep native Specs, Quick Specs, your selected model, and effort.
- **Check the result.** A local `projectctl` command stores the verification command
  and its failed and passing attempts, so completion has evidence you can inspect.
- **Reuse what you learned.** A source-controlled Wiki keeps executable feature
  records and project knowledge available to future sessions.

![Kiro plans and executes; PKStack guides the work; projectctl checks the result.](powers/pkstack/docs/artifacts/pkstack-architecture.png)

## Install

You need Kiro IDE or Kiro CLI v3, `uv`, a `python3` launcher, and access to this
private repository. The controller requires Python 3.11+; the launcher also works
with the tested macOS Python 3.9 path through `uv`. Initial runtime setup can download
Python and dependencies. See the guide below for prerequisites and preview scope.

Clone the source and save the installer path in this terminal:

```sh
git clone https://github.com/njs14/pkstack.git
cd pkstack
export PKSTACK_POWER="$PWD/powers/pkstack"
```

The **source** contains the installer. Your **target project** is the application
you want Kiro to work on; setup adds workspace assets there.

| Surface | Setup path |
| --- | --- |
| Kiro CLI | Use the terminal setup script from the saved Power source, preview and apply it to your target project, then launch `kiro-cli chat --v3 --agent pkstack` there. No IDE import is required. |
| Kiro IDE | Choose **Powers → Add Custom Power → Import power from a folder**, select the Power folder and choose **Install**, open your target project, and run `/pkstack-setup`. Review its preview, then select the workspace `pkstack` agent. |

Follow the [complete CLI and IDE setup guide](powers/pkstack/docs/usage.md) for the
commands and checks. Once installed, use `/pkstack <task>`.

## See it work

[Try one failing task](powers/pkstack/docs/first-task.md) in a disposable project. Kiro
repairs an account-ID function while its four tests stay unchanged. You inspect
a recorded failure followed by a pass. The guide works with CLI or IDE.

For larger work, [see how planning and verification fit together](powers/pkstack/docs/architecture.md).
CLI v3 and IDE are primary; Crew is optional and Web is untested.
[Validation and release status](reviews/release-status.md) records the exact tested scope.

## Sources

Poteto's pstack supplies engineering workflows, verification, and principles.
HumanLayer adds visual explanations and bounded automation design; Matt Pocock
adds agent-facing writing. Archify supplies diagrams and OKF organizes project
knowledge. The [sources guide](powers/pkstack/docs/curated-skills.md) explains the ports,
changes, and omissions.

[Maintenance](powers/pkstack/docs/upstream-control-loop.md) is separate from installation.
Apache-2.0. [Third-party notices](powers/pkstack/THIRD_PARTY_NOTICES.md).
