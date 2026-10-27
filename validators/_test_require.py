"""Assertion helper that remains active under optimized Python."""

from collections.abc import Callable
from typing import TypeVar


E = TypeVar("E", bound=Exception)


def require(condition: object, message: object = "test expectation failed") -> None:
    if not condition:
        raise AssertionError(message)


def expect_raises(error_type: type[E], action: Callable[[], object], message: str) -> E:
    try:
        action()
    except error_type as exc:
        require(str(exc), f"{message}: missing exception diagnostic")
        return exc
    raise AssertionError(message)
