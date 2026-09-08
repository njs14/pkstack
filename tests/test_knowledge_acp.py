from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
from acp import connect_to_agent
from acp._transport import NdjsonTransport, memory_transport_pair
from acp.schema import AgentMessageChunk, TextContentBlock, ToolCallStart

from pkstack import knowledge_acp as worker
from pkstack import knowledge_runtime_bridge as bridge
from pkstack.knowledge_payload import KnowledgeRuntimeError


@pytest.mark.parametrize("terminated", [True, False])
@pytest.mark.parametrize("kind", ["agent_thought_chunk", "tool_call", "extension", "malformed"])
def test_sdk_cannot_assemble_an_oversized_protocol_frame(terminated: bool, kind: str) -> None:
    async def exercise() -> None:
        client = worker._Client()
        stream = asyncio.StreamReader(limit=worker.MAX_PROTOCOL_FRAME_BYTES)
        reader = worker._BoundedReader(stream, client)
        transport = NdjsonTransport(reader, Mock())
        frame = json.dumps({"kind": kind, "data": "x" * worker.MAX_PROTOCOL_FRAME_BYTES}).encode()
        stream.feed_data(frame + (b"\n" if terminated else b""))
        stream.feed_eof()
        with pytest.raises(KnowledgeRuntimeError, match="protocol frame"):
            await asyncio.wait_for(transport.receive(), 1)
        assert client.failed.is_set()
        assert client.text == []
        assert client.text_bytes == 0

    asyncio.run(exercise())


def test_sdk_counts_ignored_frames_toward_the_aggregate_wire_limit() -> None:
    async def exercise() -> None:
        client = worker._Client()
        stream = asyncio.StreamReader(limit=worker.MAX_PROTOCOL_FRAME_BYTES)
        reader = worker._BoundedReader(stream, client)
        transport = NdjsonTransport(reader, Mock())
        frame = (
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "method": "session/update",
                    "params": {
                        "sessionId": "test",
                        "update": {
                            "sessionUpdate": "agent_thought_chunk",
                            "content": {"type": "text", "text": "x" * 900_000},
                        },
                    },
                }
            ).encode()
            + b"\n"
        )
        assert len(frame) < worker.MAX_PROTOCOL_FRAME_BYTES
        count = worker.MAX_PROTOCOL_BYTES // len(frame)
        for _ in range(count):
            stream.feed_data(frame)
            assert await transport.receive() is not None
        assert reader.wire_bytes == count * len(frame)
        assert client.failure is None
        stream.feed_data(frame)
        with pytest.raises(KnowledgeRuntimeError, match="aggregate"):
            await transport.receive()
        assert client.text == []
        assert client.text_bytes == 0

    asyncio.run(exercise())


def test_bounded_reader_preserves_sdk_frames_and_counts_eof_tail() -> None:
    async def exercise() -> None:
        client = worker._Client()
        stream = asyncio.StreamReader(limit=worker.MAX_PROTOCOL_FRAME_BYTES)
        reader = worker._BoundedReader(stream, client)
        transport = NdjsonTransport(reader, Mock())
        stream.feed_data(b'\n{"first":1}\n{"tail":2}')
        stream.feed_eof()
        assert await transport.receive() == {"first": 1}
        assert await transport.receive() == {"tail": 2}
        assert await transport.receive() is None
        assert reader.wire_bytes == len(b'\n{"first":1}\n{"tail":2}')
        assert client.failure is None

    asyncio.run(exercise())


def test_nonreading_peer_cannot_stall_prompt_cancellation_and_cleanup(tmp_path: Path) -> None:
    peer = """import json,sys,time
for _ in range(4):
    request = json.loads(sys.stdin.readline())
    method = request['method']
    if method == 'initialize':
        result = {'protocolVersion':1,'agentCapabilities':{},'authMethods':[]}
    elif method == 'session/new':
        result = {'sessionId':'test'}
    elif method == 'session/set_mode':
        result = {}
        print(json.dumps({'jsonrpc':'2.0','method':'_kiro/tools/didChange',
            'params':{'tags':[{'tag':'read'}]}}),flush=True)
    elif method == 'session/set_config_option':
        result = {'configOptions':[{'id':'model','name':'Model','type':'select',
            'currentValue':'auto','options':[{'value':'auto','name':'Auto'}]}]}
    else:
        raise RuntimeError(method)
    print(json.dumps({'jsonrpc':'2.0','id':request['id'],'result':result}),flush=True)
time.sleep(30)
"""

    async def exercise() -> None:
        actual_spawn = asyncio.create_subprocess_exec
        owned: list[asyncio.subprocess.Process] = []

        async def spawn(*args: object, **kwargs: Any) -> asyncio.subprocess.Process:
            process = await actual_spawn(sys.executable, "-c", peer, **kwargs)
            owned.append(process)
            return process

        try:
            with (
                patch.object(worker.asyncio, "create_subprocess_exec", spawn),
                pytest.raises(KnowledgeRuntimeError, match="timed out"),
            ):
                await asyncio.wait_for(
                    worker._run("unused", tmp_path, tmp_path, "x" * 500_000, {}, 1200, "auto", 0.1),
                    12,
                )
            assert len(owned) == 1
            assert owned[0].returncode is not None
            with pytest.raises(ProcessLookupError):
                os.killpg(owned[0].pid, 0)
        finally:
            for process in owned:
                if process.returncode is None:
                    os.killpg(process.pid, signal.SIGKILL)
                    await process.wait()

    asyncio.run(exercise())


def test_broken_transport_cannot_skip_owned_process_cleanup(tmp_path: Path) -> None:
    async def exercise() -> None:
        actual_spawn = asyncio.create_subprocess_exec
        original_cleanup = worker._cleanup
        owned: list[asyncio.subprocess.Process] = []
        cleaned: list[int] = []

        async def spawn(*args: object, **kwargs: object) -> asyncio.subprocess.Process:
            process = await actual_spawn(
                sys.executable,
                "-c",
                "import os,time; os.close(0); time.sleep(30)",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                start_new_session=True,
            )
            owned.append(process)
            await asyncio.sleep(0.15)
            return process

        async def cleanup(process: asyncio.subprocess.Process) -> None:
            cleaned.append(process.pid)
            await original_cleanup(process)

        try:
            with (
                patch.object(worker.asyncio, "create_subprocess_exec", spawn),
                patch.object(worker, "_cleanup", cleanup),
                pytest.raises(KnowledgeRuntimeError),
            ):
                await asyncio.wait_for(
                    worker._run("unused", tmp_path, tmp_path, "question", {}, 1200, "auto", 1),
                    12,
                )
            assert len(cleaned) == 1
            assert all(process.returncode is not None for process in owned)
            for process in owned:
                with pytest.raises(ProcessLookupError):
                    os.killpg(process.pid, 0)
        finally:
            for process in owned:
                if process.returncode is None:
                    os.killpg(process.pid, signal.SIGKILL)
                    await process.wait()

    asyncio.run(exercise())


def test_malformed_sdk_message_is_rejected_without_leaking_unvalidated_content() -> None:
    async def exercise() -> None:
        output = io.StringIO()
        handler = logging.StreamHandler(output)
        logger = logging.getLogger()
        logger.addHandler(handler)
        original_handlers, original_filters = list(logger.handlers), list(logger.filters)
        left, right = memory_transport_pair()
        client = worker._Client()
        try:
            with worker._sdk_logging(client):
                connection = connect_to_agent(client, left)
                logging.warning("UNRELATED_APPLICATION_DIAGNOSTIC")
                await right.send(
                    {
                        "jsonrpc": "2.0",
                        "method": "session/update",
                        "params": {
                            "sessionId": "test",
                            "update": {
                                "sessionUpdate": "agent_message_chunk",
                                "content": {
                                    "type": "text",
                                    "text": {"secret": "UNVALIDATED_CONTEXT_CANARY"},
                                },
                            },
                        },
                    }
                )
                await asyncio.wait_for(client.failed.wait(), 1)
                await connection.close()
                await right.close()
            assert "UNVALIDATED_CONTEXT_CANARY" not in output.getvalue()
            assert "UNRELATED_APPLICATION_DIAGNOSTIC" in output.getvalue()
            assert client.failure
            assert logger.handlers == original_handlers
            assert logger.filters == original_filters
        finally:
            logger.removeHandler(handler)

    asyncio.run(exercise())


def test_caller_credentials_and_runtime_overrides_are_not_forwarded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for key in (
        "KIRO_API_KEY",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "NODE_OPTIONS",
        "PYTHONPATH",
        "KIRO_KAS_SERVER_PATH",
        "CLOUD_CONFIG_ENDPOINT",
    ):
        monkeypatch.setenv(key, "MUST_NOT_FORWARD")
    environment = worker._environment(tmp_path)
    assert "MUST_NOT_FORWARD" not in json.dumps(environment)
    assert environment["HOME"] == os.environ["HOME"]
    assert environment["PKSTACK_KNOWLEDGE_WORKER"] == "1"
    assert Path(environment["KIRO_KAS_NODE_PATH"]).is_file()


@pytest.mark.parametrize(
    "method,params",
    [
        ("kiro/steering/documents_changed", {"documents": [{"uri": "file:///untrusted.md"}]}),
        ("kiro/mcp/status", {"servers": [{"name": "untrusted"}]}),
        ("kiro/powers/items_changed", {"powers": [{"name": "untrusted"}]}),
        ("kiro/policy/changed", {"errors": [{"message": "invalid rule"}]}),
        ("kiro/customAgent/config_error", {}),
    ],
)
def test_unexpected_configuration_fails_the_task(method: str, params: dict[str, object]) -> None:
    client = worker._Client()
    asyncio.run(client.ext_notification(method, params))
    assert client.failure


def test_live_tool_scope_cannot_expand_and_response_capture_is_bounded() -> None:
    async def exercise() -> None:
        client = worker._Client()
        client.prompting = True
        await client.ext_notification("kiro/tools/didChange", {"tags": [{"tag": "shell"}]})
        assert client.failure
        client = worker._Client()
        await client.session_update(
            "session",
            AgentMessageChunk(
                content=TextContentBlock(type="text", text="x" * (worker.MAX_RESPONSE_BYTES + 1)),
                session_update="agent_message_chunk",
            ),
        )
        assert client.failure
        assert client.text == []

    asyncio.run(exercise())


def test_recursive_worker_invocation_is_rejected_before_runtime_discovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PKSTACK_KNOWLEDGE_WORKER", "1")
    with pytest.raises(KnowledgeRuntimeError, match="recursive"):
        worker.search(tmp_path, "question")


@pytest.mark.parametrize(
    "options",
    [
        {"query": ""},
        {"query": "x" * 8001},
        {"budget": 63},
        {"budget": True},
        {"model": "bad model"},
        {"timeout_seconds": 121},
    ],
)
def test_invalid_input_fails_before_a_model_turn(
    tmp_path: Path,
    options: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    arguments: dict[str, Any] = {"query": "question", **options}

    def unexpected_runtime_probe(root: Path) -> None:
        raise AssertionError("invalid input reached runtime discovery")

    monkeypatch.setattr(worker, "runtime_status", unexpected_runtime_probe)
    with pytest.raises(KnowledgeRuntimeError):
        worker.search(tmp_path, **arguments)


def test_bridge_resolves_only_the_verified_bundled_server(tmp_path: Path) -> None:
    package = tmp_path / "kas/version/node_modules/@kiro/agent"
    server = package / "dist/server/acp-server.js"
    server.parent.mkdir(parents=True)
    server.write_text("// fixture")
    metadata = package / "package.json"
    metadata.write_text(json.dumps({"name": "@kiro/agent", "version": bridge.KAS_VERSION}))
    node = tmp_path / "node"
    node.write_text("#!/bin/sh\nexit 0\n")
    node.chmod(0o700)
    arguments = [
        "--experimental-wasm-modules",
        str(server),
        "--transport=stdio",
        "--auth=acp-callback",
    ]
    assert bridge.resolve_node(arguments) == node.resolve()
    with pytest.raises(ValueError, match="launch options changed"):
        bridge.resolve_node([*arguments, "--unreviewed=true"])
    metadata.write_text(json.dumps({"name": "@kiro/agent", "version": "999.0.0"}))
    with pytest.raises(ValueError, match="unverified"):
        bridge.resolve_node(arguments)


def test_progress_before_read_is_separate_from_final_answer_but_remains_bounded() -> None:
    async def exercise() -> None:
        client = worker._Client()
        client.prompting = True
        await client.session_update(
            "test",
            AgentMessageChunk(
                session_update="agent_message_chunk",
                content=TextContentBlock(type="text", text="Reading."),
            ),
        )
        await client.session_update(
            "test",
            ToolCallStart(
                session_update="tool_call", tool_call_id="one", title="Read", kind="read"
            ),
        )
        assert client.text == []
        assert client.text_bytes == len("Reading.")
        await client.session_update(
            "test",
            AgentMessageChunk(
                session_update="agent_message_chunk",
                content=TextContentBlock(type="text", text="{}"),
            ),
        )
        assert client.text == ["{}"]
        assert client.text_bytes == len("Reading.{}")
        client.text_bytes = worker.MAX_RESPONSE_BYTES
        await client.session_update(
            "test",
            AgentMessageChunk(
                session_update="agent_message_chunk",
                content=TextContentBlock(type="text", text="x"),
            ),
        )
        assert client.failure

    asyncio.run(exercise())


@pytest.mark.parametrize("version,compatible", [(worker.KIRO_VERSION, True), ("9.99.0", False)])
def test_runtime_status_reports_cli_compatibility_without_claiming_retrieval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, version: str, compatible: bool
) -> None:
    monkeypatch.setattr(worker.shutil, "which", lambda name: "/opt/kiro/bin/kiro-cli")
    probe = Mock(returncode=0, stdout=f"kiro-cli {version}\n")
    run = Mock(return_value=probe)
    monkeypatch.setattr(worker.subprocess, "run", run)
    status = worker.runtime_status(tmp_path)
    assert status["cli_compatible"] is compatible
    assert status["isolation_verified"] is False
    assert status["search_verified"] is False
    assert "available" not in status
    assert status["version"] == version
    run.assert_called_once()
    assert run.call_args.args[0] == ["/opt/kiro/bin/kiro-cli", "--version"]


def test_missing_runtime_reports_unverified_capabilities(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(worker.shutil, "which", lambda name: None)
    status = worker.runtime_status(tmp_path)
    assert status["cli_compatible"] is False
    assert status["isolation_verified"] is False
    assert status["search_verified"] is False
    assert "available" not in status
    assert "not installed" in status["error"]
