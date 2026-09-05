---
name: teach
description: Teach a technical concept by connecting how it operates, why it was designed that way, and concrete examples without quizzing the user.
---

# Teach the concept

Treat the request text that activated this skill as the concept and likely audience.

Calibrate from the conversation and the user's demonstrated expertise. Do not
quiz them to establish a level. Decide the few things they should leave
understanding based on whether they are changing, reviewing, debugging, or
learning the subject.

## Compose `how` and `why`

Read only enough code to locate the subject. Then apply the `how` skill to its
runtime mechanics and the `why` skill to its rationale. These are real skill
applications, not labels for a hand-written substitute. For a subsystem, run
them independently in parallel through bounded native sub-agents when
available, then synthesize their results. One may be enough for a very small
question, but state which lens was unnecessary and why.

Keep `why` narrow unless historical rationale is the point. Give it the scoped
question and useful source categories, and retain its coverage gaps and
confidence words unchanged in the teaching answer. Never rewrite `inferred`,
`speculative`, or `unknown` into certainty. Do not redo either investigation by
hand.

## Build the explanation in layers

Start with a one- or two-sentence plain definition and the practical case in
front of the user. Stop there when it answers the question. Add mechanics,
design reasons, edge cases, and a verified example only as needed. Walk through
what the user or caller does when that sequence teaches better than a list of
functions. Define necessary jargon once and distinguish an analogy from literal
behavior.

Draw only when a relationship or sequence becomes clearer. With three or more
moving parts, use a progressive series: draw the first relationship, redraw it
and add exactly one part, then redraw again for the next part or return edge.
Do not replace teaching with one crowded final diagram. Use a simple text or
Mermaid diagram supported by the selected Kiro surface; a single simple point
needs no figure.

Keep it conversational and let the user choose whether to go deeper. Do not
quiz the user, assign an exercise, demand a restatement, announce a fake pause,
or require a response to prove understanding. In a one-shot run, give the
smallest complete explanation and put any optional deeper thread at the end.
Return the explanation itself, not a report about the teaching workflow.
