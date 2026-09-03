# PK-Stack representative skill-route campaign

Status: **PASS**

This bounded local campaign closes the representative route-exercise portion of `SKL-005` and
`FBL-043`. It exercised one route in each catalog disposition without network access, credentials,
or an interactive model turn. The executable regression is
`tests/test_skill_route_campaign.py`; the full machine record is
[`skill-route-campaign.json`](skill-route-campaign.json).

## Source and asset boundary

The run began from commit `491bfdafc94832c6624ed86051955b1067245979` (tree
`e314bd4ab33e492b905a080b43c4ea8bdfba6828`). File-level hashes bind the exercised routes to the
working tree rather than pretending this new evidence already existed in that commit.

- Authoritative catalog: `powers/pk-stack/docs/upstream-skill-parity.json`
- Catalog SHA-256: `0d5e0adacf03c5497cb5549ea79dad78e43dd9c8135f3cd46f75cea032678d04`
- Upstream identities: accepted pin `efa2a531985e0a8084d36ff3cf87233be8a9f34b`; reviewed current
  `7314f723a487ec406b6369fe5865ba034cfed166`
- Complete catalog: 45 upstream names: 17 direct ports, 23 alias/consolidations, four native Kiro
  replacements, and one exclusion. Forty-four names are runnable; the current target distribution
  contains 49 canonical/controller-cache skills after the five PK-Stack-only skills are included,
  and 48 live workspace skills because `setup-pstack` remains Power-local. The five PK-Stack-only
  skills are `maintain-pk-stack`, `model-council`, `okf`, `principles`, and `verified-goal`.

The refreshed inventory binds the sorted canonical and controller-cache name lists to
`00f668664309f0fd6fef86215acde275bd96ab861e8ba1e369e8cf5db5afc7fa` and the live name list to
`6ffe81f18eb18bc3f05e62d5b149fee22b8b6d88f8f58e2f488f92aeffc1ace4`. The canonical, live, and
controller-cache copies of `/okf` are byte-identical at
`68fb857520b388e4db826dfc5c8e3eb51007b14b9564f345520f0e926c33c5b2`.

For every runnable representative, the regression compares the canonical Power bytes with the
generated `.kiro` and `.pstack/projectctl` bytes that should exist for that route. `setup-pstack` is
the intentional exception: its canonical and controller-cache copies match, while its live
`.kiro/skills` copy is absent because setup is a Power-local pre-bootstrap/refresh entrypoint.

## Exercises

| Class | Representative | Exercise and observation |
|---|---|---|
| Direct port | `create-verification-skill` | In a fresh bootstrapped workspace, generated a three-record schema-2 map, proved only `route-contract`, validated the map, and explicitly verified `route-contract` again. The call log was exactly `route-contract`, `route-contract`; the other two drafts never ran. |
| Alias/consolidation | `principle-prove-it-works` | Bound the leaf skill to the shared `principles` catalog, then ran the same file-content predicate red and green. It exited 9 when the claimed artifact was absent and 0 only when the exact artifact existed. |
| Native replacement | `setup-pstack` | Ran the Power-local shim as a dry-run, applied setup, ran it again, compared the two ownership receipts byte for byte, and ran the generated controller's doctor. The repeat created and updated nothing; doctor reported zero failures. |
| Explicit exclusion | `make-bot-ui` | Resolved the exact name through the catalog to `excluded` with a null target, then proved there is no canonical, live, or cached runnable directory. The safe `architect` alternative exists byte-identically in all three routed locations, but was only discovered because this fixture has no real bot-UI target to design. |

The relevant byte bindings were:

- `create-verification-skill/SKILL.md`:
  `ef3ef4bd660db592db5e3859f8b215342f3274a0d4babe624ece78e160bff360`
- `principle-prove-it-works/SKILL.md`:
  `0df85a89aa5412932fd7f995a954a89daaa040c483a998f9002b6f79788a5131`
- shared `principles/references/catalog.md`:
  `1c76ba2e63baa5eaa4d634db1a979e23a6cceeb70792971353aacde4fb41e608`
- `setup-pstack/SKILL.md`:
  `e5db11e0a1c5af1d620347edcf3dac576e8ac1a6e46b6c740a83f101ec63e758`
- `setup-pstack/scripts/setup_pstack.py`:
  `2d33cef88df074dea8f80f31c8c08b6a5db5644b0e4f2b5d970d117636937e84`
- safe alternative `architect/SKILL.md`:
  `0114f1cec2e8c07b625cf52c0188aebba5ee33c9bd0b389d39f5e7f2723d7382`
- PK-Stack-only `okf/SKILL.md` (canonical, live, and controller cache):
  `68fb857520b388e4db826dfc5c8e3eb51007b14b9564f345520f0e926c33c5b2`

## Exact command and result

Run from the repository root:

```bash
env PYTHONDONTWRITEBYTECODE=1 UV_OFFLINE=1 uv run --locked --no-config --no-sync pytest -p no:cacheprovider tests/test_skill_route_campaign.py -q
```

Result:

```text
..                                                                       [100%]
2 passed in 14.27s
```

The regression creates a pytest-owned temporary workspace and instantiates these route commands
there:

```text
python <Power>/skills/setup-pstack/scripts/setup_pstack.py --root <workspace> --dry-run --output json
python <Power>/skills/setup-pstack/scripts/setup_pstack.py --root <workspace> --output json
python <Power>/skills/setup-pstack/scripts/setup_pstack.py --root <workspace> --output json
<workspace>/.pstack/bin/projectctl doctor --output json
<workspace>/.pstack/bin/projectctl feature generate-map skill-route-feature-plan.json --representative route-contract --output json
<workspace>/.pstack/bin/projectctl feature validate --output json
<workspace>/.pstack/bin/projectctl feature verify route-contract --output json
python claim_probe.py
```

All setup/controller subprocesses inherited `UV_OFFLINE=1`; no campaign step read a secret or used a
network client.

## Claim boundary

This is direct local invocation proof for the setup and projectctl workflows, a deterministic
semantic replay for the consolidated principle, and a static/discovery safety proof for the
excluded route. It is not an interactive Kiro skill-selection transcript and does not claim that a
model followed the skill text. The excluded path is intentionally not invocable; exercising it
means proving resolution refuses it before any host, secret, or network action. Kiro Web remains
supported by committed asset design and untested.
