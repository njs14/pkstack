---
name: resolving-merge-conflicts
description: Resolve an in-progress Git merge or rebase by recovering both sides’ intent, preserving unrelated work, and verifying the integrated result.
---

# Resolve a merge or rebase

Honor the user's scope and active Kiro workflow. In native Plan, use permitted reading and
search, keep the result conversational, and defer commands, MCP calls, file writes, experiments,
and validation until execution is permitted. A skill invocation does not widen authority.

Inspect status, the active operation, conflicting paths, index stages, and both histories before
editing. Record unrelated dirty or staged files and preserve them. Do not start a new merge merely
because this skill was invoked. Recover intent from base/ours/theirs, commit messages, linked PRs,
issues, tests, and existing decisions. During rebase, Git's “ours” and “theirs” describe operation
sides, so identify the actual commits instead of assuming branch labels mean the same thing.

Resolve each owned conflict to preserve both changes where compatible. A rename on one side and
a behavior fix on the other usually require integrating both. Do not blindly choose whole files,
remove tests, or invent behavior to satisfy syntax. For incompatible requirements, follow the
stated merge goal and explain the tradeoff; ask one targeted question if that goal cannot decide.

Run repository-prescribed checks on the integrated paths and their callers. Inspect the complete
resolved diff, conflict-marker state, and remaining unmerged index entries. Stage only successfully
resolved owned paths by explicit name. Leave unrelated index entries as found.

Continue a rebase or finish a merge only when the user has authorized that operation and its
resulting commits. Do not bundle pre-existing staged changes into a commit: isolate the owned
resolution or stop before committing with the exact unresolved scope. Abort only when authorized;
a request to resolve does not forbid an explicitly requested abort. Reinspect each new rebase
conflict and repeat until the authorized operation completes. Report integrated intents, checks,
remaining conflicts, and whether staging, continuation, or commit actually occurred.
