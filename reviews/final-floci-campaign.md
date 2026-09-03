# Final immutable Floci campaign

## Decision

The `final-floci-902` campaign passed against candidate A, commit
`28b918268104cbcd19b18486dcb4134213c6351a`, tree
`72fe6177d20eea67b6580899c1134d586be987c0`. Its detached archive hashed to
`fa952d459574bd811c093af13c0771339ea49344f26f6105d6c66780b77cf90c`. This record is the
bounded, non-secret projection of raw owner-controlled evidence. It does not claim that this
evidence-only commit was itself executed.

## Environment and controls

The campaign used Docker Engine 29.7.2, Compose 5.5.0, and exact Floci image
`floci/floci:2.0.1@sha256:4e451c39c7bb88e3cd4f87e8fc0c25d5b47695a51185d521e2241fa00486e8eb`
on Docker Desktop's `desktop-linux` context. The verifier image was pre-pulled by digest before
the inventory baseline, so cleanup comparisons do not hide an unrelated pull.

Before either deployment, the caller froze an external judge and 14-path manifest. Their hashes
were:

- judge: `73e6b16865381c0475e528d5c87458081d92f213e31811395b4e2ecfad9560d7`
- control manifest: `1c59d2d16a7df0af558da86fa5feb30f64e6464e2232f5a7cbc119ea0e64137b`
- document-export contract: `fc4c32e718f7e4ea2aa0369c24f0bca25d7cfc5af8f64990caf34fdd2214605a`

The exact protected map is retained in `reviews/final-floci-control-manifest.json`.

## Command sequence

The caller used only the public lifecycle interface for the run:

```sh
./labctl doctor --output json
./labctl up --run-id final-floci-902 --acknowledge-docker-socket --output json
# Add one controlled comment to src/pk_stack_lab/runtime.py with apply_patch.
./labctl deploy --output json
./labctl status --output json
./labctl evidence --output json
# Restore runtime.py exactly to candidate A with apply_patch and verify all 14 hashes.
./labctl deploy --output json
./labctl status --output json
./labctl verify --output json
./labctl evidence --output json
/usr/bin/python3 -I -B /path/to/frozen/verify_feature_contract.py \
  --repo /path/to/detached/candidate \
  --expected-contract-sha256 fc4c32e718f7e4ea2aa0369c24f0bca25d7cfc5af8f64990caf34fdd2214605a \
  --control-manifest /path/to/frozen/control-manifest.json
./labctl down --output json
```

Both API and worker converged on two independent image/task-definition generations:

| Generation | Source digest | Image ID | API/worker revisions | Operation ID |
| --- | --- | --- | --- | --- |
| controlled marker | `bc4e31fb91605ba5b8c49d3abc5b24be647763e13a6844beb7a37868bc1d677a` | `sha256:c156b1d9e3573d43fdccfbaa87be79b544c298362c320963c17f280b48db6abf` | `:1` / `:1` | `f0c84db3f2b734f7ad576866d4be82f7` |
| restored candidate A | `5241fe8d4203672be0f5ed57ee9e2b2517919841b0632334b13a14a073727fe6` | `sha256:97d0151ea4bc6b357c6d8f5428d499997da0f06bf7d5286a350bf8a2f07186b6` | `:2` / `:2` | `ee0b785291220f882338032de8e8e423` |

The append-only artifact ledger contained the expected contiguous sequence 1–16 across exactly
those two operation IDs.

## Business proof

The bounded verifier reached the exact real ECS API task from a transient verifier container and
returned `ok: true`. It proved tenant-key partition separation; stable API idempotency with the
same export ID, duplicate marker and `COMPLETE` response, durable enqueue marker, and exactly one
attempt; exact S3 content; duplicate-worker no-op with unchanged S3 identity; a DLQ message from
the current invocation; and post-business API/worker image and task-definition identity.

The export was `e-89525bdfab9edf74`; the current-invocation DLQ message was
`85227e9d-8b28-4564-bf32-68fb24a5dfc3`. The frozen external judge independently returned
`ok: true` with all three expected control hashes.

## Cleanup and noninterference

Normal reachable teardown accounted for four ECS tasks and four campaign images, then completed
all eight ordered cleanup phases. No run manifest, Floci outer container, Floci data, dedicated
network, run task container, or run image remained.

The complete Docker image, container, network, and 18-entry foreign `pklab-*` inventories each
had identical before/after bytes. Their hashes and the machine-readable proof are retained in
`reviews/final-floci-campaign.json`.

## Limits

This proves the ECS-like application and lifecycle contract on local Floci 2.0.1. It does not
turn Floci into Fargate or exercise cloud IAM, VPC networking, cross-account behavior, or the AWS
production control plane. Floci also reported that it did not enforce requested read-only-root,
drop-all-capabilities, or no-new-privileges fields; both task processes nevertheless ran as
UID/GID 65532 with no mounts. Raw terminal, Docker, and emulator dumps remain outside Git because
they contain machine-specific metadata.
