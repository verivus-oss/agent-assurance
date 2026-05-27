#!/usr/bin/env python3
"""Validate `cost-record` instance documents (cost profile).

Enforces the hard invariants declared by
`profiles/cost/cost-record-kind.toml`:

  INV01 — `[record].decider_class` is in the closed `decider_class`
          vocabulary.
  INV02 — `[record].citing_kind` is in the closed `cost_citing_kind`
          vocabulary.
  INV03 — every `[[record.dimensions]].category` is in the closed
          `cost_dimension_category` vocabulary.
  INV04 — every `[[record.dimensions]].quantity` is a non-negative
          integer (no floats per canonical-form determinism).
  INV05 — `[record].incurred_at` parses as RFC 3339 `date-time`.
  INV06 — `[record].hash_algorithm` is `sha256` / `sha384` / `sha512`
          or a stronger label; weak digests (`md5`, `sha1`) are
          forbidden per SPEC §12.1.

Closure-root presence is enforced separately by
`validators/validate_closure_root.py`; this validator does not
duplicate that check.

Exit 0 on pass; 1 on any violation.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import pathlib
import re
import sys
import tomllib

REQUIRED_RECORD_FIELDS: tuple[str, ...] = (
    "action_id",
    "incurred_at",
    "citing_kind",
    "citing_ref",
    "decider_class",
    "producer_id",
    "hash_algorithm",
    "canonical_form",
)

FORBIDDEN_HASH_ALGOS = frozenset({"md5", "sha1"})

RFC3339_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


def _load_vocabularies(repo_root: pathlib.Path) -> dict[str, set[str]]:
    """Load the cost profile's closed vocabularies from its ontology.

    Returns a dict mapping vocabulary name → allowed value set.
    Missing vocabularies (e.g. ontology file moved) raise; the kind
    descriptor declares enforcement against these names, so absence
    is a deployment bug, not a soft fall-through.
    """
    ont = repo_root / "profiles" / "cost" / "ontology.toml"
    data = tomllib.loads(ont.read_text())
    want = {"decider_class", "cost_citing_kind", "cost_dimension_category"}
    found: dict[str, set[str]] = {}
    for entry in data.get("attribute_vocabularies", []):
        name = entry.get("attribute")
        if name in want:
            values = entry.get("values", [])
            found[name] = {str(v) for v in values}
    missing = want - set(found)
    if missing:
        raise SystemExit(
            f"cost-profile ontology is missing required vocabularies: "
            f"{sorted(missing)} (looked in {ont})"
        )
    return found


def _check_rfc3339(value: str) -> bool:
    if not isinstance(value, str) or not RFC3339_RE.match(value):
        return False
    try:
        # datetime.fromisoformat accepts the RFC 3339 forms (Z normalised below).
        _dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def validate(path: pathlib.Path, vocab: dict[str, set[str]]) -> list[str]:
    errors: list[str] = []
    try:
        data = tomllib.loads(path.read_text())
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return [f"{path}: cannot parse TOML ({exc})"]

    meta = data.get("meta")
    if not isinstance(meta, dict) or meta.get("template_kind") != "cost-record":
        return [
            f"{path}: not a cost-record instance "
            f"(meta.template_kind != 'cost-record')"
        ]
    if meta.get("framework_profile") != "cost":
        errors.append(
            f"{path}: meta.framework_profile must be 'cost', "
            f"got {meta.get('framework_profile')!r}"
        )

    record = data.get("record")
    if not isinstance(record, dict):
        return errors + [f"{path}: missing required `[record]` table"]

    for field in REQUIRED_RECORD_FIELDS:
        v = record.get(field)
        if not isinstance(v, str) or not v:
            errors.append(
                f"{path}: record.{field} must be a non-empty string, "
                f"got {type(v).__name__}: {v!r}"
            )

    # INV05 — RFC 3339 timestamp shape.
    iat = record.get("incurred_at")
    if isinstance(iat, str) and not _check_rfc3339(iat):
        errors.append(
            f"{path}: record.incurred_at must be RFC 3339 date-time, "
            f"got {iat!r}"
        )

    # INV02 — citing_kind in closed vocab.
    ck = record.get("citing_kind")
    if isinstance(ck, str) and ck not in vocab["cost_citing_kind"]:
        errors.append(
            f"{path}: record.citing_kind {ck!r} not in closed vocabulary "
            f"cost_citing_kind={sorted(vocab['cost_citing_kind'])}"
        )

    # INV01 — decider_class in closed vocab.
    dc = record.get("decider_class")
    if isinstance(dc, str) and dc not in vocab["decider_class"]:
        errors.append(
            f"{path}: record.decider_class {dc!r} not in closed vocabulary "
            f"decider_class={sorted(vocab['decider_class'])}"
        )

    # INV06 — hash_algorithm allowed shape (lowercase, not weak).
    ha = record.get("hash_algorithm")
    if isinstance(ha, str):
        ha_l = ha.lower()
        if ha_l in FORBIDDEN_HASH_ALGOS:
            errors.append(
                f"{path}: record.hash_algorithm {ha!r} is forbidden by "
                f"SPEC §12.1 (no MD5 or SHA-1); use SHA-256 or stronger."
            )

    # Dimensions array (INV03 + INV04 + structural).
    dims = record.get("dimensions")
    if not isinstance(dims, list) or not dims:
        errors.append(
            f"{path}: at least one `[[record.dimensions]]` entry is required"
        )
    else:
        for i, dim in enumerate(dims):
            if not isinstance(dim, dict):
                errors.append(
                    f"{path}: record.dimensions[{i}] must be a table"
                )
                continue
            cat = dim.get("category")
            if cat not in vocab["cost_dimension_category"]:
                errors.append(
                    f"{path}: record.dimensions[{i}].category {cat!r} "
                    f"not in closed vocabulary "
                    f"cost_dimension_category={sorted(vocab['cost_dimension_category'])}"
                )
            q = dim.get("quantity")
            # INV04 — non-negative integer; floats forbidden.
            if isinstance(q, bool) or not isinstance(q, int) or q < 0:
                errors.append(
                    f"{path}: record.dimensions[{i}].quantity must be a "
                    f"non-negative integer (no floats per canonical-form "
                    f"determinism); got {type(q).__name__} {q!r}"
                )
            ul = dim.get("unit_label")
            if not isinstance(ul, str) or not ul:
                errors.append(
                    f"{path}: record.dimensions[{i}].unit_label must be "
                    f"a non-empty producer-attested string; got "
                    f"{type(ul).__name__} {ul!r}"
                )

    return errors


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Validate cost-record instance documents (cost profile).",
    )
    parser.add_argument("paths", nargs="+", help="TOML cost-record file(s) to validate.")
    parser.add_argument(
        "--repo-root",
        default=".",
        help=(
            "Repository root containing `profiles/cost/ontology.toml` "
            "(used to load the closed vocabularies). Defaults to the "
            "current working directory."
        ),
    )
    args = parser.parse_args(argv)

    repo_root = pathlib.Path(args.repo_root).resolve()
    vocab = _load_vocabularies(repo_root)

    failures: list[str] = []
    checked = 0
    for raw in args.paths:
        path = pathlib.Path(raw)
        if not path.exists():
            failures.append(f"{path}: does not exist")
            continue
        checked += 1
        failures.extend(validate(path, vocab))

    if failures:
        for f in failures:
            print(f"FAIL {f}", file=sys.stderr)
        print(
            f"\nCOST-RECORD VALIDATION FAILED: {len(failures)} "
            f"error(s) across {checked} file(s).",
            file=sys.stderr,
        )
        return 1

    print(f"COST-RECORD VALIDATION PASSED ({checked} file(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
