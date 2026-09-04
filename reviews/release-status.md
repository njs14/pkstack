---
release: "0.3.0"
status: candidate
version_authority: powers/pk-stack/plugin.json
---

# PK-Stack release status

The current source targets **0.3.0**. It is not released until the exact reviewed
main commit is tagged and the release workflow succeeds.
[v0.2.0](https://github.com/njs14/pk-stack/releases/tag/v0.2.0) remains the
previous published release.

## Cleanup candidate

The cleanup started from `af757c76dfe2c9163a919baee645c66e6c207d0f`.
It removes schema-1 compatibility and duplicate controller-cache assets,
fixes verifier cancellation and evidence corrections, repairs the updater,
and replaces duplicated onboarding with an executed README walkthrough.

The [cleanup report](cleanup-validation.md) records the current checks and
limitations. Local gates passed 811 Power tests, 128 repository-policy tests,
and 17 JavaScript tests, plus lint, formatting, types, Actionlint, and ShellCheck.
Independent bounded runtime and pipeline reviews accepted the implementation.
Real Kiro CLI v3 sessions passed both the direct-command and native Quick Spec
handoffs, with recorded failures before repair. [PR #13](https://github.com/njs14/pk-stack/pull/13)
is the release candidate; merge and the live updater campaign remain pending.

## Release requirements

- Package metadata and both lockfiles match `plugin.json`.
- Lint, formatting, type checks, package tests, repository guards, Actionlint,
  and ShellCheck pass.
- Generated controller/assets match a reviewed Power-local setup.
- The fresh-consumer README walkthrough records failure, repair, and pass.
- Interactive Kiro CLI v3 checks retain normal current-session behavior and
  explicit permissions.
- Independent review has no material unresolved finding.
- The private PR passes its checks before merge; the release tag resolves to
  the reviewed main commit.

IDE Power import currently lacks a completed UI test. Kiro Web remains
untested; Crew is an optional compatibility target. These limits must stay
visible in the release report, not be inferred away from CLI results.

## Historical evidence

Earlier implementation and review records remain under
[historical/pre-v0.2](historical/pre-v0.2/). They retain their original scope.
The [Floci integration lab](https://github.com/njs14/pk-stack-floci-lab)
is a separate private consumer repository and is not included in the Power.
