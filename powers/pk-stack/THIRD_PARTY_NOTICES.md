# Third-party notices

This file records third-party attribution and direct runtime dependency
licenses for PK-Stack. It is informational and does not alter the terms of
the root `LICENSE` or any third-party license.

## Cursor pstack workflow reference

This project is an independent Kiro-native semantic port informed by selected
workflow contracts in Cursor's public pstack plugin.

- Project: `cursor/plugins`, `pstack/` subtree
- Source: <https://github.com/cursor/plugins/tree/b9ddc83c32972210b8a94d389130713e8eed346e/pstack>
- Pinned commit: `b9ddc83c32972210b8a94d389130713e8eed346e`
- Copyright: Copyright (c) 2026 Lauren Tan
- License: MIT
- Detailed file-level provenance: [`docs/provenance.md`](docs/provenance.md)

The upstream MIT notice follows verbatim.

```text
MIT License

Copyright (c) 2026 Lauren Tan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## OKF skills workflow reference

PK-Stack's Kiro-native OKF workflow is informed by selected produce, maintain,
consume, progressive-disclosure, index, and bounded-log ideas from the public
`scaccogatto/okf-skills` project. No upstream runtime, validator, MCP server,
hook, backfill implementation, visualizer, template, or specification is
redistributed or executed.

- Project: `scaccogatto/okf-skills`, `skills/` subtree
- Source: <https://github.com/scaccogatto/okf-skills/tree/bf2448f03686a8348324e4741106697d30a867f9/skills>
- Pinned commit: `bf2448f03686a8348324e4741106697d30a867f9`
- Copyright: Copyright (c) 2026 Marco Boffo
- License: MIT
- Detailed provenance: [`docs/okf-skills-provenance.md`](docs/okf-skills-provenance.md)

The upstream MIT notice follows verbatim.

```text
MIT License

Copyright (c) 2026 Marco Boffo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## OpenKnowledge CLI contract reference

PK-Stack tracks Git object identities for OpenKnowledge's public versioned CLI schema subtree to
detect changes at its optional `okn` process boundary. It does not vendor or execute those schemas
or the OpenKnowledge runtime.

- Project: `openknowledge-sh/openknowledge`, `packages/cli/schemas/v1/` subtree
- Source: <https://github.com/openknowledge-sh/openknowledge/tree/6e8bbe026448fd890ace9293bcfe89b53363cd1f/packages/cli/schemas/v1>
- Pinned commit: `6e8bbe026448fd890ace9293bcfe89b53363cd1f`
- License: Apache License 2.0
- Detailed provenance: [`docs/openknowledge-cli-contract-provenance.md`](docs/openknowledge-cli-contract-provenance.md)

The schemas are not redistributed. The root `LICENSE` contains the Apache License 2.0 text but
licenses PK-Stack rather than transferring ownership of OpenKnowledge.

## Cyclopts

Cyclopts is a direct runtime dependency used to expose the `projectctl` command
interface.

- Package: `cyclopts==4.23.2`
- Source: <https://github.com/BrianPugh/cyclopts/tree/v4.23.2>
- License: Apache License 2.0
- License text: <https://github.com/BrianPugh/cyclopts/blob/v4.23.2/LICENSE>

Cyclopts is not vendored in this repository. Its installed distribution remains
under the Apache License 2.0. The root `LICENSE` contains the complete Apache
License 2.0 text, but licenses the PK-Stack work rather than transferring
ownership of Cyclopts.

## PyYAML

PyYAML is a direct runtime dependency used to parse and emit YAML feature and
knowledge records. `pyproject.toml` allows `PyYAML>=6.0.2,<7`; the committed
lockfile currently resolves version `6.0.3`.

- Package: `PyYAML 6.0.3` in `uv.lock`
- Source: <https://github.com/yaml/pyyaml/tree/6.0.3>
- License: MIT
- License text: <https://github.com/yaml/pyyaml/blob/6.0.3/LICENSE>

The PyYAML MIT notice follows verbatim.

```text
Copyright (c) 2017-2021 Ingy döt Net
Copyright (c) 2006-2016 Kirill Simonov

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Build, development, and transitive packages

`hatchling` is the build backend. Test and development groups include tools
such as `pytest`, `pytest-cov`, `ruff`, and `ty`. Cyclopts and the development
tools resolve additional transitive packages. These packages are not vendored
or redistributed as source by this repository. The root `uv.lock` is the
authoritative version and artifact inventory for development, while
`templates/projectctl/uv.lock` is the corresponding inventory for the
bootstrapped repo-local runtime. Each installed distribution supplies its own
license metadata and license files.

## Kiro visual reference

The private repository's `assets/logo.png` mascot is an AI-generated transformation made at the
project owner's request with the installed Kiro application icon as a visual reference. The
source `.icns` file is not included. The generated mascot intentionally retains the recognizable
two-eye ghost silhouette and purple rounded-square visual language while replacing the body with
a potato. See [`assets/README.md`](assets/README.md) for generation provenance.

Kiro and its original artwork remain the property of their respective owner. This attribution
does not claim a license, endorsement, or affiliation. Review or replace the mascot before any
distribution whose trademark or artwork policy differs from this private-project use.

## Referenced but not redistributed

Kiro, Cursor, OKF, optional external reviewer CLIs, `cursor-team-kit`, Graphite,
and the Agent Plugins JSON schema are referenced for interoperability or
provenance only. This repository does not bundle their runtimes, credentials,
session state, or source code.
