#!/usr/bin/env python3
"""Compare declarations and artifact-bound executed receipts, without SQL inference."""

from __future__ import annotations

import argparse
import contextlib
import pathlib
import re
import sys

import _toml11 as tomllib
from _vocabulary import load_catalog

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "reference/database"))
from _contract import expected_counts, load_mapping


def derive_ontology_counts(repo_root: pathlib.Path) -> dict[str, int]:
    registry = expected_counts(repo_root)
    catalog = load_catalog(repo_root)
    return {
        "template_kinds": registry["kind_descriptor"],
        "entity_kinds": registry["entity_kind_descriptor"],
        "relation_predicates": registry["relation_descriptor"],
        "attribute_vocabularies": len(catalog),
        "attribute_values_declared": sum(len(item.values) for item in catalog.values()),
        "attribute_values_closed": sum(len(item.values) for item in catalog.values() if not item.extensible),
    }

def derive_rdf_counts(repo_root: pathlib.Path) -> dict[str, int | None]:
    """Return RDF triple counts via the dagtoml-rdf tool. Falls back to
    None if the tool isn't built; caller decides how to handle."""
    import subprocess

    rdf_bin = (
        repo_root
        / "tools"
        / "dagtoml-rdf"
        / "target"
        / "release"
        / "dagtoml-rdf"
    )
    schema = repo_root / "reference" / "database" / "rdf" / "schema.ttl"
    shapes = repo_root / "reference" / "database" / "rdf" / "shapes.ttl"
    out: dict[str, int | None] = {"schema": None, "shapes": None}
    if not rdf_bin.exists():
        return out
    for label, path in [("schema", schema), ("shapes", shapes)]:
        # Best-effort triple count: a missing/old binary or a timeout leaves
        # this label unset rather than failing the gate (py/empty-except).
        with contextlib.suppress(OSError, subprocess.TimeoutExpired):
            # Safe: fixed local binary path, list-args invocation, no
            # shell, no user-controlled input.
            res = subprocess.run(  # nosec B603  # noqa: S603
                [str(rdf_bin), "verify", "-o", str(path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            m = re.search(r"parsed\s+(\d+)\s+triples", res.stdout + res.stderr)
            if res.returncode == 0 and m:
                out[label] = int(m.group(1))
    return out

def parse_rust_expected_counts(repo_root: pathlib.Path) -> dict[str, int]:
    """Extract EXPECTED_COUNTS from tools/dagtoml-duckdb/src/main.rs."""
    p = repo_root / "tools" / "dagtoml-duckdb" / "src" / "main.rs"
    if not p.exists():
        return {}
    out = {}
    for m in re.finditer(r'\("([^"]+)"\s*,\s*(\d+)\)', p.read_text()):
        if m.group(1) in out:
            raise ValueError("duplicate loader count key: " + m.group(1))
        out[m.group(1)] = int(m.group(2))
    return out

def parse_go_expected_counts(repo_root: pathlib.Path) -> dict[str, int]:
    """Extract expectedCounts from tools/dagtoml-duckdb-go/main.go."""
    p = repo_root / "tools" / "dagtoml-duckdb-go" / "main.go"
    if not p.exists():
        return {}
    out = {}
    for m in re.finditer(r'\{"([^"]+)"\s*,\s*(\d+)\}', p.read_text()):
        if m.group(1) in out:
            raise ValueError("duplicate loader count key: " + m.group(1))
        out[m.group(1)] = int(m.group(2))
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=pathlib.Path, default=pathlib.Path("."))
    parser.add_argument("--declarations-only", action="store_true",
                        help="explicit partial check; database execution is covered by the required database gate")
    parser.add_argument("--receipts", type=pathlib.Path, nargs="*", default=[])
    parser.add_argument("--no-rdf", dest="rdf", action="store_false", help="explicitly skip RDF execution")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    failures = []
    compared = []

    def check(label, expected, actual):
        if expected is None or actual is None or expected != actual:
            failures.append(f"{label}: expected {expected!r}, observed {actual!r}")
        compared.append(label)

    try:
        load_mapping(root)
        ontology = derive_ontology_counts(root)
        registry = expected_counts(root)
        manifest = tomllib.loads((root / "reference/database/MANIFEST.toml").read_text())
        if "attribute_values" in manifest["counts"]:
            failures.append("retired ambiguous counts.attribute_values must not coexist with declared/closed counts")
        for name, value in ontology.items():
            check("ontology/manifest/" + name, value, manifest["counts"].get(name))
        verification = manifest["verification"]
        for engine in ("postgres", "sqlite", "duckdb"):
            if {"closed_enums", "closed_checks"} & manifest[engine].keys():
                raise ValueError("retired manifest constraint labels must use the storage mapping")
            prefix = "dagtoml_" if engine == "sqlite" else ""
            for name, value in registry.items():
                check(engine + "/declared/" + name, value,
                      verification[engine]["expected_seed_counts"].get(prefix + name))
        for name, actual in (("Rust", parse_rust_expected_counts(root)), ("Go", parse_go_expected_counts(root))):
            check(name + "/DuckDB-loader-declaration", {**registry, "reference_contract": 0, "runtime_document": 0}, actual)
        for name, key in (("KindDescriptor", "template_kinds"), ("EntityKind", "entity_kinds"),
                          ("RelationPredicate", "relation_predicates")):
            check("graph/" + name, ontology[key], verification["graph"]["expected_node_counts"].get(name))
        for name in ("template_kinds", "entity_kinds", "relation_predicates", "attribute_vocabularies"):
            check("rdf/footer/" + name, ontology[name], verification["rdf"]["expected_footer_counts"].get(name))
        footer = re.findall(r"^### Counts at generation: (\d+) template kinds, (\d+) entity kinds, (\d+) relation predicates, (\d+) attribute vocabularies\.$",
                            (root / "reference/database/rdf/schema.ttl").read_text(), re.MULTILINE)
        if len(footer) != 1:
            raise ValueError("RDF schema must contain exactly one generation-count footer")
        for name, value in zip(("template_kinds", "entity_kinds", "relation_predicates", "attribute_vocabularies"), footer[0], strict=True):
            check("rdf/executed-file-footer/" + name, ontology[name], int(value))
        if args.rdf:
            rdf = derive_rdf_counts(root)
            for name in ("schema", "shapes"):
                check("rdf/executed/" + name, verification["rdf"]["expected_triple_counts"].get(name), rdf[name])
        if not args.declarations_only:
            from _receipts import validate_receipts
            validate_receipts(root, args.receipts)
            compared.append("complete executed database and loader receipt matrix")
        elif args.receipts:
            raise ValueError("declarations-only must not be combined with executed receipts")
    except (ValueError, KeyError, OSError) as exc:
        failures.append(str(exc))
    skipped = (["database execution and loader binaries"] if args.declarations_only else []) + ([] if args.rdf else ["RDF execution"])
    print(f"Skipped: {skipped}; comparison: ontology declarations, manifest, loader declarations, "
          "and explicitly selected executed evidence")
    if failures:
        for failure in failures:
            print("FAIL: " + failure)
        return 1
    if not compared:
        raise AssertionError("count gate compared no surfaces")
    print(f"PASS: {len(compared)} asserted comparisons" + ("; partial declarations-only run" if args.declarations_only else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
