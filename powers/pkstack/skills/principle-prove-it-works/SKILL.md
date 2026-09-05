---
name: principle-prove-it-works
description: Before declaring completion, exercise the real artifact and observable path with a deterministic check that would fail if the claim were false.
---

# Prove the result

Treat the request text that activated this skill as the completion claim to verify.

Apply [prove it works](../pkstack-principles/references/catalog.md#prove-it-works). Identify an observation
that would fail if the claim were false, exercise the real user or integration path, and inspect
outputs plus side effects. Prefer a rerunnable check. Mark anything short of direct proof as
inconclusive. Return the exact command, result, and evidence boundary.
