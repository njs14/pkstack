import pytest
from botocore.exceptions import ClientError

from pk_stack_lab import runtime


def _handler(reply: list[tuple[int, dict[str, object]]]):
    handler = object.__new__(runtime.ExportHandler)
    handler.path = "/exports"
    handler.headers = {"Idempotency-Key": "retry-key"}
    handler._json = lambda: {"tenant": "tenant-a"}
    handler._reply = lambda status, body: reply.append((int(status), body))
    return handler


def test_queued_retry_republishes_after_initial_ddb_success_and_sqs_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    item: dict[str, object] | None = None
    sent: list[dict[str, object]] = []

    class Ddb:
        def put_item(self, **kwargs):
            nonlocal item
            if item is not None:
                raise ClientError({"Error": {"Code": "ConditionalCheckFailedException"}}, "PutItem")
            item = kwargs["Item"]

        def get_item(self, **kwargs):
            return {"Item": item} if item else {}

    class Sqs:
        def __init__(self, fail: bool):
            self.fail = fail

        def send_message(self, **kwargs):
            if self.fail:
                raise ClientError({"Error": {"Code": "InternalError"}}, "SendMessage")
            sent.append(kwargs)

    ddb = Ddb()
    sqs = [Sqs(True), Sqs(False)]
    monkeypatch.setattr(runtime, "_ddb", lambda endpoint: ddb)
    monkeypatch.setattr(runtime, "_sqs", lambda endpoint: sqs.pop(0))
    monkeypatch.setattr(
        runtime, "runtime_env", lambda: {"PK_STACK_LAB_ENDPOINT": "http://floci:4566"}
    )
    monkeypatch.setattr(
        runtime,
        "_env",
        lambda name: {"PK_STACK_LAB_TABLE": "table", "PK_STACK_LAB_QUEUE_URL": "queue"}[name],
    )
    first: list[tuple[int, dict[str, object]]] = []
    runtime.ExportHandler.do_POST(_handler(first))
    assert first[0][0] == 503
    assert item is not None and item["status"] == {"S": "QUEUED"}
    second: list[tuple[int, dict[str, object]]] = []
    runtime.ExportHandler.do_POST(_handler(second))
    assert second[0][0] == 202
    assert len(sent) == 1


def test_complete_retry_does_not_republish(monkeypatch: pytest.MonkeyPatch) -> None:
    item = {"idempotency": {"S": "retry-key"}, "status": {"S": "COMPLETE"}}
    sent: list[dict[str, object]] = []

    class Ddb:
        def put_item(self, **kwargs):
            raise ClientError({"Error": {"Code": "ConditionalCheckFailedException"}}, "PutItem")

        def get_item(self, **kwargs):
            return {"Item": item}

    class Sqs:
        def send_message(self, **kwargs):
            sent.append(kwargs)

    monkeypatch.setattr(runtime, "_ddb", lambda endpoint: Ddb())
    monkeypatch.setattr(runtime, "_sqs", lambda endpoint: Sqs())
    monkeypatch.setattr(
        runtime, "runtime_env", lambda: {"PK_STACK_LAB_ENDPOINT": "http://floci:4566"}
    )
    monkeypatch.setattr(
        runtime,
        "_env",
        lambda name: {"PK_STACK_LAB_TABLE": "table", "PK_STACK_LAB_QUEUE_URL": "queue"}[name],
    )
    replies: list[tuple[int, dict[str, object]]] = []
    runtime.ExportHandler.do_POST(_handler(replies))
    assert replies[0][0] == 202
    assert sent == []
