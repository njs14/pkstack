---
type: Guide
title: PK-Stack feature map
description: Index of executable feature contracts.
tags: [pk-stack, verification, feature-map]
---

# Feature map

This directory is the narrow **PROVE** interface. Each published feature
describes one user-observable behavior and binds it to one reviewed executable
verification command. Architecture, decisions, concepts, and operations belong
in the broader [KNOW index](../index.md).

## Current contracts

| Contract | What it covers |
| --- | --- |
| [Upstream maintenance](pk-stack-upstream-maintenance.md) | Pinned-source reproof and acceptance |

## Create a contract

Use the canonical project wrapper from the repository root:

```sh
.pstack/bin/projectctl feature generate account-lookup \
  --title "Account lookup" \
  --behavior "A caller can retrieve account status." \
  --expected-path "CLI -> gateway -> account service -> response" \
  --sub-feature "lookup-status=Return the current account status." \
  --entrypoint "cli=Run the account lookup command." \
  --drive "cli=Run the public command from the project root." \
  --entrypoint-proof "cli=The command exits zero and prints the expected status." \
  --gotcha "A zero exit without the expected status is insufficient." \
  --evidence-boundary "Retain bounded public output and its exit status." \
  --cleanup-boundary "Remove only verifier-owned temporary state." \
  --command "uv run pytest tests/test_account_lookup.py -q" \
  --ready --output json
```

Schema-2 contracts describe sub-features, entrypoints, driving recipes,
observable proof, gotchas, and evidence/cleanup boundaries. New contracts are
drafts unless `--ready` proves the command first. For an initial map, prepare
three to five complete records and run `feature generate-map`; only the named
representative is published until each remaining verifier passes.

```sh
.pstack/bin/projectctl feature generate-map feature-plan.json \
  --representative account-lookup --output json
.pstack/bin/projectctl feature publish <slug> --output json
```

Validate the map at any time:

```sh
.pstack/bin/projectctl feature validate --output json
```

If a contract needs deeper context, follow its `related` links before issuing
one targeted `projectctl knowledge search` query. Keep the verifier specific:
a passing command is evidence for that predicate, not proof of unrelated
features.
