"""Tiny document-export API and SQS worker used inside ECS task containers."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from botocore.exceptions import ClientError

from .aws import client
from .config import runtime_env


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"missing {name}")
    return value


def _ddb(endpoint: str):
    return client("dynamodb", endpoint=endpoint)


def _sqs(endpoint: str):
    return client("sqs", endpoint=endpoint)


def _error_code(exc: ClientError) -> str:
    """Return the structured service code; never infer it from exception prose."""
    code = exc.response.get("Error", {}).get("Code")
    return code if isinstance(code, str) else ""


class ExportHandler(BaseHTTPRequestHandler):
    server_version = "pk-stack-lab/0.1"

    def log_message(self, *_: object) -> None:  # Deliberately avoid request-body logging.
        return

    def _reply(self, status: int, body: dict[str, object]) -> None:
        data = json.dumps(body, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json(self) -> dict[str, object] | None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return None
        if not 0 < length <= 4096:
            return None
        try:
            decoded = json.loads(self.rfile.read(length))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        return decoded if isinstance(decoded, dict) else None

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/healthz":
            self._reply(HTTPStatus.OK, {"ok": True, "role": "api"})
            return
        if parsed.path != "/exports":
            self._reply(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        tenant = parse_qs(parsed.query).get("tenant", [""])[0]
        export_id = parse_qs(parsed.query).get("id", [""])[0]
        if not tenant or not export_id or len(tenant) > 64 or len(export_id) > 64:
            self._reply(HTTPStatus.BAD_REQUEST, {"error": "tenant and id required"})
            return
        endpoint = runtime_env()["PK_STACK_LAB_ENDPOINT"]
        response = _ddb(endpoint).get_item(
            TableName=_env("PK_STACK_LAB_TABLE"),
            Key={"pk": {"S": f"TENANT#{tenant}"}, "sk": {"S": export_id}},
        )
        item = response.get("Item")
        if not item:
            self._reply(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        self._reply(
            HTTPStatus.OK,
            {
                "id": export_id,
                "tenant": tenant,
                "status": item["status"]["S"],
                "object_key": item.get("object_key", {}).get("S"),
            },
        )

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/exports":
            self._reply(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        body = self._json()
        tenant = body.get("tenant") if body else None
        if not isinstance(tenant, str) or not tenant or len(tenant) > 64:
            self._reply(HTTPStatus.BAD_REQUEST, {"error": "valid tenant required"})
            return
        idem = self.headers.get("Idempotency-Key", "")
        if not idem or len(idem) > 64:
            self._reply(HTTPStatus.BAD_REQUEST, {"error": "Idempotency-Key required"})
            return
        export_id = f"e-{hashlib.sha256(f'{tenant}:{idem}'.encode()).hexdigest()[:16]}"
        endpoint = runtime_env()["PK_STACK_LAB_ENDPOINT"]
        table = _env("PK_STACK_LAB_TABLE")
        ddb = _ddb(endpoint)
        item = {
            "pk": {"S": f"TENANT#{tenant}"},
            "sk": {"S": export_id},
            "idempotency": {"S": idem},
            "status": {"S": "QUEUED"},
            "attempts": {"N": "0"},
            "tenant": {"S": tenant},
        }
        duplicate = False
        try:
            ddb.put_item(
                TableName=table,
                Item=item,
                ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)",
            )
        except ClientError as exc:
            # A conditional collision is the *only* duplicate path.  Access
            # denied, throttling, malformed requests and emulator faults must
            # remain retriable server errors rather than false conflicts.
            if _error_code(exc) != "ConditionalCheckFailedException":
                self._reply(
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    {"error": "export claim temporarily unavailable"},
                )
                return
            try:
                existing = ddb.get_item(
                    TableName=table,
                    Key={"pk": {"S": f"TENANT#{tenant}"}, "sk": {"S": export_id}},
                ).get("Item")
            except ClientError:
                self._reply(
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    {"error": "export lookup temporarily unavailable"},
                )
                return
            if not existing or existing.get("idempotency", {}).get("S") != idem:
                # This should be unreachable for the deterministic key, but it
                # is not a client conflict and must not disclose state.
                self._reply(
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    {"error": "export claim temporarily unavailable"},
                )
                return
            item = existing
            duplicate = True
        status = item.get("status", {}).get("S")
        if not isinstance(status, str):
            self._reply(
                HTTPStatus.SERVICE_UNAVAILABLE, {"error": "export state temporarily unavailable"}
            )
            return
        if status == "QUEUED":
            try:
                _sqs(endpoint).send_message(
                    QueueUrl=_env("PK_STACK_LAB_QUEUE_URL"),
                    MessageBody=json.dumps(
                        {"tenant": tenant, "id": export_id}, separators=(",", ":")
                    ),
                )
            except ClientError:
                # The durable QUEUED row is intentionally retained.  A retry
                # with the same key republished the same logical export ID.
                self._reply(
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    {"error": "export enqueue temporarily unavailable"},
                )
                return
        self._reply(
            HTTPStatus.ACCEPTED,
            {
                "id": export_id,
                "tenant": tenant,
                "status": status,
                **({"duplicate": True} if duplicate else {}),
            },
        )


def serve() -> None:
    runtime_env()
    ThreadingHTTPServer(("0.0.0.0", 8080), ExportHandler).serve_forever()


def worker() -> None:
    endpoint = runtime_env()["PK_STACK_LAB_ENDPOINT"]
    queue_url, table, bucket = (
        _env("PK_STACK_LAB_QUEUE_URL"),
        _env("PK_STACK_LAB_TABLE"),
        _env("PK_STACK_LAB_BUCKET"),
    )
    sqs, ddb, s3 = _sqs(endpoint), _ddb(endpoint), client("s3", endpoint=endpoint)
    while True:
        messages = sqs.receive_message(
            QueueUrl=queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=2, VisibilityTimeout=8
        ).get("Messages", [])
        for message in messages:
            key: dict[str, dict[str, str]] | None = None
            token: str | None = None
            try:
                payload = json.loads(message["Body"])
                tenant, export_id = payload["tenant"], payload["id"]
                if not isinstance(tenant, str) or not isinstance(export_id, str):
                    raise TypeError("invalid job")
                key = {"pk": {"S": f"TENANT#{tenant}"}, "sk": {"S": export_id}}
                current = ddb.get_item(TableName=table, Key=key).get("Item")
                if not current:
                    # Unknown/malformed jobs are left for the source queue's
                    # bounded redrive policy; they are never acknowledged.
                    continue
                if current.get("status", {}).get("S") == "COMPLETE":
                    ddb.update_item(
                        TableName=table,
                        Key=key,
                        UpdateExpression="ADD duplicate_deliveries :one",
                        ExpressionAttributeValues={":one": {"N": "1"}},
                    )
                    sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"])
                    continue
                token = secrets.token_hex(16)
                try:
                    ddb.update_item(
                        TableName=table,
                        Key=key,
                        UpdateExpression="SET #s = :processing, processing_token = :token ADD attempts :one",
                        ConditionExpression="#s = :queued",
                        ExpressionAttributeNames={"#s": "status"},
                        ExpressionAttributeValues={
                            ":queued": {"S": "QUEUED"},
                            ":processing": {"S": "PROCESSING"},
                            ":token": {"S": token},
                            ":one": {"N": "1"},
                        },
                    )
                except ClientError as exc:
                    if _error_code(exc) != "ConditionalCheckFailedException":
                        continue
                    # A competing delivery owns PROCESSING.  It is deliberately
                    # not acknowledged: only a terminal winner can consume it.
                    latest = ddb.get_item(TableName=table, Key=key).get("Item", {})
                    if latest.get("status", {}).get("S") == "COMPLETE":
                        sqs.delete_message(
                            QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"]
                        )
                    continue
                object_key = f"exports/{tenant}/{export_id}.json"
                s3.put_object(
                    Bucket=bucket,
                    Key=object_key,
                    Body=json.dumps(
                        {"tenant": tenant, "export_id": export_id}, separators=(",", ":")
                    ).encode(),
                    ContentType="application/json",
                )
                ddb.update_item(
                    TableName=table,
                    Key=key,
                    UpdateExpression="SET #s = :done, object_key = :key REMOVE processing_token",
                    ConditionExpression="#s = :processing AND processing_token = :token",
                    ExpressionAttributeNames={"#s": "status"},
                    ExpressionAttributeValues={
                        ":processing": {"S": "PROCESSING"},
                        ":token": {"S": token},
                        ":done": {"S": "COMPLETE"},
                        ":key": {"S": object_key},
                    },
                )
                sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"])
            except (ClientError, KeyError, TypeError, ValueError, json.JSONDecodeError):
                # Redrive policy on the source queue enforces the bounded DLQ path.
                # If this attempt still owns PROCESSING, make it safely
                # recoverable.  A completion whose response was lost cannot be
                # reset because its conditional token no longer exists.
                try:
                    if key is not None and token is not None:
                        ddb.update_item(
                            TableName=table,
                            Key=key,
                            UpdateExpression="SET #s = :queued REMOVE processing_token",
                            ConditionExpression="#s = :processing AND processing_token = :token",
                            ExpressionAttributeNames={"#s": "status"},
                            ExpressionAttributeValues={
                                ":processing": {"S": "PROCESSING"},
                                ":queued": {"S": "QUEUED"},
                                ":token": {"S": token},
                            },
                        )
                except ClientError:
                    pass
                continue


if __name__ == "__main__":
    role = os.environ.get("PK_STACK_LAB_ROLE", "api")
    if role == "api":
        serve()
    elif role == "worker":
        worker()
    else:
        raise SystemExit("PK_STACK_LAB_ROLE must be api or worker")
