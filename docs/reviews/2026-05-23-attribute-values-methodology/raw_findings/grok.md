**1. Measure definition**

(A) Total count of values across every `[[attribute_vocabularies]]` block in every loaded ontology, closed or extensible, including starter lists for extensible vocabularies.

This is the correct semantic for `[counts].attribute_values` because the other four fields in the same table (`template_kinds`, `entity_kinds`, `relation_predicates`, `attribute_vocabularies`) are unfiltered declaration counts aggregated over exactly the same set of ontology files (core + every `profiles/*/ontology.toml`), and the comment already present at `reference/database/MANIFEST.toml:37` states the "BOTH closed and extensible" rule with the explicit re-derivation recipe "walking every `[[attribute_vocabularies]]` block in those four ontology files and summing `len(values)`". The field is an ontology-source size metric for the reference database artefacts; the smaller, engine-specific row counts that actually appear in `attribute_value_allowed` tables live in the per-[verification.*] sections and are intentionally a subset (enum-backed closed vocabularies are omitted from the allowed table by design).

No downstream runtime consumer in a separate repository is named in this public spec repo; the only readers are humans and tooling that consult `reference/database/MANIFEST.toml` and `validators/check_manifest_drift.sh` inside this repository.

**2. Data acquisition method**

Exact mechanical recipe:

- Start at the repository root (the directory containing `core/`, `profiles/`, `reference/database/MANIFEST.toml`, etc.).
- Read exactly these files (in this order for determinism):
  - `core/ontology.toml`
  - Every file matching the glob `profiles/*/ontology.toml`, discovered by enumerating immediate subdirectories of `profiles/` and retaining those that contain an `ontology.toml` file (currently: `profiles/agent-assurance/ontology.toml`, `profiles/cost/ontology.toml`, `profiles/disclosure/ontology.toml`). Use the identical discovery loop already present in `validators/check_manifest_drift.sh:21-23`.
- In each of the four files, locate every top-level TOML table whose header is `[[attribute_vocabularies]]`.
- For each such table, read the `values` field (an array of strings). Ignore the values of `extensible`, `applies_to`, `notes`, `default`, `ijb_primitive`, `ijb_constraint_type`, and any other keys.
- Compute the integer length of that array and add it to a running total. Perform the addition for every block in every file.
- The final sum is the value of `[counts].attribute_values`.

Profile composition rule: the count is always taken over the complete set of `profiles/*/ontology.toml` files present at the moment of computation. It is the "full reference database" view; it is not scoped to a single `framework_profile` value. Adding a new profile directory or adding starter values to an extensible vocabulary in an existing profile file increases the total. This is identical to how `attribute_vocabularies = 41` (and the three other counts) are computed today.

**3. Validation tooling**

(ii) Write a small Python validator (`validators/check_attribute_values.py`) that the drift script invokes (and that the "Manifest drift" CI job can call directly).

The existing `validators/check_manifest_drift.sh` is intentionally pure POSIX bash + awk + grep so that the four block-count checks have zero Python dependency and run in the most minimal environments. Reliably extracting the contents of multi-line `values = [ ... ]` arrays (some spanning 8+ lines with trailing commas) cannot be done with awk/grep without fragile line-by-line state machines that duplicate a TOML parser. A 45-line Python 3.11+ script using only the stdlib `tomllib` module is the smallest, judgement-free implementation that matches the exact discovery and summation rules above; calling it from the bash wrapper (or as an additional step inside the same CI job) keeps the single-command UX while making the fifth field first-class and enforced exactly like the other four.

Recommended addition to `validators/check_manifest_drift.sh` (after the existing `report attribute_vocabularies` line):

```bash
# attribute_values — requires the python helper for reliable array-length summation
AV=$(python3 "$REPO_ROOT/validators/check_attribute_values.py" --repo-root "$REPO_ROOT" --quiet)
M_AV=$(manifest_count attribute_values)
report attribute_values "$M_AV" "$AV"
```

Full script body for `validators/check_attribute_values.py` (self-contained, runnable today):

```python
#!/usr/bin/env python3
"""Compute and (optionally) validate [counts].attribute_values.

Protocol (A): sum of len(values) over every [[attribute_vocabularies]]
block in core/ontology.toml + all profiles/*/ontology.toml files.
"""
import argparse
import pathlib
import sys
import tomllib

def compute(repo_root: pathlib.Path) -> int:
    core = repo_root / "core" / "ontology.toml"
    profile_onts = sorted((repo_root / "profiles").glob("*/ontology.toml"))
    total = 0
    for p in [core] + profile_onts:
        if not p.exists():
            continue
        data = tomllib.loads(p.read_text(encoding="utf-8"))
        for block in data.get("attribute_vocabularies", []):
            total += len(block.get("values", []))
    return total

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=pathlib.Path, default=pathlib.Path("."))
    ap.add_argument("--check-manifest", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    total = compute(args.repo_root)
    if args.quiet:
        print(total)
        return
    print(f"computed attribute_values (A): {total}")

    if args.check_manifest:
        mpath = args.repo_root / "reference" / "database" / "MANIFEST.toml"
        mdata = tomllib.loads(mpath.read_text(encoding="utf-8"))
        mval = mdata.get("counts", {}).get("attribute_values")
        if mval is None:
            print("ERROR: no [counts].attribute_values in MANIFEST")
            sys.exit(2)
        if mval != total:
            print(f"DRIFT: MANIFEST has {mval}, ontologies yield {total}")
            sys.exit(1)
        print(f"OK — attribute_values matches MANIFEST ({mval})")

if __name__ == "__main__":
    main()
```

**4. Independent computation under your protocol**

Exact command run at `HEAD = 99e18dba38ec3b4c6234b77bac7a87b0f2e6cdfc`:

```bash
python3 -c '
import pathlib, tomllib
root = pathlib.Path(".")
core = root / "core/ontology.toml"
profiles = sorted((root / "profiles").glob("*/ontology.toml"))
ontologies = [core] + profiles
print("Files read:")
for p in ontologies: print(" ", p)
total = 0
for p in ontologies:
    data = tomllib.loads(p.read_text(encoding="utf-8"))
    for block in data.get("attribute_vocabularies", []):
        total += len(block.get("values", []))
print("computed_attribute_values:", total)
'
```

Verbatim output:

```
Files read:
  core/ontology.toml
  profiles/agent-assurance/ontology.toml
  profiles/cost/ontology.toml
  profiles/disclosure/ontology.toml
computed_attribute_values: 170
```

Number obtained: 170.

`reference/database/MANIFEST.toml` `[counts].attribute_values` at HEAD claims 170; the protocol computation yields exactly 170 (matches).

**5. Other-reviewer reconciliation**

The most defensible interpretation I considered but rejected is (B) — sum only over blocks where `extensible = false`. I rejected it because that filter is not applied to any of the four sibling counts, contradicts the explicit "(BOTH closed and extensible)" wording and "summing `len(values)`" recipe already written at `MANIFEST.toml:37`, and would turn the top-level ontology-size metric into an engine-specific "enum surface" number whose exact value already varies by DB (postgres closed_enums list vs. sqlite closed_checks list) and is therefore already recorded in the per-[verification.*] tables.

What would change my mind: a sentence added to `SPEC.md` (or `core/ontology.md` near the attribute-vocabulary tables) that explicitly defines the purpose of `[counts].attribute_values` as "the count of literals belonging to closed (`extensible = false`) vocabularies only, for the purpose of sizing reference-schema enum declarations" together with a pointer to a concrete consumer (e.g. "used by the postgres seed generator at reference/database/postgres/seed.sql:214"). No such definition exists at any line today.

The decision the spec maintainer still needs to make: whether, after locking this protocol, the now-stale per-engine `expected_seed_counts.attribute_value_allowed` numbers (currently declared as 79/54 but actually 106 rows in all three seed files) should be brought into sync in the same change, or whether they are deliberately allowed to remain smaller "post-insertion" numbers that differ from the ontology declaration total because some closed vocabularies are realised as native enums rather than rows. A secondary wording decision is the precise new comment text on `MANIFEST.toml:37` (suggested: "sum of len(values) over every [[attribute_vocabularies]] block across core/ontology.toml + all profiles/*/ontology.toml (both extensible=true and =false; includes starter lists)").

(The persisted prompt copy is at `docs/reviews/2026-05-23-attribute-values-methodology/prompt.md`; all paths and line numbers above are relative to repo root at the cited HEAD.)

## Summary of concrete next actions (for the maintainer)

- Adopt (A) + the recipe in section 2.
- Place the Python script in `validators/check_attribute_values.py`.
- Extend `validators/check_manifest_drift.sh` with the four-line call shown in section 3 (and add the corresponding CI step if desired).
- Update the comment at `MANIFEST.toml:37` to remove the ambiguous "closed-and-extensible" phrasing.
- Re-run the drift script; it will now enforce 170 and stay green.

This protocol is fully mechanical, matches the existing file text, treats the fifth count symmetrically with the first four, and eliminates the source of the 170-vs-99 divergence.
