// DAG-TOML reference property-graph schema (non-normative).
//
// Derived from:
//   core/ontology.toml
//   profiles/agent-assurance/ontology.toml
//   core/*-kind.toml
//   profiles/agent-assurance/*-kind.toml
//   spec.md §§5, 10, 11
//
// Target: Neo4j 5.x Cypher syntax (also valid on Memgraph and most
// openCypher implementations). Nothing here is conformance-required;
// implementers MAY adopt a different node/edge model and still produce
// a spec-compliant runtime.
//
// Modelling choices:
//   * Every entity carries an :Entity base label plus a kind-specific
//     label (:Requirement, :Unit, etc.). This lets cross-kind queries
//     run against (:Entity) while kind-specific queries stay typed.
//   * Every entity carries an :IjbThing label (all 27 entity kinds are
//     IJB primitive 'thing': 17 core + 6 agent-assurance + 3 disclosure
//     + 1 cost). Edges carry an
//     ijb_primitive='path' tag in their properties — Cypher relationship-
//     type labels can't be queried alongside a structural marker without
//     an extra hop, so it lives in properties.
//   * Instance files are first-class :InstanceFile nodes; each entity
//     has a [:DECLARED_IN] edge to the file that introduced it, and
//     each relation row carries an `asserted_in` property pointing at
//     the file that asserted the edge.
//   * Free-form relation targets (e.g., contract.verified_by =
//     "adapter-contract:authority-check@1") become :FreeFormTarget
//     nodes so traversals work uniformly.
//   * Relationship *types* follow Neo4j convention — UPPER_SNAKE_CASE
//     (`:DEPENDS_ON`, `:VERIFIED_BY`). The canonical ontology predicate
//     string is ALSO stored as `r.predicate` on every edge in its
//     lowercase, optionally namespaced form (`depends_on`, `verified_by`,
//     `contract:verified_by`). Use `r.predicate` — NOT `type(r)` — when
//     cross-referencing :RelationPredicate. This lets the contract-
//     scoped predicates (e.g. `contract:verified_by`) coexist with the
//     core variant on the same relationship type.
//
// Layout:
//   1. Constraints and indexes
//   2. Seed :InstanceFile, :KindDescriptor, :EntityKind, :RelationPredicate
//   3. Example ingestion MERGEs
//   4. Invariant queries (single-producer, depends_on/blocks symmetry, cycles)
//   5. Convenience traversals (critical path, requirement coverage)


// ============================================================
// 1. Constraints and indexes
// ============================================================

CREATE CONSTRAINT entity_qualified_id IF NOT EXISTS
    FOR (e:Entity) REQUIRE e.qualified_id IS UNIQUE;

CREATE CONSTRAINT instance_file_sha IF NOT EXISTS
    FOR (f:InstanceFile) REQUIRE (f.source_path, f.content_sha256) IS UNIQUE;

CREATE CONSTRAINT kind_descriptor_pk IF NOT EXISTS
    FOR (k:KindDescriptor) REQUIRE k.template_kind IS UNIQUE;

CREATE CONSTRAINT entity_kind_pk IF NOT EXISTS
    FOR (k:EntityKind) REQUIRE k.entity_kind IS UNIQUE;

CREATE CONSTRAINT relation_predicate_pk IF NOT EXISTS
    FOR (p:RelationPredicate) REQUIRE p.predicate IS UNIQUE;

// :FreeFormTarget nodes back free-form relation targets (predicates
// whose ontology range is `unconstrained_label`, e.g. contract.applies_to
// and contract.verified_by). Query 4.4 traverses these to flag
// references that point at free-form labels via a predicate that is NOT
// declared free-form.
CREATE CONSTRAINT freeform_target_label IF NOT EXISTS
    FOR (f:FreeFormTarget) REQUIRE f.label IS UNIQUE;

CREATE INDEX entity_kind_idx IF NOT EXISTS
    FOR (e:Entity) ON (e.entity_kind);

CREATE INDEX instance_file_template_kind_idx IF NOT EXISTS
    FOR (f:InstanceFile) ON (f.template_kind);


// ============================================================
// 2. Registry seed
//    (Snapshot of the ontology declarations; regenerate from
//     core/ontology.toml + every profiles/<name>/ontology.toml.)
// ============================================================

// Template kinds. The ontology declares 23 (6 core + 9 agent-assurance
// + 3 disclosure + 1 cost + 3 com.verivus.runtime + 1 meta). That total is
// prose; `MANIFEST.toml [counts].template_kinds` is the gated source of
// truth, re-derived from core/*-kind.toml and profiles/*/*-kind.toml by
// `validators/check_manifest_drift.sh` on every push.
//
// The UNWIND data below lists 15. These eight declared kinds are absent
// from this seed:
//     profile-descriptor          core
//     disclosure-attestation      profile:disclosure
//     redaction-manifest          profile:disclosure
//     selective-disclosure-proof  profile:disclosure
//     cost-record                 profile:cost
//     api-snapshot                profile:com.verivus.runtime
//     state-mutation              profile:com.verivus.runtime
//     mutation-claim              profile:com.verivus.runtime
//
// Tracked as ISS-002
// (docs/issues/2026-05-23-iss-002-graph-cypher-seed-incomplete.md).
// The gap is invisible to CI by construction: check_attribute_values.py
// compares MANIFEST.toml's expected_node_counts against the ontology, never
// against these UNWIND rows. A green build is not evidence that this seed
// is current. These comments have themselves gone stale twice while the
// data stood still, which is why ISS-002 Safeguard A (a row-count gate on
// this file) is the fix rather than another comment.
UNWIND [
    {template_kind: 'kind-descriptor',          layer: 'core'},
    {template_kind: 'implementation-dag',       layer: 'core'},
    {template_kind: 'traceability',             layer: 'core'},
    {template_kind: 'readiness-gate',           layer: 'core'},
    {template_kind: 'contract-declaration',     layer: 'core'},
    {template_kind: 'evidence-matrix',          layer: 'core'},
    {template_kind: 'spec-contract',            layer: 'profile:agent-assurance'},
    {template_kind: 'threat-model',             layer: 'profile:agent-assurance'},
    {template_kind: 'smoke-validation',         layer: 'profile:agent-assurance'},
    {template_kind: 'rollback-plan',            layer: 'profile:agent-assurance'},
    {template_kind: 'adapter-contract',         layer: 'profile:agent-assurance'},
    {template_kind: 'adapter-registry-binding', layer: 'profile:agent-assurance'},
    {template_kind: 'assertion-bundle',         layer: 'profile:agent-assurance'},
    {template_kind: 'assertion-log-record',     layer: 'profile:agent-assurance'},
    {template_kind: 'gate-decision',            layer: 'profile:agent-assurance'}
] AS row
MERGE (k:KindDescriptor {template_kind: row.template_kind})
SET k.layer = row.layer;

// Entity kinds. The ontology declares 27 (17 core + 6 agent-assurance
// + 3 disclosure + 1 cost); `MANIFEST.toml [counts].entity_kinds` is the
// gated source of truth. The UNWIND data below lists 23. These four
// declared entity kinds are absent from this seed:
//     disclosure_attestation      DISC   profile:disclosure
//     redaction                   RED    profile:disclosure
//     selective_disclosure_proof  SDP    profile:disclosure
//     cost_record                 COST   profile:cost
// profiles/com.verivus.runtime declares no entity kinds, so it adds none
// here. Same tracking issue as the template-kind gap above (ISS-002).
UNWIND [
    {entity_kind: 'intent',           id_prefix: 'INT',         layer: 'core'},
    {entity_kind: 'feature',          id_prefix: 'FEAT',        layer: 'core'},
    {entity_kind: 'requirement',      id_prefix: 'REQ',         layer: 'core'},
    {entity_kind: 'regulation',       id_prefix: 'REG',         layer: 'core'},
    {entity_kind: 'decision',         id_prefix: 'DEC',         layer: 'core'},
    {entity_kind: 'implementation',   id_prefix: 'IMP',         layer: 'core'},
    {entity_kind: 'code',             id_prefix: 'CODE',        layer: 'core'},
    {entity_kind: 'test',             id_prefix: 'TEST',        layer: 'core'},
    {entity_kind: 'output',           id_prefix: 'OUT',         layer: 'core'},
    {entity_kind: 'unit',             id_prefix: 'U\\d+[a-z]?', layer: 'core'},
    {entity_kind: 'artifact',         id_prefix: 'ART',         layer: 'core'},
    {entity_kind: 'artifact_class',   id_prefix: 'A\\d+',       layer: 'core'},
    {entity_kind: 'gate',             id_prefix: 'G\\d+',       layer: 'core'},
    {entity_kind: 'contract',         id_prefix: 'C\\d+',       layer: 'core'},
    {entity_kind: 'claim',            id_prefix: 'E\\d+',       layer: 'core'},
    {entity_kind: 'evidence',         id_prefix: 'EV\\d+',      layer: 'core'},
    {entity_kind: 'matrix',           id_prefix: 'M\\d+',       layer: 'core'},
    {entity_kind: 'guarantee',        id_prefix: 'GUAR',        layer: 'profile:agent-assurance'},
    {entity_kind: 'invariant',        id_prefix: 'INV',         layer: 'profile:agent-assurance'},
    {entity_kind: 'non_goal',         id_prefix: 'NG',          layer: 'profile:agent-assurance'},
    {entity_kind: 'threat',           id_prefix: 'THREAT',      layer: 'profile:agent-assurance'},
    {entity_kind: 'smoke_check',      id_prefix: 'SMOKE',       layer: 'profile:agent-assurance'},
    {entity_kind: 'rollback_trigger', id_prefix: 'TRIG',        layer: 'profile:agent-assurance'}
] AS row
MERGE (k:EntityKind {entity_kind: row.entity_kind})
SET k.id_prefix_pattern = row.id_prefix,
    k.layer             = row.layer,
    k.ijb_primitive     = 'thing',
    k.ijb_class         = 'structural';

// Relation predicates. The ontology declares 31 (30 plus the SPEC §12
// `cites_upstream` predicate); `MANIFEST.toml [counts].relation_predicates`
// is the gated source of truth. The UNWIND data below lists all 31, so
// this block is at parity with the ontology.
// One per [[relations]] block in
// core/ontology.toml). Predicate names that appear more than once in
// the ontology with different domain/range tuples are namespaced as
// `<scope>:<predicate>` so the constraint on RelationPredicate.predicate
// uniqueness holds.
UNWIND [
    {predicate: 'derived_from',         inverse_of: null,             cardinality: null, acyclic: false, target_freeform: false},
    {predicate: 'realized_by',          inverse_of: 'realizes',       cardinality: null, acyclic: false, target_freeform: false},
    {predicate: 'realizes',             inverse_of: 'realized_by',    cardinality: null, acyclic: false, target_freeform: false},
    {predicate: 'constrained_by',       inverse_of: 'constrains',     cardinality: null, acyclic: false, target_freeform: false},
    {predicate: 'implemented_by',       inverse_of: 'implements',     cardinality: null, acyclic: false, target_freeform: false},
    {predicate: 'produces',             inverse_of: null,             cardinality: null, acyclic: false, target_freeform: false},
    {predicate: 'constrains',           inverse_of: 'constrained_by', cardinality: null, acyclic: false, target_freeform: false},
    {predicate: 'verified_by',          inverse_of: 'verifies',       cardinality: null, acyclic: false, target_freeform: false},
    {predicate: 'addresses',            inverse_of: null,             cardinality: null, acyclic: false, target_freeform: false},
    {predicate: 'shapes',               inverse_of: null,             cardinality: null, acyclic: false, target_freeform: false},
    {predicate: 'supersedes',           inverse_of: null,             cardinality: null, acyclic: true,  target_freeform: false},
    {predicate: 'implements',           inverse_of: 'implemented_by', cardinality: null, acyclic: false, target_freeform: false},
    {predicate: 'guided_by',            inverse_of: null,             cardinality: null, acyclic: false, target_freeform: false},
    {predicate: 'code',                 inverse_of: null,             cardinality: null, acyclic: false, target_freeform: false},
    {predicate: 'tests',                inverse_of: null,             cardinality: null, acyclic: false, target_freeform: false},
    {predicate: 'downstream_outputs',   inverse_of: null,             cardinality: null, acyclic: false, target_freeform: false},
    {predicate: 'verifies',             inverse_of: 'verified_by',    cardinality: null, acyclic: false, target_freeform: false},
    {predicate: 'depends_on',           inverse_of: 'blocks',         cardinality: null, acyclic: true,  target_freeform: false},
    {predicate: 'blocks',               inverse_of: 'depends_on',     cardinality: null, acyclic: true,  target_freeform: false},
    {predicate: 'consumes',             inverse_of: null,             cardinality: null, acyclic: false, target_freeform: false},
    {predicate: 'artifact_class',       inverse_of: null,             cardinality: 1,    acyclic: false, target_freeform: false},
    {predicate: 'contract:depends_on',  inverse_of: null,             cardinality: null, acyclic: true,  target_freeform: false},
    {predicate: 'contract:supersedes',  inverse_of: null,             cardinality: null, acyclic: true,  target_freeform: false},
    {predicate: 'related_to',           inverse_of: null,             cardinality: null, acyclic: false, target_freeform: false},
    {predicate: 'applies_to',           inverse_of: null,             cardinality: null, acyclic: false, target_freeform: true},
    {predicate: 'contract:verified_by', inverse_of: null,             cardinality: null, acyclic: false, target_freeform: true},
    {predicate: 'claim',                inverse_of: null,             cardinality: 1,    acyclic: false, target_freeform: false},
    {predicate: 'claim_id',             inverse_of: null,             cardinality: 1,    acyclic: false, target_freeform: false},
    {predicate: 'evidence',             inverse_of: null,             cardinality: 1,    acyclic: false, target_freeform: false},
    {predicate: 'evidence_id',          inverse_of: null,             cardinality: 1,    acyclic: false, target_freeform: false},
    // SPEC §12 closure-root marker — applies to every conforming kind.
    {predicate: 'cites_upstream',       inverse_of: null,             cardinality: null, acyclic: true,  target_freeform: true}
] AS row
MERGE (p:RelationPredicate {predicate: row.predicate})
SET p.inverse_of      = row.inverse_of,
    p.cardinality     = row.cardinality,
    p.acyclic         = row.acyclic,
    p.target_freeform = row.target_freeform,
    p.ijb_primitive   = 'path',
    p.ijb_class       = 'structural';


// ============================================================
// 3. Example ingestion MERGEs
//    Pattern an ingestion tool would emit per TOML file.
// ============================================================

// Per file:
//   MERGE (f:InstanceFile {source_path: $path, content_sha256: $sha})
//   SET f.template_kind = $template_kind,
//       f.schema_version = $schema_version,
//       f.ontology_version = $ontology_version,
//       f.framework_profile = $framework_profile,
//       f.title = $title;
//
// Per entity declared in that file:
//   MERGE (e:Entity {qualified_id: $qid})
//   SET e.entity_kind = $entity_kind,
//       e.ijb_primitive = 'thing',
//       e.ijb_class = 'instance',
//       e.payload = $payload  // map of kind-specific fields
//   WITH e MATCH (f:InstanceFile {source_path: $path, content_sha256: $sha})
//   MERGE (e)-[:DECLARED_IN]->(f);
//   // Apply kind label:
//   CALL apoc.create.addLabels(e, [$kind_label]) YIELD node RETURN node;
//
// Per relation asserted in that file. Note: r.predicate carries the
// canonical lowercase predicate string from the ontology — it is the
// authoritative cross-reference into :RelationPredicate. type(r) is the
// uppercase Neo4j relationship type for human readability and idiomatic
// traversals.
//   MATCH (s:Entity {qualified_id: $source_qid}), (t:Entity {qualified_id: $target_qid})
//   MATCH (f:InstanceFile {source_path: $path, content_sha256: $sha})
//   MERGE (s)-[r:DEPENDS_ON {asserted_in_path: f.source_path}]->(t)
//   SET r.predicate     = 'depends_on',
//       r.ijb_primitive = 'path',
//       r.ijb_class     = 'instance';


// ============================================================
// 4. Invariant queries
// ============================================================

// 4.1 depends_on / blocks symmetry (spec.md §5).
// Returns pairs where depends_on exists without matching blocks.
MATCH (s:Entity)-[:DEPENDS_ON]->(t:Entity)
WHERE NOT (t)-[:BLOCKS]->(s)
RETURN s.qualified_id AS missing_blocks_from,
       t.qualified_id AS missing_blocks_to;

// 4.2 Single producer per artifact (spec.md §5).
// Each :Artifact must have exactly one inbound :PRODUCES.
MATCH (a:Entity)
WHERE a.entity_kind = 'artifact'
OPTIONAL MATCH (src)-[:PRODUCES]->(a)
WITH a, count(src) AS producers, collect(src.qualified_id) AS producer_ids
WHERE producers <> 1
RETURN a.qualified_id AS artifact, producers, producer_ids;

// 4.3 depends_on cycle detection.
MATCH path = (u:Entity {entity_kind: 'unit'})-[:DEPENDS_ON*1..]->(u)
RETURN [n IN nodes(path) | n.qualified_id] AS cycle
LIMIT 50;

// 4.4 Unresolved cross-document references.
// Edges that point at a :FreeFormTarget node via a predicate that the
// ontology does NOT declare free-form. Returns the offending source +
// predicate + label so the ingestor can decide whether the target needs
// to be promoted to a real :Entity. Uses `r.predicate` (canonical
// lowercase, populated by ingestion per the modelling note above), NOT
// `type(r)`, so contract-scoped predicates like `contract:verified_by`
// resolve correctly.
MATCH (s:Entity)-[r]->(t:FreeFormTarget)
MATCH (p:RelationPredicate {predicate: r.predicate})
WHERE p.target_freeform = false
RETURN s.qualified_id AS source, r.predicate AS predicate, t.label AS unresolved_target;


// ============================================================
// 5. Convenience traversals
// ============================================================

// 5.1 Critical path: longest weighted depends_on chain among units.
//     Requires `weight` populated on :Unit nodes from the implementation-dag
//     `[computed]` table or per-unit `weight` field.
MATCH path = (start:Entity {entity_kind: 'unit'})-[:DEPENDS_ON*]->(end:Entity {entity_kind: 'unit'})
WHERE NOT ()-[:DEPENDS_ON]->(start)
  AND NOT (end)-[:DEPENDS_ON]->()
WITH path, reduce(w = 0, n IN nodes(path) | w + coalesce(n.weight, 1)) AS total_weight
RETURN [n IN nodes(path) | n.qualified_id] AS unit_chain, total_weight
ORDER BY total_weight DESC
LIMIT 1;

// 5.2 Requirement coverage.
//     REQ/REG entities and the tests that verify them.
MATCH (req:Entity)
WHERE req.entity_kind IN ['requirement', 'regulation']
OPTIONAL MATCH (req)-[:VERIFIED_BY]->(t:Entity {entity_kind: 'test'})
RETURN req.qualified_id  AS requirement,
       req.priority      AS priority,
       count(t)          AS test_count,
       collect(t.qualified_id) AS verifying_tests
ORDER BY test_count ASC;

// 5.3 Readiness gate status per artifact_class.
MATCH (ac:Entity {entity_kind: 'artifact_class'})
OPTIONAL MATCH (g:Entity {entity_kind: 'gate'})-[:ARTIFACT_CLASS]->(ac)
RETURN ac.qualified_id AS artifact_class,
       ac.review_status AS status,
       g.qualified_id   AS gate_id;

// 5.4 Threat surface for all features.
//     Walks from each :Feature through any :IMPLEMENTS edges to find
//     :Threat entities declared in the same change set. In practice the
//     ingestor would constrain this by feature qualified_id; this form
//     loads cleanly under cypher-shell without bound parameters.
MATCH (f:Entity {entity_kind: 'feature'})
OPTIONAL MATCH (f)<-[:IMPLEMENTS]-(imp:Entity)
OPTIONAL MATCH (imp)-[:DECLARED_IN]->(file:InstanceFile)<-[:DECLARED_IN]-(th:Entity {entity_kind: 'threat'})
RETURN f.qualified_id AS feature,
       collect(DISTINCT {threat: th.qualified_id,
                         likelihood: th.likelihood,
                         impact: th.impact,
                         residual_risk: th.residual_risk}) AS threats;
