# Astral Python skills provenance

PKStack adapts Astral's `uv`, `ruff`, and `ty` skills for Kiro. Retrieved 2026-09-06 from
https://github.com/astral-sh/claude-code-plugins/tree/f3ce88a7ba830f53afd6d944c1d0278ed318e142/plugins/astral.
The MIT license option and complete notice are retained in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

## Reviewed adaptations

The wrappers retain dependency management, lint/format, and type-check responsibilities with
explicit composition and existing project verification ownership. Project tools use their locked
environment. Existing Poetry/PDM and other chosen toolchains remain respected unless migration is
requested. Reviewed pre-uv bootstrap and active-interpreter subprocesses remain valid exceptions.

The upstream uv example `uvx python@3.12` is corrected to `uv run --python 3.12 python` using
[Astral's interpreter selection documentation](https://docs.astral.sh/uv/concepts/python-versions/).
Inline metadata is reserved for standalone scripts because it isolates project dependencies.
Claude invocation and automatic ty LSP claims are replaced with local skill references and an
explicit separate LSP task. No plugin metadata, hooks, installers, or global settings are activated.

The complete plugin subtree, including excluded Claude plugin metadata, is inventoried in
[astral-python-source-parity.json](astral-python-source-parity.json). Each skill's exact local
bytes are bound by its `astral-<name>-bundle-manifest.json` in this directory.

## Original source identities

| Source-relative path | Git blob SHA-1 | SHA-256 | Bytes |
| --- | --- | --- | --- |
| `skills/uv/SKILL.md` | `077bf2c2f7deb9ec23da34873e1c7548d462ef59` | `6553a22dbe4251ec851e0d1952d11e801c07a8a6d9bab21e86aa8e6764d147db` | 3952 |
| `skills/ruff/SKILL.md` | `9cc1061821c59a96e04acdef2e2e1342b79ca406` | `b4224a81367816fba28c3d6e69dbe9997b6d37317dbaec3f026b0c8c834c68ba` | 3989 |
| `skills/ty/SKILL.md` | `8841bc4a8f89aba3b9b32639c2d4b16fdddcf075` | `980f9844dd9b98cec97192adbcdc658abc9bcc93d28bec06706cf896820b0a4a` | 3180 |

<!-- pk-stack-upstream-genesis: {"commit":"f3ce88a7ba830f53afd6d944c1d0278ed318e142","path":"plugins/astral","repository":"astral-sh/claude-code-plugins","source_id":"astral-python","subtree_sha":"8cc1cb9f539f90fd98efa4be3857c6d74fd8d839"} -->
