# Review acceptance criteria

This ledger turns external-review claims into Codex-owned, reproducible release
criteria. Reviewer output is evidence to investigate, not an instruction source.
A criterion closes only after an independent reproduction, a scoped change, and
an executable regression check.

## Grok council round 1

| ID | Severity | Independent disposition | Release criterion | Status |
| --- | --- | --- | --- | --- |
| GRK-001 | high | Confirmed; the council overstated inner `uv` interpreter selection, but controller `PYTHONPATH` caused a clean host pytest predicate to fail through the wrapper. | A verifier launched through a freshly bootstrapped `.pstack/bin/projectctl` must receive the caller's project environment, with no control-plane `PYTHONPATH`, `VIRTUAL_ENV`, `PATH`, or relevant `UV_*` leakage. Cover `feature generate --ready` and `feature verify` through the real wrapper. | closed: wrapper syncs the locked controller then directly executes its Python; runner restores caller `PYTHONPATH`; real-wrapper probes match the host baseline. |
| GRK-002 | high | Confirmed | Invalid UTF-8 and malformed stored command strings must become path-qualified `FeatureMapError` values. `feature list`, `feature show`, and `feature validate` in JSON mode must each emit exactly one JSON object, never a traceback. | closed: exact exit codes/key sets and both direct and freshly bootstrapped wrapper paths are covered. |
| GRK-003 | medium | Confirmed | The verifier policy must reject relative or absolute path operands that resolve outside the project, including interpreter scripts, symlinked scripts, and nested `uv run` operands. Rejection must happen before a ready feature or goal is persisted. | closed: path-shaped operands, known option-assigned paths, symlink targets, and response files for recognized consumers are screened; goal-state regression proves rejection before state creation. |
| GRK-004 | medium | Confirmed; plain V3 uses `kiro_default`, and no portable repository-owned default-agent mechanism was found. | The post-setup workflow must attach the generated `pstack` custom agent before `/verified-goal`, or explicitly disclose that its ask/deny rules are inactive. The normal path must remain Kiro CLI V3 and must not launch an external ACP host or `kiro-cli acp`, or claim native `/goal`. | closed: setup hands off to `/agent swap pstack`, with `kiro-cli chat --v3 --agent pstack` as the discovery fallback; global defaults remain untouched; the live `pstack` campaign is preserved in `reviews/kiro-selected-profile-evidence.json` and discloses Kiro's internal ACP-named event adapter separately from the external/default-path boundary. |

## Grok council low-risk hardening

These items are not release-blocking by severity, but each is tracked so the
final acceptance reviewer sees an explicit disposition.

| ID | Disposition target | Status |
| --- | --- | --- |
| GRK-005 | Make goal-state locking fail closed when POSIX `fcntl` is unavailable, matching bootstrap and architecture documentation. | closed with fail-before-write regression |
| GRK-006 | Require an explicit boolean `draft` field rather than treating omission as ready. | closed with strict-schema regression |
| GRK-007 | Correct the misleading read-only trust test/profile wording; verifier subprocesses are approval-gated but not intrinsically read-only. | closed by non-editing/side-effect-aware wording and corrected test name |
| GRK-008 | Prevent an `okn search` query from being interpreted as an option without inventing an unverified `--` grammar. | closed by rejecting leading-hyphen queries; canonical `okn` remains absent on the test Mac |

The council's separate compound-command bypass hypothesis was rejected after
checking Kiro's current permission contract: shell compounds are parsed into
subcommands and each is matched independently, with `deny` taking precedence
over `ask` and `allow`. The final live campaign still exercises the selected
profile rather than relying on this static conclusion alone.

## Grok council round 2

Round 2 reviewed frozen commit `d67ae0fe8ec96b0720acc4f19c39e132861eb742`
with the same official Grok Build 4.6/xhigh read-only harness. Its complete
report is `reviews/grok-round-2.md`. The following claims were held open until
Codex reproduction; each was confirmed and converted into a release criterion:

| ID | Severity | Independent disposition and release criterion | Status |
| --- | --- | --- | --- |
| GRK-011 | high | Confirmed across policy, goal, feature, validation, and a fresh wrapper. Outside absolute argv[0] must be rejected before persistence; only a canonical match for the current PATH-selected executable may run outside the root. | closed: service and fresh-wrapper regressions reject the planted binary and preserve PATH-selected system/uv executables. |
| GRK-012 | medium | Confirmed and expanded by live Kiro 2.20.2 delegation: child shell permission effects did not reliably constrain an exposed shell after parent-authorized spawn. Every delegated read-only profile must omit both `shell` and `write`; the primary session owns execution. | closed: architect, reviewer, and verifier expose exactly `read` and `knowledge`; asset tests and a disposable live delegation control prove shell is unavailable. |
| GRK-013 | medium | Confirmed with a disposable Power v1-to-v2 upgrade and selected `pstack` profile. Cached `projectctl setup` must fail without explicit `--power-root`, and the current-session refresh path must return temporarily to a Power-enabled agent. | closed: structured wrapper failure, explicit-root detection, Power-local dry-run/apply receipt checks, and always-loaded same-session swap guidance are covered. |

Round 2 also reported four low-risk hardening opportunities:

| ID | Disposition target | Status |
| --- | --- | --- |
| GRK-014 | Keep the older-Python setup fallback from creating a Power-local `.venv`. | closed: fallback adds `uv run --isolated`; argv regression added. |
| GRK-015 | Do not let commented or substring `.gitignore` text impersonate required runtime patterns. | closed: exact uncommented-line membership is shared by setup and doctor. |
| GRK-016 | Prevent the legal-looking slug `readme` from becoming an invisible contract. | closed: `readme` is reserved at load, lookup, and generation boundaries. |
| GRK-017 | Reject attached inline interpreter forms such as `python -cCODE` and `node --eval=CODE`, including nested `uv run`. | closed: normalized direct/nested option detection and regressions added. |

At that checkpoint, the expanded 185-test and 88.43% branch-coverage gates
passed, and the planned remaining order was Fable peer review, Grok residual
sweep, the post-remediation Kiro profile campaign, and a final evidence-bearing
Fable acceptance pass. The later sections record completion of every step
except that final Fable gate; any material change still returns to Fable.

## Fable peer review round 1

Fable reviewed frozen commit
`6b72a713bb9966cc6325381b91ea44e961e869e4` as the peer advisor and returned
`REJECT`. The extracted report is `reviews/fable-round-1.md`. Codex independently
reproduced every material finding before remediation.

| ID | Severity | Independent disposition and release criterion | Status |
| --- | --- | --- | --- |
| FBL-001 | medium | Confirmed through a fresh wrapper: `true`, `echo`, bare/version controller self-reference, feature validation, and goal completion all accepted empty evidence. Obvious placeholder and control-plane self-reference forms must be rejected centrally before feature/goal persistence and on later validation/execution, without claiming semantic proof for arbitrary scripts. | closed: central policy is applied at feature creation, goal creation/load/save, and execution; service, direct, nested, and fresh-wrapper regressions pass; Fable round 2 found the feature/goal evidence boundary clear |
| FBL-002 | medium | Confirmed statically. Every invocation under the canonical `.pstack/bin/projectctl` prefix, including setup, ready generation, resume, clear, and future routes, must match an agent-scoped `ask`; no rule is added for a potentially foreign `./projectctl`. | closed: one catch-all canonical-prefix rule covers the route matrix; all four profiles validate on Kiro 2.21.0; Fable round 2 found the controller surface clear |
| FBL-003 | medium | Confirmed through the public CLI: active `1/4` plus `resume --max-attempts 1` wrote unloadable state. Invalid resumes must preserve valid state, and no writer may atomically replace evidence with a value that fails serialized/schema/semantic validation. | closed: transition guard, serialized round-trip, central save barrier, and whole-state concurrent-result guard pass service and direct-CLI regressions; Fable round 2 found goal transitions/invariants clear |
| FBL-004 | medium | Confirmed through both copied entrypoints. Any inferred or explicit asset root under target `.pstack` must fail as cached self-authority with structured exit 2 and no managed-file change; external Power-local and installed sources remain supported. | closed: cached authority, source symlink, symlink loop, and macOS case-folded aliases fail closed without managed changes; Fable round 2 found bootstrap authority clear |

The low findings are also explicitly dispositioned:

| ID | Disposition | Status |
| --- | --- | --- |
| FBL-005 | Perform all feature input/policy validation before creating directories. | implemented; rejected-generation no-side-effect regression passes |
| FBL-006 | Reject the named generic wrappers; retain and document a conservative, non-sandbox heuristic boundary. | implemented for named wrappers; semantic relevance remains an explicit human-review limitation |
| FBL-007 | Expand denial coverage for recursive removal, destructive Git restoration, branch deletion, and forced push. | implemented in primary profile, including global `git -C`, postfix force, forced-ref, mirror, branch-delete, and checkout-restoration forms; representative glob matches, static assertions, and Kiro schema validation pass |
| FBL-008 | Deny direct write-tool access to `.pstack` and generated Kiro agent/hook/skill/steering control-plane paths; controller subprocess writes remain separately approval-gated. | implemented with explicit deny-over-ask patterns and regressions |
| FBL-009 | Keep fail-closed symlink handling and disclose that discovery-marker symlinks are unsupported. | documented as an intentional containment trade-off |
| FBL-010 | Align arena/swarm instructions with the shipped read-only delegated profiles. | implemented; primary now materializes returned candidate/finding text |
| FBL-011 | Show `goal.contract.display` and provenance before the first proof in every skill invocation, including when continuing existing active state. | implemented and asset-tested |

## Codex adversarial closure before Fable round 2

After closing FBL-001 through FBL-011, Codex ran bounded adversarial and
compatibility audits before freezing the next peer-review snapshot. These are
primary implementation criteria, not additional Fable claims:

| ID | Release criterion | Status |
| --- | --- | --- |
| CDX-001 | A verifier must select an explicit non-shell project predicate. Direct shells, inline or stdin interpreters, package-manager execution wrappers, controller source/package/cache aliases, and obvious constant or informational commands must fail closed through both direct and recursive `uv run` forms. | closed: restrictive command grammars and direct/nested/fresh-wrapper regressions pass |
| CDX-002 | Path containment must cover executables, interpreter targets, local file URLs, known attached path flags, compiler `-oPATH`, symlink targets, and response files for known consumers. Top-level `uv` context environment aliases cannot move execution outside the stored project root. | closed: direct/`uv` containment probes preserve outside fixtures byte-for-byte; recognized response-file indirection is rejected |
| CDX-003 | Read-only Git evidence must use a built-in allowlist and reject local aliases, external helpers, output files, mutators, help-only forms, and ambiguous global options. Pytest cannot replace stored project options through `addopts` overrides. Timeouts must be positive, finite, and supported by the platform. | closed with policy and no-side-effect regressions |
| CDX-004 | Conservative option parsing must retain ordinary data semantics after `--` and permit `@`-prefixed data for tools that do not implement response files. | closed: direct and nested pytest/Cargo/npm boundary cases plus grep/project-script data cases pass |

At this checkpoint, `uv run pytest -q` reports 463 passing tests, branch
coverage is 88.98% against the configured 85% floor, lint/format/types/lock and
diff checks pass, and every generated Kiro agent schema validates on Kiro CLI
2.21.0. The remaining semantic limitation is explicit: this policy is not an
OS sandbox and cannot prove that an arbitrary project-owned script is relevant.

## Fable peer review round 2

Fable 5.1/max reviewed frozen commit `f96df36` through the read-only harness and
returned `REJECT`. Its verbatim result and session metadata are in
`reviews/fable-round-2.md`. Codex reproduced the permission finding with the
same whole-string glob matcher used by the asset tests; all five representative
hostile Git forms matched unconditional `allow` rules before remediation.

| ID | Severity | Independent disposition and release criterion | Status |
| --- | --- | --- | --- |
| FBL-012 | high | Confirmed. No Git command may receive unconditional shell approval from the primary profile: prefix globs admit `difftool` helper execution, `--output` writes into control-plane paths, and `--no-index` reads outside the workspace. Every Git shell form must instead match explicit `ask`, with destructive forms still matching `deny`. | closed in source and live campaign: removed all Git `allow` patterns, added exact `git`/`git *` ask coverage, aligned docs, added hostile/safe matcher regression, revalidated the profile on Kiro 2.21.0, and observed a one-time approval for the exact `git status --short` probe under the selected `pstack` profile; final Fable re-review pending |
| FBL-013 | medium | Confirmed as an intentionally pending evidence gate rather than a source defect. A fresh fixture campaign must select the generated `pstack` profile, stay in one normal V3 session, observe controller approval and control-plane denial behavior, record a real fail-repair-pass goal, and preserve exact post-run evidence. | closed: `reviews/kiro-selected-profile-evidence.json` preserves session `sess_3cebc0c9-ac7a-42d1-a898-9251ac6bb3f8` running `gpt-5.6-sol`/max in normal V3 with mode `pstack`; every controller call asked once, the filesystem probe was denied, goal `9bc07fe8-8bc1-4c62-826d-3f2bb2beaf93` recorded exit 1 then exit 0 against one unchanged feature-map contract, the tracked project implementation diff was only `account.py`, and the remaining writes were expected controller-owned goal/lock state |

Fable's low and note items were dispositioned as follows:

| ID | Disposition | Status |
| --- | --- | --- |
| FBL-014 | Remove the unreachable pre-run exhaustion transition. | closed; validated active state always has remaining budget and only a failed final attempt transitions to exhausted |
| FBL-015 | Preserve fail-closed status for policy-invalid stored predicates while allowing explicit `goal clear --force` recovery after evidence preservation. | closed with service regression and recovery documentation; malformed or contradictory state remains rejected |
| FBL-016 | Record a snapshot-relative coverage invocation. | closed at the current checkpoint with `--cov-config=pyproject.toml`; historical host-path commands remain unchanged as exact provenance |
| FBL-017 | Keep read-only status/tripwire queries from creating state/lock artifacts when no goal exists. | closed: atomic reads no longer acquire a mutation lock; no-artifact regression passes |
| FBL-018 | Remove the test's ambient bare-`python` dependency. | closed with `sys.executable` |
| FBL-019 | Prevent ambient uv configuration from changing cached-controller sync. | closed beyond note severity: wrapper pins `--locked --no-config`; generated-wrapper assertion passes |
| FBL-020 | PATH resolution for optional host tools. | accepted design boundary; commands remain explicit, reported, and subject to host/user trust |
| FBL-021 | Host-specific paths in historical evidence. | accepted for exact historical provenance; the current portable gate uses a relative config path |
| FBL-022 | Round-1 report is a disclosed Codex extraction. | accepted provenance note; round 2 stores the verbatim final result field |
| FBL-023 | Mixed path-pattern spelling needs live normalization evidence. | closed: the selected `pstack` profile denied `fs_write` to `.pstack/deny-probe.txt` with the matched `.pstack/**` agent-profile rule, and both Kiro file search and an independent filesystem check confirmed the file was absent |
| FBL-024 | Negative fake-capability/security scan. | confirmed clear by Fable round 2 |

After these source fixes, later gates reached 488 passing tests and 89.04%
branch coverage. The selected-profile evidence campaign subsequently closed
FBL-013/FBL-023; the final independent Fable decision remains the release gate.

## Grok council round 3

The official Grok Build 1.0.13 harness reviewed frozen commit `61c6e0c` with
`grok-4.6` at `xhigh`. Its verbatim output is `reviews/grok-round-3.md`. The one
reported material issue was held open until Codex reproduced the exact producer
and consumer paths with pinned PyYAML:

| ID | Severity | Independent disposition and release criterion | Status |
| --- | --- | --- | --- |
| GRK-021 | medium | Not reproduced. Generated feature YAML must reload without changing any legal slug, title, or argv string that YAML 1.1 could otherwise type implicitly. | rejected after reproduction: `yaml.safe_dump` already quotes ambiguous strings; `on`, `off`, `yes`, `no`, `true`, `false`, `y`, `n`, `null`, `none`, `2`, `Yes`, `NO`, `Null`, and `~` all round-trip and validate under the locked runtime; a parametrized producer/load/validate regression now preserves that contract |

The low and note items were dispositioned independently:

| ID | Disposition | Status |
| --- | --- | --- |
| GRK-022 | Correct the legacy setup-shim fallback's target-root inference. | closed: the shim now finds the nearest real `.pstack/projectctl` ancestor candidate instead of using a fixed incorrect parent depth; legacy-location regression passes |
| GRK-023 | Reject non-string elements in spec-bridge argv rather than stringifying JSON booleans or numbers. | closed centrally in `parse_command`; spec regression and documented string/list/tuple/`CommandSpec` compatibility checks pass |
| GRK-024 | Broad `git checkout *` denial also blocks branch creation. | accepted safety bias: verified-goal does not require checkout, and `git switch -c` remains available through explicit approval |
| GRK-025 | Current-session behavior is instructional rather than mechanically enforced. | accepted and already documented; the skill is deliberately a thin seam, not a scheduler or fake native `/goal` |
| GRK-026 | Selected-profile campaign is pending. | closed by the same normal-V3 `pstack` campaign recorded for FBL-013/FBL-023 |
| GRK-027 | A project verifier can fork a child, exit 0, and have that descendant killed after the parent result is collected. | accepted documented arbitrary-script/non-sandbox boundary; project predicates remain user-reviewed and semantic relevance is not claimed |

Grok's unmatched-shell dissent was rejected against Kiro's current official V3
permission contract: common read-only Git commands have ambient allows,
everything else asks, and the agent's explicit Git `ask` wins over ambient
`allow`. Its Git-output dissent is likewise approval-gated after FBL-012; the
filesystem deny is explicitly described as a direct-write-tool boundary, not a
sandbox around an approved shell subprocess.

## PK-Stack final naming and DRY pass

| ID | Acceptance criterion | Status |
| --- | --- | --- |
| PKS-001 | The Kiro Power is presented as **PK-Stack**, expanded **Poteto Kiro**, with manifest ID `pk-stack`. Runtime code must take display identity from one branding module. The established `pstack-kiro` distribution/repository/receipt manager, `pstack_kiro` package, `pstack` agent and compatibility paths, `.pstack` paths, `projectctl` commands, and setup inventory token remain stable and are documented as compatibility interfaces; user-facing slash-command routes use the `pk-stack` slug convention, including `/setup-pk-stack`. Historical council reports and upstream provenance stay exact. | closed: implementation, frozen local gates, final package audit, and authoritative live campaign pass; Fable 5.1/max final review returned `ACCEPT` with no material finding |
| PKS-002 | The pre-release Power-ID change from `pstack-kiro` to `pk-stack` must be explicit: Kiro may retain the earlier import as a separate entry, and removal uses Kiro's Power management interface without deleting project files. | documented in README and usage; live Power import remains outside the repository-only gate |
| PKS-003 | Visible contributor metadata, projectctl text/JSON identity, all four agent profiles, both hook fallback payloads, and downstream brand tests must agree with the single runtime identity source; only one complete identity-tuple test anchor may hard-code all canonical brand values. | closed: metadata and runtime output aligned; downstream identity checks derive from branding constants, while static human/Kiro surfaces are mechanically pinned; 43 focused tests, exact installed-wheel text/JSON identity, and all four Kiro schema validations pass; compatibility identifiers and historical/provenance records remain unchanged; Fable final scope matrix is clear |

## Final Codex preflight

The evidence-bearing snapshot received one more independent source audit while
the Fable account window was unavailable. These are Codex-owned findings, not
substitutes for the final Fable decision:

| ID | Severity | Reproduced defect and release criterion | Status |
| --- | --- | --- | --- |
| CDX-001 | medium | `doctor` returned `ok: true` after a receipt-owned cached controller module drifted, and after both live and cached `pstack` profiles drifted together, even though setup preflight detected the same corruption. Doctor must validate the ownership receipt and every receipt-managed path/hash, fail on missing or changed assets, and keep a clean bootstrap green. | closed: one read-only receipt audit now validates schema, manager, non-empty inventory, safe paths, and every managed digest; clean doctor reports 49 matching files, while cached drift, synchronized permission drift, missing files, invalid receipts, symlinks, and installed-controller failure paths are regressed in 28 doctor tests |
| CDX-002 | medium | `feature generate --ready` returned success for an escaping/missing related path that immediate validation rejected, and an injected `## Expected path` heading silently replaced the caller's requested expected path. Ready generation must establish exact semantic round-trip and related-path validity before running proof or writing; invalid input must run no verifier and leave the target absent or unchanged. | closed: the exact candidate is parsed and compared before proof and immediately before atomic commit; ready links require containment/existence, rejected input runs no proof and preserves targets, and valid ready plus deferred draft paths are regressed |
| CDX-003 | low | Drafts may defer existence of an in-project related document, but the generator should not author empty, absolute, escaping, or unresolvable related paths that immediate validation rejects. | closed: draft preflight now defers only existence; three invalid path classes fail before the feature directory is written, while a contained future document remains supported |
| CDX-004 | low | The first frozen-candidate live run created 13 untracked `__pycache__` files in receipt-owned controller source. Normal controller execution must write no local bytecode and must not trust a pre-existing unchecked-hash cache that could bypass source receipt evidence. | closed: the wrapper uses `-B -X pycache_prefix=/dev/null` before `-m`; installed-wheel regression proves no cache writes, demonstrates the `-B`-only unchecked-cache failure, and proves the canonical wrapper ignores it. CPython 3.11/3.12/3.14 checks, 44 focused tests, 508 full tests, the complete package audit, and the fresh selected-profile V3 campaign all pass; the live audit found zero controller caches after every command |

## Authoritative post-CDX-004 live acceptance

| ID | Acceptance criterion | Status |
| --- | --- | --- |
| LIVE-001 | The exact pushed post-CDX-004 candidate must complete a fresh one-session `kiro-cli chat --v3 --agent pstack --model gpt-5.6-sol --effort max` campaign: selected-profile write denial and one-time approvals, immutable feature-backed verifier, failed first attempt, one bounded read-only native verifier, one implementation-only repair, passing second attempt, and no external ACP, nested Kiro, `/spawn`, or claimed native `/goal`. | closed on `b39c20a`: goal `7b9586e8-b204-4443-8c12-147d5088c44e` passed in 2/4 attempts; exact session, permission, command, subagent, diff, digest, and usage evidence is preserved in `reviews/kiro-final-campaign.md` and `reviews/kiro-final-evidence.json` |
| LIVE-002 | The fresh campaign must preserve every receipt-managed asset and the hardened bytecode boundary after real controller use. | closed: doctor 39/1/0, receipt 49/49, wrapper digest matched, and cached controller source contained zero `__pycache__`, `.pyc`, or `.pyo` paths after the full campaign |

## Final Fable acceptance

Claude Code with `claude-fable-5-1` at `max` reviewed evidence-bearing snapshot
`1a145d488d8c585d9a7bbe257ba6edefc2c44d50` through the read-only harness in
`reviews/README.md`. The verbatim result is `reviews/fable-final.md`.

Verdict: `ACCEPT`. All ten required scope rows were completed, and Fable found
no unresolved `BLOCKER`, `HIGH`, or `MEDIUM` item. Its acceptance ledger is
empty. Grok 4.6/xhigh remains the narrower residual sweeper and did not make
the acceptance decision.

| ID | Severity | Independent disposition | Status |
| --- | --- | --- | --- |
| FBL-025 | low | Confirmed in a disposable two-project probe: directly executing project A's cached setup shim can dry-run project B successfully because that explicit path is treated as an external reviewed Power root. This is bounded to a user-selected source, does not escape either workspace, performs no write during dry-run, and remains receipt-auditable. The supported upgrade path remains the active Power-local `/setup-pk-stack`; users should not reuse another project's cache as an upgrade source. | accepted documented residual; non-material and not release-blocking |
| FBL-026–FBL-032 | note | Disabled advisory Stop hook, PATH-resolved optional tools, historical host paths, unsigned receipt, ambient MCP UI noise, verifier non-sandbox boundary, and opt-in ready overwrite were already documented design/environment limits. | no defect |
