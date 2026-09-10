# Observe the contract

For a checkout, drive the cart and checkout interface and assert the observed confirmed order,
not merely that an internal helper was called. For user creation, verify retrieval through the
supported interface when that proves the contract. If the contract is a database write, its
persisted state may itself be the correct observation.

Use an independently known total such as 15 for items priced 10 and 5. Recomputing the total with
the same algorithm as production can pass when both are wrong. Verify the test first fails for
the intended behavioral reason, not bad fixtures, import errors, or missing tools.

Internal mocks and call assertions deserve scrutiny, not blanket removal. A no-network guarantee,
single charge, denied write, or atomic update can require observing calls or the absence of an
effect. Preserve such regressions across refactors, and test interacting callers when the bug
only appears across them. Keep tests focused on one behavior with the assertions needed to prove it.
