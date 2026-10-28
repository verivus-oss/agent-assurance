#!/usr/bin/env python3
"""Require safe Rust crates and reject Go imports of the unsafe package."""

from pathlib import Path
import sys

from _literal_paths import glob, rglob


ROOT = Path(__file__).resolve().parents[1]


def cargo_manifests(root: Path) -> list[Path]:
    """Derive the independent tooling crates for advisory and license checks."""
    tools = root / "tools"
    if tools.is_symlink():
        raise ValueError("tooling root must not be a symbolic link")
    manifests = sorted(glob(root, "tools/*/Cargo.toml"))
    if not manifests:
        raise ValueError("native check requires a nonempty Cargo manifest population")
    for path in manifests:
        lock = path.parent / "Cargo.lock"
        if path.is_symlink() or path.parent.is_symlink() or not path.is_file():
            raise ValueError("Cargo manifest must be a regular repository file")
        if lock.is_symlink() or not lock.is_file() or not lock.stat().st_size:
            raise ValueError("Cargo manifest requires a nonempty regular lockfile")
    if len(set(manifests)) != len(manifests):
        raise ValueError("native check repeated a Cargo manifest identity")
    return manifests


def rust_has_forbid(source: str) -> bool:
    first = next((line.strip() for line in _without_comments(source).splitlines() if line.strip()), "")
    return first == "#![forbid(unsafe_code)]"


def rust_unsafe_keyword(source: str) -> bool:
    """Read Rust tokens, ignoring comments and literals, for an unsafe keyword."""
    index = 0
    while index < len(source):
        pair = source[index:index + 2]
        if pair == "//":
            end = source.find("\n", index)
            index = len(source) if end < 0 else end
            continue
        if pair == "/*":
            depth = 1
            index += 2
            while index < len(source) and depth:
                pair = source[index:index + 2]
                if pair == "/*":
                    depth += 1
                    index += 2
                elif pair == "*/":
                    depth -= 1
                    index += 2
                else:
                    index += 1
            if depth:
                raise ValueError("unclosed Rust block comment")
            continue
        raw_start = None
        for prefix in ("br", "cr", "r"):
            if source.startswith(prefix, index) and (index == 0 or not (source[index - 1].isalnum() or source[index - 1] == "_")):
                cursor = index + len(prefix)
                while cursor < len(source) and source[cursor] == "#":
                    cursor += 1
                if cursor < len(source) and source[cursor] == '"':
                    raw_start = cursor
                    break
        if raw_start is not None:
            closing = '"' + source[index + len(prefix):raw_start]
            end = source.find(closing, raw_start + 1)
            if end < 0:
                raise ValueError("unclosed Rust raw string")
            index = end + len(closing)
            continue
        if source[index] == '"':
            index += 1
            while index < len(source) and source[index] != '"':
                index += 2 if source[index] == "\\" else 1
            if index >= len(source):
                raise ValueError("unclosed Rust string")
            index += 1
            continue
        if source[index] == "'" and index + 2 < len(source):
            if source[index + 2] == "'":
                index += 3
                continue
            if source[index + 1] == "\\":
                end = source.find("'", index + 2)
                if 0 <= end - index <= 10:
                    index = end + 1
                    continue
        if source[index].isascii() and (source[index].isalpha() or source[index] == "_"):
            end = index + 1
            while end < len(source) and source[end].isascii() and (source[end].isalnum() or source[end] == "_"):
                end += 1
            if source[index:end] == "unsafe":
                return True
            index = end
            continue
        index += 1
    return False


def _without_comments(source: str) -> str:
    """Erase line and nested block comments while retaining source layout."""
    result: list[str] = []
    index = 0
    depth = 0
    while index < len(source):
        pair = source[index:index + 2]
        if depth and pair == "/*":
            depth += 1
            result.extend("  ")
            index += 2
        elif depth and pair == "*/":
            depth -= 1
            result.extend("  ")
            index += 2
        elif depth:
            result.append("\n" if source[index] == "\n" else " ")
            index += 1
        elif pair == "//":
            end = source.find("\n", index)
            if end < 0:
                result.extend(" " * (len(source) - index))
                break
            result.extend(" " * (end - index))
            index = end
        elif pair == "/*":
            depth = 1
            result.extend("  ")
            index += 2
        else:
            result.append(source[index])
            index += 1
    if depth:
        raise ValueError("unclosed Rust block comment")
    return "".join(result)


def _go_tokens(source: str) -> list[tuple[str, str]]:
    """Tokenize Go imports without interpreting strings or running a pattern engine."""
    tokens: list[tuple[str, str]] = []
    index = 0
    while index < len(source):
        char = source[index]
        pair = source[index:index + 2]
        if char.isspace():
            index += 1
        elif pair == "//":
            end = source.find("\n", index)
            index = len(source) if end < 0 else end
        elif pair == "/*":
            end = source.find("*/", index + 2)
            if end < 0:
                raise ValueError("unclosed Go block comment")
            index = end + 2
        elif char in ('"', "`", "'"):
            quote = char
            index += 1
            start = index
            while index < len(source) and source[index] != quote:
                if source[index] == "\\" and quote != "`":
                    index += 1
                index += 1
            if index == len(source):
                raise ValueError("unclosed Go string")
            tokens.append(("string" if quote != "'" else "rune", source[start:index]))
            index += 1
        elif char.isascii() and (char.isalpha() or char == "_"):
            start = index
            index += 1
            while index < len(source) and source[index].isascii() and (source[index].isalnum() or source[index] == "_"):
                index += 1
            tokens.append(("word", source[start:index]))
        else:
            tokens.append(("symbol", char))
            index += 1
    return tokens


def go_unsafe_import(source: str) -> bool:
    tokens = _go_tokens(source)
    for index, token in enumerate(tokens):
        if token != ("word", "import"):
            continue
        cursor = index + 1
        grouped = cursor < len(tokens) and tokens[cursor] == ("symbol", "(")
        if grouped:
            cursor += 1
        while cursor < len(tokens):
            kind, value = tokens[cursor]
            if grouped and (kind, value) == ("symbol", ")"):
                break
            if kind == "word" or (kind, value) == ("symbol", "."):
                cursor += 1
                if cursor == len(tokens):
                    break
                kind, value = tokens[cursor]
            if kind == "string":
                if "\\" in value:
                    raise ValueError("escaped Go import path requires manual review")
                if value == "unsafe":
                    return True
                cursor += 1
                if not grouped:
                    break
                continue
            if not grouped:
                break
            cursor += 1
    return False


def check(root: Path) -> tuple[int, int]:
    crates = sorted(glob(root, "tools/*/Cargo.toml"))
    modules = sorted(glob(root, "tools/*/go.mod"))
    if not crates or not modules:
        raise ValueError("safe tooling check requires both Rust and Go source populations")
    for manifest in crates:
        sources = [path for path in (manifest.parent / "src/main.rs", manifest.parent / "src/lib.rs") if path.is_file()]
        if not sources or any(not rust_has_forbid(path.read_text()) for path in sources):
            raise ValueError("Rust crate lacks a forbid unsafe code declaration: " + str(manifest.parent))
        for path in sorted(rglob(manifest.parent / "src", "*.rs")):
            if rust_unsafe_keyword(path.read_text()):
                raise ValueError("Rust source contains an unsafe keyword: " + str(path))
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
        if sys.argv[1:] == ["--cargo-manifests"]:
            manifests = cargo_manifests(ROOT)
            output = b"".join(path.relative_to(ROOT).as_posix().encode("utf-8") + b"\0" for path in manifests)
            sys.stdout.buffer.write(output)
            raise SystemExit(0)
        if sys.argv[1:]:
            raise ValueError("safe tools option is unsupported")
        rust_count, go_count = check(ROOT)
    except (OSError, UnicodeError, ValueError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    print(f"safe tools: {rust_count} Rust crates with forbid declarations, {go_count} Go files checked")
