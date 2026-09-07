#!/usr/bin/env python3
"""Initialize, ingest, or audit runtime documents in a reference SQL mirror."""

import argparse
import json
from pathlib import Path
import sys
from contextlib import suppress

from _storage import Store, StorageError, connect


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", required=True, choices=("postgres", "sqlite", "duckdb"))
    parser.add_argument("--destination", required=True, help="database file or PostgreSQL connection string")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    actions = parser.add_subparsers(dest="action", required=True)
    initialize = actions.add_parser("initialize")
    initialize.add_argument("--exclusive-unpublished", action="store_true", help="assert exclusive ownership of an unpublished destination")
    ingest = actions.add_parser("ingest")
    ingest.add_argument("paths", type=Path, nargs="+")
    actions.add_parser("audit")
    args = parser.parse_args(argv)
    connection = None
    store = None
    try:
        def reconnect():
            return connect(args.engine, args.destination)
        connection = reconnect()
        store = Store(args.engine, connection, args.repo_root, reconnect=reconnect)
        if args.action == "initialize":
            result = store.initialize(exclusive_unpublished=args.exclusive_unpublished)
        elif args.action == "ingest":
            result = store.ingest([(str(path), path.read_bytes()) for path in args.paths])
        else:
            result = store.audit()
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return int(result["status"] == "failed")
    except (ValueError, OSError, StorageError) as exc:
        code = getattr(exc, "code", "invalid-input-or-setup")
        status = code if code in {"commit-outcome-unknown", "rollback-unconfirmed"} else "failed"
        print(json.dumps({"status": status, "code": code, "error": str(exc), **getattr(exc, "context", {})}, ensure_ascii=True), file=sys.stderr)
        return 1
    except Exception as exc:
        # Driver diagnostics may include complete rejected rows. Preserve the
        # exception class without echoing document bytes or connection details.
        print(json.dumps({"status": "failed", "code": "database-operation-failed", "exception": type(exc).__name__}), file=sys.stderr)
        return 1
    finally:
        # Connection disposal does not change an acknowledged write outcome.
        with suppress(Exception):
            if store is not None:
                store.connection.close()
            elif connection is not None:
                connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
