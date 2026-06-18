#!/usr/bin/env python3
"""Validate draft process-control TOML files used in this repository."""

from __future__ import annotations

import argparse
import pathlib
import sys
import _toml11 as tomllib  # TOML 1.1 reference shim (stdlib tomllib is 1.0-only); see validators/_toml11.py


RELEASE_VERSION = "0.1.0"
PLACEHOLDER_MARKERS = ("<", ">", "YYYY-MM-DD")
PATH_FIELDS = ("path", "artifact_path", "evidence_path", "file_path")

KIND_ALIASES = {
    "readiness-gate": {
        "readiness-gate",
        "readiness_gate",
        "readiness",
        "gate-readiness",
    },
    "contract-declaration": {
        "contract-declaration",
        "contract_declaration",
        "contract",
        "contracts",
    },
    "evidence-matrix": {
        "evidence-matrix",
        "evidence_matrix",
        "evidence",
        "matrix",
    },
}

SECTION_ALIASES = {
    "readiness-gate": {
        "artifact_classes": ["artifact_classes", "artifacts", "readiness.artifact_classes"],
        "gates": ["gates", "readiness_gates", "readiness.gates"],
    },
    "contract-declaration": {
        "contracts": ["contracts", "declarations", "contract_declarations"],
    },
    "evidence-matrix": {
        "claims": ["claims", "assertions"],
        "evidence": ["evidence", "artifacts", "evidence_artifacts"],
        "matrix": ["matrix", "rows", "evidence_matrix"],
    },
}

REQUIRED_FIELDS = {
    "readiness-gate": {
        "artifact_classes": [("id",)],
        "gates": [("id",), ("artifact_class",), ("checks", "required_documents", "criteria", "summary")],
    },
    "contract-declaration": {
        "contracts": [("id",), ("statement", "contract", "summary"), ("applies_to", "depends_on", "supersedes", "verified_by")],
    },
    "evidence-matrix": {
        "claims": [("id",), ("claim", "statement", "assertion")],
        "evidence": [("id",), ("path", "artifact_path", "evidence_path", "file_path")],
        "matrix": [
            ("id",),
            ("claim", "claim_id"),
            ("evidence", "evidence_id"),
            ("scope_covered", "scope"),
            ("known_exclusions", "exclusions", "limitations"),
        ],
    },
}

LINK_FIELDS = {
    "readiness-gate": {
        "gates": {
            "artifact_class": "artifact_classes",
        },
    },
    "contract-declaration": {
        "contracts": {
            "depends_on": "contracts",
            "supersedes": "contracts",
            "related_to": "contracts",
            "verified_by": None,
            "applies_to": None,
        },
    },
    "evidence-matrix": {
        "matrix": {
            "claim": "claims",
            "claim_id": "claims",
            "evidence": "evidence",
            "evidence_id": "evidence",
        },
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a review-readiness TOML file.")
    parser.add_argument("toml_file", nargs="?", help="Path to the TOML file to validate.")
    parser.add_argument(
        "--version",
        action="version",
        version=RELEASE_VERSION,
        help="Show program version and exit.",
    )
    parser.add_argument(
        "--kind",
        choices=("auto", "readiness-gate", "contract-declaration", "evidence-matrix"),
        default="auto",
        help="Force a template kind instead of auto-detecting it from the document.",
    )
    parser.add_argument(
        "--repo-root",
        help="Repository root used for optional evidence path existence checks.",
    )
    parser.add_argument(
        "--check-paths-exist",
        action="store_true",
        help="Verify evidence file paths exist relative to --repo-root.",
    )
    parser.add_argument(
        "--allow-placeholders",
        action="store_true",
        help="Allow placeholder strings like <artifact-id> in ids, links, and paths.",
    )
    return parser.parse_args()


def load_toml(path: pathlib.Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def normalize_kind(value: str | None) -> str | None:
    if value is None:
        return None
    value = str(value).strip().lower().replace("_", "-")
    for kind, aliases in KIND_ALIASES.items():
        if value == kind or value in aliases:
            return kind
    return None


def has_placeholder(value: str) -> bool:
    return any(marker in value for marker in PLACEHOLDER_MARKERS)


def collect_placeholder_errors(value: object, prefix: str = "") -> list[str]:
    errors: list[str] = []
    if isinstance(value, str):
        if has_placeholder(value):
            errors.append(prefix or "<root>")
        return errors
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            errors.extend(collect_placeholder_errors(child, child_prefix))
        return errors
    if isinstance(value, list):
        for index, child in enumerate(value):
            child_prefix = f"{prefix}[{index}]" if prefix else f"[{index}]"
            errors.extend(collect_placeholder_errors(child, child_prefix))
    return errors


def section_value(doc: dict, dotted_path: str) -> object | None:
    current: object = doc
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def entries_from_value(value: object) -> list[dict]:
    if isinstance(value, list):
        return [entry for entry in value if isinstance(entry, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def resolve_section(doc: dict, aliases: list[str]) -> tuple[str | None, object | None, list[dict]]:
    for alias in aliases:
        value = section_value(doc, alias)
        if value is not None:
            return alias, value, entries_from_value(value)
    return None, None, []


def collect_ids(entries: list[dict], section: str) -> tuple[dict[str, dict], list[str]]:
    ids: dict[str, dict] = {}
    errors: list[str] = []
    for entry in entries:
        entity_id = entry.get("id")
        if not entity_id:
            errors.append(f"{section}: missing required `id` field")
            continue
        if entity_id in ids:
            errors.append(f"duplicate id: {entity_id}")
            continue
        ids[entity_id] = entry
    return ids, errors


def validate_required_sections(doc: dict, kind: str) -> tuple[dict[str, list[dict]], list[str]]:
    resolved: dict[str, list[dict]] = {}
    errors: list[str] = []

    meta = section_value(doc, "meta")
    if not isinstance(meta, dict):
        errors.append("missing required `meta` section")
    else:
        release_version = meta.get("release_version")
        if release_version is not None and release_version != RELEASE_VERSION:
            errors.append(f"meta.release_version ({release_version}) does not match expected {RELEASE_VERSION}")

    for canonical_section, aliases in SECTION_ALIASES[kind].items():
        alias, raw_value, entries = resolve_section(doc, aliases)
        if raw_value is None:
            errors.append(f"missing required `{canonical_section}` section")
            continue
        if not isinstance(raw_value, (dict, list)):
            errors.append(f"`{alias}` must be a table or array of tables")
            continue
        if isinstance(raw_value, list):
            if not raw_value:
                errors.append(f"`{alias}` must contain at least one entry")
            for index, item in enumerate(raw_value):
                if not isinstance(item, dict):
                    errors.append(f"`{alias}` entry at index {index} must be a table")
        resolved[canonical_section] = entries

    return resolved, errors


def validate_entry_fields(kind: str, section: str, entries: list[dict]) -> list[str]:
    errors: list[str] = []
    for index, entry in enumerate(entries):
        entry_id = entry.get("id", f"{section}[{index}]")
        for field_group in REQUIRED_FIELDS[kind].get(section, []):
            if not any(field in entry and entry[field] not in ("", [], {}) for field in field_group):
                if len(field_group) == 1:
                    errors.append(f"{entry_id}: missing required `{field_group[0]}` field")
                else:
                    joined = "` or `".join(field_group)
                    errors.append(f"{entry_id}: missing required `{joined}` field")
    return errors


def build_id_index(resolved: dict[str, list[dict]]) -> tuple[dict[str, str], list[str]]:
    ids: dict[str, str] = {}
    errors: list[str] = []
    for section, entries in resolved.items():
        section_ids, section_errors = collect_ids(entries, section)
        errors.extend(section_errors)
        for entity_id in section_ids:
            if entity_id in ids:
                errors.append(f"duplicate id across sections: {entity_id}")
            else:
                ids[entity_id] = section
    return ids, errors


def normalize_targets(value: object) -> list[str]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    if isinstance(value, str):
        return [value]
    return []


def validate_links(kind: str, resolved: dict[str, list[dict]], id_index: dict[str, str], allow_placeholders: bool) -> list[str]:
    errors: list[str] = []
    for section, field_map in LINK_FIELDS[kind].items():
        for entry in resolved.get(section, []):
            entry_id = entry.get("id", f"{section}:<missing-id>")
            for field, target_section in field_map.items():
                for target in normalize_targets(entry.get(field)):
                    if target_section is None:
                        continue
                    if allow_placeholders and has_placeholder(target):
                        continue
                    if target not in id_index:
                        errors.append(f"{entry_id}: `{field}` target missing: {target}")
                        continue
                    if target_section is not None and id_index.get(target) != target_section:
                        errors.append(f"{entry_id}: `{field}` target must reference `{target_section}` ids: {target}")
    return errors


def validate_placeholders(doc: dict, allow_placeholders: bool) -> list[str]:
    if allow_placeholders:
        return []
    errors: list[str] = []
    for location in collect_placeholder_errors(doc):
        errors.append(f"placeholder value not allowed at {location}")
    return errors


def validate_paths(
    doc: dict,
    repo_root: pathlib.Path | None,
    check_exists: bool,
    allow_placeholders: bool,
) -> list[str]:
    errors: list[str] = []
    if not check_exists:
        return errors
    if repo_root is None:
        return ["--check-paths-exist requires --repo-root"]

    for section_name, section_value_obj in doc.items():
        if not isinstance(section_value_obj, list):
            continue
        for entry in section_value_obj:
            if not isinstance(entry, dict):
                continue
            entity_id = entry.get("id", f"{section_name}:<missing-id>")
            for field in PATH_FIELDS:
                raw_path = entry.get(field)
                if not isinstance(raw_path, str) or not raw_path:
                    continue
                if allow_placeholders and has_placeholder(raw_path):
                    continue
                candidate = pathlib.Path(raw_path)
                if not candidate.is_absolute():
                    candidate = repo_root / candidate
                if not candidate.exists():
                    errors.append(f"{entity_id}: path does not exist under repo root: {raw_path}")
    return errors


def detect_kind(doc: dict) -> str | None:
    meta = section_value(doc, "meta")
    if isinstance(meta, dict):
        for key in ("template_kind", "kind", "control_kind", "template"):
            normalized = normalize_kind(meta.get(key))
            if normalized is not None:
                return normalized

    section_names = set(doc.keys())
    if {"gates", "readiness_gates"}.intersection(section_names) and {"artifact_classes", "artifacts"}.intersection(section_names):
        return "readiness-gate"
    if {"claims", "assertions", "matrix", "rows", "evidence_matrix"}.intersection(section_names) and {"evidence", "artifacts", "evidence_artifacts"}.intersection(section_names):
        return "evidence-matrix"
    if {"contracts", "declarations", "contract_declarations"}.intersection(section_names):
        return "contract-declaration"
    return None


def main() -> int:
    args = parse_args()
    if not args.toml_file:
        print("error: toml_file is required", file=sys.stderr)
        return 2

    toml_path = pathlib.Path(args.toml_file).resolve()
    repo_root = pathlib.Path(args.repo_root).resolve() if args.repo_root else None

    try:
        doc = load_toml(toml_path)
    except FileNotFoundError:
        print(f"error: file not found: {toml_path}", file=sys.stderr)
        return 2
    except tomllib.TOMLDecodeError as exc:
        print(f"error: invalid TOML: {exc}", file=sys.stderr)
        return 2

    kind = args.kind if args.kind != "auto" else detect_kind(doc)
    if kind is None:
        print(
            "REVIEW READINESS VALIDATION FAILED",
        )
        print("- unable to detect template kind from TOML content")
        return 1

    resolved, errors = validate_required_sections(doc, kind)
    id_index, id_errors = build_id_index(resolved)
    errors.extend(id_errors)
    errors.extend(validate_entry_fields(kind, "artifact_classes", resolved.get("artifact_classes", [])))
    errors.extend(validate_entry_fields(kind, "gates", resolved.get("gates", [])))
    errors.extend(validate_entry_fields(kind, "contracts", resolved.get("contracts", [])))
    errors.extend(validate_entry_fields(kind, "claims", resolved.get("claims", [])))
    errors.extend(validate_entry_fields(kind, "evidence", resolved.get("evidence", [])))
    errors.extend(validate_entry_fields(kind, "matrix", resolved.get("matrix", [])))
    errors.extend(validate_links(kind, resolved, id_index, args.allow_placeholders))
    errors.extend(validate_placeholders(doc, args.allow_placeholders))
    errors.extend(validate_paths(doc, repo_root, args.check_paths_exist, args.allow_placeholders))

    if errors:
        print("REVIEW READINESS VALIDATION FAILED")
        print(f"- kind: {kind}")
        print(f"- file: {toml_path}")
        for error in errors:
            print(f"- {error}")
        return 1

    total_ids = len(id_index)
    total_entries = sum(len(entries) for entries in resolved.values())
    print("REVIEW READINESS VALIDATION PASSED")
    print(f"- kind: {kind}")
    print(f"- file: {toml_path}")
    print(f"- ids: {total_ids}")
    print(f"- entries: {total_entries}")
    if args.check_paths_exist:
        print(f"- repo_root: {repo_root}")
        print("- path existence checks: enabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
