---
name: recall
description: Recover relevant project context from the current Kiro session and explicit repository knowledge without silently mining unrelated private conversations.
---

# Recall relevant context

Treat the request text that activated this skill as the decision or topic whose prior context is
needed.

Search only sources legitimately in scope: the current conversation, loaded Kiro steering, project
files, feature records, bounded Kiro retrieval through `.pkstack/bin/projectctl knowledge search`, git
history, and task history the user explicitly supplied or authorized. Do not crawl unrelated chats,
editor databases, home directories, or credentials.

Start at the matching feature record and its explicit related links. Escalate to one bounded,
targeted knowledge query only when that packet cannot answer an architecture, decision, concept, or
operations question. Use `--budget 1200`; this caps returned context, not internal model token use.
Leave model selection to Kiro unless the user explicitly selects a supported retrieval model;
automatic selection does not report its resolved model. Unavailable Kiro retrieval fails
explicitly; do not substitute a backend or model. Record the selected depth and the concrete
reason for escalation; never load the whole Wiki as ambient context.

Find decisions, constraints, abandoned approaches, and evidence that could change the current next
step. Prefer original artifacts over summaries and verify drift-prone claims against the live
repository. Label each result as current evidence, historical decision, or inference. Return a
compact reconstruction with source locations, conflicts, and anything that could not be recovered.

Ordinary knowledge retrieval uses an isolated read-only Kiro ACP worker over `Wiki/knowledge/`,
`Wiki/features/`, and `.kiro/specs/`. Keep its source paths, exact quotes, line ranges, SHA-256
values, and uncertainties with conclusions. Working notes in `Wiki/work/` require an explicit
task path and are excluded from this search. Native specs remain authoritative in place. Respect
supersession and unresolved questions; do not ask the user to repeat a settled definition unless
current evidence exposes a consequential contradiction.

Retrieval ends with that reconstruction. Use [`reflect`](../reflect/SKILL.md) to propose lessons
from completed work and [`okf`](../okf/SKILL.md) when the user requests durable project knowledge.
Pass the inspected sources forward; recall alone does not write either lessons or knowledge.
