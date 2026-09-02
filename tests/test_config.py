import pytest

from pk_stack_lab.aws import client
from pk_stack_lab.config import (
    HOST_ENDPOINT,
    TASK_ENDPOINT,
    SafetyError,
    validate_host_endpoint,
    validate_task_endpoint,
)


@pytest.mark.parametrize(
    "endpoint",
    [
        "",
        "https://127.0.0.1:4566",
        "http://localhost:4566",
        "http://127.0.0.1",
        "http://127.0.0.1:4566/x",
        "http://user:pass@127.0.0.1:4566",
        "http://127.0.0.1:4566/?q=x",
        "http://169.254.169.254:4566",
        "http://aws.amazon.com:4566",
    ],
)
def test_host_endpoint_rejects_every_non_exact_or_real_aws_path(endpoint: str) -> None:
    with pytest.raises(SafetyError):
        validate_host_endpoint(endpoint)


def test_explicit_host_client_has_no_default_aws_endpoint() -> None:
    result = client("sqs")
    assert result.meta.endpoint_url == HOST_ENDPOINT
    assert result.meta.region_name == "us-east-1"


def test_task_endpoint_is_only_the_compose_name() -> None:
    assert validate_task_endpoint(TASK_ENDPOINT) == TASK_ENDPOINT
    with pytest.raises(SafetyError):
        validate_task_endpoint(HOST_ENDPOINT)
