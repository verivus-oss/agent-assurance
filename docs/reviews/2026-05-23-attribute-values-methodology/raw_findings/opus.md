# Report — `MANIFEST.toml [counts].attribute_values`

HEAD verified: `99e18dba38ec3b4c6234b77bac7a87b0f2e6cdfc`.

---

## 1. Verification of `structural-analysis.md`

| Claim | Verdict | Evidence |
|---|---|---|
| Field location: `reference/database/MANIFEST.toml:37` | **CONFIRMED** | Read shows `attribute_values = 170` at line 37; siblings 33–36. |
| Drift script does not gate this field | **CONFIRMED** | `validators/check_manifest_drift.sh:64-67` reads only `template_kinds`, `entity_kinds`, `relation_predicates`, `attribute_vocabularies`. No `attribute_values` reference anywhere in the script. |
| Both validators have identical extensible semantics | **CONFIRMED** | `tools/dagtoml-validate-rs/src/main.rs:519-544` and `validators/validate_disclosure.py:82-105` re-read; the only branch on `extensible` is the "skip closure rejection" gate. Semantics match. |
| Closed-value count = 99, all-value count = 170 | **CONFIRMED** | Independent recompute via `tomllib`: total blocks 41, all values 170, closed values 99. Matches sibling `attribute_vocabularies = 41` on line 36. |
| Zero code consumers of `[counts].attribute_values` | **CONFIRMED** | `grep -rn 'attribute_values' validators/ tools/ --include='*.py' --include='*.rs' --include='*.go' --include='*.sh'` → zero matches. |
| `tools/dagtoml-duckdb/src/main.rs:21` mirror stale | **CONFIRMED, but worse than claimed** | Hardcode is `kind_descriptor=19, entity_kind_descriptor=26, relation_descriptor=30, attribute_vocabulary=37, attribute_value_allowed=81`. Actual seed has 20/27/31/41/109. The structural-analysis quotes "kind_descriptor=19 (stale, real=20)" but missed that **all five** fields are stale, not just one. |
| `tools/dagtoml-duckdb-go/main.go:40` same stale set | **CONFIRMED** | Lines 40–44, identical figures. |
| Structural-analysis §2 per-file table | **DISPUTED (totals correct, per-row wrong)** | Re-computation: `core/ontology.toml` is `(10 blocks, 39 values, 22 closed)`, not `(9, ~24, 22)`. `agent-assurance` is `(24, 91, 51)`, not `(24, ~108, 51)`. The errors happen to cancel so the bottom-line totals (41/170/99) survive — but the table as published is wrong and should not be cited. |

Bottom line: the structural-analysis is load-bearing-correct on every conclusion that matters (validator semantics, zero consumers, drift-script gap), but its §2 sub-totals table has arithmetic errors. The §4 staleness claim is **directionally right but undercounts** — the entire EXPECTED_COUNTS array in the two duckdb tools is stale, not just one entry.

---

## 2. Broadened evidence — the full count-mirror surface

`MANIFEST.toml` contains **six** declared count surfaces. I parsed each and compared against the actual seed files and the live ontology. Numbers in **bold** are stale today.

| Surface | Location | template_kinds / kind_desc | entity_kinds / entity_kd | relation_pred / rel_desc | attr_vocab | attr_values / attr_value_allowed |
|---|---|---|---|---|---|---|
| `[counts]` (ontology decl, CI-gated except attribute_values) | MANIFEST:33-37 | 20 ✓ | 27 ✓ | 31 ✓ | 41 ✓ | **170** (no gate) |
| postgres `expected_seed_counts` | MANIFEST:254 | **16** | **24** | 31 ✓ | **33** | **79** |
| duckdb `expected_seed_counts` | MANIFEST:285 | **16** | **24** | 31 ✓ | **33** | **79** |
| sqlite `expected_seed_counts` | MANIFEST:295 | **15** | **23** | **30** | **29** | **54** |
| graph `expected_node_counts` | MANIFEST:264 | **16** | **24** | 31 ✓ | — | — |
| rdf `expected_footer_counts` | MANIFEST:275 | 20 ✓ | 27 ✓ | 31 ✓ | 41 ✓ | — |
| Rust hardcode | `tools/dagtoml-duckdb/src/main.rs:21-27` | **19** | **26** | **30** | **37** | **81** |
| Go hardcode | `tools/dagtoml-duckdb-go/main.go:40-44` | **19** | **26** | **30** | **37** | **81** |
| **Actual seed file row counts** | `reference/database/{pg,sqlite,duckdb}/seed.sql` | 20, 20, 20 | 27, 27, 27 | 31, 31, 31 | 41, 41, 41 | **74, 109, 109** |

(Per-engine seed row counts parsed by walking each `INSERT INTO …attribute_value_allowed VALUES (…);` and counting top-level tuples; postgres is lower because the 18 `closed_enums` listed at MANIFEST:70-89 are modelled as native `CREATE TYPE` enums instead of `attribute_value_allowed` rows.)

**Three independent observations follow:**

**(a) Every count surface except the four CI-gated block counts and the auto-generated RDF footer is stale.** Not "drifted by one or two". The duckdb hardcode at `tools/dagtoml-duckdb/src/main.rs:21` is wrong on every single field. The sqlite `expected_seed_counts` understates the actual sqlite seed by 55 rows in `attribute_value_allowed`. The maintenance discipline is not partially broken; it is essentially absent everywhere a CI gate isn't pulling on it.

**(b) The recent change to 170 was a unilateral interpretation flip.** Commit `99e18db` log explicitly says:
> "MANIFEST attribute_values = 106 was numerically wrong. The comment said 'union across all closed-and-extensible-vocabulary allowed values' but the field was being maintained as if it were closed-only. … Corrected to 170 (matches the documented intent of the field)"

But the prior value 106 was neither the closed-count (99) nor the all-count (170). History via `git log -p`: the value walked `81 → 84 → 106 → 170`. The 106 value matches **today's actual sqlite/duckdb seed-row count (109)** almost exactly — off by 3, consistent with the cost-profile addition not yet rolled into the seed at that commit. **The historical maintenance intent of `attribute_values` was "rows the seed actually emits"**, not "all declared values". The 170 commit re-interpreted the field without checking the prior derivation rule.

**(c) `attribute_values` is a categorically different aggregate than its four siblings.** The other four `[counts]` fields are block counts: one row per `[[entities]]` / `[[relations]]` / `[[attribute_vocabularies]]` / `*-kind.toml`. `attribute_values` is a value count: one row per element inside a `values = […]` array. Mixing block-aggregates and value-aggregates in the same table without a comment naming the asymmetry is what made the historical drift invisible — every contributor who touched the block counts assumed `attribute_values` followed the same rule. It does not.

**(d) No SPEC normative surface names this field.** `grep attribute_values SPEC.md` → zero matches. The MANIFEST header at lines 1-10 says: "This file is NOT a DAG-TOML kind … project metadata. The validators under `validators/` do not inspect it beyond TOML parse-ability." The whole file is self-declared informational. The CI-gated four are the *de facto* normative subset.

---

## 3. Root discrepancy

**The single sentence:** `attribute_values` is a definitionally underspecified field of a categorically different aggregation kind than its siblings, embedded in a `[counts]` mirror surface whose entire maintenance discipline (six surfaces total) is broken everywhere CI isn't gating it — so the grok/codex disagreement is not a methodology dispute, it is two reviewers reading two different defensible meanings into a field that has no SPEC text, no consumer, and no producer-side validator.

The deeper failure is the mirror pattern itself. `[counts]` (one source), `expected_seed_counts` (three engine copies), `expected_node_counts` (graph copy), `expected_footer_counts` (RDF copy), `EXPECTED_COUNTS` (Rust hardcode), `expectedCounts` (Go hardcode) — eight hand-maintained copies of figures that all derive from one source (the ontology files + the seed files). One CI gate (`check_manifest_drift.sh`) pulls on four of the eight surface's four fields. Every other field on every other surface drifts silently. The brittleness-as-feature principle the project is built on (invalidations must propagate visibly) is being violated by the very file that documents what the reference databases ship.

---

## 4. Recommendation — option (E), single PR

A "set it to 170 and call it documentation" answer fixes nothing the user actually cares about. Brittleness-as-feature requires the producer-side validator. Below is the concrete edit.

### 4.1 MANIFEST.toml edit

Replace line 37 with two unambiguously-named fields:

```toml
# attribute_values_declared = sum of len(values) across every
# [[attribute_vocabularies]] block in core + every profile ontology.
# Matches the ontology's documented surface, ignoring whether each
# vocabulary is open or closed.
attribute_values_declared = 170

# attribute_values_closed = same sum restricted to vocabularies with
# extensible = false. This is the size of the rejection surface the
# tools/dagtoml-validate-rs and validators/validate_disclosure.py
# `check_vocab` functions actually enforce (see
# tools/dagtoml-validate-rs/src/main.rs:519-544 and
# validators/validate_disclosure.py:82-105).
attribute_values_closed = 99
```

This makes the categorical difference explicit, gives both reviewers their honest number, and names the consumer for the closed count (the two validators) at file:line in the field's own comment.

### 4.2 New validator: `validators/check_attribute_values.py`

```python
#!/usr/bin/env python3
"""Re-derive [counts].attribute_values_declared and
[counts].attribute_values_closed from the ontology files and exit
non-zero on drift. Invoked by check_manifest_drift.sh."""
import pathlib, sys, tomllib

REPO = pathlib.Path(__file__).resolve().parents[1]

ONTOLOGIES = [
    REPO / "core" / "ontology.toml",
    *sorted((REPO / "profiles").glob("*/ontology.toml")),
]

declared = closed = 0
for f in ONTOLOGIES:
    for v in tomllib.loads(f.read_text()).get("attribute_vocabularies", []):
        n = len(v.get("values", []))
        declared += n
        if not v.get("extensible", False):
            closed += n

manifest = tomllib.loads((REPO / "reference/database/MANIFEST.toml").read_text())
counts = manifest.get("counts", {})
claimed_d = counts.get("attribute_values_declared")
claimed_c = counts.get("attribute_values_closed")

fail = 0
def report(label, claimed, actual):
    global fail
    op = "==" if claimed == actual else "!="
    tag = "" if claimed == actual else "   <-- DRIFT"
    if claimed != actual: fail = 1
    print(f"  {label:32s} {claimed!s:>5} {op} {actual}{tag}")

print("attribute-values drift (MANIFEST vs ontology)")
report("attribute_values_declared", claimed_d, declared)
report("attribute_values_closed",   claimed_c, closed)
sys.exit(fail)
```

### 4.3 `check_manifest_drift.sh` wire-in

Append after current line 85:

```bash
report attribute_vocabularies "$M_VOCABS"    "$TOTAL_VOCABS"

# attribute_values_{declared,closed} — value-aggregate, not block-aggregate.
# Computed by validators/check_attribute_values.py because pure bash
# cannot sum array lengths inside TOML reliably.
if ! python3 "$REPO_ROOT/validators/check_attribute_values.py"; then
    fail=1
fi
```

### 4.4 SPEC addition

Add one paragraph in `SPEC.md §10` (the ontology section) where attribute_vocabularies are introduced:

> Reference-database manifests MAY publish derived counts of the
> attribute-value surface. When they do, they MUST distinguish
> `attribute_values_declared` (the union across every
> `[[attribute_vocabularies]]` block's `values` array) from
> `attribute_values_closed` (the same union restricted to
> `extensible = false` vocabularies — the surface the normative
> validators reject against). Mixing the two aggregates in one field
> is prohibited.

This is the only field-naming convention worth a normative line; everything else in `MANIFEST.toml` stays informational.

### 4.5 Why this is producer-side

The validator at 4.2 derives both numbers from the ontology files in <50ms and asserts the manifest matches. Any ontology change that adds a `values = […]` entry without bumping the manifest will fail CI loudly. The user's "invalidations must propagate visibly" principle is satisfied by the script returning non-zero exit, not by hoping a future reviewer notices a drifted comment.

### 4.6 Separate follow-up commit (same branch, different concern)

Do not bundle into the same PR; file as immediate follow-up:

- Extend `check_manifest_drift.sh` to **also** assert every `expected_seed_counts.*`, `expected_node_counts.*`, and `expected_footer_counts.*` in MANIFEST.toml against the actual seed file row counts.
- Delete the hardcoded `EXPECTED_COUNTS` in `tools/dagtoml-duckdb/src/main.rs:21-27` and `tools/dagtoml-duckdb-go/main.go:40-44` and have both tools read MANIFEST.toml at runtime (or generate the constants from MANIFEST.toml at build time). They are pure duplication today and contribute nothing CI doesn't already check at the manifest layer.

These two changes finish closing the brittleness gap. They are out of scope of the `attribute_values` question per se, but in scope of the broadened evidence — and the user asked me to identify it.

---

## 5. What I would NOT do, and why

**Option (A) — set to 170 + add validator that asserts 170.** Rejected: the field still has no consumer, the categorical asymmetry with its siblings is still invisible to readers, and the reading of "all declared values" is a choice that one reviewer prefers and the other rejects. Picking 170 declares one reviewer right by fiat; my recommendation (E) accommodates both, with named distinctions. The cost of adding a second field is one line of TOML and zero changes to consumers (there are none). The cost of picking 170 alone is that the next reviewer who notices the closure-surface meaning files the same ticket again.

**Option (B) — rename to `closed_attribute_values` and use 99 alone.** Rejected for the symmetric reason: it discards the historically-intended documentation of "what the ontology declares" without replacement.

**Option (D) — delete the field entirely.** Rejected as a near miss. It's defensible (no consumer exists today, removing ambiguity is itself a win) — but the user values documentation of the spec's declared surface, and removing the field hides a number that has legitimate reader value (e.g., a runtime author wanting to size their attribute-value-allowed table). My recommendation keeps the documentation and adds the discipline.

**Concerns with my own recommendation:**
1. Two new field names invite a third reviewer to want a third name. Mitigation: SPEC §10 paragraph (4.4) makes the names normative for any future manifest, so the bikeshed is closed at the spec layer.
2. The follow-up work (4.6) is sized at maybe an afternoon but I am scoping it out of the immediate PR. If the user's brittleness principle is read strictly, both should ship together. I split them because the `attribute_values` ambiguity is the active blocker (two reviewers disagreed publicly); the broader mirror staleness is silent rot that has existed for many commits and can take an extra day without harm. If the user prefers, they can be one PR — the validator script grows from ~25 lines to ~60.
3. The 99 / 170 numbers themselves will need rebumping every time someone edits a vocabulary's `values` array. That is the point — the new validator will tell them by failing CI. Producer-side responsibility is satisfied; brittleness propagates visibly.
