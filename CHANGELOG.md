# Changelog

Release notes are kept short and tied to the Power manifest version. The
manifest is the release metadata authority; package and generated mirrors must
match it.

## Unreleased

- completes the PKStack namespace across the Python package, distribution,
  repository-local `.pkstack/` state, generated controller, docs, tests, and
  GitHub automation.

## [0.2.0] — 2026-09-03

This release hardens the Kiro-native PKStack workflow and prepares the private
repository for its first stable metadata line.

- standardizes the public name as **PKStack (Poteto Kiro)** while retaining
  consistent `pkstack`, `pkstack`, `.pkstack`, and `projectctl` interfaces;
- documents a runnable Power-local setup workflow and current-session handoff;
- makes the DO / PROVE / KNOW boundaries and the Floci lab separation explicit;
- adds the curated `show-me` explainer and the reviewed offline Archify diagram
  runtime, with exact bundle and source-parity records;
- adds secretless pull-request CI and a private tag-bound release workflow;
- adds release metadata, community guidance, security reporting, and review
  evidence indexing; and
- preserves earlier validation and provenance records as historical evidence.

The private `v0.2.0` tag records the reviewed release commit. Later changes on
`main` remain unreleased until a subsequent version is cut.
