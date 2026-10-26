#!/usr/bin/env python3
"""Build validator and syscall instruments, then execute the required gates."""

import os
from pathlib import Path
import sys
import tarfile
import uuid

import _toml11 as toml
from database_ci import download, run


def main():
    root = Path(__file__).resolve().parents[1]
    work = root / ".local/runtime-ci" / uuid.uuid4().hex
    work.mkdir(parents=True)
    (work / "scratch").mkdir()
    env = {**os.environ, "TMPDIR": str(work / "scratch"), "GOCACHE": str(work / "go-cache"),
           "PYTHONDONTWRITEBYTECODE": "1"}
    lock = toml.loads((root / "reference/database/engine-lock.toml").read_text())["syscall_instrument"]
    archive = work / "strace.tar.xz"
    download(lock["source_url"], lock["source_sha256"], archive)
    source = work / "strace-source"
    source.mkdir()
    with tarfile.open(archive) as contents:
        contents.extractall(source, filter="data")
    directories = list(source.iterdir())
    if len(directories) != 1 or not directories[0].is_dir():
        raise ValueError("unexpected pinned strace source layout")
    prefix = work / "strace-install"
    for command in (["./configure", "--prefix=" + str(prefix), "--enable-mpers=no"], ["make", "-j2"], ["make", "install"]):
        run(command, directories[0], env)
    strace = prefix / "bin/strace"
    version = run([str(strace), "--version"], root, env).splitlines()[0]
    if version != "strace -- version " + lock["version"]:
        raise ValueError("actual syscall instrument version differs from its lock")
    run(["cargo", "build", "--release", "--locked", "--manifest-path", "tools/dagtoml-validate-rs/Cargo.toml"], root, env)
    rust = root / "tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs"
    go = work / "dagtoml-validate-go"
    run(["go", "build", "-o", str(go), "./..."], root / "tools/dagtoml-validate-go", env)
    receipt = work / "runtime-receipt.json"
    for command in (
        [sys.executable, "validators/check_runtime_documents.py", "--rs", str(rust), "--go", str(go),
         "--strace", str(strace), "--work-dir", str(work / "specimens"), "--receipt", str(receipt)],
        [sys.executable, "validators/check_runtime_ownership.py", "--receipt", str(receipt)],
        [sys.executable, "validators/check_database_instruments.py"],
    ):
        print(run(command, root, env), end="", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
