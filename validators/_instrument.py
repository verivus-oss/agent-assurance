"""Assertions for executable acceptance instruments, including optimized Python."""


def require(condition, message="acceptance property failed"):
    if not condition:
        raise AssertionError(message)
