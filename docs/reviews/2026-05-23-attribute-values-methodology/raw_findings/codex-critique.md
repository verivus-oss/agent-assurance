**1. Verification of Opus Evidence**

| Claim | Verdict | Evidence |
|---|---|---|
| `MANIFEST.toml [counts].attribute_values = 170` at line 37 | confirmed | [MANIFEST.toml](/srv/repos/external/verivus-oss/agent-assurance/reference/database/MANIFEST.toml:37) has `attribute_values = 170`. |
| Drift script gates only four block counts, not `attribute_values` | confirmed | [check_manifest_drift.sh](/srv/repos/external/verivus-oss/agent-assurance/validators/check_manifest_drift.sh:64) reads `template_kinds`, `entity_kinds`, `relation_predicates`, `attribute_vocabularies`; `rg -n attribute_values validators/check_manifest_drift.sh` has no matches. |
| Validators enforce closed vocabularies only | confirmed | Rust accepts unseen values when `extensible` is true at [main.rs](/srv/repos/external/verivus-oss/agent-assurance/tools/dagtoml-validate-rs/src/main.rs:537); Python does the same at [validate_disclosure.py](/srv/repos/external/verivus-oss/agent-assurance/validators/validate_disclosure.py:98). |
| Ontology counts are 41 vocabularies, 170 all values, 99 closed values | confirmed | Command output: `core: blocks=10 all=39 closed=22; agent-assurance: blocks=24 all=91 closed=51; cost: blocks=3 all=22 closed=22; disclosure: blocks=4 all=18 closed=4; TOTAL blocks=41 all=170 closed=99`. |
| Structural-analysis arithmetic errors | confirmed | [structural-analysis.md](/srv/repos/external/verivus-oss/agent-assurance/docs/reviews/2026-05-23-attribute-values-methodology/structural-analysis.md:60) says core `9/~24/22` and agent-assurance `24/~108/51`; actual is core `10/39/22`, agent-assurance `24/91/51`. The total row also says `41` even though its displayed block subtotals sum to `40`. |
| Zero code consumers of `[counts].attribute_values` | confirmed | `rg -n "attribute_values" validators tools --glob '*.py' --glob '*.rs' --glob '*.go' --glob '*.sh'` returned no matches. |
| Opus 8-surface table values from MANIFEST and DuckDB hardcodes | mostly confirmed | MANIFEST values are at [lines 33-37](/srv/repos/external/verivus-oss/agent-assurance/reference/database/MANIFEST.toml:33), [254](/srv/repos/external/verivus-oss/agent-assurance/reference/database/MANIFEST.toml:254), [264](/srv/repos/external/verivus-oss/agent-assurance/reference/database/MANIFEST.toml:264), [275](/srv/repos/external/verivus-oss/agent-assurance/reference/database/MANIFEST.toml:275), [285](/srv/repos/external/verivus-oss/agent-assurance/reference/database/MANIFEST.toml:285), [295](/srv/repos/external/verivus-oss/agent-assurance/reference/database/MANIFEST.toml:295). Rust hardcode is [main.rs](/srv/repos/external/verivus-oss/agent-assurance/tools/dagtoml-duckdb/src/main.rs:21); Go hardcode is [main.go](/srv/repos/external/verivus-oss/agent-assurance/tools/dagtoml-duckdb-go/main.go:40). |
| Opus actual seed row counts `74, 109, 109` | refuted_with_evidence | SQL-aware recount gives all three engines `kind/entity/relation/vocab/value = 20/27/31/41/106`. Inserts start at [postgres seed.sql](/srv/repos/external/verivus-oss/agent-assurance/reference/database/postgres/seed.sql:217), [sqlite seed.sql](/srv/repos/external/verivus-oss/agent-assurance/reference/database/sqlite/seed.sql:166), [duckdb seed.sql](/srv/repos/external/verivus-oss/agent-assurance/reference/database/duckdb/seed.sql:149). |
| `106 ≈ today’s sqlite/duckdb seed row count 109` | refuted_with_evidence | Today’s sqlite and duckdb `attribute_value_allowed` row count is `106`, not `109`. It is not approximate; it matches the previous manifest value exactly. |
| Historical `81 → 84 → 106 → 170` | confirmed | `git log -p -- reference/database/MANIFEST.toml` shows `81` introduced in `d91b15b`, changed to `84` in `bc2a7c5`, to `106` in `fccc1dc`, to `170` in `99e18db`. |
| Historical maintenance tracked seed rows | confirmed, stronger than Opus | Recounting blobs: `d91b15b`: manifest `81`, all seeds `81`; `bc2a7c5`: manifest `84`, all seeds `84`; `fccc1dc`: manifest `106`, all seeds `106`; `99e18db`: manifest `170`, all seeds still `106`. |
| Opus missed mirror surfaces | refuted_with_evidence | [MANIFEST.toml](/srv/repos/external/verivus-oss/agent-assurance/reference/database/MANIFEST.toml:276) also has `expected_triple_counts = { schema = 1100, shapes = 148 }`. `cargo run --quiet -p dagtoml-rdf --manifest-path tools/dagtoml-rdf/Cargo.toml -- verify -o reference/database/rdf/schema.ttl` reports `parsed 1291 triples`; shapes reports `148`. So `schema = 1100` is stale and omitted from Opus’s mirror table. |
| RDF footer counts are current | confirmed | `bash validators/check_manifest_drift.sh` reports RDF footer `20/27/31/41 == ontology`, matching [schema.ttl footer](/srv/repos/external/verivus-oss/agent-assurance/reference/database/rdf/schema.ttl:934). |
| Graph expected counts stale | confirmed, but Opus compared the wrong actual | [schema.cypher](/srv/repos/external/verivus-oss/agent-assurance/reference/database/graph/schema.cypher:89) contains `KindDescriptor=15`, [line 110](/srv/repos/external/verivus-oss/agent-assurance/reference/database/graph/schema.cypher:110) contains `EntityKind=23`, [line 146](/srv/repos/external/verivus-oss/agent-assurance/reference/database/graph/schema.cypher:146) contains `RelationPredicate=31`; MANIFEST expects `16/24/31`, while ontology is `20/27/31`. |

**2. Critique of the Recommendation**

§4.1 MANIFEST split: directionally correct, but incomplete. `attribute_values_declared = 170` and `attribute_values_closed = 99` are defensible names. I would keep them rather than `_total/_enforced`: “closed” maps directly to `extensible = false`, while “enforced” is a validator behavior claim. However, the historical third number is real: `attribute_value_allowed` seed rows are `106`. I would not add that as a third top-level `[counts].attribute_values_*` field; it belongs in the per-engine `expected_seed_counts.attribute_value_allowed`, which already exists and is stale.

§4.1 also misses [ontology_source](/srv/repos/external/verivus-oss/agent-assurance/reference/database/MANIFEST.toml:21): it names only `profiles/agent-assurance/ontology.toml`, while the counts include disclosure and cost profiles. The split should add a profile glob/list there.

§4.2 validator: correct for the two ontology aggregates, but it only closes the specific `170 vs 99` hole. It deliberately leaves `expected_seed_counts`, graph counts, RDF triple counts, and DuckDB hardcodes stale. Given Opus’s own evidence, that is too narrow for the same PR unless the PR is explicitly “attribute vocabulary count naming only.”

§4.3 wire-in: mechanically fine if inserted before the existing `fail` check at [check_manifest_drift.sh](/srv/repos/external/verivus-oss/agent-assurance/validators/check_manifest_drift.sh:87). Minor issue: Opus’s snippet includes the existing `report attribute_vocabularies` line as context; applying it literally could duplicate that report.

§4.4 SPEC paragraph: I would modify it. The phrase “union across every values array” is mathematically sloppy because the implementation counts `(attribute, value)` entries, not a deduplicated union. Also, SPEC §10 is about IJB conformance, while `MANIFEST.toml` declares itself non-normative at [lines 1-15](/srv/repos/external/verivus-oss/agent-assurance/reference/database/MANIFEST.toml:1). If the spec gets a normative rule, it should say: “reference manifests that publish attribute-value counts MUST name whether they are all declared values, closed-vocabulary values, or emitted `attribute_value_allowed` rows.”

The PR split is only partly honest. Deferring deletion of hardcoded DuckDB constants is acceptable. Deferring all stale manifest verification counts is can-kicking, because the historical source of the mistaken `attribute_values` field was exactly the seed-row mirror: `81/84/106` matched seeds until `99e18db`.

**3. What I Would Do Differently**

I would modify Opus’s patch:

1. Replace `[counts].attribute_values` with:
   - `attribute_values_declared = 170`
   - `attribute_values_closed = 99`

2. Update `[ontology_source]` to include all profile ontologies, preferably `profile_ontology_glob = "../../profiles/*/ontology.toml"`.

3. Add Opus’s ontology validator, but word it as counting `(attribute, value)` entries, not “union.”

4. In the same PR, fix and gate manifest verification counts:
   - postgres `expected_seed_counts = 20/27/31/41/106`
   - duckdb `expected_seed_counts = 20/27/31/41/106`
   - sqlite `expected_seed_counts = 20/27/31/41/106` with prefixed table names
   - graph `expected_node_counts = 15/23/31` if it is meant to describe current graph artifact, or regenerate graph to `20/27/31` and then set that
   - RDF `expected_triple_counts.schema = 1291`, `shapes = 148`, or remove/gate the field

5. Either update the DuckDB hardcodes to `20/27/31/41/106` immediately or delete them in the same follow-up commit. Leaving them at `19/26/30/37/81` while adding only the new validator preserves known rot.

**4. Decision Matrix**

| Option | What it buys | What it costs | Residual risk |
|---|---|---|---|
| Opus recommendation as written | Resolves `170 vs 99`; adds CI gate for both ontology aggregates | Leaves stale seed, graph, RDF triple, and DuckDB hardcode mirrors; SPEC wording uses “union” loosely | Same mirror-rot class persists immediately |
| Modified Opus: split + gate all manifest count mirrors | Resolves ambiguity and makes current manifest counts trustworthy | Slightly larger validator; must decide whether to regenerate graph or record current graph counts | DuckDB hardcodes still stale unless also changed |
| Modified Opus + remove/update DuckDB hardcodes | Best closure of the known count-mirror problem | Largest PR; touches tools as well as manifest/spec | Future duplicate mirrors still need discipline |
| Restore historical seed-row meaning only: `attribute_values = 106` | Matches actual historical maintenance and current seeds | Discards useful `170` and `99`; keeps ambiguous name | Future reviewers reopen same dispute |
| Delete `attribute_values` entirely | Removes ambiguous top-level field | Loses useful ontology surface documentation | Seed/graph/RDF mirror rot remains untouched |

**5. Bottom Line**

I would modify the Opus recommendation; the maintainer should split `attribute_values` into declared/closed counts, but bundle a manifest mirror-count cleanup/gate in the same PR and fix Opus’s incorrect seed-row evidence before relying on the report.
