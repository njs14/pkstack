#!/usr/bin/env bash
set -euo pipefail

: "${KIRO_ARCHIVE:?KIRO_ARCHIVE is required}"
: "${KIRO_BIN_DIR:?KIRO_BIN_DIR is required}"
: "${KIRO_HOME:?KIRO_HOME is required}"
: "${KIRO_USER_HOME:?KIRO_USER_HOME is required}"
: "${RUNNER_TEMP:?RUNNER_TEMP is required}"

expected_sha256=6eccb46617a84690fc892219f264f7617312761c9a3d7e38cc47a0e2ab0152b7
for target in "$KIRO_BIN_DIR" "$KIRO_HOME" "$KIRO_USER_HOME"; do
  [[ ! -e "$target" && ! -L "$target" ]]
  [[ "$(dirname "$target")" == "$RUNNER_TEMP" ]]
done
[[ -f "$KIRO_ARCHIVE" && ! -L "$KIRO_ARCHIVE" ]]
printf '%s  %s\n' "$expected_sha256" "$KIRO_ARCHIVE" | sha256sum --check

mkdir -m 0700 "$KIRO_BIN_DIR" "$KIRO_HOME" "$KIRO_USER_HOME"
mkdir -m 0700 "$KIRO_HOME/agents"
tar --extract --xz --file "$KIRO_ARCHIVE" --directory "$KIRO_BIN_DIR" \
  --strip-components=2 \
  kirocli/bin/kiro-cli \
  kirocli/bin/kiro-cli-chat
test "$("$KIRO_BIN_DIR/kiro-cli" --version)" = "kiro-cli 2.21.0"
install -m 0600 .kiro/agents/pstack-maintainer.json \
  "$KIRO_HOME/agents/pstack-maintainer.json"

(
  cd "$RUNNER_TEMP"
  HOME="$KIRO_USER_HOME" KIRO_HOME="$KIRO_HOME" \
    "$KIRO_BIN_DIR/kiro-cli" settings chat.disableInheritingDefaultResources true
  HOME="$KIRO_USER_HOME" KIRO_HOME="$KIRO_HOME" \
    "$KIRO_BIN_DIR/kiro-cli" settings app.disableAutoupdates true
  HOME="$KIRO_USER_HOME" KIRO_HOME="$KIRO_HOME" \
    "$KIRO_BIN_DIR/kiro-cli" settings telemetry.enabled false
)
test ! -e "$KIRO_HOME/settings/mcp.json"
test ! -d "$KIRO_HOME/hooks"
