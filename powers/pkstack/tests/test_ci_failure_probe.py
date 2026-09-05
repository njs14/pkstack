"""Disposable hosted proof that an actual failed test blocks aggregation."""


def test_ci_rejects_an_actual_failed_test() -> None:
    raise AssertionError("Intentional disposable CI gate validation failure")
