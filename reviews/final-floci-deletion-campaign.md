# Final Floci exact-deletion campaign

## Decision

The `final-floci-903` campaign passed against commit
`8806fa607b991d8e3ca9d004f2724412596f715d`, tree
`bd0488dc2b184c39c0a6c538d5f2d2ebf73375cf`. The detached Git archive embedded that exact
commit and hashed to `cc14e34967b9132f985bdc99da92f4ba2b2e713b8077894a3b8b0b7db8a76cfb`.
All 390 tracked files still matched the archive after the campaign. This closes FBL-042 for the
exact claim-bound outer-container/network deletion path; it does not claim this evidence-only
commit was itself executed.

## Frozen controls

The caller copied the 14-path control manifest and judge outside the detached candidate before
starting the lab, made both direct owner-controlled files read-only, and verified every protected
hash. The key hashes were:

- control manifest: `d35c86b45b640d817f57b7bfd5bc61c36b42e7cd4d4bdcfc32c6bd64f6d48aa7`
- external judge: `73e6b16865381c0475e528d5c87458081d92f213e31811395b4e2ecfad9560d7`
- document-export contract: `37203aba7f6404e0a820fcacbca770857070c77a6e161d9622d9011e85c80d80`
- lifecycle source: `5e85a0d8a39d8963b36aa3e59b8ae0c43482d53b34b865a0e828c47834d7710b`

The environment was Docker Engine 29.7.2, Compose 5.5.0, and Floci
`floci/floci:2.0.1@sha256:4e451c39c7bb88e3cd4f87e8fc0c25d5b47695a51185d521e2241fa00486e8eb`
on Docker Desktop's `desktop-linux` context.

## Public lifecycle

The exact detached candidate ran this sequence successfully:

```sh
./labctl doctor --output json
./labctl up --run-id final-floci-903 --acknowledge-docker-socket --output json
./labctl deploy --output json
./labctl status --output json
./labctl verify --output json
./labctl evidence --output json
/usr/bin/python3 -I -B /path/to/frozen/verify_feature_contract.py \
  --repo /path/to/detached/candidate \
  --expected-contract-sha256 37203aba7f6404e0a820fcacbca770857070c77a6e161d9622d9011e85c80d80 \
  --control-manifest /path/to/frozen/control-manifest.json
./labctl down --output json
```

The single deploy produced source digest
`5241fe8d4203672be0f5ed57ee9e2b2517919841b0632334b13a14a073727fe6`, image
`sha256:a8bcf12e649d324f60a25a7f402f27fe22e3b1125ca63d1266004f19c79cad8b`, and API/worker
task-definition revision `:1`. Both services and both exact tasks were running before verification.
The append-only artifact ledger contained one operation and the contiguous sequence 1–8.

## Application and independent proof

The built-in verifier returned `ok: true` over bounded HTTP to the exact real ECS API task. It
proved tenant partition separation; stable API idempotency with the same export ID, durable row,
enqueue marker, and exactly one attempt; exact S3 content; duplicate-worker no-op with unchanged
S3 identity; a current-invocation DLQ message; and post-business image/task identity.

The export was `e-74216228444e90e7`, and the DLQ message was
`2df342e5-ad70-4e1a-805e-666844a7e4ce`. The separately frozen judge then repeated the business
proof while the same deployment remained live and independently returned `ok: true` with all
three frozen hashes.

## Exact deletion and foreign preservation

Before `up`, the caller created a hardened, network-isolated foreign sentinel named
`pklab-final-floci-903-foreign-sentinel`. It intentionally carried
`com.docker.compose.project=pk-stack-lab` but no PK-Stack ownership claim, directly exercising the
project-label collision that whole-project Compose teardown could mishandle. Its container ID was
`7af98305fffde923cab3431371e4aebfdcc91749487509523f5f24bf01420ff6`; its bounded inspect hash
before and after `labctl down` was identically
`a34f1613263d6a8a4c0647804b23baaf2887c1cfefd67dd238feaa7e24824381`, and it was still running.

Normal reachable teardown reported two ECS tasks and two campaign image tags, and completed all
eight ordered phases:

1. `aws_compute_absent`
2. `aws_data_absent`
3. `aws_definitions_cluster_absent`
4. `aws_postconditions_passed`
5. `docker_outer_absent`
6. `floci_data_absent`
7. `docker_images_absent`
8. `local_postconditions_passed`

Independent postconditions found no state manifest, Floci data, exact Floci outer container,
dedicated network, current-claim container, exact API/worker task container, or exact run image
tag. The full sorted static image, container, and network inventories, plus the eight-entry foreign
`pklab-*` projection, matched byte-for-byte across the campaign.

Only after that proof did the caller re-resolve the sentinel name to its recorded immutable ID and
remove that exact container. A second inventory comparison matched the pre-sentinel host state
byte-for-byte for images, containers, networks, and the foreign `pklab-*` projection. No other
Docker object was removed by the harness.

## Limits

This proves the ECS-like application and exact-deletion contracts on local Floci 2.0.1. It does
not turn Floci into Fargate or exercise cloud IAM, VPC networking, cross-account behavior, or the
AWS production control plane. Floci did not enforce three requested task hardening fields, though
both task processes ran as UID/GID 65532 with no mounts. The sentinel used Docker's `none` network;
the fail-closed response to a foreign attachment on the dedicated network was not exercised live
in this campaign. Raw terminal, Docker, and emulator outputs remain owner-only temporary evidence;
the JSON companion is the bounded non-secret projection.
