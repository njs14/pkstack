---
name: improve-claude-md
description: Improve CLAUDE.md while preserving commands and making conditional guidance concise; on Kiro, also translate applicable guidance into AGENTS.md or steering when requested.
compatibility: Kiro IDE 1.x and Kiro CLI v3; Kiro Crew compatible; Kiro Web supported by design but untested; edits Claude compatibility files or Kiro instructions as requested.
---

# Improve agent instructions

Treat the request text that activated this skill as the editing task. Inspect the target instructions and repository before editing. Preserve the writer's intent, every
useful command, the project identity, project map, security boundaries, and non-obvious constraints.

For `CLAUDE.md`, keep universally relevant context as plain Markdown and wrap domain-specific rules
in narrowly worded `<important if="...">` blocks. For Kiro-native output, place universal agent
agreements in `AGENTS.md` and narrowly scoped knowledge in `.kiro/steering/` using the repository's
existing convention; do not assume Claude-specific XML changes Kiro weighting.

Remove vague exhortations, stale examples, duplicated rules, prose already enforced by tooling,
and code snippets better replaced by stable file references. Never remove a command merely because
it is infrequently used. Keep each rule in one source of truth and preserve stronger local safety
instructions.

Show a concise before/after structure and validate that referenced paths and commands still exist.
Do not rewrite unrelated instruction files unless the user asked for cross-agent normalization.
