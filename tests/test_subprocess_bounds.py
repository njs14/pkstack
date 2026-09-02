from __future__ import annotations

import subprocess
import sys
import time

import pytest

from pk_stack_lab import cli


def _python(source: str, *, timeout: float = 5) -> str:
    return cli._run(
        [sys.executable, "-I", "-c", source],
        timeout=timeout,
        bind_socket=False,
    )


def test_run_kills_child_as_soon_as_stdout_exceeds_byte_limit() -> None:
    source = f"import os; os.write(1, b'x' * {cli.MAX_READ + 1})"

    with pytest.raises(cli.LabError, match=rf"output exceeded {cli.MAX_READ} bytes"):
        _python(source)


def test_run_drains_and_discards_huge_stderr_on_success() -> None:
    source = (
        "import os\n"
        "for _ in range(64): os.write(2, b'e' * 65536)\n"
        "os.write(1, b'ok\\n')\n"
    )

    assert _python(source) == "ok\n"


def test_run_bounds_nonzero_stderr_diagnostic_while_draining() -> None:
    source = (
        "import os\n"
        "os.write(2, b'BEGIN_DIAGNOSTIC ')\n"
        "for _ in range(64): os.write(2, b'x' * 65536)\n"
        "os.write(2, b'TAIL_MUST_BE_DISCARDED')\n"
        "raise SystemExit(7)\n"
    )

    with pytest.raises(cli.LabError) as raised:
        _python(source)

    message = str(raised.value)
    assert "BEGIN_DIAGNOSTIC" in message
    assert "TAIL_MUST_BE_DISCARDED" not in message
    assert len(message.encode("utf-8")) < 1200


def test_run_timeout_kills_and_reaps_child(monkeypatch: pytest.MonkeyPatch) -> None:
    real_popen = subprocess.Popen
    children: list[subprocess.Popen[bytes]] = []

    def recording_popen(*args: object, **kwargs: object) -> subprocess.Popen[bytes]:
        child = real_popen(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(cli.subprocess, "Popen", recording_popen)
    started = time.monotonic()

    with pytest.raises(cli.LabError, match="command failed"):
        _python("import signal; signal.pause()", timeout=0.1)

    assert time.monotonic() - started < 2
    assert len(children) == 1
    assert children[0].poll() is not None


def test_run_rejects_non_utf8_success_stdout() -> None:
    with pytest.raises(cli.LabError, match="invalid UTF-8"):
        _python("import os; os.write(1, b'\\xff')")
