# Try one failing task

The included account-ID example starts broken. Its verifier uses only Python’s
standard library. Work in a disposable copy so the Power’s fixture stays unchanged.

## Prepare the project

From a PKStack checkout, save its Power path:

```sh
export PKSTACK_POWER="$PWD/powers/pkstack"
test -f "$PKSTACK_POWER/plugin.json"
```

Copy the example, preview setup, and install into the copy:

```sh
PKSTACK_DEMO=$(mktemp -d "${TMPDIR:-/tmp}/pkstack-demo.XXXXXX")
cp -R "$PKSTACK_POWER/examples/verified-goal-demo/." "$PKSTACK_DEMO/"
cd "$PKSTACK_DEMO"
git init -q
python3 "$PKSTACK_POWER/skills/pkstack-setup/scripts/setup_pkstack.py" \
  --root "$PWD" --dry-run --output json
python3 "$PKSTACK_POWER/skills/pkstack-setup/scripts/setup_pkstack.py" \
  --root "$PWD" --output json
.pkstack/bin/projectctl doctor --output json
```

Setup preserves conflicting user files. If it reports a conflict, stop and
inspect the named path; do not force an overwrite.

## Record the failure

```sh
.pkstack/bin/projectctl goal start "Repair account ID normalization" \
  --command "python3 -m unittest discover -s tests -v" \
  --max-attempts 4 --output json
.pkstack/bin/projectctl goal verify --output json
```

The last command should exit **1**, report failed tests, and leave the goal
`active`. Keep the tests unchanged: they are the acceptance criteria.

## Repair in Kiro

Start a session in that directory:

```sh
kiro-cli chat --v3 --agent pkstack
```

Then ask:

```text
/pkstack-verified-goal Repair account ID normalization using the existing goal. Keep the tests unchanged. Remove spaces and hyphens, accept exactly twelve decimal digits, and raise ValueError otherwise. Rerun the stored verifier until it passes or the attempt budget is exhausted.
```

Kiro should edit `account.py` and rerun the stored command in this conversation.
Check the result yourself:

```sh
.pkstack/bin/projectctl goal status --output json
python3 -m unittest discover -s tests -v
```

Success means stored status `passed`, a failing attempt followed by a passing
attempt, and all four tests passing. An `exhausted` goal is unfinished; inspect
the failure before explicitly adding attempts.

The runner screens common hazards but is not an OS sandbox. Review verifiers
before approving execution. `/pkstack-verified-goal` is a PKStack skill, not
Kiro’s native `/goal`.

For larger work, [start with a native Spec or Quick Spec](usage.md#plan-and-bind-work).
Bind its artifacts to a verifier, then publish a reusable feature contract once
the implementation passes.
