# Validation report

This report separates deterministic local checks, controller proof, the live Docker-backed Floci
campaign, Kiro-session evidence, and model-council acceptance. A pass at one boundary is not
reported as a pass at another. The current snapshot is candidate-complete through the fresh
exact-tree Floci boundary. The selected-profile Kiro campaign and final council gates are still
pending.

## Bootstrap and controller provenance

PK-Stack was generated from the reviewed Power/controller source and retains a 49-file ownership
receipt in `.pstack/bootstrap.json`. The maintained controller source suite passed **508 tests** at
source commit `191997501c41ae078b6548b9d6c898aadf2907ae`. The generated controller was compared
byte-for-byte with that source before the current lab-only hardening work.

The repository-local generated controller currently reports:

```sh
.pstack/bin/projectctl doctor --output json
.pstack/bin/projectctl feature validate --output json
.pstack/bin/projectctl knowledge validate --output json
```

Observed result: 39 doctor checks passed, zero failed, and one optional warning reported that
canonical `okn` is unavailable. All 49 receipt-managed files matched their recorded hashes. The
one ready `document-export` feature contract had zero errors and warnings. Knowledge validation
passed in explicit `feature-map-only` mode; strict broader OKF validation was not claimed.

An isolated temporary repository also exercised ready feature generation, validation, execution,
and a bounded stored goal. Goal `4360c683-7cc7-4bda-b0a5-c2b70b009735` recorded attempt 1 as a
real failure and attempt 2 as passed after the smallest fixture repair. That proves controller
state transitions, not a Kiro session.

## Candidate static gate

After the final pre-live safety audit, all of these commands exited zero:

```sh
env PYTHONDONTWRITEBYTECODE=1 \
  uv run --locked --no-config --no-sync pytest -p no:cacheprovider -q
env PYTHONDONTWRITEBYTECODE=1 uv run --locked --no-config --no-sync ruff check .
uv lock --check
git diff --check
sh -n labctl
./labctl doctor --output json
```

Pytest passed **221 tests** in 5.42 seconds. Ruff and diff checks were clean; the lock resolved 15
packages. Doctor proved Docker server access through context `desktop-linux`, daemon
`fabba3a8-3367-4971-9e85-efbdb563f86f`, the Unix socket at
`unix:///Users/noahsutter/.docker/run/docker.sock`, loopback endpoint
`http://127.0.0.1:4566`, task endpoint `http://floci:4566`, and the pinned Floci 2.0.1 digest.

The `labctl` launcher was also exercised through its fresh non-editable isolated uv environment,
explicit uv-managed Python 3.12 selection, and forced package reinstall. The judge source-closure
precondition saw exactly the five declared `src/pk_stack_lab/*.py` files and no bytecode or added
source.

The post-round-1 audit added regression coverage for state-directory ownership, complete
ledger-bound active identities, untagged-S3 create/tag recovery, stale-image partial cleanup,
bounded subprocess output/process-group termination, every destructive inner-phase crash, and
terminal manifest cleanup. The final audit additionally made every ECS describe/list path reject
unexpected structured failures and bound teardown's Compose input to the original run claim.

## Fresh exact-tree live Floci campaign: `live-final-902`

The final audited source used the public interface only:

```sh
./labctl up --run-id live-final-902 --acknowledge-docker-socket --output json
./labctl deploy --output json
# Remove the controlled temporary build-input marker.
./labctl deploy --output json
./labctl status --output json
./labctl verify --output json
./labctl evidence --output json
```

`up` created claim `ddfc9f0d56d0deb47c208157cd5541fa` with canonical state schema v2,
Compose digest `ffc0ae8024ceb2487f13efc4ee71a0c5c02f89e800e5657bb65783892bd45e38`,
and a cleared S3-create intent after successful tagging. Both deployment generations stabilized
one API and one worker service:

| Generation | Source digest | Docker image ID | API/worker revisions |
| --- | --- | --- | --- |
| controlled marker | `8ed57e672518fe41188f5b9ec2275eca9ad57eba65f157def997971e443dba12` | `sha256:4b5b4315c29eb040870840764d323a2ee4aeb4eaa04fc569675e9302139963c1` | `:1` / `:1` |
| restored candidate | `d36f1eabc87725beab70b474a4777637520edb118a10bcecf7c20ad905a8977e` | `sha256:4566a83166a5ddb123b72a205b08aefd3cf2da700f337a89e8c41692226e58f7` | `:2` / `:2` |

The append-only ledger retained all 16 planned and observed image/task-definition events. The
active API task was `2e147d27a9e44c57b2f8bee70102f730`; the worker task was
`07458654a12d46d5aa5034aa1b146094`.

The live verifier returned `ok: true` for export `e-387e74ba4a1222f1`. It proved API request
idempotency, terminal `COMPLETE`, exact object
`exports/tenant-a/e-387e74ba4a1222f1.json`, exact JSON body/content type/ETag, tenant-key partition
separation, duplicate worker delivery as a consumed no-op with attempts remaining at 1 and S3
identity unchanged, and current-invocation DLQ message
`ca59a186-ac07-47fb-819a-f96427a816e0`. Post-business identity reproof passed.

Both application containers ran as `65532:65532` on `pk-stack-lab-net`, with no mounts and exact
image/task/run/claim/operation/source identity. Task definitions requested read-only rootfs,
`CapDrop: ALL`, and `no-new-privileges`; Floci 2.0.1 demonstrably did not propagate those three
controls to Docker. Evidence reported them as emulator limitations rather than claiming they were
effective.

## External judge

While the final generation was live, an owner-controlled read-only external copy of the judge and
an independent read-only control manifest invoked exactly the checkout's verifier:

```sh
python3 /private/tmp/pk-stack-judge-final-902.037z1V/verify_feature_contract.py \
  --repo /Users/noahsutter/git-projects/pk-stack-lab \
  --expected-contract-sha256 cc10d305410139155e5071bdd067dc780c2be51cbd7d404479f45e8fe3b59a04 \
  --control-manifest /private/tmp/pk-stack-judge-final-902.037z1V/control-manifest.json
```

It exited zero with:

```json
{
  "contract_sha256": "cc10d305410139155e5071bdd067dc780c2be51cbd7d404479f45e8fe3b59a04",
  "control_manifest_sha256": "05df1735d8b702c9c9a54e23eae0c90cc81aa49ac94e1e3aaa9d9ac30529c041",
  "judge_sha256": "d47418287932afbfa851593eb348d053c658fe683cd63b559cb4349c326646ab",
  "ok": true
}
```

The external judge and manifest were direct, single-link files with modes 0500 and 0400. The
judge bounded stdout, rejected any stderr, rehashed all protected files before and after, required
the exact executable-source closure, and parsed the fixed-size resource projection rather than the
internal artifact ledger.

## Exact teardown and noninterference

```sh
./labctl down --output json
```

`down` exited zero and reported four ECS tasks, four immutable image references, and every frozen
phase complete in order:

```text
aws_compute_absent
aws_data_absent
aws_definitions_cluster_absent
aws_postconditions_passed
docker_outer_absent
floci_data_absent
docker_images_absent
local_postconditions_passed
```

Independent exact-name/reference queries then found no `live-final-902` images, no Floci outer
container, no Floci ECS task container, no `pk-stack-lab-net`, and no `.lab-state`. Pre-existing
foreign image tags remained unchanged:

```text
pklab-live-r2-902-api:d8f448b8302cb827d588aabe    250c0499c7c0
pklab-live-r2-902-worker:d8f448b8302cb827d588aabe 250c0499c7c0
```

## Council and current-session status

Sol Advisor v0.6.0 supplied build-phase advice and is recorded as advisory, not acceptance.
Fable 5.1 round 1 reviewed commit `0b000d359b99f34ee5001088548ca872322e734a` at max effort and
returned eight material findings; their remediations are present in this later candidate but have
not yet received a clean Fable disposition. The real one-process interactive
`kiro-cli chat --v3 --agent pstack --model gpt-5.6-sol --effort max` fail-repair-pass campaign is
also still pending. Grok 4.6 `xhigh` runs only after clean Fable acceptance on that exact commit.
Private GitHub publication is likewise not claimed yet.
