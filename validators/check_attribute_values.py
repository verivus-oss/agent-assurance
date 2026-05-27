#!/usr/bin/env python3
"""Comprehensive count-mirror drift gate.

Recomputes every count surface in the repository from its real
source and compares against the declared values in
`reference/database/MANIFEST.toml`, the hardcoded EXPECTED_COUNTS
arrays in the dagtoml-duckdb tools, and (informationally) the
seed.sql header comments. Exits non-zero on any drift.

Count surfaces gated (per the Opus consultant's broadened
evidence + codex's critique that defers nothing):

  1. `[counts]` — ontology block counts + attribute_values_{declared,closed}
  2. `expected_seed_counts` × 3 engines (postgres / duckdb / sqlite)
  3. `expected_node_counts` (graph)
  4. `expected_triple_counts` (rdf)
  5. `expected_footer_counts` (rdf — already auto-generated)
  6. `tools/dagtoml-duckdb/src/main.rs:22-26` (Rust hardcode)
  7. `tools/dagtoml-duckdb-go/main.go:40-44` (Go hardcode)

The script does NOT regenerate the seed files; if a seed row
count differs from its expected value, the script reports the
drift. The fix is either to regenerate the seed from the
ontology or update the expected value to match the seed — both
are conscious maintainer actions, not automated.

This validator is independent of `check_manifest_drift.sh`
(which gates a narrower four-field surface) — the bash script
invokes this Python script as an additional step so the two
work together without overlap.

Exit 0 on full agreement; 1 on any drift.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
import tomllib


# ---------- ontology truth ---------------------------------------------------

def derive_ontology_counts(repo_root: pathlib.Path) -> dict[str, int]:
    """Return ontology-derived counts: template_kinds, entity_kinds,
    relation_predicates, attribute_vocabularies, attribute_values_declared,
    attribute_values_closed.
    """
    ontology_paths = [repo_root / "core" / "ontology.toml"]
    profiles_dir = repo_root / "profiles"
    if profiles_dir.exists():
        ontology_paths.extend(sorted(profiles_dir.glob("*/ontology.toml")))

    kind_files = list((repo_root / "core").glob("*-kind.toml"))
    if profiles_dir.exists():
        kind_files.extend(profiles_dir.glob("*/*-kind.toml"))

    entities = relations = vocabs = values_declared = values_closed = 0
    for p in ontology_paths:
        d = tomllib.loads(p.read_text())
        entities += len(d.get("entities", []))
        relations += len(d.get("relations", []))
        for v in d.get("attribute_vocabularies", []):
            vocabs += 1
            n = len(v.get("values", []))
            values_declared += n
            if not v.get("extensible", False):
                values_closed += n

    return {
        # template_kinds = N descriptor files + 1 for the meta `kind-descriptor`
        # itself, which is described in spec.md and not by a separate descriptor.
        "template_kinds": len(kind_files) + 1,
        "entity_kinds": entities,
        "relation_predicates": relations,
        "attribute_vocabularies": vocabs,
        "attribute_values_declared": values_declared,
        "attribute_values_closed": values_closed,
    }


# ---------- seed-file truth --------------------------------------------------

def _count_tuple_rows(seed_path: pathlib.Path, table_re_str: str) -> int | None:
    """Count tuple rows inside the named INSERT INTO block.

    Reliable line-based counter: a tuple row in our SQL seeds always
    begins (modulo whitespace) with `(` followed by a quoted column
    value. This avoids both the ARRAY[...] paren-balance trap and the
    apostrophe-inside-string trap.
    """
    if not seed_path.exists():
        return None
    txt = seed_path.read_text()
    m = re.search(
        rf"INSERT INTO {table_re_str}\b.*?\bVALUES",
        txt,
        re.DOTALL,
    )
    if not m:
        return None
    rest = txt[m.end():]
    # Stop at the next top-level statement so we only count this block's tuples.
    end_match = re.search(
        r"\n\s*(?:INSERT INTO|ALTER|CREATE|DROP|COMMIT|--\s*=====)", rest
    )
    if end_match:
        rest = rest[: end_match.start()]
    count = 0
    for line in rest.split("\n"):
        s = line.lstrip()
        if s.startswith("(") and "'" in s:
            count += 1
    return count


def derive_seed_counts(repo_root: pathlib.Path, engine: str) -> dict[str, int]:
    """Return per-engine seed-row counts under
    `reference/database/<engine>/seed.sql`."""
    db_dir = repo_root / "reference" / "database" / engine
    seed = db_dir / "seed.sql"
    prefix = "dagtoml_" if engine == "sqlite" else "(?:dagtoml\\.)?"
    tables = [
        "kind_descriptor",
        "entity_kind_descriptor",
        "relation_descriptor",
        "attribute_vocabulary",
        "attribute_value_allowed",
    ]
    out: dict[str, int] = {}
    for t in tables:
        # Sqlite prefixes its tables with `dagtoml_`; postgres has no schema
        # qualifier; duckdb uses `dagtoml.` prefix.
        full_table = f"{prefix}{t}"
        out[t] = _count_tuple_rows(seed, full_table) or 0
    return out


# ---------- RDF triple truth -------------------------------------------------

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
        try:
            # Safe: fixed local binary path, list-args invocation, no
            # shell, no user-controlled input.
            res = subprocess.run(  # nosec B603  # noqa: S603
                [str(rdf_bin), "verify", "-o", str(path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            m = re.search(r"parsed\s+(\d+)\s+triples", res.stdout + res.stderr)
            if m:
                out[label] = int(m.group(1))
        except (OSError, subprocess.TimeoutExpired):
            pass
    return out


# ---------- hardcoded-mirror truth -------------------------------------------

def parse_rust_expected_counts(repo_root: pathlib.Path) -> dict[str, int]:
    """Extract EXPECTED_COUNTS from tools/dagtoml-duckdb/src/main.rs."""
    p = repo_root / "tools" / "dagtoml-duckdb" / "src" / "main.rs"
    if not p.exists():
        return {}
    out = {}
    for m in re.finditer(r'\("([^"]+)"\s*,\s*(\d+)\)', p.read_text()):
        out[m.group(1)] = int(m.group(2))
    return out


def parse_go_expected_counts(repo_root: pathlib.Path) -> dict[str, int]:
    """Extract expectedCounts from tools/dagtoml-duckdb-go/main.go."""
    p = repo_root / "tools" / "dagtoml-duckdb-go" / "main.go"
    if not p.exists():
        return {}
    out = {}
    for m in re.finditer(r'\{"([^"]+)"\s*,\s*(\d+)\}', p.read_text()):
        out[m.group(1)] = int(m.group(2))
    return out


# ---------- manifest counts --------------------------------------------------

def manifest_data(repo_root: pathlib.Path) -> dict:
    return tomllib.loads(
        (repo_root / "reference" / "database" / "MANIFEST.toml").read_text()
    )


# ---------- reporting --------------------------------------------------------

class DriftReport:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.summary: list[str] = []

    def check(self, label: str, expected: int | None, actual: int | None) -> None:
        if expected is None and actual is None:
            self.summary.append(f"  {label:60s}   (skipped — both unknown)")
            return
        op = "==" if expected == actual else "!="
        tag = "" if expected == actual else "   <-- DRIFT"
        self.summary.append(
            f"  {label:60s} {str(expected):>6} {op} {str(actual):>6}{tag}"
        )
        if expected != actual:
            self.failures.append(f"{label}: declared {expected}, actual {actual}")

    def print(self) -> int:
        for line in self.summary:
            print(line)
        if self.failures:
            # Emit every failure diagnostic verbatim before the summary
            # count — otherwise the operator sees only a phantom "DRIFT: N"
            # with no named reason. This is the mirror-rot pattern the
            # module exists to prevent (per ISS-001).
            print()
            print("FAILURES (each is one surface out of sync):")
            for i, msg in enumerate(self.failures, 1):
                # Indent multi-line messages for readability.
                lines = msg.splitlines() or [""]
                print(f"  {i}. {lines[0]}")
                for cont in lines[1:]:
                    print(f"     {cont}")
            print()
            print(f"COUNT-MIRROR DRIFT: {len(self.failures)} surface(s) out of sync.")
            return 1
        print()
        print("COUNT-MIRROR OK — every surface agrees with reality.")
        return 0


# ---------- main -------------------------------------------------------------

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Comprehensive count-mirror drift gate. Compares every "
            "count surface in the repo (MANIFEST.toml, tools/dagtoml-* "
            "hardcodes, seed.sql row counts, RDF triple counts) against "
            "their authoritative sources (ontology TOML, seed SQL, "
            "RDF tool output) and fails CI on any divergence."
        )
    )
    parser.add_argument(
        "--repo-root", type=pathlib.Path, default=pathlib.Path("."),
        help="Repository root (defaults to current directory).",
    )
    parser.add_argument(
        "--no-rdf", dest="rdf", action="store_false",
        help=(
            "Skip the RDF triple-count probe. By default the gate WILL "
            "verify `[verification.rdf].expected_triple_counts` against "
            "the actual RDF triple count from `dagtoml-rdf verify`. "
            "Passing --no-rdf is only sensible when the tool isn't "
            "built; missing-binary is handled gracefully even without "
            "this flag (the gate fails-soft with an explicit note)."
        ),
    )
    parser.set_defaults(rdf=True)
    parser.add_argument(
        "--quiet", action="store_true",
        help="Print only the per-surface drift summary header on success.",
    )
    args = parser.parse_args(argv)
    repo = args.repo_root.resolve()

    ontology = derive_ontology_counts(repo)
    seeds = {
        "postgres": derive_seed_counts(repo, "postgres"),
        "sqlite": derive_seed_counts(repo, "sqlite"),
        "duckdb": derive_seed_counts(repo, "duckdb"),
    }
    rust = parse_rust_expected_counts(repo)
    go = parse_go_expected_counts(repo)
    manifest = manifest_data(repo)
    rdf = derive_rdf_counts(repo) if args.rdf else {"schema": None, "shapes": None}

    counts = manifest.get("counts", {})
    # The verification blocks live under [verification.postgres] / [verification.sqlite] etc.
    ver = manifest.get("verification", {})
    pg_v = ver.get("postgres", {}).get("expected_seed_counts", {})
    sqlite_v = ver.get("sqlite", {}).get("expected_seed_counts", {})
    duckdb_v = ver.get("duckdb", {}).get("expected_seed_counts", {})
    graph_v = ver.get("graph", {}).get("expected_node_counts", {})
    rdf_v_footer = ver.get("rdf", {}).get("expected_footer_counts", {})
    rdf_v_triples = ver.get("rdf", {}).get("expected_triple_counts", {})

    report = DriftReport()
    report.summary.append("count-mirror gate  (declared vs actual)")
    report.summary.append("=" * 90)

    report.summary.append("\n[counts] (ontology-derived):")
    for k in (
        "template_kinds",
        "entity_kinds",
        "relation_predicates",
        "attribute_vocabularies",
        "attribute_values_declared",
        "attribute_values_closed",
    ):
        report.check(f"  [counts].{k}", counts.get(k), ontology[k])

    # Legacy single-field rejection: the OLD `attribute_values` field was
    # split into _declared + _closed during the methodology-convergence
    # session (docs/reviews/2026-05-23-attribute-values-methodology/).
    # Once a field exits production, the gate MUST reject re-introduction
    # regardless of whether the new fields are also present — otherwise a
    # future PR can silently restore the ambiguous field by adding it
    # alongside the named ones. Per ISS-001 (brittleness-as-feature):
    # invalidations must propagate visibly; this is one such surface.
    if "attribute_values" in counts:
        report.failures.append(
            "[counts].attribute_values is the legacy ambiguous field that "
            "was retired in commit 9996826. It has been split into "
            "`attribute_values_declared` (170) and `attribute_values_closed` "
            "(99). The field MUST NOT be re-introduced regardless of "
            "whether the named successors are also present — silent "
            "coexistence is itself a defect. Remove the `attribute_values "
            "= ...` line from MANIFEST.toml."
        )

    for engine, seed_truth, mfst_block in (
        ("postgres", seeds["postgres"], pg_v),
        ("sqlite", seeds["sqlite"], sqlite_v),
        ("duckdb", seeds["duckdb"], duckdb_v),
    ):
        report.summary.append(f"\nexpected_seed_counts.{engine}:")
        # sqlite uses the `dagtoml_` prefix in its [verification] table keys
        prefix = "dagtoml_" if engine == "sqlite" else ""
        for k in (
            "kind_descriptor",
            "entity_kind_descriptor",
            "relation_descriptor",
            "attribute_vocabulary",
            "attribute_value_allowed",
        ):
            report.check(
                f"  {engine}.expected_seed_counts.{prefix}{k}",
                mfst_block.get(f"{prefix}{k}"),
                seed_truth[k],
            )

    report.summary.append("\nexpected_node_counts.graph (cross-checked vs ontology):")
    for src_key, ont_key in (
        ("KindDescriptor", "template_kinds"),
        ("EntityKind", "entity_kinds"),
        ("RelationPredicate", "relation_predicates"),
    ):
        report.check(
            f"  graph.expected_node_counts.{src_key}",
            graph_v.get(src_key),
            ontology[ont_key],
        )

    report.summary.append("\nexpected_footer_counts.rdf (vs ontology):")
    for src_key, ont_key in (
        ("template_kinds", "template_kinds"),
        ("entity_kinds", "entity_kinds"),
        ("relation_predicates", "relation_predicates"),
        ("attribute_vocabularies", "attribute_vocabularies"),
    ):
        report.check(
            f"  rdf.expected_footer_counts.{src_key}",
            rdf_v_footer.get(src_key),
            ontology[ont_key],
        )

    if args.rdf:
        report.summary.append("\nexpected_triple_counts.rdf (vs dagtoml-rdf verify):")
        # If the dagtoml-rdf binary isn't built, refuse to silently skip:
        # the maintainer MUST either build it or pass --no-rdf explicitly.
        # Anything else is the silent-mirror-rot pattern the gate exists
        # to prevent.
        if rdf["schema"] is None or rdf["shapes"] is None:
            report.failures.append(
                "RDF triple-count gate could not run: "
                "tools/dagtoml-rdf/target/release/dagtoml-rdf is missing or "
                "did not produce a parseable `parsed N triples` line. "
                "Either `cargo build --release -p dagtoml-rdf "
                "--manifest-path tools/dagtoml-rdf/Cargo.toml` or pass "
                "`--no-rdf` to acknowledge skipping this surface."
            )
            report.summary.append(
                "  rdf.expected_triple_counts.schema                              "
                "(tool not available — hard fail, see FAILURES below)"
            )
        else:
            report.check(
                "  rdf.expected_triple_counts.schema",
                rdf_v_triples.get("schema"),
                rdf["schema"],
            )
            report.check(
                "  rdf.expected_triple_counts.shapes",
                rdf_v_triples.get("shapes"),
                rdf["shapes"],
            )

    report.summary.append("\ntools/dagtoml-duckdb/src/main.rs EXPECTED_COUNTS:")
    for k in (
        "kind_descriptor",
        "entity_kind_descriptor",
        "relation_descriptor",
        "attribute_vocabulary",
        "attribute_value_allowed",
    ):
        report.check(
            f"  rust.EXPECTED_COUNTS.{k}",
            rust.get(k),
            seeds["postgres"][k] if k == "attribute_value_allowed" or k != "" else None,
        )

    # The Rust + Go hardcodes mirror duckdb's expected_seed_counts. Cross-check
    # against the duckdb seed truth (all three engines agree at HEAD anyway).
    report.summary.append("\ntools/dagtoml-duckdb-go/main.go expectedCounts:")
    for k in (
        "kind_descriptor",
        "entity_kind_descriptor",
        "relation_descriptor",
        "attribute_vocabulary",
        "attribute_value_allowed",
    ):
        report.check(
            f"  go.expectedCounts.{k}",
            go.get(k),
            seeds["duckdb"][k],
        )

    if args.quiet and not report.failures:
        # Quieter CI output on success: just the header.
        print("count-mirror gate: OK")
        return 0

    return report.print()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
