---
name: to-questionnaire
description: Create a focused questionnaire for a person who holds missing knowledge. Use to obtain facts or decisions asynchronously while reusing known answers; creates the document without sending it.
---

# Create a questionnaire

Honor the user's scope and active Kiro workflow. In native Plan, use permitted reading and
search, keep the result conversational, and defer commands, MCP calls, file writes, experiments,
and validation until execution is permitted. A skill invocation does not widen authority.

Reuse known recipient context, settled answers, and the user's stated decision. Inspect existing
artifacts before asking questions. If a material gap remains, use [grilling](../grilling/SKILL.md)
to ask about the recipient's role/expertise and the result the user needs, rather than asking the
user to answer the unknown subject themselves. Do not reopen settled preferences.

Draft a short discovery questionnaire aimed at what the recipient knows that the user lacks.
Order the consequential unknowns first, one idea per question. Provide enough context for someone
outside this conversation and use the recipient's vocabulary. Include:

- Purpose and the decision depending on the answers; sender, recipient, and intended use when known.
- A brief context paragraph including settled facts, so they need not be asked again.
- How to answer, known deadline, and approximate effort when justified. Welcome partial answers
  and explicit uncertainty; do not invent a deadline or commitment.
- Questions grouped by theme only when useful, with an answer space beneath each. Explain why a
  question matters only when its relevance could be missed.
- One closing invitation to add consequential information the questions missed.

Verify every requested knowledge gap has a question and no question asks for secrets. Write the
artifact to the requested path or `to-questionnaire-<topic>.md` in the existing working area.
Report the path and intended recipient. Sending or posting requires separate explicit authority;
retain later accepted answers through the existing project knowledge lifecycle.
