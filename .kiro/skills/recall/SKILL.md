---
name: recall
description: Recover relevant project context from the current Kiro session and explicit repository knowledge without silently mining unrelated private conversations.
compatibility: Kiro IDE 1.x and Kiro CLI v3; Kiro Crew compatible; Kiro Web supported by design but untested; projectctl knowledge and git history are optional sources.
---

# Recall relevant context

Treat the request text that activated this skill as the decision or topic whose prior context is
needed.

Search only sources legitimately in scope: the current conversation, loaded Kiro steering, project
files, `.pstack/bin/projectctl knowledge search`, feature records, git history, and task history the
user explicitly supplied or authorized. Do not crawl unrelated chats, editor databases, home
directories, or credentials.

Find decisions, constraints, abandoned approaches, and evidence that could change the current next
step. Prefer original artifacts over summaries and verify drift-prone claims against the live
repository. Label each result as current evidence, historical decision, or inference. Return a
compact reconstruction with source locations, conflicts, and anything that could not be recovered.
