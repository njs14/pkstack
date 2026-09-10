---
type: feature
slug: pkstack-consumer-permissions
title: Consumer agents inherit Kiro permission policy
draft: false
schema_version: 2
verification:
  command:
  - uv
  - run
  - --frozen
  - pytest
  - tests/test_permission_preset.py
  - tests/test_kiro_assets.py::test_consumer_agents_inherit_policy_and_keep_role_tools
  - tests/test_kiro_assets.py::test_subagent_availability_keeps_roles_and_leaves_trust_to_global_policy
  - -q
related:
- ../knowledge/pkstack/runtime-and-verification.md
- ../../powers/pkstack/docs/permissions.md
---

# Consumer agents inherit Kiro permission policy

## User behavior

The primary PKStack agent exposes built-in tools. Consumer profiles inherit user
and workspace permission policy, while three helpers retain read-only tool lists.
An optional global YAML preset allows built-ins with targeted shell denies.
Installing it is a manual action outside project setup; MCP and CI-agent policy
are separate.

## Expected path

User policy -> Kiro capability evaluation -> selected agent's available tools.

## Sub-features

### `policy`

The example policy permits routine development and matches the documented direct
destructive command forms. Test commands are strings, never shell invocations.

### `roles`

Consumer profiles contain no inline policy or legacy trust grants. Helpers expose
only read and knowledge tools, regardless of global allows.

## How to get to it (user POV)

### `cli`

Read the global permission guide and manually review the example against existing
user and workspace policies before adopting it.

## Driving it

### `cli`

#### Recipe

Run the stored verifier from the locked repository development environment.

#### Observable proof

Routine and destructive command examples receive the expected preset effects;
consumer profiles retain their roles; setup leaves the user policy untouched.

## Evidence boundary

The verifier checks YAML glob examples, profile structure, and setup ownership.
It does not execute hazardous commands, prove arbitrary script safety, or replace
version-specific native CLI/IDE runtime observations.

## Cleanup boundary

Tests use disposable fixtures and normal test caches. They do not install global
permission rules or change CI profiles.

## Gotchas

- An existing ask or deny overrides a new allow across Kiro scopes.
- Tool permission does not grant authority beyond the user's requested task.
- Shell source-text matching does not resolve aliases or arbitrary scripts.

## Verification

The stored command reads the packaged YAML and canonical consumer profiles and
exercises project setup. Its scope is bounded by the evidence boundary above.
