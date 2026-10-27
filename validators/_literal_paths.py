"""Enumerate files with fixed path segments and explicit star segments."""

import os
import stat
from pathlib import Path
from collections.abc import Iterator


def _status(path: Path) -> os.stat_result | None:
    try:
        return path.stat()
    except (FileNotFoundError, NotADirectoryError) as exc:
        if path.is_symlink():
            raise OSError(f"{path}: dangling discovery candidate") from exc
        if path.parent.is_symlink():
            try:
                parent_status = path.parent.stat()
            except (FileNotFoundError, NotADirectoryError) as parent_exc:
                raise OSError(f"{path.parent}: dangling discovery directory") from parent_exc
            if not stat.S_ISDIR(parent_status.st_mode):
                raise OSError(f"{path.parent}: discovery parent is not a directory") from exc
        return None


def candidate_file(path: Path) -> bool:
    status = _status(path)
    if status is None:
        return False
    if not stat.S_ISREG(status.st_mode):
        raise OSError(f"{path}: discovery candidate is not a regular file")
    return True


def candidate_directory(path: Path) -> bool:
    status = _status(path)
    return status is not None and stat.S_ISDIR(status.st_mode)


def discovery_root(path: Path, *, required: bool = False) -> bool:
    status = _status(path)
    if status is None:
        if required:
            raise OSError(f"{path}: discovery root is missing")
        return False
    if not stat.S_ISDIR(status.st_mode):
        raise OSError(f"{path}: discovery root is not a directory")
    return True


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
    if not discovery_root(folder):
        return []
    try:
        with os.scandir(folder) as entries:
            return sorted(entries, key=lambda entry: entry.name)
    except (FileNotFoundError, NotADirectoryError) as exc:
        raise OSError(f"{folder}: discovery root changed during scan") from exc


def glob(root: Path, pattern: str) -> Iterator[Path]:
    parts = pattern.split("/")
    if not parts or any(not part or part in (".", "..") for part in parts):
        raise ValueError("path pattern must contain safe nonempty segments")

    def visit(folder: Path, index: int) -> Iterator[Path]:
        if index == len(parts):
            if _status(folder) is not None:
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
                if index + 1 == len(parts) or candidate_directory(Path(entry.path)):
                    yield from visit(Path(entry.path), index + 1)

    yield from visit(root, 0)


def rglob(root: Path, pattern: str) -> Iterator[Path]:
    yield from glob(root, "**/" + pattern)
