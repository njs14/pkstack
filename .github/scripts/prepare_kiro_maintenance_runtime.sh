#!/usr/bin/env bash
set -euo pipefail

: "${KIRO_ARCHIVE:?KIRO_ARCHIVE is required}"
: "${KIRO_BIN_DIR:?KIRO_BIN_DIR is required}"
: "${KIRO_HOME:?KIRO_HOME is required}"
: "${KIRO_USER_HOME:?KIRO_USER_HOME is required}"
: "${RUNNER_TEMP:?RUNNER_TEMP is required}"
: "${TRUSTED_ROOT:?TRUSTED_ROOT is required}"

agent_name=${KIRO_AGENT_NAME:-pkstack-maintainer}
if [[ ! "$agent_name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  echo "KIRO_AGENT_NAME is invalid" >&2
  exit 2
fi

expected_sha256=7fc0564fd02295a64470c4bf52752f5475f3280be3fa4dd9db255162e07e9825
[[ -d "$RUNNER_TEMP" && ! -L "$RUNNER_TEMP" ]] || exit 1
[[ "$KIRO_BIN_DIR" != "$KIRO_USER_HOME" ]] || exit 1
# v3 reads global agents from HOME/.kiro; keep both CLI lookup paths identical.
[[ "$KIRO_HOME" == "$KIRO_USER_HOME/.kiro" ]] || exit 1
for target in "$KIRO_BIN_DIR" "$KIRO_USER_HOME"; do
  [[ ! -e "$target" && ! -L "$target" ]] || exit 1
  [[ "$(dirname "$target")" == "$RUNNER_TEMP" ]] || exit 1
  [[ "$(basename "$target")" =~ ^kiro-[a-z0-9-]+$ ]] || exit 1
done
[[ ! -e "$KIRO_HOME" && ! -L "$KIRO_HOME" ]] || exit 1
[[ -f "$KIRO_ARCHIVE" && ! -L "$KIRO_ARCHIVE" ]] || exit 1
printf '%s  %s\n' "$expected_sha256" "$KIRO_ARCHIVE" | sha256sum --check

mkdir -m 0700 "$KIRO_BIN_DIR" "$KIRO_USER_HOME"
mkdir -m 0700 "$KIRO_HOME"
mkdir -m 0700 "$KIRO_HOME/agents" "$KIRO_HOME/settings"
tar --extract --xz --file "$KIRO_ARCHIVE" --directory "$KIRO_BIN_DIR" \
  --strip-components=2 \
  kirocli/bin/kiro-cli \
  kirocli/bin/kiro-cli-chat
test "$("$KIRO_BIN_DIR/kiro-cli" --version)" = "kiro-cli 2.21.1"
trusted_agent="$TRUSTED_ROOT/.kiro/agents/${agent_name}.json"
[[ -f "$trusted_agent" && ! -L "$trusted_agent" ]] || exit 1
install -m 0600 "$trusted_agent" \
  "$KIRO_HOME/agents/${agent_name}.json"

settings_path="$KIRO_HOME/settings/cli.json"
install -m 0600 /dev/null "$settings_path"
printf '%s\n' \
  '{' \
  '  "app.disableAutoupdates": true,' \
  '  "chat.disableInheritingDefaultResources": true,' \
  '  "telemetry.enabled": false' \
  '}' >"$settings_path"
printf '%s  %s\n' \
  81d98ac813691c26f18f797ca5126c5150125cf74d2f6d413e152290074a6bd0 \
  "$settings_path" | sha256sum --check
test "$(stat -c '%a' "$settings_path")" = 600
test ! -e "$KIRO_HOME/settings/mcp.json"
test -d "$KIRO_USER_HOME/.kiro"
test ! -d "$KIRO_HOME/hooks"
