"""Real-engine side-by-side replay checks with independently hashed originals."""


import hashlib

from replay_runtime_documents import replay
from _storage import StorageError
from _instrument import require

CHECKS = frozenset({"replay-requires-private-ownership", "replay-missing-changed-invalid-sources-no-writes",
                   "replay-valid-occurrences-and-audit", "replay-refuses-populated-destination",
                   "opaque-authority-operands-retained"})


def exercise_replay(store, work):
    work.mkdir(parents=True, exist_ok=True)
    kinds = ("adapter-contract", "adapter-registry-binding", "gate-decision")
    entries = []
    for kind in kinds:
        raw = (store.root / f"examples/minimal-{kind}.toml").read_bytes()
        (work / (kind + ".toml")).write_bytes(raw)
        entries.append({"source_path": "legacy/" + kind + ".toml", "source_file": kind + ".toml",
                        "content_sha256": "sha256:" + hashlib.sha256(raw).hexdigest()})
    checks = []
    try:
        replay(store, entries, manifest_directory=work)
    except StorageError as exc:
        require(exc.code == "ownership-required")
    else:
        raise AssertionError("replay accepted a destination without private ownership")
    checks.append("replay-requires-private-ownership")
    before = store.counts()
    invalid = b'[meta]\ntemplate_kind = "adapter-contract"\n'
    (work / "invalid.toml").write_bytes(invalid)
    for broken in ({**entries[0], "source_file": "missing.toml"},
                   {**entries[0], "content_sha256": "sha256:" + "0" * 64},
                   {**entries[0], "source_file": "invalid.toml", "content_sha256": "sha256:" + hashlib.sha256(invalid).hexdigest()}):
        report = replay(store, [entries[1], broken], manifest_directory=work, exclusive_unpublished=True)
        require(report["status"] == "failed" and report["committed_documents"] == 0)
        require([entry["status"] for entry in report["entries"]] == ["validated-pending-batch", "failed"])
        require(store.counts() == before)
    unsupported = b'[meta]\ntemplate_kind="assertion-bundle"\n'
    (work / "unsupported.toml").write_bytes(unsupported)
    entry = {**entries[0], "source_file": "unsupported.toml", "content_sha256": "sha256:" + hashlib.sha256(unsupported).hexdigest()}
    report = replay(store, [entry], manifest_directory=work, exclusive_unpublished=True)
    require(report["status"] == "failed" and report["entries"][0]["code"] == "unsupported-projection")
    require(store.counts() == before)
    checks.append("replay-missing-changed-invalid-sources-no-writes")
    report = replay(store, entries, manifest_directory=work, exclusive_unpublished=True)
    require(report["status"] == "committed" and report["committed_documents"] == len(kinds))
    require(len({entry["id"] for entry in report["entries"]}) == len(kinds))
    require(store.audit()["status"] == "consistent")
    checks.append("replay-valid-occurrences-and-audit")
    try:
        replay(store, entries, manifest_directory=work, exclusive_unpublished=True)
    except StorageError as exc:
        require(exc.code == "populated-destination")
    else:
        raise AssertionError("replay appended to an already populated destination")
    checks.append("replay-refuses-populated-destination")
    # SPEC preserves the opaque rule. It neither assigns severity/operator
    # fields nor evaluates a runtime-owned expression in this string.
    expression = b'authority_rule = "constraint(A-inert, rule=private_op(severity=private_tier))"\n'
    raw = (work / "gate-decision.toml").read_bytes() + b"\n[extension]\n" + expression
    result = store.ingest([("opaque/authority.toml", raw)])
    saved = store.rows("runtime_document", ("source_toml",), "WHERE instance_file_id = ?",
                       (result["documents"][0]["id"],))
    require(bytes(saved[0]["source_toml"]) == raw and expression in bytes(saved[0]["source_toml"]))
    require(store.audit()["status"] == "consistent")
    checks.append("opaque-authority-operands-retained")
    require(set(checks) == CHECKS and len(checks) == len(CHECKS))
    return checks
