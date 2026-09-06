---
name: grill-me
description: Interview me to sharpen a plan, idea, or decision and expose consequential assumptions before I commit to it.
---

# Grill me

Read and apply the bundled [`grilling`](../grilling/SKILL.md) method to the activating request.
Use ordinary Kiro skill discovery and file reading; this entrypoint requires no external
Skill API. Keep the interview conversational, resolve facts through inspection, and stop when
the decision is sufficiently clear or the user stops it.

For a request that explicitly includes maintaining project definitions and decisions, use
[`grill-with-docs`](../grill-with-docs/SKILL.md). Otherwise return the interview's conclusions
without creating a document or starting implementation solely because the interview ended.
