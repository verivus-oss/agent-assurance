"""Dedicated-connection, atomic writers for the non-normative reference mirrors."""

from contextlib import contextmanager
from datetime import date
from pathlib import Path
import sqlite3
import threading
import time
import uuid

from _contract import bundle_digest, expected_counts, REGISTRY_TABLES
from _projection import (INSTANCE_COLUMNS, PROJECTION_COLUMNS, PROVENANCE_COLUMNS,
                         project, semantic_json, timestamp_index)
from _vocabulary import load_catalog

_DUCKDB_WRITER = threading.RLock()
DOCUMENT_COLUMNS = ("template_kind", "source_toml", "projection_version", "contract_bundle_sha256", *PROJECTION_COLUMNS)


class StorageError(RuntimeError):
    """A stable outcome code and a diagnostic safe to display as JSON."""

    def __init__(self, code: str, detail: str):
        self.code = code
        super().__init__(f"{code}: {detail}")


def connect(engine: str, destination: str):
    if engine == "sqlite":
        return sqlite3.connect(destination, isolation_level=None, timeout=0.25)
    if engine == "duckdb":
        import duckdb
        try:
            return duckdb.connect(destination)
        except duckdb.IOException as exc:
            code = "busy/unsupported-writer" if "lock" in str(exc).lower() else "setup"
            raise StorageError(code, str(exc)) from exc
    if engine == "postgres":
        import psycopg
        return psycopg.connect(destination, autocommit=True)
    raise ValueError(f"unsupported database engine: {engine!r}")


class Store:
    """The caller grants dedicated use of an idle connection for each operation.

    A reconnect callback must return a fresh dedicated connection to the same
    destination. It enables commit-outcome reconciliation. Without it, a lost
    acknowledgement is explicitly indeterminate. DuckDB has one writer process;
    this module serializes its callers within that process.
    """

    def __init__(self, engine: str, connection, repo_root: Path, *, reconnect=None):
        if engine not in {"sqlite", "duckdb", "postgres"}:
            raise ValueError("unsupported engine")
        self.engine = engine
        self.connection = connection
        self.root = repo_root.resolve()
        self.reconnect = reconnect
        self._lock = _DUCKDB_WRITER if engine == "duckdb" else threading.RLock()

    def table(self, name: str) -> str:
        return ("dagtoml_" if self.engine == "sqlite" else "dagtoml.") + name

    def execute(self, sql: str, parameters=()):
        # SQL identifiers originate in this module or the validated mapping.
        # Every document-authored value uses driver parameters.
        return self.connection.execute(sql.replace("?", "%s") if self.engine == "postgres" else sql, parameters)

    def rows(self, table: str, columns: tuple, where: str = "", parameters=()) -> list[dict]:
        expressions = [f"CAST({column} AS TEXT) AS {column}" if column in {"meta_extras", "extras"}
                       else column for column in columns]
        cursor = self.execute(f"SELECT {','.join(expressions)} FROM {self.table(table)} {where}", parameters)  # nosec B608 # noqa: S608
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    def insert(self, table: str, values: dict) -> None:
        self.execute(f"INSERT INTO {self.table(table)} ({','.join(values)}) VALUES ({','.join('?' for _ in values)})",  # nosec B608 # noqa: S608
                     tuple(values.values()))

    def prepare(self) -> None:
        """Never end an existing caller transaction, including an aborted one."""
        if self.engine == "sqlite":
            if self.connection.in_transaction:
                raise StorageError("active-caller-transaction", "supply a dedicated idle connection")
            self.execute("PRAGMA foreign_keys = ON")
            if self.execute("PRAGMA foreign_keys").fetchone() != (1,):
                raise StorageError("setup", "SQLite foreign keys are not enabled")
            if self.execute("PRAGMA ignore_check_constraints").fetchone() != (0,):
                raise StorageError("setup", "SQLite CHECK constraints must be enabled")
        elif self.engine == "postgres":
            from psycopg.pq import TransactionStatus
            if self.connection.info.transaction_status != TransactionStatus.IDLE:
                raise StorageError("active-caller-transaction", "supply a dedicated idle connection")
            self.connection.autocommit = True
            for encoding in ("server_encoding", "client_encoding"):
                if self.execute(f"SHOW {encoding}").fetchone()[0] != "UTF8":
                    raise StorageError("setup", "PostgreSQL server and client encoding must both be UTF8")
        else:
            try:
                first = self.execute("SELECT txid_current()").fetchone()[0]
                second = self.execute("SELECT txid_current()").fetchone()[0]
            except Exception as exc:
                code = "active-caller-transaction" if type(exc).__name__ == "TransactionException" else "setup"
                raise StorageError(code, "connection is not a usable idle DuckDB connection") from exc
            if first == second:
                raise StorageError("active-caller-transaction", "supply a dedicated idle connection")

    @contextmanager
    def transaction(self):
        self.execute("BEGIN")
        try:
            yield
        except BaseException as original:
            try:
                self.execute("ROLLBACK")
            except Exception as rollback:
                raise StorageError("rollback-unconfirmed", f"pre-commit failure {original}; rollback acknowledgement failed: {rollback}") from original
            raise
        else:
            try:
                self.execute("COMMIT")
            except Exception as exc:
                # COMMIT may have reached the server. A rollback claim would
                # be false until a fresh connection establishes the outcome.
                raise StorageError("commit-outcome-unknown", str(exc)) from exc

    def contract(self) -> list[dict]:
        return self.rows("reference_contract", ("singleton_id", "contract_bundle_sha256", "projection_version"))

    def verify_identity(self, digest: str) -> None:
        if self.contract() != [{"singleton_id": 1, "contract_bundle_sha256": digest, "projection_version": 1}]:
            raise StorageError("contract-mismatch", "destination is uninitialized or belongs to another bundle")

    def counts(self) -> dict[str, int]:
        return {name: self.execute(f"SELECT count(*) FROM {self.table(name)}").fetchone()[0]  # nosec B608 # noqa: S608
                for name in (*REGISTRY_TABLES, "instance_file", "reference_contract", "runtime_document")}

    def verify_catalog(self) -> dict[str, int]:
        counts = self.counts()
        for name, expected in expected_counts(self.root).items():
            if counts[name] != expected:
                raise StorageError("catalog-mismatch", f"{name}: expected {expected}, observed {counts[name]}")
        expected_pairs = {(name, token) for name, item in load_catalog(self.root).items() for token in item.values}
        observed = self.execute(f"SELECT attribute, value FROM {self.table('attribute_value_allowed')}").fetchall()  # nosec B608 # noqa: S608
        if len(observed) != len(expected_pairs) or set(observed) != expected_pairs:
            raise StorageError("catalog-mismatch", "executed allowed-value pairs differ from the ontology declarations")
        metadata = self.rows("attribute_vocabulary", ("attribute", "extensible", "ijb_constraint_type", "default_value"))
        catalog = load_catalog(self.root)
        if {row["attribute"] for row in metadata} != set(catalog):
            raise StorageError("catalog-mismatch", "executed vocabulary names differ from the ontology")
        for row in metadata:
            item = catalog[row["attribute"]]
            if (row["extensible"] != item.extensible or row["ijb_constraint_type"] != item.declaration["ijb_constraint_type"]
                    or row["default_value"] != item.declaration.get("default")):
                raise StorageError("catalog-mismatch", f"vocabulary metadata differs: {item.attribute}")
        return counts

    def _empty(self) -> None:
        counts = self.counts()
        if counts["instance_file"] or counts["runtime_document"]:
            raise StorageError("populated-destination", "initialize an empty unpublished destination before replay")

    def _fresh(self) -> None:
        if self.reconnect is None:
            raise StorageError("commit-outcome-unknown", "reconnection is unavailable; inspect the destination before retrying")
        try:
            self.connection.close()
        except Exception:  # nosec B110 # noqa: S110
            pass
        self.connection = self.reconnect()
        self.prepare()

    def initialize(self, *, exclusive_unpublished: bool = False) -> dict:
        if exclusive_unpublished is not True:
            raise StorageError("ownership-required", "initialization requires exclusive ownership of an unpublished destination")
        from _sql_probes import probe_constraints
        digest = bundle_digest(self.root)
        with self._lock:
            self.prepare()
            for attempt in range(3):
                try:
                    self.verify_catalog()
                    self._empty()
                    if self.contract():
                        self.verify_identity(digest)
                        if bundle_digest(self.root) != digest:
                            raise StorageError("bundle-changed", "trusted inputs changed during initialization")
                        return {"status": "already-initialized", "contract_bundle_sha256": digest}
                    probes = probe_constraints(self, digest)
                    self._empty()
                    if self.contract():
                        self.verify_identity(digest)
                        return {"status": "already-initialized", "contract_bundle_sha256": digest}
                    with self.transaction():
                        self._empty()
                        if bundle_digest(self.root) != digest:
                            raise StorageError("bundle-changed", "trusted inputs changed during initialization")
                        self.insert("reference_contract", {"singleton_id": 1, "contract_bundle_sha256": digest,
                                                           "projection_version": 1})
                    return {"status": "initialized", "contract_bundle_sha256": digest, "probes": probes}
                except Exception as exc:
                    unknown = isinstance(exc, StorageError) and exc.code == "commit-outcome-unknown"
                    if unknown:
                        try:
                            self._fresh()
                            self.verify_catalog()
                            self._empty()
                            self.verify_identity(digest)
                            return {"status": "already-initialized", "contract_bundle_sha256": digest,
                                    "reconciled_commit": True}
                        except Exception as reconcile:
                            raise StorageError("commit-outcome-unknown", "initialization could not be reconciled") from reconcile
                    if not self._retryable(exc):
                        raise
                    if attempt == 2:
                        raise StorageError("retryable-busy", "initialization retry limit reached") from exc
                    if self.reconnect:
                        self._fresh()
                    time.sleep(0.05 * (attempt + 1))
        raise AssertionError("unreachable initialization retry state")

    def _retryable(self, exc: Exception) -> bool:
        if self.engine == "postgres":
            return getattr(exc, "sqlstate", None) in {"23505", "40001", "40P01"}
        if self.engine == "sqlite":
            code = getattr(exc, "sqlite_errorcode", 0)
            return code & 255 in {sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED} or code in {
                sqlite3.SQLITE_CONSTRAINT_UNIQUE, sqlite3.SQLITE_CONSTRAINT_PRIMARYKEY}
        return type(exc).__name__ == "TransactionException"

    @staticmethod
    def _equivalent(actual: dict, expected: dict) -> bool:
        for column, wanted in expected.items():
            value = actual[column]
            if column in {"extras", "meta_extras"}:
                if semantic_json(value) != semantic_json(wanted):
                    return False
            elif column in {"created_at", "captured_at"}:
                if (timestamp_index(value) if value is not None else None) != wanted:
                    return False
            elif column == "created":
                if (value.isoformat() if type(value) is date else value) != wanted:
                    return False
            elif value != wanted:
                return False
        return True

    def existing(self, projected, digest: str) -> str | None:
        identity = projected.instance
        parents = self.rows("instance_file", ("id", *INSTANCE_COLUMNS),
                            "WHERE source_path = ? AND content_sha256 = ?",
                            (identity["source_path"], identity["content_sha256"]))
        if not parents:
            return None
        parent = parents[0]
        identifier = parent["id"]
        documents = self.rows("runtime_document", DOCUMENT_COLUMNS, "WHERE instance_file_id = ?", (identifier,))
        expected_document = {"template_kind": identity["template_kind"], "source_toml": projected.source,
                             "projection_version": 1, "contract_bundle_sha256": digest, **projected.fields}
        provenance = self.rows("provenance", PROVENANCE_COLUMNS, "WHERE instance_file_id = ?", (identifier,))
        matches = (len(parents) == 1 and self._equivalent(parent, identity)
                   and len(documents) == 1 and self._equivalent(documents[0], expected_document)
                   and ((projected.provenance is None and not provenance)
                        or (projected.provenance is not None and len(provenance) == 1
                            and self._equivalent(provenance[0], projected.provenance))))
        if not matches:
            raise StorageError("stored-document-conflict", f"metadata, provenance, bytes, or projection mismatch for {identity['source_path']!r}")
        return str(identifier)

    def ingest(self, documents: list[tuple[str, bytes]]) -> dict:
        if not documents:
            raise ValueError("an ingestion batch must contain at least one document")
        digest = bundle_digest(self.root)
        projected = [project(source, path, self.root) for path, source in documents]
        if bundle_digest(self.root) != digest:
            raise StorageError("bundle-changed", "trusted validation inputs changed during projection")
        with self._lock:
            self.prepare()
            for attempt in range(3):
                identifiers = []
                new_identities = set()
                try:
                    with self.transaction():
                        self.verify_identity(digest)
                        for item in projected:
                            identifier = self.existing(item, digest)
                            if identifier is None:
                                new_identities.add((item.instance["source_path"], item.instance["content_sha256"]))
                                identifier = uuid.uuid4().hex if self.engine == "sqlite" else str(uuid.uuid4())
                                self.insert("instance_file", {"id": identifier, **item.instance})
                                if item.provenance is not None:
                                    self.insert("provenance", {"instance_file_id": identifier, **item.provenance})
                                self.insert("runtime_document", {"instance_file_id": identifier,
                                            "template_kind": item.instance["template_kind"], "source_toml": item.source,
                                            "projection_version": 1, "contract_bundle_sha256": digest, **item.fields})
                            identifiers.append(identifier)
                        if bundle_digest(self.root) != digest:
                            raise StorageError("bundle-changed", "trusted inputs changed before ingestion commit")
                    return self._receipt(projected, identifiers, digest, reconciled=False)
                except Exception as exc:
                    if isinstance(exc, StorageError) and exc.code == "commit-outcome-unknown":
                        try:
                            self._fresh()
                            with self.transaction():
                                self.verify_identity(digest)
                                identifiers = [self.existing(item, digest) for item in projected]
                            if all(identifiers):
                                return self._receipt(projected, identifiers, digest, reconciled=True)
                            new_presence = {identifier is not None for item, identifier in zip(projected, identifiers, strict=True)
                                            if (item.instance["source_path"], item.instance["content_sha256"]) in new_identities}
                            old_missing = any(identifier is None for item, identifier in zip(projected, identifiers, strict=True)
                                              if (item.instance["source_path"], item.instance["content_sha256"]) not in new_identities)
                            if new_presence == {False} and not old_missing and attempt < 2:
                                continue
                        except Exception as reconcile:
                            raise StorageError("commit-outcome-unknown", "whole-batch reconciliation was unavailable or found a conflict") from reconcile
                        raise StorageError("commit-outcome-unknown", "whole batch is not present after acknowledgement loss") from exc
                    if not self._retryable(exc):
                        raise
                    if attempt == 2:
                        raise StorageError("retryable-busy", "ingestion retry limit reached") from exc
                    if self.reconnect:
                        self._fresh()
                    time.sleep(0.05 * (attempt + 1))
        raise AssertionError("unreachable ingestion retry state")

    @staticmethod
    def _receipt(projected, identifiers, digest, *, reconciled):
        return {"status": "committed", "contract_bundle_sha256": digest, "reconciled_commit": reconciled,
                "documents": [{"id": identifier, "source_path": item.instance["source_path"],
                               "content_sha256": item.instance["content_sha256"],
                               "unindexed_fields": [list(path) for path in item.unindexed_fields]}
                              for item, identifier in zip(projected, identifiers, strict=True)]}

    def audit(self) -> dict:
        digest = bundle_digest(self.root)
        failures = []
        checked = 0
        with self._lock:
            self.prepare()
            with self.transaction():
                self.verify_identity(digest)
                parents = self.rows("instance_file", ("id", "source_path", "template_kind"))
                for parent in parents:
                    if parent["template_kind"] not in {"adapter-contract", "adapter-registry-binding", "gate-decision"}:
                        continue
                    checked += 1
                    documents = self.rows("runtime_document", ("source_toml",), "WHERE instance_file_id = ?", (parent["id"],))
                    try:
                        if len(documents) != 1:
                            raise StorageError("metadata-only", "affected instance has no complete runtime_document")
                        item = project(bytes(documents[0]["source_toml"]), parent["source_path"], self.root)
                        if self.existing(item, digest) != str(parent["id"]):
                            raise StorageError("stored-document-conflict", "source hash or identity differs")
                    except (ValueError, StorageError) as exc:
                        failures.append({"id": str(parent["id"]), "source_path": parent["source_path"], "error": str(exc)})
        if bundle_digest(self.root) != digest:
            raise StorageError("bundle-changed", "trusted validation inputs changed during audit")
        return {"status": "failed" if failures else "consistent", "checked_documents": checked,
                "failures": failures, "contract_bundle_sha256": digest,
                "excluded": ["runtime execution", "signature verification", "evidence authenticity", "other template kinds"]}
