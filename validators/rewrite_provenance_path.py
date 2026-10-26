#!/usr/bin/env python3
"""Replace one fixture source path with a quoted absolute path."""

import json
from pathlib import Path
import sys


def rewrite(source: Path, destination: Path, value: str) -> None:
    found = 0
    rows = []
    for line in source.read_text().splitlines(keepends=True):
        if line.lstrip().startswith("source_path "):
            found += 1
            rows.append("source_path   = " + json.dumps(value) + "\n")
        else:
            rows.append(line)
    if found != 1:
        raise ValueError("fixture must contain exactly one source path")
    destination.write_text("".join(rows))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("expected source, destination, absolute path")
    rewrite(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])
