# Review the observed interface

`critique` evaluates hierarchy, clarity, information architecture, cognitive load, product
identity, and whether the real user can complete the intended journey. `audit` evaluates
implementation evidence: accessibility, performance, responsiveness, theming, and consistency.
Both are report-only unless repair is included in the request.

Inspect representative screens and the complete task path before reporting. Include loading,
empty, error, success, long-content, and permission states that the product actually exposes.
Use the [quality checks](quality.md) in the same inspection round; reuse current findings.
For native apps, inspect the actual supported device classes and platform controls rather
than applying web DOM checks. If tooling is unavailable, label the unverified dimensions.

For each finding, record its location, reproduction or screenshot evidence, user impact,
severity, and a concrete repair. Distinguish a broken interaction or inaccessible path from
a preference about style. Verify automated warnings against source and behavior before
promoting them to findings. No Impeccable detector ships here; never claim a detector score,
rule count, or accessibility certification from this review.

Prioritize blocked tasks and data loss, then significant usability/accessibility problems,
then local inconsistencies and discretionary polish. Name systemic causes when several
screens repeat the same defect. Keep useful existing patterns visible so repairs preserve
them. End with the highest-value next changes and unresolved evidence; do not manufacture
numeric precision or recommend every available command.

A later repair uses the exact target and revision reviewed. If content or code changed,
recheck affected findings. Do not close a newer review's backlog using stale evidence or
create hidden critique storage as a side effect of an inline report.
