#!/usr/bin/env python3
"""Validate a DAG-TOML kind-descriptor file.

A kind-descriptor is a TOML file whose `[meta].template_kind` is
`"kind-descriptor"`. It carries the prose explanation, required-field
declarations, hard-invariant pointers, and worked-example pointers for
exactly one other `template_kind`.

The kind-descriptor itself is a `template_kind`. The recursion stops at
the prose definition in spec.md §2.4 plus this validator; no
`kind-descriptor-kind.toml` is shipped or required.
"""

from __future__ import annotations

import argparse
import pathlib
import sys
import _toml11 as tomllib  # TOML 1.1 reference shim (stdlib tomllib is 1.0-only); see validators/_toml11.py


REQUIRED_META_FIELDS = ("schema_version", "template_kind", "describes_kind", "title")
REQUIRED_KIND_FIELDS = ("name", "summary", "prose")
PLACEHOLDER_MARKERS = ("<", ">", "YYYY-MM-DD")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a DAG-TOML kind-descriptor file.",
    )
    parser.add_argument("descriptor_file", help="Path to the descriptor TOML.")
    parser.add_argument(
        "--repo-root",
        help="Repository root for optional referenced-file existence checks.",
    )
    parser.add_argument(
        "--check-references-exist",
        action="store_true",
        help="Verify referenced example/validator/ontology paths exist under --repo-root.",
    )
    parser.add_argument(
        "--allow-placeholders",
        action="store_true",
        help="Allow placeholder strings like <feature> in fields.",
    )
    return parser.parse_args()


def has_placeholder(value: str) -> bool:
    return any(marker in value for marker in PLACEHOLDER_MARKERS)


def validate(doc: dict, *, allow_placeholders: bool) -> list[str]:
    errors: list[str] = []
    meta = doc.get("meta")
    if not isinstance(meta, dict):
        errors.append("missing required `[meta]` table")
        return errors

    for field in REQUIRED_META_FIELDS:
        if field not in meta:
            errors.append(f"meta: missing required field `{field}`")

    if meta.get("template_kind") != "kind-descriptor":
        errors.append(
            f"meta.template_kind: expected `\"kind-descriptor\"`, got "
            f"`{meta.get('template_kind')!r}`"
        )

    describes_kind = meta.get("describes_kind")
    if describes_kind is not None and not isinstance(describes_kind, str):
        errors.append("meta.describes_kind: must be a string")

    kind = doc.get("kind")
    if not isinstance(kind, dict):
        errors.append("missing required `[kind]` table")
        return errors

    for field in REQUIRED_KIND_FIELDS:
        if field not in kind:
            errors.append(f"kind: missing required field `{field}`")

    name = kind.get("name")
    if isinstance(name, str) and isinstance(describes_kind, str) and name != describes_kind:
        errors.append(
            f"kind.name `{name}` does not match meta.describes_kind "
            f"`{describes_kind}`"
        )

    summary = kind.get("summary")
    if isinstance(summary, str) and len(summary.strip()) < 10:
        errors.append("kind.summary: must be at least 10 characters")

    prose = kind.get("prose")
    if isinstance(prose, str) and len(prose.strip()) < 50:
        errors.append("kind.prose: must be at least 50 characters")

    if not allow_placeholders:
        for path, value in iter_strings(doc):
            if _is_prose_field(path):
                continue
            if has_placeholder(value):
                errors.append(f"{path}: placeholder value not allowed")

    return errors


def _is_prose_field(path: str) -> bool:
    """Return True for fields whose content is intentionally illustrative
    prose. Placeholder syntax (`<x>`, `YYYY-MM-DD`) is expected inside
    code-block examples in these fields and is not a validation error."""
    return path in {"kind.prose", "kind.summary"} or path.endswith(".inline") or path.endswith(".inline_summary") or path.endswith(".description") or path.endswith(".statement") or path.endswith(".notes") or path.endswith(".note")


def iter_strings(node: object, prefix: str = "") -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if isinstance(node, dict):
        for k, v in node.items():
            sub = f"{prefix}.{k}" if prefix else str(k)
            out.extend(iter_strings(v, sub))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out.extend(iter_strings(v, f"{prefix}[{i}]"))
    elif isinstance(node, str):
        out.append((prefix or "<root>", node))
    return out


def check_references(
    doc: dict, repo_root: pathlib.Path, allow_placeholders: bool
) -> list[str]:
    errors: list[str] = []
    kind = doc.get("kind", {})

    for entry in kind.get("example", []):
        if not isinstance(entry, dict):
            continue
        path = entry.get("file")
        if not isinstance(path, str) or not path:
            continue
        if not allow_placeholders and has_placeholder(path):
            errors.append(f"kind.example.file: placeholder path not allowed: {path}")
            continue
        if not (repo_root / path).exists():
            errors.append(
                f"kind.example.file: path does not exist under repo root: {path}"
            )

    for entry in kind.get("hard_invariants", []):
        if not isinstance(entry, dict):
            continue
        enforced_by = entry.get("enforced_by")
        if not isinstance(enforced_by, str) or not enforced_by:
            continue
        # Skip explicit "planned" or "TBD" markers; the field is allowed to
        # describe enforcement that does not yet ship as a validator.
        lowered = enforced_by.lower()
        if "(planned)" in lowered or "(tbd)" in lowered or "prose review" in lowered:
            continue
        # Only treat as a path if the string looks like a bare file reference
        # (ends with .py or .toml or .json, with no spaces or parentheses).
        if (
            ("/" in enforced_by or enforced_by.endswith((".py", ".toml", ".json")))
            and " " not in enforced_by
            and "(" not in enforced_by
        ):
            if not (repo_root / enforced_by).exists():
                errors.append(
                    f"kind.hard_invariants.enforced_by: path does not exist "
                    f"under repo root: {enforced_by}"
                )

    for ref in kind.get("references", []):
        if not isinstance(ref, str):
            continue
        bare = ref.split("#", 1)[0].strip()
        if not bare:
            continue
        if has_placeholder(bare) and not allow_placeholders:
            continue
        if not (repo_root / bare).exists():
            errors.append(
                f"kind.references: path does not exist under repo root: {bare}"
            )

    return errors


def main() -> int:
    args = parse_args()
    path = pathlib.Path(args.descriptor_file).resolve()
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    with path.open("rb") as handle:
        try:
            doc = tomllib.load(handle)
        except tomllib.TOMLDecodeError as exc:
            print(f"error: TOML parse failure: {exc}", file=sys.stderr)
            return 2

    errors = validate(doc, allow_placeholders=args.allow_placeholders)

    if args.check_references_exist:
        if not args.repo_root:
            errors.append("--check-references-exist requires --repo-root")
        else:
            repo_root = pathlib.Path(args.repo_root).resolve()
            errors.extend(
                check_references(doc, repo_root, args.allow_placeholders)
            )

    if errors:
        print("KIND DESCRIPTOR VALIDATION FAILED")
        print(f"- file: {path}")
        for err in errors:
            print(f"- {err}")
        return 1

    kind = doc.get("kind", {})
    print("KIND DESCRIPTOR VALIDATION PASSED")
    print(f"- file: {path}")
    print(f"- describes_kind: {doc['meta'].get('describes_kind')}")
    print(f"- example_count: {len(kind.get('example', []))}")
    print(f"- invariant_count: {len(kind.get('hard_invariants', []))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
