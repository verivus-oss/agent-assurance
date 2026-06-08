#!/usr/bin/env python3
"""Validate a `rollback-plan` instance file against the profile ontology.

Enforces:

- `[meta].template_kind == "rollback-plan"`.
- At least one `[[triggers]]` entry.
- Every `[[triggers]]` entry carries `id`, `trigger_kind`, `metric`,
  `threshold`, `action` (per `rollback-plan-kind.toml`).
- Every `[[triggers]].trigger_kind` value is in the profile
  ontology's `trigger_kind` `attribute_vocabularies` value set
  (or matches the legacy `kind` alias).

The trigger-kind enum is the closure rule from the hard invariant
at `profiles/agent-assurance/rollback-plan-kind.toml`:

  > Every `[[triggers]].trigger_kind` value is drawn from the
  > profile ontology's allowed set (or the explicit `kind` alias).

That rule is not enforced by `validate_ijb_conformance.py` because
its instance-file rules only inspect ID-shaped strings and
declared predicate values. This validator closes that gap.

Usage:
    python3 validators/validate_rollback_plan.py <file.toml> [--ontology PATH]
"""

from __future__ import annotations

import argparse
import pathlib
import sys
import _toml11 as tomllib  # TOML 1.1 reference shim (stdlib tomllib is 1.0-only); see validators/_toml11.py


DEFAULT_ONTOLOGY = "profiles/agent-assurance/ontology.toml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("file", help="rollback-plan TOML to validate.")
    parser.add_argument(
        "--ontology",
        default=DEFAULT_ONTOLOGY,
        help="Path to the profile ontology TOML (default: profiles/agent-assurance/ontology.toml).",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root used to resolve --ontology when relative.",
    )
    return parser.parse_args()


def load_toml(path: pathlib.Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def trigger_kind_values(ontology_doc: dict) -> set[str]:
    for vocab in ontology_doc.get("attribute_vocabularies", []):
        if vocab.get("attribute") == "trigger_kind":
            values = vocab.get("values", [])
            if isinstance(values, list):
                return {str(v) for v in values}
    return set()


def validate(plan_doc: dict, allowed_values: set[str]) -> list[str]:
    errors: list[str] = []
    meta = plan_doc.get("meta", {})
    if meta.get("template_kind") != "rollback-plan":
        errors.append(
            f"[meta].template_kind is {meta.get('template_kind')!r}; expected 'rollback-plan'."
        )

    triggers = plan_doc.get("triggers", [])
    if not isinstance(triggers, list) or not triggers:
        errors.append("at least one [[triggers]] entry is required.")
        return errors

    required_fields = ("id", "metric", "threshold", "action")
    for index, trig in enumerate(triggers):
        prefix = f"[[triggers]] #{index}"
        if not isinstance(trig, dict):
            errors.append(f"{prefix}: must be a table.")
            continue

        trig_id = trig.get("id", "<unset>")
        kind_value = trig.get("trigger_kind") or trig.get("kind")
        if not isinstance(kind_value, str) or not kind_value.strip():
            errors.append(f"{prefix} (id={trig_id!r}): missing trigger_kind/kind.")
        elif kind_value not in allowed_values:
            errors.append(
                f"{prefix} (id={trig_id!r}): trigger_kind={kind_value!r} not in profile "
                f"ontology vocabulary; allowed values: "
                f"{sorted(allowed_values)}."
            )

        for field in required_fields:
            if field not in trig:
                errors.append(f"{prefix} (id={trig_id!r}): missing required field '{field}'.")

    return errors


def main() -> int:
    args = parse_args()
    plan_path = pathlib.Path(args.file).resolve()
    repo_root = pathlib.Path(args.repo_root).resolve()
    ontology_path = pathlib.Path(args.ontology)
    if not ontology_path.is_absolute():
        ontology_path = (repo_root / ontology_path).resolve()

    try:
        plan_doc = load_toml(plan_path)
    except FileNotFoundError:
        print(f"error: file not found: {plan_path}", file=sys.stderr)
        return 2
    except tomllib.TOMLDecodeError as exc:
        print(f"error: invalid TOML: {exc}", file=sys.stderr)
        return 2

    try:
        ontology_doc = load_toml(ontology_path)
    except FileNotFoundError:
        print(f"error: ontology not found: {ontology_path}", file=sys.stderr)
        return 2

    allowed = trigger_kind_values(ontology_doc)
    if not allowed:
        print(
            f"error: ontology at {ontology_path} declares no trigger_kind values",
            file=sys.stderr,
        )
        return 2

    errors = validate(plan_doc, allowed)
    if errors:
        print("ROLLBACK PLAN VALIDATION FAILED")
        print(f"- file: {plan_path}")
        print(f"- ontology: {ontology_path}")
        print(f"- trigger_kind vocabulary size: {len(allowed)}")
        for err in errors:
            print(f"- ERROR: {err}")
        return 1

    print("ROLLBACK PLAN VALIDATION PASSED")
    print(f"- file: {plan_path}")
    print(f"- triggers: {len(plan_doc.get('triggers', []))}")
    print(f"- trigger_kind vocabulary size: {len(allowed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
