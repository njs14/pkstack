---
type: Guide
title: PKStack feature map
description: Index of executable feature contracts.
tags: [pkstack, verification, feature-map]
---

# Feature map

This directory is the narrow **PROVE** interface. Each published feature
describes one user-observable behavior and binds it to one reviewed executable
verification command. Architecture, decisions, concepts, and operations belong
in the broader [KNOW index](../index.md).

## Current contracts

| Contract | What it covers |
| --- | --- |
| [pkstack-power-installation](pkstack-power-installation.md) | Project-owned executable contract |
| [pkstack-upstream-maintenance](pkstack-upstream-maintenance.md) | Project-owned executable contract |

## Create a contract

Use the canonical project wrapper from the repository root:

```sh
.pkstack/bin/projectctl feature generate account-lookup \
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
one to five complete records and run `feature generate-map`; only the named
representative is published until each remaining verifier passes.

```sh
.pkstack/bin/projectctl feature generate-map feature-plan.json \
  --representative account-lookup --output json
.pkstack/bin/projectctl feature publish <slug> --output json
```

Validate the map at any time:

```sh
.pkstack/bin/projectctl feature validate --output json
```

If a contract needs deeper context, follow its `related` links before issuing
one targeted `projectctl knowledge search` query. Keep the verifier specific:
a passing command is evidence for that predicate, not proof of unrelated
features.
