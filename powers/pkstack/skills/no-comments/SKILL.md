---
name: no-comments
description: Remove stale, redundant, or compensating code comments while preserving external contracts and the non-obvious reasons maintainers genuinely need.
---

# Make the code explain itself

Treat the request text that activated this skill as the code area whose comments
and suppressions should be reviewed.

## Fix the scope

Use the caller's explicit files or diff. If none is supplied, inspect the
current diff against the base branch, defaulting to `main`, and include both the
index and working tree. Record the chosen base and exact paths before editing.
Do not sweep outside that fence.

Preserve license notices, generated-file warnings, public API contracts,
protocol constraints, safety invariants, compatibility reasons, and tradeoffs
that remain non-obvious after reading the code. Treat lint or type suppressions
and workaround comments as defect leads. Remove syntax narration, stale
history, commented-out code, labels duplicated by good names, and comments that
only compensate for unclear structure.

## Get and adjudicate a fresh report

1. Ask a fresh native Kiro sub-agent, using a read-only profile, to inspect the
   exact scope. Do not give it the author's classifications or proposed keeps.
   Require a report of comments and suppressions only, not application-code
   edits.
2. Inspect the report and its claimed diff against the actual files. Reject
   scope escapes, application-code edits, exception-protected deletions,
   misstated kill reasons, or flags that blame intentional code which remains.
   Independently audit missed scoped lint and TypeScript suppressions.
3. For a thin constraint comment such as "do not remove" or "do not change",
   use `how` or `why` on the symbol before accepting either deletion or
   retention. A keep needs evidence that it describes something this scope
   cannot change. If that evidence refutes the keep or remains ambiguous, do
   not restore the comment; record the unenforced constraint.
4. If the first report violates the contract, reject it and run exactly one
   fresh review again with the failure named. If the second report also fails,
   stop this workflow as failed and report the review defect as open.

## Fix accepted findings

Prefer clearer names, smaller functions, or the real API over replacement
prose. Fix a safe in-scope root cause and remove its workaround. When several
accepted findings require a new structure, use `architect` once for that set,
then implement the smallest coherent shape. Do not widen the scope to repair an
out-of-scope cause; make the narrow safe improvement and report the rest.

For a real constraint still expressed only in a comment, offer the cheapest
in-scope type, runtime check, test, or CI rule that would enforce it. Wait for
explicit approval before making that structural change. An unattended run may
encode it only when the caller pre-authorized that exact class of edit. If it is
not approved, leave code unchanged, remove only a refuted comment, and report
the constraint and proposed encoding.

Run the focused tests, lint, and typecheck that cover the changed area. Return
the exact deletion count, every restored comment with evidence, review reruns,
accepted fixes, any architect shape, encoding offers and approvals, completed
encodings, unenforced constraints, and remaining open work.
