---
type: feature
slug: pkstack-power-installation
title: PKStack Power installation metadata
draft: false
schema_version: 2
verification:
  command:
  - uv
  - run
  - --frozen
  - pytest
  - tests/test_kiro_assets.py::test_power_details_metadata_matches_manifest_and_embeds_small_jpg
  - tests/test_branding.py::test_readmes_link_to_documentation_and_public_entrypoints
  - -q
related:
- ../knowledge/pkstack/installation-and-upgrades.md
- ../../powers/pkstack/POWER.md
---

# PKStack Power installation metadata

## User behavior

The distributed Power supplies display metadata consistent with its Agent Plugins manifest and a compact inline JPG; installation instructions identify the actual remote Power directory.

## Expected path

Power directory URL -> plugin.json and POWER.md -> agent loading and IDE display metadata

## Sub-features

### `metadata`

Description, author, keywords, and bounded thumbnail match their reviewed sources.

### `source`

Both installation entrypoints document the canonical Power directory URL and empty-import recovery.

## How to get to it (user POV)

### `cli`

Run the package metadata and installation-guide regressions from the repository root.

## Driving it

### `cli`

#### Recipe

Run the stored pytest command through the locked repository development environment.

#### Observable proof

Both regressions pass after reading the real package, manifest, JPG, and README files.

## Evidence boundary

This verifier proves packaged metadata and URL guidance. Native rendering and live remote installation require separate version-bound observations.

## Cleanup boundary

Pytest may create only its normal temporary state; do not change installed Kiro Powers or application settings.

## Gotchas

- A Kiro success notification can follow an empty repository-root import.

## Verification

`uv run --frozen pytest tests/test_kiro_assets.py::test_power_details_metadata_matches_manifest_and_embeds_small_jpg tests/test_branding.py::test_readmes_link_to_documentation_and_public_entrypoints -q`

A passing command proves the behavior described above, not merely that files exist.
