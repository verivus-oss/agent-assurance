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
import contextlib
import pathlib
import re
import sys
import _toml11 as tomllib  # TOML 1.1 reference shim (stdlib tomllib is 1.0-only); see validators/_toml11.py


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

def _paren_delta(line: str) -> int:
    """Net bracket depth of a line, ignoring brackets inside quoted strings."""
    depth, in_str, prev = 0, False, ""
    for ch in line:
        if ch == "'" and prev != "\\":
            in_str = not in_str
        elif not in_str:
            if ch in "([":
                depth += 1
            elif ch in ")]":
                depth -= 1
        prev = ch
    return depth


def _split_columns(row: str) -> list[str]:
    """Split a tuple row on top-level commas only, so commas inside quotes or
    inside ARRAY[...] / [...] / json_array(...) literals do not split it."""
    inner = row.strip()
    inner = inner[1:] if inner.startswith("(") else inner
    inner = inner.rstrip(",;").rstrip()
    inner = inner[:-1] if inner.endswith(")") else inner
    cols, buf, depth, in_str, prev = [], "", 0, False, ""
    for ch in inner:
        if ch == "'" and prev != "\\":
            in_str = not in_str
            buf += ch
        elif in_str:
            buf += ch
        elif ch in "([":
            depth += 1
            buf += ch
        elif ch in ")]":
            depth -= 1
            buf += ch
        elif ch == "," and depth == 0:
            cols.append(buf.strip())
            buf = ""
        else:
            buf += ch
        prev = ch
    if buf.strip():
        cols.append(buf.strip())
    return cols


def _tuple_rows(seed_path: pathlib.Path, table_re_str: str) -> list[str]:
    """Return complete tuple rows inside the named INSERT INTO block.

    Rows are joined until bracket balance returns to zero, so a row split
    across several lines is returned whole. A line-based reader looks correct
    against today's seeds, where every row happens to fit on one line, and
    silently reads the wrong column the moment one is reformatted.
    """
    if not seed_path.exists():
        return []
    txt = seed_path.read_text()
    m = re.search(rf"INSERT INTO {table_re_str}\b.*?\bVALUES", txt, re.DOTALL)
    if not m:
        return []
    rest = txt[m.end():]
    end_match = re.search(
        r"\n\s*(?:INSERT INTO|ALTER|CREATE|DROP|COMMIT|--\s*=====)", rest
    )
    block = rest[: end_match.start()] if end_match else rest

    rows, buf, depth = [], "", 0
    for raw in block.splitlines():
        if not buf and not raw.strip().startswith("('"):
            continue
        buf = f"{buf} {raw.strip()}" if buf else raw.strip()
        depth += _paren_delta(raw)
        if depth <= 0:
            rows.append(buf.strip())
            buf, depth = "", 0
    return rows


def _count_tuple_rows(seed_path: pathlib.Path, table_re_str: str) -> int | None:
    """Count tuple rows inside the named INSERT INTO block."""
    if not seed_path.exists():
        return None
    return len(_tuple_rows(seed_path, table_re_str)) or None


def derive_seed_vocab_surfaces(
    repo_root: pathlib.Path, engine: str
) -> tuple[dict[str, str | None], dict[str, list[str]]]:
    """Return (vocabulary -> claimed native backing or None,
    vocabulary -> the list of values seeded for it).

    The last column of an `attribute_vocabulary` row names the native construct
    that enforces a closed value set (`backing_enum_type` in postgres and
    duckdb, `backing_check_constraint` in sqlite), or NULL. The claim is only a
    claim: `derive_schema_native_constructs` checks whether the named construct
    exists. A row that does not parse into 8 columns is an error rather than a
    guess, because the permissive guess is the one that hides defects.
    """
    db_dir = repo_root / "reference" / "database" / engine
    seed = db_dir / "seed.sql"
    prefix = "dagtoml_" if engine == "sqlite" else "(?:dagtoml\\.)?"

    claims: dict[str, str | None] = {}
    unparseable: list[str] = []
    for row in _tuple_rows(seed, f"{prefix}attribute_vocabulary"):
        cols = _split_columns(row)
        if len(cols) != 8 or not cols[0].startswith("'"):
            unparseable.append(row[:70])
            continue
        last = cols[-1].strip()
        claims[cols[0].strip("'")] = None if last.upper() == "NULL" else last.strip("'")
    if unparseable:
        raise ValueError(
            f"{engine}: {len(unparseable)} attribute_vocabulary row(s) did not "
            f"parse into 8 columns, so the backing column cannot be read. A "
            f"gate that cannot tell MUST NOT guess: {unparseable[:3]}"
        )

    seeded: dict[str, list[str]] = {}
    for row in _tuple_rows(seed, f"{prefix}attribute_value_allowed"):
        cols = _split_columns(row)
        if len(cols) != 2:
            raise ValueError(
                f"{engine}: attribute_value_allowed row did not parse into 2 "
                f"columns: {row[:70]}"
            )
        seeded.setdefault(cols[0].strip("'"), []).append(cols[1].strip("'"))
    return claims, seeded


def derive_schema_native_constructs(
    repo_root: pathlib.Path, engine: str
) -> dict[str, set[str]]:
    """Return native construct name -> the value set it enforces.

    Postgres and duckdb use `CREATE TYPE <name> AS ENUM (...)`. Sqlite has no
    enum type and uses `<col> TEXT CHECK (<col> ... IN (...))`. A backing named
    by a seed but absent here is an unverified assertion, which is exactly the
    "promoted to engine enums" excuse in machine-readable form.
    """
    schema = repo_root / "reference" / "database" / engine / "schema.sql"
    if not schema.exists():
        return {}
    txt = schema.read_text()
    out: dict[str, set[str]] = {}
    for m in re.finditer(r"CREATE TYPE\s+(\w+)\s+AS ENUM\s*\((.*?)\);", txt, re.S):
        out[m.group(1)] = set(re.findall(r"'([^']*)'", m.group(2)))
    for m in re.finditer(
        r"(\w+)\s+TEXT\s+CHECK\s*\(\s*\1[^)]*?IN\s*\((.*?)\)", txt, re.S
    ):
        out.setdefault(m.group(1), set(re.findall(r"'([^']*)'", m.group(2))))
    return out


# Pre-existing gaps in the sqlite mirror, predating the mutation-kind branch.
# These eight vocabularies carry NULL in sqlite's `backing_check_constraint`
# column AND have no value rows AND are named by no CHECK in sqlite/schema.sql,
# so nothing in the sqlite mirror enforces them. Postgres backs all eight with
# enum types. This is a baseline, not a green light: every entry is printed on
# every run, and an entry that acquires a PARTIAL seed is checked normally
# rather than skipped, so the baseline cannot quietly widen.
SQLITE_MEMBERSHIP_BASELINE = {
    "adapter_id_derivation",
    "adapter_ref_syntax",
    "gate_decision_verdict",
    "override_rule_operator",
    "runtime_clock_policy",
    "runtime_kind",
    "runtime_network_policy",
    "severity_tier",
}


def derive_ontology_vocabularies(
    repo_root: pathlib.Path,
) -> tuple[dict[str, set[str]], list[str]]:
    """Return (vocabulary name -> declared value set, duplicate names).

    Duplicates are returned rather than silently collapsed: two ontologies
    declaring the same vocabulary under different value sets is a defect no
    count can see, and the previous dict-overwrite made the last one win.
    """
    paths = [repo_root / "core" / "ontology.toml"]
    profiles_dir = repo_root / "profiles"
    if profiles_dir.exists():
        paths.extend(sorted(profiles_dir.glob("*/ontology.toml")))
    out: dict[str, set[str]] = {}
    duplicates: list[str] = []
    for p in paths:
        d = tomllib.loads(p.read_text())
        for v in d.get("attribute_vocabularies", []):
            name = v["attribute"]
            if name in out:
                duplicates.append(f"{name} (redeclared in {p})")
            out[name] = set(v.get("values", []))
    return out, duplicates


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
            if m:
                out[label] = int(m.group(1))
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

    # Counts agreeing is necessary and NOT sufficient, and neither is a
    # seed-driven name check. Testing defeated the first version of this gate
    # three separate ways: rename a vocabulary in the seeds and the ontology
    # name went unenforced; claim a backing type that does not exist and the
    # values could be deleted; typo a value and the count still matched. The
    # loop below is therefore ONTOLOGY-driven, verifies every claimed backing
    # against the engine's schema, and compares exact value SETS.
    ont_vocab, ont_duplicates = derive_ontology_vocabularies(repo)
    for dup in ont_duplicates:
        report.failures.append(
            f"  ontology: {dup} is declared by more than one ontology, so its "
            f"value set is ambiguous"
        )

    for engine in ("postgres", "sqlite", "duckdb"):
        report.summary.append(f"\nattribute_value_allowed membership.{engine}:")
        claims, seeded = derive_seed_vocab_surfaces(repo, engine)
        native = derive_schema_native_constructs(repo, engine)
        baselined: list[str] = []

        for name, declared in sorted(ont_vocab.items()):
            if name not in claims:
                report.failures.append(
                    f"  {engine}: {name} is declared by an ontology but has no "
                    f"attribute_vocabulary row"
                )
                continue
            backing = claims[name]
            rows = seeded.get(name, [])

            if backing is not None:
                if backing not in native:
                    report.failures.append(
                        f"  {engine}: {name} claims native backing {backing!r}, "
                        f"which no CREATE TYPE or CHECK in {engine}/schema.sql "
                        f"defines, so nothing enforces it"
                    )
                elif not declared <= native[backing]:
                    missing = sorted(declared - native[backing])
                    report.failures.append(
                        f"  {engine}: {name} is backed by {backing!r}, which does "
                        f"not admit {missing}"
                    )
                elif rows:
                    report.failures.append(
                        f"  {engine}: {name} has {len(rows)} value row(s) despite "
                        f"being backed by {backing!r}"
                    )
                continue

            if not declared:
                continue  # open vocabulary with no enumerated values
            if engine == "sqlite" and name in SQLITE_MEMBERSHIP_BASELINE and not rows:
                baselined.append(f"{name} ({len(declared)} values)")
                continue
            if not rows:
                report.failures.append(
                    f"  {engine}: {name} ({len(declared)} values declared) is "
                    f"absent from attribute_value_allowed"
                )
            elif set(rows) != declared:
                report.failures.append(
                    f"  {engine}: {name} value set differs from the ontology: "
                    f"missing {sorted(declared - set(rows))}, "
                    f"unexpected {sorted(set(rows) - declared)}"
                )
            elif len(rows) != len(declared):
                report.failures.append(
                    f"  {engine}: {name} has duplicate value rows "
                    f"({len(rows)} rows for {len(declared)} values)"
                )

        for name in sorted(set(claims) - set(ont_vocab)):
            report.failures.append(
                f"  {engine}: {name} has an attribute_vocabulary row but is "
                f"declared by no ontology"
            )
        for name in sorted(set(seeded) - set(ont_vocab)):
            report.failures.append(
                f"  {engine}: {name} has value rows but is declared by no ontology"
            )

        report.summary.append(
            f"  {len(ont_vocab)} ontology vocabularies, "
            f"{sum(1 for b in claims.values() if b is None)} unbacked in this "
            f"mirror, {len(seeded)} with value rows, "
            f"{len(native)} native constructs in schema.sql"
        )
        for item in baselined:
            report.summary.append(
                f"  BASELINED (pre-existing, unenforced in this mirror): {item}"
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
