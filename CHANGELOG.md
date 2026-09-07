# Changelog

Release notes are kept short and tied to the Power manifest version. The
manifest is the release metadata authority; package and generated mirrors must
match it.

## [0.4.4] — 2026-09-06

PKStack 0.4.4 adds a uvx launcher and bundled Python tooling guidance while keeping
the installed project controller authoritative for project operations.

- Runs setup, explicit upgrades, and everyday commands through `uvx --from` a
  reviewed local wheel or checkout, with explicit project selection.
- Preserves the application's verifier environment, installed controller version,
  structured errors, exit status, and cancellation behavior.
- Leads onboarding with uvx while retaining Kiro Power folder import and existing
  `projectctl` and `pkstack-setup` entrypoints. No registry publication or global
  installation is required, and upgrades never run automatically.
- Bundles reviewed Astral `uv`, `ruff`, and `ty` guidance and checks maintained
  Python source, tests, scripts, and executable templates with locked tooling.
- Preserves Kiro-owned Auto model selection and records bounded native routing
  evidence without claiming that Auto identifies its resolved model.
- Runs stacked-PR checks and isolates dependency resolution for executable
  documentation walkthroughs.

See the [Astral and Auto acceptance report](reviews/astral-python-auto/README.md),
[uvx validation and independent review](reviews/uvx-entrypoint/README.md), and
[installation and upgrade guide](powers/pkstack/docs/usage.md). The uvx acceptance
is deterministic CLI evidence, not a new native Kiro model/IDE campaign.

## [0.4.3] — 2026-09-06

The [native planning acceptance report](reviews/planning-043-v5/README.md)
records the passing routing check, composed workflow evidence, and review limits.

PKStack planning uses one shared grilling method inside native Kiro Plan and
Specs. Existing interview commands remain available.

- Reuses settled answers and grounds questions in available project facts.
- Keeps Plan conversational and read-only, with native Specs owning their files.
- Captures reusable definitions and decisions after an approved implementation
  plan, once writes are permitted; explicit no-write requests take precedence.
- Clarifies Power discovery, effective skill inventory, agent switching, native
  Spec review, code-intelligence orientation, and model/effort selection.
- Preserves native approvals, upstream skill provenance, and executable proof.

Existing installations use the [reviewed managed refresh](powers/pkstack/docs/upgrade-0.4.md).
Native acceptance and publication are separate gates recorded in the release status.

## [0.4.2] — 2026-09-06

PKStack 0.4.2 makes the first installation and verified task explicit for Kiro
CLI and IDE users. Existing commands, verification contracts, and ownership
rules are unchanged.

- Explains the practical benefits before the workflow catalog and provenance.
- Gives CLI and IDE installation paths, distinguishes the Power source from
  the target project, and assigns the source path before using it.
- Aligns setup guidance with the supported Python launcher and `uv` runtime
  behavior, including first-use downloads and offline cache requirements.
- Connects installation to the included failing task and shows the expected
  failure, Kiro repair, and stored passing result.
- Documents user-owned saved requests, their role beside skills and executable
  goals, and the observed v3 prompt-menu compatibility limit.
- Exercises the documented source-to-target commands and packaged-Power paths
  in onboarding regressions. Scripted repair remains controller evidence;
  native Kiro campaign results are recorded separately in the release status.

Start with the [installation guide](powers/pkstack/docs/usage.md), then
[try the failing task](powers/pkstack/docs/first-task.md). Existing 0.4
installations use the [reviewed managed refresh](powers/pkstack/docs/upgrade-0.4.md).

## [0.4.1] — 2026-09-06

PKStack 0.4.1 improves local knowledge validation and corrects the current
knowledge-runtime documentation. It preserves the 0.4 interfaces and runtime
compatibility limits.

- Reuses Markdown heading parsing within a validation call while preserving
  fresh bounded reads and path checks for every link. Seven-sample benchmarks
  reduced median time from 25.05 ms to 22.18 ms on the repository Wiki and from
  3.151 s to 0.262 s on a synthetic shared-target fixture, with identical results.
- Corrects README, compatibility, release, and architecture guidance: `okn` is
  retired, validation is local, and bounded knowledge search uses Kiro ACP.
  Historical provenance and the normal interactive Kiro workflow remain intact.
- Aligns the documented IDE evidence and diagram status with the retained
  bounded campaigns and refreshed artifacts.
- Documents fresh-worktree setup, reviewed managed refresh, and verification;
  removes duplicate ignore rules.

Use the [0.4 upgrade guide](powers/pkstack/docs/upgrade-0.4.md) for a reviewed
managed refresh. The [measurement evidence](reviews/evidence-led-improvements/README.md)
distinguishes the synthetic benchmark from the smaller repository workload.

## [0.4.0] — 2026-09-06

PKStack 0.4.0 adds native knowledge authoring and bounded Kiro retrieval.
Normal work stays in the current Kiro conversation.

- Adds four curated authoring workflows for interviews, detailed specifications,
  documentation-guided requirements, and Markdown knowledge management.
- Separates retained `Wiki/knowledge/` from working `Wiki/work/` drafts and keeps
  native `.kiro/specs/` owned by Kiro.
- Replaces the optional `okn` backend with local metadata, link, and feature-map
  validation, plus optional read-only Kiro ACP search over source snapshots.
- Verifies returned quotations and derives line locations on the host; bounds
  time, tools, protocol frames, response size, and process cleanup. Unsupported
  Kiro versions fail closed. Verified quotations do not certify generated prose.
- Extends upstream curation and secretless validation to the knowledge skills,
  and refreshes the component, task, and updater diagrams.

Live knowledge retrieval is verified on macOS with Kiro CLI 2.21.1/KAS 0.58.7.
Linux CI verifies controller behavior; its native runtime canary verifies agent
discovery and model inventory, not end-to-end knowledge retrieval. Other Kiro
versions and Windows knowledge retrieval remain outside the verified contract.

Read the [0.4 upgrade guide](powers/pkstack/docs/upgrade-0.4.md) and the
[knowledge acceptance report](reviews/knowledge-foundation.md) for migration,
evidence, and limits.

## [0.3.0] — 2026-09-05

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
