"""Assertion helper that remains active under optimized Python."""


def require(condition: object, message: object = "test expectation failed") -> None:
    if not condition:
        raise AssertionError(message)
