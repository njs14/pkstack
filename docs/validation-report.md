# Validation report

## Bootstrap evidence

Reviewed source command:

```sh
sed -n '1,280p' /Users/noahsutter/git-projects/codex/skills/setup-pstack/scripts/setup_pstack.py
```

Dry-run command (exit 0):

```sh
python3 /Users/noahsutter/git-projects/codex/skills/setup-pstack/scripts/setup_pstack.py \
  --root /Users/noahsutter/git-projects/pk-stack-lab --dry-run --output json
```

The JSON reported `ok: true`, no conflicts, and only repository-local `.pstack`, `.kiro`,
`Wiki/features`, `projectctl`, and `.gitignore` additions. Apply command (exit 0):

```sh
python3 /Users/noahsutter/git-projects/codex/skills/setup-pstack/scripts/setup_pstack.py \
  --root /Users/noahsutter/git-projects/pk-stack-lab --output json
```

The apply JSON reported `ok: true`, no conflicts, and the same scoped additions. The frozen
source Power was inspected only and was not modified.

## Historical runtime validation: ci-012 (superseded)

The final static gates all exited 0 after the propagation, parser, proof, and cleanup changes:

```sh
uv lock --check
uv run ruff check .
uv run pytest
git diff --check
```

This historical section predates the mandatory security enforcement checks and is not a final
acceptance claim. `uv lock --check` reported `Resolved 15 packages`; Ruff reported `All checks passed!`; pytest
collected and passed **54** tests; and `git diff --check` was silent.

This clean cold lifecycle used run `ci-012` (all commands exited 0):

```sh
./labctl doctor --output json
./labctl up --run-id ci-012 --output json
./labctl deploy --output json
./labctl status --output json
./labctl verify --output json
.pstack/bin/projectctl doctor --output json
.pstack/bin/projectctl feature validate --output json
.pstack/bin/projectctl feature verify document-export --output json
./labctl evidence --output json
```

Doctor confirmed Docker server `29.7.2`, Compose `5.4.0`, context socket
`unix:///Users/noahsutter/.docker/run/docker.sock`, `http://127.0.0.1:4566`, task endpoint
`http://floci:4566`, `us-east-1`, and the exact immutable Floci digest. The run created only
`pklab-ci-012-*` resources. Deploy registered API and worker revisions `:1`; status and evidence
reported one RUNNING API task `a86caa7127e14d47b89038c351a6ac8a` and one RUNNING worker task
`25655711bf364f5b891f98a79765f1f4`.

Both service creation and repeat-update code request `propagateTags=SERVICE`. The resulting
Floci `DescribeTasks(include=['TAGS'])` task dictionaries omitted `tags`, while
`ListTagsForResource` returned `{'tags': []}` for each task. The current-run proof therefore
retains its exact service-tag plus task ARN/family/container chain; it does not fake unavailable
task tags.

Manual verify returned `ok: true` for fresh export `e-ae7ca79dc29bdc10`, terminal `COMPLETE`,
object `exports/tenant-a/e-ae7ca79dc29bdc10.json`, cross-tenant isolation, duplicate API POST,
worker duplicate delivery no-op (`attempts: 1`, unchanged S3 identity), and the invocation's
own DLQ message `09329d1f-66e4-41e7-b7e1-9d281fafb617`. The stored feature verifier independently
called only `./labctl verify --output json` and passed with distinct fresh export
`e-99b0fdd4fba7aac5`, object `exports/tenant-a/e-99b0fdd4fba7aac5.json`, and DLQ message
`48d2ce4d-0b9d-4f4c-a651-c934cdac2577`. Projectctl doctor reported 39 pass/0 fail (one expected
optional `okn` warning); feature validation reported one ready contract with no errors or
warnings. The repository-owned independent judge also passed:

```sh
uv run python judge/verify_feature_contract.py --repo /Users/noahsutter/git-projects/pk-stack-lab \
  --expected-contract-sha256 8793192a8d316c67e9b0633f23388b87913cf0867c0a4957444eb63529a55098
```

It returned the same contract hash and `ok: true`.

Live mount inspection before teardown showed exactly two Floci bind mounts—the discovered Docker
socket to `/var/run/docker.sock` and repository-local `.lab-state/floci-data` to `/app/data`—and
`[]` for both real task containers. Evidence reported the exact Floci ECS label/resource-ID chain,
dedicated network, images, task-definition revisions, allowed Floci labels, and manifest hash
`82f0d0f3db661a19665ae71393904c963751c35edc3f70c15a79b03b6df5709c`, without secrets.

Teardown and independent checks all exited 0:

```sh
./labctl down --output json
docker ps -a --filter label=floci=true --format '{{.Names}} {{.Labels}}'
docker ps -a --filter name=^pk-stack-lab-floci$ --format '{{.Names}}'
docker network ls --filter name=^pk-stack-lab-net$ --format '{{.Name}}'
docker image ls --format '{{.Repository}}:{{.Tag}}'
docker volume ls --format '{{.Name}}'
```

`down` returned zero owned ECS tasks, Floci container, network, local data, and current-run
images. The container and network queries returned no output. The exact ci-012 image tags were
absent afterward while the pre-existing image tags remained untouched. The volume inventory after
teardown was the same seven pre-teardown IDs (`03c607…f37f`, `7a4036…ad48`, `37b268…71a`,
`37fb87…78b0`, `51ccd8…93c8`, `083df5…3978`, `fcfd30…f002`), so ci-012 created no anonymous
lab volume. `.lab-state` was absent after cleanup. Floci 2.0.1's missing task-tag response after
explicit propagation is the documented emulator limitation; this historical proof does not manufacture
task tags.

## Floci security-limit validation: live-r3-902

This runtime attempt stopped under the then-mandatory fail-closed security check:

```sh
./labctl up --run-id live-r3-902 --acknowledge-docker-socket --output json  # exit 0
./labctl deploy --output json                                                # exit 0
./labctl evidence --output json                                              # exit 1
./labctl down --output json                                                  # exit 0
```

The API and worker definitions requested user `65532:65532`, read-only root filesystem,
`CapDrop: ALL`, and `no-new-privileges`. Docker inspected both exact current Floci task
containers as `user=65532:65532 readonly=false capdrop=null security=null mounts=[]`.
Evidence therefore returned `real ECS task container did not enforce required security fields`.
An `internal: true` network experiment also left the Floci container healthy while deploy failed
with `Could not connect to the endpoint URL: "http://127.0.0.1:4566/"`. The post-down read-only
checks found no Floci container, `pk-stack-lab-net`, `pklab-live-r3-902-*` tag, or `.lab-state`.
This is an accepted Floci-emulator limitation, not evidence that those three controls are
effective. The release bar still requires non-root application tasks, no task mounts or Docker
socket, exact identity, dedicated networking, and a separately hardened verifier.

## Post-stop local validation

No further Floci lifecycle was launched after the security hard stop. Local corrections added
the verifier's explicit Python entrypoint and exact-name `finally` cleanup, broad ordinary-
exception JSON rendering, state-owner validation, and expanded judge protected closure. The
latest pre-acceptance static suite passed with `uv lock --check`, `uv run --locked --no-config --no-sync
ruff check .`, and `uv run --locked --no-config --no-sync pytest` (**63 passed**). The real
vendored controller also passed `./projectctl doctor --output json` (39 pass, 0 fail, one
expected `okn is unavailable` warning), `feature validate`, and `knowledge validate`; broad
OKF validation was explicitly not run because `okn` is unavailable. This root test suite is
distinct from the managed controller suite.
