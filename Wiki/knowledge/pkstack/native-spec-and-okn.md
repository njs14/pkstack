---
type: Decision
title: Preserve native Kiro planning and bounded knowledge retrieval
description: Current Kiro ACP retrieval and local validation decision, with the earlier okn choice retained as superseded history.
tags: [pkstack, decision, kiro, knowledge, okf]
---

# Preserve native Kiro planning and bounded knowledge retrieval

## Current decision

Use Kiro's native Spec, Quick Spec, Bug Fix, and Plan workflows for structured planning. Keep the
transition visible in the current IDE or CLI conversation. Bind completed native artifacts to one
reviewed command or published feature verifier, then use PKStack's current-session verified-goal
loop for terminal proof. A new feature can begin with a failing command; publish a reusable
feature contract after it passes when that record will help future work.

Use `projectctl knowledge search` for bounded retrieval through an isolated read-only Kiro ACP
worker. The worker uses native Kiro CLI authentication and the official Python ACP client pinned
to `agent-client-protocol==0.12.1`. The version-specific isolation adapter currently supports POSIX,
Kiro CLI 2.21.1, and embedded KAS 0.58.7. Missing or unsupported runtime and model selections fail
explicitly, without a silent backend or model fallback.

Search reads `Wiki/knowledge/`, `Wiki/features/`, and `.kiro/specs/`. Working notes in `Wiki/work/`,
native skills, and instructions are excluded. Native specs and operational assets retain their
authoritative locations; ordinary relative links connect them to topic knowledge. No document
synchronization or persistent index, ranker, graph, query engine, or MCP backend is introduced.

The host validates the worker's JSON and exact source evidence, checks that the corpus is unchanged,
and returns a `schemaVersion: "2"` context with answer, source paths, quotes, line ranges, content
SHA-256 values, uncertainties, and an `incomplete` flag. It rejects malformed, excluded, over-budget,
or incomplete output after at most one bounded correction. `--budget` caps returned context using
UTF-8 JSON bytes divided by four; internal token use is unreported. `--model` defaults to `auto`,
whose resolved model is unknown.

Use `projectctl knowledge validate` for local authoring metadata and Markdown links, composed with
feature validation. It invokes no Kiro process, model, or `okn`. This small deterministic check
does not establish full OKF conformance, graph semantics, or factual correctness. `knowledge status`
reports layout and retrieval availability; local validation remains usable without retrieval.
See the [usage contract](../../../powers/pkstack/docs/usage.md#use-project-knowledge) for exact limits.

## Superseded runtime choice

The earlier decision selected `openknowledge-sh/openknowledge`'s canonical `okn` because its
ranked, bounded, provenance-bearing retrieval fit the KNOW interface without building a separate
knowledge engine. It distinguished that runtime from independent `okfcli/okf` conformance or SARIF
checks, which did not replace its search, query, MCP, lifecycle, or safety behavior.

That runtime choice is superseded. Kiro now performs the bounded retrieval task, and the host
checks returned evidence; local validation is independent of a model. The optional `okn` backend
and `--require-okn` flag are removed. The `openknowledge-cli-contract` maintenance source is retired
with its paired manifest/ledger history archived. Its provenance remains historical evidence.
The independently tracked Google OKF specification and OKF skills methodology remain active.

## Consequences

- Normal Kiro CLI v3 and IDE sessions keep planning and execution ownership; ACP is bounded to retrieval.
- Native artifacts and dependency waves remain authoritative.
- Local metadata/link validation and feature validation compose; neither can hide failure in the other.
- Unavailable retrieval is explicit and does not prevent local validation.
- Exact citations make an answer inspectable; they do not prove every claim or feature behavior.
- Future workflow guidance cannot silently change runtime, authorization, or verification authority.

See the [composition architecture](native-kiro-composition.md),
[knowledge lifecycle](knowledge-lifecycle.md), and [context-depth runbook](context-depth.md).
