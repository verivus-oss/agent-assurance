#!/usr/bin/env python3
"""Run fixed-string CI text checks without pattern matching."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import _toml11 as toml


ROOT = Path(__file__).resolve().parents[1]

def toml_files(folder: Path) -> list[Path]:
    found = []
    for directory, children, names in os.walk(folder):
        children[:] = [name for name in children if not name.startswith(".")]
        found.extend(Path(directory) / name for name in names if name.endswith(".toml"))
    return sorted(found)


def has_provenance(path: Path) -> bool:
    return any(line.startswith("[provenance]") for line in path.read_text().splitlines())


def provenance() -> None:
    files = toml_files(ROOT)
    positives = [path for path in files if "examples/negative" not in path.relative_to(ROOT).as_posix()
                 and has_provenance(path)]
    negatives = [path for path in toml_files(ROOT / "examples/negative") if has_provenance(path)]
    if not positives or not negatives:
        raise ValueError("provenance positive or negative source population is empty")
    command = [sys.executable, str(ROOT / "validators/validate_provenance.py")]
    accepted = subprocess.run(command + [str(path) for path in positives] + ["--repo-root", str(ROOT)],  # nosec B603  # noqa: S603
                              cwd=ROOT, capture_output=True, text=True, check=False)
    if accepted.returncode:
        raise ValueError("positive provenance sweep failed: " + accepted.stdout + accepted.stderr)
    for path in negatives:
        rejected = subprocess.run(command + [str(path), "--repo-root", str(ROOT)], cwd=ROOT,  # nosec B603  # noqa: S603
                                  capture_output=True, text=True, check=False)
        if rejected.returncode != 1:
            raise ValueError("negative provenance fixture was not rejected: " + str(path))
    print(f"provenance: {len(positives)} positive files accepted, {len(negatives)} negative files rejected")


def language_symbols() -> None:
    source = ROOT / "examples/language-validation/traceability.toml"
    rows = toml.loads(source.read_text()).get("code", [])
    if not rows or len(rows) != len({row.get("id") for row in rows}):
        raise ValueError("language fixture code declarations are missing or duplicated")
    for row in rows:
        relative, symbol = row.get("path"), row.get("symbol")
        if (not isinstance(relative, str) or not relative.startswith("examples/language-validation/src/")
                or not isinstance(symbol, str) or not symbol):
            raise ValueError("language fixture code declaration is incomplete")
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT / "examples/language-validation/src"):
            raise ValueError("language fixture code path escapes its source tree")
        if not path.is_file() or symbol not in path.read_text():
            raise ValueError("language fixture symbol missing: " + relative + " " + symbol)
    print(f"language fixtures: {len(rows)} declared symbols found")


def tracked_files() -> list[Path]:
    git = shutil.which("git")
    if git is None:
        raise ValueError("git executable is required")
    result = subprocess.run([git, "ls-files", "-z"], cwd=ROOT, capture_output=True, check=False)  # nosec B603  # noqa: S603
    if result.returncode:
        raise ValueError("could not enumerate tracked files")
    paths = [ROOT / os.fsdecode(name) for name in result.stdout.split(b"\0") if name]
    if len(paths) < 100 or ROOT / "spec.md" not in paths or ROOT / "core/ontology.toml" not in paths:
        raise ValueError("tracked source population is incomplete")
    return paths


def banned_markers() -> None:
    examples = toml_files(ROOT / "examples")
    if not examples:
        raise ValueError("example TOML population is empty")
    for path in examples:
        for line in path.read_text().splitlines():
            field, separator, _ = line.partition("=")
            if separator and field.strip() == "kind":
                raise ValueError("bare kind field found in " + str(path.relative_to(ROOT)))
    needle = "/srv/" + "repos/internal"
    scanned = 0
    for path in tracked_files():
        relative = path.relative_to(ROOT)
        if relative.parts[0] in (".github", ".git", ".local") or relative.parts[:2] == ("docs", "reviews"):
            continue
        if relative.name in ("AGENTS.md", "CHANGELOG.md"):
            continue
        if needle.encode() in path.read_bytes():
            raise ValueError("internal path found in " + str(relative))
        scanned += 1
    if scanned < 100:
        raise ValueError("internal path scan population is incomplete")
    print(f"banned markers: {len(examples)} example TOML files and {scanned} tracked files checked")


def make_help(paths: list[str]) -> None:
    if not paths:
        raise ValueError("make-help requires a Makefile")
    count = 0
    for source in paths:
        path = Path(source)
        for line in path.read_text().splitlines():
            target, colon, remainder = line.partition(":")
            marker = remainder.find("## ")
            if colon and marker >= 0 and target and all(
                char.isascii() and (char.isalpha() or char in "_-" ) for char in target
            ):
                print("  " + target.ljust(32) + " " + remainder[marker + 3:])
                count += 1
    if not count:
        raise ValueError("no documented Make targets found")


def main(args: list[str]) -> None:
    if args == ["provenance"]:
        provenance()
    elif args == ["language-symbols"]:
        language_symbols()
    elif args == ["banned-markers"]:
        banned_markers()
    elif args and args[0] == "make-help":
        make_help(args[1:])
    else:
        raise ValueError("expected provenance, language-symbols, banned-markers, or make-help")


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except (OSError, ValueError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
