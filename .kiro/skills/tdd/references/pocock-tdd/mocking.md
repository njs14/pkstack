# Substitute at a meaningful boundary

Prefer real owned behavior. Substitute external APIs, nondeterministic time/randomness, or unsafe
I/O where a controlled test needs it. Use the repository's existing local database or filesystem
fixtures when their fidelity is useful. State what a fake cannot prove about production.

Inject a concrete operation interface at the boundary, such as charge or lookup, instead of a
generic fetcher requiring a second router inside each test. Do not add an abstraction for a
hypothetical second adapter or mock away the behavior the test claims to verify. Boundary tests
may validate arguments, call counts, or non-occurrence when those effects are the real contract.
Combine boundary substitutes with relevant integration proof without reopening settled tooling
choices or introducing credentials into candidate tests.
