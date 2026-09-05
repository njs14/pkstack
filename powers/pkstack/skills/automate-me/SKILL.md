---
name: automate-me
description: Turn a demonstrated, repeatable working style into a reviewable project-local Kiro skill without mining private transcripts or publishing changes automatically.
---

# Capture a repeatable working style

Treat the request text that activated this skill as the behavior to make repeatable.

Use only the current conversation, repository guidance, explicitly supplied examples, and evidence
the user asked you to inspect. Do not crawl unrelated conversations, private history, or editor
databases. Separate durable instructions from one-off task details, credentials, model choices, and
machine-specific paths.

## Build the skill

1. Describe the trigger, desired outcome, constraints, and evidence of success in plain language.
2. Ask one focused question only if two materially different behaviors remain plausible.
3. Inspect `.pkstack/bootstrap.json` when present and choose a narrowly named project-local
   `.kiro/skills/<name>/SKILL.md` that is not receipt-managed by PKStack. Writing a new unowned
   skill still follows the selected Kiro agent's approval policy; never overwrite a managed skill.
4. Keep the main file short. Put optional detail in a relative `references/` file only when it will
   be loaded on demand.
5. Make permissions and external effects explicit. Never embed secrets, fixed model identifiers,
   automatic publishing, or destructive cleanup.
6. Validate the skill against one normal example and one boundary or failure example.

Return the captured behavior, evidence used, files written, validation performed, and any decisions
left to the user. Do not create a commit or pull request unless separately requested.
