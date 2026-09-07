#!/usr/bin/env python3
"""Exercise gate failure controls and retain property-level mutation evidence."""


import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference/database"))
sys.path.insert(0, str(ROOT / "conformance"))
from _contract import artifact_hashes, bundle_digest, load_mapping  # noqa: E402
from _isolated import copy_source  # noqa: E402
from _storage import Store, StorageError  # noqa: E402
from _sql_probes import probe_constraints  # noqa: E402
from check_database_job_results import JOBS, validate as validate_jobs  # noqa: E402
from check_database_vocabularies import run_lane, source_identity  # noqa: E402
from check_runtime_ownership import declarations  # noqa: E402
from check_sql_source_access import opaque_sql_only  # noqa: E402
from discrimination import discover_cases  # noqa: E402
from negative_fixtures import population  # noqa: E402
from runtime_coverage import execute as runtime_observations  # noqa: E402
from _instrument import require  # noqa: E402


def replaced(text, old, new):
    if text.count(old) != 1:
        raise AssertionError("mutation must select exactly one source subject: " + repr(old))
    return text.replace(old, new)


def read_sql_descriptor(path):
    descriptor = os.open(path, os.O_RDONLY)
    try:
        return os.read(descriptor, 1)
    finally:
        os.close(descriptor)


def controls(root, work):
    observations = []

    def killed(name, operation, exception, needle):
        try:
            operation()
        except exception as exc:
            if needle not in str(exc):
                raise AssertionError(f"{name}: unrelated/setup failure: {exc}") from exc
            observations.append({"control": name, "status": "killed", "failing_property": needle,
                                 "exception": type(exc).__name__, "output": str(exc)})
        else:
            raise AssertionError(name + ": mutation survived")

    schema = (root / "reference/database/sqlite/schema.sql").read_text()
    seed = (root / "reference/database/sqlite/seed.sql").read_text()
    stores = []

    def database(name, mutated_schema=schema):
        path = work / (name + ".db")
        (work / (name + "-schema.sql")).write_text(mutated_schema)
        connection = sqlite3.connect(path, isolation_level=None)
        store = Store("sqlite", connection, root)
        store.prepare()
        # Artifact setup errors occur outside the expected-failure catch.
        connection.executescript(mutated_schema)
        connection.executescript(seed)
        stores.append(store)
        return store

    try:
        baseline = database("positive-control")
        baseline.verify_catalog()
        positive_probes = probe_constraints(baseline, bundle_digest(root))
        if not positive_probes or {row["actual"] for row in positive_probes} != {"accept", "reject"}:
            raise AssertionError("real-engine positive baseline has no discriminating probes")
        for name, statement in (("deleted-catalog-token", "DELETE FROM dagtoml_attribute_value_allowed WHERE attribute='severity_tier' AND value='critical'"),
                                ("same-count-catalog-replacement", "UPDATE dagtoml_attribute_value_allowed SET value='invented' WHERE attribute='severity_tier' AND value='critical'"),
                                ("false-backing-hint", "UPDATE dagtoml_attribute_vocabulary SET backing_check_constraint='smoke_status' WHERE attribute='smoke.decision'"),
                                ("missing-backing-hint", "UPDATE dagtoml_attribute_vocabulary SET backing_check_constraint=NULL WHERE attribute='runtime_kind'")):
            store = database(name)
            before = store.connection.total_changes
            store.execute(statement)
            if store.connection.total_changes != before + 1:
                raise AssertionError("catalog mutation failed to select its token")
            killed(name, store.verify_catalog, StorageError, "catalog-mismatch")
        kind_check = "CHECK (runtime_kind IS NULL OR runtime_kind IN ('wasi-component', 'oci-action', 'os-sandbox'))"
        gate_check = "CHECK (gate_decision_verdict IS NULL OR gate_decision_verdict IN ('pass', 'fail'))"
        mutations = (("loosened-runtime-column", replaced(schema, kind_check, "CHECK (1)"), "forbidden target write succeeded"),
                     ("constraint-on-neighbor", replaced(schema, kind_check,
                        "CHECK (runtime_clock_policy IS NULL OR runtime_clock_policy IN ('wasi-component', 'oci-action', 'os-sandbox'))"), "target failed outside the expected"),
                     ("removed-gate-sql-membership", replaced(schema, gate_check, "CHECK (1)"), "forbidden target write succeeded"))
        provenance_check = "CHECK (length(CAST(source_sha256 AS BLOB)) = 71 AND length(source_sha256) = 71 AND substr(source_sha256, 1, 7) = 'sha256:' AND substr(source_sha256, 8) NOT GLOB '*[^0-9a-f]*')"
        mutations += (("loosened-provenance-digest", replaced(schema, provenance_check, "CHECK (length(source_sha256) = 71)"), "forbidden target write succeeded"),
                      ("text-length-bundle-digest", replaced(schema, "length(CAST(contract_bundle_sha256 AS BLOB)) = 64", "length(contract_bundle_sha256) = 64"), "forbidden target write succeeded"))
        mutations += (("nul-truncated-contract-digest", replaced(schema, " AND length(contract_bundle_sha256) = 64", ""), "forbidden target write succeeded"),
                      ("nul-truncated-provenance-digest", replaced(schema, " AND length(source_sha256) = 71", ""), "forbidden target write succeeded"))
        for name, variant, needle in mutations:
            store = database(name, variant)
            store.verify_catalog()
            killed(name, lambda: probe_constraints(store, bundle_digest(root)), AssertionError, needle)
        # Independent spot check of the relaxed-column kill, without the probe
        # planner or its fixture builder. This write is invalid by the ontology.
        from _sql_probes import document_fixture
        relaxed = database("independent-loosened-spot-check", mutations[0][1])
        digest = bundle_digest(root)
        relaxed.insert("reference_contract", {"singleton_id": 1, "contract_bundle_sha256": digest, "projection_version": 1})
        identifier = "independent-spot-check"
        relaxed.insert("instance_file", {"id": identifier, "source_path": "independent.toml", "content_sha256": "sha256:" + "0" * 64,
                                         "schema_version": "0.1.0", "template_kind": "adapter-contract", "framework_profile": "agent-assurance"})
        row = document_fixture("adapter-contract", identifier, digest)
        row["runtime_kind"] = "not-a-declared-runtime"
        relaxed.insert("runtime_document", row)
        require(relaxed.rows("runtime_document", ("runtime_kind",)) == [{"runtime_kind": "not-a-declared-runtime"}])
        observations.append({"control": "independent-loosened-spot-check", "status": "confirmed",
                             "output": "relaxed SQL accepted not-a-declared-runtime; the independent ontology oracle rejects it"})
        baseline.initialize(exclusive_unpublished=True)

        class MissingDocumentHalf(Store):
            def insert(self, table, values):
                if table != "runtime_document":
                    return super().insert(table, values)
                return None

        mutant = MissingDocumentHalf("sqlite", baseline.connection, root)
        raw = (root / "examples/minimal-adapter-contract.toml").read_bytes()

        def atomic_property():
            receipt = mutant.ingest([("atomic-mutant.toml", raw)])
            identifier = receipt["documents"][0]["id"]
            require(len(mutant.rows("runtime_document", ("source_toml",), "WHERE instance_file_id = ?", (identifier,))) == 1, "atomic write lacks its document half")

        killed("removed-atomic-document-half", atomic_property, AssertionError, "atomic write lacks its document half")
        killed("wrong-linked-engine-version", lambda: run_lane(root, "sqlite", str(work / "wrong-version.db"), "0.0.0", "sqlite-floor"), ValueError, "wrong engine version")
        with opaque_sql_only():
            hashes = artifact_hashes(root)
            require(len(hashes) == 9 and all(len(value) == 64 for value in hashes.values()))
            killed("SQL-text-inference", lambda: (root / "reference/database/sqlite/schema.sql").read_text(), ValueError, "SQL-source-access")
            killed("SQL-byte-inference", lambda: (root / "reference/database/sqlite/seed.sql").read_bytes().decode(), ValueError, "SQL-source-access")
            killed("SQL-os-open-inference", lambda: read_sql_descriptor(root / "reference/database/sqlite/schema.sql"), ValueError, "SQL-source-access")
        from check_sql_source_access import main as checker
        require(checker(["--repo-root", str(root), "--declarations-only", "--no-rdf"]) == 0)
        good_jobs = {name: {"result": "success"} for name in JOBS}
        validate_jobs(good_jobs)
        for name in sorted(JOBS):
            for state in ("failure", "skipped", "cancelled"):
                variant = deepcopy(good_jobs)
                variant[name]["result"] = state
                killed("dependency/" + name + "/" + state, lambda: validate_jobs(variant), ValueError, "must succeed")
        killed("missing-dependency", lambda: validate_jobs({}), ValueError, "exactly")

        candidate = work / "source"
        copy_source(root, candidate)
        checker_source = candidate / "validators/check_attribute_values.py"
        original_checker = checker_source.read_text()
        checker_source.write_text(replaced(original_checker, '    registry = expected_counts(repo_root)',
            '    (repo_root / "reference/database/sqlite/schema.sql").read_text()\n    registry = expected_counts(repo_root)'))
        try:
            process = subprocess.run([sys.executable, str(candidate / "validators/check_sql_source_access.py"),  # nosec B603 # noqa: S603
                                      "--repo-root", str(candidate), "--declarations-only", "--no-rdf"],
                                     cwd=candidate, capture_output=True, text=True, timeout=60)
            require(process.returncode == 1 and "SQL-source-access" in process.stdout, process.stdout + process.stderr)
            observations.append({"control": "reintroduced-checker-SQL-interpretation", "status": "killed",
                                 "failing_property": "SQL source unavailable to checker", "output": process.stdout + process.stderr})
        finally:
            checker_source.write_text(original_checker)
        from _review_controls import exercise as review_controls
        observations.extend(review_controls(candidate, work))
        declarations(candidate)
        discover_cases(candidate / "conformance/cases")
        population(candidate, candidate / "conformance/negative-expectations.toml")
        mapping = candidate / "reference/database/vocabulary-storage.toml"
        original = mapping.read_text()
        variants = {
            "missing-vocabulary-mapping": re.sub(r'\[\[vocabularies\]\]\nattribute = "runtime_kind".*?(?=\[\[vocabularies\]\])', '', original, count=1, flags=re.S),
            "missing-validator-module-owner": replaced(original,
                'validator_owners = ["validators/validate_gate_decision.py", "validators/_runtime_document_vocab.py"]',
                'validator_owners = ["validators/validate_gate_decision.py"]'),
            "missing-invariant-owner": original[:original.rindex("[[invariant_owners]]")],
            "missing-required-section-disposition": re.sub(r'\[\[required_section_dispositions\]\].*?(?=\[\[)', '', original, count=1, flags=re.S),
        }
        for name, variant in variants.items():
            require(variant != original)
            mapping.write_text(variant)
            try:
                killed(name, lambda: declarations(candidate), ValueError,
                       {"missing-vocabulary-mapping": "one disposition", "missing-validator-module-owner": "validator owner",
                        "missing-invariant-owner": "ownership ledger", "missing-required-section-disposition": "disposition ledger"}[name])
            finally:
                mapping.write_text(original)
        descriptor = candidate / "profiles/agent-assurance/adapter-contract-kind.toml"
        original_descriptor = descriptor.read_text()
        for name, variant, needle in (
            ("new-unknown-invariant", replaced(original_descriptor, '\nid          = "INV01"', '\nid          = "INV99"'), "ownership ledger"),
            ("planned-shipped-owner", replaced(original_descriptor, 'enforced_by = "validators/validate_adapter_contract.py"',
                'enforced_by = "validators/validate_adapter_contract.py (planned)"') if original_descriptor.count('enforced_by = "validators/validate_adapter_contract.py"') == 1
                else original_descriptor.replace('enforced_by = "validators/validate_adapter_contract.py"', 'enforced_by = "validators/validate_adapter_contract.py (planned)"', 1), "stale planned")):
            require(variant != original_descriptor)
            descriptor.write_text(variant)
            try:
                killed(name, lambda: declarations(candidate), ValueError, needle)
            finally:
                descriptor.write_text(original_descriptor)
        side = next((candidate / "conformance/cases/gate-decision/invalid").glob("*.expected.toml"))
        contents = side.read_bytes()
        side.unlink()
        try:
            killed("missing-sidecar", lambda: discover_cases(candidate / "conformance/cases"), ValueError, "no expected sidecar")
        finally:
            side.write_bytes(contents)
        orphan = side.with_name("orphan.expected.toml")
        orphan.write_bytes(contents)
        try:
            killed("orphan-sidecar", lambda: discover_cases(candidate / "conformance/cases"), ValueError, "orphan sidecar")
        finally:
            orphan.unlink()
        new_kind = candidate / "conformance/cases/unmapped-new-kind"
        new_kind.mkdir()
        try:
            killed("new-unmapped-kind", lambda: discover_cases(candidate / "conformance/cases"), ValueError, "no KIND_VALIDATOR")
        finally:
            new_kind.rmdir()
        for verdict in ("valid", "invalid"):
            directory = candidate / "conformance/cases/gate-decision" / verdict
            hidden = directory.with_name(verdict + "-withheld")
            directory.rename(hidden)
            try:
                killed("missing-" + verdict + "-control", lambda: discover_cases(candidate / "conformance/cases"), ValueError, "no " + verdict + " control")
            finally:
                hidden.rename(directory)
        unwired = candidate / "examples/negative/unwired-fixture.toml"
        unwired.write_bytes(raw)
        try:
            killed("new-unwired-negative", lambda: population(candidate, candidate / "conformance/negative-expectations.toml"), ValueError, "missing, duplicate, or orphan")
        finally:
            unwired.unlink()
        require(all(item["passed"] for item in runtime_observations(candidate)))
        module = candidate / "validators/_runtime_document_vocab.py"
        original_module = module.read_text()
        py_mutations = (
            ("removed-gate-membership", replaced(original_module,
                '    ("gate-decision", "decision", "verdict", "gate_decision_verdict", True),\n', '')),
            ("optional-wrong-type-as-absence", replaced(original_module,
                'if not required and field not in table:', 'if not required and (field not in table or not isinstance(table[field], str)):')),
            ("misrouted-adapter-kind", replaced(original_module,
                'errors = validate_fields(doc, kind, repo_root)', 'errors = validate_fields(doc, "adapter-registry-binding", repo_root)')),
        )
        for name, variant in py_mutations:
            module.write_text(variant)
            try:
                failures = [item for item in runtime_observations(candidate) if not item["passed"]]
                require(failures, name + " survived the independent specimen gate")
                observations.append({"control": name, "status": "killed", "failing_property": "independent expected outcome",
                                     "output": failures})
            finally:
                module.write_text(original_module)
        ontology = candidate / "profiles/agent-assurance/ontology.toml"
        original_ontology = ontology.read_text()
        ontology.write_text(original_ontology + '\n[[attribute_vocabularies]]\nattribute="runtime_kind"\nvalues=[]\nextensible=false\n')
        try:
            killed("duplicate-ontology-vocabulary", lambda: load_mapping(candidate), ValueError, "duplicate")
        finally:
            ontology.write_text(original_ontology)
        mandatory = candidate / "spec.md"
        content = mandatory.read_bytes()
        mandatory.unlink()
        try:
            killed("missing-bundle-source", lambda: bundle_digest(candidate), ValueError, "missing bundle file")
        finally:
            mandatory.write_bytes(content)
    finally:
        for store in stores:
            store.connection.close()
    return observations


def receipt_controls(root, paths, work):
    from _receipts import validate_receipts
    validate_receipts(root, paths)
    original = [json.loads(path.read_text()) for path in paths]
    observations = []
    variants = {}
    variants["missing-lane"] = original[:-1]
    variants["duplicate-lane"] = [*original, original[0]]
    for name, edit in (
        ("wrong-version", lambda row: row.update(actual_version="0.0.0")),
        ("stale-source", lambda row: row["source"].update(commit="0" * 40)),
        ("zero-probes", lambda row: row.update(constraint_probes=[])),
        ("renamed-probe", lambda row: row["constraint_probes"][0].update(probe="invented")),
        ("skipped-check", lambda row: row.update(skipped=["engine unavailable"])),
        ("failed-probe", lambda row: row["constraint_probes"][0].update(actual="inconclusive")),
        ("missing-replay", lambda row: row.update(replay_checks=[])),
        ("missing-metadata", lambda row: row.update(metadata_checks=[])),
    ):
        variant = deepcopy(original)
        edit(variant[0])
        variants[name] = variant
    variant = deepcopy(original)
    next(row for row in variant if "loader" in row)["loader"]["binary_sha256"] = "0" * 64
    variants["stale-loader-binary"] = variant
    variant = deepcopy(original)
    next(row for row in variant if "loader" in row)["loader"]["verify_checks"] = []
    variants["missing-loader-verify-controls"] = variant
    for name, variant in variants.items():
        directory = work / name
        directory.mkdir()
        candidates = []
        for index, row in enumerate(variant):
            path = directory / f"{index}.json"
            path.write_text(json.dumps(row))
            candidates.append(path)
        try:
            validate_receipts(root, candidates)
        except ValueError as exc:
            observations.append({"control": name, "status": "killed", "output": str(exc)})
        else:
            raise AssertionError("receipt mutation survived: " + name)
    return observations


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--receipts", type=Path, nargs="+", help="run the separate full-matrix receipt failure controls")
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    identity = source_identity(root)
    work = root / ".local/database-instruments" / uuid.uuid4().hex
    work.mkdir(parents=True)
    path = work / "receipt.json"
    path.write_text(json.dumps({"status": "incomplete"}))
    try:
        observations = receipt_controls(root, args.receipts, work) if args.receipts else controls(root, work)
        if not observations or len({row["control"] for row in observations}) != len(observations):
            raise AssertionError("instrument population is empty or duplicated")
        if source_identity(root) != identity:
            raise AssertionError("instrument modified the source tree it measured")
    except Exception as exc:
        path.write_text(json.dumps({"status": "failed", "source": identity, "error": str(exc)}, indent=2))
        raise
    path.write_text(json.dumps({"status": "passed", "source": identity, "controls": observations,
                               "scope": "full-matrix receipt failure controls" if args.receipts else "SQL, validator, ownership, discovery, and job-result instruments",
                               "skipped": []}, ensure_ascii=True, indent=2) + "\n")
    print(f"PASS: {len(observations)} property controls, compared with passing controls; skipped=[]; evidence={path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
