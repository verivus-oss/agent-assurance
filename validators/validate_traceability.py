#!/usr/bin/env python3
"""Validate traceability TOML files used in this repository."""

from __future__ import annotations

import argparse
import pathlib
import sys
import tomllib
from collections import defaultdict


SECTIONS = [
    "intents",
    "features",
    "requirements",
    "regulations",
    "decisions",
    "implementations",
    "code",
    "tests",
    "outputs",
]

LINK_FIELDS = {
    "intents": ["derived_from", "realized_by"],
    "features": ["realizes", "constrained_by", "implemented_by", "produces"],
    "requirements": ["constrains", "verified_by"],
    "regulations": ["constrains", "verified_by"],
    "decisions": ["addresses", "shapes", "supersedes"],
    "implementations": ["implements", "guided_by", "code", "tests", "downstream_outputs"],
    "code": ["realizes"],
    "tests": ["verifies"],
    "outputs": ["realizes"],
}

DOWNSTREAM_FIELDS = {
    "intents": ["realized_by"],
    "features": ["implemented_by", "produces"],
    "requirements": ["verified_by", "constrains"],
    "regulations": ["verified_by", "constrains"],
    "decisions": ["shapes"],
    "implementations": ["code", "tests", "downstream_outputs"],
    "code": ["realizes"],
    "tests": ["verifies"],
    "outputs": ["realizes"],
}

PLACEHOLDER_MARKERS = ("<", ">", "YYYY-MM-DD")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a traceability TOML file.")
    parser.add_argument("traceability_file", help="Path to the TOML file to validate.")
    parser.add_argument(
        "--repo-root",
        help="Repository root used for optional CODE/TEST path existence checks.",
    )
    parser.add_argument(
        "--check-paths-exist",
        action="store_true",
        help="Verify CODE and TEST paths exist relative to --repo-root.",
    )
    parser.add_argument(
        "--allow-placeholders",
        action="store_true",
        help="Allow placeholder strings like <component> in ids and paths.",
    )
    return parser.parse_args()


def load_toml(path: pathlib.Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def gather_entities(doc: dict) -> tuple[dict[str, dict], list[str]]:
    entities: dict[str, dict] = {}
    errors: list[str] = []
    for section in SECTIONS:
        for entry in doc.get(section, []):
            entity_id = entry.get("id")
            if not entity_id:
                errors.append(f"{section}: missing required `id` field")
                continue
            if entity_id in entities:
                errors.append(f"duplicate id: {entity_id}")
                continue
            entities[entity_id] = {"section": section, "entry": entry}
    return entities, errors


def has_placeholder(value: str) -> bool:
    return any(marker in value for marker in PLACEHOLDER_MARKERS)


def validate_links(doc: dict, entities: dict[str, dict]) -> list[str]:
    errors: list[str] = []
    for section, fields in LINK_FIELDS.items():
        for entry in doc.get(section, []):
            entity_id = entry.get("id", f"{section}:<missing-id>")
            for field in fields:
                for target in entry.get(field, []):
                    if target not in entities:
                        errors.append(f"{entity_id}: `{field}` target missing: {target}")
    for relation in doc.get("relations", []):
        source = relation.get("from")
        target = relation.get("to")
        relation_type = relation.get("type", "<missing-type>")
        if source not in entities:
            errors.append(f"relation `{relation_type}` missing `from` target: {source}")
        if target not in entities:
            errors.append(f"relation `{relation_type}` missing `to` target: {target}")
    return errors


def build_forward_graph(doc: dict) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = defaultdict(set)
    for section, fields in DOWNSTREAM_FIELDS.items():
        for entry in doc.get(section, []):
            source = entry.get("id")
            if not source:
                continue
            for field in fields:
                for target in entry.get(field, []):
                    graph[source].add(target)
    return graph


def reachable(graph: dict[str, set[str]], start: str, target_prefixes: tuple[str, ...]) -> bool:
    stack = [start]
    seen: set[str] = set()
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        if current != start and current.startswith(target_prefixes):
            return True
        stack.extend(graph.get(current, ()))
    return False


def detect_cycles(doc: dict) -> list[str]:
    errors: list[str] = []
    for section, field in (("intents", "derived_from"), ("decisions", "supersedes")):
        graph: dict[str, set[str]] = defaultdict(set)
        for entry in doc.get(section, []):
            source = entry.get("id")
            if not source:
                continue
            for target in entry.get(field, []):
                graph[source].add(target)

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> bool:
            if node in visited:
                return False
            if node in visiting:
                return True
            visiting.add(node)
            for nxt in graph.get(node, ()):
                if visit(nxt):
                    return True
            visiting.remove(node)
            visited.add(node)
            return False

        for node in list(graph):
            if visit(node):
                errors.append(f"{section}: `{field}` contains a cycle involving {node}")
                break
    return errors


def validate_paths(
    doc: dict,
    repo_root: pathlib.Path | None,
    check_exists: bool,
    allow_placeholders: bool,
) -> list[str]:
    errors: list[str] = []
    for section in ("code", "tests"):
        for entry in doc.get(section, []):
            entity_id = entry.get("id", f"{section}:<missing-id>")
            raw_path = entry.get("path", "")
            if not raw_path:
                errors.append(f"{entity_id}: missing `path`")
                continue
            if not allow_placeholders and has_placeholder(raw_path):
                errors.append(f"{entity_id}: placeholder path not allowed: {raw_path}")
            if check_exists:
                if repo_root is None:
                    errors.append("--check-paths-exist requires --repo-root")
                    continue
                if not (repo_root / raw_path).exists():
                    errors.append(f"{entity_id}: path does not exist under repo root: {raw_path}")
    return errors


def validate_placeholders(doc: dict, allow_placeholders: bool) -> list[str]:
    if allow_placeholders:
        return []
    errors: list[str] = []
    for section in SECTIONS:
        for entry in doc.get(section, []):
            entity_id = entry.get("id")
            if entity_id and has_placeholder(entity_id):
                errors.append(f"{section}: placeholder id not allowed: {entity_id}")
    return errors


def validate_downstream_realization(doc: dict) -> list[str]:
    errors: list[str] = []
    graph = build_forward_graph(doc)
    for section in ("requirements", "regulations"):
        for entry in doc.get(section, []):
            entity_id = entry.get("id")
            if not entity_id:
                continue
            if not reachable(graph, entity_id, ("CODE:", "TEST:", "OUT:", "IMP:")):
                errors.append(
                    f"{entity_id}: no downstream realization path to implementation, code, tests, or outputs"
                )
    return errors


def validate_computed(doc: dict, entities: dict[str, dict]) -> list[str]:
    errors: list[str] = []
    computed = doc.get("computed", {})
    for field in ("root_intents", "terminal_outputs", "unverified_requirements", "unmapped_code", "coverage_gaps"):
        for target in computed.get(field, []):
            if target and field not in ("coverage_gaps",) and target not in entities:
                errors.append(f"computed `{field}` target missing: {target}")
    return errors


def main() -> int:
    args = parse_args()
    traceability_path = pathlib.Path(args.traceability_file).resolve()
    repo_root = pathlib.Path(args.repo_root).resolve() if args.repo_root else None

    try:
        doc = load_toml(traceability_path)
    except FileNotFoundError:
        print(f"error: file not found: {traceability_path}", file=sys.stderr)
        return 2
    except tomllib.TOMLDecodeError as exc:
        print(f"error: invalid TOML: {exc}", file=sys.stderr)
        return 2

    entities, errors = gather_entities(doc)
    errors.extend(validate_placeholders(doc, args.allow_placeholders))
    errors.extend(validate_links(doc, entities))
    errors.extend(detect_cycles(doc))
    errors.extend(validate_downstream_realization(doc))
    errors.extend(validate_paths(doc, repo_root, args.check_paths_exist, args.allow_placeholders))
    errors.extend(validate_computed(doc, entities))

    if errors:
        print("TRACEABILITY VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("TRACEABILITY VALIDATION PASSED")
    print(f"- file: {traceability_path}")
    print(f"- entities: {len(entities)}")
    if args.check_paths_exist:
        print(f"- repo_root: {repo_root}")
        print("- path existence checks: enabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
