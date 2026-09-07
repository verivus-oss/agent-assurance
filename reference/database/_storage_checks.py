"""Acceptance checks against a real initialized database, with fixed oracles."""


import hashlib
import json

from _projection import project, semantic_json, timestamp_index
from _storage import Store, StorageError
from _instrument import require

CHECKS = frozenset({
    "optional-derivation-stores-null", "two-valid-captured-versions-stored-consistently",
    "three-kinds-and-idempotent-repeat", "exact-original-bytes-and-prefixed-hash", "profile-alias-preserved",
    "changed-content-and-distinct-source-occurrences", "invalid-batch-and-mandatory-identity-leave-state-unchanged",
    "failure-between-parent-and-document-rolls-back", "active-caller-transaction-preserved",
    "initialization-ownership-and-population-refusal", "optional-metadata-portability-and-omission-report",
    "native-and-quoted-date-and-local-timestamp-indexes", "semantic-json-order-unicode-escapes-and-decimal-number-equivalence",
    "audit-and-repeat-reject-array-order", "audit-and-repeat-reject-bool-versus-number", "audit-and-repeat-reject-missing-property",
    "audit-and-repeat-detect-raw-bytes-and-projection-corruption", "audit-detects-source-hash-corruption",
})


def exercise_storage(store: Store) -> list[str]:
    """Use an isolated test destination. This function intentionally writes rows."""
    checks = []
    root = store.root
    kinds = ("adapter-contract", "adapter-registry-binding", "gate-decision")
    sources = {kind: (root / f"examples/minimal-{kind}.toml").read_bytes() for kind in kinds}
    batch = [(f"check/{kind}.toml", sources[kind]) for kind in kinds]
    first = store.ingest(batch)
    require(len(first["documents"]) == 3)
    require(store.ingest(batch) == first)
    checks.append("three-kinds-and-idempotent-repeat")
    for record, (_, raw) in zip(first["documents"], batch, strict=True):
        saved = store.rows("runtime_document", ("source_toml",), "WHERE instance_file_id = ?", (record["id"],))
        require(len(saved) == 1 and bytes(saved[0]["source_toml"]) == raw)
        require(record["content_sha256"] == "sha256:" + hashlib.sha256(raw).hexdigest())
    for kind, record in zip(kinds, first["documents"], strict=True):
        rows = store.rows(kind.replace("-", "_") + "_document", ("instance_file_id", "source_toml", "source_path"),
                          "WHERE instance_file_id = ?", (record["id"],))
        require(len(rows) == 1 and bytes(rows[0]["source_toml"]) == sources[kind]
                and rows[0]["source_path"] == "check/" + kind + ".toml", "convenience view lost its source projection")
    checks.append("exact-original-bytes-and-prefixed-hash")
    for kind in kinds:
        alias = sources[kind].replace(b'framework_profile = "agent-assurance"', b'framework_profile = "AGDF"')
        require(alias != sources[kind])
        result = store.ingest([(f"alias/{kind}.toml", alias)])
        saved = store.rows("instance_file", ("framework_profile",), "WHERE id = ?", (result["documents"][0]["id"],))
        require(saved == [{"framework_profile": "AGDF"}])
    checks.append("profile-alias-preserved")
    changed = store.ingest([(batch[0][0], batch[0][1] + b"\n# another content version\n")])
    require(changed["documents"][0]["id"] != first["documents"][0]["id"])
    relocated = store.ingest([("other/source.toml", batch[0][1])])
    require(relocated["documents"][0]["id"] != first["documents"][0]["id"])
    checks.append("changed-content-and-distinct-source-occurrences")

    import re
    from pathlib import Path
    import uuid
    from unittest.mock import patch
    omitted = re.sub(rb'^id_derivation[^\n]*\n', b'', sources[kinds[0]], count=1, flags=re.M)
    require(omitted != sources[kinds[0]])
    optional_result = store.ingest([("optional/derivation.toml", omitted)])
    require(store.rows("runtime_document", ("adapter_id_derivation",), "WHERE instance_file_id = ?",
                       (optional_result["documents"][0]["id"],)) == [{"adapter_id_derivation": None}])
    require(store.ingest([("optional/derivation.toml", omitted)]) == optional_result and store.audit()["status"] == "consistent")
    checks.append("optional-derivation-stores-null")
    # Capture valid A, replace its path with valid B, and exercise the complete
    # projection/write/repeat/audit path while forbidding a root-source reopen.
    capture = root / ".local/storage-capture" / (uuid.uuid4().hex + ".toml")
    capture.parent.mkdir(parents=True, exist_ok=True)
    a = sources[kinds[0]]
    b = a.replace(b'network_policy = "denied"', b'network_policy = "open"')
    if b == a:
        b = re.sub(rb'(network_policy\s*=\s*)"denied"', rb'\1"open"', a, count=1)
    require(a != b)
    project(a, str(capture), root)
    project(b, str(capture), root)
    capture.write_bytes(a)
    captured = capture.read_bytes()
    capture.write_bytes(b)
    original_read = Path.read_bytes
    def guarded_read(path):
        require(path != capture, "storage reopened the captured root source")
        return original_read(path)
    with patch.object(Path, "read_bytes", guarded_read):
        version_a = store.ingest([(str(capture), captured)])
    version_b = store.ingest([(str(capture), capture.read_bytes())])
    for result, raw, policy in ((version_a, a, "denied"), (version_b, b, "open")):
        item = result["documents"][0]
        require(item["content_sha256"] == "sha256:" + hashlib.sha256(raw).hexdigest())
        row = store.rows("runtime_document", ("source_toml", "runtime_network_policy"), "WHERE instance_file_id = ?", (item["id"],))[0]
        require(bytes(row["source_toml"]) == raw and row["runtime_network_policy"] == policy)
        require(store.ingest([(str(capture), raw)]) == result)
    require(version_a["documents"][0]["id"] != version_b["documents"][0]["id"] and store.audit()["status"] == "consistent")
    checks.append("two-valid-captured-versions-stored-consistently")

    def rejected(action, code=None):
        try:
            action()
        except (StorageError, ValueError) as exc:
            if code is not None:
                require(getattr(exc, "code", None) == code, str(exc))
        else:
            raise AssertionError("expected rejection did not occur")

    before = store.counts()
    rejected(lambda: store.ingest([("batch/valid.toml", sources[kinds[0]]),
                                  ("batch/invalid.toml", sources[kinds[2]].replace(b'verdict                 = "fail"', b'verdict                 = "unknown"'))]))
    require(store.counts() == before)
    rejected(lambda: store.ingest([("unsupported.toml", b'[meta]\ntemplate_kind="assertion-bundle"\n')]), "unsupported-projection")
    rejected(lambda: store.ingest([("nul\0path", sources[kinds[0]])]))
    require(store.counts() == before)
    checks.append("invalid-batch-and-mandatory-identity-leave-state-unchanged")

    class FailDocument(Store):
        def insert(self, table, values):
            if table == "runtime_document":
                raise ValueError("injected failure after parent write")
            return super().insert(table, values)

    rejected(lambda: FailDocument(store.engine, store.connection, root).ingest([("atomic/new.toml", sources[kinds[0]])]))
    require(store.counts() == before)
    checks.append("failure-between-parent-and-document-rolls-back")

    # Ownership is tested using caller work that must survive the rejection.
    store.execute("BEGIN")
    store.execute(f"UPDATE {store.table('instance_file')} SET title = ? WHERE id = ?", ("caller-owned", first["documents"][0]["id"]))  # nosec B608 # noqa: S608
    rejected(lambda: store.ingest([("active/new.toml", sources[kinds[0]])]), "active-caller-transaction")
    require(store.rows("instance_file", ("title",), "WHERE id = ?", (first["documents"][0]["id"],)) == [{"title": "caller-owned"}])
    store.execute("ROLLBACK")
    require(store.counts() == before)
    checks.append("active-caller-transaction-preserved")
    rejected(lambda: store.initialize(exclusive_unpublished=True), "populated-destination")
    rejected(lambda: store.initialize(), "ownership-required")
    checks.append("initialization-ownership-and-population-refusal")

    # Optional metadata has a portable index domain and a lossless source.
    metadata = sources[kinds[0]].replace(b"[adapter]\n", b'''created_at = 2026-09-07T12:00:00+10:00
"nested.key" = { text = "\x63\x61\x66\xc3\xa9", flags = [true, false], number = 1 }
native_date = 2026-09-07
large_integer = 9007199254740992
nonfinite = nan
bad_nested = { text = "\\u0000" }
"bad\\u0000key" = "retained in source"
docs_url = "extension-only"

[adapter]
''').replace(b'title             = "Adapter contract: red-team-review consumer"', b'title = "has\\u0000nul"')
    result = store.ingest([("metadata/indexes.toml", metadata)])
    item = result["documents"][0]
    omitted = {tuple(path) for path in item["unindexed_fields"]}
    require(omitted == {("meta", "title"), ("meta", "native_date"), ("meta", "large_integer"),
                       ("meta", "nonfinite"), ("meta", "bad_nested"), ("meta", "bad\0key")}, omitted)
    saved = store.rows("instance_file", ("title", "created_at", "meta_extras"), "WHERE id = ?", (item["id"],))[0]
    require(saved["title"] is None)
    require("nested.key" in json.loads(saved["meta_extras"]))
    require(json.loads(saved["meta_extras"])["docs_url"] == "extension-only")
    require(store.ingest([("metadata/indexes.toml", metadata)]) == result)
    checks.append("optional-metadata-portability-and-omission-report")
    for value, indexed in ((b'"2026-09-07"', "2026-09-07"), (b'2026-09-07', "2026-09-07"), (b'"invalid-date"', None)):
        raw = sources[kinds[0]].replace(b'"2026-05-21"', value)
        projected = project(raw, "date.toml", root)
        require(projected.instance["created"] == indexed)
    local = metadata.replace(b'2026-09-07T12:00:00+10:00', b'2026-09-07T12:00:00')
    projected = project(local, "local-time.toml", root)
    require(projected.instance["created_at"] is None and ("meta", "created_at") in projected.unindexed_fields)
    timestamps = (
        ("2026-09-07T12:00:00+10:00", "2026-09-07T02:00:00Z"),
        ("2026-09-07T12:00:00-01:59", "2026-09-07T13:59:00Z"),
        ("2026-09-07T12:00:00+23:59", "2026-09-06T12:01:00Z"),
        ("2026-09-07t12:00:00z", "2026-09-07T12:00:00Z"),
        ("2026-09-07T12:00:00+00:60", None),
        ("2026-09-07T12:00:00+00:99", None),
        ("2026-09-07T12:00:00-01:75", None),
        ("2026-09-07T12:00:00+24:00", None),
    )
    for index, (value, expected) in enumerate(timestamps):
        raw = metadata.replace(b"2026-09-07T12:00:00+10:00", json.dumps(value).encode())
        path = f"metadata/offset-{index}.toml"
        projected = project(raw, path, root)
        require(projected.instance["created_at"] == expected, value)
        require((("meta", "created_at") in projected.unindexed_fields) == (expected is None), value)
        written = store.ingest([(path, raw)])
        row = store.rows("instance_file", ("created_at",), "WHERE id = ?", (written["documents"][0]["id"],))[0]
        require((None if row["created_at"] is None else timestamp_index(row["created_at"])) == expected, value)
        require(store.ingest([(path, raw)]) == written)
    checks.append("native-and-quoted-date-and-local-timestamp-indexes")

    original = saved["meta_extras"]
    tree = json.loads(original)
    equivalent = json.dumps(dict(reversed(list(tree.items()))), ensure_ascii=False).replace('"number": 1', '"number": 1.0')
    require(semantic_json(original) == semantic_json(equivalent))
    store.execute(f"UPDATE {store.table('instance_file')} SET meta_extras = ? WHERE id = ?", (equivalent, item["id"]))  # nosec B608 # noqa: S608
    require(store.ingest([("metadata/indexes.toml", metadata)]) == result)
    require(store.audit()["status"] == "consistent")
    checks.append("semantic-json-order-unicode-escapes-and-decimal-number-equivalence")
    for label, altered in (("array-order", {**tree, "nested.key": {**tree["nested.key"], "flags": [False, True]}}),
                           ("bool-versus-number", {**tree, "nested.key": {**tree["nested.key"], "flags": [1, False]}}),
                           ("missing-property", {key: value for key, value in tree.items() if key != "nested.key"})):
        store.execute(f"UPDATE {store.table('instance_file')} SET meta_extras = ? WHERE id = ?", (json.dumps(altered), item["id"]))  # nosec B608 # noqa: S608
        rejected(lambda: store.ingest([("metadata/indexes.toml", metadata)]), "stored-document-conflict")
        audit = store.audit()
        require(audit["status"] == "failed" and any(row["id"] == item["id"] for row in audit["failures"]))
        checks.append("audit-and-repeat-reject-" + label)
    store.execute(f"UPDATE {store.table('instance_file')} SET meta_extras = ? WHERE id = ?", (original, item["id"]))  # nosec B608 # noqa: S608

    identifier = first["documents"][0]["id"]
    for column, value, restore in (("source_toml", b"damaged", sources[kinds[0]]),
                                   ("runtime_network_policy", "open", "denied")):
        store.execute(f"UPDATE {store.table('runtime_document')} SET {column} = ? WHERE instance_file_id = ?", (value, identifier))  # nosec B608 # noqa: S608
        rejected(lambda: store.ingest([batch[0]]), "stored-document-conflict")
        require(store.audit()["status"] == "failed")
        store.execute(f"UPDATE {store.table('runtime_document')} SET {column} = ? WHERE instance_file_id = ?", (restore, identifier))  # nosec B608 # noqa: S608
    checks.append("audit-and-repeat-detect-raw-bytes-and-projection-corruption")
    # DuckDB can reject updates to indexed parent fields while children exist.
    # Model administrator corruption by removing and restoring the projection
    # around that update. The helper itself never performs these mutations.
    from _storage import DOCUMENT_COLUMNS
    document = store.rows("runtime_document", DOCUMENT_COLUMNS, "WHERE instance_file_id = ?", (identifier,))[0]
    store.execute(f"DELETE FROM {store.table('runtime_document')} WHERE instance_file_id = ?", (identifier,))  # nosec B608 # noqa: S608
    require(any("metadata-only" in failure["error"] for failure in store.audit()["failures"]))
    store.execute(f"UPDATE {store.table('instance_file')} SET content_sha256 = ? WHERE id = ?", ("sha256:" + "f" * 64, identifier))  # nosec B608 # noqa: S608
    store.insert("runtime_document", {"instance_file_id": identifier, **document})
    require(store.audit()["status"] == "failed")
    store.execute(f"DELETE FROM {store.table('runtime_document')} WHERE instance_file_id = ?", (identifier,))  # nosec B608 # noqa: S608
    store.execute(f"UPDATE {store.table('instance_file')} SET content_sha256 = ? WHERE id = ?", (first["documents"][0]["content_sha256"], identifier))  # nosec B608 # noqa: S608
    store.insert("runtime_document", {"instance_file_id": identifier, **document})
    checks.append("audit-detects-source-hash-corruption")
    require(store.audit()["status"] == "consistent")
    require(len(checks) == len(CHECKS) and set(checks) == CHECKS, checks)
    return checks
