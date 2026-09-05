# PKStack identity validation

Recorded September 4, 2026 (America/New_York; the CLI evidence timestamps are
September 5 UTC). Candidate implementation: `aaee6848472c7d584845fce4e8f847c8b854059d`,
based on `aed6c5a441ad359ed8fbdd8596551f3763b6bf55`.
[PR #18](https://github.com/njs14/pkstack/pull/18) carries the change.

## Scope and review

PKStack is the display name; `pkstack` is the handle. The six first-party routes
are `/pkstack`, `/pkstack-setup`, `/pkstack-maintain`,
`/pkstack-verified-goal`, `/pkstack-model-council`, and `/pkstack-principles`.
Imported routes, native Kiro commands, and upstream methods remain unchanged.

An independent Codex review found two issues: 22 local consolidation targets
still used moved paths, and four historical transition rationales had been
rewritten. Both were corrected and rechecked. The final review reported no
material findings within the naming scope. Independent comparisons checked
179 active Markdown files for broken local targets, preserved executable modes,
178 frozen upstream/history files, and 959 source-identity fields. All seven
historical transition arrays match the base. The existing parity test now
checks that consolidation targets resolve.

## Deterministic checks

From `powers/pkstack`:

```sh
uv lock --check
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen ty check
uv run --frozen pytest -q -p no:cacheprovider -o addopts=''
```

Result: **827 tests passed in 185.81 seconds**; lint, formatting (37 files),
types, and lockfile checks passed. After review corrections, the targeted
branding and parity tests passed. No executable behavior changed after the
full suite; GitHub CI reruns the suite against the final PR head.

From the repository root:

```sh
actionlint .github/workflows/*.yml
shellcheck .github/scripts/*.sh
python3 -B -m unittest discover -s .github/scripts -p 'test_*.py'
node --test .github/scripts/test_pkstack_pr_policy.js
.pkstack/bin/projectctl version --output json
.pkstack/bin/projectctl feature validate --output json
.pkstack/bin/projectctl knowledge validate --output json
git diff --check
```

Result: **134 Python policy tests and 17 Node tests passed**. Actionlint,
ShellCheck, version, feature validation, knowledge validation, and diff checks
exited zero. Canonical `okn` was available. Its knowledge scan reported three
warnings for intentional links from `Wiki/` to repository documentation outside
the Wiki bundle; no errors. Local Actionlint was 1.7.12 and ShellCheck 0.11.0;
CI independently installs checksum-pinned analyzers.

Canonical setup regenerated the root's managed files from the renamed Power.
The old generated files were retained in an external temporary backup, not
removed from an unrelated checkout. Setup now refuses legacy `.pk-stack` and
`.pstack` entries before locking or writing. Twelve regressions cover files,
directories, dangling symlinks, preview, and apply.

## Real CLI v3 consumer

Disposable workspace: `/private/tmp/pkstack-cli-smoke.OGqYCk`.
Runtime: **Kiro CLI 2.21.1**, generated `pkstack` agent, **GPT-5.6 Luna / Low**.
No ACP host, trust-all flag, new API key, or global permission change was used.

The README fixture was copied into the empty Git workspace, then these commands
were run (the Power source was the reviewed worktree):

```sh
python3 /private/tmp/pkstack-rebrand.N2MfUP/powers/pkstack/skills/pkstack-setup/scripts/setup_pkstack.py \
  --root /private/tmp/pkstack-cli-smoke.OGqYCk --dry-run --output json
python3 /private/tmp/pkstack-rebrand.N2MfUP/powers/pkstack/skills/pkstack-setup/scripts/setup_pkstack.py \
  --root /private/tmp/pkstack-cli-smoke.OGqYCk --output json
.pkstack/bin/projectctl doctor --output json
.pkstack/bin/projectctl goal start 'Repair account ID normalization' \
  --command 'python3 -m unittest discover -s tests -v' --max-attempts 4 --output json
.pkstack/bin/projectctl goal verify --output json
kiro-cli chat --v3 --agent pkstack --model gpt-5.6-luna --effort low
```

Preview and installation succeeded without conflicts. Doctor reported **81
passed, zero warnings, zero failures**. All four generated agent profiles were
accepted. The first goal verification exited 1, failing three of four tests.

In the one interactive session:

1. `/pkstack` loaded through Kiro's native skill disclosure tool. A bounded
   discovery request returned request classification as its first checkpoint
   and native `/spec` planning followed by `/agent swap pkstack` as its handoff.
2. `/pkstack-verified-goal` loaded in the same session. The request named the
   existing goal and permitted repair only in `account.py`, with no test,
   verifier-contract, or managed-file changes.
3. Kiro read the stored contract and failure, read and repaired `account.py`,
   then ran `.pkstack/bin/projectctl goal verify --output json`.
   Skill loads, shell calls, and the file write received separate native
   approvals. The final readback used `goal status --output json`.

Stored goal `21544fe0-c609-4ace-8592-ab7d28a03f9b` reached **passed** on attempt
2 of 4. The history retains exit 1 followed by exit 0; the successful result ran
all four tests. Contract digest before and after:
`76f93d5ac99e3988d1981d5e4be262ed1515941b64663d9212aa6ecd3451cd70`.
The copied test and tracked fixture have the same SHA-256:
`65932341be2d1b133366ec58e583f224751f1f89b9d8d26ebfeb897cab664974`.

Kiro reported 0.01 credits for entry discovery and 0.03 for the repair turn
(0.04 total). The account dashboard baseline was 294.49 of 1,000, with overages
disabled; a refreshed account-wide after-reading is not yet recorded. Per-turn
usage is direct CLI output, not an estimate of unrelated account activity.

## Artwork and README layout

The square mascot is preserved. The new tracked banner adds the background
knowledge tree and the requested short copy, “PKStack — From plan to proof.”
[Asset provenance](../powers/pkstack/assets/README.md) records the generation,
dimensions, and checksum. Both READMEs cap its display width at 600 pixels.

Root and Power READMEs were rendered with Markdown parsing and a local
GitHub-like stylesheet in isolated headless Chrome at 1200- and 375-pixel
viewport widths. All four screenshots were visually inspected. The banner
rendered at 600 × 240 on desktop and 343 × 137 on narrow screens, with no page
horizontal overflow. This is a local layout check, not a claim of pixel-identical
GitHub rendering.

## Repository and remaining gates

The existing GitHub repository was renamed in place to `njs14/pkstack`, retaining
repository ID 1355551292, privacy, main, automatic merged-branch deletion, and
workflow IDs. Working remotes use the new URL. Workflow filenames remain stable;
visible names and dependent policy references changed together. Push and PR
creation through the existing GitHub credentials succeeded. Ruleset inspection
returned the existing plan-related 403; privacy was not changed to bypass it.
App-specific integrations are not claimed verified merely from repository access.

The renamed IDE import is not yet accepted: its native folder chooser currently
leaves Select Folder disabled. Earlier IDE evidence covers the preceding name,
not this renamed build. Kiro Web, Crew, and IDE goal/Spec execution are not newly
tested here. The autonomous updater remains disabled; its proposal-stage defect
is separate work. No tag or release was created. Merge and release readiness
require completed live gates, not this report alone.
