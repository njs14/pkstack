from __future__ import annotations

import os
import pty
import select
import signal
import stat
import subprocess
import time
from pathlib import Path

import pytest

POWER = Path(__file__).resolve().parents[1] / "powers/pkstack"
TEMPLATE = POWER / "skills/wizard/template.sh"
HITL = POWER / "skills/diagnosing-bugs/scripts/hitl-loop.template.sh"


def run_shell(tmp_path: Path, body: str, *, text: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-c", 'source "$1"\n' + body, "wizard-test", str(TEMPLATE)],
        cwd=tmp_path,
        input=text,
        capture_output=True,
        text=True,
        env={**os.environ, "ENV_FILE": str(tmp_path / "values.env")},
        timeout=10,
    )


def test_literal_values_round_trip_without_execution_and_repeat_is_idempotent(tmp_path: Path):
    secret = "  quote' \" $(touch PWNED) `touch PWNED2` ${HOME} \\ space # = ; & "
    body = 'ask_secret API_TOKEN "Token"\nwrite_env API_TOKEN "$API_TOKEN"\n'
    result = run_shell(tmp_path, body, text=secret + "\n")
    assert result.returncode == 0, result.stderr
    assert secret not in result.stdout + result.stderr
    target = tmp_path / "values.env"
    original = target.read_bytes()
    original_stat = target.stat()
    assert stat.S_IMODE(original_stat.st_mode) == 0o600
    repeat = run_shell(tmp_path, body, text="\n")
    assert repeat.returncode == 0, repeat.stderr
    assert target.read_bytes() == original
    assert target.stat().st_mtime_ns == original_stat.st_mtime_ns
    value = subprocess.run(
        ["bash", "-c", 'source "$1"; printf "%s" "$API_TOKEN"', "read-literal", str(target)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    assert value.stdout == secret
    assert not (tmp_path / "PWNED").exists()
    assert not (tmp_path / "PWNED2").exists()
    assert not list(tmp_path.glob(".*.env.*"))
    assert not list(tmp_path.glob("*.wizard-lock"))


def test_updates_preserve_other_lines_and_collapse_duplicate_keys(tmp_path: Path):
    target = tmp_path / "values.env"
    target.write_text("# local settings\nOTHER=preserved\nAPI_TOKEN=one\nAPI_TOKEN=two\n")
    result = run_shell(tmp_path, "write_env API_TOKEN replacement")
    assert result.returncode == 0, result.stderr
    assert target.read_text() == "# local settings\nOTHER=preserved\nAPI_TOKEN=replacement\n"
    assert stat.S_IMODE(target.stat().st_mode) == 0o600


@pytest.mark.parametrize("key", ["PATH", "HOME", "BASH_ENV", "ENV_FILE", "A[$(touch PWNED)]"])
def test_reserved_or_executable_variable_names_are_rejected(tmp_path: Path, key: str):
    result = run_shell(
        tmp_path, 'IFS= read -r key\nask_secret "$key" "Value"', text=key + "\nsecret\n"
    )
    assert result.returncode != 0
    assert not (tmp_path / "values.env").exists()
    assert not (tmp_path / "PWNED").exists()


def test_failed_write_in_conditional_cannot_report_success(tmp_path: Path):
    target = tmp_path / "values.env"
    destination = tmp_path / "untouched"
    destination.write_text("do not change")
    target.symlink_to(destination)
    result = run_shell(tmp_path, "if write_env API_TOKEN value; then exit 99; else exit 7; fi")
    assert result.returncode == 7
    assert "Saved" not in result.stdout
    assert destination.read_text() == "do not change"
    assert not list(tmp_path.glob("*.wizard-lock"))


def test_existing_nonliteral_input_is_never_executed(tmp_path: Path):
    target = tmp_path / "values.env"
    target.write_text("API_TOKEN=$(touch PWNED)\n")
    result = run_shell(tmp_path, 'ask_secret API_TOKEN "Token"', text="\n")
    assert result.returncode != 0
    assert not (tmp_path / "PWNED").exists()
    assert target.read_text() == "API_TOKEN=$(touch PWNED)\n"


def test_eof_keeps_saved_file_and_does_not_finish(tmp_path: Path):
    target = tmp_path / "values.env"
    target.write_text("API_TOKEN=saved\n")
    result = run_shell(
        tmp_path,
        'TOTAL_STAGES=1\nstage "input"\nask_secret API_TOKEN "Token"\n'
        'write_env API_TOKEN "$API_TOKEN"\nfinish',
    )
    assert result.returncode != 0
    assert target.read_text() == "API_TOKEN=saved\n"
    assert "stages completed" not in result.stdout
    assert "incomplete" in result.stderr


def read_until(fd: int, marker: bytes) -> bytes:
    result = b""
    deadline = time.monotonic() + 5
    while marker not in result and time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], 0.1)
        if ready:
            try:
                result += os.read(fd, 4096)
            except OSError:
                break
    assert marker in result, result
    return result


def test_secret_input_is_hidden_on_a_real_terminal(tmp_path: Path):
    master, slave = pty.openpty()
    process = subprocess.Popen(
        [
            "bash",
            "-c",
            'source "$1"; ask_secret API_TOKEN Token; '
            'write_env API_TOKEN "$API_TOKEN"; printf DONE',
            "test",
            str(TEMPLATE),
        ],
        cwd=tmp_path,
        stdin=slave,
        stdout=slave,
        stderr=slave,
        env={**os.environ, "ENV_FILE": str(tmp_path / "values.env")},
    )
    os.close(slave)
    try:
        output = read_until(master, b"Token: ")
        os.write(master, b"PTY_SECRET_SENTINEL\n")
        output += read_until(master, b"DONE")
        assert process.wait(timeout=5) == 0
        assert b"PTY_SECRET_SENTINEL" not in output
        assert "PTY_SECRET_SENTINEL" in (tmp_path / "values.env").read_text()
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master)


def test_interrupt_before_input_does_not_write_or_finish(tmp_path: Path):
    process = subprocess.Popen(
        [
            "bash",
            "-c",
            'source "$1"; ask_secret API_TOKEN Token; write_env API_TOKEN "$API_TOKEN"; finish',
            "test",
            str(TEMPLATE),
        ],
        cwd=tmp_path,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        assert process.stdout is not None
        read_until(process.stdout.fileno(), b"Token: ")
        os.killpg(process.pid, signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == 143
        assert b"stages completed" not in stdout
        assert b"incomplete" in stderr
        assert not (tmp_path / ".wizard.env").exists()
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def test_account_helper_requires_explicit_target_and_uses_stdin(tmp_path: Path):
    stub = tmp_path / "bin"
    stub.mkdir()
    command = stub / "gh"
    command.write_text('#!/bin/bash\nprintf "%s\\n" "$@" > "$TEST_ARGS"\ncat > "$TEST_STDIN"\n')
    command.chmod(0o755)
    body = """
export PATH="$PWD/bin:$PATH"
export TEST_ARGS="$PWD/args" TEST_STDIN="$PWD/stdin"
if set_secret API_TOKEN secret; then exit 99; fi
[[ ! -e "$TEST_ARGS" ]]
export WIZARD_ALLOW_GITHUB_WRITES=1 WIZARD_GITHUB_REPOSITORY=example/project
set_secret API_TOKEN secret
"""
    result = run_shell(tmp_path, body)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "args").read_text().splitlines() == [
        "secret",
        "set",
        "API_TOKEN",
        "--repo",
        "example/project",
    ]
    assert (tmp_path / "stdin").read_text() == "secret"
    assert "secret" not in result.stdout + result.stderr


def test_human_observation_loop_eof_has_no_verdict(tmp_path: Path):
    result = subprocess.run(
        ["bash", str(HITL)], cwd=tmp_path, input="", text=True, capture_output=True, timeout=5
    )
    assert result.returncode != 0
    assert "OBS_RESULT=" not in result.stdout
