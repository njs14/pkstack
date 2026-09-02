"""Explicit, fail-closed Floci boto3 client construction."""

from __future__ import annotations

from typing import Any

import boto3
from botocore.config import Config

from .config import (
    HOST_ENDPOINT,
    REGION,
    TASK_ENDPOINT,
    validate_host_endpoint,
    validate_task_endpoint,
)


def client(service: str, *, endpoint: str = HOST_ENDPOINT) -> Any:
    """Create one client that cannot fall back to a real AWS endpoint or credentials."""
    if endpoint == TASK_ENDPOINT:
        endpoint = validate_task_endpoint(endpoint)
    else:
        endpoint = validate_host_endpoint(endpoint)
    return boto3.session.Session(
        aws_access_key_id="local-lab-access",
        aws_secret_access_key="local-lab-secret",
        aws_session_token="local-lab-token",
        region_name=REGION,
    ).client(
        service,
        endpoint_url=endpoint,
        config=Config(retries={"max_attempts": 2, "mode": "standard"}),
    )
