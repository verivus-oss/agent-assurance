"""Require fresh receipts for every declared engine lane and both seed loaders."""

import hashlib
import json
import re
from pathlib import Path
import sys

from _contract import artifact_hashes, bundle_digest, expected_counts, load_mapping
from _vocabulary import load_catalog
from _sql_probes import expected_probes
from _catalog_checks import CHECKS as METADATA_CHECKS
from _replay_checks import CHECKS as REPLAY_CHECKS
from _storage_checks import CHECKS as STORAGE_CHECKS
from _protocol_checks import CHECKS as PROTOCOL_CHECKS
from _connection_checks import CHECKS as CONNECTION_CHECKS
import _toml11 as toml


def validate_receipts(root: Path, paths: list[Path], *, require_clean=True, include_loaders=True) -> list[dict]:
    sys.path.insert(0, str(root / "validators"))
    from check_database_vocabularies import source_identity
    lock = toml.loads((root / "reference/database/engine-lock.toml").read_text())
    lanes = lock.get("lanes", [])
    expected_lane_names = {f"{engine}-{level}" for engine in ("postgres", "sqlite", "duckdb") for level in ("floor", "maintained")}
    if len(lanes) != len(expected_lane_names) or {lane["id"] for lane in lanes} != expected_lane_names:
        raise ValueError("engine lock must enumerate exactly the six required compatibility lanes")
    by_lane = {lane["id"]: lane for lane in lanes}
    if include_loaders:
        for name in ("rust", "go"):
            by_lane["duckdb-loader-" + name] = {**by_lane["duckdb-maintained"], "loader": name}
    receipts = [json.loads(path.read_text()) for path in paths]
    names = [receipt.get("lane") for receipt in receipts]
    if len(names) != len(set(names)) or set(names) != set(by_lane):
        raise ValueError("missing, duplicate, or unexpected executed lane receipt")
    source = source_identity(root)
    if require_clean and (not source["tracked_tree_clean"] or not source["bundle_files_tracked"]):
        raise ValueError("full executed receipt gate requires a clean tracked tree at a named commit")
    artifacts, digest = artifact_hashes(root), bundle_digest(root)
    registry = expected_counts(root)
    catalog = load_catalog(root)
    expected_pairs = {(name, token) for name, item in catalog.items() for token in item.values}
    load_mapping(root)
    probe_plan = expected_probes(root, digest)
    for receipt in receipts:
        lane = by_lane[receipt["lane"]]
        if (receipt.get("status") != "passed" or receipt.get("receipt_version") != 1
                or receipt.get("skipped") != [] or receipt.get("engine") != lane["engine"]
                or receipt.get("actual_version") != lane["version"] or receipt.get("expected_version") != lane["version"]):
            raise ValueError("failed, skipped, wrong-engine, or wrong-version receipt")
        if receipt.get("source") != source or receipt.get("artifacts") != artifacts or receipt.get("contract_bundle_sha256") != digest:
            raise ValueError("stale receipt: source commit/tree, artifacts, or validation bundle differ")
        counts = receipt.get("seed_counts", {})
        if counts != {**registry, "instance_file": 0, "reference_contract": 0, "runtime_document": 0}:
            raise ValueError("receipt seed counts do not match the declarations and empty seed-only contract")
        pairs = [tuple(pair) for pair in receipt.get("allowed_pairs", [])]
        if len(pairs) != len(expected_pairs) or set(pairs) != expected_pairs:
            raise ValueError("receipt does not demonstrate the exact complete catalog")
        probes = receipt.get("constraint_probes", [])
        if (len(probes) != len(probe_plan) or {item["probe"]: item.get("expected") for item in probes} != probe_plan
                or any(item.get("actual") != item.get("expected") for item in probes)
                or {item.get("actual") for item in probes} != {"accept", "reject"}):
            raise ValueError("receipt probe population is absent, incomplete, duplicated, or failed")
        if len(receipt.get("metadata_checks", [])) != len(METADATA_CHECKS) or set(receipt["metadata_checks"]) != METADATA_CHECKS:
            raise ValueError("metadata rejection controls are missing or duplicated")
        if len(receipt.get("storage_checks", [])) != len(STORAGE_CHECKS) or set(receipt["storage_checks"]) != STORAGE_CHECKS:
            raise ValueError("storage acceptance checks are missing or duplicated")
        if len(receipt.get("protocol_checks", [])) != len(PROTOCOL_CHECKS) or set(receipt["protocol_checks"]) != PROTOCOL_CHECKS:
            raise ValueError("protocol acceptance checks are missing or duplicated")
        if len(receipt.get("initialization_checks", [])) != 7 or len(receipt.get("concurrency_checks", [])) != 2:
            raise ValueError("initialization or writer concurrency checks are missing")
        if set(receipt.get("replay_checks", [])) != REPLAY_CHECKS or len(receipt["replay_checks"]) != len(REPLAY_CHECKS):
            raise ValueError("replay acceptance checks are missing or duplicated")
        if set(receipt.get("connection_checks", [])) != CONNECTION_CHECKS[lane["engine"]] or len(receipt["connection_checks"]) != len(CONNECTION_CHECKS[lane["engine"]]):
            raise ValueError("connection precondition checks are missing or duplicated")
        initialization = {row["check"]: row for row in receipt["initialization_checks"]}
        bundle_changes = {"initialization-bundle-change-" + phase: ("commit-outcome-unknown" if phase == "reconciliation" else "bundle-changed")
                          for phase in ("existing", "after-probes", "before-publish", "reconciliation")}
        if set(initialization) != {"same-bundle-initializers", "different-bundle-initializers", "initialization-commit-acknowledgement-loss"} | bundle_changes.keys():
            raise ValueError("initialization check identities differ")
        for name, allowed in (("same-bundle", {"already-initialized", "retryable-busy"}),
                              ("different-bundle", {"contract-mismatch", "retryable-busy"})):
            row = initialization[name + "-initializers"]
            outcomes = row.get("outcomes", [])
            if row.get("barrier_participants") != 2 or len(outcomes) != 2 or outcomes.count("initialized") != 1 or not set(outcomes) <= allowed | {"initialized"}:
                raise ValueError("initialization race lacks valid participant outcomes")
        if initialization["initialization-commit-acknowledgement-loss"].get("outcome") != "reconciled":
            raise ValueError("initialization commit loss was not reconciled")
        if any(initialization[name].get("outcome") != expected for name, expected in bundle_changes.items()):
            raise ValueError("initialization bundle changes were not rejected")
        concurrency = {row["check"]: row for row in receipt["concurrency_checks"]}
        special = {"sqlite": ("sqlite-writer-lock-exhaustion", "retryable-busy"),
                   "duckdb": ("duckdb-external-writer-process", "busy/unsupported-writer"),
                   "postgres": ("postgres-duplicate-reconciliation", "both-committed-same-id")}[lane["engine"]]
        if set(concurrency) != {"concurrent-identical-writers", special[0]} or concurrency[special[0]].get("outcome") != special[1]:
            raise ValueError("writer concurrency check identities or outcomes differ")
        concurrent = concurrency["concurrent-identical-writers"]
        outcomes = concurrent.get("outcomes", [])
        if concurrent.get("barrier_participants") != 2 or len(outcomes) != 2 or "committed" not in outcomes or not set(outcomes) <= {"committed", "retryable-busy"}:
            raise ValueError("writer concurrency lacks committed-state evidence")
        if "loader" in lane:
            loader = receipt.get("loader", {})
            if loader.get("language") != lane["loader"] or loader.get("source_commit") != source["commit"]:
                raise ValueError("loader receipt lacks a build of this source commit")
            checks = loader.get("verify_checks", [])
            expected_loader = {"pristine-seed": (0, 0, 0), "reference-contract-populated": (1, 1, 0),
                               "runtime-document-populated": (1, 1, 1)}
            if len(checks) != len(expected_loader) or {row.get("check") for row in checks} != set(expected_loader):
                raise ValueError("loader standalone verify control population is missing or duplicated")
            for row in checks:
                code, contracts, documents = expected_loader[row["check"]]
                if row.get("exit_code") != code or row.get("counts") != {"reference_contract": contracts, "runtime_document": documents}:
                    raise ValueError("loader standalone verify did not observe the expected populated state")
                for table, count in row["counts"].items():
                    if not re.search(r"^\s*" + table + r"\s+" + str(count) + (r" != 0" if count else r" == 0"), row.get("output", ""), re.M):
                        raise ValueError("loader standalone verify lacks the intended table diagnostic")
            binary = root / loader.get("binary", "")
            if not binary.is_file() or hashlib.sha256(binary.read_bytes()).hexdigest() != loader.get("binary_sha256"):
                raise ValueError("missing or stale loader binary")
    return receipts
