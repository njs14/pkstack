"""Tiny document-export API and SQS worker used inside ECS task containers."""

from __future__ import annotations

import hashlib
import json
import os
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
            TableName=_env("PK_STACK_LAB_TABLE"), Key={"pk": {"S": f"TENANT#{tenant}"}, "sk": {"S": export_id}}
        )
        item = response.get("Item")
        if not item:
            self._reply(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        self._reply(
            HTTPStatus.OK,
            {"id": export_id, "tenant": tenant, "status": item["status"]["S"], "object_key": item.get("object_key", {}).get("S")},
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
            "pk": {"S": f"TENANT#{tenant}"}, "sk": {"S": export_id}, "idempotency": {"S": idem},
            "status": {"S": "QUEUED"}, "attempts": {"N": "0"}, "tenant": {"S": tenant},
        }
        try:
            ddb.put_item(
                TableName=table, Item=item,
                ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)",
            )
        except ClientError:
            existing = ddb.get_item(
                TableName=table,
                Key={"pk": {"S": f"TENANT#{tenant}"}, "sk": {"S": export_id}},
            ).get("Item")
            if existing and existing.get("idempotency", {}).get("S") == idem:
                if existing.get("status", {}).get("S") == "QUEUED":
                    _sqs(endpoint).send_message(
                        QueueUrl=_env("PK_STACK_LAB_QUEUE_URL"),
                        MessageBody=json.dumps({"tenant": tenant, "id": export_id}),
                    )
                self._reply(
                    HTTPStatus.ACCEPTED,
                    {
                        "id": export_id,
                        "tenant": tenant,
                        "status": existing["status"]["S"],
                        "duplicate": True,
                    },
                )
                return
            self._reply(HTTPStatus.CONFLICT, {"error": "idempotency conflict"})
            return
        _sqs(endpoint).send_message(
            QueueUrl=_env("PK_STACK_LAB_QUEUE_URL"), MessageBody=json.dumps({"tenant": tenant, "id": export_id})
        )
        self._reply(HTTPStatus.ACCEPTED, {"id": export_id, "tenant": tenant, "status": "QUEUED"})


def serve() -> None:
    runtime_env()
    ThreadingHTTPServer(("0.0.0.0", 8080), ExportHandler).serve_forever()


def worker() -> None:
    endpoint = runtime_env()["PK_STACK_LAB_ENDPOINT"]
    queue_url, table, bucket = _env("PK_STACK_LAB_QUEUE_URL"), _env("PK_STACK_LAB_TABLE"), _env("PK_STACK_LAB_BUCKET")
    sqs, ddb, s3 = _sqs(endpoint), _ddb(endpoint), client("s3", endpoint=endpoint)
    while True:
        messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=2, VisibilityTimeout=8).get("Messages", [])
        for message in messages:
            try:
                payload = json.loads(message["Body"])
                tenant, export_id = payload["tenant"], payload["id"]
                if not isinstance(tenant, str) or not isinstance(export_id, str):
                    raise TypeError("invalid job")
                key = {"pk": {"S": f"TENANT#{tenant}"}, "sk": {"S": export_id}}
                current = ddb.get_item(TableName=table, Key=key).get("Item")
                if not current or current.get("status", {}).get("S") == "COMPLETE":
                    if current:
                        ddb.update_item(
                            TableName=table,
                            Key=key,
                            UpdateExpression="ADD duplicate_deliveries :one",
                            ExpressionAttributeValues={":one": {"N": "1"}},
                        )
                    sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"])
                    continue
                object_key = f"exports/{tenant}/{export_id}.json"
                s3.put_object(Bucket=bucket, Key=object_key, Body=json.dumps({"tenant": tenant, "export_id": export_id}).encode(), ContentType="application/json")
                ddb.update_item(TableName=table, Key=key, UpdateExpression="SET #s = :done, object_key = :key ADD attempts :one", ExpressionAttributeNames={"#s": "status"}, ExpressionAttributeValues={":done": {"S": "COMPLETE"}, ":key": {"S": object_key}, ":one": {"N": "1"}})
                sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"])
            except (ClientError, KeyError, TypeError, ValueError, json.JSONDecodeError):
                # Redrive policy on the source queue enforces the bounded DLQ path.
                continue


if __name__ == "__main__":
    role = os.environ.get("PK_STACK_LAB_ROLE", "api")
    if role == "api":
        serve()
    elif role == "worker":
        worker()
    else:
        raise SystemExit("PK_STACK_LAB_ROLE must be api or worker")
