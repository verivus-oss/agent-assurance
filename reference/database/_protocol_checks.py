"""Real-driver commit acknowledgement and provenance protocol witnesses."""


import hashlib

from _storage import Store, StorageError
from _projection import timestamp_index
from _instrument import require
from unittest.mock import patch

CHECKS = frozenset({"provenance-atomic-row-upstream-subject-and-portable-index", "audit-and-repeat-compare-provenance",
                   "lost-commit-acknowledgement-reconciles-whole-batch", "confirmed-uncommitted-batch-retries-whole-operation",
                   "unavailable-reconciliation-reports-indeterminate-outcome", "changed-bundle-before-commit-rolls-back",
                   "rollback-acknowledgement-loss-preserves-pre-commit-error"})


def exercise_protocol(store: Store) -> list[str]:
    checks = []
    raw = (store.root / "examples/minimal-adapter-contract.toml").read_bytes()
    source = (store.root / "LICENSE").read_bytes()
    upstream = "sha256:" + hashlib.sha256(source).hexdigest()
    closure = "sha256:" + hashlib.sha256(("provenance.source_sha256 " + upstream + "\n").encode()).hexdigest()
    sentinel = "sha256:" + hashlib.sha256(b"").hexdigest()
    authored = raw.replace(sentinel.encode(), closure.encode()) + (f'''
[provenance]
source_path = "LICENSE"
source_sha256 = "{upstream}"
source_bytes = {len(source)}
captured_at = "2026-09-07T12:00:00+10:00"
extraction_method = "fixed-fixture"
source_description = "retained\\u0000description"
opaque_extra = {{ values = [true, 1, "\u0063\u0061\u0066\u00e9"] }}
''').encode()
    result = store.ingest([("protocol/provenance.toml", authored)])
    record = result["documents"][0]
    require(record["unindexed_fields"] == [["provenance", "source_description"]])
    provenance = store.rows("provenance", ("source_path", "source_sha256", "source_bytes", "source_description"),
                            "WHERE instance_file_id = ?", (record["id"],))[0]
    require(provenance == {"source_path": "LICENSE", "source_sha256": upstream,
                          "source_bytes": len(source), "source_description": None})
    require(store.ingest([("protocol/provenance.toml", authored)]) == result)
    require(record["content_sha256"] != upstream)
    require(store.audit()["status"] == "consistent")
    captured = store.rows("provenance", ("captured_at",), "WHERE instance_file_id = ?", (record["id"],))[0]
    require(timestamp_index(captured["captured_at"]) == "2026-09-07T02:00:00Z")
    for index, offset in enumerate((b"+00:99", b"-01:75")):
        invalid_offset = authored.replace(b"+10:00", offset)
        omitted = store.ingest([(f"protocol/invalid-offset-{index}.toml", invalid_offset)])["documents"][0]
        require(["provenance", "captured_at"] in omitted["unindexed_fields"])
        captured = store.rows("provenance", ("captured_at",), "WHERE instance_file_id = ?", (omitted["id"],))[0]
        require(captured["captured_at"] is None)
    checks.append("provenance-atomic-row-upstream-subject-and-portable-index")
    store.execute(f"UPDATE {store.table('provenance')} SET source_description = ? WHERE instance_file_id = ?",  # nosec B608 # noqa: S608
                  ("corrupted", record["id"]))
    try:
        store.ingest([("protocol/provenance.toml", authored)])
    except StorageError as exc:
        require(exc.code == "stored-document-conflict")
    else:
        raise AssertionError("repeat did not detect changed provenance")
    require(store.audit()["status"] == "failed")
    store.execute(f"UPDATE {store.table('provenance')} SET source_description = NULL WHERE instance_file_id = ?", (record["id"],))  # nosec B608 # noqa: S608
    checks.append("audit-and-repeat-compare-provenance")

    class LoseAcknowledgement(Store):
        fired = False
        commit_reached_engine = True

        def execute(self, sql, parameters=()):
            if sql == "COMMIT" and not self.fired:
                self.fired = True
                super().execute("COMMIT" if self.commit_reached_engine else "ROLLBACK")
                raise OSError("injected lost commit acknowledgement")
            return super().execute(sql, parameters)

    if store.reconnect is None:
        raise AssertionError("full protocol checks require a reconnectable persistent destination")
    fault = LoseAcknowledgement(store.engine, store.connection, store.root, reconnect=store.reconnect)
    try:
        reconciled = fault.ingest([("protocol/acknowledged-elsewhere.toml", raw), ("protocol/provenance.toml", authored)])
    finally:
        store.connection = fault.connection
    require(reconciled["status"] == "committed" and reconciled["reconciled_commit"] is True)
    require(len(reconciled["documents"]) == 2 and reconciled["documents"][1]["id"] == record["id"])
    require(store.audit()["status"] == "consistent")
    checks.append("lost-commit-acknowledgement-reconciles-whole-batch")

    fault = LoseAcknowledgement(store.engine, store.connection, store.root, reconnect=store.reconnect)
    fault.commit_reached_engine = False
    try:
        retried = fault.ingest([("protocol/not-committed-first-attempt.toml", raw), ("protocol/provenance.toml", authored)])
    finally:
        store.connection = fault.connection
    require(retried["status"] == "committed" and retried["reconciled_commit"] is False)
    require(len(retried["documents"]) == 2 and retried["documents"][1]["id"] == record["id"])
    require(store.audit()["status"] == "consistent")
    checks.append("confirmed-uncommitted-batch-retries-whole-operation")

    fault = LoseAcknowledgement(store.engine, store.connection, store.root)
    try:
        fault.ingest([("protocol/indeterminate.toml", raw)])
    except StorageError as exc:
        require(exc.code == "commit-outcome-unknown")
        from _contract import bundle_digest
        require(exc.context == {"operation": "ingest", "contract_bundle_sha256": bundle_digest(store.root),
                               "documents": [{"source_path": "protocol/indeterminate.toml",
                                              "content_sha256": "sha256:" + hashlib.sha256(raw).hexdigest()}]})
    else:
        raise AssertionError("lost acknowledgement without reconciliation must not report success")
    require(store.audit()["status"] == "consistent")
    checks.append("unavailable-reconciliation-reports-indeterminate-outcome")
    from _contract import bundle_digest
    digest = bundle_digest(store.root)
    before = store.counts()
    with patch("_storage.bundle_digest", side_effect=[digest, digest, "f" * 64]):
        try:
            store.ingest([("protocol/changed-bundle.toml", raw)])
        except StorageError as exc:
            require(exc.code == "bundle-changed")
        else:
            raise AssertionError("writer committed after a trusted-bundle change")
    require(store.counts() == before and store.audit()["status"] == "consistent")
    checks.append("changed-bundle-before-commit-rolls-back")

    class LoseRollbackAcknowledgement(Store):
        def insert(self, table, values):
            if table == "runtime_document":
                raise ValueError("original-pre-commit-property")
            return super().insert(table, values)

        def execute(self, sql, parameters=()):
            result = super().execute(sql, parameters)
            if sql == "ROLLBACK":
                raise OSError("lost rollback acknowledgement")
            return result

    fault = LoseRollbackAcknowledgement(store.engine, store.connection, store.root)
    try:
        fault.ingest([("protocol/rollback-unknown.toml", raw)])
    except StorageError as exc:
        require(exc.code == "rollback-unconfirmed" and "original-pre-commit-property" in str(exc))
    else:
        raise AssertionError("rollback acknowledgement loss was reported as success")
    require(store.counts() == before and store.audit()["status"] == "consistent")
    checks.append("rollback-acknowledgement-loss-preserves-pre-commit-error")
    if len(checks) != len(CHECKS) or set(checks) != CHECKS:
        raise AssertionError("protocol check population changed without review")
    return checks
