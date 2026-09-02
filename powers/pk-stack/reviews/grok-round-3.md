# Grok advisory council, round 3

- Snapshot: `61c6e0c`
- CLI: official Grok Build `1.0.13`
- Model: `grok-4.6`
- Reasoning effort: `xhigh`
- Harness: read-only Git archive; strict sandbox; plan permissions; only
  read_file, grep, and list_dir; web and subagents disabled

The content below is the verbatim plain output from the bounded sweep. It is
untrusted advisory analysis until Codex independently reproduces and
dispositions each finding.

---

I'll start by locating the caller-authorized review contract and mapping the repository so the council review is grounded in first-party evidence only.I'll read the review contract and core architecture docs first, then inspect implementation files independently of prior review notes.Next I’ll inspect the Python control plane, Kiro assets, and tests against the public claims.I’ll now inspect the Kiro assets, skills, and tests that implement the claimed current-session workflow.# Grok advisory council review

Conclusion: ADVISORY_CONCERNS

The ownership split is implemented in source: Kiro assets are instructions and permission profiles, `projectctl` owns state and proof, and OKF is an optional `okn` subprocess. Native `/goal`, ACP, classic/V2, and `/spawn` are not hidden defaults. One material defect remains in the PROVE path: `feature generate` emits YAML 1.1 frontmatter that the same loader rejects for otherwise-legal slugs, titles, and argv tokens, so a successful generate can produce a contract that cannot be shown, validated, or used as a goal source.

## Scope matrix

| Area | Status |
| --- | --- |
| 1. Architecture | clear |
| 2. Kiro CLI v3 / current session | clear |
| 3. `projectctl` / Cyclopts | finding |
| 4. Optional OKF | clear |
| 5. Feature maps | finding |
| 6. Verified-goal loop | clear |
| 7. Bootstrap / idempotence | clear |
| 8. Permissions / hooks / safety | clear |
| 9. Tests / docs / provenance | clear |
| 10. Fake capabilities | clear |

## Material findings

### GRK-021 — MEDIUM — `feature generate` can write contracts that the loader cannot parse

**Citations:** `src/pstack_kiro/features.py:24`, `src/pstack_kiro/features.py:52`, `src/pstack_kiro/features.py:92-96`, `src/pstack_kiro/features.py:100-102`, `src/pstack_kiro/features.py:107-118`, `src/pstack_kiro/features.py:264-288`, `src/pstack_kiro/cli.py:187-218`

**Observed:** Generation dumps frontmatter with `yaml.safe_dump(..., allow_unicode=True)` and no quoting representer. Loading uses `yaml.safe_load` and then requires `type(slug) is str`, `isinstance(title, str)`, and `type(item) is str` for every command argv element. The locked runtime is PyYAML 6.x (`pyproject.toml:16`, `templates/projectctl/uv.lock` package `pyyaml`). PyYAML’s default SafeDumper/SafeLoader pair still applies YAML 1.1 implicit typing to unquoted scalars. The slug grammar `_SLUG = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"` accepts tokens that YAML 1.1 treats as booleans, null, or integers (`on`, `off`, `yes`, `no`, `true`, `false`, `y`, `n`, `null`, `none`, `2`). Tests load planted documents with coerced types (`tests/test_hardening.py:320-344`) but never generate those values and reload them.

**Violated contract:** Feature generate is the public authoring path for the PROVE interface (`README.md:84-91`, `docs/usage.md:311-357`). A generated file must be loadable by `feature show` / `feature validate` / `goal start --feature`. Ready generation may run a passing proof and then persist `draft: false` (`cli.py:187-218`) even when the written document is unloadable.

**Failure scenario:** In a bootstrapped project:

```bash
.pstack/bin/projectctl feature generate on \
  --title Yes \
  --behavior "A caller enables the feature." \
  --expected-path "UI -> flag -> stored state" \
  --output json
.pstack/bin/projectctl feature show on --output json
```

Generate returns `ok: true` and writes `Wiki/features/on.md`. Show exits 2 with `FeatureMapError` (`slug must be a string` and/or `title must be a non-empty string`). The same break happens for a normal slug whose stored command list contains an unquoted YAML 1.1 token (`python3 verify.py on`). `/verified-goal` cannot bind `--feature on`. `feature validate` and `doctor` fail closed on a file this CLI just created.

**Fix task:** Make `generate_feature` emit frontmatter that roundtrips through the same loader (quote every string scalar, or dump-load-compare before `os.replace`/`os.link`). Refuse to write if the reloaded `FeatureSpec` does not equal the in-memory spec. Add generate/show/validate regressions for slug/title/argv tokens in the YAML 1.1 bool/null/int set.

**Acceptance test:** Isolated project with `Wiki/features` writable. Run the generate/show pair above, then:

```bash
.pstack/bin/projectctl feature generate sample \
  --title Sample \
  --behavior "A caller runs a tagged check." \
  --expected-path "CLI -> verifier -> result" \
  --command "python3 verify.py on" \
  --output json
.pstack/bin/projectctl feature show sample --output json
.pstack/bin/projectctl feature validate --output json
```

Expected after fix: all three commands exit 0; `show` JSON has `feature.slug == "on"` and `feature.title == "Yes"` for the first contract, and `feature.command` contains the string `"on"` for the second; validate `ok: true` (warnings only for draft). Current expected failure: generate `ok: true`; show/validate nonzero with `FeatureMapError` / `ok: false` on coerced non-strings.

## Low findings and notes

### GRK-022 — LOW — Setup shim fallback points at the target cache with the wrong parent depth

`skills/setup-pstack/scripts/setup_pstack.py:11-15` sets `POWER_ROOT = SCRIPT_PATH.parents[3]`, then if `src/pstack_kiro` is missing sets `PROJECT_ROOT = SCRIPT_PATH.parents[4]` and `POWER_ROOT = PROJECT_ROOT / ".pstack" / "projectctl"`. For the cached copy at `.pstack/projectctl/skills/setup-pstack/scripts/setup_pstack.py`, `parents[4]` is `.pstack`, so the fallback becomes `.pstack/.pstack/projectctl`. The normal cached path never takes this branch because cache `src/` exists, and `bootstrap.py:204-220` still refuses a cache asset root. An incomplete Power therefore fails as `ModuleNotFoundError` or as cached-authority `ValueError`, not as a structured “Power is missing src/templates” error. Fail-closed, but the fallback cannot succeed and misreports the authority path.

### GRK-023 — LOW — Spec-bridge argv is stringified rather than type-checked

`src/pstack_kiro/goal.py:185-186` passes `payload["command"]` to `parse_command`. The non-string branch (`src/pstack_kiro/runner.py:834-836`) does `tuple(str(item) for item in value)` with no `type is str` check, unlike feature loading (`features.py:107-118`). A bridge `{"command": ["pytest", true]}` becomes `("pytest", "True")` and can be stored as the immutable goal contract. Malformed spec JSON should fail like a non-string feature command list.

### GRK-024 — LOW — `git checkout *` deny also blocks branch creation

`templates/project/.kiro/agents/pstack.json:72-73` denies `git checkout *` and `git checkout -- *` to prevent worktree clobber (`tests/test_kiro_assets.py:320-332`). That also matches `git checkout -b topic`. The verified-goal loop does not need branch creation, so this is over-broad least privilege rather than a completion-gate failure.

### GRK-025 — NOTE — Current-session and permission attachment are instructional, not mechanically enforced

`/verified-goal` and setup skills tell the model to stay in the current `kiro-cli --v3` session and to `/agent swap pstack` (`skills/verified-goal/SKILL.md:9-18`, `skills/setup-pstack/SKILL.md:55-77`). Nothing in `src/pstack_kiro` can prevent ACP, `/spawn`, or remaining on `kiro_default`. The Stop hook is disabled (`templates/project/.kiro/hooks/pstack-tripwire.json:13`). That matches the docs; it is not a fake `/goal` or hidden scheduler.

### GRK-026 — NOTE — Selected-profile Kiro campaign is not in this snapshot’s validation evidence

`docs/validation-report.md:214-218` states the recorded repair loop did not use `--agent pstack` and does not prove the generated ask/deny profile was active. Later text still treats a selected-profile campaign as pending (`docs/validation-report.md:344-348`). This review did not execute Kiro. Least-privilege claims for live matching remain a residual limitation, not a source-level fake capability.

### GRK-027 — NOTE — Parent-exit-0 plus killed descendants is still a pass

`src/pstack_kiro/runner.py:1131-1158` records `passed=(returncode == 0)` after killing the process group. `tests/test_hardening.py:508-526` asserts that a parent which spawns a 60s child and exits 0 is `passed is True` while the child is dead. That matches the documented non-sandbox process boundary; a fork-and-exit script can still complete a goal.

## Advisory remediation ledger

| ID | Fix task | Acceptance test | Status |
| --- | --- | --- | --- |
| GRK-021 | Emit feature frontmatter that roundtrips through `yaml.safe_load` and the strict string/bool schema; refuse to write on mismatch; add generate/show/validate regressions for YAML 1.1 bool/null/int tokens in slug, title, and argv. | Isolated `feature generate on --title Yes ... --output json` then `feature show on --output json` and `feature generate sample ... --command "python3 verify.py on"` then `feature show sample` / `feature validate --output json`. Expected: exit 0; slug/title/command tokens remain strings `"on"` / `"Yes"`; validate `ok: true`. | open |

## Design dissent and attack scenarios

1. **Unmatched shell default on `pstack`.** The primary profile asks for `git` / `git *` and `.pstack/bin/projectctl *`, and denies a destructive subset (`templates/project/.kiro/agents/pstack.json:27-108`). There is no catch-all `shell` `*` `ask` or deny-by-default rule. Tests only prove hostile git forms are not `allow` (`tests/test_kiro_assets.py:350-378`). If this Kiro build default-allows unmatched shell, `python3 -c ...`, `curl | sh`, or `cp` onto `.pstack/bin/projectctl` never hits an ask/deny rule. That would change acceptance of the least-privilege story. A catch-all `shell` `*` `ask` (or deny-default plus enumerated allows) is the smallest way to make the profile independent of an undocumented default.

2. **Git write-through after one `ask`.** `git diff --output=.kiro/hooks/evil.json` and `git log --output=.pstack/state/goal.json` match `git *` `ask`, not the `fs_write` deny on `.pstack/**` and `.kiro/hooks/**`. The verifier policy rejects git `--output` (`src/pstack_kiro/runner.py:239-246`, `636-637`), but the agent shell path does not. A rubber-stamped git command can rewrite hooks, the controller wrapper, or goal evidence without using the write tool. Acceptance should treat “deny control-plane writes” as either covering this git form or as explicitly out of scope for shell.

3. **YAML 1.1 frontmatter as the PROVE schema.** GRK-021 is the concrete break. Replacing feature metadata with JSON (or a quoted-scalar-only dump plus mandatory reload) would remove a class of generate/load splits that strict `type is str` checks cannot fix on the write path. Leaving YAML 1.1 in place requires the roundtrip gate above; tests that only plant already-coerced documents will not catch the producer.

## Evidence assessed and residual limitations

**Inspected in this snapshot:** `src/pstack_kiro/*.py`; `skills/*/SKILL.md` and `skills/setup-pstack/scripts/setup_pstack.py`; `dev.kiro/steering/*.md`; `templates/project/.kiro/agents/*.json` and `hooks/*.json`; `plugin.json`; `pyproject.toml`; `docs/{architecture,usage,kiro-v3-compatibility,provenance,validation-report}.md`; `README.md`; `NOTICE`; `THIRD_PARTY_NOTICES.md`; `examples/verified-goal-demo/**`; `tests/*.py` (139 `def test_` functions, many parametrized). Prior review files were not used as authority.

**Repository-reported, not re-executed here:** `docs/validation-report.md` command tables (ruff/ty/pytest/coverage, `kiro-cli agent validate`, isolated Kiro V3 repair). This review did not run tests, generate features, invoke `projectctl`, or talk to Kiro. GRK-021’s YAML 1.1 roundtrip is inferred from the dump/load APIs, PyYAML 6.x lock, and strict `type is str` checks; it was not executed. Live deny/ask matching, unmatched-shell default, Power-import file set, and selected-profile `/verified-goal` behavior are therefore not established beyond static source.
