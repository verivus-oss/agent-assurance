#!/usr/bin/env python3
"""Require safe Rust crates and reject Go imports of the unsafe package."""

from pathlib import Path
import sys

from _literal_paths import glob, rglob


ROOT = Path(__file__).resolve().parents[1]


def rust_has_forbid(source: str) -> bool:
    return any(line.strip() == "#![forbid(unsafe_code)]" for line in source.splitlines())


def go_unsafe_import(source: str) -> bool:
    in_group = False
    for raw in source.splitlines():
        line = raw.strip()
        if line.startswith("//") or not line:
            continue
        if line == "import (":
            in_group = True
            continue
        if in_group and line == ")":
            in_group = False
            continue
        if line.startswith("import "):
            line = line[len("import "):].strip()
        elif not in_group:
            continue
        if line.startswith("_ ") or line.startswith(". "):
            line = line[2:].strip()
        return_value = line.startswith('"unsafe"') and (
            len(line) == len('"unsafe"') or line[len('"unsafe"'):].lstrip().startswith("//")
        )
        if return_value:
            return True
    return False


def check(root: Path) -> tuple[int, int]:
    crates = sorted(glob(root, "tools/*/Cargo.toml"))
    modules = sorted(glob(root, "tools/*/go.mod"))
    if not crates or not modules:
        raise ValueError("safe tooling check requires both Rust and Go source populations")
    for manifest in crates:
        sources = [path for path in (manifest.parent / "src/main.rs", manifest.parent / "src/lib.rs") if path.is_file()]
        if not sources or not any(rust_has_forbid(path.read_text()) for path in sources):
            raise ValueError("Rust crate lacks a forbid unsafe code declaration: " + str(manifest.parent))
    go_count = 0
    for manifest in modules:
        files = sorted(rglob(manifest.parent, "*.go"))
        if not files:
            raise ValueError("Go module has no source files: " + str(manifest.parent))
        for path in files:
            go_count += 1
            if go_unsafe_import(path.read_text()):
                raise ValueError("Go source imports unsafe: " + str(path))
    return len(crates), go_count


if __name__ == "__main__":
    try:
        rust_count, go_count = check(ROOT)
    except ValueError as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    print(f"safe tools: {rust_count} Rust crates with forbid declarations, {go_count} Go files checked")
