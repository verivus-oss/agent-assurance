#!/usr/bin/env python3
"""Regression instrument: SQL source is unavailable to the declaration checker."""

from contextlib import contextmanager
import inspect
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reference/database"))
from _opaque import opaque_sha256  # noqa: E402


@contextmanager
def opaque_sql_only():
    # CPython's open audit event covers pathlib, io, builtins, and os.open.
    # This is an instrument over trusted checker code, not a security sandbox
    # for arbitrary native extensions or a compromised interpreter.
    state = {"active": True, "installed": False}
    sentinel = object()

    def audit(event, args):
        if event == "dagtoml.sql_source_access.control" and args == (sentinel,):
            state["installed"] = True
        if not state["active"] or event != "open" or not str(args[0]).endswith(".sql"):
            return
        frame = inspect.currentframe()
        permitted = False
        try:
            while frame is not None:
                if frame.f_code is opaque_sha256.__code__:
                    permitted = True
                    break
                frame = frame.f_back
        finally:
            del frame
        if not permitted:
            raise ValueError("SQL-source-access: only opaque identity hashing is permitted in this checker")

    sys.addaudithook(audit)
    sys.audit("dagtoml.sql_source_access.control", sentinel)
    if not state["installed"]:
        raise RuntimeError("SQL source-access instrument was not installed")
    try:
        yield
    finally:
        state["active"] = False


def main(argv=None):
    with opaque_sql_only():
        # Install before importing the checker and its transitive callees so
        # moving SQL interpretation into module initialization cannot evade it.
        import check_attribute_values
        return check_attribute_values.main(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
