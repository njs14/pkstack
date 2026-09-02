# Fable peer review, round 2

- Snapshot: `f96df36`
- Model: `claude-fable-5-1`
- Effort: `max`
- Session: `d06c98ac-57c4-4993-872d-e34b913b0da3`
- Duration: 1,331,169 ms
- Harness: read-only Git archive; Claude Code safe/restricted mode; empty
  strict MCP configuration; only Read, Glob, and Grep; no persistence

The reviewer report below is the verbatim final `result` field extracted from
the JSON event envelope. It is untrusted advisory analysis until Codex
independently reproduces and dispositions each finding.

---

# Fable acceptance review

Verdict: REJECT

The candidate is a genuine Kiro-native semantic port: workflow semantics live in skills and steering, executable evidence lives in a Cyclopts `projectctl` with a shell-free, policy-screened verifier runner, and the goal seam is deterministic, fail-closed state with explicit resume/clear. Two material issues remain: the installed primary agent profile unconditionally `allow`s open-ended `git diff*`/`git log*`/`git show*` shell globs, which under the candidate's own matcher assumptions admit unapproved arbitrary execution (`git difftool --extcmd`) and unapproved writes into the very control-plane paths the profile claims to deny (`--output=`); and the repository itself records that no Kiro campaign has ever run with the `pstack` profile selected, so the permission profile's live behavior is unobserved by the candidate's own acceptance order. Everything else reviewed is either clear or a bounded low-severity item.

## Scope matrix

| # | Area | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Architecture and boundaries | clear | Skills are instructions only (`skills/verified-goal/SKILL.md:9,15-18,55`); state/transitions owned by `projectctl` (`src/pstack_kiro/goal.py:241-290`); hooks are static printf / disabled advisory (`templates/project/.kiro/hooks/pstack-session.json:10,13`, `pstack-tripwire.json:6,13`); no runtime service, no Cursor artifacts (`tests/test_kiro_assets.py:426-436`). |
| 2 | Kiro CLI v3 / current session | clear | Current session is the normal path (`SKILL.md:9`); no native `/goal` claim (`docs/kiro-v3-compatibility.md:247-264`); ACP/`--v2`/`--classic`/`/spawn` only as disclaimers (`docs/usage.md:280-281`); hooks use `version: "v1"` + PascalCase triggers. Live proof of the selected profile is pending — see FBL-013 (area 9). |
| 3 | `projectctl` / Cyclopts | clear | `cyclopts==4.23.2` pinned (`pyproject.toml:15`, `templates/projectctl/uv.lock:15-16`); consistent `_emit`/`_fail`, exit 2 structured error, 1 failed proof (`src/pstack_kiro/cli.py:108-112,119-125,198-207`); strict schemas (`features.py:69-153`); flock + atomic replace (`goal.py:75-86,103-130`). Low items FBL-014/015/017. |
| 4 | Optional OKF | clear | `okn` resolved via PATH and reported honestly as `feature-map-only` when absent (`src/pstack_kiro/knowledge.py:25-41,54-63`); `--require-okn` opt-in (`:48-57`); leading-hyphen query rejected (`:88`); hostile `Wiki/` symlink handled (`tests/test_hardening.py:641-667`). |
| 5 | Feature maps / PROVE | clear | Proof-before-write for `--ready` (`cli.py:187-207`); overwrite only with explicit flag (`cli.py:173,181,217`); reserved `readme`, slug regex, boolean `draft` (`features.py:138-142,156-164`); placeholder/self-reference/hazard screen in runner (`runner.py:168-195,239-246,636-637`); concurrent generate one winner (`tests/test_features.py:71-112`). |
| 6 | Verified-goal seam | clear | Transitions only in `verify_goal` (`goal.py:279-289`); completion requires `passed` (`SKILL.md:66`); nonzero verifier exit expected (`SKILL.md:60`); resume/clear explicit and guarded (`goal.py:299-323,326-335`; `SKILL.md:62`); state invariants incl. digest and evidence consistency (`goal.py:375-428`); race discard (`goal.py:275-278`). |
| 7 | Bootstrap / idempotence | clear | Receipt with per-file sha256, conflicts vs pending_updates, `--update-managed` opt-in, cached-authority refusal (`cli.py:96-101`; `tests/test_bootstrap.py:42-64,67-133,333-344`); concurrent bootstrap one winner (`:285-330`); dry-run no artifacts (`:278-282`); no source-checkout dependency after install (`bootstrap.py:81-98`). |
| 8 | Permissions, hooks, safety | finding | FBL-012: `templates/project/.kiro/agents/pstack.json:30-34` open-ended git `allow` globs defeat `fs_write` deny at `:46-56`. Hooks schema/trigger names correct; Stop hook disabled and described as advisory. |
| 9 | Tests, docs, provenance | finding | FBL-013: selected-profile campaign evidence absent by the repository's own statement (`docs/validation-report.md:214-218,274,295-297`; `reviews/README.md:54-55`). Tests otherwise cover failure/adversarial/idempotence/transitions. Provenance coherent (`THIRD_PARTY_NOTICES.md`, `NOTICE`, `pyproject.toml:11-12`). FBL-016 low. |
| 10 | Fake-capability audit | clear | No `/goal`, no guaranteed Power install, Stop hook not sold as enforcement (`docs/validation-report.md:315-318`), campaign limitations disclosed (`:214-218,319-322`), fixture labelled intentionally red (`examples/verified-goal-demo/README.md:3,15-17`), round-1 Fable transcript labelled as extraction (`:305-308`). |

## Material findings

### FBL-012 — HIGH — Primary profile `allow`s open-ended `git diff*`/`git log*`/`git show*`, admitting unapproved execution and control-plane writes

- Citations: `templates/project/.kiro/agents/pstack.json:27-37` (allow), `:46-56` (fs_write deny), `:64-113` (shell deny contains no `difftool`/`--output`/`--ext-diff` form); matcher assumption used by the candidate's own tests `tests/test_kiro_assets.py:291,347`; the candidate's runner classifies exactly these forms as hazards `src/pstack_kiro/runner.py:239-246,622-623,636-637` and tests them `tests/test_runner.py:225,228-229`; contradicted claims `docs/kiro-v3-compatibility.md:86,165` ("read-only Git"), `docs/usage.md:289` ("control-plane paths are `deny`").
- Observed: the installed primary agent (`bootstrap.py:43-60` copies this template into the project) grants unconditional shell `allow` to any command string beginning `git diff`, `git log`, or `git show`. Under whole-string glob matching (the semantics the candidate's tests assert), `git difftool -y --extcmd=<cmd> HEAD~1 HEAD` and `git difftool -y -x <cmd>` match `git diff*` and run `<cmd>` with no prompt; `git diff --output=<path>`, `git log ... --output=<path>`, `git show --output=<path> <rev>` write/truncate an arbitrary path (relative, absolute, or `../`) with no prompt; `git diff --no-index <outside-file> /dev/null` reads outside the `./**` fs_read scope. No `ask`/`deny` rule matches these single (non-compound) git invocations, so the compound-command rationale at `reviews/acceptance-criteria.md:29-33` does not apply.
- Violated contract: least-privilege permissions; fs_write deny for `.pstack/**` and `.kiro/{agents,hooks,skills,steering}/**`; documented "read-only Git" allow; "no broad trust".
- Failure scenario: repository content (README, feature file, commit message) instructs the agent to run `git difftool -y --extcmd=sh HEAD~1 HEAD` → arbitrary execution without approval; or `git diff --output=.kiro/agents/pstack.json` → profile truncated/corrupted so the session falls back to `kiro_default`; or `git log -1 --format=%B --output=.kiro/hooks/inject.json` with a crafted commit body → hook file created that Kiro executes on the next `SessionStart`; or `--output=.pstack/state/goal.json` / `--output=.pstack/bin/projectctl` → goal evidence or controller destroyed. Each bypasses the deny rules the docs present as the safety boundary.
- Smallest fix: in `templates/project/.kiro/agents/pstack.json:27-37` remove the trailing-wildcard git patterns and either move git to `ask` or enumerate a closed set of exact argument forms (no `*` after an option-capable position); update `docs/kiro-v3-compatibility.md:86,165` accordingly; add a regression test asserting no shell `allow` pattern fnmatches the hostile forms; existing installs pick it up via `projectctl setup --update-managed` (`pending_updates`).
- Acceptance test: new `tests/test_kiro_assets.py::test_primary_profile_never_allows_git_forms_that_execute_or_write` — for each of `git difftool -y --extcmd=sh HEAD~1 HEAD`, `git difftool -y -x sh`, `git diff --ext-diff`, `git diff --output=.kiro/hooks/evil.json`, `git log -1 --format=%B --output=.pstack/state/goal.json`, `git show --output=/tmp/escape HEAD`, `git log --output=../outside.txt`, `git diff --no-index /etc/hosts /dev/null`, assert `not any(fnmatchcase(cmd, p) for p in shell_allow_patterns)`. Expected: fails on the current snapshot (all match), passes after the fix; `test_agent_templates_are_json_least_privilege_profiles` still passes; `kiro-cli agent validate --path templates/project/.kiro/agents/pstack.json` exits 0.

### FBL-013 — MEDIUM — No Kiro campaign has run with the `pstack` profile selected; the candidate's own acceptance order requires it before final acceptance

- Citations: `docs/validation-report.md:214-218` ("did not select `--agent pstack` … does not prove that the generated pstack permission profile was active … its evidence is not claimed"), `:274` ("plain V3 kept `kiro_default`, so generated permission rules were inactive"), `:295-297` (remaining order includes the selected-profile campaign), `:319-322`; `reviews/README.md:54-55`; `reviews/acceptance-criteria.md:32-33` ("The final live campaign still exercises the selected profile rather than relying on this static conclusion alone").
- Observed: the only recorded live campaign ran under `kiro_default`. No repository artifact shows the `pstack` profile active during `/verified-goal`: no observed `ask` for `.pstack/bin/projectctl goal verify`, no observed `deny` on a control-plane write, no observed skill/agent discovery after `/agent swap pstack`, and no final `goal status --output json` under that profile.
- Violated contract: the final gate reviews "completed validation evidence"; the permission profile (the sole runtime safety boundary, and the subject of FBL-012) has never been exercised, and the repository's own plan defers the compound-command conclusion to this campaign.
- Failure scenario: if Kiro's pattern normalization differs from the candidate's assumptions (e.g. `./**` vs `.pstack/**`, or absolute paths), the deny rules never fire in practice and every documented safety statement about the profile is untested prose.
- Smallest fix: run the fixture campaign (`examples/verified-goal-demo/README.md:7-12`) with `kiro-cli chat --v3 --agent pstack` (or `/agent swap pstack` in-session), and add a post-remediation section to `docs/validation-report.md` containing: the launch/swap command, the observed skill-load approval, the observed `ask` prompt text for `.pstack/bin/projectctl goal verify --output json`, one observed `deny` for an attempted write under `.kiro/` or `.pstack/`, the observed `git` allow/ask behavior for one FBL-012 form, and the final `goal status --output json` payload.
- Acceptance test: `grep -n -- "--agent pstack\|/agent swap pstack" docs/validation-report.md` returns a line inside a "post-remediation campaign" section (currently only lines 215, 274, 319-321, all negations/limitations); that section contains a `goal status --output json` payload with `"status": "passed"` and a `contract.display` equal to the `account-lookup` feature command, plus the observed ask and deny prompts. Expected: absent on the current snapshot; present after the campaign (still a claim, but the self-declared gap closes).

## Low findings and notes

- **FBL-014 — LOW — Unreachable exhaustion branch.** `src/pstack_kiro/goal.py:257-261` cannot execute: status is `active` there and `_validate_state` (`goal.py:416-420`) already rejects active state with `attempt_count >= max_attempts`. Dead code obscures the intended transition. Fix: delete or convert to an invariant assertion.
- **FBL-015 — LOW — Policy drift makes stored state unclearable through the CLI.** `goal.py:399-402` re-runs `enforce_verification_policy` on every load; `clear_goal` loads first (`goal.py:328-333`), so if PATH/executable drift makes an accepted verifier policy-invalid, `goal status` and `goal clear --force` both error and only the manual runbook remains (`docs/usage.md:644-663`). Fail-closed is intentional; the unusable explicit clear is the defect. Fix: let `clear --force` surface a policy-rejected state as `invalid` and clear it after preserving evidence, or document as a design choice.
- **FBL-016 — LOW — Coverage gate not reproducible from the snapshot as recorded.** `docs/validation-report.md:54,75,147` pass `--cov-config=/Users/…/pyproject.toml`, an absolute path outside this snapshot; whether it equals `pyproject.toml:44-51` cannot be established. Fix: record the snapshot-relative command (`uv run pytest --cov=pstack_kiro`).
- **FBL-017 — LOW — Read routes create state artifacts.** `goal.py:78-81` creates `.pstack/state/` (0700) and the lock file on every locked route, including `goal status` with no goal. Bounded (gitignored by bootstrap), but a read route mutates the workspace. Fix: skip locking/creation when the state directory does not exist.
- **FBL-018 — LOW — Environment-dependent test.** `tests/test_goal.py:203` stores `python passes.py`; on hosts without a bare `python` on PATH the policy screen rejects it and the test's intent (policy-invalid-later) is not exercised as designed. Fix: use `sys.executable` or a fixture shim.
- **FBL-019 — NOTE — Wrapper honors ambient uv configuration.** `src/pstack_kiro/bootstrap.py:95` runs `uv sync --quiet --locked` per invocation without `--no-config`; `--locked` plus lock hashes bound resolution, so this is a documented-trust limitation, not a defect.
- **FBL-020 — NOTE — PATH trust for optional tools.** `doctor.py:255-256` (`kiro-cli agent validate`), `:296-297` (`git check-ignore`), `knowledge.py:25,94` (`okn`) resolve executables from PATH; consistent with the documented design.
- **FBL-021 — NOTE — Host-specific paths in docs.** `docs/kiro-v3-compatibility.md:42`, `docs/validation-report.md:54,75,147` embed a developer home path; not a credential, but reduces portability of the evidence.
- **FBL-022 — NOTE — Round-1 Fable evidence is an extraction.** `docs/validation-report.md:305-308` and `reviews/fable-round-1.md:5-9` disclose the truncated envelope honestly; treat that ledger as Codex-authored.
- **FBL-023 — NOTE — Mixed pattern styles.** `pstack.json:23,60` use `./**` while `:49-53` use bare `.pstack/**`; Kiro's path normalization is unverifiable here — the FBL-013 campaign's observed deny should settle it.
- **FBL-024 — NOTE — Verified context.** No `shell=True`, `yaml.load`, `pickle`, `eval`, or trust flags in source; delegated profiles are `["read","knowledge"]` (`tests/test_kiro_assets.py:250-252`); Stop hook `enabled: false` (`pstack-tripwire.json:13`); SessionStart hook executes no repository code (`pstack-session.json:10`); `feature generate` overwrite only with `--overwrite` (`cli.py:173,181,217`); lock pins match `pyproject.toml:14-17`.

## Acceptance ledger

| ID | Fix task | Acceptance test | Status |
| --- | --- | --- | --- |
| FBL-012 | Remove trailing-wildcard `git diff*`/`git log*`/`git show*` allows in `templates/project/.kiro/agents/pstack.json:30-34` (move git to `ask` or enumerate exact forms); align `docs/kiro-v3-compatibility.md:86,165`; add regression test | New `test_primary_profile_never_allows_git_forms_that_execute_or_write` asserting no allow pattern fnmatches `git difftool -y --extcmd=sh HEAD~1 HEAD`, `git diff --output=.kiro/hooks/evil.json`, `git log -1 --format=%B --output=.pstack/state/goal.json`, `git show --output=/tmp/escape HEAD`, `git diff --ext-diff`, `git log --output=../outside.txt`, `git diff --no-index /etc/hosts /dev/null`; expected fail now, pass after fix; `kiro-cli agent validate --path templates/project/.kiro/agents/pstack.json` exit 0 | open |
| FBL-013 | Run the fixture campaign under `--agent pstack`/`/agent swap pstack` and record commands, observed ask for `goal verify`, observed control-plane deny, observed git allow/ask, final `goal status --output json` in `docs/validation-report.md` | `grep -n -- "--agent pstack\|/agent swap pstack" docs/validation-report.md` hits a post-remediation campaign section containing a `"status": "passed"` status payload and the observed ask/deny prompts; expected absent now, present after | open |

## Validation evidence assessed

Source and test inspection (static, this review):
- Agent/hook/steering templates: `templates/project/.kiro/agents/*.json`, `templates/project/.kiro/hooks/*.json`, `dev.kiro/steering`.
- Runtime: `src/pstack_kiro/{cli,goal,runner,features,bootstrap,doctor,knowledge,paths}.py`; `pyproject.toml`; `templates/projectctl/uv.lock`.
- Skills: `skills/verified-goal/SKILL.md`, `skills/setup-pstack`.
- Tests read in full or in relevant part: `tests/test_kiro_assets.py`, `test_runner.py`, `test_goal.py`, `test_bootstrap.py`, `test_hardening.py`, `test_features.py`, `test_edge_cases.py`, `test_cli.py`, `test_cli_direct.py`, `test_doctor.py`, `test_knowledge.py`, `test_packaging.py` — coverage of failure, boundary, adversarial, idempotence, and state-transition cases confirmed by reading; none executed.
- Docs/provenance: `docs/{usage,architecture,kiro-v3-compatibility,validation-report}.md`, `reviews/*`, `THIRD_PARTY_NOTICES.md`, `NOTICE`, `.gitignore`, `examples/verified-goal-demo/README.md`.

Command results reported only by the repository (claims, not independently verified):
- `pytest` 463 passed, 88.98% branch coverage; ruff/ty/wheel build gates (`docs/validation-report.md:140-149`; `reviews/acceptance-criteria.md:101-105`).
- `kiro-cli agent validate` success and observed Kiro snapshot (`docs/kiro-v3-compatibility.md:40-52`).
- Kiro V3 fixture campaign under `kiro_default` with `gpt-5.6-sol`/max (`docs/validation-report.md:156-254`).
- External Fable round-1 and Grok round-2 reports and their dispositions (`reviews/`).

## Residual limitations and unverified claims

- Kiro's exact shell-pattern semantics (whole-string glob vs. prefix; tokenized vs. raw string) and path normalization for `./**` vs `.pstack/**` cannot be established from the repository; FBL-012 holds under prefix or glob semantics for the `--output=` and `--no-index` forms, while the `difftool` form depends on `*` spanning `tool …` as the candidate's tests assume.
- The exact bytes `git log --format … --output=<path>` writes were not verified; `git diff --output=<path>` truncation/overwrite is sufficient for the finding.
- Hook `timeout`/`enabled` field semantics, `/agent swap` discovery timing, and whether Powers/skills are auto-discovered in the current session are documented from claimed observation only (`docs/validation-report.md:319-322`).
- Real `okn` behavior is untested in the repository (`reviews/acceptance-criteria.md:27`); tests monkeypatch `which`.
- No test, build, lint, coverage, Kiro, or shell command was executed by this review; all numerical results above are repository claims.
- The coverage configuration path used in reported gates is outside the snapshot (FBL-016), so the reported percentages are not reproducible from the snapshot as written.
- This pass appears to precede the repository's planned selected-profile campaign (`docs/validation-report.md:295-297`); a subsequent final pass over that evidence is still required by the candidate's own review order.
