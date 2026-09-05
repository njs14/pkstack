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
| Installation | Archive installs cleanly; setup is idempotent and preserves user work | Source install, idempotence, and three conflict modes passed; final archive pending |
| Legacy transition | v0.2.0 rejection makes no writes; documented clean transition preserves source and evidence | Three rejection modes preserved 302 files; clean transition preserved all four user fixtures |
| Permissions | Allowed operations work; equivalent denied forms remain blocked | Three native hard-deny forms and one ask/cancel control passed; combined-short-option limitation retained |
| DO / PROVE / KNOW | Generated parity, doctor, feature gates, and canonical okn validation pass | Doctor81, schema, canonical okn, generated parity passed; upstream freshness nonzero for two sources |
| Updater | Current review context supports a bounded live campaign and correct accept/reject handling | Prior rejection context defect confirmed |
| Deterministic gates | Repository, Power, formatting, lint, types, lockfile, and workflow checks pass | 184 repository / 861 Power tests passed; final delta checks pending |
| Packaging | Two identical archives, correct contents/checksum/version, extracted-consumer smoke | Pending candidate freeze |
| Independent review | Frozen candidate accepted with no unresolved material findings | Pending |
| Delivery | Exact PR/main commit CI, release notes, upgrade guide, and publication handoff | Pending |

## Findings

| ID | Reproduction / diagnosis | Required closure |
| --- | --- | --- |
| R030-01 | Archify's compact sequence expands beyond the desktop viewport; original visual receipt fails | Fix responsible reader layout and check real renders without lowering thresholds |
| R030-02 | Required control-loop taxonomy was absent from the loaded method in a fresh conversation | Make the required method reliably available and retest native loading |
| R030-03 | Generated loop advertises two attempts but does not enforce them; valid baseline trim is rejected | Fresh generation enforces bounds and preserves baseline identity through negative cases |
| R030-04 | Updater PR #32 review confused neighboring file records and rejected a valid same-day date | Bind explicit changed record identities/date semantics into bounded review context; regression and live acceptance |
| R030-05 | Candidate gate omits checks run in ordinary CI | Align required deterministic checks without extending credential access |
| R030-06 | Changelog understates unreleased work and rewrites historical v0.2.0 identities | Accurate 0.3.0 notes and historical release description |

| R030-07 | Primary profile has no forced git-switch deny rule; reordered destructive forms reach ask | Narrow native-matcher repair and equivalent-form verification |
| R030-08 | Fresh Archify sequence caption moves inside its preceding band | Keep caption associated with its own band and verify unchanged fresh JSON |
| R030-09 | Current feature documentation says six sources but manifest has seven | Corrected to reference the configured entries |
| R030-10 | Native CLI rejects kiro_default and cannot discover Power-local setup after a Default swap | Corrected default-agent spelling and documented conditional Power discovery / tested script path |

Additional findings enter this ledger when reproduced. External blocks stay
incomplete; historical successes never stand in for current-candidate evidence.

## Evidence handling

Local campaign data is retained in `/private/tmp/pkstack-release-030-evidence/`.
Keep commands, hashes, native session identifiers, terminal results, and limits
in scoped reports. Do not commit credentials, private reasoning, or raw session
transcripts. Preserve the original failing evidence alongside retests.
