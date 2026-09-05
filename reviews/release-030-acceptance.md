# PKStack 0.3.0 release acceptance

Campaign started September 5, 2026 from
`3d4583a16fe2caca497d8b8fe7d5c860a12c1a2f` in an isolated checkout.
This is a working ledger, not a release verdict. No tag or release is authorized
by this record. The latest published release remains v0.2.0.

## Required coverage

| Area | Acceptance condition | Current result |
| --- | --- | --- |
| Core routes | All six command routes load and perform their documented role | Five installed routes passed; Power-local setup unavailable in native CLI, IDE proof pending |
| Native planning | CLI and IDE Standard and Quick Spec bind failure, repair, and pass in the same conversation | CLI Standard and Quick passed; current desktop planning pending |
| Additional surfaces | Agent Focus, Crew, and Web exercise applicable advertised paths | Web stored failure/repair/pass; follow-up and desktop checks blocked by Mac lock |
| Curated helpers | All six perform bounded real tasks; generated outputs satisfy independent checks | All six bounded tasks passed with recorded follow-up/authoring corrections; Archify unchanged-input replays passed |
| Installation | Archive installs cleanly; setup is idempotent and preserves user work | Source install, idempotence, three conflict modes, and extracted-main archive installation passed |
| Legacy transition | v0.2.0 rejection makes no writes; documented clean transition preserves source and evidence | Three rejection modes preserved 302 files; clean transition preserved all four user fixtures |
| Permissions | Allowed operations work; equivalent denied forms remain blocked | Standalone and three grouped forms natively denied; ordinary ask/cancel preserved |
| DO / PROVE / KNOW | Generated parity, doctor, feature gates, and canonical okn validation pass | Doctor81, schema, canonical okn, generated parity passed; Archify accepted, OKF freshness pending updater |
| Updater | Current review context supports a bounded live campaign and correct accept/reject handling | Source and correct Opus review passed; base browser timeout blocked merge and PR #34 was closed; harness investigation active |
| Deterministic gates | Repository, Power, formatting, lint, types, lockfile, and workflow checks pass | 870 Power, 184 repository, 17 Node tests passed after cleanup repair; lint/format/types/lock/workflow checks passed |
| Packaging | Two identical archives, correct contents/checksum/version, extracted-consumer smoke | Main 3859f63 produced two identical archives and passed extracted-consumer checks; rebind if main advances |
| Independent review | Frozen candidate accepted with no unresolved material findings | Security and product scopes approved through reviewed head 67b7e36; remaining surface acceptance stays open |
| Delivery | Exact PR/main commit CI, release notes, upgrade guide, and publication handoff | PR #33 merged; CI 33976733214 and 33976929179 passed; commit-bound notes and upgrade guide prepared; publication held |

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
| R030-10 | Native CLI rejects kiro_default and does not discover Power-local setup after a Default swap | Corrected the default agent name and conditional Power-discovery guidance; direct setup script verified; IDE setup proof remains a separate open surface gate |
| R030-11 | Upstream Archify delta reproduces malformed-argument output, watcher crashes, and missing caption-width rejection | Three runtime fixes and metadata checks passed; seven-path update accepted transactionally; live detector reports Archify current |
| R030-12 | Evidence index has broken package links and a stale current-version label | Active package paths and status label corrected; local targets verified; historical names retained |
| R030-13 | Reader startup rejection bypasses cleanup and leaves its browser child/profile | Injected failure reproduced the leak; startup wait moved under existing cleanup; regression and real reader/export tests passed; initiating CI timeout remains unproven, as recorded in [browser harness report](release-030-browser-harness.md) |

Additional findings enter this ledger when reproduced. External blocks stay
incomplete; historical successes never stand in for current-candidate evidence.

## Evidence handling

Local campaign data is retained in `/private/tmp/pkstack-release-030-evidence/`.
Keep commands, hashes, native session identifiers, terminal results, and limits
in scoped reports. Do not commit credentials, private reasoning, or raw session
transcripts. Preserve the original failing evidence alongside retests.
