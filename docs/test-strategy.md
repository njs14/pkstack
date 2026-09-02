# Test strategy

Unit tests cover endpoint refusal and client construction: host clients always carry the
explicit loopback endpoint and fixed region, while the task endpoint is only the literal
Docker-network URL. These tests prevent accidental default endpoint/ambient credentials paths.

The cold lifecycle is the integration proof. It uses the public `labctl` surface in this
order: doctor, up, deploy, status, verify, evidence, down. The feature contract deliberately
uses only `./labctl verify --output json`; no raw Docker or AWS CLI escape hatch is stored.

State tests require an exact canonical manifest and verify concurrent exclusive lifecycle
claiming, directory-relative no-follow reads/writes, manifest retention on partial local
failure, and refusal of linked or tampered state. Deployment tests require `propagateTags=SERVICE`
for both create and repeat-deploy update. Ownership tests require exact service tags, reject any
returned task-tag mismatch, validate the current-run ECS ARN/family-to-Floci container chain,
and prove both task containers before `verify` can run Docker exec or mutate the emulator. They
also require an empty Docker mount list. ci-011 observed Floci omit task tags even after the
propagation request, so that absence is recorded as an emulator limitation rather than forged
evidence. Parser subprocess tests require a single JSON error object on stdout for JSON-mode
argument failures; cleanup tests restrict image removal to the two current-run tags.

For a future independently judged Kiro mutation, first copy
`judge/verify_feature_contract.py` outside the checkout. Hash
`Wiki/features/document-export.md` with `shasum -a 256` and retain that value before handing
over the mutable checkout. After the lab is deployed, execute the copied judge with
`--repo <mutated-checkout> --expected-contract-sha256 <recorded-hash>`. It hashes before and
after, parses bounded JSON, and invokes only `<repo>/labctl verify --output json`; it never
uses Docker or AWS commands. Retain the judge JSON output with the two visible hashes.
