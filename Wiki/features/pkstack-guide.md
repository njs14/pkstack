---
type: feature
slug: pkstack-guide
title: PKStack guide installation and routing contract
draft: false
schema_version: 2
verification:
  command:
  - uv
  - run
  - --frozen
  - pytest
  - tests/test_pkstack_guide.py
  - tests/test_kiro_assets.py::test_pkstack_routes_are_namespaced_without_renaming_upstream_identities
  - tests/test_kiro_assets.py::test_skill_routing_review_fixture_is_strict_and_names_real_skills
  - tests/test_kiro_assets.py::test_skill_routing_markdown_pointers_resolve_within_the_power
  - -q
related:
- ../knowledge/pkstack/native-kiro-composition.md
- ../../powers/pkstack/skills/pkstack-guide/SKILL.md
---

# PKStack guide installation and routing contract

## User behavior

The project advisor is registered as a native PKStack skill, installs its exact resources through reviewed setup, and preserves user-owned conflicts. Routing declarations distinguish advice from execution.

## Expected path

Canonical Power -> packaged skill inventory -> reviewed setup -> workspace skill and routing declarations

## Sub-features

### `installation`

Setup installs both guide resources exactly and repeat setup changes nothing.

### `ownership`

Preview is read-only and existing user edits survive attempted refresh.

### `routing`

The advisory entry and two representative scenarios point to real shipped skills.

## How to get to it (user POV)

### `setup`

Install or refresh the Power through the reviewed Power-local setup skill.

### `discovery`

Use pkstack-guide directly or ask pkstack for workflow advice in the selected Kiro agent.

## Driving it

### `setup`

#### Recipe

Run the stored focused contract verifier from the locked repository environment.

#### Observable proof

Exact-byte installation, receipt hashes, idempotence, and conflict-preservation assertions pass.

### `discovery`

#### Recipe

Run the stored registration, reference-link, and scenario-fixture checks; inspect native behavior separately.

#### Observable proof

The skill is registered, reference pointers resolve, and advisory scenarios retain their expected routes and forbidden effects.

## Evidence boundary

This verifier covers packaged registration, pointers, setup effects and declared routing cases. Native CLI behavior, IDE discovery, advice quality, and permission-runtime selection require separate observations.

## Cleanup boundary

Tests use disposable project fixtures and ordinary test caches; no global Kiro settings, real project application, or accounts are changed.

## Gotchas

- A structural routing fixture does not prove natural-language behavior, selected-agent attachment, or a current project verification result.

## Verification

`uv run --frozen pytest tests/test_pkstack_guide.py tests/test_kiro_assets.py::test_pkstack_routes_are_namespaced_without_renaming_upstream_identities tests/test_kiro_assets.py::test_skill_routing_review_fixture_is_strict_and_names_real_skills tests/test_kiro_assets.py::test_skill_routing_markdown_pointers_resolve_within_the_power -q`

A passing command proves the behavior described above, not merely that files exist.
