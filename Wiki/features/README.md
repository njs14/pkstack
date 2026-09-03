---
type: Guide
title: Feature map
description: PK-Stack executable feature-contract index.
tags: [pk-stack, verification, feature-map]
---

# Feature map

This directory is the narrow **PROVE** interface. Each feature file describes
one user-observable behavior and binds it to one explicitly reviewed executable
verification command. Broader architecture, decisions, concepts, and
operations belong elsewhere in `Wiki/` (the **KNOW** interface).

Create a contract with:

```bash
.pstack/bin/projectctl feature generate account-lookup \
  --title "Account lookup" \
  --behavior "A caller can retrieve account status." \
  --expected-path "Runtime -> gateway -> account service -> response" \
  --sub-feature "lookup-status=Return the current account status." \
  --entrypoint "cli=Run the account lookup command." \
  --drive "cli=Run the public command from the project root." \
  --entrypoint-proof "cli=The command exits zero and prints the expected status." \
  --gotcha "A zero exit without the expected status is insufficient." \
  --evidence-boundary "Retain bounded public output and its exit status." \
  --cleanup-boundary "Remove only verifier-owned temporary state." \
  --command "uv run pytest tests/test_account_lookup.py" \
  --ready
```

Schema-2 contracts map sub-features, every user entrypoint, a same-name drive
recipe and observable proof for each entrypoint, gotchas, and evidence/cleanup
boundaries. Generated contracts default to `draft: true`. With `--ready`,
projectctl runs the command first and writes a ready contract only when that
proof passes.

For an initial map, prepare one exact JSON object containing 3-5 complete
schema-2 feature records, then prove only one representative:

```bash
.pstack/bin/projectctl feature generate-map feature-plan.json \
  --representative account-lookup
```

The remaining records stay drafts until each is independently proven with
`.pstack/bin/projectctl feature publish <slug>`.
