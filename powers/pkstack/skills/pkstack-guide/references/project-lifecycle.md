# Project lifecycle advice

Use the section matching the user's uncertainty. These are decision aids, not a mandatory
sequence. Operational checkpoints belong to the linked skills and to
[PKStack's workflow reference](../../pkstack/references/workflows.md).

## Starting a project

Establish the user or caller, one useful outcome, and the smallest slice that could demonstrate
it. If product intent is unclear, recommend a focused [grill-me](../../grill-me/SKILL.md)
conversation; a full implementation plan belongs in the native Kiro workflow.

For a shared package or unfamiliar developer experience, work backwards from a caller example
or a tutorial using [technical-writing](../../technical-writing/SKILL.md). Choose the document's
job: tutorial, how-to, reference, or explanation. A tutorial is not an API dump or a substitute
for running its example.

Pair the first runnable slice with a feedback loop. Before an app exists, do not demand a
completed app-wide verification skill. When stack selection is open, consider whether the
agent can launch, control, diagnose, and observe the proposed surface; debugging support is a
tradeoff, not permission to migrate an established stack. Recommend
[pkstack-setup](../../pkstack-setup/SKILL.md) when repository scaffolding is missing and adoption
is wanted. Setup is not proof that the product works.

## Understanding an existing project

Restate the underlying issue before endorsing a proposed cause. Start from the relevant
feature, native Spec, README, code, and linked decisions, not a whole-repo survey. Use
[how](../../how/SKILL.md) for mechanics, [why](../../why/SKILL.md) for rationale, and
[teach](../../teach/SKILL.md) when the human needs an intuitive explanation of both.
[recall](../../recall/SKILL.md) recovers in-scope context; it does not grant access to unrelated
chat histories or guarantee Slack, tickets, monitoring, or analytics are connected.

Preserve useful existing scripts, tests, verification skills, and decisions. Distinguish an
unfamiliar system from an unhealthy one. No new harness or architecture exercise is necessary
merely because a project is adopting PKStack.

## Establishing trustworthy feedback

Identify how a real user or caller reaches the behavior and what would demonstrate the
expected result. Useful verification usually needs a known starting state, actionable
prerequisite checks, a repeatable drive path, evidence, and bounded cleanup. Reusable project
commands should reduce repeated effort, disclose capabilities through help, report failures
clearly, and make dangerous effects previewable. Reuse suitable tools before inventing a CLI.

Use [create-verification-skill](../../create-verification-skill/SKILL.md) for missing coverage
of the actual surface; use [maintain-verification-skill](../../maintain-verification-skill/SKILL.md)
for drift in an existing workflow. A public library API exercised by a real test can be its
matching surface; a UI screenshot alone cannot prove persistence, and unit tests alone cannot
establish an unexercised UI journey. Judge the claimed behavior, not the tool category.

Feature records make paths, gotchas, and proof discoverable. Their presence, draft/publication
state, and past receipts do not replace a current run when current behavior is being claimed.
If observed failures concern the product rather than the verifier, preserve the expectation
and route the defect separately. If the harness is already adequate, use it and move on.

## Choosing a design

Choose the smallest method that can settle the open question:

- External facts or guarantees: [research](../../research/SKILL.md), with primary sources.
- Logic, state, interaction, timing, or appearance that must be observed: the Prototype workflow
  through `/pkstack prototype ...`; there is no separate installed `/prototype` command.
- A significant API, data model, or system boundary: [architect](../../architect/SKILL.md),
  starting from usage and comparing meaningful alternatives.
- An already selected artifact that needs competing attempts: [arena](../../arena/SKILL.md),
  without duplicating the same architecture comparison.

State the decision a prototype should settle and the observations needed. Compare real variants
when useful, then carry the evidence into the chosen design. A prototype is not production proof.
Repeated call-site workarounds or type escape hatches are reasons to revisit the design, not
automatic proof that every cast is wrong. Avoid adversarial ceremony over abstract plans when
a small permitted experiment would resolve the uncertainty. Advisory mode proposes that
experiment; it does not run it.

## Moving from design to implementation

Read [pkstack](../../pkstack/SKILL.md) for native Plan, Spec, Quick Spec, and Bug Fix selection
and exact client-specific handoffs. Resume an existing native package rather than recreating
its decisions or tasks. Keep small work small. An explicit plan-only request still belongs to
native Plan; prototypes wait until execution is permitted.

After approval, execution uses the existing workflow and
[pkstack-verified-goal](../../pkstack-verified-goal/SKILL.md) for the checkable outcome. Recommend
small, independently verifiable units and proof on the matching surface. Kiro owns native task
dependencies and approvals; the guide creates no parallel ledger or completion predicate.
Carry accepted knowledge through [okf](../../okf/SKILL.md) at the existing lifecycle checkpoints.
Do not copy a temporary plan into permanent knowledge or delete native Specs to imitate an
upstream cleanup practice.

## Bugs, upkeep, and completion

Use [diagnosing-bugs](../../diagnosing-bugs/SKILL.md) for a defect requiring a tight reproduction
and tested hypotheses; [triage](../../triage/SKILL.md) for incoming reports;
[improve-codebase-architecture](../../improve-codebase-architecture/SKILL.md) for a requested
survey of structural friction; and verifier maintenance for coverage drift. Preserve the
difference between an assessment and permission to repair.

For transfer or interruption use [handoff](../../handoff/SKILL.md) only when portable context is
needed. For PR status or continued observation use [babysit-pr](../../babysit-pr/SKILL.md) with
the user's actual terminal condition and write authority. Do not turn advice into a scheduled
job, publication, model change, or a cloud/worktree migration. Suggest cadence or parallelism
when the workload and user request justify them, not as universal prerequisites.

## Sources and Kiro adaptations

This is locally authored PKStack guidance, informed by the user-supplied exports of lauren
(@poteto)'s [Part 1: Verification is all you need](https://x.com/poteto/article/2094457600259842065)
(2026-08-31) and [Part 2: Research, Planning, Prototyping, and Architecture](https://x.com/poteto/status/2097732320606507506)
(2026-09-09). The supplied Part 1 export is incomplete and omits command and feature-map examples;
no missing example is reconstructed here. The
[verification-skill example](https://github.com/poteto/verification-skill-example) is fictional
and intentionally omits its driver implementation.

[ask-matt at the catalog pin](https://github.com/mattpocock/skills/blob/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/ask-matt/SKILL.md)
informs the idea of a situation-to-workflow advisor. Its package remains excluded: this is not
a port of its persona, tracker flow, context thresholds, or setup. Native Kiro planning and
PKStack's existing knowledge and verification ownership take precedence over source examples.
No Cursor cloud dependency, fixed model family, transcript crawler, daily automation, or new
upstream executable is introduced. These dated editorial inputs are not an automatically
synchronized source inventory; future revisions require reviewing the affected advice.
