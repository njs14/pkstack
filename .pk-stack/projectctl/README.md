# Repo-local projectctl

This directory is managed by the PK-Stack bootstrap. Use the canonical
`.pk-stack/bin/projectctl` entrypoint. A bootstrap-managed `./projectctl` may also
exist as a convenience, but workflows never select an ambient root executable.

The cached controller is not setup authority. Setup and refresh must use the
Power-local `/setup-pk-stack` skill, or an explicitly reviewed `--power-root`;
`projectctl setup` fails closed when that source is omitted.

Runtime goal state lives in `.pk-stack/state/` and is intentionally ignored.
