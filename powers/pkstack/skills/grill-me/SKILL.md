---
name: grill-me
description: Interview me to sharpen a plan, idea, or decision and expose consequential assumptions before I commit to it.
---

# Grill me

Read and apply the bundled [`grilling`](../grilling/SKILL.md) method to the activating request.
Use ordinary Kiro skill discovery and file reading; this entrypoint requires no external Skill
API. Reuse settled answers and stop when the requested decision or plan is sufficiently clear.

A standalone decision interview stays conversational and does not automatically create Wiki
files or start implementation. If the user requests an implementation plan, follow the shared
method's native planning handoff and approved-plan knowledge capture checkpoint. A plan's approval
does not override native Plan's read-only phase or an explicit no-write instruction.

Use [`grill-with-docs`](../grill-with-docs/SKILL.md) when the request also includes maintaining
project definitions and decisions as the interview unfolds. It uses the same interview context,
not a second round of questions already settled here.
