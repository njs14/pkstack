# Bounded Kiro Crew Nightly compatibility smoke

Status: **PASS within the bounded command-surface scope, with a material upstream packaging
limitation**.

This record captures a local command-surface and doctor smoke of the KiroCrew Nightly listed by
the official feed at `2026-09-03T12:02:57Z`. The signed package provenance, installation, public
CLI surface, and dependency diagnostics passed. The smoke did not open a PK-Stack repository
through Crew, exercise a PK-Stack skill, run a verified goal, or test Crew task orchestration. It
is therefore compatibility evidence, not a PK-Stack workflow pass or release gate.

## Source and installation provenance

- Official feed: `https://updates.crew.kiro.dev/feed/nightly/latest-mac.yml`
- Feed observation: `2026-09-03T12:02:57Z`
- Feed SHA-256: `0274b7299b26c292cb173685a546598f34f10e7af167f64dfe3a7fa2e4aef4f9`
- Advertised version: `0.6.0-nightly.20260903t061110`
- Advertised DMG size: `632801756` bytes
- Advertised SHA-512, base64:
  `gTmWRYO0v+14S5Qzl6lZeAYSEAYh6JplDiknQAVo765quJim7fY/9Ac7f28mr55OfsDBSgEMnkoQwF9darI2og==`
- DMG URL:
  `https://download.crew.kiro.dev/desktop/nightly/0.6.0-nightly.20260903t061110/KiroCrew.dmg`
- Downloaded DMG SHA-256:
  `d11e6e50925ae2cb1c824465352063664a492fe799789f4a612b58d2c1cca4fa`

The mounted artifact had bundle identifier `com.amazon.kiro.crew` and the exact advertised
version. Deep/strict code-signature verification passed. Gatekeeper accepted a notarized
Developer ID from `AMZN Mobile LLC`, Team ID `94KV3E626L`; the signature timestamp was
`2026-09-03 02:39:14`. Installation proceeded only after confirming that no KiroCrew process was
running. The prior `0.6.0-nightly.20260902t061347` application remains recoverable at:

```text
/Users/noahsutter/.Trash/KiroCrew Nightly 0.6.0-nightly.20260902t061347.app
```

## Bounded command-surface smoke

The normalized command boundary was:

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/noahsutter/.local/bin/kirocrew --version
PYTHONDONTWRITEBYTECODE=1 /Users/noahsutter/.local/bin/kirocrew --help
PYTHONDONTWRITEBYTECODE=1 /Users/noahsutter/.local/bin/kirocrew doctor
```

`--version` returned exact version `0.6.0-nightly.20260903t061110`, `--help` completed
successfully, and `doctor` concluded `Kiro Crew is ready!`. Doctor observed Kiro CLI `2.21.0`, a
working Kiro login and runtime, required dependencies, and MCP tools. The Crew gateway was not
running.

Doctor also reported non-passing or optional environment observations: stored older defaults, a
Homebrew AWS executable excluded by Crew's trusted-path policy, no cgroup v2 on macOS, no selected
project directory, an absent optional ACP backend, and optional channels or integrations that were
not configured. These observations did not prevent the bounded doctor result, and this campaign
does not reinterpret them as PK-Stack coverage.

The existing global Crew configuration names `acp` as its provider. That is Crew-owned transport
configuration. It does not change PK-Stack's ordinary entrypoint, which remains Kiro IDE
chat/Agent Focus or an interactive `kiro-cli --v3` session, and it does not endorse a
user-launched ACP host as the default PK-Stack path.

## Upstream packaging finding and recovery

Invoking the Nightly CLI rewrote bundled Python `.pyc` files inside the signed application even
with `PYTHONDONTWRITEBYTECODE=1`, invalidating the application's signed seal after the smoke. This
is a material upstream packaging limitation rather than evidence of a PK-Stack source mutation.

The post-smoke application was moved recoverably to:

```text
/Users/noahsutter/.Trash/KiroCrew Nightly 0.6.0-nightly.20260903t061110 post-smoke.app
```

A fresh copy of the exact verified Sep. 3 bundle was then restored to
`/Applications/KiroCrew Nightly.app`. Its version, deep signature, and Gatekeeper acceptance were
re-verified after restoration, and the CLI was not invoked again. A future CLI invocation may
reproduce the signed-seal mutation until upstream packaging prevents writes inside the signed
bundle.

## Evidence boundary

The repository worktree was at commit `f6e3440c6a6c6faab1030501baa3c193535207e1`, tree
`f8f28bc5142e6ac67c06dfe0f7a60a9b9fdb752d`, when this record was prepared, and the worktree was
clean before the record edits began. That identity is
context only: the smoke exercised the external KiroCrew installation, not an immutable archive of
that PK-Stack tree. No Crew GUI, project trust flow, task runner, compaction/reinjection path,
channel, schedule, gateway lifecycle, PK-Stack skill, native Spec bridge, or current-session
verified-goal behavior was exercised. No model turn or explicit secret/API key was supplied;
doctor did inspect the existing Kiro login status.

Terminal status: **command-surface and doctor smoke passed, with a material upstream packaging
limitation; PK-Stack Crew end-to-end remains untested**. The machine-readable companion is
[`kirocrew-nightly-smoke-campaign.json`](kirocrew-nightly-smoke-campaign.json).
