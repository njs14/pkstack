# PKStack & friends validation

Recorded September 5, 2026. Product changes are committed at
`151b9da6e0dd6fd295e81044c477f0d96ab0c0aa`, based on
`f53f0931ef3a6748242d2dd569fe0cef0ddb2106`.
[PR #31](https://github.com/njs14/pkstack/pull/31) also contains the later static
diagram exports and campaign reports. It is not a release publication.

## What changed

- The root README is 258 rendered words and the Power README is 166, excluding
  code. Installation stays up front; the executable example moved to
  [First task](../powers/pkstack/docs/first-task.md).
- [Sources and friends](../powers/pkstack/docs/curated-skills.md) identifies each
  source, purpose, adaptation, and exclusion. Product identity remains PKStack;
  imported skill names and upstream methods remain intact.
- Skill descriptions and handoffs distinguish visual explanation from evidence
  logging, human writing from agent instructions, task repair from reusable
  automation, and other neighboring jobs. Setup remains bounded installation,
  not an unsolicited tour through every skill.
- Thirty routing cases extend the existing test suite. They check the declared
  boundaries and supported composition; they are not a runtime router or a
  measured model-success rate.
- The existing no-tool Opus review receives a versioned, digest-bound skill
  context: candidate catalog, relevant neighboring instructions, shared
  steering, and cases read from the immutable base. Its whole context is capped
  at 64 KiB. Missing coverage or oversized context stops for manual review;
  nothing is silently dropped to manufacture approval.
- Poteto's bundled `unslop` supplied the prose-editing method. The separate
  No AI Slop plugin was not used for this revision or uninstalled from the Mac.

No Python controller behavior, model pipeline, credentials, workflow permissions,
or bundled upstream executable runtime changed. The updater stays enabled;
the Floci lab stays separate.

## Deterministic checks

Commands below ran from the repository root unless a directory is shown:

```sh
python3 -B -m unittest discover -s .github/scripts -p 'test_*.py' -q
node --test .github/scripts/test_pkstack_pr_policy.js
actionlint .github/workflows/*.yml
shellcheck .github/scripts/*.sh
cd powers/pkstack
uv sync --quiet --locked --all-groups
uv lock --check
uv run --frozen ruff check src tests skills/pkstack-setup/scripts/setup_pkstack.py
uv run --frozen ruff format --check src tests skills/pkstack-setup/scripts/setup_pkstack.py
uv run --frozen ty check
uv run --frozen pytest -q
```

The first local full Power run returned 854 passes and one failure: the existing
walkthrough test still looked for the example in the README. The test now follows
the README's link and executes the same setup/failure/repair example from
`docs/first-task.md`. Its focused rerun with `test_kiro_assets.py` passed all 116
tests. It was not replaced with a weaker text-only check.

The corrected exact product head passed
[CI run 33966764291](https://github.com/njs14/pkstack/actions/runs/33966764291):
177 repository Python tests, 17 JavaScript tests, and 854 Power tests, with one
installed-Kiro check skipped on Linux. Lint, formatting, types, lockfile,
Actionlint, and ShellCheck passed. The documentation/export head
`f84585ae8f7e4c47006d972dbc6c780eabb80766` then passed the same full gate in
[CI run 33967873493](https://github.com/njs14/pkstack/actions/runs/33967873493).
The final IDE-evidence commit requires its own green PR check before merge.

The following documentation CI run caught one exact support-wording assertion:
the report had changed `Kiro Web is untested` to a combined Web/Crew sentence.
The explicit Web sentence was restored without changing the test or support
claim. That run's 853 passes, one failure, and one skip are not reported as green.
The subsequent focused run of `test_kiro_assets.py`, `test_branding.py`, and
`test_readme_walkthrough.py` passed all 128 tests; `git diff --check` also passed.

Reviewed setup regenerated managed files without conflicts or stale files.
The generated controller returned **81 doctor passes, zero failures or warnings**,
and passed `feature validate` and `knowledge validate --require-okn` on the Mac.
This is separate from host-package tests. The diagram-export follow-up passed
all 12 branding tests and `git diff --check`.

```sh
.pkstack/bin/projectctl doctor --output json
.pkstack/bin/projectctl feature validate --output json
.pkstack/bin/projectctl knowledge validate --require-okn --output json
```

Knowledge validation reported `mode: canonical-okn`; it was not the narrow
feature-only fallback.

## Live Kiro evidence

| Campaign | Result and boundary |
| --- | --- |
| [CLI Standard and Quick Spec](friends-cli-validation.md) | Both native planning paths handed off to `pkstack` in the same conversation, bound the Spec, recorded a failing stored verifier, repaired only `account.py`, then passed all four unchanged tests. |
| [IDE Standard and Quick Spec](friends-ide-validation.md) | Both native planning paths completed same-tab handoff, recorded failure, implementation-only repair, and pass at attempt 2/4 with unchanged tests and planning documents. |
| [Six curated skills](friends-curated-validation.md) | Functional observations, including failures, are recorded separately. Do not treat successful skill discovery as a passing workflow. |

All model campaigns used interactive Kiro, Luna / Low, and existing Kiro
authentication. No ACP, trust-all mode, external provider key, schedule, or
publication was added. The CLI report records an account-wide usage change from
340.44 to 343.46 of 1,000 credits; concurrent runs prevent attributing that delta
to one lane. Rounded per-turn costs appear in the individual reports.

The later curated-campaign `/usage` reading was **343.88 of 1,000** at
12:56:52 UTC: **3.44 covered credits** above the shared baseline. That remains
an account-wide estimate, not an exclusive task charge. Curated turn displays
sum to 0.28 credits.

After both IDE campaigns, the refreshed native account meter read **348.68 of
1,000**, with overages disabled. That is **8.24 credits** above the shared
340.44 baseline, including any concurrent account use. The four displayed IDE
turns sum to **0.90 credits**; these measurements are not interchangeable.

These small fixtures do not prove production applications, every model, all
native Spec modes, or universal skill obedience. Crew and Web remain untested.
The IDE Standard fixture's four tests do not cover its prose Spec's ASCII
edge case; the recorded passing predicate is not proof of every prose property.
The CLI report also records a quoted/unquoted controller-command approval
difference without claiming its cause or a new permission-boundary proof.

## Independent review

A separate agent reviewed the product/docs/routing changes it had not authored
and reran 27 focused tests: no material findings. A fresh read-only reviewer
inspected the review-context producer and consumer, exact-base/head binding,
trusted workflow wiring, path/mode constraints, and fail-closed limits. It
independently ran 100 guard and 14 stream tests: no material findings.

The final IDE evidence review independently matched both goal histories,
contract digests, timestamps, original read-only tests, native artifacts, and
seven core installed files against the candidate. It found no material issue
in the five-file evidence/support update. All 19 local links resolved; the
128 focused asset, branding, and walkthrough checks passed after the support
assertion update, followed by clean Ruff and formatting checks.

These are scoped Codex reviews, not a new live Opus pipeline verdict. The existing
Opus pipeline was extended in place; its schema and validation tests passed, but
this change did not trigger a paid autonomous upstream-update campaign. The new
trusted-base fixture becomes available to subsequent candidate reviews only
after this owner-reviewed PR reaches main.

## Diagrams and reading checks

The three tracked JSON/HTML pairs passed Archify's nine structural checks and
automated visual checks at four desktop sizes. Light and dark endpoint captures
were inspected. The 1600-pixel-wide PNGs were then exported statically from each
compiled SVG with librsvg 2.62.3 and inspected separately. Their source, tool
version, and regeneration commands are in the
[artifact guide](../powers/pkstack/docs/artifacts/README.md).

The temporary export helper's SHA-256 is
`28dc6b542d917f0e92ad46527cdd2a95790c1dd424c17d23ed867ed22c931358`.
It did not execute the artifact HTML or alter diagram geometry and is not a new
product dependency. This authoring run used local Archify 2.17; the Power's
vendored version was deliberately not upgraded. Its separate live smoke's
clipping failure therefore remains a limitation, not a contradiction of the
three inspected documentation diagrams.

Both READMEs were inspected in GitHub on the diagram-only export commit
`1df518be8daf4e932d604a52b90e3aba6304d7e3`, at 1440×1000 and
390×844. The banner resolves from both paths; headings, prose, and installation
steps fit the narrow layout. GitHub keeps the long clone command in a horizontally
scrollable code block. The overview scales to fit; phone readers need to open
the image for its small detail labels. The browser viewport was restored afterward.

The final independent evidence audit found no material findings: 34 local links
resolved, retained CLI goal/test hashes agreed with the reports, and the failed
or pending smokes remained explicitly qualified. No 0.3.0 tag or release has
been created. All four CLI/IDE Spec campaigns are complete; the final evidence
commit still requires green exact-head CI and review before merge.
