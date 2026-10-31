"""Explicit temporary module/class attributes for verification instruments."""

from contextlib import contextmanager
from types import ModuleType


@contextmanager
def temporary_attribute(owner, name, replacement):
    """Replace an existing attribute and restore its exact local definition."""
    if not isinstance(owner, (ModuleType, type)) or type(name) is not str or not name.isidentifier():
        raise TypeError('temporary attributes require a module or class and an identifier')
    namespace = vars(owner)
    local = name in namespace
    previous = namespace.get(name)
    if not local:
        getattr(owner, name)
    setattr(owner, name, replacement)
    try:
        yield replacement
    finally:
        if local:
            setattr(owner, name, previous)
        else:
            delattr(owner, name)


def returning(value):
    """Keep the same supplied result object on every invocation."""
    def call(*_arguments, **_keywords):
        return value
    return call


def raising(error):
    """Raise the supplied failure without manufacturing a mock object."""
    if not isinstance(error, BaseException):
        raise TypeError('temporary failure requires an exception instance')
    def call(*_arguments, **_keywords):
        raise error
    return call


def successive(values):
    """Consume a captured finite sequence and reject undeclared extra calls."""
    if type(values) not in (list, tuple) or not values:
        raise TypeError('temporary replies require a nonempty list or tuple')
    captured = tuple(values)
    position = 0
    def call(*_arguments, **_keywords):
        nonlocal position
        if position == len(captured):
            raise AssertionError('temporary replies exhausted')
        value = captured[position]
        position += 1
        return value
    return call
