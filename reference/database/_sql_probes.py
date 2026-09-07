"""Executed SQL witnesses. Setup failures never count as constraint rejections."""

import sqlite3
import uuid

from _contract import load_mapping
from _projection import PROJECTION_COLUMNS
from _vocabulary import load_catalog

PROVENANCE_DIGEST_CASES = (
    ("sha256:" + "a" * 64, True), ("sha256:" + "A" * 64, False),
    ("sha256:" + "g" * 64, False), ("sha256:" + "a" * 63, False),
    ("sha256:" + "a" * 65, False), ("sha256:" + "a" * 64 + "\n", False),
    ("sha256:" + "a" * 64 + "\0tail", False), ("a" * 64, False), (None, False),
    *(("sha256:" + "a" * offset + "\0" + "Z" * (63 - offset), False) for offset in (0, 31, 63)),
)

CONTRACT_NUL_CASES = ("a" * 64 + "\0tail", *("a" * offset + "\0" + "Z" * (63 - offset) for offset in (0, 31, 63)))


def constraint_failure(engine: str, exc: Exception, family: str, column: str = "") -> bool:
    message = str(exc).lower()
    if engine == "postgres":
        if family == "encoding" and type(exc).__name__ == "DataError" and "cannot contain NUL" in str(exc):
            # PostgreSQL text cannot represent NUL. psycopg refuses it at the
            # binding boundary; retain that layer explicitly in the receipt.
            return True
        codes = {"value": {"22P02", "23514"}, "shape": {"23514", "23502"},
                 "encoding": {"23514", "23502", "22021"},
                 "foreign-key": {"23503"}, "unique": {"23505"}}
        return getattr(exc, "sqlstate", None) in codes[family]
    if engine == "sqlite":
        codes = {"value": {sqlite3.SQLITE_CONSTRAINT_CHECK},
                 "encoding": {sqlite3.SQLITE_CONSTRAINT_CHECK, sqlite3.SQLITE_CONSTRAINT_NOTNULL},
                 "shape": {sqlite3.SQLITE_CONSTRAINT_CHECK, sqlite3.SQLITE_CONSTRAINT_NOTNULL},
                 "foreign-key": {sqlite3.SQLITE_CONSTRAINT_FOREIGNKEY},
                 "unique": {sqlite3.SQLITE_CONSTRAINT_PRIMARYKEY, sqlite3.SQLITE_CONSTRAINT_UNIQUE}}
        return (getattr(exc, "sqlite_errorcode", None) in codes[family]
                and (family != "value" or column.lower() in message))
    if family == "value":
        return type(exc).__name__ in {"ConversionException", "ConstraintException"} and (
            "enum" in message or "uint8" in message or column.lower() in message)
    markers = {"shape": ("check constraint", "not null"), "encoding": ("check constraint", "not null"), "foreign-key": ("foreign key",),
               "unique": ("primary key", "unique constraint", "duplicate key")}
    return type(exc).__name__ == "ConstraintException" and any(marker in message for marker in markers[family])


def document_fixture(kind: str, identifier: str, digest: str) -> dict:
    fields = dict.fromkeys(PROJECTION_COLUMNS)
    if kind == "adapter-contract":
        fields.update(runtime_kind="wasi-component", runtime_network_policy="denied", runtime_clock_policy="injected")
    elif kind == "adapter-registry-binding":
        fields["adapter_ref_syntax"] = "content-hash"
    elif kind == "gate-decision":
        fields["gate_decision_verdict"] = "pass"
    else:
        raise ValueError("unsupported SQL probe kind")
    return {"instance_file_id": identifier, "template_kind": kind, "source_toml": b"probe-only",
            "projection_version": 1, "contract_bundle_sha256": digest, **fields}


def expected_probes(root, digest):
    """Exact planned labels and outcomes, including mandatory controls."""
    catalog = load_catalog(root)
    expected = {}
    for row in load_mapping(root):
        if row["representation"] not in {"document-column", "entity-column"}:
            continue
        tokens = catalog[row["attribute"]].values
        values = [(value, True) for value in tokens]
        values += [(value, False) for value in sorted({"__undeclared_issue_74__", "", tokens[0].upper(), tokens[0] + " ", " " + tokens[0]})]
        values.append((None, not row.get("required", False)))
        for value, accepted in values:
            for operation in ("insert", "update"):
                expected[f"{row['attribute']}/{operation}/{value!r}"] = "accept" if accepted else "reject"
    for kind in ("adapter-contract", "adapter-registry-binding", "gate-decision"):
        for name in ("incompatible-column", "wrong-parent-kind", "dangling-parent", "duplicate-projection", "restrict-parent-delete"):
            expected[f"{kind}/{name}"] = "reject"
    for column, value in (("projection_version", 2), ("source_toml", None),
                          ("template_kind", "assertion-bundle"), ("contract_bundle_sha256", "f" * 64)):
        expected[f"document/{column}/{value!r}"] = "reject"
    for column, value in (("singleton_id", 2), ("projection_version", 2),
                          ("contract_bundle_sha256", "A" * 64), ("contract_bundle_sha256", "a" * 64 + "\n"),
                          ("contract_bundle_sha256", "a" * 63), ("contract_bundle_sha256", "g" * 64)):
        expected[f"contract/{column}/{value!r}"] = "reject"
    for value in CONTRACT_NUL_CASES:
        expected[f"contract/contract_bundle_sha256/{value!r}"] = "reject"
    for value, accepted in PROVENANCE_DIGEST_CASES:
        for operation in ("insert", "update"):
            expected[f"provenance/source_sha256/{operation}/{value!r}"] = "accept" if accepted else "reject"
    return expected


def probe_constraints(store, digest: str) -> list[dict]:
    catalog = load_catalog(store.root)
    mapping = load_mapping(store.root)
    observations = []

    def run(label, kind, setup, target, accepted, family="shape", column="", readback=None):
        store.execute("BEGIN")
        try:
            identifier = uuid.uuid4().hex if store.engine == "sqlite" else str(uuid.uuid4())
            # These writes are setup, outside the target rejection catch.
            store.insert("reference_contract", {"singleton_id": 1, "contract_bundle_sha256": digest,
                                                "projection_version": 1})
            store.insert("instance_file", {"id": identifier, "source_path": "sql-probe.toml",
                         "content_sha256": "sha256:" + "0" * 64, "schema_version": "0.1.0",
                         "template_kind": kind, "framework_profile": "agent-assurance"})
            fixture = document_fixture(kind, identifier, digest)
            setup(identifier, fixture)
            try:
                target(identifier, fixture)
            except Exception as exc:
                if accepted or not constraint_failure(store.engine, exc, family, column):
                    raise AssertionError(f"{label}: target failed outside the expected {family} constraint: {exc}") from exc
                observations.append({"probe": label, "expected": "reject", "actual": "reject",
                                     "exception": type(exc).__name__, "diagnostic": str(exc),
                                     "rejection_layer": "driver-encoding" if store.engine == "postgres" and family == "encoding" and getattr(exc, "sqlstate", None) is None else "database"})
            else:
                if not accepted:
                    raise AssertionError(f"{label}: forbidden target write succeeded")
                if readback is not None:
                    readback(identifier)
                observations.append({"probe": label, "expected": "accept", "actual": "accept"})
        finally:
            store.execute("ROLLBACK")

    def noop(*_):
        return None
    for row in mapping:
        if row["representation"] not in {"document-column", "entity-column"}:
            continue
        attribute = row["attribute"]
        table, column = row["enforcement_sites"][0]
        kind = row.get("template_kind", "adapter-contract")
        tokens = catalog[attribute].values
        if not tokens:
            raise AssertionError("a constrained column needs nonempty positive controls")
        invalid = {"__undeclared_issue_74__", "", tokens[0].upper(), tokens[0] + " ", " " + tokens[0]}
        if any(value in tokens for value in invalid):
            raise AssertionError("negative witness must be absent from the declared vocabulary")
        values = [(value, True) for value in tokens] + [(value, False) for value in sorted(invalid)]
        if table == "runtime_document":
            values.append((None, not row["required"]))
        else:
            values.append((None, True))

        def entity(identifier):
            return {"id": identifier, "qualified_id": "REQ:sql-probe", "prefix": "REQ",
                    "entity_kind": "requirement", "declared_in": identifier}

        for value, accepted in values:
            for operation in ("insert", "update"):
                def setup(identifier, fixture):
                    if operation == "update":
                        baseline = fixture if table == "runtime_document" else entity(identifier)
                        store.insert(table, {**baseline, column: tokens[0]})

                def target(identifier, fixture):
                    if operation == "insert":
                        baseline = fixture if table == "runtime_document" else entity(identifier)
                        store.insert(table, {**baseline, column: value})
                    else:
                        key = "instance_file_id" if table == "runtime_document" else "id"
                        store.execute(f"UPDATE {store.table(table)} SET {column} = ? WHERE {key} = ?", (value, identifier))  # nosec B608 # noqa: S608

                def readback(identifier):
                    key = "instance_file_id" if table == "runtime_document" else "id"
                    actual = store.execute(f"SELECT {column} FROM {store.table(table)} WHERE {key} = ?", (identifier,)).fetchall()  # nosec B608 # noqa: S608
                    if actual != [(value,)]:
                        raise AssertionError(f"{attribute}: round-trip mismatch: {actual!r}")

                run(f"{attribute}/{operation}/{value!r}", kind, setup, target, accepted,
                    "shape" if value is None else "value", column, readback)

    # Independent witnesses for the disjoint row shape and parent identity.
    for kind in ("adapter-contract", "adapter-registry-binding", "gate-decision"):
        other_column = "adapter_ref_syntax" if kind == "adapter-contract" else "runtime_kind"
        other_value = "content-hash" if kind == "adapter-contract" else "wasi-component"
        run(f"{kind}/incompatible-column", kind, noop,
            lambda identifier, fixture: store.insert("runtime_document", {**fixture, other_column: other_value}), False)
        other_kind = "gate-decision" if kind != "gate-decision" else "adapter-contract"
        run(f"{kind}/wrong-parent-kind", kind, noop,
            lambda identifier, fixture: store.insert("runtime_document", document_fixture(other_kind, identifier, digest)),
            False, "foreign-key")
        run(f"{kind}/dangling-parent", kind, noop,
            lambda identifier, fixture: store.insert("runtime_document", {**fixture, "instance_file_id": str(uuid.uuid4())}),
            False, "foreign-key")
        run(f"{kind}/duplicate-projection", kind,
            lambda identifier, fixture: store.insert("runtime_document", fixture),
            lambda identifier, fixture: store.insert("runtime_document", fixture), False, "unique")
        run(f"{kind}/restrict-parent-delete", kind,
            lambda identifier, fixture: store.insert("runtime_document", fixture),
            lambda identifier, fixture: store.execute(f"DELETE FROM {store.table('instance_file')} WHERE id = ?", (identifier,)),  # nosec B608 # noqa: S608
            False, "foreign-key")
    for column, value, family in (("projection_version", 2, "shape"), ("source_toml", None, "shape"),
                                  ("template_kind", "assertion-bundle", "shape"),
                                  ("contract_bundle_sha256", "f" * 64, "foreign-key")):
        setup = (lambda identifier, fixture: store.execute(
            f"UPDATE {store.table('instance_file')} SET template_kind = ? WHERE id = ?", (value, identifier))) if column == "template_kind" else noop  # nosec B608 # noqa: S608
        run(f"document/{column}/{value!r}", "gate-decision", setup,
            lambda identifier, fixture: store.insert("runtime_document", {**fixture, column: value}), False, family)
    for column, value in (("singleton_id", 2), ("projection_version", 2),
                          ("contract_bundle_sha256", "A" * 64), ("contract_bundle_sha256", "a" * 64 + "\n"),
                          ("contract_bundle_sha256", "a" * 63), ("contract_bundle_sha256", "g" * 64)):
        run(f"contract/{column}/{value!r}", "gate-decision", noop,
            lambda identifier, fixture: store.execute(f"UPDATE {store.table('reference_contract')} SET {column} = ?", (value,)), False)  # nosec B608 # noqa: S608
    for nul_digest in CONTRACT_NUL_CASES:
        run(f"contract/contract_bundle_sha256/{nul_digest!r}", "gate-decision", noop,
            lambda identifier, fixture: store.execute(f"UPDATE {store.table('reference_contract')} SET contract_bundle_sha256 = ?", (nul_digest,)), False, "encoding")  # nosec B608 # noqa: S608
    for value, accepted in PROVENANCE_DIGEST_CASES:
        for operation in ("insert", "update"):
            def setup(identifier, fixture):
                if operation == "update":
                    store.insert("provenance", {"instance_file_id": identifier, "source_path": "upstream.txt",
                                               "source_sha256": "sha256:" + "a" * 64, "source_bytes": 0})

            def target(identifier, fixture):
                if operation == "insert":
                    store.insert("provenance", {"instance_file_id": identifier, "source_path": "upstream.txt",
                                               "source_sha256": value, "source_bytes": 0})
                else:
                    store.execute(f"UPDATE {store.table('provenance')} SET source_sha256 = ? WHERE instance_file_id = ?", (value, identifier))  # nosec B608 # noqa: S608

            def readback(identifier):
                if store.rows("provenance", ("source_sha256",), "WHERE instance_file_id = ?", (identifier,)) != [{"source_sha256": value}]:
                    raise AssertionError("provenance digest did not round-trip")

            run(f"provenance/source_sha256/{operation}/{value!r}", "adapter-contract", setup, target, accepted, "encoding", "source_sha256", readback)
    expected = expected_probes(store.root, digest)
    actual = {item["probe"]: item["actual"] for item in observations}
    if len(observations) != len(expected) or actual != expected:
        raise AssertionError("SQL probe population is incomplete")
    if store.counts()["instance_file"] or store.counts()["runtime_document"]:
        raise AssertionError("constraint probes leaked rows outside rolled-back transactions")
    # A competing initializer may publish after our last rollback. The caller
    # reconciles that committed singleton before any further write.
    return observations
