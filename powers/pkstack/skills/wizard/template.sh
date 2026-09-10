#!/usr/bin/env bash
# Adapted from Matt Pocock's wizard template; see the Power provenance inventory.
set +x
set -euo pipefail

ENV_FILE="${ENV_FILE:-.wizard.env}"
TOTAL_STAGES=0
_wizard_stage=0

_wizard_incomplete() {
  local status=$?
  if (( status != 0 )); then
    printf '\nWizard incomplete. Saved stages remain; inspect and rerun when ready.\n' >&2
  fi
}
trap _wizard_incomplete EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

_wizard_key() {
  [[ "$1" =~ ^[A-Z][A-Z0-9_]*$ ]] || return 1
  case "$1" in
    BASH*|UID|EUID|PPID|SHELLOPTS|IFS|PATH|HOME|ENV|SHELL|CDPATH|PWD|OLDPWD|TMPDIR|PYTHON*|LD_*|DYLD_*|ENV_FILE|TOTAL_STAGES|WIZARD_*) return 1 ;;
  esac
}

# Values travel over stdin, never through a command argument or sourced file.
_wizard_env() {
  python3 - "$1" "$ENV_FILE" "$2" 3<&0 <<'PYCODE'
import os
import re
import shlex
import signal
import stat
import sys
import tempfile
from pathlib import Path

mode, filename, key = sys.argv[1:]
path = Path(filename)
lock = path.with_name(path.name + ".wizard-lock")
temporary = None
locked = False


def interrupted(signum, frame):
    raise SystemExit(128 + signum)


signal.signal(signal.SIGTERM, interrupted)
try:
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
        raise ValueError("invalid key")
    if mode == "write":
        lock.mkdir(mode=0o700)
        locked = True
    lines = []
    if path.is_symlink():
        raise ValueError("symlink target")
    if path.exists():
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_size > 1024 * 1024:
            raise ValueError("unsafe file")
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "r", encoding="utf-8") as stream:
            lines = stream.read(1024 * 1024 + 1).splitlines(keepends=True)
    found = []
    for line in lines:
        if line.startswith(key + "="):
            raw = line[len(key) + 1 :].rstrip("\r\n")
            tokens = shlex.split(raw, comments=False, posix=True)
            if len(tokens) != 1 or shlex.quote(tokens[0]) != raw:
                raise ValueError("not a literal written by this helper")
            found.append(tokens[0])
    if mode == "read":
        if found:
            sys.stdout.write(found[-1])
    elif mode == "write":
        with os.fdopen(3, "r", encoding="utf-8") as values:
            value = values.read(65537)
        if len(value) > 65536 or any(c in value for c in ("\r", "\n", "\0")):
            raise ValueError("value must be a bounded single line")
        replacement = key + "=" + shlex.quote(value) + "\n"
        output = []
        inserted = False
        for line in lines:
            if line.startswith(key + "="):
                if not inserted:
                    output.append(replacement)
                    inserted = True
            else:
                output.append(line)
        if not inserted:
            if output and not output[-1].endswith("\n"):
                output[-1] += "\n"
            output.append(replacement)
        new = "".join(output)
        if new != "".join(lines) or stat.S_IMODE(path.stat().st_mode) != 0o600:
            fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(new)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
            temporary = None
    else:
        raise ValueError("invalid operation")
except (OSError, ValueError, UnicodeError):
    print("Cannot safely read or update wizard assignment file.", file=sys.stderr)
    sys.exit(1)
finally:
    if temporary is not None:
        os.unlink(temporary)
    if locked:
        lock.rmdir()
PYCODE
}

say() { printf '  %s\n' "$1"; }
step() { say "$1"; }
pause() {
  printf '%s ' "${1:-Press Enter when ready.}"
  IFS= read -r _wizard_reply
}
confirm() {
  local reply
  printf '%s [y/N] ' "$1"
  IFS= read -r reply || return 1
  [[ "$reply" == y || "$reply" == Y || "$reply" == yes || "$reply" == YES ]]
}
banner() { printf '\n%s (%s stages)\n' "$1" "$TOTAL_STAGES"; }
stage() {
  _wizard_stage=$((_wizard_stage + 1))
  printf '\nStage %s/%s: %s\n' "$_wizard_stage" "$TOTAL_STAGES" "$1"
}
open_url() {
  [[ "$1" == https://* ]] || return 1
  if command -v open >/dev/null 2>&1; then open "$1"
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$1"
  else printf 'Visit this URL in your browser: %s\n' "$1"; fi
}
_wizard_ask() {
  local secret="$1" key="$2" prompt="$3" current input
  _wizard_key "$key" || return 1
  current=$(_wizard_env read "$key") || return 1
  printf '%s' "$prompt"
  if [[ -n "$current" ]]; then printf ' [Enter keeps saved value]'; fi
  printf ': '
  if [[ "$secret" == 1 ]]; then
    IFS= read -r -s input || { printf '\n' >&2; return 1; }
    printf '\n'
  else
    IFS= read -r input || return 1
  fi
  if [[ -z "$input" && -n "$current" ]]; then input="$current"; fi
  printf -v "$key" '%s' "$input"
}
ask() { _wizard_ask 0 "$1" "$2"; }
ask_secret() { _wizard_ask 1 "$1" "$2"; }
write_env() {
  _wizard_key "$1" || return 1
  printf '%s' "$2" | _wizard_env write "$1" || return 1
  printf 'Saved %s to %s\n' "$1" "$ENV_FILE"
}
_wizard_github_target() {
  [[ "${WIZARD_ALLOW_GITHUB_WRITES:-0}" == 1 ]] &&
    [[ "${WIZARD_GITHUB_REPOSITORY:-}" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]
}
set_secret() {
  _wizard_key "$1" && _wizard_github_target || return 1
  printf '%s' "$2" | gh secret set "$1" --repo "$WIZARD_GITHUB_REPOSITORY" >/dev/null 2>&1
}
set_var() {
  _wizard_key "$1" && _wizard_github_target || return 1
  printf '%s' "$2" | gh variable set "$1" --repo "$WIZARD_GITHUB_REPOSITORY" >/dev/null 2>&1
}
finish() {
  (( TOTAL_STAGES > 0 && _wizard_stage == TOTAL_STAGES )) || return 1
  printf '\nWizard stages completed. Verify the intended product behavior separately.\n'
}

# Source the library in a disposable shell for behavioral tests.
if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then return 0; fi

# STAGES: author this section. Set TOTAL_STAGES and an explicit ENV_FILE.
# No live setup is configured in the distributed template.
printf 'Copy this template and author the requested human-only stages first.\n' >&2
exit 1
