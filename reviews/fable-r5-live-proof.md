# Fable round-5 exact-executable live proof

## Decision

The fresh `fable-r5-902` Docker-backed Floci lifecycle and owner-controlled external judge passed
against executable commit `cb2cb0905687c3e94e539333d8945c37109f6189`, tree
`c28e71a050185f19befb3832e865c4e54f2bcf03`. The run exercised the strengthened API-idempotency
contract, two deployment generations, final source identity, normal teardown, exact local
postconditions, and foreign-image noninterference. This closes `FBL-028` and `FBL-029` locally.

This record is evidence for the next immutable Fable review; it is not itself a Fable verdict.
Adding this Markdown record after the run does not change the executable/protected bytes listed
below. The next reviewer must independently compare its snapshot against those hashes rather than
trusting this disposition.

## Static gates

The executable commit passed both complete suites:

```sh
env PYTHONDONTWRITEBYTECODE=1 \
  uv run --locked --no-config --no-sync pytest -p no:cacheprovider -q
# 298 passed

(cd powers/pk-stack && env PYTHONDONTWRITEBYTECODE=1 \
  uv run --locked --no-config --no-sync pytest -p no:cacheprovider -q)
# 509 passed
```

These are the static suite results retained with this campaign. The broader pre-Fable tool gates
remain recorded separately in `docs/validation-report.md`; this live-proof record does not restate
them as newly rerun. The optional missing-`okn` warning remains a disclosed feature-map-only
limitation.

## Live command sequence

The campaign used the public lifecycle interface with run ID `fable-r5-902`:

```sh
./labctl doctor --output json
./labctl up --run-id fable-r5-902 --acknowledge-docker-socket --output json
# Add one controlled build-input marker to src/pk_stack_lab/runtime.py.
./labctl deploy --output json
# Restore src/pk_stack_lab/runtime.py byte-for-byte to executable commit cb2cb09.
./labctl deploy --output json
./labctl status --output json
./labctl verify --output json
./labctl evidence --output json
```

Both API and worker services converged on each generation:

| Generation | Source digest | Docker image ID | API/worker revisions | Operation ID |
| --- | --- | --- | --- | --- |
| controlled marker | `21d72b651fe61d76f14cb4c2e427755a3ffefe4704da6c8397311283b97c1d72` | `sha256:43545de6babede31a7d1eeaa5dc93b2578145338c35fbf9c9d582010c0bc5f69` | `:1` / `:1` | `3ce59f0bbf08bd17c5676b915a5f0f3a` |
| restored executable commit | `5241fe8d4203672be0f5ed57ee9e2b2517919841b0632334b13a14a073727fe6` | `sha256:8510c0cf5e34ce1c81869249a893779b8d9a9992a9ad322aec59cdf63c7d1377` | `:2` / `:2` | `d0e2fe295881efa76e36fc025c1b4f87` |

The restored runtime SHA-256 was
`83a05fcc163e8f72b418cb72834967e8d274bebfe872d4608ad393c18469cfe9`, matching the executable
commit and the frozen protected-file manifest. `labctl evidence` reported the final source digest
explicitly at the top level as
`5241fe8d4203672be0f5ed57ee9e2b2517919841b0632334b13a14a073727fe6`.

The strengthened live verifier returned `ok: true` for export `e-80e481584565639f` and
current-invocation DLQ message `df56c9f6-c725-486a-8ce3-d42ec91af49d`. It passed the duplicate
response marker and accepted-status checks, stable export identity, exact durable idempotency key,
durable enqueue confirmation, exactly-one attempt count, tenant-key partition separation, exact S3
result, duplicate worker no-op, and post-business deployment-identity reproof.

## Frozen external judge

Before the controlled build-input marker, the 14-path control manifest and judge were frozen under
`/private/tmp/pk-stack-judge-fable-r5.dg6p1m/controls`. The judge was owner read/execute-only mode
0500; the manifest was owner read-only mode 0400. After restoring the executable commit and running
the direct verifier, the invocation was:

```sh
/usr/bin/python3 -I -B \
  /private/tmp/pk-stack-judge-fable-r5.dg6p1m/controls/verify_feature_contract.py \
  --repo /Users/noahsutter/git-projects/pk-stack-lab \
  --expected-contract-sha256 f8678410245c3f62b186a88535432f7f97d2f02687d1ea3685e30f526242fc48 \
  --control-manifest \
    /private/tmp/pk-stack-judge-fable-r5.dg6p1m/controls/control-manifest.json
```

It exited zero with no reported contract failure:

```json
{
  "contract_sha256": "f8678410245c3f62b186a88535432f7f97d2f02687d1ea3685e30f526242fc48",
  "control_manifest_sha256": "b7b7e9176d435242738abfb9ea31b4faed4573cd68448454b5d964235629dd0d",
  "judge_sha256": "73e6b16865381c0475e528d5c87458081d92f213e31811395b4e2ecfad9560d7",
  "ok": true
}
```

The frozen manifest contained this exact protected map:

| Protected path | SHA-256 |
| --- | --- |
| `Dockerfile` | `47c93bfcd953e7fe86e646d8716dc7c24a78833066e31a41467d347544c3eb18` |
| `Wiki/features/document-export.md` | `f8678410245c3f62b186a88535432f7f97d2f02687d1ea3685e30f526242fc48` |
| `compose.yaml` | `ffc0ae8024ceb2487f13efc4ee71a0c5c02f89e800e5657bb65783892bd45e38` |
| `judge/verify_feature_contract.py` | `73e6b16865381c0475e528d5c87458081d92f213e31811395b4e2ecfad9560d7` |
| `labctl` | `46bf7cca6cfbf7087500fb2cf03b2b16aed6cb139f37bcdde6138a0df6817fe1` |
| `projectctl` | `93f4462111b4a72c6c4ea5a402d81ff09d621638ae3421b20d7a86b2fd1dbde6` |
| `pyproject.toml` | `63deb2783b7d50945fefba4cbe7fd19eff01e6f044801d13476ecca67793bcae` |
| `requirements-runtime.txt` | `e73780d0b36142977c667a9082ba1bbc5424001e87b2f734e24d84c25e2bcebe` |
| `src/pk_stack_lab/__init__.py` | `f001ea670f453bdb2ce26ce7df9aff77ca260ee74675b292803d1a3a556eab16` |
| `src/pk_stack_lab/aws.py` | `dbfdcc821c66026267d9ce97a97d12c5e6b2f6f1c6716089649abd03559ce422` |
| `src/pk_stack_lab/cli.py` | `9ebefe70c21ddb09ca955e239e0f63adf247c62ad46079f0400b98d5f39b41c1` |
| `src/pk_stack_lab/config.py` | `f93542dfa2dba8f04b3c05691a245f2be25c4cac5e56ab68f798606ef47929e0` |
| `src/pk_stack_lab/runtime.py` | `83a05fcc163e8f72b418cb72834967e8d274bebfe872d4608ad393c18469cfe9` |
| `uv.lock` | `49c65a6bfc5b6c9c01073feafed8e4cf21c60d222df34e071b8f92c45a9d6dbd` |

The manifest file itself hashed to
`b7b7e9176d435242738abfb9ea31b4faed4573cd68448454b5d964235629dd0d`.
The judge revalidated the fixed executable-source closure and the strengthened bounded verifier
payload against those controls.

## Teardown and noninterference

Normal reachable teardown used the public command:

```sh
./labctl down --output json
```

It accounted for four ECS tasks and four immutable image references and completed all eight frozen
phases in order:

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

Postcondition checks found no run manifest, Floci outer container, dedicated lab network,
claim-bound task container, or `fable-r5-902` generation image. The complete before/after foreign
image inventory was unchanged.

## Scope and remaining limits

This run closes the repository-fixable idempotency and exact-executable live-proof gaps. It does
not turn Floci into Fargate, prove AWS cloud IAM/network behavior, add egress isolation, or change
the documented Floci 2.0.1 security-field and metadata propagation limitations. It also does not
replace the earlier one-process Kiro campaign: that remains separately scoped evidence of ordinary
interactive `kiro-cli chat --v3` current-session fail-repair-pass behavior, with its disclosed raw
transcript and process-metadata limits. Final acceptance still requires Fable to review an
immutable snapshot containing this record; Grok remains the post-Fable sweeper.
