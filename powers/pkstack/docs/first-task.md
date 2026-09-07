# Try one failing task

The included account-ID example starts broken. Its verifier uses only Python’s
standard library. Work in a disposable copy so the Power’s fixture stays unchanged.

## Prepare the project

Install the Power using the [Kiro installation flow](usage.md#install-the-power).
Copy `examples/verified-goal-demo/` from the Power folder into a disposable
project and open that project in Kiro. Invoke `/pkstack-setup`, review its
preview, and approve the intended workspace changes. Resolve any reported
conflicts before continuing, then select the workspace `pkstack` agent.

The commands below run from that prepared project's root directory.

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

Choose either surface, using the disposable target directory:

- **CLI:** Start a session from the terminal still in that directory:

  ```sh
  kiro-cli chat --v3 --agent pkstack
  ```

- **IDE:** Open the directory printed by `pwd` in Kiro, start a fresh chat or
  Agent Focus session, and select the workspace `pkstack` agent. The terminal
  setup above has already created its workspace assets.

Then send the same request in that session:

```text
/pkstack-verified-goal Repair account ID normalization using the existing goal. Keep the tests unchanged. Remove spaces and hyphens, accept exactly twelve decimal digits, and raise ValueError otherwise. Rerun the stored verifier until it passes or the attempt budget is exhausted.
```

Review Kiro's command and write approval requests. Kiro should edit `account.py`
and rerun the stored command in this conversation. If discovery fails, use the
CLI's bare `/agent` picker and try `/agent swap pkstack` in the same conversation;
then inspect `/config skills`. In the IDE, use its workspace agent picker.
Agent discovery and skill discovery are separate: if newly installed skills
remain absent, open one fresh chat in the same project and select `pkstack` again.
See [the discovery guide](usage.md#attach-the-generated-agent) if the agent itself
is missing.

Check the result yourself in a terminal at the disposable target root:

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

For larger work, [start with native planning](usage.md#plan-and-bind-work).
PKStack uses the shared grilling interview in conversational Plan, Spec, and Quick
Spec workflows. Plan stays read-only until native approval; approved implementation
plans save reusable knowledge at the first permitted write step. For Spec-backed
work, bind its artifacts to a verifier, then publish a reusable feature contract
once the implementation passes.
