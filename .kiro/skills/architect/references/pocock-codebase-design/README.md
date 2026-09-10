# Design useful module interfaces

A module combines an interface and implementation. Its interface includes everything a caller
must know: types, invariants, ordering, errors, configuration, and performance expectations.
Depth means substantial behavior behind a small interface, not a long call chain. A seam is a
place to substitute behavior without changing the caller; an adapter fills that role. Locality
means understanding and changing a concept in a small, coherent area. Use this vocabulary where
it clarifies a decision, preserving the project's established domain names and terminology.

Prefer interfaces that hide policy and make the common caller easy to read. Apply the deletion
test: does deleting a wrapper concentrate complexity or simply relocate it? Judge by concrete
callers, data ownership, and meaningful behavior tests, not file size alone. The interface should
be a useful test surface; do not expose internals solely to make a test convenient.

Use [dependency and test guidance](DEEPENING.md) to choose a seam and
[alternative interface design](DESIGN-IT-TWICE.md) within architect's existing alternatives pass.
These are shared references, not a new planning skill or a second contest.
