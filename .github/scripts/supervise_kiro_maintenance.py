"""Supervise a direct Kiro process without retaining its private transcript."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import selectors
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

from validate_kiro_maintenance_stream import (
    DEADLINE_SECONDS,
    GRACE_SECONDS,
    MAX_REPORT_BYTES,
    AttestationError,
    StreamValidator,
    _json,
    _read_regular,
)


def supervise(
    command: list[str],
    validator: StreamValidator,
    *,
    deadline: float = DEADLINE_SECONDS,
    grace: float = GRACE_SECONDS,
) -> dict[str, Any]:
    """Drain both pipes with bounded reads, and reap on every exit path."""
    canceled = False

    def cancel(signum: int, frame: object) -> None:
        nonlocal canceled
        canceled = True

    previous = {sig: signal.signal(sig, cancel) for sig in (signal.SIGTERM, signal.SIGINT)}
    child: subprocess.Popen[bytes] | None = None
    failure: str | None = None
    stopping: float | None = None
    started = time.monotonic()
    try:
        child = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True
        )
        assert child.stdout is not None and child.stderr is not None
        with selectors.DefaultSelector() as selector:
            for pipe, stderr in ((child.stdout, False), (child.stderr, True)):
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, stderr)
            while selector.get_map() or child.poll() is None:
                now = time.monotonic()
                if failure is None:
                    if canceled:
                        failure = "maintenance-agent-canceled"
                    elif now - started >= deadline:
                        failure = "maintenance-agent-deadline"
                if failure is not None and stopping is None:
                    stopping = now
                    _signal_group(child.pid, signal.SIGTERM)
                if stopping is not None and now - stopping >= grace:
                    break
                for key, _ in selector.select(timeout=0.05):
                    chunk = os.read(key.fd, 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                    elif failure is None:
                        try:
                            validator.feed(chunk, stderr=key.data)
                        except AttestationError as exc:
                            failure = str(exc)
                    else:
                        label = "stderr" if key.data else "stdout"
                        validator.bytes[label] += len(chunk)
                        validator.discarded_bytes[label] += len(chunk)
                # After termination keep draining, but never validate discarded data
                # as successful evidence. The grace deadline also covers descendants.
            if failure is None:
                try:
                    validator.finish(child.wait())
                except AttestationError as exc:
                    failure = str(exc)
    except OSError:
        failure = "maintenance-agent-process-error"
    finally:
        if child is not None:
            # Kill surviving descendants even if the direct process has exited.
            _signal_group(child.pid, signal.SIGKILL)
            child.wait()
            if child.stdout is not None:
                child.stdout.close()
            if child.stderr is not None:
                child.stderr.close()
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    return validator.report(child.returncode if child is not None else None, failure)


def _signal_group(pid: int, sig: signal.Signals) -> None:
    with contextlib.suppress(ProcessLookupError):
        os.killpg(pid, sig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command
    if command[:1] == ["--"]:
        command = command[1:]
    try:
        validator = StreamValidator(
            _json(_read_regular(args.agent, 128 * 1024)), os.environ.get("KIRO_API_KEY", "")
        )
        if not command:
            raise AttestationError("maintenance-agent-process-error")
        report = supervise(command, validator)
        encoded = json.dumps(report, sort_keys=True).encode() + b"\n"
        if len(encoded) > MAX_REPORT_BYTES:
            raise AttestationError("maintenance-agent-report-limit")
        # The shell publishes this fixed-schema result only after Git-state validation.
        with args.result.open("xb") as output:
            output.write(encoded)
        return 0 if report["agent_attestation"] == "passed" else 1
    except (OSError, ValueError):
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
