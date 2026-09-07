"""Copy repository sources into persistent ignored test workspaces."""

from pathlib import Path
import shutil
import subprocess
import hashlib


def copy_source(root: Path, target: Path):
    if target.exists():
        raise ValueError("isolated source destination must not already exist")
    binary = shutil.which("git")
    if binary is None:
        raise ValueError("Git is required to discover the source population")
    names = subprocess.run([binary, "ls-files", "--cached", "--others", "--exclude-standard", "-z"],  # nosec B603 # noqa: S603
                           cwd=root, check=True, capture_output=True).stdout.decode().split("\0")  # nosec B603 # noqa: S603
    files = {name for name in names if name and not name.endswith(".zip")}
    if not files or "spec.md" not in files:
        raise ValueError("isolated copy source population is missing")
    target.mkdir(parents=True)
    copied = {}
    for name in sorted(files):
        source = root / name
        if not source.resolve().is_relative_to(root.resolve()):
            raise ValueError("isolated source contains an escaping symlink")
        if source.is_file():
            destination = target / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            copied[name] = hashlib.sha256(destination.read_bytes()).hexdigest()
    commit = subprocess.run([binary, "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True).stdout.decode().strip()  # nosec B603 # noqa: S603
    return {"source_commit": commit, "copied_files": len(copied), "content_sha256": copied,
            "excluded": ["ignored files", "untracked ZIP archives"]}
