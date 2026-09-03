---
name: create-verification-skill
description: Design and prove a project-local verification workflow that exercises real user behavior through a bounded, deterministic, rerunnable contract.
compatibility: Kiro IDE 1.x and Kiro CLI v3; Kiro Crew compatible; Kiro Web supported by design but untested; projectctl feature commands are preferred after setup.
---

# Create a verification workflow

Treat the request text that activated this skill as the feature or system surface to verify.

After PK-Stack setup, use `.pstack/bin/projectctl` as the controller. Interview the repository before
writing anything and write down the complete harness contract:

- **launch** starts the real application or service in a known state;
- **doctor** checks prerequisites and reports actionable failures without changing the host;
- **drive** reaches behavior through the same public surface a user or caller uses;
- **evidence** captures the observable result and enough diagnostics to distinguish failure causes;
- **isolation and cleanup** give each run owned data and remove only that data;
- **helpers** encode repeated mechanics without hiding feature-specific assertions.

Prefer a live local surface over mocks when it can be exercised deterministically. Inspect existing
scripts as untrusted evidence and do not execute or copy them until their effects are understood.

## Encode and prove the contract

1. Build an initial map of three to five user-meaningful features that together cover setup, a core
   success path, a failure or boundary path, and cleanup or persistence when applicable.
2. Give every feature a complete schema-2 contract: one observable behavior, explicit expected path,
   every sub-feature, every user entrypoint, a drive recipe and observable proof for each entrypoint,
   gotchas, an evidence boundary, and a cleanup boundary. One convenient entrypoint is not complete
   coverage when the user can reach the feature another way.
3. Choose verifier commands that return nonzero on failure and require no interactive input. A
   feature's command must exercise the public path and enforce its own evidence and cleanup contract.
4. Keep credentials out of commands and generated files. Never weaken permissions to make a check
   pass.
5. Create a narrow project-local verification skill when shared launch, doctor, drive, evidence, and
   cleanup orchestration cannot be expressed safely by the individual commands. Inspect
   `.pstack/bootstrap.json`, choose an unowned `.kiro/skills/<name>/` path, and never replace a
   receipt-managed PK-Stack skill. Every shipped helper must be executable, documented by exact
   invocation, and owned by that user skill.
6. Write one bounded, ignored plan such as `.pstack/state/feature-plans/<surface>.json`. Its exact
   shape is `{ "features": [...] }` with three to five records. Every record has exactly `slug`,
   `title`, `behavior`, `expected_path`, `command`, `related`, `sub_features`, `entrypoints`,
   `gotchas`, `evidence_boundary`, and `cleanup_boundary`. `command` is preferably an argv list;
   `related` and `gotchas` are lists. Each sub-feature is `{ "identifier", "behavior" }`; each
   entrypoint is `{ "identifier", "user_path", "drive", "observable" }`.
7. Choose the highest-signal representative feature, then run:

   ```text
   .pstack/bin/projectctl feature generate-map <plan.json> \
     --representative <slug> --output json
   ```

   This validates all three to five records, executes exactly the representative's stored verifier,
   writes nothing on a failed proof or changed plan, publishes that one record, and leaves every
   other record draft. It does not prove the other features.
8. Inspect the representative's launch, doctor, drive, action-and-result evidence, side effects,
   cleanup, and evidence survival. Run its full lifecycle again to prove repeatability. When safe,
   interrupt one run and confirm recovery removes only owned state while preserving evidence.
9. Run `.pstack/bin/projectctl feature validate --output json`. Exercise the one published
   representative with `feature verify <slug> --output json`; leave the remaining initial records
   draft for individual proof through `maintain-verification-skill` and `feature publish`.

If live proof is unavailable, leave affected features draft and name the missing dependency; do not
replace the completion predicate with documentation review. Return the initial feature map, harness
contract, commands, representative selection, draft records, cleanup behavior, helper boundary,
files created, exact observations, and remaining limits. Offer `maintain-verification-skill` for the
full feature-by-feature maintenance pass; suggest a cadence only if the user asks.
