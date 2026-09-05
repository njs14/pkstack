# PKStack 0.3.0 release acceptance

Campaign started September 5, 2026 from
`3d4583a16fe2caca497d8b8fe7d5c860a12c1a2f` in an isolated checkout.
This ledger records tested coverage and explicit assumptions. No tag or release
is authorized by this record. The latest published release remains v0.2.0.
On September 5, the user directed that IDE operation be assumed and further GUI
testing should not block delivery. The affected rows below are waived acceptance
checks, not fresh passing native results.

## Required coverage

| Area | Acceptance condition | Current result |
| --- | --- | --- |
| Core routes | All six command routes load and perform their documented role | Five installed routes and direct setup script passed; Power-local setup unavailable in native CLI; native IDE setup assumed by user direction |
| Native planning | CLI and IDE Standard and Quick Spec bind failure, repair, and pass in the same conversation | CLI Standard and Quick passed; IDE GUI checks waived by user direction |
| Additional surfaces | Agent Focus, Crew, and Web exercise applicable advertised paths | Web stored failure/repair/pass; final GUI follow-up, Agent Focus, and Crew checks waived by user direction |
| Curated helpers | All six perform bounded real tasks; generated outputs satisfy independent checks | All six bounded tasks passed with recorded corrections; final builder/verified-goal composition passed natively at attempt 2/4 with an unchanged five-test suite; Archify unchanged-input replays passed |
| Installation | Archive installs cleanly; setup is idempotent and preserves user work | Source install, idempotence, three conflict modes, and extracted-main archive installation passed |
| Legacy transition | v0.2.0 rejection makes no writes; documented clean transition preserves source and evidence | Three rejection modes preserved 302 files; clean transition preserved all four user fixtures |
| Permissions | Allowed operations work; equivalent denied forms remain blocked | Standalone and three grouped forms natively denied; ordinary ask/cancel preserved |
| DO / PROVE / KNOW | Generated parity, doctor, feature gates, and canonical okn validation pass | Doctor81, schema, canonical okn, generated parity passed; all seven upstream sources and authenticated feature verification passed on accepted main 23b34a7 |
| Updater | Current review context supports a bounded live campaign and correct accept/reject handling | First two failures retained and proven defects repaired; third source 33980370382 and candidate gate 33980726626 passed; PR #37 automatically merged after exact review |
| Deterministic gates | Repository, Power, formatting, lint, types, lockfile, and workflow checks pass | 870 Power passed; 185 repository and 17 Node tests passed after retry cleanup repair; static checks passed |
| Packaging | Two identical archives, correct contents/checksum/version, extracted-consumer smoke | Main 3859f63 has historical passing evidence; final report commit requires its own archive/install receipt in the local handoff |
| Independent review | Frozen candidate accepted with no unresolved material findings | Product/cleanup and security/retry scopes approved; exact PR #37 review and merge tree independently verified; GUI assumptions separately disclosed |
| Delivery | Exact PR/main commit CI, release notes, upgrade guide, and publication handoff | PRs #33, #35, #36 merged after exact-head CI; PR #37 merged after exact candidate gates; final report PR/main CI and archive binding will be recorded in the local handoff after passing; publication held |

## Findings

| ID | Reproduction / diagnosis | Disposition / evidence |
| --- | --- | --- |
| R030-01 | Compact Archify sequence expands beyond the desktop viewport | Reader layout repaired; original frozen input, desktop/narrow renders, interactions, and exports passed; see [Archify report](release-030-archify.md) |
| R030-02 | Required control-loop taxonomy was absent from the loaded method | Required method made available in the loaded skill; fresh native design task passed; see [loop helpers](release-030-loop-helpers.md) |
| R030-03 | Generated loop does not enforce its attempt limit and rejects a valid baseline trim | Wrapper repaired; fresh native generation passed five tests and 24 independent process cases; see [loop helpers](release-030-loop-helpers.md) |
| R030-04 | PR #32 review swapped omitted file identities and rejected a valid same-day date | Schema v3 context repaired; live PR #34 Opus approval independently confirmed both correct identities and date; overall updater gate separately failed its base browser test |
| R030-05 | Candidate gate omits ordinary CI checks | Both candidate and base gates now run the complete policy suites and required version/knowledge checks; verified in live run 33977500077 |
| R030-06 | Changelog understates 0.3 work and rewrites historical 0.2 identities | Accurate 0.3 notes and historical 0.2 names restored; exact-version note extraction and immutable links tested |
| R030-07 | Destructive Git-switch spellings reach ask instead of deny | Tested standalone, reordered, prefixed, and three grouped forms now deny natively; benign ask/cancel controls retained; see [permission report](release-030-permissions.md) |
| R030-08 | A fresh sequence caption moves inside its preceding band | Placement repaired; unchanged native JSON replay matches the validated artifact; see [Archify report](release-030-archify.md) |
| R030-09 | Feature documentation says six sources but manifest has seven | Wording now refers to the configured manifest entries |
| R030-10 | Native CLI rejects kiro_default and does not discover Power-local setup after a Default swap | Corrected the default agent name and conditional Power-discovery guidance; direct setup script verified; native IDE setup remains unverified and is waived as a delivery blocker by user direction |
| R030-11 | Upstream Archify delta reproduces malformed-argument output, watcher crashes, and missing caption-width rejection | Three runtime fixes and metadata checks passed; seven-path update accepted transactionally; live detector reports Archify current |
| R030-12 | Evidence index has broken package links and a stale current-version label | Active package paths and status label corrected; local targets verified; historical names retained |
| R030-13 | Reader startup rejection bypasses cleanup and leaves its browser child/profile | Injected failure reproduced the leak; startup wait moved under existing cleanup; regression and real reader/export tests passed; initiating CI timeout remains unproven, as recorded in [browser harness report](release-030-browser-harness.md) |
| R030-14 | Pending-marker cleanup exposes an invalid EOF separator and prevents the next repair | Real Git/prepare regression reproduced a clean-before/failing-after diff; narrow empty-separator cleanup passes while preserving prose, accepted-marker integrity, and unrelated whitespace rejection |

Additional findings enter this ledger when reproduced. Untested checks remain
identified as such, including the GUI checks explicitly waived by the user;
historical successes never stand in for current-candidate evidence.

## Evidence handling

Local campaign data is retained in `/private/tmp/pkstack-release-030-evidence/`.
Keep commands, hashes, native session identifiers, terminal results, and limits
in scoped reports. Do not commit credentials, private reasoning, or raw session
transcripts. Preserve the original failing evidence alongside retests.
