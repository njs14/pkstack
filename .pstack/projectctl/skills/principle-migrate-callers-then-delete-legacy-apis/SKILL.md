---
name: principle-migrate-callers-then-delete-legacy-apis
description: When no external compatibility promise applies, inventory callers, migrate them to the chosen internal API, and remove the old path in the same bounded wave.
---

# Remove the retired path

Treat the request text that activated this skill as an internal API migration.

Apply [migrate callers, then delete legacy APIs](../principles/references/catalog.md#migrate-callers-then-delete-legacy-apis).
Prove the consumer inventory and external obligations first. Move coordinated callers, delete the
old implementation and obsolete tests, and time-box any adapter a verified external consumer still
needs. Return the inventory, removed path, and compatibility evidence.
