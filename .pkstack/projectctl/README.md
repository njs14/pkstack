# Repo-local projectctl

This directory is managed by the PKStack bootstrap. Use the canonical
`.pkstack/bin/projectctl` entrypoint.

The cached controller is not setup authority. Setup and refresh must use the
Power-local `/pkstack-setup` skill, or an explicitly reviewed `--power-root`;
`projectctl setup` fails closed when that source is omitted.

Runtime goal state lives in `.pkstack/state/` and is intentionally ignored.
