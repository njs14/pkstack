---
name: show-me-your-work
description: Produce a compact, auditable decision trail that connects requirements, evidence, choices, edits, and verification without exposing hidden reasoning.
compatibility: Kiro IDE 1.x and Kiro CLI v3; Kiro Crew compatible; Kiro Web supported by design but untested.
---

# Show the decision trail

Treat the request text that activated this skill as the work whose visible evidence should be
audited.

At the start, choose a stable slug. Do not create or edit the trail by hand. Append every material
decision or checkpoint through the deterministic projectctl lever:

```text
.pstack/bin/projectctl evidence append <slug> \
  --requirement <bounded requirement> \
  --evidence <bounded evidence pointer or digest> \
  --decision <bounded visible decision> \
  --verification <exact check and observation> \
  --verdict VERIFIED|NOT VERIFIED|INCONCLUSIVE \
  --output json
```

The default target is `.pstack/state/evidence/<slug>/decision-log.jsonl`, beneath the setup-managed
ignore rule and therefore uncommitted by default. Use a committed trail only when the user explicitly
requests that durable review surface, and require both `--committed` and the exact
`--target Wiki/evidence/<slug>/decision-log.jsonl` on every append and audit command. Neither flag
alone is sufficient. An optional repository artifact requires `--artifact <relative-path>` and may
bind `--artifact-sha256 <lowercase-sha256>`; use hashes when later drift would change the claim.

Each canonical line contains `schema_version`, `sequence`, `timestamp`, `requirement`, `evidence`,
`decision`, `artifact`, `verification`, and `verdict`. Projectctl validates the complete prior file,
chooses the next contiguous sequence and strictly increasing timestamp, checks exact keys and bounds,
validates any repository-relative artifact and digest, screens known credential shapes, preserves the
prior byte prefix, and replaces the file atomically while holding its lock. This is an append-only
workflow convention with deterministic validation, not a signed or tamper-proof log.

Record decisions as they happen. Include rejected alternatives only when consequential. A
retrospective reconstruction must be labeled as such and cannot claim contemporaneous coverage.

Do not expose private chain-of-thought, unrelated conversation history, credentials, personal data,
or unbounded raw logs. The artifact records bounded evidence and decisions, not hidden reasoning.

Before handoff, run:

```text
.pstack/bin/projectctl evidence audit <slug> --output json
```

For a committed trail, repeat the exact `--committed --target
Wiki/evidence/<slug>/decision-log.jsonl` binding. Ask a read-only native Kiro sub-agent for an
independent evidence audit when the trail is large or high risk; give it the bounded trail and named
artifacts, not private transcripts. The current session reconciles all findings. Finish with a
coverage summary that compares acceptance requirements with entries: proven requirements,
unsupported claims, missing intervals, invalid references, verdict counts, and the exact next check.
