# Third-party notices

This file records third-party attribution and direct runtime dependency
licenses for PKStack. It is informational and does not alter the terms of
the root `LICENSE` or any third-party license.

## Cursor pstack workflow reference

This project is an independent Kiro-native semantic port informed by selected
workflow contracts in Cursor's public pstack plugin.

- Project: `cursor/plugins`, `pstack/` subtree
- Genesis source: <https://github.com/cursor/plugins/tree/b9ddc83c32972210b8a94d389130713e8eed346e/pstack>
- Genesis commit: `b9ddc83c32972210b8a94d389130713e8eed346e`
- Accepted pin: `7314f723a487ec406b6369fe5865ba034cfed166`
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

PKStack's Kiro-native OKF workflow is informed by selected produce, maintain,
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

PKStack retains historical Git object identities for OpenKnowledge's public versioned CLI schema
subtree. The `okn` process boundary and its active maintenance source have been retired. These
records preserve prior attribution; PKStack does not vendor or execute the schemas or runtime.

- Project: `openknowledge-sh/openknowledge`, `packages/cli/schemas/v1/` subtree
- Source: <https://github.com/openknowledge-sh/openknowledge/tree/6e8bbe026448fd890ace9293bcfe89b53363cd1f/packages/cli/schemas/v1>
- Pinned commit: `6e8bbe026448fd890ace9293bcfe89b53363cd1f`
- License: Apache License 2.0
- Detailed provenance: [`docs/openknowledge-cli-contract-provenance.md`](docs/openknowledge-cli-contract-provenance.md)

The schemas are not redistributed. The root `LICENSE` contains the Apache License 2.0 text but
licenses PKStack rather than transferring ownership of OpenKnowledge.

## HumanLayer skills semantic references

The Kiro-native `build-iterated-agentic-loop`, `design-control-loop`,
`narrow-react-prop-types`, and `show-me` skills preserve
reviewed semantics from HumanLayer's public skills catalog. Their wrappers and
bounded references are adapted for Kiro and PKStack's stricter workflow
security boundaries.

- Project: `humanlayer/skills`, reviewed plugin subtrees
- Source: <https://github.com/humanlayer/skills>
- Pinned catalog commit: `3c2629142c5d437428269b1b722b08c0b87f574d`
- Copyright: Copyright (c) 2026 HumanLayer
- License: MIT
- Detailed file-level provenance: the `docs/humanlayer-*-provenance.md` records

The upstream MIT notice follows verbatim.

```text
MIT License

Copyright (c) 2026 HumanLayer

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

## Matt Pocock `writing-for-agents` semantic reference

The Kiro-native `writing-for-agents` skill adapts the agent-facing writing method
from `mattpocock/skills` while excluding OpenAI-only UI metadata.

- Project: `mattpocock/skills`
- Source: <https://github.com/mattpocock/skills>
- Pinned commit: `6654f6b60cd9d5be8b54c6fafe44346dabeb3b76`
- Copyright: Copyright (c) 2026 Matt Pocock
- License: MIT
- Detailed provenance: [`docs/mattpocock-writing-for-agents-provenance.md`](docs/mattpocock-writing-for-agents-provenance.md)

The Matt Pocock MIT notice in the following section also applies to this source.
The `LICENSE` bytes at both recorded source revisions are identical.

## Matt Pocock knowledge skills semantic references

The Kiro-native `grilling`, `grill-me`, `domain-modeling`, and `grill-with-docs`
skills adapt decision-focused interviewing, domain language, and decision capture from
Matt Pocock's skills. Native Kiro references replace the upstream Skill API; project
knowledge follows PKStack's Wiki lifecycle. OpenAI UI metadata is provenance-only.

- Project: `mattpocock/skills`
- Source: <https://github.com/mattpocock/skills/tree/3cca18b368ae95cdbdebbff572ccafa662551015>
- Pinned commit: `3cca18b368ae95cdbdebbff572ccafa662551015`
- Copyright: Copyright (c) 2026 Matt Pocock
- License: MIT
- Detailed provenance: the four `docs/mattpocock-{grilling,grill-me,domain-modeling,grill-with-docs}-provenance.md` records

The upstream MIT notice follows verbatim.

```text
MIT License

Copyright (c) 2026 Matt Pocock

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

## Archify reviewed offline runtime

PKStack redistributes a reviewed, byte-addressed subset of the Archify runtime
under [`skills/archify/upstream/`](skills/archify/upstream). The Kiro wrapper
and curated bundle manifest are separate from the pinned upstream source.
The runtime preserves upstream bytes except for the documented PKStack layout
patches in [Archify provenance](docs/tt-a1i-archify-provenance.md), which records
original and local hashes. Tests, rendered demo HTML, `node_modules`, build/gallery tooling, the
network update checker, and npm lock/install workflow are intentionally not
included.

- Project: `tt-a1i/archify`, `archify/` subtree
- Source: <https://github.com/tt-a1i/archify/tree/2ead014aa8ec91f104cd052f1a6ca82de5e26c31/archify>
- Pinned commit: `2ead014aa8ec91f104cd052f1a6ca82de5e26c31`
- Copyright: Copyright (c) 2026 tt-a1i (Archify); Copyright (c) 2025 Cocoon AI
- License: MIT
- Detailed file-level provenance: [`docs/tt-a1i-archify-provenance.md`](docs/tt-a1i-archify-provenance.md)
- Exact shipped bundle: [`docs/tt-a1i-archify-bundle-manifest.json`](docs/tt-a1i-archify-bundle-manifest.json)

The vendored runtime includes the upstream MIT license and its separate
third-party brand-mark notice at [`skills/archify/upstream/LICENSE`](skills/archify/upstream/LICENSE)
and [`skills/archify/upstream/THIRD_PARTY_NOTICES.md`](skills/archify/upstream/THIRD_PARTY_NOTICES.md).
The upstream MIT notice follows verbatim.

```text
MIT License

Copyright (c) 2026 tt-a1i (Archify)
Copyright (c) 2025 Cocoon AI

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

## Cyclopts

Cyclopts is a direct runtime dependency used to expose the `projectctl` command
interface.

- Package: `cyclopts==4.23.2`
- Source: <https://github.com/BrianPugh/cyclopts/tree/v4.23.2>
- License: Apache License 2.0
- License text: <https://github.com/BrianPugh/cyclopts/blob/v4.23.2/LICENSE>

Cyclopts is not vendored in this repository. Its installed distribution remains
under the Apache License 2.0. The root `LICENSE` contains the complete Apache
License 2.0 text, but licenses the PKStack work rather than transferring
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

## markdown-it-py

markdown-it-py is a direct runtime dependency used for CommonMark link and
heading parsing in local knowledge validation. `pyproject.toml` allows
`markdown-it-py>=4,<5`; the committed lockfile currently resolves version `4.2.0`.

- Package: `markdown-it-py 4.2.0` in `uv.lock`
- Source: <https://github.com/executablebooks/markdown-it-py/tree/v4.2.0>
- License: MIT (the port also carries the MIT notice of the original
  `markdown-it` by Vitaly Puzrin and Alex Kocharin)
- License text: <https://github.com/executablebooks/markdown-it-py/blob/v4.2.0/LICENSE>
  and <https://github.com/executablebooks/markdown-it-py/blob/v4.2.0/LICENSE.markdown-it>

## agent-client-protocol

agent-client-protocol is the official Python ACP client used by the bounded
`knowledge search` worker. `pyproject.toml` pins `agent-client-protocol==0.12.1`.

- Package: `agent-client-protocol 0.12.1` in `uv.lock`
- Source: <https://github.com/agentclientprotocol/python-sdk>
- License: Apache-2.0
- License text: the `LICENSE` file shipped in the distribution's `licenses/`
  directory

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

The repository's artwork references Kiro's ghost mascot. The historical `assets/banner.png`
mascot is an AI-generated transformation made at the project owner's request with the
installed Kiro application icon as a visual reference; the source `.icns` file is not included.
The current `assets/logo.png` "Knowledge crest" depicts four ghost characters with a book and
knowledge tree and was selected on September 6, 2026. See [artwork creation history](https://github.com/njs14/pkstack/blob/main/docs/assets/creation-history.md)
for the generation provenance of both images.

Kiro and its original artwork remain the property of their respective owner. This attribution
does not claim a license, endorsement, or affiliation. Review or replace the mascot before any
distribution whose trademark or artwork policy differs from this private-project use.

## Referenced but not redistributed

Kiro, Cursor, OKF, optional external reviewer CLIs, `cursor-team-kit`, Graphite,
and the Agent Plugins JSON schema are referenced for interoperability or
provenance only. This repository does not bundle their runtimes, credentials,
session state, or source code.

## Astral Python skills

Source: https://github.com/astral-sh/claude-code-plugins/tree/f3ce88a7ba830f53afd6d944c1d0278ed318e142

Upstream offers MIT or Apache-2.0; these adapters use the MIT option.

```text
MIT License

Copyright (c) 2025 Astral Software Inc.

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

## Impeccable design methods

- Project: `pbakaus/impeccable`, `skill/` subtree
- Pin: `dbdc470e70dbbda69f9b78ee38bc38ea1d3560b9`
- Copyright 2025 Paul Bakaus
- License: Apache License 2.0; complete terms in [LICENSE](LICENSE)
- [Source license](https://github.com/pbakaus/impeccable/blob/dbdc470e70dbbda69f9b78ee38bc38ea1d3560b9/LICENSE)
- [Adaptations and exclusions](docs/pbakaus-impeccable-provenance.md)

PKStack modified and condensed the design instructions for Kiro. It does not redistribute
Impeccable's binary, browser tooling, fonts, or its iOS/Android platform references. The upstream
NOTICE.md attributes those excluded platform references to ehmo's MIT-licensed
[platform-design-skills](https://github.com/ehmo/platform-design-skills).

## OpenAI Codex PR Babysitter method

- Project: `openai/codex`, `.codex/skills/babysit-pr/` subtree
- Pin: `9f70e348e0227980de97e361cce830236fb18317`
- OpenAI Codex, Copyright 2025 OpenAI
- License: Apache License 2.0; complete terms in [LICENSE](LICENSE)
- [Source license](https://github.com/openai/codex/blob/9f70e348e0227980de97e361cce830236fb18317/LICENSE)
- [Adaptations and exclusions](docs/openai-babysit-pr-provenance.md)

PKStack modified the workflow and heuristics for Kiro and its existing authorization and
completion contract. The Python watcher and Codex profile are not redistributed. The upstream
root NOTICE also attributes Ratatui to Florian Dehau and the Ratatui Developers; no Ratatui code
is included in this skill adaptation.
