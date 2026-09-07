---
type: Architecture
title: Runtime, verification, and permission boundaries
description: What projectctl proves, how native Kiro remains in control, and what historical regressions teach.
tags: [pkstack, verification, runtime, permissions, evidence]
---

# Runtime, verification, and permission boundaries

## Current contract

Kiro owns the conversation, model selection, planning workflows, tools, and permissions.
PKStack's instructions arrange work around those native facilities. `projectctl` owns deterministic
project operations, feature contracts, and goal state. **DO** is the command surface; **PROVE** is
the executable feature/goal contract; **KNOW** is retained understanding. See the
[composition decision](native-kiro-composition.md) for native planning and the
[installation guide](installation-and-upgrades.md) for launcher/controller ownership.

A goal binds a reviewed verifier, its provenance and digest, and a finite attempt budget. A failed
attempt must stay visible. Repair the implementation, then rerun the stored verifier; do not change
the predicate to obtain a pass. The [goal implementation](../../../powers/pkstack/src/pkstack/goal.py)
owns locking, state invariants, explicit resume/clear behavior, and persistence. Native Spec
artifacts remain native; a binding does not establish their semantic completeness or authorize
rewriting tests. Published feature records keep their own schema and verifier requirements.

The [runner](../../../powers/pkstack/src/pkstack/runner.py) rejects obvious placeholder proofs,
controller self-reference, and prohibited command forms. It executes argv rather than a shell
program and bounds output and process lifetime. These checks are an evidence-integrity screen,
not an OS sandbox or a proof that an arbitrary script tests the stated behavior. A parent exiting
successfully can satisfy its predicate even when descendants require cleanup. Approved processes
still run with the user's privileges. A disabled advisory Stop hook is not a scheduler or a
mechanical guarantee that an agent continues working.

## Permission evidence must use the selected profile

Generating an agent profile or passing its schema validator does not prove live matching. Record
which profile was selected, the actual allowed/asked/denied action, runtime version, and fixture
scope. Read-only delegated profiles must not acquire general shell tools through misleading labels.
Open-ended Git globs are unsafe shortcuts: apparent read operations can accept output paths,
external diff commands, or names such as `difftool`. Test argument and spelling variants as well
as nominal commands. Tool permissions do not constrain everything an approved subprocess may do.

The 0.3 permission campaign found missing `git switch` discard/reset forms and subsequently grouped
short-option gaps. Its repaired examples include reordered options and grouped forms. That is
bounded matcher evidence, not a complete shell containment claim. Inspect the current
[primary profile](../../../powers/pkstack/templates/project/.kiro/agents/pkstack.json) and tests
when changing these boundaries; old reviews refer to earlier names and schemas.

## Reusable regressions from early reviews

The early Fable/Grok reports concern historical candidates. Their lasting lessons are:

- Validate state before atomic replacement; a resume budget must not persist an active goal with
  no remaining attempts. Failed validation must preserve the previous loadable state.
- Test real wrapper execution with application-only dependencies. Controller `PYTHONPATH`,
  `VIRTUAL_ENV`, `PATH`, and uv settings must not contaminate the application verifier.
- Check generation/loading round trips, including YAML values that look like booleans or numbers,
  malformed UTF-8 and argv, and reserved feature names. Structured JSON errors must remain structured.
- Inspect executable paths and operands, absolute paths, joined interpreter flags, and wrapper
  commands. String filtering cannot establish arbitrary script semantics.
- Setup authority must come from reviewed package assets, not an installed controller cache.
  Receipt hashes establish ownership, not cryptographic provenance. Preflight is not a guarantee
  of whole-transaction rollback after a later filesystem failure.

The source-specific table below preserves finding identities and links to the disposition ledger.
No historical issue is declared currently open or fixed solely because a reviewer labeled it so.

## Client and model limits

The repository targets native CLI v3 and IDE agent-panel workflows. Crew command-surface/doctor
smokes do not prove project orchestration, and Web remains untested end to end in the retained
compatibility material. Model availability and native commands can drift; inspect current
repository pins and rerun the relevant probes after a runtime update. A menu entry is command
recognition, not execution proof. Selected Auto is reported as Auto; do not invent its underlying
model. Requested effort and displayed/account-wide costs have different evidence boundaries.

Knowledge search is the explicit bounded ACP exception, not the normal execution mode. Its
supported tuple and remaining Linux live-query gap belong to the
[knowledge lifecycle](knowledge-lifecycle.md) and runtime decision, separately from local checks.


## Design permission probes with both refusal and ordinary controls

The [Git-switch audit](../../../reviews/release-030-permissions.md) first found destructive forms
falling through to **ask**, rather than the intended **deny**. The difference matters: this was a
missing hard-deny rule, not evidence that commands ran silently. After standalone and reordered
forms were repaired, review found grouped spellings such as `-qf`, `-dqf`, and `-qC` still asked.
The follow-up added exact supported groups and ordinary controls with benign branch names. A
broad pattern containing `*f*` could span spaces into a branch name and falsely reject safe work.

The native probes used disposable directories with no Git repository in any parent, tested the
actual installed profile, and compared the complete protected file inventory afterward. That
fixture choice contained an operator error: an intended Deny selection was interpreted as Allow,
and Git failed because there was no repository. It is not deny evidence. Later ordinary controls
were cancelled with Escape; destructive cases had to return the agent-profile denial without an
approval. The resulting claim covers the tested option spellings, not aliases, arbitrary grouping,
absolute executables, quoting variants, or subprocess containment.

## Schema, discovery, selection, and action are separate gates

The [2.21.0 loader probe](../../../reviews/kiro-v3-agent-discovery-probe.json) found three read-only
helpers that passed schema validation but were absent from Workspace agent rows. An inert empty
`toolsSettings` object restored discovery without adding authority. The later
[updater investigation](../../../reviews/pipeline-readiness-validation.md#global-agent-loading-defect)
found a different mismatch: global listing saw the maintainer while v3 chat silently selected the
default agent under a split home layout. A nonempty JSON stream had been mistaken for sufficient
execution evidence. Require actual session-bound agent selection before model/tool activity;
advertised choices and successful process exit are insufficient.

These versioned defects explain why schema checks, effective inventory, selected-agent attestation,
and concrete permission behavior all have a role. The sentinel is not a universal schema rule,
and a canary exercising workspace agents does not validate a differently configured global agent.

The [native command audit](../../../reviews/cli-native-command-audit/README.md) also distinguished
working commands from completion entries: the bare agent picker, same-session agent swap,
`/config skills`, and `/code status` ran; requirements analysis and several planning commands were
only recognized. In that build `/agent list` tried to select an agent named `list`. Diagnose the
specific client surface before recommending restart or a command from broader documentation.
Automatic Power inclusion and inherited skills are distinct settings; inspect the selected
agent's effective inventory rather than infer complete isolation from one switch.

## Source-specific retained knowledge

These summaries describe what is retained from each source. Historical observations keep their
original candidate and scope; they are not fresh verification of this checkout.

| Source | Retained guidance or bounded observation |
| --- | --- |
| [powers/pkstack/docs/architecture.md](../../../powers/pkstack/docs/architecture.md) | Kiro owns execution while projectctl owns commands and proof; shell-free verification and unsigned ownership receipts do not constitute a sandbox or semantic truth. |
| [powers/pkstack/docs/kiro-v3-compatibility.md](../../../powers/pkstack/docs/kiro-v3-compatibility.md) | Separate documentation, command recognition, native execution, and client-specific evidence; selected Auto does not reveal its underlying model and Crew/Web have narrower evidence. |
| [powers/pkstack/reviews/acceptance-criteria.md](../../../powers/pkstack/reviews/acceptance-criteria.md) | Historical disposition ledger ties environment isolation, JSON parsing, path checks, profile attachment, and proof-policy corrections to reproducible acceptance tests. |
| [powers/pkstack/reviews/fable-round-1.md](../../../powers/pkstack/reviews/fable-round-1.md) | FBL-001 through FBL-004 motivate rejecting placeholder/self proof, complete controller permission coverage, loadable resume state, and external setup authority; older snapshot was rejected. |
| [powers/pkstack/reviews/fable-round-2.md](../../../powers/pkstack/reviews/fable-round-2.md) | FBL-012/013 show why open-ended Git allow globs and an unselected primary profile invalidate permission claims; read-only source review was not live matcher proof. |
| [powers/pkstack/reviews/grok-round-1.md](../../../powers/pkstack/reviews/grok-round-1.md) | GRK-001 through GRK-004 exposed wrapper environment leakage, malformed feature JSON output, operand containment gaps, and missing active-profile attachment. |
| [powers/pkstack/reviews/grok-round-2.md](../../../powers/pkstack/reviews/grok-round-2.md) | GRK-011 through GRK-017 extend review to absolute executables, shell-capable read-only profiles, cached setup, reserved readme names, and joined interpreter flags; findings require disposition rather than blind acceptance. |
| [powers/pkstack/reviews/grok-round-3.md](../../../powers/pkstack/reviews/grok-round-3.md) | GRK-021 demonstrates generator/loader YAML round-trip failures; bridge argv typing, setup fallback errors, and parent-exit/descendant cleanup limits remain distinct from semantic proof. |
| [powers/pkstack/reviews/kiro-selected-profile-campaign.md](../../../powers/pkstack/reviews/kiro-selected-profile-campaign.md) | The bc6e79a-era selected pstack-profile run records concrete permission observations and a 2-of-4 fixture pass, preceding the later bytecode-boundary campaign. |
| [powers/pkstack/reviews/kiro-final-campaign.md](../../../powers/pkstack/reviews/kiro-final-campaign.md) | The b39c20a post-CDX-004 campaign supersedes the earlier run for its original acceptance scope; it records selected-profile fail-repair-pass and preservation, not current release proof. |
| [reviews/release-030-permissions.md](../../../reviews/release-030-permissions.md) | Missing destructive git switch forms and later grouped-option gaps required real matcher probes and narrow regressions; this is not complete shell containment. |
| [reviews/kirocrew-nightly-smoke-campaign.md](../../../reviews/kirocrew-nightly-smoke-campaign.md) | September 3 Crew command-surface and doctor observations passed with a packaging limitation; no PKStack task orchestration or verified-goal workflow was exercised. |
| [reviews/astral-python-auto/README.md](../../../reviews/astral-python-auto/README.md) | A bounded Auto-selected Python repair passed after one-time interactive permission; underlying model, universal routing, and zero-intervention behavior were not established. |
