import threading

import pytest
from botocore.exceptions import ClientError

from pk_stack_lab import runtime


class _LeaseDdb:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.item: dict[str, object] = {"status": "QUEUED", "attempts": 0}

    def update_item(self, **kwargs: object) -> None:
        values = kwargs["ExpressionAttributeValues"]
        expression = str(kwargs["ConditionExpression"])
        assert isinstance(values, dict)
        with self.lock:
            if "attribute_not_exists(processing_lease_until)" in expression:
                now = int(values[":now"]["N"])
                claimable = self.item["status"] == "QUEUED" or (
                    self.item["status"] == "PROCESSING"
                    and (
                        "processing_lease_until" not in self.item
                        or int(self.item["processing_lease_until"]) < now
                    )
                )
                if not claimable:
                    raise ClientError(
                        {"Error": {"Code": "ConditionalCheckFailedException"}}, "UpdateItem"
                    )
                self.item.update(
                    status="PROCESSING",
                    processing_token=values[":token"]["S"],
                    processing_lease_until=int(values[":lease"]["N"]),
                    attempts=int(self.item["attempts"]) + 1,
                )
                return
            if (
                self.item["status"] != "PROCESSING"
                or self.item.get("processing_token") != values[":token"]["S"]
            ):
                raise ClientError(
                    {"Error": {"Code": "ConditionalCheckFailedException"}}, "UpdateItem"
                )
            if ":done" in values:
                self.item.update(status="COMPLETE", object_key=values[":key"]["S"])
            else:
                self.item["status"] = "QUEUED"
            self.item.pop("processing_token", None)
            self.item.pop("processing_lease_until", None)


def test_worker_claim_has_one_winner_and_expired_lease_recovers() -> None:
    ddb = _LeaseDdb()
    key = {"pk": {"S": "TENANT#tenant-a"}, "sk": {"S": "e-1"}}
    barrier = threading.Barrier(3)
    outcomes: list[tuple[str, bool]] = []

    def claim(token: str) -> None:
        barrier.wait()
        outcomes.append(
            (token, runtime._claim_job(ddb, table="exports", key=key, token=token, now=100))
        )

    first = threading.Thread(target=claim, args=("token-a",))
    second = threading.Thread(target=claim, args=("token-b",))
    first.start()
    second.start()
    barrier.wait()
    first.join()
    second.join()
    assert sorted(passed for _, passed in outcomes) == [False, True]
    winner = next(token for token, passed in outcomes if passed)
    loser = next(token for token, passed in outcomes if not passed)
    assert ddb.item["attempts"] == 1

    assert runtime._claim_job(ddb, table="exports", key=key, token=loser, now=105) is False
    assert runtime._claim_job(ddb, table="exports", key=key, token=loser, now=107) is True
    assert ddb.item["attempts"] == 2
    with pytest.raises(ClientError):
        runtime._complete_job(
            ddb, table="exports", key=key, token=winner, object_key="exports/a/e-1.json"
        )
    runtime._complete_job(
        ddb, table="exports", key=key, token=loser, object_key="exports/a/e-1.json"
    )
    assert ddb.item == {
        "status": "COMPLETE",
        "attempts": 2,
        "object_key": "exports/a/e-1.json",
    }


def _handler(reply: list[tuple[int, dict[str, object]]]):
    handler = object.__new__(runtime.ExportHandler)
    handler.path = "/exports"
    handler.headers = {"Idempotency-Key": "retry-key"}
    handler._json = lambda: {"tenant": "tenant-a"}
    handler._reply = lambda status, body: reply.append((int(status), body))
    return handler


def _get_handler(tenant: str, export_id: str, reply: list[tuple[int, dict[str, object]]]):
    handler = object.__new__(runtime.ExportHandler)
    handler.path = f"/exports?tenant={tenant}&id={export_id}"
    handler._reply = lambda status, body: reply.append((int(status), body))
    return handler


def test_get_export_uses_tenant_partition_key_and_hides_other_tenants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    export_id = "e-0123456789abcdef"
    item = {
        "status": {"S": "COMPLETE"},
        "object_key": {"S": f"exports/tenant-a/{export_id}.json"},
    }
    requested_keys: list[dict[str, dict[str, str]]] = []

    class Ddb:
        def get_item(self, **kwargs):
            key = kwargs["Key"]
            requested_keys.append(key)
            return {"Item": item} if key["pk"]["S"] == "TENANT#tenant-a" else {}

    monkeypatch.setattr(runtime, "_ddb", lambda endpoint: Ddb())
    monkeypatch.setattr(
        runtime, "runtime_env", lambda: {"PK_STACK_LAB_ENDPOINT": "http://floci:4566"}
    )
    monkeypatch.setattr(runtime, "_env", lambda name: "exports-table")

    owner_reply: list[tuple[int, dict[str, object]]] = []
    runtime.ExportHandler.do_GET(_get_handler("tenant-a", export_id, owner_reply))
    other_reply: list[tuple[int, dict[str, object]]] = []
    runtime.ExportHandler.do_GET(_get_handler("tenant-b", export_id, other_reply))

    assert owner_reply == [
        (
            200,
            {
                "id": export_id,
                "tenant": "tenant-a",
                "status": "COMPLETE",
                "object_key": f"exports/tenant-a/{export_id}.json",
            },
        )
    ]
    assert other_reply == [(404, {"error": "not found"})]
    assert requested_keys == [
        {"pk": {"S": "TENANT#tenant-a"}, "sk": {"S": export_id}},
        {"pk": {"S": "TENANT#tenant-b"}, "sk": {"S": export_id}},
    ]


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

        def update_item(self, **kwargs):
            assert item is not None
            item["enqueue_confirmed"] = {"BOOL": True}

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


def test_confirmed_queued_duplicate_does_not_republish(monkeypatch: pytest.MonkeyPatch) -> None:
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

        def update_item(self, **kwargs):
            assert item is not None
            item["enqueue_confirmed"] = {"BOOL": True}

    class Sqs:
        def send_message(self, **kwargs):
            sent.append(kwargs)

    ddb = Ddb()
    sqs = Sqs()
    monkeypatch.setattr(runtime, "_ddb", lambda endpoint: ddb)
    monkeypatch.setattr(runtime, "_sqs", lambda endpoint: sqs)
    monkeypatch.setattr(
        runtime, "runtime_env", lambda: {"PK_STACK_LAB_ENDPOINT": "http://floci:4566"}
    )
    monkeypatch.setattr(
        runtime,
        "_env",
        lambda name: {"PK_STACK_LAB_TABLE": "table", "PK_STACK_LAB_QUEUE_URL": "queue"}[name],
    )
    first: list[tuple[int, dict[str, object]]] = []
    second: list[tuple[int, dict[str, object]]] = []
    runtime.ExportHandler.do_POST(_handler(first))
    runtime.ExportHandler.do_POST(_handler(second))
    assert first[0][0] == 202 and second[0][0] == 202
    assert len(sent) == 1
