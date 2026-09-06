---
type: Observation
title: Local validation after the prototype migration
description: Later September 5 source inspection and actual generated-controller validation supersede the prototype validator observation.
tags: [knowledge, validation, observation, migration]
---

# Local validation after the prototype migration

This is a later observation on 2026-09-05, after the historical prototype inspection in
[observations.md](observations.md). That earlier observation accurately described its supplied
prototype; it does not establish the behavior of the migrated candidate.

The current candidate `validate()` performs feature validation, metadata checks, and local Markdown
link checks without discovering or invoking Kiro, a model, okn, or openknowledge. Its active
`search()` delegates to the bounded Kiro ACP worker. There is no optional okn backend.

The host executed the generated repository command `.pkstack/bin/projectctl knowledge validate
--output json` after a reviewed setup update. It returned exit 0, `ok: true`, `mode: local`, and
`schemaVersion: "2"`, with all 12 documents, 72 local links, and the feature contract passing.
The actual [JSON result](evidence/validation-after-retirement.json) is retained for inspection.
This proves that particular local run; it does not prove full OKF conformance, deployed behavior,
or all possible knowledge correctness. The full package and independent review gates were still
pending at the time this observation was recorded.

The prototype code has changed since the earlier observation. Its prior bytes are frozen in the
host evidence archive; the current source snapshot is
[`knowledge.py`](../../../powers/pkstack/src/pkstack/knowledge.py).
