# Astral Python and Auto acceptance

This candidate ports Astral's `uv`, `ruff`, and `ty` guidance into the Kiro Power, adds
repository-only `CLAUDE.md -> AGENTS.md`, and distinguishes selected Auto from an undisclosed
underlying model. It does not tag or publish a release.

## Native Python exercise

Kiro CLI v3 session `sess_2d246c91-592f-42a0-846c-d0aa5202418f` ran with **Auto** selected.
It read all three installed skills, corrected lint/format/type failures in `greet.py`, and
preserved the greeting behavior for whitespace, empty, and Unicode names. Ruff check,
Ruff format --check, ty, and runtime assertions passed through the existing feature verifier.
The coordinator independently reran that verifier and checked the source diff and global
Kiro settings hash. Only `greet.py` source changed; Python regenerated one tracked bytecode
cache file in the disposable fixture.

The first non-interactive attempt could not approve skill disclosure or file edits. It read
the skills directly, diagnosed the failures, and stopped without repairing the file. The
same session resumed interactively; one `fs_write` request for `greet.py` received Allow.
There was no persistent permission change. This is bounded CLI evidence, not a claim about
all models, all tasks, the IDE, or zero-intervention operation.

[Native summary](native-summary.json), [skill reads](native-skill-read-excerpts.json),
[original failure](native-baseline.json), [final host verifier](native-host-final.json),
and [native final prose](native-final-text.txt) retain the evidence. Raw logs are retained
locally at the hash-bound paths in the summary. Native prose says the controller persisted
a receipt; the actual command returns a result, whose stdout the coordinator retained.
No internal receipt persistence is claimed. The underlying Auto model remains undisclosed.

## Source and deterministic checks

[Astral pin](astral-pin.json) records the verified commit; the Power's provenance inventory
binds the original plugin subtree, and per-skill manifests bind the adapted bytes. The three
wrappers passed skill validation. Source-inventory, installation/idempotency, model-output,
Kiro assets, packaging, and README targeted checks passed (150 tests). The corrected candidate
`d36bb88b2f10e3103060ecbad0c1053ccba5564e` passed all ten full local lanes: **974 Power tests and
234 repository unit tests**, plus Ruff lint/format, ty, workflow/shell checks, maintenance guards,
and local knowledge validation. The first full run found one stale bootstrap steering inventory
assertion; its expected list was corrected and the full gate rerun successfully.

[Python coverage](python-coverage.md) describes maintained surfaces and exclusions.
[Full gate summary](full-gate-summary.json) binds the commit, command, counts, and receipt hashes.
The native exercise used the same final skill bytes; later bootstrap inventory, test, and root
static-checker changes were outside the code exercised by that native fixture. Independent review
is pending; no review verdict is implied by the green local gate.
