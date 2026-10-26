"""Enumerate files with fixed path segments and explicit star segments."""

import os
from pathlib import Path
from collections.abc import Iterator


def _segment(name: str, form: str) -> bool:
    if form == "*":
        return True
    if "*" not in form:
        return name == form
    if form.count("*") != 1:
        raise ValueError("unsupported path segment: " + form)
    prefix, suffix = form.split("*", 1)
    return len(name) >= len(prefix) + len(suffix) and name.startswith(prefix) and name.endswith(suffix)


def _children(folder: Path) -> list[os.DirEntry[str]]:
    try:
        with os.scandir(folder) as entries:
            return sorted(entries, key=lambda entry: entry.name)
    except (FileNotFoundError, NotADirectoryError):
        return []


def glob(root: Path, pattern: str) -> Iterator[Path]:
    parts = pattern.split("/")
    if not parts or any(not part or part in (".", "..") for part in parts):
        raise ValueError("path pattern must contain safe nonempty segments")

    def visit(folder: Path, index: int) -> Iterator[Path]:
        if index == len(parts):
            if folder.exists():
                yield folder
            return
        part = parts[index]
        if part == "**":
            yield from visit(folder, index + 1)
            for entry in _children(folder):
                if entry.is_dir(follow_symlinks=False):
                    yield from visit(Path(entry.path), index)
            return
        for entry in _children(folder):
            if _segment(entry.name, part):
                if index + 1 == len(parts) or entry.is_dir(follow_symlinks=True):
                    yield from visit(Path(entry.path), index + 1)

    yield from visit(root, 0)


def rglob(root: Path, pattern: str) -> Iterator[Path]:
    yield from glob(root, "**/" + pattern)
