# Reference database schema

**Status:** Non-normative. Informative guidance for implementers who want
to ingest DAG-TOML instances into a database. Nothing in this directory
is a conformance requirement for DAG-TOML or the Agent Assurance Profile;
a runtime MAY persist data however it likes, including not at all.

This directory exists because two independent implementer questions kept
recurring:

1. *"If I want to query a corpus of DAG-TOML files relationally, what
   tables would I create?"* — answered by [`postgres/schema.sql`](postgres/schema.sql).
2. *"My system already speaks property-graph; what do the nodes and edges
   look like?"* — answered by [`graph/schema.cypher`](graph/schema.cypher).

Both schemas are **derived from** the ontology files (`core/ontology.toml`,
`profiles/agent-assurance/ontology.toml`) and the `*-kind.toml` descriptors
in `core/` and `profiles/agent-assurance/`. They are not parallel
vocabulary — every table, enum, column, node label, and relationship type
traces back to a declaration in the spec, and the ontology files remain
the source of truth.

## Design principles

1. **IJB-grounded.** The six IJB primitives (`thing | scope | path |
   observed | constraint | time`) and their class markers (`structural |
   instance`; for attribute vocabularies, `structural | policy | observed`)
   are first-class enums. Every entity row and edge row records its IJB
   tags so consumers can filter by primitive without re-reading the
   ontology.

2. **Hybrid relational + JSONB.** Cross-kind structure (instance files,
   entities, relations, attribute vocabularies, provenance) is modelled
   as proper tables. Kind-specific payload — fields that vary per
   `template_kind` and add no graph-traversal value — lives in a
   `payload JSONB` column on the entity row. This keeps the schema small
   and stable across the 14 kinds without losing data fidelity. Promote
   a JSONB field to a generated column when an index would help.

3. **Open at the edges where the spec is open.** `requirement_kind`,
   `test_kind`, `trigger_kind`, and the policy/algorithm vocabularies
   marked `extensible = true` in the ontology are stored as `text` with
   a CHECK against `attribute_value_allowed` rather than as PostgreSQL
   enums. Vocabularies marked `extensible = false` (`priority`,
   `unit.status`, `review.status`, `likelihood`, `impact`,
   `residual_risk`, etc.) are real enums.

4. **Spec invariants surface as DB constraints where cheap, and as
   queryable views where not.** `relation_descriptor` carries an
   `is_acyclic` flag inherited from the ontology; cycle checks for
   `depends_on` run as a recursive CTE inside the `find_depends_on_cycles()`
   function. Single-producer-per-artifact (`spec.md §5`) is NOT a unique
   partial index — Postgres forbids subqueries in partial-index
   predicates, and a naive index on `target_entity_id WHERE predicate =
   'produces'` would over-reject legitimate non-artifact `produces`
   edges (FEAT→OUT, units→OUT). It is enforced post-ingestion via the
   `invariant_violations_multi_producer` view (or, in a stricter
   deployment, a deferred constraint trigger). Cross-document `REQ:`
   resolution is likewise enforced as a post-ingestion view
   (`invariant_violations_unresolved_refs`), not a deferred FK — TOML
   files are ingested in unconstrained order, so we cannot rely on
   producer-rows existing before consumer-rows.

5. **Two-version pin preserved.** Every `instance_file` row carries both
   `schema_version` (semver, file shape) and `ontology_version` (integer,
   relation vocabulary). They bump independently — see `core/ontology.md
   §1`.

## What's modelled and what isn't

**In:** all 15 template kinds (5 core + 9 profile + the meta
`kind-descriptor` template kind that every `*-kind.toml` file declares),
all 23 entity kinds (17 core + 6 profile), all 30 core relation
predicates (with `contract:`-namespaced variants for predicate names
the ontology declares more than once with different domain/range
tuples — `contract:depends_on`, `contract:supersedes`,
`contract:verified_by`), all 29 attribute vocabularies (5 core + 24
profile), the optional `[provenance]` table (spec.md §11), and the
universal `[meta]` shape.

**Out:** runtime concerns (queues, gate-decision signature verification,
adapter-registry trust-anchor resolution, evidence-bundle Merkle
recomputation). These belong to a runtime; this schema only needs to
*store* the data they produce or consume.

## Ingestion model

A reference ingestion path:

1. Parse `*.toml` → write one `instance_file` row with `[meta]` fields,
   `provenance` row if present.
2. Walk each top-level table of the parsed TOML. For arrays like
   `[[requirements]]`, `[[units]]`, `[[contracts]]`, etc., insert one
   `entity` row per element, populating `qualified_id` from the
   element's `id` (or for `units`, from its element index per the
   `implementation-dag` kind's identifier rules).
3. Walk each relation-bearing field (`depends_on`, `blocks`,
   `verified_by`, `produces`, `consumes`, …) and insert one `relation`
   row per source/target pair. Free-form targets (e.g.,
   `contract.verified_by = "adapter-contract:authority-check@1"`) go to
   `relation.target_label` with `target_entity_id` left null.
4. Run the post-ingestion invariant checks listed in
   [`postgres/schema.sql`](postgres/schema.sql) (§ "Invariant queries").

## Seeding

Both schemas ship seed data that mirrors the ontology declarations
(entity kinds, relation predicates, attribute vocabularies, allowed
values). A reference loader would generate the seed inserts from
`core/ontology.toml` and `profiles/agent-assurance/ontology.toml` at
build time so the schema never drifts from the spec. The seed snippets
in `postgres/seed.sql` and the `MERGE` blocks at the bottom of
`graph/schema.cypher` are checked-in *examples* of what such a loader
would emit — they are intentionally a snapshot, not a substitute for
the loader.

## Files

```
reference/database/
├── README.md                        ← human entry point (this file)
├── MANIFEST.toml                    ← machine-readable companion: paths,
│                                       counts, targets, namespaced
│                                       predicates, verification commands
├── postgres/
│   ├── schema.sql                   ← PG enums, tables, indexes, views, cycle-detection function
│   └── seed.sql                     ← ontology-derived reference data
├── sqlite/
│   ├── schema.sql                   ← SQLite/libSQL STRICT tables, CHECK lists, json1, views
│   └── seed.sql                     ← same registry data, json_array() for arrays
├── duckdb/
│   ├── schema.sql                   ← DuckDB native ENUMs + LIST<T> arrays, port of the PG schema
│   └── seed.sql                     ← same data, ['a','b'] array literals
├── rdf/
│   ├── schema.ttl                   ← ontology as RDF/Turtle (generated by tools/dagtoml-rdf)
│   └── shapes.ttl                   ← SHACL shapes encoding the graph-shaped IJB invariants
└── graph/
    └── schema.cypher                ← Neo4j constraints, indexes, seed MERGEs, sample queries
```

Agents and ingestion tools should prefer `MANIFEST.toml` for discovery
(paths, counts, target versions, expected node/row counts after load)
and fall back to this README only for human-readable design rationale.

## Relation to validators

The validators under `validators/` enforce the same invariants this
schema models — they read TOML files; this schema stores the parsed
results. A round-trip test (parse → ingest → re-emit → validate) is the
strongest conformance evidence an implementer can produce, but it is
not part of CI for this repo (this repo only validates the source TOML).
