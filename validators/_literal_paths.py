"""Enumerate files with fixed path segments and explicit star segments."""

import os
import stat
from pathlib import Path
from collections.abc import Iterator


def _status(path: Path) -> os.stat_result | None:
    try:
        return path.stat()
    except (FileNotFoundError, NotADirectoryError) as exc:
        for depth, ancestor in enumerate((path, *path.parents)):
            try:
                entry = ancestor.lstat()
            except (FileNotFoundError, NotADirectoryError):
                # A missing lower segment may hide a broken link higher in the path.
                entry = None
            if entry is None:
                continue
            if stat.S_ISLNK(entry.st_mode):
                try:
                    entry = ancestor.stat()
                except (FileNotFoundError, NotADirectoryError) as link_exc:
                    kind = "candidate" if depth == 0 else "directory"
                    raise OSError(f"{ancestor}: dangling discovery {kind}") from link_exc
            if depth == 0:
                raise OSError(f"{path}: discovery candidate changed during inspection") from exc
            if not stat.S_ISDIR(entry.st_mode):
                raise OSError(f"{ancestor}: discovery parent is not a directory") from exc
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


def _children(folder: Path, *, required: bool) -> list[os.DirEntry[str]]:
    if not discovery_root(folder, required=required):
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

    def visit(folder: Path, index: int, observed: bool) -> Iterator[Path]:
        if index == len(parts):
            if _status(folder) is None:
                if observed:
                    raise OSError(f"{folder}: discovery candidate changed during scan")
                return
            yield folder
            return
        part = parts[index]
        if part == "**":
            yield from visit(folder, index + 1, observed)
            for entry in _children(folder, required=observed):
                if entry.is_symlink():
                    if entry.is_dir():
                        raise OSError(f"{entry.path}: recursive discovery directory link needs an explicit root")
                    if not entry.is_file():
                        raise OSError(f"{entry.path}: dangling recursive discovery link")
                if entry.is_dir(follow_symlinks=False):
                    yield from visit(Path(entry.path), index, True)
            return
        for entry in _children(folder, required=observed):
            if _segment(entry.name, part):
                if index + 1 == len(parts) or candidate_directory(Path(entry.path)):
                    yield from visit(Path(entry.path), index + 1, True)

    yield from visit(root, 0, False)


def rglob(root: Path, pattern: str) -> Iterator[Path]:
    yield from glob(root, "**/" + pattern)
