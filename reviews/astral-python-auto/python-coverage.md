# First-party Python static coverage

The shared `.github/scripts/pkstack_python_static.py` gate checks maintained Python from
the existing locked Power environment. No dependency or tool-version upgrade was required.

| Maintained surface | Ruff lint and format | ty |
| --- | --- | --- |
| Power `src` and `tests` | Existing coverage retained | Existing coverage retained |
| Power benchmarks and examples | Added | Added |
| Setup entrypoint | Existing coverage retained | Added |
| Repository `.github` Python modules and tests | Added | Added |
| Seven Python heredocs in maintained shell scripts and workflow run steps | Added | Added |

Generated `.kiro` and `.pkstack` copies and historical `reviews` fixtures remain excluded
from independent static checks; installation and distribution tests verify generated parity.
Root `ruff.toml` and `ty.toml` define repository-script coverage, and Power configuration covers
its own sources. The existing pre-uv Python version guard retains its documented Ruff exception.

The shared gate is called by the local/CI policy lane and both upstream-candidate static gates.
Quoted Python heredocs are materialized into temporary `.py` files and only passed to static
analyzers. Their contents are never imported, executed, or evaluated by extraction. Unsupported
or ambiguous recognized Python heredocs fail with an origin and line number. Focused tests
cover all seven current bodies and lint, format, type, continuation, indentation, here-string,
and unsupported/multiple-heredoc cases. This is a bounded extractor for the maintained shell
forms, not a general shell parser.

The pass repaired lint and type diagnostics and formatted the newly covered files. Explicit
runtime narrowing preserves external-data checks; JSON fixtures use heterogeneous JSON types.
A coordinator regression check caught a worker change that raised `TypeError` for unhashable
focus titles. The corrected implementation preserves `StreamError`, with tests for malformed
values in each title position. Embedded workflow validators and fixture checksums were re-pinned
from their final source bytes.

Run the static gate from the repository root:

```sh
uv run --frozen --project powers/pkstack python -B .github/scripts/pkstack_python_static.py --repo-root .
```

Full local checks also cover behavior, browser rendering, packaging, generated parity, source
provenance, permissions, and workflow contracts. See the acceptance README and gate summary
for the exact checked commit and outcomes.
