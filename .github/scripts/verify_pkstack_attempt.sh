#!/usr/bin/env bash
set -euo pipefail
umask 077

: "${BASE_SHA:?BASE_SHA is required}"
: "${DETECTOR_PATH:?DETECTOR_PATH is required}"
: "${FEEDBACK_PATH:?FEEDBACK_PATH is required}"
: "${GOAL_STATUS_PATH:?GOAL_STATUS_PATH is required}"
: "${GUARD_PATH:?GUARD_PATH is required}"
: "${TRUSTED_PROJECTCTL_ROOT:?TRUSTED_PROJECTCTL_ROOT is required}"
: "${ATTEMPT_NUMBER:?ATTEMPT_NUMBER is required}"
: "${GITHUB_OUTPUT:?GITHUB_OUTPUT is required}"
: "${READONLY_GITHUB_TOKEN:?READONLY_GITHUB_TOKEN is required}"
: "${KIRO_BIN_DIR:?KIRO_BIN_DIR is required}"
: "${KIRO_HOME:?KIRO_HOME is required}"
: "${KIRO_USER_HOME:?KIRO_USER_HOME is required}"
: "${GIT_BOUNDARY_STATE:?GIT_BOUNDARY_STATE is required}"
: "${CONTROL_PLAN_PATH:?CONTROL_PLAN_PATH is required}"
if [[ ! "$ATTEMPT_NUMBER" =~ ^[1-2]$ ]]; then
  echo "ATTEMPT_NUMBER must be an integer from 1 through 2" >&2
  exit 2
fi

project_root=$(pwd -P)
verification_log="${RUNNER_TEMP:?RUNNER_TEMP is required}/pkstack-verify-${ATTEMPT_NUMBER}.log"
trusted_python="$TRUSTED_PROJECTCTL_ROOT/.venv/bin/python"

trusted_projectctl() {
  PYTHONPATH="$TRUSTED_PROJECTCTL_ROOT/src" \
    "$trusted_python" -B -X pycache_prefix=/dev/null -m pkstack "$@"
}

# Invoked as a callback by capture_verification.
# shellcheck disable=SC2329
trusted_projectctl_network() {
  GITHUB_TOKEN="$readonly_token" \
    PYTHONPATH="$TRUSTED_PROJECTCTL_ROOT/src" \
    "$trusted_python" -B -X pycache_prefix=/dev/null -m pkstack "$@"
}

capture_verification() {
  local output_path=$1
  shift
  local command_rc=0
  "$@" >"$output_path" || command_rc=$?
  printf '%s' "$readonly_token" | python3 "$feedback_helper" \
    --capture --log "$output_path" --detail "$stage_detail" --target "$FEEDBACK_PATH" \
    --attempt "$ATTEMPT_NUMBER" --status "$evidence_error" || return 1
  return "$command_rc"
}

trusted_accept_with_feedback() {
  local output_path=$1
  shift
  capture_verification "$output_path" trusted_projectctl_network upstream accept "$@"
}

# Git subprocesses launched directly or by immutable controller code inherit
# the same non-executable configuration boundary. The guard also supplies
# these settings itself, so this remains defense in depth across processes.
export GIT_CONFIG_NOSYSTEM=1
export GIT_CONFIG_SYSTEM=/dev/null
export GIT_CONFIG_GLOBAL=/dev/null
export GIT_ATTR_NOSYSTEM=1
export GIT_EXTERNAL_DIFF=
export GIT_NO_REPLACE_OBJECTS=1
export GIT_PAGER=cat
export GIT_TERMINAL_PROMPT=0
export GIT_CONFIG_COUNT=4
export GIT_CONFIG_KEY_0=core.hooksPath
export GIT_CONFIG_VALUE_0=/dev/null
export GIT_CONFIG_KEY_1=core.fsmonitor
export GIT_CONFIG_VALUE_1=false
export GIT_CONFIG_KEY_2=diff.external
export GIT_CONFIG_VALUE_2=
export GIT_CONFIG_KEY_3=core.attributesFile
export GIT_CONFIG_VALUE_3=/dev/null

# The candidate checkout's entire Git control plane was model-visible. All
# finalizer/controller Git calls therefore use a detached, prepare-time Git
# directory and a fresh base index outside that checkout. New blobs are written
# only to the external object directory; the original object store is read-only
# alternate input whose object identities Git verifies cryptographically.
export GIT_DIR="$GIT_BOUNDARY_STATE/git"
export GIT_COMMON_DIR="$GIT_BOUNDARY_STATE/git"
export GIT_WORK_TREE="$project_root"
export GIT_INDEX_FILE="$GIT_BOUNDARY_STATE/index"
export GIT_OBJECT_DIRECTORY="$GIT_BOUNDARY_STATE/objects"
export GIT_ALTERNATE_OBJECT_DIRECTORIES="$project_root/.git/objects"

without_finalizer_git_metadata() {
  # The immutable test suites create their own temporary repositories. Do not
  # redirect those independent Git fixtures into the checkout finalizer.
  env \
    -u GIT_DIR \
    -u GIT_COMMON_DIR \
    -u GIT_WORK_TREE \
    -u GIT_INDEX_FILE \
    -u GIT_OBJECT_DIRECTORY \
    -u GIT_ALTERNATE_OBJECT_DIRECTORIES \
    -u GIT_EXTERNAL_DIFF \
    -u GIT_CONFIG_COUNT \
    -u GIT_CONFIG_KEY_0 \
    -u GIT_CONFIG_VALUE_0 \
    -u GIT_CONFIG_KEY_1 \
    -u GIT_CONFIG_VALUE_1 \
    -u GIT_CONFIG_KEY_2 \
    -u GIT_CONFIG_VALUE_2 \
    -u GIT_CONFIG_KEY_3 \
    -u GIT_CONFIG_VALUE_3 \
    "$@"
}

trusted_git() {
  git \
    -c core.hooksPath=/dev/null \
    -c core.fsmonitor=false \
    -c diff.external= \
    -c core.attributesFile=/dev/null \
    "$@"
}

# This closes the key-bearing projection before any candidate code is run.
python3 "$GUARD_PATH" --root "$project_root" close-attempt \
  --base "$BASE_SHA" \
  --git-state "$GIT_BOUNDARY_STATE"
test -z "${KIRO_API_KEY:-}"
python3 - "$RUNNER_TEMP" "$KIRO_BIN_DIR" "$KIRO_HOME" "$KIRO_USER_HOME" <<'PY'
from __future__ import annotations

import shutil
import sys
from pathlib import Path

runner = Path(sys.argv[1])
if runner.is_symlink() or not runner.is_dir():
    raise SystemExit("refusing invalid runner temp directory")
temporary = runner.resolve()
binary, kiro_home, user_home = (Path(raw) for raw in sys.argv[2:])
if binary == user_home or kiro_home != user_home / ".kiro":
    raise SystemExit("refusing invalid Kiro runtime home layout")
for target in (binary, user_home):
    if target.is_symlink():
        raise SystemExit(f"refusing symlinked Kiro runtime path: {target}")
    resolved = target.resolve()
    if (
        target.parent != runner
        or resolved.parent != temporary
        or not resolved.name.startswith("kiro-")
    ):
        raise SystemExit(f"refusing Kiro runtime path outside runner temp: {target}")
    if resolved.exists() and not resolved.is_dir():
        raise SystemExit(f"Kiro runtime path is not a directory: {target}")
if kiro_home.is_symlink() or (kiro_home.exists() and not kiro_home.is_dir()):
    raise SystemExit("refusing invalid nested Kiro home")
if kiro_home.resolve() != user_home.resolve() / ".kiro":
    raise SystemExit("refusing Kiro home outside isolated user home")
# Validate the whole layout before deleting anything; the user parent owns .kiro.
for target in (binary, user_home):
    if target.exists():
        shutil.rmtree(target)
PY
unset KIRO_BIN_DIR KIRO_HOME KIRO_USER_HOME
python3 "$GUARD_PATH" --root "$project_root" validate-trusted-snapshot \
  --base "$BASE_SHA" \
  --trusted-root "${TRUSTED_ROOT:?TRUSTED_ROOT is required}"
readonly_token=$READONLY_GITHUB_TOKEN
unset READONLY_GITHUB_TOKEN

diagnostics_root="$RUNNER_TEMP/pkstack-verification-results"
test ! -L "$diagnostics_root"
mkdir -p "$diagnostics_root"
stage_path="$diagnostics_root/attempt-${ATTEMPT_NUMBER}.stage"
test ! -e "$stage_path" && test ! -L "$stage_path"
reason_path="$diagnostics_root/attempt-${ATTEMPT_NUMBER}.reason"
test ! -e "$reason_path" && test ! -L "$reason_path"
stage_detail="$RUNNER_TEMP/pkstack-stage-detail-${ATTEMPT_NUMBER}.log"
feedback_status="$RUNNER_TEMP/pkstack-feedback-status-${ATTEMPT_NUMBER}.json"
evidence_error="$RUNNER_TEMP/pkstack-evidence-error-${ATTEMPT_NUMBER}.json"
stage_offset="$RUNNER_TEMP/pkstack-stage-offset-${ATTEMPT_NUMBER}"
feedback_helper="$(dirname -- "${BASH_SOURCE[0]}")/pkstack_verification_feedback.py"
test ! -e "$evidence_error" && test ! -L "$evidence_error"
: >"$stage_detail"
# Invoked by the EXIT trap.
# shellcheck disable=SC2329
cleanup_verification_evidence() {
  rm -f -- "$verification_log" "$stage_detail" "$feedback_status" "$evidence_error" "$stage_offset" \
    "$RUNNER_TEMP/pkstack-dry-run-${ATTEMPT_NUMBER}.json" \
    "$RUNNER_TEMP/pkstack-accept-preview-${ATTEMPT_NUMBER}.json" \
    "$RUNNER_TEMP/pkstack-accept-${ATTEMPT_NUMBER}.json" \
    "$RUNNER_TEMP/pkstack-post-accept-${ATTEMPT_NUMBER}.json"
}
trap "cleanup_verification_evidence" EXIT
mark_stage() {
  : >"$stage_detail"
  wc -c <"$verification_log" >"$stage_offset"
  printf '%s\n' "$1" >"$stage_path"
}

set +e
(
  set -euo pipefail

  mark_stage detector
  detector_validation=$(python3 "$GUARD_PATH" validate-detector --detector "$DETECTOR_PATH" | tee "$stage_detail")
  drift_count=$(jq -er '.drift_count' <<<"$detector_validation")
  selected_source_id=$(jq -er '.selected_source_id // ""' "$CONTROL_PLAN_PATH")
  expected_head=$(jq -er '.expected_head // ""' "$CONTROL_PLAN_PATH")

  # The base-commit controller performs the only generated-file update. This
  # must precede proposal preview because acceptance requires generated parity.
  mark_stage setup
  trusted_projectctl setup \
    --root . \
    --power-root powers/pkstack \
    --update-managed \
    --output json
  mark_stage feature-contract
  trusted_projectctl feature validate --output json
  mark_stage generated-parity
  capture_verification "$RUNNER_TEMP/pkstack-dry-run-${ATTEMPT_NUMBER}.json" \
    trusted_projectctl setup \
    --root . \
    --power-root powers/pkstack \
    --dry-run \
    --update-managed \
    --output json
  jq -e '
    .ok == true
    and (.conflicts | length) == 0
    and (.created | length) == 0
    and (.updated | length) == 0
    and (.pending_updates | length) == 0
    and (.stale_managed | length) == 0
  ' "$RUNNER_TEMP/pkstack-dry-run-${ATTEMPT_NUMBER}.json"

  if (( drift_count > 0 )); then
    mark_stage proposal
    if proposal_validation=$(python3 "$GUARD_PATH" validate-proposal \
      --detector "$DETECTOR_PATH" \
      --proposal .pkstack-maintenance/proposal.json \
      --selected-source-id "$selected_source_id" | tee "$stage_detail"); then
      if ! jq -e \
      --arg source_id "$selected_source_id" \
      --arg expected_head "$expected_head" \
      '.ok == true and .source_id == $source_id and .expected_head == $expected_head' \
      <<<"$proposal_validation"; then
        printf '%s\n' proposal-control-mismatch >"$reason_path"
        printf '%s\n' "Proposal validation failed: proposal-control-mismatch"
        exit 1
      fi
    else
      proposal_reason=$(jq -er '.reason | select(type == "string")' <<<"$proposal_validation") \
        || proposal_reason=proposal-invalid
      printf '%s\n' "$proposal_reason" >"$reason_path"
      # The next repair reads this private log, not the retained public report.
      printf 'Proposal validation failed: %s\n' "$proposal_reason"
      exit 1
    fi
    mark_stage accept-preview
    trusted_accept_with_feedback "$RUNNER_TEMP/pkstack-accept-preview-${ATTEMPT_NUMBER}.json" \
      --manifest maintenance/upstreams.json \
      --power-root powers/pkstack \
      --proposal .pkstack-maintenance/proposal.json \
      --expected-head "$expected_head" \
      --dry-run \
      --output json
  else
    [[ "$drift_count" == "0" ]]
    test ! -e .pkstack-maintenance/proposal.json
  fi

  # Only immutable base code is executable here. The candidate is constrained
  # to Markdown/JSON data, Kiro runtime state is gone, and no token is exported.
  mark_stage policy-tests
  without_finalizer_git_metadata python3 .github/scripts/test_pkstack_maintenance_guard.py
  mark_stage power-tests
  (
    unset GIT_DIR GIT_COMMON_DIR GIT_WORK_TREE GIT_INDEX_FILE
    unset GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES
    unset GIT_EXTERNAL_DIFF GIT_CONFIG_COUNT
    unset GIT_CONFIG_KEY_0 GIT_CONFIG_VALUE_0 GIT_CONFIG_KEY_1 GIT_CONFIG_VALUE_1
    unset GIT_CONFIG_KEY_2 GIT_CONFIG_VALUE_2 GIT_CONFIG_KEY_3 GIT_CONFIG_VALUE_3
    uv run --frozen --project . python -B .github/scripts/pkstack_python_static.py
    uv run --frozen --project . pytest -q
  )

  # Commit the reviewed transition only after every pre-pin gate passes. A later
  # failure is retryable because prepare-attempt restores both pin and ledger
  # from BASE_SHA before asking Kiro for a fresh proposal.
  if (( drift_count > 0 )); then
    mark_stage accept
    trusted_accept_with_feedback "$RUNNER_TEMP/pkstack-accept-${ATTEMPT_NUMBER}.json" \
      --manifest maintenance/upstreams.json \
      --power-root powers/pkstack \
      --proposal .pkstack-maintenance/proposal.json \
      --expected-head "$expected_head" \
      --output json
    jq -e \
      --arg source_id "$selected_source_id" \
      --arg expected_head "$expected_head" \
      '.ok == true and .accepted == true and .source_id == $source_id
       and .expected_head == $expected_head' \
      "$RUNNER_TEMP/pkstack-accept-${ATTEMPT_NUMBER}.json"
  fi
  test ! -e .pkstack-maintenance
  # The owner-only, ignored accept lock is intentionally persistent. Only the
  # proposal/journal context is transactional and must be consumed.

  mark_stage post-accept
  trusted_projectctl setup \
    --root . \
    --power-root powers/pkstack \
    --update-managed \
    --output json
  # The trusted checker validates candidate data after final regeneration. Its
  # hash diagnostics go to the private repair log; it never rewrites coverage.
  PYTHONPATH="$TRUSTED_PROJECTCTL_ROOT/src" \
    "$trusted_python" -B "$(dirname "$GUARD_PATH")/pkstack_knowledge_coverage.py" \
    --repo-root "$project_root" --base "$BASE_SHA"
  python3 "$GUARD_PATH" --root "$project_root" boundary \
    --base "$BASE_SHA" \
    --scope final \
    --stage
  post_accept_detector="$RUNNER_TEMP/pkstack-post-accept-${ATTEMPT_NUMBER}.json"
  set +e
  capture_verification "$post_accept_detector" trusted_projectctl_network upstream check \
    --manifest maintenance/upstreams.json \
    --power-root powers/pkstack \
    --output json
  post_accept_rc=$?
  set -e
  post_accept_validation=$(
    python3 "$GUARD_PATH" validate-detector --detector "$post_accept_detector"
  )
  remaining_drift_count=$(jq -er '.drift_count' <<<"$post_accept_validation")
  if (( remaining_drift_count == 0 )); then
    [[ "$post_accept_rc" == "0" ]]
  else
    [[ "$post_accept_rc" != "0" ]]
  fi
  if (( drift_count > 0 )); then
    python3 "$GUARD_PATH" --root "$project_root" validate-serialized-acceptance \
      --base "$BASE_SHA" \
      --before-detector "$DETECTOR_PATH" \
      --after-detector "$post_accept_detector" \
      --selected-source-id "$selected_source_id"
  else
    [[ "$remaining_drift_count" == "0" ]]
  fi
  mark_stage goal
  GITHUB_TOKEN="$readonly_token" trusted_projectctl goal verify --output json
  capture_verification "$GOAL_STATUS_PATH" trusted_projectctl goal status --output json
  jq -e '
    .ok == true
    and .goal.status == "passed"
    and .goal.max_attempts == 3
    and (.goal.attempt_count >= 2 and .goal.attempt_count <= 3)
  ' "$GOAL_STATUS_PATH"

  mark_stage final-boundary
  python3 "$GUARD_PATH" --root "$project_root" boundary \
    --base "$BASE_SHA" \
    --scope final \
    --stage
  test -z "$(trusted_git diff --no-ext-diff --no-textconv --name-only)"
  test -z "$(trusted_git ls-files --others --exclude-standard)"
  mark_stage complete
) >"$verification_log" 2>&1
verification_rc=$?
set -e
stage_log_end=$(wc -c <"$verification_log")
if [[ -e "$evidence_error" ]]; then verification_rc=1; fi

finalizer_rc=0
if [[ "$verification_rc" -ne 0 ]]; then
  set +e
  python3 "$GUARD_PATH" --root "$project_root" finalize-git-state \
    --base "$BASE_SHA" \
    --git-state "$GIT_BOUNDARY_STATE" >>"$verification_log" 2>&1
  finalizer_rc=$?
  set -e
fi

feedback_rc=0
if [[ -e "$evidence_error" ]]; then
  cp -- "$evidence_error" "$feedback_status"
  feedback_rc=1
elif [[ "$verification_rc" -ne 0 && "$finalizer_rc" -eq 0 ]]; then
  printf '%s' "$readonly_token" | python3 "$feedback_helper" \
    --log "$verification_log" --detail "$stage_detail" --target "$FEEDBACK_PATH" \
    --attempt "$ATTEMPT_NUMBER" --status "$feedback_status" \
    --stage-start "$(cat "$stage_offset")" --stage-end "$stage_log_end" || feedback_rc=$?
fi
readonly_token=

# Actions retains this fixed-field stdout; never publish raw verifier output.
python3 - "$stage_path" "$ATTEMPT_NUMBER" "$verification_rc" "$finalizer_rc" \
  "$BASE_SHA" "${GITHUB_RUN_ID:?GITHUB_RUN_ID is required}" "$reason_path" "$RUNNER_TEMP" "$feedback_status" "$feedback_rc" <<'PY'
import json
import re
import sys
from pathlib import Path

stage_file = Path(sys.argv[1])
stage = stage_file.read_text(encoding="ascii").strip()
allowed = {
    "detector",
    "setup",
    "feature-contract",
    "generated-parity",
    "proposal",
    "accept-preview",
    "policy-tests",
    "power-tests",
    "accept",
    "post-accept",
    "goal",
    "final-boundary",
    "complete",
}
attempt, exit_code, cleanup_exit = map(int, sys.argv[2:5])
base_sha, run_id = sys.argv[5:7]
reason_file = Path(sys.argv[7])
proposal_reasons = {
    "proposal-missing",
    "proposal-invalid",
    "proposal-detector-invalid",
    "proposal-binding-mismatch",
    "proposal-dispositions-invalid",
    "proposal-marker-missing",
    "proposal-marker-invalid",
    "proposal-control-mismatch",
}
reason = "verification-stage-failed" if exit_code else None
if stage == "proposal" and exit_code != 0:
    reason = "proposal-invalid"
    if reason_file.is_file() and not reason_file.is_symlink() and reason_file.stat().st_size <= 128:
        candidate = reason_file.read_text(encoding="utf-8", errors="replace").strip()
        if candidate in proposal_reasons:
            reason = candidate
if stage in {"accept-preview", "accept"} and exit_code != 0:
    reason = "acceptance-failed"
    acceptance_path = Path(sys.argv[8]) / f"pkstack-{stage}-{attempt}.json"
    acceptance_reasons = {
        "upstream accept requires a complete source-bound candidate parity artifact": (
            "acceptance-candidate-parity"
        ),
        "upstream accept requires canonical/generated Power parity": "acceptance-generated-parity",
        "upstream accept requires an exactly re-proved current pin": "acceptance-pin-reproof",
        "upstream accept requires a complete fast-forward comparison": (
            "acceptance-comparison-incomplete"
        ),
        "current upstream head does not match --expected-head": "acceptance-head-changed",
        "upstream accept proposal is stale or already applied": "acceptance-stale",
    }
    if (
        acceptance_path.is_file()
        and not acceptance_path.is_symlink()
        and acceptance_path.stat().st_size <= 32768
    ):
        try:
            payload = json.loads(acceptance_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            payload = None
        if isinstance(payload, dict) and isinstance(payload.get("error"), str):
            reason = acceptance_reasons.get(payload["error"], reason)
if (
    stage not in allowed
    or not 1 <= attempt <= 4
    or not 0 <= exit_code <= 255
    or not 0 <= cleanup_exit <= 255
    or re.fullmatch(r"[0-9a-f]{40}", base_sha) is None
    or re.fullmatch(r"[1-9][0-9]{0,15}", run_id) is None
):
    raise SystemExit("invalid trusted verifier diagnostic metadata")
feedback_exit = int(sys.argv[10])
if feedback_exit:
    reason = "verification-evidence-invalid"
    feedback_result = json.loads(Path(sys.argv[9]).read_text())
    if feedback_result.get("reason") == "verification-feedback-credential":
        reason = "verification-feedback-credential"
report = {
    "schema_version": 1,
    "source_run_id": int(run_id),
    "base_sha": base_sha,
    "attempt": attempt,
    "stage": stage,
    "exit_code": exit_code,
    "cleanup_exit_code": cleanup_exit,
    "passed": exit_code == cleanup_exit == feedback_exit == 0,
    "reason": reason,
}
encoded = json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n"
destination = stage_file.with_suffix(".json")
with destination.open("x", encoding="utf-8") as output:
    output.write(encoded)
stage_file.unlink()
reason_file.unlink(missing_ok=True)
print(encoded, end="")
if not report["passed"]:
    print(
        f"::warning::PKStack verification failed at {stage}"
        f" (exit {exit_code}; cleanup {cleanup_exit})"
    )
PY
if [[ "$finalizer_rc" -ne 0 ]]; then
  echo "trusted Git finalizer cleanup failed" >&2
  exit "$finalizer_rc"
fi

if [[ "$verification_rc" -eq 0 ]]; then
  printf 'passed=true\n' >>"$GITHUB_OUTPUT"
  printf 'attempt=%s\n' "$ATTEMPT_NUMBER" >>"$GITHUB_OUTPUT"
  rm -f "$verification_log" "$FEEDBACK_PATH"
  exit 0
fi

if [[ "$feedback_rc" -ne 0 ]]; then
  exit "$feedback_rc"
fi
rm -f "$verification_log"
printf 'passed=false\n' >>"$GITHUB_OUTPUT"
printf 'attempt=%s\n' "$ATTEMPT_NUMBER" >>"$GITHUB_OUTPUT"
exit 0
