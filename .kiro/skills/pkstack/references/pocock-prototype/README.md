# Choose the question a prototype answers

Use a throwaway prototype to answer one bounded design question. A logic or state question uses
[the state exploration method](LOGIC.md); a visual direction question uses
[the visual alternatives method](UI.md). Infer the branch from the request and context, stating
an assumption when useful. Ask only when choosing wrong would materially change the result.

Native Plan stays conversational and does not create or run prototypes. In execution, use a
clearly marked scratch location or the user's requested place. Keep state in memory unless a
scratch persistence experiment is the question. No real account, payment, or production mutations.
Make the artifact easy to run using established local tools and exercise the scenarios that answer
the question; extensive production hardening is premature, but runnable behavior must be checked.

Capture the question, observations, answer, uncertainty, and artifact identity. Retain accepted
conclusions through the existing OKF lifecycle and link the authoritative native Spec. Preserve
the prototype only where authorized; a request to explore does not authorize branch publication.
Promote validated ideas into production with the normal implementation and verification process,
then remove owned throwaway variants and controls from the production candidate.
