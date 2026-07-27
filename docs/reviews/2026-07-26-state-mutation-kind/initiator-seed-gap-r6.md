# Initiator verification of Grok's round-6 blocker

Initiator: Claude (Opus 5), Werner Kasselman's session, 2026-07-27, at
`2d5809e`. Written after the round-6 dispatch, so the reviewed commit did not
move mid-flight.

Grok said the two new closed vocabularies are missing their eight
`attribute_value_allowed` rows. Devin said their absence is expected because
they were "promoted to engine enums". Both cannot be true. This is the
resolution, run rather than argued.

## The rule, as the seed states it about itself

`reference/database/postgres/seed.sql:232-234`:

```sql
-- Allowed values for non-enum-backed (i.e., extensible) vocabularies.
-- Enum-backed values are enforced by the Postgres enum type itself, so
-- their allowed values do not need to be repeated here.
```

So membership of `attribute_value_allowed` is decided by **enum backing**, not
by closedness. The last column of each `attribute_vocabulary` row names the
backing enum type, or NULL.

## The rule, as the data actually obeys it

Parsed all `INSERT INTO attribute_vocabulary` statements (there is more than
one; a single-statement parse silently sees 5 of 50 rows) and the
`attribute_value_allowed` block:

| Population | Count |
|---|---|
| vocabularies in the seed | 50 |
| enum-backed | 16 |
| non-enum-backed | 34 |
| distinct vocabularies with value rows | 31 |
| value rows | 144 |

Testing "seeded if and only if not enum-backed" across all 50:

- enum-backed but seeded anyway: **0**
- non-enum-backed but not seeded: **3**, namely `execution_proof_scheme`,
  `finality_basis`, and `license`

`license` is `extensible = true` with **zero** declared values
(`core/ontology.toml`), so it has no value list to seed and is not a violation.

**That leaves exactly the two vocabularies this branch added.** Every other
non-enum-backed vocabulary in the repository is seeded.

## Devin's explanation is false

No enum type exists for either:

```
$ grep -rn "CREATE TYPE" reference/database/postgres/schema.sql
```

lists 16 types, none for `execution_proof_scheme` or `finality_basis`. And both
carry NULL in the enum column, exactly like the two that ARE seeded:

```
seed.sql:227  ('witness_scheme',         ..., 'profile:com.verivus.runtime', NULL),
seed.sql:228  ('attester_observed',      ..., 'profile:com.verivus.runtime', NULL),
seed.sql:229  ('execution_proof_scheme', ..., 'profile:com.verivus.runtime', NULL),
seed.sql:230  ('finality_basis',         ..., 'profile:com.verivus.runtime', NULL);
```

`witness_scheme` and `attester_observed` contribute 3 value rows each. The two
new ones contribute 0.

## A wrong cut that nearly refuted a correct blocker

The initiator's first pass asked "which CLOSED vocabularies have no value
rows?" and got **18**, including core vocabularies like `priority`,
`unit.status` and `review.status` that predate this branch by many months. Read
naively that says closedness is not the criterion and Grok generalised from a
two-item sample.

It was the wrong cut. 16 of those 18 are enum-backed and correctly excluded.
Once the enum column is taken into account the exceptions collapse to the two
new vocabularies. Recorded because the wrong cut was more comforting than the
right one, and stopping there would have dismissed a real defect on
sophisticated-looking evidence.

## Same gap in all three engine seeds

Occurrence counts per vocabulary name (1 = the `attribute_vocabulary` row only;
4 = that row plus 3 value rows):

| Engine | witness_scheme | attester_observed | execution_proof_scheme | finality_basis |
|---|---|---|---|---|
| postgres | seeded (3 values) | seeded (3 values) | **0 values** | **0 values** |
| sqlite | 4 | 4 | **1** | **1** |
| duckdb | 4 | 4 | **1** | **1** |

## Why every gate stayed green

`validators/check_attribute_values.py` compares
`expected_seed_counts.attribute_value_allowed` against the actual row count in
the seed files. Both say 144, so they agree. Nothing compares the SET of
non-enum-backed vocabularies in the ontologies against the SET present in
`attribute_value_allowed`. The RDF surface does embed the new values as
`owl:oneOf`, which is why the triple count moved to 1476 and looked like full
propagation.

This is the same defect class as the manifest-drift defect that `301a322` was
written to fix, one surface deeper: `301a322` propagated the vocabulary ROWS and
the counts, and did not propagate the VALUE rows.

## Fix scope, if it is applied

1. Eight `attribute_value_allowed` rows in each of the three seeds, mirroring
   the witness block (4 values for `execution_proof_scheme`, 4 for
   `finality_basis`).
2. `attribute_value_allowed` 144 to 152 at `reference/database/MANIFEST.toml`
   lines 283, 314 and 324.
3. The same constant in `tools/dagtoml-duckdb/src/main.rs:33` and
   `tools/dagtoml-duckdb-go/main.go:46`.
4. The `144 attribute_value_allowed rows` comment at
   `reference/database/sqlite/seed.sql:14`.
5. Re-run `validators/check_manifest_drift.sh` between steps rather than after
   them, since this is the surface where fixing top-down previously produced a
   plausible wrong result.

A durable fix would additionally make the gate compare the two SETS, not just
the two COUNTS. That is what would have caught this without a reviewer.

## Named questions the initiator verified independently

Run at `2d5809e`, primaries rebuilt from this tree.

| Question | Result |
|---|---|
| 1, ALLOWED_COLLISIONS is earned | **Confirmed.** Mutating only the RKC02 site from `hasKey` to `tableOf` and rebuilding: `array-proof` go=0 (accepted, wrong) with rs=1 py=1, so the corpus reddens; `table-proof` stays rs=1 go=1 py=1. The pair does discriminate by verdict. Matches Grok and Devin. |
| 3d, no other negative violates the convention | **Confirmed.** All 32 `examples/negative/*.toml` swept: 18 carry `[provenance]`, all 18 are rejected. |
| 4, shared `closure_root` | **Confirmed correct.** Both fixtures carry identical `provenance.source_sha256`, `mutation.authorization_sha256` and `mutation.effect_sha256`, which are the three pinned records. `PROFILE.toml:93-96` states that RKC02 is kind-layer precisely because a closure stream can pin presence but never absence. |
| 5, `attribute_values_closed = 123` | **Confirmed** by summing `len(values)` over `extensible = false` across `core/ontology.toml` and all five profile ontologies: 32 + 51 + 14 + 22 + 4 = 123. `attribute_values_declared` = 216 and `attribute_vocabularies` = 50 also confirmed. |
| 5, RDF `schema = 1476` | **Confirmed.** Regenerated `schema.ttl` with the freshly built `dagtoml-rdf` into a scratch path: byte-identical to the committed file, footer counts 23/27/31/50, and `verify` parses 1476 triples. `shapes.ttl` parses 148. |
| all 22 kind descriptors | PASS with `--check-references-exist`. |
