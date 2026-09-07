#!/usr/bin/env python3
"""Replay original source versions into an empty, initialized private destination."""

import argparse
import hashlib
import json
from pathlib import Path
from contextlib import suppress

from _projection import project, text_identity
from _storage import Store, StorageError, connect
import _toml11 as toml


def replay(store: Store, entries: list[dict], *, manifest_directory: Path, exclusive_unpublished=False) -> dict:
    if exclusive_unpublished is not True:
        raise StorageError("ownership-required", "replay requires an unpublished private destination")
    store.prepare()
    store._empty()
    if not isinstance(entries, list) or not entries:
        raise ValueError("replay manifest needs at least one sources entry")
    captured, report = [], []
    for index, entry in enumerate(entries):
        try:
            if not isinstance(entry, dict):
                raise ValueError("sources entry must be a table")
            source_path = text_identity(entry.get("source_path"), "sources.source_path")
            file_name = text_identity(entry.get("source_file"), "sources.source_file")
            expected_hash = text_identity(entry.get("content_sha256"), "sources.content_sha256")
            source = (manifest_directory / file_name).read_bytes()
            actual_hash = "sha256:" + hashlib.sha256(source).hexdigest()
            if actual_hash != expected_hash:
                raise ValueError("original source bytes do not match the legacy instance content_sha256")
            project(source, source_path, store.root)
            captured.append((source_path, source))
            report.append({"entry": index, "source_path": source_path, "status": "validated-pending-batch"})
        except (ValueError, OSError) as exc:
            report.append({"entry": index, "source_path": entry.get("source_path") if isinstance(entry, dict) else None,
                           "status": "failed", "error": str(exc)})
    if any(row["status"] == "failed" for row in report):
        return {"status": "failed", "committed_documents": 0, "entries": report}
    result = store.ingest(captured)
    for row, committed in zip(report, result["documents"], strict=True):
        row.update(status="committed", id=committed["id"])
    return {"status": "committed", "committed_documents": len(report), "entries": report,
            "contract_bundle_sha256": result["contract_bundle_sha256"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", required=True, choices=("postgres", "sqlite", "duckdb"))
    parser.add_argument("--destination", required=True)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--exclusive-unpublished", action="store_true")
    args = parser.parse_args(argv)
    def reconnect():
        return connect(args.engine, args.destination)
    store = None
    try:
        store = Store(args.engine, reconnect(), args.repo_root, reconnect=reconnect)
        manifest = toml.loads(args.manifest.read_text())
        result = replay(store, manifest.get("sources"), manifest_directory=args.manifest.resolve().parent,
                        exclusive_unpublished=args.exclusive_unpublished)
    except (ValueError, OSError, StorageError) as exc:
        code = exc.code if isinstance(exc, StorageError) else "invalid-input-or-setup"
        result = {"status": code if code in {"commit-outcome-unknown", "rollback-unconfirmed"} else "failed",
                  "code": code, "error": str(exc)}
    except Exception as exc:
        result = {"status": "failed", "code": "database-operation-failed", "exception": type(exc).__name__}
    finally:
        with suppress(Exception):
            if store is not None:
                store.connection.close()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=True, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=True))
    return int(result["status"] != "committed")


if __name__ == "__main__":
    raise SystemExit(main())
