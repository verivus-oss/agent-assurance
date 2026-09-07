#!/usr/bin/env python3
"""Build a pinned private database lane or loader and retain its executed receipt."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
import uuid
import zipfile

import _toml11 as toml


def run(command, root, env):
    # Commands are fixed build/test tools with list arguments, never a shell.
    result = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True)  # nosec B603 # noqa: S603
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {command[0]}\n{result.stdout}{result.stderr}")
    return result.stdout


def download(url, digest, target):
    if not url.startswith("https://"):
        raise ValueError("pinned build artifacts require HTTPS")
    with urllib.request.urlopen(url, timeout=60) as response:  # nosec B310 # noqa: S310
        data = response.read()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError("downloaded build artifact does not match its pinned SHA-256")
    target.write_bytes(data)


def build_sqlite(lane, work, env):
    archive = work / "sqlite.tar.gz"
    download(lane["source_url"], lane["source_sha256"], archive)
    source = work / "sqlite-source"
    source.mkdir()
    with tarfile.open(archive) as contents:
        contents.extractall(source, filter="data")
    roots = list(source.iterdir())
    if len(roots) != 1 or not roots[0].is_dir():
        raise ValueError("unexpected pinned SQLite source layout")
    prefix = work / "sqlite-install"
    for command in (["./configure", "--prefix=" + str(prefix), "CFLAGS=-O2 -DSQLITE_ENABLE_COLUMN_METADATA"],
                    ["make", "-j2"], ["make", "install"]):
        run(command, roots[0], env)
    return str(prefix / "lib")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--lane")
    selector.add_argument("--loader", choices=("rust", "go"))
    parser.add_argument("--container-runtime", choices=("docker", "podman"), default="docker")
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    lock = toml.loads((root / "reference/database/engine-lock.toml").read_text())
    name = args.lane or "duckdb-loader-" + args.loader
    lanes = {lane["id"]: lane for lane in lock["lanes"]}
    lane = lanes[args.lane or "duckdb-maintained"]
    output = root / ".local/database-ci"
    work = root / ".local/database-work" / name / uuid.uuid4().hex
    work.mkdir(parents=True)
    (work / "scratch").mkdir()
    (output / "receipts").mkdir(parents=True, exist_ok=True)
    receipt_path = output / "receipts" / (name + ".json")
    receipt_path.write_text(json.dumps({"status": "incomplete", "lane": name}))
    env = {**os.environ, "TMPDIR": str(work / "scratch"), "GOCACHE": str(work / "go-cache")}
    destination = str(work / ("agent_assurance.duckdb" if lane["engine"] == "duckdb" else "reference.db"))
    container = None
    loader_record = None
    try:
        if lane["engine"] == "sqlite":
            env["LD_LIBRARY_PATH"] = build_sqlite(lane, work, env)
        elif lane["engine"] == "postgres":
            runtime = shutil.which(args.container_runtime)
            if runtime is None:
                raise ValueError("selected container runtime is missing")
            container = "dagtoml-vocabulary-" + uuid.uuid4().hex
            run([runtime, "run", "-d", "--rm", "--name", container, "-e", "POSTGRES_PASSWORD=dagtoml-ci",
                 "-p", "127.0.0.1::5432", lane["image"]], root, env)
            address = run([runtime, "port", container, "5432/tcp"], root, env).strip()
            if not address.startswith("127.0.0.1:") or not address.removeprefix("127.0.0.1:").isdigit():
                raise ValueError("container database is not bound to a single loopback port")
            destination = "host=127.0.0.1 port=" + address.split(":")[1] + " user=postgres password=dagtoml-ci dbname=postgres"
            import psycopg
            for attempt in range(120):
                try:
                    with psycopg.connect(destination, autocommit=True):
                        break
                except psycopg.OperationalError:
                    if attempt == 119:
                        raise
                    time.sleep(0.25)
        if args.loader:
            archive = work / "duckdb.zip"
            download(lock["duckdb_cli"]["url"], lock["duckdb_cli"]["sha256"], archive)
            with zipfile.ZipFile(archive) as contents:
                if "duckdb" not in contents.namelist():
                    raise ValueError("pinned DuckDB CLI archive contains no duckdb binary")
                (work / "duckdb").write_bytes(contents.read("duckdb"))
            (work / "duckdb").chmod(0o755)
            if args.loader == "rust":
                run(["cargo", "build", "--release", "--locked", "--manifest-path", "tools/dagtoml-duckdb/Cargo.toml"], root, env)
                built = root / "tools/dagtoml-duckdb/target/release/dagtoml-duckdb"
            else:
                built = work / "dagtoml-duckdb-go"
                run(["go", "build", "-o", str(built), "./..."], root / "tools/dagtoml-duckdb-go", env)
            published_binary = output / "bin" / args.loader / built.name
            published_binary.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(built, published_binary)
            build_output = run([str(published_binary), "--repo-root", str(root), "--duckdb", str(work / "duckdb"),
                                "-o", destination], root, env)
            (output / ("loader-" + args.loader + "-build.log")).write_text(build_output)
            from check_database_vocabularies import source_identity
            loader_record = {"language": args.loader, "source_commit": source_identity(root)["commit"],
                             "binary": published_binary.relative_to(root).as_posix(),
                             "binary_sha256": hashlib.sha256(published_binary.read_bytes()).hexdigest()}
        command = [sys.executable, str(root / "validators/check_database_vocabularies.py"), "--repo-root", str(root),
                   "--engine", lane["engine"], "--destination", destination, "--expected-version", lane["version"],
                   "--lane", name, "--receipt", str(receipt_path)]
        if args.loader:
            command.append("--existing-seed")
        print(run(command, root, env), end="")
        if loader_record:
            receipt = json.loads(receipt_path.read_text())
            receipt["loader"] = loader_record
            receipt_path.write_text(json.dumps(receipt, ensure_ascii=True, sort_keys=True, indent=2) + "\n")
    finally:
        if container is not None:
            run([runtime, "rm", "-f", container], root, env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
