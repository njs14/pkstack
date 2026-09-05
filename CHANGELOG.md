# Changelog

Release notes are kept short and tied to the Power manifest version. The
manifest is the release metadata authority; package and generated mirrors must
match it.

## [0.3.0] — Unreleased

PKStack 0.3.0 consolidates the product identity and its Kiro-native workflows.
It requires a clean installation when moving from 0.2.0; old installations,
goal state, and feature schemas are not automatically migrated.

- Uses **PKStack** as the product name and `pkstack` for the package,
  distribution, workspace agent, and `.pkstack/` state. The entry point is
  `/pkstack`, with five other namespaced command routes. `projectctl` remains
  the controller command.
- Adds concise source guides, a runnable failing task, and contextual handoffs
  between native planning, verified goals, and curated helpers.
- Records native CLI and IDE Standard and Quick Spec workflows, with
  same-conversation handoff and executable evidence. The release acceptance
  ledger distinguishes current checks from earlier bounded campaigns.
- Hardens the autonomous updater's isolated candidate tests, independent
  review context, immutable provenance, and rejection handling. The existing
  daily schedule stays enabled.
- Extends explicit `git switch` deny rules to tested reordered flags and the
  grouped forms `-qf`, `-dqf`, and `-qC`; ordinary branch switching still requires
  approval. These bounded rules do not parse every shell or Git spelling.
- Fixes the compact Archify reader layout and sequence caption placement,
  and strengthens reusable control-loop attempt and baseline verification.
  It also rejects malformed render arguments, recovers from watcher errors,
  and rejects captions wider than their sequence frames. Local adaptations
  retain separately recorded upstream identities and bundle hashes.
- Produces reproducible Power archives with commit-derived timestamps and
  SHA-256 checksums, and publishes version-specific release notes.

See the [upgrade guide](powers/pkstack/docs/upgrade-0.3.md) before replacing an
older installation and the [release acceptance ledger](reviews/release-030-acceptance.md)
for checks, evidence, and compatibility limits.

## [0.2.0] — 2026-09-03

This release hardens the Kiro-native PK-Stack workflow and prepares the private
repository for its first stable metadata line.

- standardizes the public name as **PK-Stack (Poteto Kiro)** while retaining
  `pstack-kiro`, `pstack_kiro`, `.pstack`, and `projectctl` compatibility names;
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
