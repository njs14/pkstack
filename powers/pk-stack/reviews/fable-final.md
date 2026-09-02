# Fable final acceptance

- Snapshot: `1a145d488d8c585d9a7bbe257ba6edefc2c44d50`
- Model: `claude-fable-5-1`
- Effort: `max`
- Session: `25cffed9-3de9-4e27-9709-e42811089574`
- Duration: 1,228,643 ms
- Harness: read-only Git archive; Claude Code safe/restricted mode; empty
  strict MCP configuration; only Read, Glob, and Grep; no persistence

The reviewer report below is the verbatim final `result` field extracted from
the JSON event envelope. Reviewer claims remain untrusted analysis; Codex
separately ran the executable release gates and dispositioned the one LOW item.

---

# Fable acceptance review

Verdict: ACCEPT

The snapshot is a coherent Kiro-native port: Kiro executes, the shipped skills are thin instructions over `.pstack/bin/projectctl`, and the Cyclopts controller owns deterministic, lock-protected goal/feature state with a fail-closed verifier policy. The two previously material items (FBL-012 Git allow globs, FBL-013 selected-profile live campaign) are closed in this tree by code (`templates/project/.kiro/agents/pstack.json:27-34`, regression `tests/test_kiro_assets.py:365-393`) and by repository-reported campaign records. No material finding survives attempted disproof; one LOW defect (foreign-project cache accepted as setup authority) and several documented residuals remain. All live-session and test-run results are treated as claims, not verified observations.

## Scope matrix

| # | Area | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Architecture and boundaries | clear | Ownership table `docs/architecture.md:166-174` matches code: skills only invoke `.pstack/bin/projectctl` (`skills/verified-goal/SKILL.md:13-22`; `tests/test_bootstrap.py:200-218`); no agent runtime or orchestration service in `src/pstack_kiro/*`; the only subprocess launches are the stored verifier (`src/pstack_kiro/runner.py:1057-1162`), optional `kiro-cli agent validate` (`src/pstack_kiro/doctor.py:296-312`), and optional `okn` (`src/pstack_kiro/knowledge.py:24-105`). |
| 2 | Kiro CLI v3 / current session | clear | Normal path `kiro-cli chat --v3 --agent pstack` (`README.md:53-112`; `docs/kiro-v3-compatibility.md:8-33`); `/goal` explicitly not claimed (`docs/kiro-v3-compatibility.md:260-277`); ACP boundary disclosed, not used (`:279-292`; `reviews/kiro-selected-profile-campaign.md:204-213`); native subagents via `toolsSettings.subagent` (`templates/project/.kiro/agents/pstack.json:122-135`), no `/spawn`; hooks use `version: "v1"` + `SessionStart`/`Stop` (`templates/project/.kiro/hooks/pstack-session.json:2,7`; `pstack-tripwire.json:2,7`), checked by `doctor.py:176-177`. |
| 3 | `projectctl` / Cyclopts | clear | `App(name="projectctl")` + sub-apps (`src/pstack_kiro/cli.py:43-49`); uniform `_emit`/`_fail` JSON with exit 2 (`:52-75`), exit 1 for failed doctor/verify (`:117-127,323-340`); `fcntl.flock` + atomic 0600 writes (`src/pstack_kiro/goal.py:74-136`); `yaml.safe_load` only (`src/pstack_kiro/features.py:52`); lexical + per-component symlink containment (`src/pstack_kiro/paths.py:13-38`); shell=False argv, denied/non-evidentiary executables, timeout→124, launch failure→127 (`runner.py:30-50,168-195,819-845,852-984`); no `shell=True`/`os.system`/`yaml.load`/`pickle`/`eval` in source. |
| 4 | Optional OKF | clear | `okn` resolved from PATH and reported absent, not fabricated (`knowledge.py:24-42`); `feature-map-only` degradation; `Wiki/` symlink tree rejection before search (`knowledge.py:82-105`; `tests/test_hardening.py:641`); design stated `docs/architecture.md:372-385`. |
| 5 | Feature maps / PROVE | clear | Slug grammar + reserved `readme` (`features.py:24-25`; `tests/test_features.py:369,381`); round-trip equality before write (`features.py:349-364`); `os.link` no-overwrite atomic write (`:371-390`; `tests/test_features.py:117`); `--ready` proof must pass or exit 1 with `created: false` (`cli.py:204-214`); placeholder/non-evidentiary commands rejected (`features.py:258-262`; `tests/test_features.py:175`; `tests/test_hardening.py:483`). |
| 6 | Verified-goal seam | clear | Contract provenance + digest (`goal.py:142-195`); active-goal conflict (`:198-235`); verify increments attempt only after unchanged-state check, `passed`/`exhausted`/`active` (`:246-290`); resume bounded 1–20 and explicit (`:293-323`); active clear needs `--force` (`:326-335`); tripwire read-only advisory (`:338-360`); controller calls are `ask` in Kiro (`pstack.json:35-42`); transitions tested (`tests/test_goal.py:66,130,156,174,217,248`; `tests/test_cli_direct.py:100,143`). |
| 7 | Bootstrap / idempotence | finding | Two-phase preflight/apply with ownership receipt, refusal to overwrite modified managed files, post-apply re-hash (`src/pstack_kiro/bootstrap.py:215-401`; `tests/test_bootstrap.py:42,259,289,337`; `tests/test_hardening.py:41-204`). Cached-authority refusal is target-local only → FBL-025 (LOW). |
| 8 | Permissions / hooks / safety | clear | Custom agent: `includeMcpJson:false`, `includePowers:false` (`pstack.json:12-13`); fs_write deny on `.pstack/**` and `.kiro/{agents,hooks,skills,steering}/**` (`:43-53`), ask elsewhere (`:54-60`), shell deny list (`:61-110`); Stop hook disabled and labelled advisory (`pstack-tripwire.json:6,13`); SessionStart hook executes no repository code (`pstack-session.json:6,10`); trust flags not depended on (`docs/kiro-v3-compatibility.md:189-193`). |
| 9 | Tests / docs / provenance | clear | Thirteen test modules cover failure, adversarial, symlink, concurrency, tamper, and state paths (`tests/test_hardening.py:204,421,473,535`; `tests/test_runner.py:278,374,443,477,645`; `tests/test_doctor.py:189,215`); pins consistent (`templates/projectctl/uv.lock:15-16,69-72,84-85` vs `bootstrap.py:76-79`); Apache-2.0 `LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES.md` with pinned upstream commit; docs separate observed/official/design/unverified (`docs/kiro-v3-compatibility.md:41-77,324-337`; `docs/validation-report.md:692-722`). Reported results remain claims (see evidence section). |
| 10 | Fake-capability audit | clear | `/goal` appears only as a non-claim; `trust-all-tools`, `--classic`, `--v2`, `kiro-cli acp` appear only as disclaimers/tests; Power installation not guaranteed (`docs/kiro-v3-compatibility.md:324-337`); demo fixture labelled as fixture (`examples/verified-goal-demo/README.md:15-17`); campaign archives explicitly outside the repository (`reviews/kiro-selected-profile-campaign.md:176-183`). |

## Material findings

None.

## Low findings and notes

**FBL-025 — LOW — A foreign project's `.pstack/projectctl` cache is accepted as setup authority**
- Citations: `skills/setup-pstack/scripts/setup_pstack.py:12-18`; `src/pstack_kiro/bootstrap.py:222-239` (refusal compares only against the *target's* `.pstack`), `:254-305` (the cache is populated as a complete asset root incl. `templates/project` and `uv.lock`), `:274-275` (stated intent), `:566-569` (refusal message); claims at `bootstrap.py:117-119`, `README.md:100-101`, `docs/architecture.md:82-89`, `docs/usage.md:155-158`.
- Observed: `_same_or_descendant(asset_root, cache_root)` is evaluated only against `<target>/.pstack`. A shim or `--power-root` pointing at `<other-project>/.pstack/projectctl` passes `_validate_power_assets` (`bootstrap.py:510-529`, completeness only) and bootstraps the target from that cache. Tests cover only the target-local case (`tests/test_bootstrap.py:71-137,139-197`; `tests/test_kiro_assets.py:164-172`).
- Scenario: project A was bootstrapped at an older Power version (e.g., pre-FBL-012 Git allow globs). From project B, `python3 <A>/.pstack/projectctl/skills/setup-pstack/scripts/setup_pstack.py --root <B>` (or `projectctl setup --power-root <A>/.pstack/projectctl`) succeeds; B receives A's stale assets, records them as managed, and `doctor` reports clean. This contradicts "the cached controller is not setup authority … fails closed when that source is omitted".
- Why not material: the path is user-directed and explicit; docs already define an external `--power-root` as user-reviewed; no trust widening, workspace escape, or partial-success misreport; receipt remains auditable. Related: if the ancestor walk finds no cache, `setup_pstack.py:20-22` fails with an unstructured `ModuleNotFoundError` rather than the structured JSON error the shim otherwise produces.
- Fix task: reject any asset root that is (or lies within) a bootstrap-generated cache regardless of target (e.g., detect the generated `.pstack/projectctl/README.md` marker or a `.pstack` path component in the resolved asset root), emit a structured error when the shim cannot resolve a Power root, and add a foreign-cache regression test.
- Suggested regression: bootstrap `A` and `B` under `tmp_path`; run `python3 A/.pstack/projectctl/skills/setup-pstack/scripts/setup_pstack.py --root B --dry-run --output json`; expect exit 2, `error_type: "ValueError"`, message containing "cache as setup authority", and `B/.pstack/bootstrap.json` byte-identical before/after.

**FBL-026 — NOTE — Stop hook is disabled and advisory; enabling it runs repository-controlled code without per-call approval**
- `templates/project/.kiro/hooks/pstack-tripwire.json:6,10,13`; `src/pstack_kiro/goal.py:338-360`. Default `enabled: false`; the command only reads goal state. If a user enables it, `.pstack/bin/projectctl` runs on every Stop under hook trust rather than the `ask` rule. Documented as advisory (`docs/kiro-v3-compatibility.md:195-216`). No defect.

**FBL-027 — NOTE — Optional external tools are resolved from the user's PATH**
- `src/pstack_kiro/doctor.py:88,296-312`; `src/pstack_kiro/knowledge.py:25,94`. `kiro-cli` and `okn` are located via PATH and executed with a timeout; neither is repository-controlled, and absence is reported rather than fabricated. Host-environment dependent; documented as optional.

**FBL-028 — NOTE — Host-specific absolute paths remain in historical evidence**
- `docs/validation-report.md:55,76,148`; `docs/kiro-v3-compatibility.md:45`. Labelled historical/observed; no credential class exposure found in the repository-wide scan. Hygiene only.

**FBL-029 — NOTE — Ownership receipt is unsigned**
- `docs/architecture.md:153-156` discloses SHA-256-only integrity. A forged receipt cannot authorize overwriting modified files (`tests/test_hardening.py:204`); `doctor` discloses mismatches (`doctor.py:219-253`). Documented residual.

**FBL-030 — NOTE — Ambient MCP UI noise during the live campaign**
- `reviews/kiro-selected-profile-campaign.md:80-84` reports a GitHub MCP SSE 404 card despite `includeMcpJson: false` (`pstack.json:12`), attributed to host-level startup before the prompt. Cannot be independently established from the repository; not a candidate defect on current evidence.

**FBL-031 — NOTE — Verifier policy is explicitly not a sandbox**
- `src/pstack_kiro/runner.py:853-859`; `docs/architecture.md:266-307`. Stored verifiers run with the user's privileges inside the project; safety rests on reviewed contracts, the policy grammar, and `ask`-gated controller invocation (`pstack.json:35-42`). Documented design choice.

**FBL-032 — NOTE — `feature generate --overwrite --ready` intentionally replaces existing content**
- `docs/usage.md:378-380`; `features.py:349-364,371-390`; `tests/test_features.py:95,257`. Overwrite is opt-in, proof-gated, and semantic-drift-checked; not a preservation defect.

## Acceptance ledger

| ID | Fix task | Acceptance test | Status |
| --- | --- | --- | --- |
| — | No material findings; ledger empty. | — | — |

## Validation evidence assessed

**Static source and test inspection (performed in this review, no execution):**
- `src/pstack_kiro/{cli,goal,runner,bootstrap,features,discovery,models,doctor,knowledge,paths}.py` in full; all six `skills/*/SKILL.md`; four agent templates; both hook templates; both steering files; `templates/projectctl/uv.lock`; `pyproject.toml`; `plugin.json`; `LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES.md`; `.gitignore`; `examples/verified-goal-demo/*`.
- All thirteen `tests/*.py` read for scenario coverage: idempotence and mode normalization (`tests/test_bootstrap.py:42,259`), concurrency (`:289`; `tests/test_features.py:117`), cached-authority refusal (`:71,139`), symlink/escape hardening (`tests/test_hardening.py:41-148`; `tests/test_runner.py:374-520`), tamper/forged state (`tests/test_hardening.py:204,421`), policy rejection before persistence (`:473,535`), state transitions and resume rules (`tests/test_goal.py:66-248`; `tests/test_cli_direct.py:100,143`), asset-format checks (`tests/test_kiro_assets.py:77-172,365-393`).
- Repository-wide searches: no `shell=True`, `os.system`, `yaml.load(`, `pickle`, `eval(`, `exec(` in source; `/goal`, `trust-all-tools`, `--classic`, `--v2`, `kiro-cli acp` only in disclaimers/tests; no credential-class strings found.

**Command and session results reported by the repository (claims, not verified here):**
- `docs/validation-report.md:604-613`: 508 tests passed, 89.22 % coverage, lint/format clean; `:615-638` package audit; `:640-690` campaign summary.
- `reviews/kiro-selected-profile-campaign.md` and `reviews/kiro-selected-profile-evidence.json`: selected-profile live run (denied `.pstack` write, one-time approvals, fail→diagnose→repair→pass in 2 of 4 attempts, receipt audit `managed_files=49 mismatches=0`).
- `reviews/kiro-final-campaign.md` and `reviews/kiro-final-evidence.json`: final campaign records; `kiro-cli agent validate` outcomes.
- `reviews/acceptance-criteria.md:118-206`: disposition ledger closing FBL-012/013 and later items.
- Raw Kiro archives are stated to reside outside the repository (`reviews/kiro-selected-profile-campaign.md:176-183`).

## Residual limitations and unverified claims

- No command, test, hook, or Kiro session was executed for this review; all counts, coverage figures, `agent validate` results, and live-session observations are repository claims.
- Kiro's real permission-matcher semantics (glob precedence for `./**` versus `.pstack/**`, `deny > ask > allow`) cannot be established from repository content; the candidate's behavior claim rests on reported campaign observations (`reviews/kiro-selected-profile-campaign.md:65-78`).
- The reviewed working tree contains no `.git` metadata, so the campaign snapshot identifiers (`reviews/kiro-selected-profile-campaign.md:3` and the final-campaign record) cannot be tied to this exact tree from repository evidence.
- Power installation via Kiro, `/knowledge` availability, and the ACP-terminology plumbing are documented as unverified or host-observed (`docs/kiro-v3-compatibility.md:324-337`; `reviews/kiro-selected-profile-campaign.md:204-213`).
- First-run behavior of the wrapper's `uv sync --locked` (`src/pstack_kiro/bootstrap.py:85-103`) without network or a populated uv cache was not established from repository evidence.
- Behavior of PATH-resolved optional tools (`kiro-cli`, `okn`, `uv`) depends on the host environment and is outside static review.
