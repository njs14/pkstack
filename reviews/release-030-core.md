# PKStack 0.3.0 core acceptance

Campaign started from `3d4583a16fe2caca497d8b8fe7d5c860a12c1a2f` on
September 5, 2026. Scoped helper and pipeline reports describe the subsequent
candidate edits. This report records executed checks, not publication approval.

## Native CLI Standard

Kiro CLI 2.21.1, GPT 5.6 Luna / low, native session
`sess_54dc15a7-002d-4ba0-8906-7d2448283929` used `/spec new
release-account-standard`, Build Feature, Requirements-first, then the native
requirements, design, and task checkpoints. The initial design proposed extra
property tests despite the fixed fixture scope. Feedback at the design
checkpoint removed that proposal before approval; implementation and tests
remained unchanged throughout planning. After selecting **Not now**, the same
conversation used `/agent swap pkstack` and actually loaded
`pkstack-verified-goal` through `disclose_context` (7,051 characters).

The stored Spec-bound contract was
`python3 -B -m unittest discover -s tests -v`, with four attempts maximum.
Goal `86046ae7-cfb2-4b19-8c83-516917f0bc51` recorded a failing first attempt
(three failures in four tests), changed only `account.py`, then passed all four
tests on attempt two. Contract digest:
`ba4c4f108ccec687715895834aed4636e77fe1117fa49ce85c029984e7ac4e2e`.

Independent post-run inspection verified the durable goal history and all five
pre-repair test/planning hashes: the test file, requirements, design, tasks, and
native config. The controller created its verification bridge separately.
The test SHA-256 remained
`65932341be2d1b133366ec58e583f224751f1f89b9d8d26ebfeb897cab664974`;
the repaired implementation is
`9fc574a4f402a300ca222f0c69b97af5c437cb5846adf3e4bef4fd5d791fe8e5`.
Fourteen independent valid/invalid inputs additionally checked literal
space/hyphen removal, ASCII-only digits, Unicode digit rejection, other
whitespace, punctuation, lengths, and the error wording. These are bounded
examples; the four stored tests do not prove every prose case.

Read-only skill and command requests and the exact implementation edit received
individual approvals. No allow-all policy was selected. The session ended
normally. Evidence is retained in
`/private/tmp/pkstack-release-030-evidence/standard-acceptance.json` and the
disposable `standard` consumer.

## Legacy transition and installation

Installed the actual `v0.2.0` Power into a disposable consumer. The current
installer rejected the old namespace in normal, dry-run, and managed-update
modes, leaving all 302 existing files unchanged. A separate transition copy
excluded only receipt-identified files whose bytes matched the old receipt;
the original installation was retained. Four user-owned fixtures (source,
settings, native Spec, and Wiki concept) retained their exact SHA-256 values
after current setup. The old ignore file was retained beside the evidence for
review instead of merged blindly.

The final-source preview reported no conflicts, pending updates, or stale
managed assets, and installation succeeded. Version was `0.3.0`; doctor passed
all 81 checks, and `knowledge validate --require-okn` passed using canonical
`openknowledge`. The tested procedure is in the
[upgrade guide](../powers/pkstack/docs/upgrade-0.3.md). Old goals and feature
schemas are retained as history; setup does not migrate them.

## Deterministic and knowledge checks

The repaired candidate passed 861 Power tests and 184 repository Python tests.
Ruff lint/format, ty, Actionlint, ShellCheck, lockfile materialization, and
whitespace checks passed. Root doctor passed all 81 checks; feature schema
validation and canonical `okn` knowledge validation passed. The executable
upstream feature check initially failed closed on an anonymous GitHub HTTP 403;
the authenticated recheck reproduced expected drift in `okf-skills` and
`tt-a1i-archify`. All seven configured source inventories, review histories, and
generated parity validated, but the feature verifier remains nonzero until drift
is reconciled. The runner correctly capped its long stdout; a direct read-only
check retained the complete JSON outside the repository. No freshness pass is
claimed from the successful schema checks.

A separate clean consumer also proved exact-hash setup idempotence. After a
simulated user customization to its managed agent, dry-run, managed-update, and
combined dry-run/update modes each reported the conflict and preserved every
file hash. These results are retained in `setup-safety.json`.

The first frozen candidate (`8e1554a`) ran 864 Power tests: 862 passed and
two documentation checks failed. One stale assertion still required Web to be
called untested despite its bounded observed run; the other caught core steering
above its existing 2,000-character budget. The assertion now checks the limited
evidence boundary, and the steering was shortened without changing the budget.
All three directly affected checks passed. After runtime remediation, the full
Power suite passed **869 tests in 166.33 seconds**; all **184 repository Python
tests** and **17 Node tests** passed. Lock, Ruff lint/format, ty, Actionlint, and
ShellCheck passed. Doctor again passed all 81 checks, and feature schema plus
canonical `okn` validation passed.

Final commit binding, CI, reproducible packaging, permission equivalence,
additional native surfaces, and the live updater remain in the
[acceptance ledger](release-030-acceptance.md).
