#!/usr/bin/env python3
"""Emit the owned catalog section from TOML; do not infer SQL semantics."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "validators"))
from _vocabulary import load_catalog  # noqa: E402

BEGIN = "-- BEGIN GENERATED DECLARED VOCABULARY VALUES\n"
END = "-- END GENERATED DECLARED VOCABULARY VALUES\n"
TABLES = {"postgres": "attribute_value_allowed", "duckdb": "dagtoml.attribute_value_allowed",
          "sqlite": "dagtoml_attribute_value_allowed"}


def render(repo_root: Path, engine: str) -> str:
    def quote(value: str) -> str:
        if "\x00" in value:
            raise ValueError("catalog tokens cannot contain NUL in SQL mirrors")
        return "'" + value.replace("'", "''") + "'"

    catalog = load_catalog(repo_root)
    pairs = sorted((name, value) for name, item in catalog.items() for value in item.values)
    if not pairs:
        raise ValueError("empty declared-token population")
    rows = [f"    ({quote(name)}, {quote(value)})" for name, value in pairs]
    # SQL identifiers are selected from TABLES; quote rejects NUL and doubles
    # literal apostrophes. This generator writes artifacts, never executes SQL.
    return (f"-- Complete catalog: {len(pairs)} declared pairs, including native-backed tokens.\n"  # nosec B608
            f"INSERT INTO {TABLES[engine]} (attribute, value) VALUES\n" + ",\n".join(rows) + ";\n")


def generated_seed(repo_root: Path, engine: str) -> str:
    seed = (repo_root / f"reference/database/{engine}/seed.sql").read_text(encoding="utf-8")
    if seed.count(BEGIN) != 1 or seed.count(END) != 1:
        raise ValueError(f"{engine}: expected exactly one of each generation marker")
    before, remainder = seed.split(BEGIN)
    _, after = remainder.split(END)
    return before + BEGIN + render(repo_root, engine) + END + after


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    for engine in TABLES:
        path = args.repo_root / f"reference/database/{engine}/seed.sql"
        generated = generated_seed(args.repo_root, engine)
        if args.write:
            path.write_text(generated, encoding="utf-8")
        elif generated.encode() != path.read_bytes():
            raise SystemExit(f"FAIL: {engine} generated catalog differs; run with --write")
    print("PASS: all three owned seed sections match the TOML-derived catalog")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
