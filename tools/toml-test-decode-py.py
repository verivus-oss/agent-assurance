#!/usr/bin/env python3
"""Expose the vendored Python TOML 1.1 parser to toml-test."""

from __future__ import annotations

import json
import math
import pathlib
import sys
from datetime import date, datetime, time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "validators"))
import _toml11 as tomllib  # noqa: E402


def tagged(value: object) -> object:
    if isinstance(value, dict):
        return {key: tagged(item) for key, item in value.items()}
    if isinstance(value, list):
        return [tagged(item) for item in value]
    if isinstance(value, bool):
        return {"type": "bool", "value": str(value).lower()}
    if isinstance(value, int):
        return {"type": "integer", "value": str(value)}
    if isinstance(value, float):
        if math.isnan(value):
            rendered = "nan"
        elif math.isinf(value):
            rendered = "inf" if value > 0 else "-inf"
        else:
            rendered = repr(value)
        return {"type": "float", "value": rendered}
    if isinstance(value, datetime):
        return {"type": "datetime" if value.tzinfo else "datetime-local",
                "value": value.isoformat()}
    if isinstance(value, date):
        return {"type": "date-local", "value": value.isoformat()}
    if isinstance(value, time):
        return {"type": "time-local", "value": value.isoformat()}
    if isinstance(value, str):
        return {"type": "string", "value": value}
    raise TypeError(f"unsupported TOML value type: {type(value).__name__}")


def main() -> int:
    try:
        data = tomllib.loads(sys.stdin.buffer.read().decode("utf-8"))
    except (UnicodeError, tomllib.TOMLDecodeError) as exc:
        print(f"TOML parse error: {exc}", file=sys.stderr)
        return 1
    json.dump(tagged(data), sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
