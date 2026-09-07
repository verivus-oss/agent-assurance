"""Non-normative storage mapping and immutable validation-bundle identity."""

import hashlib
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "validators"))
import _toml11 as toml  # noqa: E402
from _vocabulary import load_catalog  # noqa: E402
from _runtime_document_vocab import BINDINGS  # noqa: E402
from _opaque import opaque_sha256  # noqa: E402

REPRESENTATIONS = {"document-column", "entity-column", "runtime-operand-catalog",
                   "pattern-catalog", "domain-key-catalog", "namespace-catalog", "catalog"}
ENGINES = ("postgres", "sqlite", "duckdb")
REGISTRY_TABLES = ("kind_descriptor", "entity_kind_descriptor", "relation_descriptor",
                   "attribute_vocabulary", "attribute_value_allowed")


def load_mapping(root: Path) -> list[dict]:
    catalog = load_catalog(root)
    mapping = toml.loads((root / "reference/database/vocabulary-storage.toml").read_text())
    if mapping.get("meta", {}).get("projection_version") != 1:
        raise ValueError("unsupported storage mapping version")
    rows = mapping.get("vocabularies")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("vocabulary mapping must be an array of tables")
    names = [row.get("attribute") for row in rows]
    if any(not isinstance(name, str) for name in names) or len(names) != len(set(names)) or set(names) != set(catalog):
        raise ValueError("mapping must have exactly one disposition per discovered vocabulary")
    sites = set()
    for row in rows:
        declaration = catalog[row["attribute"]]
        if (row.get("source") != declaration.source or row.get("extensible") is not declaration.extensible
                or row.get("representation") not in REPRESENTATIONS or not row.get("owner")):
            raise ValueError(f"invalid mapping disposition: {row['attribute']}")
        if not isinstance(row.get("enforcement_sites"), list):
            raise ValueError("every mapping needs explicit enforcement sites, empty for catalog-only")
        if row["representation"] == "document-column":
            path = row.get("path")
            if not isinstance(path, list) or not path or any(not isinstance(part, str) or not part for part in path):
                raise ValueError("extraction paths must be nonempty literal segment arrays")
            kind = row.get("template_kind")
            if kind not in {"adapter-contract", "adapter-registry-binding", "gate-decision"}:
                raise ValueError("unsupported projection kind")
            descriptor = toml.loads((root / f"profiles/agent-assurance/{kind}-kind.toml").read_text())["kind"]
            required = any(entry["path"] == ".".join(path) for entry in descriptor["required_fields"])
            if not isinstance(row.get("required"), bool) or row["required"] != required or declaration.extensible:
                raise ValueError(f"mapping requiredness/closed-field mismatch: {row['attribute']}")
            if row["enforcement_sites"] != [["runtime_document", row.get("column")]]:
                raise ValueError("document mapping must identify its actual runtime_document column")
            if (kind, tuple(path)) in sites:
                raise ValueError("duplicate extraction path")
            sites.add((kind, tuple(path)))
            owners = row.get("validator_owners")
            expected_owners = {"validators/validate_" + kind.replace("-", "_") + ".py",
                               "validators/_runtime_document_vocab.py"}
            if (not isinstance(owners, list) or len(owners) != len(expected_owners) or set(owners) != expected_owners
                    or any(not (root / owner).is_file() for owner in owners)):
                raise ValueError("missing validator owner")
    smoke = next(row for row in rows if row["attribute"] == "smoke.decision")
    if (smoke.get("representation") != "catalog" or smoke.get("follow_up_status") != "open"
            or smoke.get("follow_up") != "promote-smoke-validation-result-decision" or not smoke.get("follow_up_completion")):
        raise ValueError("smoke.decision requires the explicit open storage/semantic follow-up")
    expected_documents = {(attribute, kind, (section, field), attribute, required)
                          for kind, section, field, attribute, required in BINDINGS}
    actual_documents = {(row["attribute"], row["template_kind"], tuple(row["path"]), row["column"], row["required"])
                        for row in rows if row["representation"] == "document-column"}
    if actual_documents != expected_documents:
        raise ValueError("document mapping must match every supported validator binding exactly")
    expected_entities = {"priority": "priority", "unit.status": "unit_status", "review.status": "review_status",
                         "likelihood": "likelihood", "impact": "impact", "residual_risk": "residual", "status": "smoke_status"}
    actual_entities = {row["attribute"]: row["enforcement_sites"]
                       for row in rows if row["representation"] == "entity-column"}
    if actual_entities != {key: [["entity", column]] for key, column in expected_entities.items()}:
        raise ValueError("entity mapping differs from the supported physical projection")
    if any(row["enforcement_sites"] for row in rows
           if row["representation"] not in {"entity-column", "document-column"}):
        raise ValueError("catalog-only dispositions cannot claim physical column enforcement")
    return rows


def bundle_entries(root: Path) -> dict[str, str]:
    root = root.resolve()
    paths = {root / name for name in (
        "spec.md", "core/ontology.md", "core/ontology.toml",
        "profiles/agent-assurance/ontology.toml", "profiles/agent-assurance/PROFILE.toml",
        "foundations/ijb/canonical-assertion-grammar.md", "reference/database/vocabulary-storage.toml",
        "requirements/toml.txt", "requirements/database.txt",
        "reference/database/engine-lock.toml",
    )}
    for pattern in ("profiles/*/ontology.toml", "core/*-kind.toml", "profiles/*/*-kind.toml",
                    "profiles/*/PROFILE.toml", "validators/**/*.py", "reference/database/**/*.py",
                    "requirements/database*.txt"):
        paths.update(root.glob(pattern))
    entries = {}
    for path in paths:
        relative = path.relative_to(root).as_posix()
        if any(part in {".", ".."} for part in path.relative_to(root).parts) or not path.resolve().is_relative_to(root):
            raise ValueError(f"bundle path escapes trusted root: {relative!r}")
        if relative in entries or not path.is_file():
            raise ValueError(f"duplicate or missing bundle file: {relative!r}")
        entries[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(sorted(entries.items(), key=lambda item: item[0].encode("utf-8")))


def bundle_digest(root: Path) -> str:
    entries = bundle_entries(root)
    digest = hashlib.sha256(b"DAGTOML-reference-contract-v1\0" + struct.pack(">Q", len(entries)))
    for path, file_hash in entries.items():
        encoded = path.encode("utf-8")
        digest.update(struct.pack(">Q", len(encoded)))
        digest.update(encoded)
        digest.update(bytes.fromhex(file_hash))
    return digest.hexdigest()


def artifact_hashes(root: Path) -> dict[str, str]:
    paths = [f"reference/database/{engine}/{name}.sql" for engine in ENGINES for name in ("schema", "seed")]
    paths.extend(["reference/database/MANIFEST.toml", "reference/database/vocabulary-storage.toml",
                  "reference/database/engine-lock.toml"])
    return {path: opaque_sha256(root / path) for path in paths}


def expected_counts(root: Path) -> dict[str, int]:
    catalog = load_catalog(root)
    ontologies = [root / "core/ontology.toml", *sorted(root.glob("profiles/*/ontology.toml"))]
    docs = [toml.loads(path.read_text()) for path in ontologies]
    return dict(zip(REGISTRY_TABLES, (
        1 + len(list(root.glob("core/*-kind.toml"))) + len(list(root.glob("profiles/*/*-kind.toml"))),
        sum(len(doc.get("entities", [])) for doc in docs),
        sum(len(doc.get("relations", [])) for doc in docs),
        len(catalog), sum(len(item.values) for item in catalog.values()),
    ), strict=True))
