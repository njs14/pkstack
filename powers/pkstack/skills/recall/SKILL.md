---
name: recall
description: Recover relevant project context from the current Kiro session and explicit repository knowledge without silently mining unrelated private conversations.
---

# Recall relevant context

Treat the request text that activated this skill as the decision or topic whose prior context is
needed.

Search only sources legitimately in scope: the current conversation, loaded Kiro steering, project
files, feature records, canonical `okn` through `.pkstack/bin/projectctl knowledge search`, git
history, and task history the user explicitly supplied or authorized. Do not crawl unrelated chats,
editor databases, home directories, or credentials.

Start at the matching feature record and its explicit related links. Escalate to one bounded,
targeted knowledge query only when that packet cannot answer an architecture, decision, concept, or
operations question. Record the selected depth and the concrete reason for escalation; never load
the whole Wiki as ambient context.

Find decisions, constraints, abandoned approaches, and evidence that could change the current next
step. Prefer original artifacts over summaries and verify drift-prone claims against the live
repository. Label each result as current evidence, historical decision, or inference. Return a
compact reconstruction with source locations, conflicts, and anything that could not be recovered.
