"""Expose owned compile-only syntax helpers to conformance commands."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'validators'))
import _literal_ast as _owned  # noqa: E402

__all__ = _owned.__all__


def __getattr__(name):
    return getattr(_owned, name)
