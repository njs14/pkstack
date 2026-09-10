# Deepen a module without losing proof

Classify dependencies before choosing the test boundary. In-process computation and state can
usually be tested directly. Local substitutes can exercise owned I/O cheaply, but their fidelity
limits remain explicit. Remote owned systems may benefit from a port with production transport
and a test adapter. True external services need controlled boundary substitutes plus proportionate
integration evidence where access permits.

Two concrete adapter needs support a real seam; one hypothetical extension seldom justifies new
indirection. Keep internal test seams private unless callers need them. Prefer a small public
interface that reaches the behavior where real bugs occur, including interacting callers.

Move coverage to that interface before retiring tests coupled to removed structure. Delete only
redundant tests after proving the new coverage preserves meaningful regressions, including denied
operations and absence of forbidden effects. A security or authority check can be a valid boundary
test even when it observes an internal guard. Do not delete tests merely because they use mocks,
private functions, call counts, or negative assertions.
