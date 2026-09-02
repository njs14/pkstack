# Provenance and porting boundary

PK-Stack (Poteto Kiro) is an independent Kiro CLI v3 implementation of selected
verified-development workflow ideas from Cursor's public pstack plugin. It is
not a copy of Cursor's runtime, a compatibility layer for Cursor tools, or a
drop-in redistribution of the upstream plugin.

## Source snapshot

The behavioral reference was the `pstack/` subtree of
[`cursor/plugins`](https://github.com/cursor/plugins) at commit
[`b9ddc83c32972210b8a94d389130713e8eed346e`](https://github.com/cursor/plugins/commit/b9ddc83c32972210b8a94d389130713e8eed346e),
retrieved on 2026-09-01. The pinned manifest identified upstream pstack as
version `0.14.5`.

Upstream pstack is licensed under the MIT License:

> Copyright (c) 2026 Lauren Tan

The complete upstream notice is reproduced in
[`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md). The source repository as
a whole did not expose a repository-level license in the snapshot; the license
relied on here is the explicit `pstack/LICENSE` file in the referenced subtree.

## Meaning of clean-room semantic port

This project uses "clean-room semantic port" in a practical repository sense:

- Public upstream files were consulted to identify observable workflow
  contracts, terminology, sequencing, safety concerns, and failure modes.
- The Kiro skills, Python package, state model, command interfaces, tests, and
  documentation were authored independently for Kiro CLI v3.
- Upstream source files are not vendored, patched, imported, or executed by
  this repository. The upstream MIT notice itself is reproduced as required
  attribution.
- This was not a formal two-team clean-room process in which one team wrote a
  specification and an isolated second team implemented it. The phrase does
  not make that stronger legal or procedural claim.

The repository deliberately separates the interfaces that do work, prove
behavior, and recover knowledge. `projectctl` owns deterministic project
operations and goal state, feature records own executable proof, and OKF or
other knowledge tooling remains an optional source of broader context. Those
interfaces, the Cyclopts implementation, and the current-session
`/verified-goal` protocol are original Kiro-port additions rather than upstream
pstack components.

The current name is Kiro-specific branding, not a restoration of upstream
metadata. The Power manifest identifier and combined-repository name are `pk-stack`; the Python
distribution, receipt manager, package, agent routes, and on-disk `.pstack` paths retain their
documented compatibility identifiers.

## Upstream files consulted

Every link below is pinned to the source commit. The descriptions state why a
file was consulted; they do not imply that its expression was copied.

### Packaging and entry points

- [`pstack/README.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/README.md)
  described the upstream product boundary, skill catalog, and external
  `cursor-team-kit` dependencies.
- [`pstack/.cursor-plugin/plugin.json`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/.cursor-plugin/plugin.json)
  identified upstream package metadata and Cursor registration fields.
- [`pstack/LICENSE`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/LICENSE)
  supplied the upstream license and copyright notice.
- [`pstack/agents/poteto-agent.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/agents/poteto-agent.md)
  showed the Cursor-specific wrapper-agent mechanism that this project does
  not require for its normal path.

### Setup, routing, and bounded execution

- [`pstack/skills/setup-pstack/SKILL.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/setup-pstack/SKILL.md)
  informed idempotent setup, validation of detected capabilities, and the
  optional verification bootstrap.
- [`pstack/skills/poteto-mode/SKILL.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/poteto-mode/SKILL.md)
  informed playbook routing, visible skip decisions, artifact-based review,
  and real-surface verification.
- [`pstack/skills/poteto-mode/playbooks/autonomous-run.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/poteto-mode/playbooks/autonomous-run.md)
  informed the checkable exit predicate, evidence-guided iterations, and rule
  against weakening a predicate to claim success.
- [`pstack/skills/poteto-mode/playbooks/feature.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/poteto-mode/playbooks/feature.md)
  informed explicit decomposition, isolated implementation ownership, lead
  review, and verification on the affected surface.
- [`pstack/skills/poteto-mode/playbooks/opening-a-pr.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/poteto-mode/playbooks/opening-a-pr.md)
  was reviewed to identify Cursor, Graphite, branch-rewrite, and publication
  behavior that should not be part of the Kiro-native core.
- [`pstack/skills/poteto-mode/playbooks/worktree-cleanup.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/poteto-mode/playbooks/worktree-cleanup.md)
  was reviewed for destructive-action risks and was not ported.
- [`pstack/skills/poteto-mode/scripts/bootstrap.ts`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/poteto-mode/scripts/bootstrap.ts)
  was reviewed to identify runtime dependency installation that should not be
  copied into a skill.

### Architecture, candidate comparison, and review

- [`pstack/skills/architect/SKILL.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/architect/SKILL.md)
  informed grounding, usage-first sketches, structurally distinct candidates,
  implementation checkpoints, and redesign after repeated structural friction.
- [`pstack/skills/architect/references/runner-prompt.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/architect/references/runner-prompt.md),
  [`design-red-flags.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/architect/references/design-red-flags.md),
  and [`rationale-template.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/architect/references/rationale-template.md)
  informed the focus on caller experience, deep interfaces, explicit
  alternatives, and coherent ownership boundaries.
- [`pstack/skills/arena/SKILL.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/arena/SKILL.md)
  informed shared rubrics, isolated candidates, judging after candidate
  completion, base selection, coherent grafting, and final verification.
- [`pstack/skills/interrogate/SKILL.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/interrogate/SKILL.md)
  informed identical evidence packets, independent reviews, consensus and
  disagreement analysis, lead judgment, and the rule against auto-applying
  reviewer advice.
- [`pstack/skills/interrogate/references/reviewer-prompt.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/interrogate/references/reviewer-prompt.md),
  [`rubric.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/interrogate/references/rubric.md),
  [`code-quality-review.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/interrogate/references/code-quality-review.md),
  and [`lead-judgment.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/interrogate/references/lead-judgment.md)
  informed the evidence categories and disposition model used by the
  Kiro-native `model-council` skill.
- [`pstack/skills/swarm/SKILL.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/swarm/SKILL.md)
  informed bounded partitions, isolated writes, explicit worker outcomes, and
  aggregation that preserves gaps and dropouts.

### Verification maps and audit trails

- [`pstack/skills/create-verification-skill/SKILL.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/create-verification-skill/SKILL.md)
  informed repository-first discovery, launch and doctor checks, user-surface
  driving, retained evidence, cleanup, and proof of the generated verifier.
- [`pstack/skills/create-verification-skill/references/feature-map-example/README.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/create-verification-skill/references/feature-map-example/README.md),
  [`create-note.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/create-verification-skill/references/feature-map-example/create-note.md),
  and [`search.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/create-verification-skill/references/feature-map-example/search.md)
  informed the user-point-of-view feature record, explicit entry points,
  executable driving recipe, observable end state, and documented gotchas.
- [`pstack/skills/maintain-verification-skill/SKILL.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/maintain-verification-skill/SKILL.md)
  informed index reconciliation, source review, live verification, preserved
  evidence, cleanup invariants, and separation of documentation drift from a
  product regression.
- [`pstack/skills/show-me-your-work/SKILL.md`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/show-me-your-work/SKILL.md),
  [`decision-log-template.tsv`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/show-me-your-work/references/decision-log-template.tsv),
  and [`log.sh`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/show-me-your-work/scripts/log.sh)
  informed append-only, evidence-linked iteration records and safe handling of
  generated spreadsheet cells. The upstream helper script is not included.

### Engineering principles

The following short upstream principles were consulted as behavioral
references:

- [`principle-prove-it-works`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/principle-prove-it-works/SKILL.md)
- [`principle-fix-root-causes`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/principle-fix-root-causes/SKILL.md)
- [`principle-sequence-verifiable-units`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/principle-sequence-verifiable-units/SKILL.md)
- [`principle-make-operations-idempotent`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/principle-make-operations-idempotent/SKILL.md)
- [`principle-model-the-domain`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/principle-model-the-domain/SKILL.md)
- [`principle-boundary-discipline`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/principle-boundary-discipline/SKILL.md)
- [`principle-separate-before-serializing-shared-state`](https://github.com/cursor/plugins/blob/b9ddc83c32972210b8a94d389130713e8eed346e/pstack/skills/principle-separate-before-serializing-shared-state/SKILL.md)

The Kiro implementation expresses these ideas through its own command model,
skill prose, tests, and permission boundary rather than copying the upstream
principle files.

## Adapted semantics

The port preserves these behavioral ideas:

- Define success as an executable predicate and never weaken it to obtain a
  pass.
- Make the smallest evidence-backed change per iteration and retain the result
  needed to diagnose the next attempt.
- Verify the real user or project surface rather than treating compilation,
  a clean diff, or an agent report as sufficient proof.
- Keep setup and state transitions idempotent, validate external data at
  boundaries, and avoid concurrent writes to shared files.
- Describe features from the user's point of view with explicit entry points,
  driving instructions, observable outcomes, and limitations.
- Compare structurally distinct architecture candidates under one rubric,
  preserve a coherent selected design, and restart the design when repeated
  implementation friction disproves it.
- Give reviewers the same evidence packet, distinguish consensus from
  disagreement, classify findings explicitly, and never let review opinion
  override a failing executable verifier.
- Partition parallel work into bounded scopes, isolate writable outputs, and
  report incomplete coverage and dropouts instead of hiding them.

The implementation of those ideas is Kiro-native. Skills run in the user's
current `kiro-cli --v3` session. Native Kiro sub-agents may perform bounded
work, while `projectctl` owns deterministic goal state and verification.

## Behavior deliberately not copied

The following upstream behavior was intentionally excluded or redesigned:

- Cursor packaging and paths, including `.cursor-plugin/plugin.json`,
  `.cursor/rules/`, `.cursor/skills/`, and the Cursor `agents` manifest field.
- Cursor-only skill metadata such as `mode`, `reminder`, `icon`, `color`, and
  `disable-model-invocation`. The non-conforming upstream
  `name: Poteto Mode` value was not retained.
- Cursor `Task` arguments and environment assumptions, including
  `run_in_background`, `readonly`, `environment: "cloud"`,
  `cloud_base_branch`, and fixed Cursor model slugs.
- Cursor's `/loop` wake mechanism, sticky-mode runtime behavior, and any
  assumption that `/goal` exists in Kiro CLI v3.
- Nested ACP or secondary Kiro sessions as the default execution path. Kiro's
  user-facing `/spawn` command is not used as internal skill fanout.
- Graphite stack operations, PR watcher/orchestrator scripts, Cursor cloud
  workers, the dormant Benny automation pack, and `cursor-team-kit` skills
  such as `deslop`, `control-ui`, and `control-cli`.
- Automatic dependency installation from a skill. Dependencies are declared
  in `pyproject.toml` and resolved through the normal package workflow.
- Broad authorization for external ticket, chat, customer, deployment, or
  publication actions. Such actions require the user's exact authorization.
- Destructive defaults such as `git reset --hard`, forced worktree removal,
  recursive deletion, simulator deletion, or overwriting unowned global
  configuration.
- Treating model labels as proof that different models ran. An external Fable,
  Grok, or other reviewer is optional, read-only by default, and identified
  only when execution evidence establishes its identity.

## Licensing boundary

The independently authored `pstack-kiro` repository is distributed under the
Apache License 2.0 in the root [`LICENSE`](../LICENSE). The upstream pstack MIT
license remains attached to upstream pstack and to any upstream expression that
might later be incorporated. The notice in `THIRD_PARTY_NOTICES.md` is
preserved even though this version is a semantic reimplementation and does not
vendor the upstream files.

Names such as Cursor, Kiro, pstack, Cyclopts, PyYAML, Fable, Grok, and OKF are
used only to identify compatibility, provenance, or optional integrations. No
trademark license, endorsement, or affiliation is claimed.

Python dependencies are installed as separate third-party distributions and
remain under their own licenses. Direct runtime dependencies and their license
links are listed in `THIRD_PARTY_NOTICES.md`; the complete resolved package
inventory is in `uv.lock`. Kiro, Cursor, OKF, external reviewer CLIs, and the
Agent Plugins schema are not redistributed by this repository merely because
the documentation or configuration refers to them.

If a future change copies or vendors upstream source, templates, images, or
scripts, that change must add file-level provenance as appropriate, preserve
the applicable notice, and update both this document and
`THIRD_PARTY_NOTICES.md`.
