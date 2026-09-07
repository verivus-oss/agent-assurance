"""Private-destination initialization and writer concurrency acceptance tests."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
import threading
from unittest.mock import patch

from _contract import bundle_digest, bundle_entries
from _storage import Store, StorageError


def initialize_checks(store: Store, work: Path) -> list[dict]:
    store._empty()
    if store.contract():
        raise AssertionError("initialization tests require an empty, uninitialized private destination")
    if not store.reconnect:
        raise AssertionError("initialization tests require a real reconnect factory")
    outcomes = []
    alternate = work / "alternate-bundle"
    for relative in bundle_entries(store.root):
        target = alternate / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((store.root / relative).read_bytes())
    with (alternate / "spec.md").open("a") as handle:
        handle.write("\n<!-- Isolated different-bundle initialization test. -->\n")
    if bundle_digest(alternate) == bundle_digest(store.root):
        raise AssertionError("different-bundle race has identical subjects")

    def reset_private():
        store._empty()
        store.execute(f"DELETE FROM {store.table('reference_contract')}")  # nosec B608 # noqa: S608

    for name, roots in (("same-bundle", (store.root, store.root)), ("different-bundle", (store.root, alternate))):
        barrier = threading.Barrier(2)

        def contender(root):
            candidate = Store(store.engine, store.reconnect(), root, reconnect=store.reconnect)
            try:
                barrier.wait(timeout=20)
                return candidate.initialize(exclusive_unpublished=True)
            except StorageError as exc:
                return {"status": exc.code}
            finally:
                candidate.connection.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(contender, root) for root in roots]
            results = [future.result(timeout=120) for future in futures]
        statuses = sorted(result["status"] for result in results)
        if statuses.count("initialized") != 1:
            raise AssertionError(f"{name}: race did not produce exactly one initializer: {results!r}")
        allowed_other = {"already-initialized", "retryable-busy"} if name == "same-bundle" else {"contract-mismatch", "retryable-busy"}
        if next(status for status in statuses if status != "initialized") not in allowed_other:
            raise AssertionError(f"{name}: wrong committed-state reconciliation: {results!r}")
        singleton = store.contract()
        if len(singleton) != 1 or store.counts()["instance_file"] or store.counts()["runtime_document"]:
            raise AssertionError("racing probes leaked state or overwrote the singleton")
        winner = next(result for result in results if result["status"] == "initialized")
        if singleton[0]["contract_bundle_sha256"] != winner["contract_bundle_sha256"]:
            raise AssertionError("losing initializer overwrote the winner")
        outcomes.append({"check": name + "-initializers", "barrier_participants": 2, "outcomes": statuses})
        reset_private()

    class LoseInitializationAcknowledgement(Store):
        fired = False

        def execute(self, sql, parameters=()):
            result = super().execute(sql, parameters)
            if sql == "COMMIT" and not self.fired:
                self.fired = True
                raise OSError("injected lost initialization commit acknowledgement")
            return result

    fault = LoseInitializationAcknowledgement(store.engine, store.connection, store.root, reconnect=store.reconnect)
    try:
        receipt = fault.initialize(exclusive_unpublished=True)
    finally:
        store.connection = fault.connection
    if receipt.get("status") != "already-initialized" or receipt.get("reconciled_commit") is not True:
        raise AssertionError("initialization acknowledgement loss did not reconcile committed state")
    outcomes.append({"check": "initialization-commit-acknowledgement-loss", "outcome": "reconciled"})
    reset_private()
    digest = bundle_digest(store.root)
    for phase in ("existing", "after-probes", "before-publish", "reconciliation"):
        reset_private()
        candidate = store
        def concurrent_publication(subject, expected):
            if expected != digest:
                raise AssertionError("probe received a different bundle")
            subject.insert("reference_contract", {"singleton_id": 1, "contract_bundle_sha256": digest, "projection_version": 1})
            return []
        if phase == "existing":
            concurrent_publication(store, digest)
        if phase == "reconciliation":
            candidate = LoseInitializationAcknowledgement(store.engine, store.connection, store.root, reconnect=store.reconnect)
        sequence = [digest, digest, "f" * 64] if phase == "reconciliation" else [digest, "f" * 64]
        from contextlib import nullcontext
        probe_context = patch("_sql_probes.probe_constraints", side_effect=concurrent_publication) if phase == "after-probes" else nullcontext()
        with probe_context, patch("_storage.bundle_digest", side_effect=sequence):
            try:
                candidate.initialize(exclusive_unpublished=True)
            except StorageError as exc:
                expected_code = "commit-outcome-unknown" if phase == "reconciliation" else "bundle-changed"
                if exc.code != expected_code:
                    raise AssertionError("bundle-change control failed for the wrong reason") from exc
                if phase == "reconciliation" and (exc.context != {"operation": "initialize", "contract_bundle_sha256": digest}
                                                  or not isinstance(exc.__cause__, StorageError) or exc.__cause__.code != "bundle-changed"):
                    raise AssertionError("indeterminate initialization lost identity or bundle-change cause")
                outcomes.append({"check": "initialization-bundle-change-" + phase, "outcome": expected_code})
            else:
                raise AssertionError("initialization returned success after bundle changed: " + phase)
            finally:
                store.connection = candidate.connection
        reset_private()
    if len(outcomes) != 7:
        raise AssertionError("initialization concurrency check population changed")
    return outcomes


def writer_checks(store: Store, destination: str) -> list[dict]:
    raw = (store.root / "examples/minimal-adapter-contract.toml").read_bytes()
    barrier = threading.Barrier(2)

    def contender():
        candidate = Store(store.engine, store.reconnect(), store.root, reconnect=store.reconnect)
        try:
            barrier.wait(timeout=20)
            return candidate.ingest([("concurrent/repeat.toml", raw)])
        except StorageError as exc:
            return {"status": exc.code}
        finally:
            candidate.connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(contender) for _ in range(2)]
        results = [future.result(timeout=60) for future in futures]
    committed = [result for result in results if result["status"] == "committed"]
    if not committed or any(result["status"] not in {"committed", "retryable-busy"} for result in results):
        raise AssertionError("concurrent writers did not reach a supported committed/busy outcome")
    ids = {result["documents"][0]["id"] for result in committed}
    if len(ids) != 1 or len(store.rows("instance_file", ("id",), "WHERE source_path = ?", ("concurrent/repeat.toml",))) != 1:
        raise AssertionError("concurrent repeats created duplicate or conflicting source identities")
    checks = [{"check": "concurrent-identical-writers", "barrier_participants": 2,
               "outcomes": [result["status"] for result in results]}]
    if store.engine == "sqlite":
        store.execute("BEGIN IMMEDIATE")

        def blocked_writer():
            candidate = Store(store.engine, store.reconnect(), store.root, reconnect=store.reconnect)
            try:
                candidate.ingest([("concurrent/blocked.toml", raw)])
            except StorageError as exc:
                return exc.code
            finally:
                candidate.connection.close()
            raise AssertionError("locked SQLite writer unexpectedly committed")

        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                outcome = pool.submit(blocked_writer).result(timeout=20)
            if outcome != "retryable-busy":
                raise AssertionError("SQLite lock exhaustion did not return explicit retryable-busy")
        finally:
            store.execute("ROLLBACK")
        if store.rows("instance_file", ("id",), "WHERE source_path = ?", ("concurrent/blocked.toml",)):
            raise AssertionError("busy writer left a partial document")
        checks.append({"check": "sqlite-writer-lock-exhaustion", "outcome": outcome})
    elif store.engine == "duckdb":
        code = '''import json,sys
sys.path.insert(0,sys.argv[1])
from _storage import connect,StorageError
try:
    connection=connect("duckdb",sys.argv[2])
except StorageError as exc:
    print(json.dumps({"status":exc.code}))
    sys.exit(0 if exc.code=="busy/unsupported-writer" else 1)
connection.close()
sys.exit(1)
'''
        result = subprocess.run([sys.executable, "-c", code, str(store.root / "reference/database"), destination],  # nosec B603 # noqa: S603
                                check=False, capture_output=True, text=True, timeout=20)
        if result.returncode != 0 or json.loads(result.stdout).get("status") != "busy/unsupported-writer":
            raise AssertionError("external DuckDB writer was not refused at file-open")
        checks.append({"check": "duckdb-external-writer-process", "outcome": "busy/unsupported-writer"})
    else:
        # PostgreSQL permits independent writable connections. Both contenders
        # must finish the duplicate reconciliation, without an embedded lock.
        if len(committed) != 2:
            raise AssertionError("PostgreSQL duplicate writer did not reconcile to the committed document")
        checks.append({"check": "postgres-duplicate-reconciliation", "outcome": "both-committed-same-id"})
    if len(checks) != 2 or store.audit()["status"] != "consistent":
        raise AssertionError("writer concurrency checks did not complete consistently")
    return checks
