#!/usr/bin/env bash
# Adapted from Matt Pocock's human observation loop. Capture no secrets.
set +x
set -euo pipefail
trap 'printf "\nObservation loop interrupted; no verdict.\n" >&2; exit 130' INT
trap 'printf "\nObservation loop interrupted; no verdict.\n" >&2; exit 143' TERM
step() {
  printf '\n%s\nPress Enter when done: ' "$1"
  IFS= read -r _hitl_reply
}
capture() {
  local key="$1" prompt="$2" answer
  [[ "$key" =~ ^OBS_[A-Z0-9_]+$ ]] || return 1
  printf '%s (redacted observations only): ' "$prompt"
  IFS= read -r answer || return 1
  printf -v "$key" '%s' "$answer"
}
if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then return 0; fi
# Replace these stages with the reported user-surface reproduction.
step 'Perform the prepared local reproduction; keep login values in the product.'
capture OBS_RESULT 'Describe the exact observed symptom or successful result'
printf '\nOBS_RESULT=%s\n' "$OBS_RESULT"
