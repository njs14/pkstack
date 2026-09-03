# Hosted Kiro runtime canary campaign

This record closes the first hosted proof for the read-only Kiro product/runtime drift canary. It
does not promote a Kiro pin, exercise a model turn, test the IDE or Web GUI, or substitute for the
separate upstream-maintenance lifecycle and final model-council gates.

## Immutable target

- Repository: private `njs14/pk-stack`
- Commit: `7ce09e3dc161965b0cdac01f992e7ec1c89748b0`
- Tree: `f137f8779a54aed751ba1f1d5cbe3f04aadc032b`
- Workflow SHA-256: `d34c1ea3469ece0a869520b74e836dae49c531e6769902e6e0d9eb0f83ab4c0e`
- Canary SHA-256: `f09b066323e615b079f3e09d619aa2a3942ad2e40c3f2891015e7e502e3aace7`
- Canary-test SHA-256: `5d22312b9c127c67e1364010210d04cac25ccadadf27bad1c9066ee10ca14762`

## Hosted result

[GitHub Actions run 33743033801](https://github.com/njs14/pk-stack/actions/runs/33743033801)
completed successfully from `main` on 2026-09-03. Job `100609118832` ran for 39 seconds. Every
named step passed, including hardened networking, default-branch refusal, immutable checkout,
secretless runtime/agent probing, authenticated model inventory, final pin enforcement, and
cleanup. No artifact was uploaded.

The gate observed:

- stable CLI `2.21.0`;
- archive SHA-256 `6eccb46617a84690fc892219f264f7617312761c9a3d7e38cc47a0e2ab0152b7`;
- archive size `536335872` and manifest SHA-256
  `1903a24b034424fe5d74bc16f9b01265cdf5491bcce7d6354b46b21f4c3a67af`;
- exact schema validation and `Workspace` discovery for `pstack`, `pstack-architect`,
  `pstack-maintainer`, `pstack-reviewer`, and `pstack-verifier`;
- a strict live model-inventory result with SHA-256
  `a31f58159d05d9372714c287dab39de135812addcb52c85172b9c556768b64ec`;
- IDE `1.0.437`, Kiro Crew CLI `0.6.0.dev20260903061110`, and Kiro Crew desktop
  `0.6.0-nightly.20260903t061110` as non-gating observations;
- all 13 recorded Kiro documentation bodies unchanged; and
- final gate `pass` followed by successful scratch cleanup.

`KIRO_API_KEY` was present only in the inventory step, after the complete reviewed pin tuple
matched. The canary passed it to exactly one bounded child command,
`kiro-cli chat --list-models --format json`, scanned both streams for the literal key, retained only
the output digest, and sent no model turn. A newer, rollback, republished, or otherwise unpinned
binary cannot enter that step.

## Failed-safe precursor and remediation

The first accepted dispatch, [run 33742467152](https://github.com/njs14/pk-stack/actions/runs/33742467152)
on commit `7b55f353bf03a6b3b89ab09bf206d7e70505ff9f`, stopped during secretless archive extraction because
the provisional 512 MiB per-member ceiling was below the reviewed `kiro-cli-chat` member. The
inventory step was skipped and cleanup passed. Local measurement of the manifest-bound archive
showed `kiro-cli` at `113921088` bytes and `kiro-cli-chat` at `838911376` bytes. Commit `7ce09e3`
binds those exact member sizes when the complete archive pin matches and retains a 1 GiB generic
ceiling for secretless probes of future unpinned releases.

An even earlier dispatch request was rejected by GitHub before a run existed because `runner.temp`
is unavailable in job-level `env`. Commit `7b55f35` moved each scratch binding to step scope and
added a static placement regression. No runner or credential was used by that rejected request.

## Local commands supporting the hosted proof

```text
env PYTHONDONTWRITEBYTECODE=1 uv run --locked --no-config --no-sync pytest -p no:cacheprovider -q
# 302 passed

python3 .github/scripts/test_pk_stack_maintenance_guard.py
# 63 passed; includes 25 canary tests and 18 subtests

env PYTHONDONTWRITEBYTECODE=1 uv run --locked --no-config --no-sync ruff check .
# All checks passed

cd powers/pk-stack
env PYTHONDONTWRITEBYTECODE=1 uv run --frozen pytest -q
# 769 passed
```

Both repository lock checks, the Power Ruff/format/type gates, YAML parsing, and `git diff --check`
also passed. The machine-readable companion is
[`kiro-runtime-canary-campaign.json`](kiro-runtime-canary-campaign.json).
