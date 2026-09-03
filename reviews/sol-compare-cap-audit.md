# Sol Advisor compare-cap audit

This record covers the selective Sol Advisor audit of PK-Stack's source-scoped reconstruction at
GitHub's repository-wide 300-file Compare response ceiling. It is an implementation review, not a
Fable acceptance or release verdict.

## First audit

- Base and working-tree HEAD: `9fc846884fb897b592d40366430d77d692aee72b`
- Reviewed diff SHA-256:
  `10e9d4aa1ece89821d271dd805e0bf038a92b6da8f370d5d3b455423f4e79322`
- Reviewer: installed `sol_advisor_sol_reviewer`, `gpt-5.6-sol`, high effort
- Access: instruction-enforced read-only on an unrestricted local filesystem; network unused
- Verdict: `FIX FIRST`

The reviewer found two material defects:

1. `SOL-001` (high): valid untrusted UTF-8 blobs could drive unbounded worst-case
   `difflib.SequenceMatcher` work after the network timeout ceased to apply.
2. `SOL-002` (medium): rename uniqueness considered only removed and added candidates, so an
   unchanged file with the same identity could make a copy/delete pair look like a pure rename.

## Remediation

The canonical and generated controllers now reject either blob side above 5,000 lines and share a
25,000,000-line-pair work budget across every tree-derived patch in one comparison. The work charge
happens before matcher construction. Rename inference now requires the full type/mode/SHA/size
identity to occur exactly once in each entire subtree. Capped adversarial-line, aggregate-budget,
and unchanged-duplicate regressions accompany the prior unique-rename and patch round-trip tests.

Parent verification after remediation reported:

- `117 passed` for `powers/pk-stack/tests/test_upstreams.py`;
- `302 passed` for the root suite;
- `787 passed` for the canonical Power suite;
- locked Ruff, format, `ty`, JSON, diff, generated-parity, and bootstrap-receipt checks passed;
- active standard GitHub workflows passed `actionlint` with the intentional `SC2174` warning
  suppressed because `umask 077` protects intermediate directories;
- all standalone shell scripts passed `shellcheck`.

## Fresh audit

- Reviewed diff SHA-256:
  `9a9a269d15b5ed7ef79a2ea0e63a42be7a97dcc53fd950d5da3b732fbabe4585`
- Resulting implementation commit: `441ccae81ee6dcda68c987a06aadcb3139357d7c`
- Tree: `a0c755a9f41b50b17002395dc5b3209db1b80845`
- Reviewer: fresh installed `sol_advisor_sol_reviewer`, `gpt-5.6-sol`, high effort
- Access: instruction-enforced read-only on an unrestricted local filesystem; network unused
- Verdict: `ACCEPT` for advancement to Fable, expressed by the reviewer as `ship`
- Material findings: none
- `SOL-001`: closed
- `SOL-002`: closed

The fresh reviewer independently rehashed the final diff, confirmed canonical/generated controller
SHA-256 `6c3c1c7af9920ace1d23b6b3a354005b62e70066e256bec7ab3bca9388bba146`,
confirmed the three maintenance-skill copies at
`f57d5eb0ac9b70499d7e5f86108491a8d368212a28f88bf4244a752aa9f5e1d3`, and found zero
bootstrap receipt mismatches. It inspected but did not rerun the parent-reported test and lint
commands, contact GitHub, or replay the hosted detector artifact.

Fable 5.1 at xhigh must still review an immutable commit carrying this implementation. This Sol
audit does not accept the release or close the hosted reviewer credential prerequisite.
