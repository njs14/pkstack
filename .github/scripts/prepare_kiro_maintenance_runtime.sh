#!/usr/bin/env bash
set -euo pipefail

: "${KIRO_ARCHIVE:?KIRO_ARCHIVE is required}"
: "${KIRO_BIN_DIR:?KIRO_BIN_DIR is required}"
: "${KIRO_HOME:?KIRO_HOME is required}"
: "${KIRO_USER_HOME:?KIRO_USER_HOME is required}"
: "${RUNNER_TEMP:?RUNNER_TEMP is required}"
: "${TRUSTED_ROOT:?TRUSTED_ROOT is required}"

agent_name=${KIRO_AGENT_NAME:-pk-stack-maintainer}
if [[ ! "$agent_name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  echo "KIRO_AGENT_NAME is invalid" >&2
  exit 2
fi

expected_sha256=6eccb46617a84690fc892219f264f7617312761c9a3d7e38cc47a0e2ab0152b7
for target in "$KIRO_BIN_DIR" "$KIRO_HOME" "$KIRO_USER_HOME"; do
  [[ ! -e "$target" && ! -L "$target" ]]
  [[ "$(dirname "$target")" == "$RUNNER_TEMP" ]]
done
[[ -f "$KIRO_ARCHIVE" && ! -L "$KIRO_ARCHIVE" ]]
printf '%s  %s\n' "$expected_sha256" "$KIRO_ARCHIVE" | sha256sum --check

mkdir -m 0700 "$KIRO_BIN_DIR" "$KIRO_HOME" "$KIRO_USER_HOME"
mkdir -m 0700 "$KIRO_HOME/agents" "$KIRO_HOME/settings"
tar --extract --xz --file "$KIRO_ARCHIVE" --directory "$KIRO_BIN_DIR" \
  --strip-components=2 \
  kirocli/bin/kiro-cli \
  kirocli/bin/kiro-cli-chat
test "$("$KIRO_BIN_DIR/kiro-cli" --version)" = "kiro-cli 2.21.0"
trusted_agent="$TRUSTED_ROOT/.kiro/agents/${agent_name}.json"
[[ -f "$trusted_agent" && ! -L "$trusted_agent" ]]
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
test ! -e "$KIRO_USER_HOME/.kiro"
test ! -d "$KIRO_HOME/hooks"
