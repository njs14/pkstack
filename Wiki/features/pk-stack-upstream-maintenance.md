---
type: feature
schema_version: 2
slug: pk-stack-upstream-maintenance
title: PK-Stack upstream maintenance
draft: false
verification:
  command:
    - .pstack/bin/projectctl
    - upstream
    - check
    - --manifest
    - maintenance/upstreams.json
    - --power-root
    - powers/pk-stack
    - --output
    - json
related:
  - ../architecture/native-kiro-composition.md
  - ../decisions/native-spec-and-okn.md
  - ../operations/context-depth.md
  - ../../maintenance/upstreams.json
  - ../../maintenance/upstream-reviews.json
  - ../../powers/pk-stack/docs/provenance.md
  - ../../powers/pk-stack/docs/okf-skills-provenance.md
  - ../../powers/pk-stack/docs/okf-spec-provenance.md
---

# PK-Stack upstream maintenance

## User behavior

A maintainer can reprove every immutable configured source pin, its one canonical genesis marker,
and every later transition marker; compare each accepted baseline with its current configured ref;
select exactly one drifting source per transaction; inspect its bounded and exhaustive untrusted
path-and-patch inventory; and prove that every accepted pin transition has an exact
content-addressed A/B/C review disposition for every changed path.
Every semantic patch is complete, count-reconciled, and applied from an exact Git-OID-verified old
blob to the exact current blob; old/new regular-blob modes are explicit; every unavailable raster
asset is excluded with disposition B; and the canonical Power still matches every
bootstrap-managed workspace copy. Drift and any network, schema, identity, ledger, pagination,
size, or parity failure return nonzero.

The autonomous acceptance path is limited to the four configured GitHub source repositories. A
separate weekly or manually dispatched Kiro canary observes product/runtime/documentation drift
without editing the repository or promoting a new CLI pin.

## Expected path

Strict local manifest and source-scoped contiguous review ledgers -> exactly one genesis marker per
source -> fixed GitHub API origin -> pinned/current commit and tree reproof -> deterministic
one-source selection -> fast-forward compare plus exact subtree and source inventory -> every
accepted transition digest/path/reviewability reproof -> ownership-aware bootstrap dry-run -> JSON
verdict. Each genesis marker must precede every
transition marker and bind the ledger genesis exactly; transition markers remain ordered and
immutable. Upstream content is data only and is never executed. This flow follows the
[native Kiro composition boundary](../architecture/native-kiro-composition.md), the
[canonical KNOW decision](../decisions/native-spec-and-okn.md), and the
[task-driven context-depth runbook](../operations/context-depth.md).

## Sub-features

### `remote-reproof`

Reprove repository identity, immutable commit and tree identities, fast-forward ancestry, bounded
pagination, and exact changed-path inventory against the configured authoritative origin.

### `skill-package-parity`

Account for every tracked source path. Cursor skill packages retain direct, alias,
native-replacement, or excluded handling; generic OKF sources retain exact A/B/C source-inventory
dispositions. All parity artifacts are deterministic and source-scoped.

### `review-and-provenance`

Bind the ledger genesis and every accepted transition to canonical provenance markers, exhaustive
A/B/C review evidence, semantic patch completeness, and independent Fable 5.1 review.

### `transactional-acceptance`

Freshly revalidate the exact proposal, canonical/generated parity, tests, and ownership before one
atomic ledger append and pin advance; a failed check changes neither baseline.

### `hands-off-cadence`

Run the same fail-closed maintenance contract on schedule and through an authorized manual dispatch
without granting upstream content execution authority.

### `kiro-product-canary`

Resolve the official stable Kiro CLI manifest, select exactly the x86_64 Linux headless archive,
verify and probe the advertised binary, validate and discover the five workspace agents, and query
the live model inventory without sending a model turn. Record bounded, non-gating observations for
IDE metadata, Kiro Crew Nightly feeds, the changelog, `llms.txt`, and already tracked relevant Kiro
documentation hashes.

## How to get to it (user POV)

### `local-check`

From the repository root, request a read-only comparison of the accepted pin and current upstream
state without accepting or modifying either one.

### `current-session-maintenance`

In the current Kiro IDE agent panel or CLI v3 session, invoke the PK-Stack maintenance workflow,
review its bounded proposal, and keep any acceptance decision explicit.

### `scheduled-cadence`

Let the repository's scheduled GitHub workflow discover drift, build a bounded candidate, and run
the same gates using repository-scoped credentials and permissions.

### `manual-dispatch`

An authorized maintainer may dispatch the same hands-off maintenance workflow outside its cadence.
After the repository's one-time permissions and credentials are configured, that run follows the
same bounded proposal, candidate gates, Fable acceptance, exact-SHA merge, and fail-closed policy as
the scheduled run; it does not require a second per-run landing approval.

## Driving it

### `local-check`

#### Recipe

Run `.pstack/bin/projectctl upstream check --manifest maintenance/upstreams.json` with
`--power-root powers/pk-stack --output json`. Pass a GitHub token only through the environment when
the API requires authentication.

#### Observable proof

The bounded JSON reports every exact source identity, source-scoped inventory digest and parity,
bootstrap parity, the deterministic selected source, and a nonzero drift verdict when any accepted
pin is behind.

### `current-session-maintenance`

#### Recipe

Invoke `/maintain-pk-stack` in the selected `pstack` agent, keep one live coordinator, inspect the
generated proposal, and run the documented verification/review sequence.

#### Observable proof

For the selected source, every changed path has one A/B/C disposition, semantic adaptations and
generated assets reconcile, and the verifier is rerun once after any repair. Acceptance remains a
separately authorized, one-source action; other source pins and ledgers remain byte-identical.

### `scheduled-cadence`

#### Recipe

Run the compiled upstream-maintenance GitHub workflow on its configured cadence with least-privilege
repository permissions, environment-only credentials, and the checked-in manifest, ledger, and
review policy. Separately, let `.github/workflows/pk-stack-kiro-runtime-canary.yml` run weekly, or
dispatch that read-only canary manually when Kiro ships a change.

#### Observable proof

One run produces durable run and candidate identities, exact inventory evidence, all required test
results, and a review disposition; missing credentials or incomplete evidence fail closed without
moving the pin. The separate canary fails red on a newer stable CLI or runtime regression but never
edits a pin or candidate branch.

### `manual-dispatch`

#### Recipe

Use the workflow's authorized manual-dispatch entrypoint. The workflow automatically creates only
its own exact-head candidate PR, runs its bound Fable 5.1 `xhigh` review, and squash-merges that
exact SHA only when every policy gate accepts. Inspect the durable evidence afterward or while a
failed run is awaiting remediation; no model output or upstream text receives independent landing
authority.

#### Observable proof

The workflow identifies the triggering run and candidate, preserves every prior marker and ledger
entry byte-for-byte, and changes the accepted pin only after the exact proposal passes fresh gates.
A rejected, stale, foreign, or ambiguous candidate remains unmerged without asking a model to
override policy. A manually dispatched product canary remains read-only: `KIRO_API_KEY` is scoped
only to live `--list-models` inventory after the advertised tuple exactly matches the reviewed
version, SHA-256, derived URL, and size; an unpinned binary never receives it. The canary neither
calls Anthropic nor sends a model turn, uploads an artifact, or mutates the checkout. Its
advertised-binary checksum/version, exact
five-agent validation/discovery, and strict model-inventory checks are gates; IDE metadata, Kiro
Crew Nightly feeds, the changelog, `llms.txt`, and recorded documentation hashes are bounded
observations. A maintainer must separately promote a stable pin because workflow and protected
controller files are trust roots.

## Evidence boundary

Retain source and tree identities, bounded inventories and digests, A/B/C dispositions, bootstrap
and test results, workflow/candidate IDs, prospective Fable 5.1 `xhigh` verdicts, and the canary's
bounded product metadata and content hashes. Do not retain GitHub tokens, Kiro credentials, raw
secret-bearing logs, private reasoning, or unbounded upstream content. Historical review records
preserve the effort actually used, including prior `max` runs.

## Cleanup boundary

A read-only check removes only verifier-owned temporary files. Successful acceptance consumes only
the exact reviewed proposal and preserves the ledger, the singular genesis marker, all transition
markers, and the prior pin in history. Failure or cancellation leaves the accepted baseline intact
and never recursively deletes worktrees, runtime state, or foreign assets. The product canary
always removes only its isolated temporary Kiro runtime and retains no uploaded artifact.

## Gotchas

- Expected upstream drift is a nonzero candidate state until it is reviewed; it is not a passing check.
- Anonymous GitHub API access can return 403; pass the existing token through the environment without logging it.
- Cursor skill parity includes nested playbooks, templates, and helper semantics, not only top-level SKILL.md files.
- OKF source inventories cover every regular blob even when PK-Stack adapts only a narrow semantic subset.
- Multiple drifting sources are serialized; no proposal or acceptance transaction may mix them.
- Each source has exactly one canonical genesis marker before all immutable transition markers.
- Missing credentials, incomplete pagination, or indeterminate identity evidence fail closed without acceptance.
- Prospective Fable 5.1 review uses `xhigh`; historical records keep the actual earlier `max` effort.
- Only the four configured GitHub source repositories advance autonomously; Kiro product facts are observations, not a fifth self-updating source.
- A newer stable Kiro CLI deliberately fails the canary until a human reviews and promotes every trust-root pin copy; the canary itself must not edit workflows or protected controller code.

## Verification

`.pstack/bin/projectctl upstream check --manifest maintenance/upstreams.json --power-root powers/pk-stack --output json`

An expected upstream change keeps this contract failing until the change has been reviewed and
semantically adapted, the canonical Power has been regenerated and tested, provenance is current,
and `upstream accept` has freshly validated the exact proposal before appending the ledger
transition and advancing the pin.
