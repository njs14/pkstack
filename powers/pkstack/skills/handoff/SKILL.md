---
name: handoff
description: Write a focused resume document for a fresh session or another agent. Use when pausing work, transferring context, or resuming without repeating completed investigation.
---

# Hand off current work

Honor the user's scope and active Kiro workflow. In native Plan, use permitted reading and
search, keep the result conversational, and defer commands, MCP calls, file writes, experiments,
and validation until execution is permitted. A skill invocation does not widen authority.

Tailor the document to the stated next-session purpose. Reuse PKStack's
[Pause and Session pickup](../poteto-kiro-mode/references/workflows.md) checkpoints and existing native
Spec state. Inspect the actual branch, commit, dirty paths, and active operation when commands
are permitted. Distinguish observed current state from earlier conversation claims.

Write one focused Markdown document to the requested location or a fresh OS temporary path.
Include:

- User intent, accepted scope, current authority, and constraints that must survive the handoff.
- Exact working directory, branch/commit, owned dirty paths, active merge or rebase, and any
  confirmed live process handle. A log or lock alone does not prove a process is running.
- Decisions and rationale with links to existing Specs, knowledge, issues, commits, and artifacts;
  reference them instead of copying whole plans or inventing another task ledger.
- Completed work and verification: exact command, result, artifact, and the candidate it applies
  to. State which evidence is stale after subsequent edits and must be rerun.
- Unresolved work, material uncertainty, blockers, and the next concrete action. Name useful
  installed skills and the specific job each would do.

Remove secrets, personal details irrelevant to continuation, and private transcripts. Retain
recovery paths when useful, without copying credentials or session state. The receiving session
must inspect current state, reuse valid completed work, and revalidate only what has changed.
Report the path and next action; creating the document does not send it to another person or
change the active native workflow. Durable knowledge still follows the existing OKF lifecycle.
