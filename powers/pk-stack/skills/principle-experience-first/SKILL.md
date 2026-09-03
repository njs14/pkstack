---
name: principle-experience-first
description: Resolve product, API, and workflow tradeoffs from the consuming user's experience, including failure and maintenance paths, rather than implementation convenience.
compatibility: Kiro IDE 1.x and Kiro CLI v3; Kiro Crew compatible; Kiro Web supported by design but untested.
---

# Design from the user's seat

Treat the request text that activated this skill as an experience tradeoff.

Apply [experience first](../principles/references/catalog.md#experience-first). Identify the actual
consumer, trace the core success and failure paths, and remove surface area that does not improve
that loop. Treat maintainers and API callers as users too. Return the user-visible decision and the
behavior that proves it is better.
