---
name: show-me-your-work
description: Produce a compact, auditable decision trail that connects requirements, evidence, choices, edits, and verification without exposing hidden reasoning.
---

# Show the decision trail

Treat the request text that activated this skill as the work whose visible evidence should be
audited.

Use this method when the user requests a decision trail or the selected workflow requires one.
For "show me what you did" without that context, summarize existing evidence and gaps without
creating a new log. For a visual explanation, use [`show-me`](../show-me/SKILL.md).
When a visual artifact accompanies a requested trail, reference that artifact's existing evidence
rather than repeating its investigation.

At the start, choose a stable slug. Do not create or edit the trail by hand. Append every material
decision or checkpoint through the deterministic projectctl lever:

```text
.pkstack/bin/projectctl evidence append <slug> \
  --requirement <bounded requirement> \
  --evidence <bounded evidence pointer or digest> \
  --decision <bounded visible decision> \
  --verification <exact check and observation> \
  --verdict VERIFIED|NOT VERIFIED|INCONCLUSIVE \
  --output json
```

The default target is `.pkstack/state/evidence/<slug>/decision-log.jsonl`, beneath the setup-managed
ignore rule and therefore uncommitted by default. Use a committed trail only when the user explicitly
requests that durable review surface, and require both `--committed` and the exact
`--target Wiki/evidence/<slug>/decision-log.jsonl` on every append and audit command. Neither flag
alone is sufficient. An optional repository artifact requires `--artifact <relative-path>` and may
bind `--artifact-sha256 <lowercase-sha256>`; use hashes when later drift would change the claim.

Each canonical line contains `schema_version`, `sequence`, `timestamp`, `requirement`, `evidence`,
`decision`, `artifact`, `verification`, and `verdict`. Projectctl validates the prior file's structure,
chooses the next contiguous sequence and strictly increasing timestamp, checks exact keys and bounds,
validates the new event's repository-relative artifact and digest, screens known credential shapes, preserves the
prior byte prefix, and replaces the file atomically while holding its lock. This is an append-only
workflow convention with deterministic validation, not a signed or tamper-proof log.

An old artifact may change or disappear. Append a correction without rewriting the old event;
`evidence audit` still reports the historical reference's present drift. A successful append proves
the write succeeded, not that every historical artifact is still current.

Record decisions as they happen. Include rejected alternatives only when consequential. A
retrospective reconstruction must be labeled as such and cannot claim contemporaneous coverage.

Do not expose private chain-of-thought, unrelated conversation history, credentials, personal data,
or unbounded raw logs. The artifact records bounded evidence and decisions, not hidden reasoning.

Before handoff, run:

```text
.pkstack/bin/projectctl evidence audit <slug> --output json
```

For a committed trail, repeat the exact `--committed --target
Wiki/evidence/<slug>/decision-log.jsonl` binding. Ask a read-only native Kiro sub-agent for an
independent evidence audit when the trail is large or high risk; give it the bounded trail and named
artifacts, not private transcripts. The current session reconciles all findings. Finish with a
coverage summary that compares acceptance requirements with entries: proven requirements,
unsupported claims, missing intervals, invalid references, verdict counts, and the exact next check.
