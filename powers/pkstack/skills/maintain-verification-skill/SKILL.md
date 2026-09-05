---
name: maintain-verification-skill
description: Audit and update an existing verification workflow against current user-visible behavior while preserving scope, safety, and executable proof.
---

# Maintain a verification workflow

Treat the request text that activated this skill as the verification surface to audit.

Do not assume a passing old check still covers current behavior. Preserve this sequence:

1. **Locate the surface.** Find the authoritative verification skill, its feature-map index, every
   feature record, executable commands, implementation entrypoints, and existing evidence. Use
   `.pkstack/bin/projectctl feature list --output json` and `feature show <slug> --output json` when
   PKStack is set up. Feature records use schema 2; unsupported records need a fresh reviewed
   contract grounded in the current implementation and public surface.
2. **Check index hygiene.** Reconcile the index, feature files, and user-visible surface. Record
   missing, stale, duplicate, or orphaned entries before editing.
   Also find native `.kiro/specs/*/pkstack-verification.json` bridges. Treat their
   `requirements.md` or `bugfix.md`, `design.md`, and `tasks.md` as Kiro-owned planning artifacts;
   reconcile each bridge to its exact published feature or reviewed command without rewriting the
   native plan.
3. **Run independent source audits.** Keep one live coordinator responsible for the shared runtime
   and evidence surface. Assign one read-only native Kiro sub-agent per feature when the
   records are independent. Each compares the claimed behavior and path with current code and real
   entrypoints and returns file pointers, drift, and risks. Do not let auditors edit shared files.
4. **Reconcile first.** Combine the audits into one coverage ledger. Classify each feature as
   **clean**, **changed**, or **blocked** and distinguish product drift from verifier drift.
5. **Run the mandatory live pass.** The single coordinator exercises every feature's launch,
   doctor/preflight, drive,
   evidence capture, failure recovery, evidence survival, and cleanup/residue checks on its real
   surface. Static inspection or a unit-only shortcut cannot replace this pass. After an initial
   failed drive, allow exactly one recovery retry. If the real surface remains unreachable, record
   **verified-unreachable** with the failed commands and environment evidence rather than retrying
   indefinitely or substituting inspection. Verify that failed attempts leave no unsafe residue and
   that bounded evidence remains available after cleanup.
6. **Triage and repair verifier scope.** Modify only the project-local, user-owned verification skill
   and feature records unless the user separately requested product repairs. Never relax an
   expectation to preserve green output. Keep blocked checks explicit.
7. **Prove or stop.** For every remaining initial-map draft, review its complete contract and run
   `.pkstack/bin/projectctl feature publish <slug> --output json`; publication executes the stored
   verifier and changes draft state only after it passes. For an already published verifier changed
   during this pass, run `feature verify <slug> --output json`. Never hand-edit `draft: false` or use
   another feature's evidence. Then run `.pkstack/bin/projectctl feature validate --output json` and
   nearby tests. Report a clean, changed-and-proved, verified-unreachable, or blocked outcome. When
   verifier assets changed and the user separately authorized a pull request, group the maintenance
   result into one reviewed pull request rather than one per feature. Without that authorization,
   leave the local result and report the exact next action.
8. **Refresh spec bindings last.** After a changed feature passes its required proof, rerun
   `.pkstack/bin/projectctl goal bind-spec <spec-name> --feature <slug> --output json`. An identical
   bridge is a no-op. A changed bridge requires explicit `--overwrite` only after comparing the old
   and new contracts. Never preserve green output by pointing a spec at a weaker verifier.

Keep scratch audit notes uncommitted. Return the index reconciliation, per-feature outcome, changed
contracts, exact live runs, recovery and residue results, observed side effects, and unverified gaps.
