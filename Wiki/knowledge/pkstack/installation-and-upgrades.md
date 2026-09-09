---
type: Guide
title: Installation, controller ownership, and upgrades
description: Official Kiro Power installation, workspace initialization, controller ownership, and reviewed upgrades.
tags: [pkstack, installation, upgrades, ownership]
---

# Installation, controller ownership, and upgrades

## Install through Kiro

Use **Powers → Add Custom Power → Import power from GitHub** with
`https://github.com/njs14/pkstack/tree/main/powers/pkstack`. The directory component
is required: the repository root contains maintainer material, while the Power
manifest and skills live in `powers/pkstack/`.

For local import, clone the public repository over HTTPS without a GitHub account,
review `powers/pkstack/`, and select that directory through **Import power from a
folder**. Both paths follow the [official installation guide](https://kiro.dev/docs/powers/installation/).
CLI v3 [detects IDE-installed Powers](https://kiro.dev/docs/cli/v3/new-features/#powers-auto-pickup).
Install from the reviewed Power folder or extracted release archive.

IDE 1.0.437 can accept the repository-root URL, install no Power files, and still
report success. If the details show **No description available** and no skills,
uninstall the empty entry and import the full directory URL. Updating an entry
retains its source path. Check the installed content and visible skills instead
of relying on the success notification.

The [installation metadata contract](../../features/pkstack-power-installation.md)
checks the actual package fields, compact inline image, and README URLs. The
[September 9 native observation](../../../docs/kiro-v3-compatibility.md#september-9-remote-power-installation-and-display)
records the incorrect import, corrected remote package, and bounded display
preview separately from that executable package check.

After installation, invoke `/pkstack-setup` where Kiro exposes the Power's skill
to initialize the application workspace. Review its preview before applying
changes. Select the workspace `pkstack` agent afterward; Power registration alone
does not establish that its skills are attached to the active agent.

The project-local `.pkstack/bin/projectctl` runs explicit operational commands.
The public launcher and asset-bearing wheel path have been retired. Setup runs
from the loaded Power, while the installed controller preserves the caller's
application environment for verification.

## Consumer package boundary

The current Power uses `plugin.json`. Its [POWER.md compatibility file](../../../powers/pkstack/POWER.md)
supplies display fields because IDE 1.0.437 still reads that file for its details
page, even when the agent uses Agent Plugins loading. The metadata matches the
manifest; a compact inline JPG renders under the details view's content security
policy. Kiro also accepts a standalone legacy `POWER.md`, and does not document
`POWERS.md`. `dev.kiro` is Kiro's reverse-domain
extension namespace. It is required by this package's steering layout, not a
place for development-only files. The [Power compatibility guide](../../../powers/pkstack/docs/kiro-v3-compatibility.md)
explains the format and dated support limits.

User guides live in `powers/pkstack/docs/`. Setup catalogs and integrity manifests
live in `metadata/`, while upstream attribution and adaptation records live in
`provenance/`. These remain packaged because bootstrap validates the complete
skill bundle and consumers need its attribution. Runtime source, templates, and
locks remain self-contained. The root development project adds test and static
analysis tools without shipping them in the Power's dependency graph. README
artwork and detailed compatibility campaigns live in repository `docs/`.


## Retained launcher evidence

Historical launcher reviews below describe the versions they tested. The
[previous-controller receipt](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/uvx-entrypoint/previous-controller-compatibility.json)
recorded a newer launcher calling version and doctor against a 0.4.3 controller
without changing managed files. It does not establish current compatibility or
an installation path for this release.

## Upgrade without discarding project ownership

Invoke `/pkstack-setup` from the reviewed installed Power and review its pending-update preview before approving managed changes.
Upgrade updates managed files only when they still match the previous receipt. Changed managed
files require reconciliation; stale managed files are not automatically deleted. Keep a rollback
copy with the receipt, native Specs, goals, Wiki, settings, and user changes. Never remove entire
Wiki or Kiro directories to make a preview green.

Receipt schema 2 and goal schema 3 require a reviewed
[clean reinstall](../../../powers/pkstack/docs/usage.md#clean-reinstall) for older state.
`--update-managed` is not a migration bypass. The 0.4 knowledge transition retired
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
metadata needed by uvx resolution. A warm local cache hid the failure. The historical correction used isolated empty uv tool/cache directories in the
packaging lane with its existing network allowlist. A successful warm-cache install is insufficient evidence for an offline first install.


## Diagnose onboarding by the boundary that failed

The [0.4.2 first-task campaign](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/onboarding-042/README.md) cloned a source path with
spaces, captured it before entering a different target with spaces, and verified preview,
installation, doctor, and an unchanged second setup. A native session then repaired only the
implementation against the stored failed verifier. The observer neither supplied that repair nor
created a passing attempt. Fresh paths did not imply a fresh account or empty cache; that claim
needed the later [cold-cache walkthrough](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/uvx-entrypoint/README.md#hosted-ci-remediation).

The [launcher review](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/uvx-entrypoint/grok-review.md) used a real application
virtualenv with a dependency unavailable to the controller. It also checked cancellation and
previous-controller compatibility. That implementation separated launcher selection, controller execution, and the
application verifier environment. Removing every matching PATH entry would have
damaged a legitimate caller entry; that launcher removed only its own leading
environment entry. The current project wrapper must still preserve the caller environment.

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
| [README.md](../../../README.md) | Current product entrypoint follows official local-folder Power installation and links workspace initialization and first-task guidance. |
| [powers/pkstack/README.md](../../../powers/pkstack/README.md) | Power-local entrypoint uses the same official folder installation flow with package-relative documentation links. |
| [powers/pkstack/docs/usage.md](../../../powers/pkstack/docs/usage.md) | Install through Kiro, initialize the workspace with the installed setup skill, use the project-local controller, and review receipt-aware managed updates. |
| [powers/pkstack/docs/first-task.md](../../../powers/pkstack/docs/first-task.md) | Use a disposable intentionally failing account fixture, record the failure, preserve tests, and let native Kiro repair the implementation before stored verification. |
| [powers/pkstack/docs/upgrade-0.3.md](https://github.com/njs14/pkstack/blob/e6cd3e0ab3d1d24c3e22df3ef8524e79244d83be/powers/pkstack/docs/upgrade-0.3.md) | Legacy namespace transition uses a separate clean checkout and preserves rollback evidence; receipt-aware refresh cannot bypass incompatible installation boundaries. |
| [powers/pkstack/docs/upgrade-0.4.md](https://github.com/njs14/pkstack/blob/e6cd3e0ab3d1d24c3e22df3ef8524e79244d83be/powers/pkstack/docs/upgrade-0.4.md) | The 0.4 transition retires okn, preserves user-owned Wiki/Specs, and distinguishes local validation from runtime-dependent bounded retrieval. |
| [powers/pkstack/examples/verified-goal-demo/README.md](../../../powers/pkstack/examples/verified-goal-demo/README.md) | The account-ID example is intentionally broken and its narrow verifier is a demonstration predicate, not general application acceptance. |
| [reviews/onboarding-042/README.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/onboarding-042/README.md) | The 0.4.2 CLI campaign recorded failure then native repair/pass at 2 of 4 with unchanged tests and paths containing spaces; existing account/cache state limits first-install claims. |
| [reviews/uvx-entrypoint/README.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/uvx-entrypoint/README.md) | Launcher/controller separation and explicit upgrades were exercised with real wheels; cold-cache hosted walkthrough failures required isolated resolution tests rather than runtime changes. |
| [reviews/uvx-entrypoint/grok-review.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/uvx-entrypoint/grok-review.md) | Read-only review of 9e9f327 distinguished launcher version from controller version, exact current-directory selection, receipt ownership from trust, and inherited application dependencies. |
| [reviews/uvx-entrypoint/grok-followup.md](https://github.com/njs14/pkstack/blob/9bb1cbbb52552f95f7ccc61e14c44283e526c80d/reviews/uvx-entrypoint/grok-followup.md) | Test-only f218172 correction addressed offline uvx resolution missing registry metadata despite locked sync; warm local caches had hidden it. |
