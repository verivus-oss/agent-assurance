"""Assertion helper that remains active under optimized Python."""

from __future__ import annotations

from collections.abc import Callable


def require(condition: object, message: object = "test expectation failed") -> None:
    if not condition:
        raise AssertionError(message)


def expect_raises(error_type: type[Exception], action: Callable[[], object], message: str) -> Exception:
    try:
        action()
    except error_type as exc:
        require(str(exc), f"{message}: missing exception diagnostic")
        return exc
    raise AssertionError(message)
