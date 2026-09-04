# PK-Stack Power (Poteto Kiro)

<p align="center">
  <img src="assets/logo.png" alt="A scholarly potato ghost, the PK-Stack mascot" width="220">
</p>

PK-Stack adds verified-development workflows to Kiro. Use Kiro's native
planning, then work against an executable check in the current conversation.

**[Start with the installation guide and failing-task walkthrough](https://github.com/njs14/pk-stack#install).**

This directory is the installable Power. Import it through Kiro's Power
manager, then invoke `/setup-pk-stack` in your target project. Prerequisites
are Kiro CLI v3 or Kiro IDE 1.x, Python 3.11+, and `uv`.
The [usage guide](docs/usage.md) includes the terminal-only setup path.

`plugin.json` owns the release version. Setup materializes workspace assets
in `.kiro/` and a locked controller in `.pk-stack/`; this Power remains the
source for future refreshes. It does not launch a replacement agent runtime.

## Package references

- [Usage and recovery](docs/usage.md)
- [Architecture and trust boundaries](docs/architecture.md)
- [Kiro surface support and validation limits](docs/kiro-v3-compatibility.md)
- [pstack workflow parity](docs/upstream-skill-parity.md) and [curated skills](docs/curated-skills.md)
- [Upstream update workflow](docs/upstream-control-loop.md)
- [Porting provenance](docs/provenance.md)
- [Repository validation evidence](https://github.com/njs14/pk-stack/blob/main/reviews/release-status.md)

The package is licensed under Apache-2.0. See [LICENSE](LICENSE),
[NOTICE](NOTICE), and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
