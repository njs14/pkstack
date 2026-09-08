"""Exercise the actual pipe supervisor with local processes, never a model."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

import supervise_kiro_maintenance as supervisor
import validate_kiro_maintenance_stream as stream
from test_validate_kiro_maintenance_stream import PROFILE, attested_events, envelope, stream_bytes


class SupervisorTests(unittest.TestCase):
    def run_child(self, body: str, *, deadline: float = 10, grace: float = 0.1):
        validator = stream.StreamValidator(PROFILE, "credential-sentinel-value")
        prefix = stream_bytes(attested_events()[:3])
        suffix = stream_bytes(attested_events()[-1:])
        code = (
            "import os, signal, sys, time\n"
            f"prefix = {prefix!r}\nsuffix = {suffix!r}\n"
            "def write(data, fd=1):\n"
            "    while data:\n"
            "        count = os.write(fd, data)\n"
            "        data = data[count:]\n" + body
        )
        started = time.monotonic()
        report = supervisor.supervise(
            [sys.executable, "-c", code], validator, deadline=deadline, grace=grace
        )
        self.assertLess(time.monotonic() - started, deadline + grace + 3)
        self.assertLessEqual(len(validator.buffer), stream.MAX_EVENT_BYTES + 65536)
        self.assertLess(len(json.dumps(report).encode()), stream.MAX_REPORT_BYTES)
        self.assertNotIn("credential-sentinel-value", json.dumps(report))
        return report

    def test_large_valid_stream_and_interleaved_stderr_have_complete_counters(self):
        event = stream_bytes(
            [envelope({"sessionUpdate": "tool_call_update", "content": "x" * 65536})]
        )
        report = self.run_child(
            f"write(prefix)\nevent = {event!r}\n"
            "for _ in range(300):\n    write(event)\n    write(b'diagnostic\\n', 2)\n"
            "write(suffix)\n"
        )
        self.assertEqual(report["agent_attestation"], "passed")
        self.assertGreater(report["bytes"]["stdout"], 16 * 1024 * 1024)
        self.assertEqual(report["bytes"]["stderr"], 300 * len(b"diagnostic\n"))
        self.assertEqual(report["event_counts"]["tool_call_update"], 300)
        self.assertEqual(sum(report["event_bytes"].values()), report["bytes"]["stdout"])
        self.assertEqual(report["candidate_acceptance"], "not-evaluated")

    def test_late_malformed_secret_and_cross_session_cannot_pass(self):
        event = stream_bytes(
            [envelope({"sessionUpdate": "tool_call_update", "content": "x" * 65536})]
        )
        cross = attested_events()[3]
        cross["data"]["sessionId"] = "sess_00000000-0000-4000-8000-000000000099"
        for late, reason in (
            (b'{"broken":NaN}\n', "stream-invalid"),
            (stream_bytes([cross]), "session-mismatch"),
            (
                stream_bytes(
                    [
                        envelope(
                            {
                                "sessionUpdate": "agent_message_chunk",
                                "text": "credential-sentinel-value",
                            }
                        )
                    ]
                ).replace(b"credential", b"cred\\u0065ntial"),
                "secret-detected",
            ),
        ):
            with self.subTest(reason=reason):
                report = self.run_child(
                    f"write(prefix)\nevent = {event!r}\n"
                    "for _ in range(260):\n    write(event)\n"
                    f"write({late!r})\nwrite(suffix)\n"
                )
                self.assertEqual(report["reason"], "maintenance-agent-" + reason)
                self.assertEqual(report["agent_attestation"], "failed")

    def test_stdout_stderr_event_and_event_count_limits(self):
        small = stream_bytes([envelope({"sessionUpdate": "tool_call_update"})])
        medium = stream_bytes(
            [envelope({"sessionUpdate": "tool_call_update", "text": "x" * 65536})]
        )
        cases = (
            ("write(prefix)\nwhile True: write(b'x' * 65536)\n", "event-byte-limit"),
            ("write(prefix)\nwhile True: write(b'x' * 65536, 2)\n", "stderr-limit"),
            (
                f"write(prefix)\nevent = {small!r}\nwhile True: write(event * 100)\n",
                "event-count-limit",
            ),
            (f"write(prefix)\nevent = {medium!r}\nwhile True: write(event)\n", "stdout-limit"),
        )
        for body, reason in cases:
            with self.subTest(reason=reason):
                report = self.run_child(body)
                self.assertEqual(report["reason"], "maintenance-agent-" + reason)
                self.assertIsNotNone(report["process_exit_status"])

    def test_timeout_cancellation_and_ignored_termination_reap_child(self):
        with tempfile.TemporaryDirectory() as directory:
            pid_path = Path(directory) / "pid"
            for canceled, ignores in ((False, False), (False, True), (True, True)):
                with self.subTest(canceled=canceled, ignores=ignores):
                    body = f"open({str(pid_path)!r}, 'w').write(str(os.getpid()))\n"
                    if ignores:
                        body += "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                    if canceled:
                        body += "os.kill(os.getppid(), signal.SIGTERM)\n"
                    body += "time.sleep(60)\n"
                    report = self.run_child(body, deadline=0.2)
                    self.assertEqual(
                        report["reason"],
                        "maintenance-agent-canceled" if canceled else "maintenance-agent-deadline",
                    )
                    with self.assertRaises(ProcessLookupError):
                        os.kill(int(pid_path.read_text()), 0)
                    self.assertEqual(list(Path(directory).iterdir()), [pid_path])

    def test_terminal_event_does_not_replace_successful_exit(self):
        report = self.run_child("write(prefix)\nwrite(suffix)\nraise SystemExit(7)\n")
        self.assertTrue(report["terminal_event_present"])
        self.assertEqual(report["process_exit_status"], 7)
        self.assertEqual(report["reason"], "maintenance-agent-run-failed")


if __name__ == "__main__":
    unittest.main()
