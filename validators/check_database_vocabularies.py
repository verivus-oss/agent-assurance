#!/usr/bin/env python3
"""Execute the reference SQL artifacts and retain an artifact-bound test receipt."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reference/database"))
from _contract import artifact_hashes, bundle_digest, bundle_entries  # noqa: E402
from _storage import Store, connect  # noqa: E402
from _storage_checks import exercise_storage  # noqa: E402
from _protocol_checks import exercise_protocol  # noqa: E402
from _concurrency_checks import initialize_checks, writer_checks  # noqa: E402
from _replay_checks import exercise_replay  # noqa: E402
from _connection_checks import exercise_connection  # noqa: E402


def source_identity(root: Path) -> dict:
    def git(*args):
        binary = shutil.which("git")
        if binary is None:
            raise ValueError("Git is required to bind the receipt to a source commit")
        # Fixed read-only Git subcommands, list arguments, no shell.
        return subprocess.run([binary, *args], cwd=root, check=True, capture_output=True).stdout  # nosec B603 # noqa: S603
    tracked = set(git("ls-files", "-z").decode().split("\0"))
    return {"commit": git("rev-parse", "HEAD").decode().strip(),
            "tracked_tree_clean": not bool(git("status", "--porcelain", "--untracked-files=no")),
            "bundle_files_tracked": set(bundle_entries(root)) <= tracked,
            "diff_sha256": hashlib.sha256(git("diff", "HEAD", "--binary")).hexdigest()}


def engine_version(store: Store) -> str:
    query = {"postgres": "SHOW server_version", "sqlite": "SELECT sqlite_version()", "duckdb": "SELECT version()"}[store.engine]
    return store.execute(query).fetchone()[0].split()[0].removeprefix("v")


def run_lane(root: Path, engine: str, destination: str, expected_version: str, lane: str, *, existing_seed=False) -> dict:
    if destination == ":memory:":
        raise ValueError("full executed lanes require a persistent private destination for connection-loss tests")
    identity = source_identity(root)
    hashes = artifact_hashes(root)
    digest = bundle_digest(root)
    connection = connect(engine, destination)
    store = Store(engine, connection, root, reconnect=lambda: connect(engine, destination))
    try:
        actual_version = engine_version(store)
        if actual_version != expected_version:
            raise ValueError(f"wrong engine version: selected {expected_version}, connected {actual_version}")
        store.prepare()
        if not existing_seed:
            # Execution is the only interpretation of SQL source. Schema/seed
            # load failures are infrastructure failures, never negative probes.
            for name in ("schema", "seed"):
                sql = (root / f"reference/database/{engine}/{name}.sql").read_text(encoding="utf-8")
                if engine == "sqlite":
                    connection.executescript(sql)
                else:
                    connection.execute(sql)
        counts = store.verify_catalog()
        if any(counts[name] for name in ("instance_file", "reference_contract", "runtime_document")):
            raise ValueError("schema/seed must leave the instance and initialization populations empty")
        # The table identifier is selected from the closed engine map.
        pairs = store.execute(f"SELECT attribute,value FROM {store.table('attribute_value_allowed')} ORDER BY attribute,value").fetchall()  # nosec B608 # noqa: S608
        work = root / ".local/database-checks" / lane / uuid.uuid4().hex
        work.mkdir(parents=True)
        connection_checks = exercise_connection(store, destination)
        initialization_checks = initialize_checks(store, work)
        initialization = store.initialize(exclusive_unpublished=True)
        if initialization["status"] != "initialized" or store.counts()["reference_contract"] != 1:
            raise AssertionError("initializer did not publish exactly one contract row")
        if store.initialize(exclusive_unpublished=True)["status"] != "already-initialized":
            raise AssertionError("empty same-bundle initialization must be idempotent")
        replay_checks = exercise_replay(store, work / "replay-originals")
        storage_checks = exercise_storage(store)
        protocol_checks = exercise_protocol(store)
        concurrency_checks = writer_checks(store, destination)
        if source_identity(root) != identity or artifact_hashes(root) != hashes or bundle_digest(root) != digest:
            raise ValueError("source or SQL artifacts changed while the executed gate was running")
        return {"receipt_version": 1, "status": "passed", "lane": lane, "engine": engine,
                "expected_version": expected_version, "actual_version": actual_version, "source": identity,
                "artifacts": hashes, "contract_bundle_sha256": digest, "seed_counts": counts,
                "allowed_pairs": pairs, "constraint_probes": initialization["probes"],
                "storage_checks": storage_checks, "protocol_checks": protocol_checks, "skipped": [],
                "initialization_checks": initialization_checks, "concurrency_checks": concurrency_checks,
                "replay_checks": replay_checks,
                "connection_checks": connection_checks,
                "excluded": ["libSQL compatibility", "runtime execution", "signature verification", "evidence authenticity"]}
    finally:
        store.connection.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--engine", required=True, choices=("postgres", "sqlite", "duckdb"))
    parser.add_argument("--destination", required=True, help="fresh private database, or isolated existing seed-only loader output")
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--lane", required=True)
    parser.add_argument("--existing-seed", action="store_true")
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args(argv)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    try:
        receipt = run_lane(args.repo_root.resolve(), args.engine, args.destination, args.expected_version,
                           args.lane, existing_seed=args.existing_seed)
    except Exception as exc:
        args.receipt.write_text(json.dumps({"status": "failed", "lane": args.lane,
                                           "error": str(exc), "exception": type(exc).__name__}, indent=2))
        raise
    args.receipt.write_text(json.dumps(receipt, ensure_ascii=True, sort_keys=True, indent=2) + "\n")
    print(f"PASS lane {args.lane}: connected {args.engine} {receipt['actual_version']}; "
          f"{len(receipt['constraint_probes'])} SQL probes, {len(receipt['storage_checks'])} storage checks, "
          f"and {len(receipt['protocol_checks'])} protocol checks; "
          f"{len(receipt['initialization_checks'])} initialization and {len(receipt['concurrency_checks'])} concurrency checks; "
          f"{len(receipt['replay_checks'])} replay and {len(receipt['connection_checks'])} connection checks; "
          "compared with discovered ontology and fixed storage expectations; skipped=[]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
