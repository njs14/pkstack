---
name: unslop
description: Edit prose into concise, specific, human writing while preserving the author's facts, voice, uncertainty, and intended audience.
---

# Remove synthetic-sounding prose

Treat the request text that activated this skill as the prose and editing goal.

For a document's structure, compose this pass with
[`technical-writing`](../technical-writing/SKILL.md) for humans or
[`writing-for-agents`](../writing-for-agents/SKILL.md) for agents. Preserve their technical
claims, triggers, checkpoints, and authority boundaries while editing sentences.

Use three passes:

1. **Scan.** Mark the concrete patterns below without changing meaning.
2. **Rewrite.** Preserve facts, commitments, caveats, intended audience, and the
   writer's recognizable voice. Flag an unclear factual claim instead of
   smoothing it into an invention.
3. **Self-audit.** Ask what still makes the result sound generated. Remove the
   remaining tell, then confirm that the edit did not erase useful nuance.

## Pattern catalog

Check for:

- unsupported grandeur, promotional adjectives, generic scene-setting,
  formulaic obstacle-and-triumph paragraphs, and conclusions with no fact or
  plan;
- outlet or expert name-dropping without a relevant claim, vague attribution,
  cutoff disclaimers used instead of research, and fake quotations;
- shallow participle clauses that claim to explain significance, repeated
  summaries, forced groups of three, false ranges, and synonym cycling for one
  concept;
- stock agent vocabulary and abstract metaphor nouns where a plain project
  term exists, plus ornate substitutes for `is`, `has`, or `use`;
- "not only X but Y" contrast frames, canned transitions, chatbot greetings,
  offers that add nothing, and sycophantic agreement;
- decorative emoji, title-case headings, excessive bold labels, inline headers
  that repeat the sentence, curly quotation marks, and punctuation used as a
  substitute for clear sentence structure;
- filler, stacked hedges, weak verbs propped up by adverbs, passive voice that
  hides a relevant actor, and dense sentences the reader must backtrack to
  parse; and
- claims about how something feels when the text should name a mechanism,
  command, boundary, number, or observable result;
- mannered prose, including aphorisms, personified code, figurative verbs, and
  rhetorical fragments where a literal sentence would work; and
- over-compression that drops articles or verbs, uses unexplained abbreviations,
  or replaces a readable sentence with arrows and symbol notation.

Use periods or commas to separate thoughts. Reserve colons for labels, lists, and examples.
Write complete sentences and preserve the author's existing voice without adding opinions,
informality, or reactions to make the prose sound human.

Prefer plain verbs and specific nouns. Keep technical terms the audience needs
and give each concept one stable name. A sentence that could appear unchanged
in an unrelated project's documentation probably says too little.

Return the revised prose. Add a short note only when a material choice,
uncertain fact, or preserved exception needs explanation.
