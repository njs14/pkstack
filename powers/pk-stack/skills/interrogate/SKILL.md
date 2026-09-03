---
name: interrogate
description: Route a high-stakes proposal through the PK-Stack model council for evidence-bound challenge, without granting reviewers implementation authority.
compatibility: Kiro IDE 1.x and Kiro CLI v3; Kiro Crew compatible; Kiro Web supported by design but untested; optional external advisors require user-provided access.
---

# Interrogate a proposal

Treat the request text that activated this skill as the artifact and decision to challenge.

Apply the [`model-council`](../model-council/SKILL.md) workflow when its
optional advisors are available, and use independent native Kiro reviewer
sub-agents for the required review lenses. Reviewers receive evidence but no
implementation authority. Read
[`references/review-contract.md`](references/review-contract.md) before
delegating.

## Establish scope and intent

1. Resolve the exact diff, files, design, or proposal from the request and
   current repository. Include enough unchanged surrounding code to trace
   reachable paths.
2. State one paragraph of intent from the request and repository evidence.
   Review execution against that intent; do not silently substitute a different
   goal.
3. Build one bounded evidence packet containing the same artifact, context,
   constraints, acceptance criteria, and requested citations for every
   reviewer.

Ask for concrete findings with file and symbol locations. Broad impressions,
praise, and untraced hypotheticals are not findings.

## Run independent review lenses

Run at least these two lenses independently. A reviewer may apply both, but
each lens must have an independent result before synthesis.

- **Correctness reviewer:** trace happy and failure paths, edge cases, error
  propagation, repeated calls, concurrency, root cause, security boundaries,
  and whether tests observe the real integration rather than a proxy.
- **Code-quality reviewer:** look for behavior-preserving deletion or
  simplification, scattered special cases, shallow indirection, dishonest
  types, boundary leakage, duplicate helpers, logic in the wrong owner,
  unnecessary serialization, and non-atomic state changes.

Reviewers use the same intent and evidence packet so differences reflect
independent judgment rather than different inputs. They do not see each
other's output before returning. Each finding includes severity, location,
reachable evidence, consequence, and a concrete fix when one is justified.

## Apply lead judgment

The current Kiro session is a pragmatic lead, not a vote counter. Deduplicate
findings, show consensus and disagreements, and judge each result with this
rubric:

- Can the reported path actually occur under the real types and callers?
- Is this a correctness, security, or maintainability consequence rather than
  personal style?
- Does the reviewer lack constraints, prior attempts, migration context, or a
  planned follow-up?
- Would the proposed abstraction serve a known second use, or is it premature?
- Can a structural simplification delete complexity without changing behavior?
- Does direct artifact evidence support the finding, and what check would
  prove the repair?

Agreement raises confidence but is not proof. Lone correctness or security
findings still receive full scrutiny. Normalize every result into **Act on**,
**Consider**, **Noted**, or **Dismissed**, naming which reviewers raised it and
the lead rationale. Include an agreement map.

Reviewers are advisory. Never auto-apply output, transfer credentials, or treat
review consensus as verification. The current session owns remediation and
executable acceptance; obtain authorization before any external or destructive
action.
