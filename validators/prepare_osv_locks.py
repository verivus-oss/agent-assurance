#!/usr/bin/env python3
"""Expose every pinned Python lock under a scanner-recognized filename."""

from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "requirements"
TARGET = ROOT / "osv-locks"


def main() -> None:
    locks = sorted(path for path in SOURCE.iterdir()
                   if path.is_file() and path.suffix == ".txt")
    if len(locks) < 7:
        raise RuntimeError("pinned Python lock population shrank")
    if TARGET.exists():
        raise RuntimeError("OSV preparation target is already present")
    for lock in locks:
        destination = TARGET / lock.stem / "requirements.txt"
        destination.parent.mkdir(parents=True)
        shutil.copyfile(lock, destination)
        if destination.read_bytes() != lock.read_bytes():
            raise RuntimeError("OSV input differs from pinned Python lock")
    actual = {directory.name for directory in TARGET.iterdir()
              if directory.is_dir() and (directory / "requirements.txt").is_file()}
    if actual != {lock.stem for lock in locks}:
        raise RuntimeError("OSV lock copy population differs from source")
    print(f"OSV prepared {len(locks)} pinned Python lock inputs")


if __name__ == "__main__":
    main()
