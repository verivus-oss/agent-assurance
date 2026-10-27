"""Expose every tracked Python requirements lock as an OSV-recognized name."""

from __future__ import annotations

import json
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path


def tracked_sources(root: Path) -> list[Path]:
    """Derive the lock population from this checkout, including new files."""
    git = shutil.which("git")
    if git is None:
        raise SystemExit("git executable is required for OSV lock discovery")
    # The executable is resolved and all arguments are fixed. No shell runs.
    tracked = subprocess.run(  # noqa: S603  # nosec B603
        [git, "ls-files", "-z", "--", "requirements"],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout
    sources = sorted(
        root / name.decode("utf-8")
        for name in tracked.split(b"\0")
        if name and Path(name.decode("utf-8")).suffix == ".txt"
    )
    if not sources:
        raise SystemExit("No tracked Python requirements locks found")
    return sources


def stage(root: Path) -> None:
    staging = root / "osv-python-lockfiles"
    if staging.exists() or staging.is_symlink():
        raise SystemExit(f"OSV staging already exists: {staging}")

    sources = tracked_sources(root)

    for source in sources:
        if source.is_symlink() or not source.is_file():
            raise SystemExit(f"Tracked requirements lock is absent or symlinked: {source}")
        destination = staging / source.stem / "requirements.txt"
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        if destination.read_bytes() != source.read_bytes():
            raise SystemExit(f"OSV staging copy differs from source: {source}")

    staged = [child / "requirements.txt" for child in staging.iterdir() if (child / "requirements.txt").is_file()]
    if len(staged) != len(sources):
        raise SystemExit("OSV staging count differs from tracked lock count")
    print(f"OSV Python lockfiles staged and verified: {len(sources)}")


def canonical_name(name: str) -> str:
    """Apply the PyPI name equivalence rule without a regex engine."""
    result: list[str] = []
    for character in name.lower():
        if character in "-_.":
            if not result or result[-1] != "-":
                result.append("-")
        elif character.isascii() and character.isalnum():
            result.append(character)
        else:
            raise SystemExit(f"Invalid Python package name: {name}")
    if not result or result[0] == "-" or result[-1] == "-":
        raise SystemExit(f"Invalid Python package name: {name}")
    return "".join(result)


def pins(source: Path) -> set[tuple[str, str]]:
    expected: set[tuple[str, str]] = set()
    try:
        original = source.read_bytes()
    except OSError as exc:
        raise SystemExit(f"Cannot read tracked Python lock {source}: {exc}") from exc
    try:
        lines = original.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        digest = hashlib.sha256(original).hexdigest()
        raise SystemExit(
            f"Invalid UTF-8 in tracked Python lock {source} (source sha256 {digest}, bytes {exc.start}:{exc.end})"
        ) from None
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith(("#", "--hash=")):
            continue
        name, separator, remainder = line.partition("==")
        if not separator or not name or not remainder:
            raise SystemExit(f"Unsupported requirement in {source}: {line}")
        version_parts = remainder.partition(";")[0].split()
        if not version_parts:
            raise SystemExit(f"Missing pinned version in {source}: {line}")
        version = version_parts[0]
        expected.add((canonical_name(name), version))
    return expected


def verify(root: Path, result_file: Path) -> None:
    try:
        original = result_file.read_bytes()
    except OSError as exc:
        raise SystemExit(f"OSV scan result is unavailable: {result_file}: {exc}") from exc
    try:
        result = json.loads(original.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        digest = hashlib.sha256(original).hexdigest()
        raise SystemExit(f"OSV scan result is not valid UTF-8 JSON (source sha256 {digest})") from None
    if not isinstance(result, dict) or not isinstance(result.get("results"), list):
        raise SystemExit("OSV scan result has no results list")
    scanned: dict[Path, set[tuple[str, str]]] = {}
    for entry in result["results"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("source"), dict):
            raise SystemExit("OSV scan result has an invalid source entry")
        source = entry["source"]
        if not isinstance(source.get("path"), str):
            raise SystemExit("OSV scan result has a source without a path")
        parts = Path(source["path"]).parts
        if "osv-python-lockfiles" not in parts:
            continue
        path = Path(*parts[parts.index("osv-python-lockfiles") :])
        if path in scanned or source.get("type") != "lockfile":
            raise SystemExit(f"Unexpected OSV source entry: {path}")
        if not isinstance(entry.get("packages"), list):
            raise SystemExit(f"OSV source has no package list: {path}")
        packages: set[tuple[str, str]] = set()
        for item in entry["packages"]:
            if not isinstance(item, dict) or not isinstance(item.get("package"), dict):
                raise SystemExit(f"OSV source has an invalid package entry: {path}")
            package = item["package"]
            if package.get("ecosystem") != "PyPI":
                continue
            name, version = package.get("name"), package.get("version")
            if not isinstance(name, str) or not isinstance(version, str) or not version:
                raise SystemExit(f"OSV source has an incomplete Python package: {path}")
            packages.add((canonical_name(name), version))
        scanned[path] = packages

    sources = tracked_sources(root)
    expected = {
        Path("osv-python-lockfiles") / source.stem / "requirements.txt": pins(source)
        for source in sources
    }
    if len(expected) != len(sources):
        raise SystemExit("OSV alias names collide")
    if set(scanned) != {path for path, packages in expected.items() if packages}:
        raise SystemExit("OSV scanner did not discover every nonempty Python lock")
    for path, packages in expected.items():
        if scanned.get(path, set()) != packages:
            raise SystemExit(f"OSV package extraction differs from source: {path}")
    print(f"OSV Python coverage verified: {len(sources)} locks, {sum(map(len, expected.values()))} pins")


def cleanup(root: Path) -> None:
    staging = root / "osv-python-lockfiles"
    if staging.is_symlink():
        raise SystemExit(f"Refusing to remove symlinked OSV staging: {staging}")
    if staging.exists():
        shutil.rmtree(staging)
    result = root / "osv-scan-results.json"
    result.unlink(missing_ok=True)


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    if len(sys.argv) == 1:
        stage(root)
    elif len(sys.argv) == 3 and sys.argv[1] == "--verify":
        verify(root, Path(sys.argv[2]))
    elif len(sys.argv) == 2 and sys.argv[1] == "--cleanup":
        cleanup(root)
    else:
        raise SystemExit("usage: prepare_osv_python.py [--verify results.json | --cleanup]")
