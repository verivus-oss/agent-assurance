"""Structural adapter/binding checks. References remain inert at the SPEC layer."""

from pathlib import Path
import re

from _vocabulary import canonical_profile, load_catalog

KINDS = ("adapter-contract", "adapter-registry-binding", "gate-decision")
BINDINGS = (
    ("adapter-contract", "adapter", "runtime_kind", "runtime_kind", True),
    ("adapter-contract", "adapter", "runtime_network_policy", "runtime_network_policy", True),
    ("adapter-contract", "adapter", "runtime_clock_policy", "runtime_clock_policy", True),
    ("adapter-contract", "adapter", "id_derivation", "adapter_id_derivation", False),
    ("adapter-registry-binding", "binding", "adapter_ref_syntax", "adapter_ref_syntax", True),
    ("gate-decision", "decision", "verdict", "gate_decision_verdict", True),
)
ASSERTION_ID = re.compile(r"A-[A-Za-z0-9][A-Za-z0-9_-]*")
HEX64 = re.compile(r"[0-9a-f]{64}")
PRIMITIVES = frozenset({"thing", "scope", "path", "observed", "constraint", "time"})


def validate_fields(doc: dict, kind: str, repo_root: Path) -> list[str]:
    errors = []
    meta = doc.get("meta")
    if not isinstance(meta, dict) or meta.get("template_kind") != kind:
        return [f"RDMETA: meta.template_kind must equal {kind!r}"]
    if canonical_profile(meta.get("framework_profile")) != "agent-assurance":
        errors.append("RDMETA: meta.framework_profile must identify agent-assurance (AGDF alias accepted)")
    try:
        catalog = load_catalog(repo_root)
    except (OSError, ValueError) as exc:
        return [*errors, f"RDLOAD: vocabulary load failed: {exc}"]
    for owner, section, field, attribute, required in BINDINGS:
        if owner != kind:
            continue
        table = doc.get(section)
        if not isinstance(table, dict):
            errors.append(f"RDVOCAB {attribute}: {section} must be a table")
            continue
        if not required and field not in table:
            continue
        declaration = catalog.get(attribute)
        if declaration is None or declaration.extensible or not declaration.values:
            errors.append(f"RDLOAD: missing/invalid closed vocabulary {attribute}")
            continue
        value = table.get(field)
        if not isinstance(value, str) or value not in declaration.values:
            errors.append(f"RDVOCAB {attribute}: {section}.{field} must be a declared string; got type {type(value).__name__}")
    return errors


def _nonempty(table: dict, field: str, location: str, errors: list[str]) -> None:
    value = table.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"RDSTRUCT: {location}.{field} must be a nonempty string")


def _entries(table: dict, field: str, location: str, errors: list[str], *, required: bool = False) -> list[dict]:
    if field not in table and not required:
        return []
    value = table.get(field)
    if not isinstance(value, list) or (required and not value):
        errors.append(f"RDSTRUCT: {location}.{field} must be {'a nonempty' if required else 'an'} array of tables")
        return []
    if any(not isinstance(entry, dict) for entry in value):
        errors.append(f"RDSTRUCT: every {location}.{field} entry must be a table")
        return []
    return value


def validate_adapter(doc: dict, repo_root: Path, *, binding: bool = False) -> list[str]:
    kind = "adapter-registry-binding" if binding else "adapter-contract"
    errors = validate_fields(doc, kind, repo_root)
    section = "binding" if binding else "adapter"
    table = doc.get(section)
    if not isinstance(table, dict):
        return errors
    try:
        catalog = load_catalog(repo_root)
        extra = catalog["registry_scheme" if binding else "input_hash_method"]
    except (OSError, ValueError, KeyError) as exc:
        return [*errors, f"RDLOAD: vocabulary load failed: {exc}"]
    if binding:
        _nonempty(table, "adapter_ref", section, errors)
        _nonempty(table, "registry_url", section, errors)
        scheme, url = table.get("registry_url_scheme"), table.get("registry_url")
        if not isinstance(scheme, str) or scheme not in extra.values:
            errors.append("INV01: binding.registry_url_scheme must be declared in registry_scheme, including declared extensions")
        if not isinstance(scheme, str) or not isinstance(url, str) or not url.startswith(scheme + "://"):
            errors.append("INV02: binding.registry_url must start with the declared scheme followed by ://")
        for entry in _entries(table, "trust_anchor_refs", section, errors):
            _nonempty(entry, "anchor_id", "binding.trust_anchor_refs[]", errors)
        for entry in _entries(table, "policy_constraint_refs", section, errors):
            value = entry.get("constraint_id")
            if not isinstance(value, str) or ASSERTION_ID.fullmatch(value) is None:
                errors.append("INV03: binding.policy_constraint_refs[].constraint_id must match the whole ASCII assertion-ID grammar")
    else:
        _nonempty(table, "input_source", section, errors)
        if "input_hash_method" in table:
            value = table["input_hash_method"]
            if not isinstance(value, str) or (not extra.extensible and value not in extra.values):
                errors.append("RDVOCAB input_hash_method: adapter.input_hash_method must satisfy its declared string vocabulary")
        digest_field = {"wasi-component": "component_digest", "oci-action": "oci_image_digest",
                        "os-sandbox": "profile_args_digest"}.get(table.get("runtime_kind") if isinstance(table.get("runtime_kind"), str) else None)
        artifact = table.get("runtime_artifact")
        if not isinstance(artifact, dict):
            errors.append("INV02: adapter.runtime_artifact must be a table")
        elif digest_field:
            value = artifact.get(digest_field)
            if not isinstance(value, str) or HEX64.fullmatch(value) is None:
                errors.append(f"INV02: adapter.runtime_artifact.{digest_field} must be exactly 64 lowercase ASCII hex characters")
        for entry in _entries(table, "emits", section, errors, required=True):
            value = entry.get("ijb_primitive")
            if not isinstance(value, str) or value not in PRIMITIVES:
                errors.append("INV03: adapter.emits[].ijb_primitive must be one of the six IJB primitives")
        for entry in _entries(table, "conformance_fixtures", section, errors, required=True):
            for field in ("raw_input_ref", "expected_bundle_ref"):
                _nonempty(entry, field, "adapter.conformance_fixtures[]", errors)
        for entry in _entries(table, "declared_invariants", section, errors):
            for field in ("id", "description", "enforced_by"):
                _nonempty(entry, field, "adapter.declared_invariants[]", errors)
        if "runtime_env_allowlist" in table:
            env = table["runtime_env_allowlist"]
            if not isinstance(env, list) or any(not isinstance(value, str) for value in env):
                errors.append("RDSTRUCT: adapter.runtime_env_allowlist must be an array of strings")
    return errors
