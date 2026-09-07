"""Captured TOML bytes and deterministic, portable metadata indexes."""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import re

from _contract import load_mapping
from _runtime_validation import validate_document
from _runtime_document_vocab import KINDS
import _toml11 as toml

INSTANCE_COLUMNS = ("source_path", "content_sha256", "schema_version", "ontology_version",
                    "template_kind", "framework_profile", "title", "docs_url", "created",
                    "created_at", "meta_extras")
PROVENANCE_COLUMNS = ("source_path", "source_sha256", "source_bytes", "captured_at",
                      "extraction_method", "source_description", "extras")
PROJECTION_COLUMNS = ("runtime_kind", "runtime_network_policy", "runtime_clock_policy",
                      "adapter_id_derivation", "adapter_ref_syntax", "gate_decision_verdict")
META_KEYS = {"schema_version", "ontology_version", "template_kind", "framework_profile",
             "title", "docs", "created", "created_at"}
RFC3339 = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt][0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:[Zz]|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])")


@dataclass(frozen=True)
class Projection:
    source: bytes
    instance: dict
    provenance: dict | None
    fields: dict
    unindexed_fields: tuple[tuple[str, ...], ...]


class UnsupportedProjection(ValueError):
    code = "unsupported-projection"


def text_identity(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or "\0" in value:
        raise ValueError(f"invalid mandatory text identity: {label}")
    value.encode("utf-8", errors="strict")
    return value


def json_representable(value: object) -> bool:
    if isinstance(value, str):
        return "\0" not in value
    if isinstance(value, bool):
        return True
    if isinstance(value, int):
        return abs(value) <= 9007199254740991
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(json_representable(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and "\0" not in key and json_representable(item)
                   for key, item in value.items())
    return False


def json_index(table: dict, excluded: set[str], prefix: str, omitted: list) -> str:
    result = {}
    for key, value in table.items():
        if key in excluded:
            continue
        if "\0" not in key and json_representable(value):
            result[key] = value
        else:
            omitted.append((prefix, key))
    return json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def optional_index(table: dict, key: str, prefix: str, omitted: list, convert) -> object:
    if key not in table:
        return None
    value = convert(table[key])
    if value is None:
        omitted.append((prefix, key))
    return value


def optional_text(value: object) -> str | None:
    return value if isinstance(value, str) and "\0" not in value else None


def date_index(value: object) -> str | None:
    if type(value) is date:
        return value.isoformat()
    if isinstance(value, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            pass
    return None


def timestamp_index(value: object) -> str | None:
    if isinstance(value, str):
        if not RFC3339.fullmatch(value):
            return None
        try:
            value = datetime.fromisoformat(value.upper().replace("Z", "+00:00"))
        except ValueError:
            return None
    if isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None:
        try:
            return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        except (OverflowError, ValueError):
            return None
    return None


def _unique_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key in stored JSON index")
        result[key] = value
    return result


def semantic_json(text: str) -> object:
    """Tagged scalars prevent Python's True == 1 from hiding index corruption."""
    value = json.loads(text, parse_int=Decimal, parse_float=Decimal,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")),
                       object_pairs_hook=_unique_object)

    def tagged(item):
        if isinstance(item, dict):
            return ("object", {key: tagged(child) for key, child in item.items()})
        if isinstance(item, list):
            return ("array", [tagged(child) for child in item])
        return (type(item).__name__, item)

    return tagged(value)


def project(source: bytes, source_path: str, repo_root: Path) -> Projection:
    """Validate and project the supplied immutable buffer, without reopening it."""
    source_path = text_identity(source_path, "source_path")
    if not isinstance(source, bytes):
        raise ValueError("source must be captured bytes")
    doc = toml.loads(source.decode("utf-8", errors="strict"))
    meta = doc.get("meta")
    kind = meta.get("template_kind") if isinstance(meta, dict) else None
    if not isinstance(kind, str) or kind not in KINDS:
        raise UnsupportedProjection("unsupported-projection: only adapter-contract, adapter-registry-binding, and gate-decision are supported")
    errors = validate_document(doc, Path(source_path), repo_root, kind)
    if errors:
        raise ValueError("document validation failed: " + json.dumps(errors, ensure_ascii=True))
    omitted = []
    instance = {"source_path": source_path, "content_sha256": "sha256:" + hashlib.sha256(source).hexdigest()}
    for key in ("schema_version", "template_kind", "framework_profile"):
        instance[key] = text_identity(meta.get(key), "meta." + key)
    ontology_version = meta.get("ontology_version")
    if ontology_version is not None and (type(ontology_version) is not int or not 1 <= ontology_version <= 2147483647):
        raise ValueError("invalid meta.ontology_version")
    instance["ontology_version"] = ontology_version
    for key, column, convert in (("title", "title", optional_text), ("docs", "docs_url", optional_text),
                                 ("created", "created", date_index), ("created_at", "created_at", timestamp_index)):
        instance[column] = optional_index(meta, key, "meta", omitted, convert)
    instance["meta_extras"] = json_index(meta, META_KEYS, "meta", omitted)
    provenance = None
    if "provenance" in doc:
        table = doc["provenance"]
        provenance = {key: text_identity(table.get(key), "provenance." + key)
                      for key in ("source_path", "source_sha256")}
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", provenance["source_sha256"]):
            raise ValueError("provenance.source_sha256 must use canonical prefixed lowercase encoding")
        count = table.get("source_bytes")
        if type(count) is not int or not 0 <= count <= 9223372036854775807:
            raise ValueError("provenance.source_bytes must be a nonnegative signed 64-bit integer")
        provenance["source_bytes"] = count
        for key in ("captured_at", "extraction_method", "source_description"):
            provenance[key] = optional_index(table, key, "provenance", omitted,
                                             timestamp_index if key == "captured_at" else optional_text)
        provenance["extras"] = json_index(table, set(PROVENANCE_COLUMNS) - {"extras"}, "provenance", omitted)
    fields = dict.fromkeys(PROJECTION_COLUMNS)
    for row in load_mapping(repo_root):
        if row["representation"] == "document-column" and row["template_kind"] == kind:
            value = doc
            for segment in row["path"]:
                value = value.get(segment) if isinstance(value, dict) else None
            fields[row["column"]] = value
    return Projection(source, instance, provenance, fields, tuple(omitted))
