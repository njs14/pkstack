---
type: Guide
title: Installation, controller ownership, and upgrades
description: How reviewed package sources, uvx, project controllers, and receipt-aware upgrades fit together.
tags: [pkstack, installation, uvx, upgrades, ownership]
---

# Installation, controller ownership, and upgrades

## Choose a source and a project separately

PKStack supplies engineering workflows for Kiro, a project-local command runner, and retained
knowledge. The source Power is `powers/pkstack/`. A reviewed checkout or local wheel supplies the
installer; the target is the application repository where Kiro will work. Capture the absolute
source path before changing directories. Quote paths, including paths containing spaces. The
documented uvx commands explicitly request Python `>=3.11`; the bootstrap shim's older-Python
guard is a separate, intentional compatibility boundary.

Set `PKSTACK_PACKAGE` to that reviewed checkout's Power directory or local wheel. From the target:

```sh
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack setup --dry-run --output json
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack setup --output json
uvx --python '>=3.11' --from "$PKSTACK_PACKAGE" pkstack doctor --output json
```

Review the preview before applying it. No global tool install or package-registry publication is
needed. Installed native skills still need discovery under the selected workspace agent. In CLI,
use `/agent swap pkstack` and inspect `/config skills`; in IDE, select the workspace agent. A Power
being listed is not evidence that its skills are attached to the active agent.

## The launcher is not the installed controller

The inspected [launcher](../../../powers/pkstack/src/pkstack/launcher.py) handles `setup` and explicit
`upgrade` using its own reviewed package. Other commands execute the selected project's
`.pkstack/bin/projectctl`. Downloading a newer launcher does not silently upgrade a project.
`pkstack --version` reports the launcher version; `pkstack version` reports the installed
controller version. `--project PATH` must precede the command. By default the project is exactly
the current directory, with no ancestor search and no automatic creation of a missing directory.

Before forwarding, the launcher checks the executable wrapper bytes and required runtime receipt
entries. The receipt records local ownership and hashes; it is not a signature or proof that a
package source is trustworthy. Controller environment isolation preserves the application's
interpreter and dependencies for its verifier. Keep launcher installation, controller installation,
and application dependencies distinct when diagnosing import failures.

The [previous-controller receipt](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/uvx-entrypoint/previous-controller-compatibility.json)
records a newer launcher calling version and doctor against a 0.4.3 controller without changing
managed files. This is bounded compatibility evidence, not a promise for every old controller.

## Upgrade without discarding project ownership

Preview `pkstack upgrade --dry-run --output json` from an explicitly selected reviewed package.
Upgrade updates managed files only when they still match the previous receipt. Changed managed
files require reconciliation; stale managed files are not automatically deleted. Keep a rollback
copy with the receipt, native Specs, goals, Wiki, settings, and user changes. Never remove entire
Wiki or Kiro directories to make a preview green.

The 0.3 namespace transition requires a separate clean checkout for installations using the
legacy namespaces; `--update-managed` is not a migration bypass. The 0.4 knowledge transition retired
`okn` and `--require-okn`; local metadata/link validation remains available independently of Kiro
retrieval. Setup does not reinterpret old goals, migrate an arbitrary Wiki, or create passing
evidence from historical results. After a clean refresh, check version, doctor, feature validation,
knowledge validation and status, and a second preview with no pending updates.

## First-task evidence and limits

Use the disposable account-ID example: preserve its original tests, record the genuine initial
failure, repair only the implementation in the same native Kiro conversation, then run the stored
verifier again. A passing fixture shows that predicate, not arbitrary application correctness.
The 0.4.2 onboarding campaign recorded failure and pass at attempts 1 and 2 of 4 with unchanged
tests, paths containing spaces, and one-time tool approvals. It retained existing account state
and caches, so it did not establish empty-cache or fresh-account onboarding.

Later uvx walkthrough CI exposed that gap: `uv sync` had cached distributions but not all registry
metadata needed by uvx resolution. A warm local cache hid the failure. The corrected walkthroughs
use isolated empty uv tool/cache directories in the packaging lane with its existing network
allowlist. A successful warm-cache install is insufficient evidence for an offline first install.


## Diagnose onboarding by the boundary that failed

The [0.4.2 first-task campaign](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/onboarding-042/README.md) cloned a source path with
spaces, captured it before entering a different target with spaces, and verified preview,
installation, doctor, and an unchanged second setup. A native session then repaired only the
implementation against the stored failed verifier. The observer neither supplied that repair nor
created a passing attempt. Fresh paths did not imply a fresh account or empty cache; that claim
needed the later [cold-cache walkthrough](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/uvx-entrypoint/README.md#hosted-ci-remediation).

The [launcher review](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/uvx-entrypoint/grok-review.md) used a real application
virtualenv with a dependency unavailable to the controller. It also checked cancellation and
previous-controller compatibility. Use these boundaries when diagnosing an import failure: the
launcher selects the package, the project wrapper owns forwarding, and the application supplies
its own verifier environment. Removing every matching PATH entry would damage a legitimate caller
entry; the reviewed launcher removes only its own leading environment entry.

Input delivery is another boundary. One onboarding probe submitted only the skill name because
terminal completion separated it from the request; it was cancelled before implementation and
remained a failed attempt. The successful run submitted the complete inspected request. Similarly,
a prompt menu opening did not prove saved-request creation or expansion: a purported details
command became an ordinary model request. Keep the direct first-task path usable without those
unverified conveniences. The [command audit](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/cli-native-command-audit/README.md)
adds observed agent and skill diagnostics without claiming that agent hot reload proves skill hot
reload or a complete installation.

## Source-specific retained knowledge

These summaries describe what is retained from each source. Historical observations keep their
original candidate and scope; they are not fresh verification of this checkout.

| Source | Retained guidance or bounded observation |
| --- | --- |
| [README.md](../../../README.md) | Current product entrypoint: explicit reviewed package source, CLI/IDE setup, DO/PROVE/KNOW roles, and links to first-task and recovery guides. |
| [powers/pkstack/README.md](../../../powers/pkstack/README.md) | Power-local entrypoint preserves the same installation contract with package-relative asset and documentation links. |
| [powers/pkstack/docs/usage.md](../../../powers/pkstack/docs/usage.md) | Source selection is distinct from target selection; uvx forwards project operations to the installed controller, explicit upgrades reconcile receipts, and native agent discovery must be checked. |
| [powers/pkstack/docs/first-task.md](../../../powers/pkstack/docs/first-task.md) | Use a disposable intentionally failing account fixture, record the failure, preserve tests, and let native Kiro repair the implementation before stored verification. |
| [powers/pkstack/docs/upgrade-0.3.md](../../../powers/pkstack/docs/upgrade-0.3.md) | Legacy namespace transition uses a separate clean checkout and preserves rollback evidence; receipt-aware refresh cannot bypass incompatible installation boundaries. |
| [powers/pkstack/docs/upgrade-0.4.md](../../../powers/pkstack/docs/upgrade-0.4.md) | The 0.4 transition retires okn, preserves user-owned Wiki/Specs, and distinguishes local validation from runtime-dependent bounded retrieval. |
| [powers/pkstack/examples/verified-goal-demo/README.md](../../../powers/pkstack/examples/verified-goal-demo/README.md) | The account-ID example is intentionally broken and its narrow verifier is a demonstration predicate, not general application acceptance. |
| [reviews/onboarding-042/README.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/onboarding-042/README.md) | The 0.4.2 CLI campaign recorded failure then native repair/pass at 2 of 4 with unchanged tests and paths containing spaces; existing account/cache state limits first-install claims. |
| [reviews/uvx-entrypoint/README.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/uvx-entrypoint/README.md) | Launcher/controller separation and explicit upgrades were exercised with real wheels; cold-cache hosted walkthrough failures required isolated resolution tests rather than runtime changes. |
| [reviews/uvx-entrypoint/grok-review.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/uvx-entrypoint/grok-review.md) | Read-only review of 9e9f327 distinguished launcher version from controller version, exact current-directory selection, receipt ownership from trust, and inherited application dependencies. |
| [reviews/uvx-entrypoint/grok-followup.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/uvx-entrypoint/grok-followup.md) | Test-only f218172 correction addressed offline uvx resolution missing registry metadata despite locked sync; warm local caches had hidden it. |
