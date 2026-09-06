---
type: Observation
title: Prototype knowledge validation versus the local-only requirement
description: Dated inspection comparing current knowledge.py validation and search behavior with the native knowledge-foundation requirement.
tags: [upstream-maintenance, observation, okn, acp, validation]
---

# Historical prototype knowledge validation versus the local-only requirement

This is the pre-retirement prototype observation produced during the native authoring fixture.
Its code and native requirement links below point to frozen test inputs. The current implementation
and verification are recorded in the [foundation report](../../../reviews/knowledge-foundation.md);
this historical record does not describe the final migrated validator.

## Observation of 2026-09-05

Recorded 2026-09-05 (America/New_York) from source inspection only. No command was executed for this
record.

### What the native requirement asks for

[`.kiro/specs/knowledge-foundation/requirements.md`](../../../reviews/knowledge-foundation-evidence/fixture/.kiro/specs/knowledge-foundation/requirements.md)
requires that `projectctl knowledge validate` run deterministically and locally, with no model turn
and no `okn` subprocess, and that the replacement search use Kiro ACP and return independently
verifiable source quotations inside a host-enforced returned-context budget. The accepted plan
requires deterministic local-only validation and rejects shipping an optional `okn` backend, so
retaining `okn` is not an open choice. That spec also requires the current implementation to be
inspected before anyone claims the requirements are implemented.

### What the current code does

From [`powers/pkstack/src/pkstack/knowledge.py`](../../../reviews/knowledge-foundation-evidence/fixture/powers/pkstack/src/pkstack/knowledge.py):

- `validate()` calls `status()`, which resolves `okn`/`openknowledge` on `PATH`, refuses a
  workspace-local executable, and probes it with `okn version` against a `0.13.0` minimum. When that
  executable is present, `validate()` runs `okn --error-format json validate --spec 0.2 --profile okf
  --format json <knowledge root>` and reports `mode: "canonical-okn"`. The local-only path exists,
  but only as the fallback: with `okn` absent it returns `mode: "feature-map-only"` from
  `validate_feature_map` plus `validate_local_links`, and labels that a degraded warning.
- Consequence: the required local-only validation migration is incomplete. The subprocess is still
  the preferred path, and the local path that matches the accepted requirement is the one the code
  currently labels degraded. `require_okn=True` additionally makes the absence of `okn` a hard error.
  This is unfinished migration work, not evidence of an optional backend being retained.
- `search()` already delegates to `pkstack.knowledge_acp.search` and converts
  `KnowledgeRuntimeError` into `KnowledgeError`. The former `okn search` implementation remains as
  `_legacy_search`, which `search()` does not call.
- Legacy-path checks only, in the unused `_legacy_search` adapter and its `okn` protocol validators:
  budget bounds of 64 to 8000 tokens, a required `okf+sha256://<revision>/<path>#<contentSha256>`
  locator whose revision, content hash, and percent-decoded path must agree with the reported source,
  rejection of any source under `work/`, per-source token estimates that must sum to the reported
  total and stay within budget, and blanking of captured `stdout`/`stderr` on protocol failure. These
  behaviors belong to the dead `okn` adapter and are explicitly not attributed to the active ACP
  search; the ACP module was not inspected, so nothing here describes its retrieval safety.

### Limits of this observation

This is source inspection, not implementation proof. `pkstack.knowledge_acp`,
`pkstack.knowledge_payload`, `pkstack.features`, and `pkstack.knowledge_links` were not read here, so
this record makes no claim about whether the ACP path avoids a model turn, how the host enforces the
returned-context budget, or whether quotations verify end to end. No validation command was run; the
host runs deterministic validation separately. The excluded draft under `Wiki/work/` was not read.

### Open questions recorded at that inspection

When the local-only validation migration completes, and who finishes removing the `okn` subprocess
path from `validate()`, is unresolved in the material inspected here. Whether to keep `okn` as an
optional backend is not open; the accepted plan already rejects that.

Separately, widening autonomous upstream source acceptance beyond the configured GitHub entries still
has no accepted date and no accepted owner. See the
[glossary open questions](glossary.md#open-questions).

## Related

- [Accepted upstream maintenance decisions](decisions.md)
- [Upstream maintenance vocabulary](glossary.md)
- [Knowledge lifecycle](../pkstack/knowledge-lifecycle.md) for the decision, observation, hypothesis,
  and open-question distinction
- [Native planning and bounded retrieval](../pkstack/native-spec-and-okn.md) for the current runtime
  decision, including the superseded canonical-okn choice
