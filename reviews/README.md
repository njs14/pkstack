# Release evidence

Start with the [current release status](release-status.md). It is the
only current surface that can describe whether this repository is ready for a
release. The `plugin.json` version is the metadata authority; a historical
record never accepts a different candidate.

Older test runs, Kiro observations, upstream campaigns, and reviewer reports
are retained under [`historical/pre-v0.2/`](historical/pre-v0.2/) with their
original provenance. They are useful context and regression history, not
current gate results. The [validation report](../powers/pkstack/docs/validation-report.md)
explains how to collect a fresh evidence packet.

Review contracts and Power-specific review guidance remain with the package in
[`powers/pkstack/reviews/`](../powers/pkstack/reviews/).

The Floci application and its live integration campaigns are maintained in the
separate private [pk-stack-floci-lab](https://github.com/njs14/pk-stack-floci-lab)
repository. Floci is not a PKStack release artifact or release gate.
