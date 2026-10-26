#!/usr/bin/env python3
"""Fail the always-run aggregate on any absent, skipped, or failed dependency."""

from _literal_json import loads as loads_json
import os

JOBS = frozenset({"engines", "loaders", "instruments"})


def validate(results):
    if not isinstance(results, dict) or set(results) != JOBS:
        raise ValueError("database aggregate requires exactly engines, loaders, and instruments")
    if any(not isinstance(row, dict) or row.get("result") != "success" for row in results.values()):
        raise ValueError("every required database dependency must succeed; skipped is failure")


if __name__ == "__main__":
    validate(loads_json(os.environ["DATABASE_JOB_RESULTS"]))
    print("All three required dependency jobs succeeded; skipped=[]")
