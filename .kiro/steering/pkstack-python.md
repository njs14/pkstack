---
inclusion: fileMatch
fileMatchPattern:
  - "**/*.py"
  - "**/*.pyi"
  - "**/pyproject.toml"
  - "**/uv.lock"
  - "**/ruff.toml"
  - "**/ty.toml"
---

# PKStack Python discipline

Read the relevant bundled skills before Python environment, lint/format, or typing work:
`uv` owns dependencies and script execution; `ruff` owns lint and format; `ty` owns type checking.
Use project-pinned tools and the project's supported Python version. Preserve a chosen alternate
manager or checker unless migration is requested. Keep bootstrap-before-uv and active-interpreter
subprocess exceptions explicit. Standalone inline metadata isolates project dependencies.

Compose these helpers with the active task; preserve native planning permissions, existing tests,
and projectctl verification ownership. Do not install the Claude plugin, configure an LSP, change
models, or run global tool installation as a side effect. Avoid duplicate mandatory checks.
