---
name: technical-writing
description: Write or revise technical documentation for a specific reader and task, with verified commands, direct language, and maintainable information placement.
---

# Write useful technical documentation

Treat the request text that activated this skill as the document, audience, and outcome.

This method serves human readers: tutorials, how-to guides, references, and explanations.
For instructions consumed by an agent, use
[`writing-for-agents`](../writing-for-agents/SKILL.md). For mixed audiences, keep each audience's
instructions in its own linked document and reuse verified facts across them.

Write for a tired engineer who needs the correct result on the first read.
Inspect the implementation and existing documentation before writing. Use the
real symbol, file, flag, command, and product name; do not invent a synonym for
something the code already names.

For project knowledge, use the existing topic and
[`OKF document lifecycle`](../okf/references/document-lifecycle.md). Drafts belong in
`Wiki/work/`; durable explanations belong in `Wiki/knowledge/`. Preserve explicit
native destinations for package documentation, skills, steering, and Kiro specs.
Do not move an existing document merely because this skill is being used.

Apply all four layers below. They answer different questions: what document is
this, how does each sentence address the reader, how much does it ask the reader
to load, and can it be read more than one way.

## 1. Pick one Diátaxis (Diataxis) mode

Choose from the reader's job, not the material available:

- **Tutorial:** action while learning. Build one thing through visible,
  successful steps; keep explanation brief and linked.
- **How-to:** action during real work. Assume competence, lead with the goal,
  allow necessary forks, and exclude background lessons.
- **Reference:** facts for lookup. Mirror the product or API structure and state
  names, options, defaults, limits, errors, and compatibility without opinion.
- **Explanation:** understanding while learning. Bound one why question and
  discuss context, history, alternatives, and tradeoffs.

Do not mix modes to make one page comprehensive. Split the material and link
where modes meet.

## 2. Use Google developer sentence style

- Address the reader as “you” and use present tense.
- Name the actor and action. Use passive voice only when the actor is unknown or
  irrelevant.
- Write instructions as commands. Put the condition before the command and the
  common path before exceptions.
- Lead with the outcome. Put prerequisites before commands, expected
  observations after them, and recovery beside the likely failure.
- Use sentence-case headings that carry the point. Use numbered lists for
  sequences and bullets for other sets; keep items parallel.
- Use descriptive link text rather than “click here.” Link volatile detail to
  its authority instead of copying it.
- Avoid buzzwords, figurative language, “please,” and claims that a task is
  simple or easy.

## 3. Make STE load one thing at a time

Use Simplified Technical English discipline without writing robotic prose:

- Put one instruction in each sentence and one thought in each other sentence.
- Split a sentence when a reader must retain one action while parsing another.
- Put a warning or condition before the step it controls.
- Keep articles and verbs that make the grammar explicit.
- Give one word one meaning and one action one verb throughout the document.
- Prefer direct commands over narration or passive obligation.
- Cut words that do no work, but keep every word needed to parse the sentence.

One load at a time does not mean one sentence length. Mix short and long
sentences when each still carries one coherent thought.

## 4. Remove Global English ambiguity

- Put `only`, `not`, and other modifiers next to what they modify.
- Break long noun strings into clauses that state the relationship.
- Make each pronoun point to one noun; repeat the noun when uncertain.
- Give every coordinated clause its own verb when omission permits two readings.
- Make `and` and `or` grouping explicit with `both`, `either`, or a rewritten
  list.
- Use one name per concept. Do not rename the same thing for variety.
- Prefer periods to semicolons or em dashes. Avoid slashes, idioms, unexplained
  abbreviations, and culture-specific metaphors.
- Make parenthetical text grammatical, or move it into its own sentence.

Apply [`unslop`](../unslop/SKILL.md) after the four layers. That pass removes
filler and stock phrasing; it does not replace technical verification.

## Review checklist

Before returning the document, check each item:

1. Is the audience and job explicit, and is each file one Diataxis mode?
2. Does the opening state the useful outcome?
3. Are prerequisites, commands, expected results, and recovery in reader order?
4. Is every instruction a command with its condition first?
5. Does each sentence load one instruction or one coherent thought?
6. Can any filler word be removed without losing meaning?
7. Is each modifier beside its target, each pronoun unambiguous, and each clause
   complete?
8. Does every concept keep one name across files?
9. Are headings, lists, links, and code formatting structurally correct?
10. Are security boundaries, compatibility limits, and untested claims explicit?
11. Do paths, symbols, flags, defaults, counts, and error text match the current
    implementation?
12. Did you run each safe example or the closest faithful check and record what
    remains documentation-only?

Return the intended reader and mode, files changed, examples and links checked,
and every claim that remains unverified.
