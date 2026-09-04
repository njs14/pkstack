---
type: Decision
title: Preserve native Kiro planning and canonical okn retrieval
description: Decision to keep PK-Stack as a thin workflow and verification seam over native Kiro and OKF.
tags: [pk-stack, decision, kiro, okn, okf]
---

# Preserve native Kiro planning and canonical okn retrieval

## Decision

Use Kiro's native Spec, Quick Spec, Bug Fix, and Plan workflows for structured planning. Keep the
transition visible in the current IDE or CLI conversation. Bind completed native artifacts to one
reviewed command or published feature verifier, then use PK-Stack's current-session verified-goal
loop for terminal proof. A new feature can begin with a failing command; publish a reusable
feature contract after it passes when that record will help future work.

Use `openknowledge-sh/openknowledge`'s `okn` as the canonical broader KNOW implementation. Its
ranked, bounded, provenance-bearing retrieval is the interface PK-Stack needs. `okfcli/okf` may be
run as an explicitly named independent conformance or SARIF check, but it does not replace `okn`
search, query, MCP, lifecycle, or safety behavior.

## Consequences

- PK-Stack stays a Power and thin compatibility seam rather than becoming an agent runtime.
- Native Kiro artifacts and dependency waves remain authoritative.
- Feature validation and OKF validation compose; neither can hide failure in the other.
- Missing canonical `okn` is reported as degraded feature-map-only operation.
- Workspace-local executables cannot masquerade as the canonical KNOW runtime.
- Future OKF skill packages may add workflow guidance above this boundary, but cannot silently
  change the runtime or verification authority.

See the [composition architecture](../architecture/native-kiro-composition.md) and the
[context-depth runbook](../operations/context-depth.md).
