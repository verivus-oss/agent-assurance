-- DAG-TOML reference Postgres schema (non-normative).
--
-- Derived from:
--   core/ontology.toml
--   profiles/agent-assurance/ontology.toml
--   core/*-kind.toml
--   profiles/agent-assurance/*-kind.toml
--   spec.md §§2, 5, 10, 11
--
-- Target: PostgreSQL 14+ (uses generated columns, JSONB, multirange-free).
-- Hybrid relational + JSONB. Closed vocabularies are enums; open
-- vocabularies are text + attribute_value_allowed.
--
-- Layout:
--   1. Schema setup
--   2. IJB primitive enums (spec.md §10)
--   3. Closed attribute-vocabulary enums (ontology: extensible=false)
--   4. Registry tables (kind/entity_kind/relation/attribute descriptors)
--   5. Instance tables (instance_file, provenance, entity, relation)
--   6. Indexes (graph traversal, single-producer invariant, FKs)
--   7. Convenience views (dag_unit, requirement_coverage, gate_status)
--   8. Invariant queries (cycle detection, single-producer, REQ: resolution)
--
-- Round-trip discipline: a TOML file ingested into this schema and
-- re-emitted MUST validate against validators/ in the repo root.


-- ============================================================
-- 1. Schema setup
-- ============================================================

CREATE SCHEMA IF NOT EXISTS dagtoml;
SET search_path TO dagtoml, public;


-- ============================================================
-- 2. IJB primitive enums (spec.md §10)
-- ============================================================

CREATE TYPE ijb_primitive AS ENUM (
    'thing',
    'scope',
    'path',
    'observed',
    'constraint',
    'time'
);

-- Used on entities and relations.
CREATE TYPE ijb_class AS ENUM (
    'structural',
    'instance'
);

-- Used on attribute vocabularies.
CREATE TYPE ijb_constraint_type AS ENUM (
    'structural',
    'policy',
    'observed'
);

-- Spec/profile layering.
-- spec_layer lists every published profile namespace. Add a new value
-- with `ALTER TYPE spec_layer ADD VALUE 'profile:<name>'` when shipping
-- a new profile.
CREATE TYPE spec_layer AS ENUM (
    'core',
    'profile:agent-assurance',
    'profile:disclosure',
    'profile:cost'
);


-- ============================================================
-- 3. Closed attribute-vocabulary enums
--    (Ontology vocabularies declared with extensible = false.)
-- ============================================================

-- core/ontology.toml
CREATE TYPE priority_level    AS ENUM ('must', 'should', 'could');
CREATE TYPE unit_status       AS ENUM ('pending', 'in_progress', 'done', 'blocked', 'deferred');
CREATE TYPE review_status     AS ENUM ('draft', 'blocked', 'ready', 'in_review', 'rereview_needed');

-- profiles/agent-assurance/ontology.toml (extensible = false subset)
CREATE TYPE risk_level        AS ENUM ('negligible', 'low', 'medium', 'high', 'critical');
CREATE TYPE residual_risk     AS ENUM ('accepted', 'mitigated', 'open');
CREATE TYPE smoke_decision    AS ENUM ('pass', 'fail', 'inconclusive');
CREATE TYPE gate_verdict      AS ENUM ('pass', 'fail');
CREATE TYPE severity_tier     AS ENUM ('info', 'low', 'medium', 'high', 'critical');
CREATE TYPE runtime_kind      AS ENUM ('wasi-component', 'oci-action', 'os-sandbox');
CREATE TYPE network_policy    AS ENUM ('denied', 'loopback-only', 'allowlist', 'open');
CREATE TYPE clock_policy      AS ENUM (
    'injected', 'source-date-epoch', 'monotonic-from-zero', 'host-wall-clock'
);
CREATE TYPE adapter_id_derivation AS ENUM ('content-hash', 'nonce', 'external');
CREATE TYPE adapter_ref_syntax    AS ENUM ('content-hash', 'name-version-pin');
-- override_decision_method is `extensible = true` in the profile ontology,
-- so it is stored as TEXT against attribute_value_allowed, not as an enum.
-- override_rule_operator is `extensible = false` so it is a real enum.
CREATE TYPE override_rule_op      AS ENUM ('=', '!=', '<', '<=', '>', '>=', 'IN', 'AND', 'OR');


-- ============================================================
-- 4. Registry tables (seed data lives in seed.sql)
-- ============================================================

-- One row per template_kind. 5 core + 9 profile + 1 meta = 15 rows
-- expected. The meta row is `kind-descriptor` itself — the template_kind
-- that every *-kind.toml file in the spec declares.
CREATE TABLE kind_descriptor (
    template_kind     TEXT PRIMARY KEY,
    layer             spec_layer NOT NULL,
    descriptor_path   TEXT NOT NULL,            -- path to the *-kind.toml
    requires_profile  TEXT,                     -- e.g., 'agent-assurance'
    notes             TEXT
);

-- One row per declared entity kind. 17 core + 6 profile = 23 rows expected.
-- id_prefix_pattern is a Python regex (e.g., 'REQ', 'U\d+[a-z]?', 'A\d+').
CREATE TABLE entity_kind_descriptor (
    entity_kind        TEXT PRIMARY KEY,
    id_prefix_pattern  TEXT NOT NULL,
    layer              spec_layer NOT NULL,
    defining_kind      TEXT NOT NULL REFERENCES kind_descriptor(template_kind),
    ijb_primitive      ijb_primitive NOT NULL,  -- 'thing' for all 23
    ijb_class          ijb_class     NOT NULL,  -- 'structural' for all 23
    description        TEXT
);

-- One row per relation predicate. 30 rows expected (one per [[relations]]
-- block in core/ontology.toml). Predicate names that appear more than
-- once in the ontology with different domain/range tuples are namespaced
-- as `<scope>:<predicate>` (currently only `contract:depends_on`,
-- `contract:supersedes`, `contract:verified_by`) so the PK on `predicate`
-- remains usable as the FK target from `relation`. Profile-introduced
-- predicates, if added in future, MUST be namespaced as
-- 'agent-assurance:<predicate>'.
CREATE TABLE relation_descriptor (
    predicate       TEXT PRIMARY KEY,
    domain          TEXT[] NOT NULL,            -- allowed source entity_kinds
    range           TEXT[] NOT NULL,            -- allowed target entity_kinds
    inverse_of      TEXT REFERENCES relation_descriptor(predicate),
    cardinality     INT,                        -- NULL = unbounded
    is_acyclic      BOOLEAN NOT NULL DEFAULT FALSE,
    target_freeform BOOLEAN NOT NULL DEFAULT FALSE,
    ijb_primitive   ijb_primitive NOT NULL,     -- 'path' for all
    ijb_class       ijb_class NOT NULL,         -- 'structural' for all
    layer           spec_layer NOT NULL,
    namespace       TEXT,                       -- e.g., 'agent-assurance'
    notes           TEXT
);

CREATE TABLE attribute_vocabulary (
    attribute              TEXT PRIMARY KEY,    -- e.g., 'priority', 'unit.status', 'trigger_kind'
    applies_to_entity      TEXT[],              -- entity_kinds it constrains (NULL = any)
    applies_to_template    TEXT[],              -- template_kinds it constrains (NULL = any)
    ijb_constraint_type    ijb_constraint_type NOT NULL,
    extensible             BOOLEAN NOT NULL,
    default_value          TEXT,
    layer                  spec_layer NOT NULL,
    backing_enum_type      TEXT                 -- e.g., 'priority_level' if mirrored as a PG enum
);

CREATE TABLE attribute_value_allowed (
    attribute   TEXT NOT NULL REFERENCES attribute_vocabulary(attribute),
    value       TEXT NOT NULL,
    PRIMARY KEY (attribute, value)
);


-- ============================================================
-- 5. Instance tables
-- ============================================================

-- Every TOML file ingested.
CREATE TABLE instance_file (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_path        TEXT NOT NULL,
    content_sha256     TEXT NOT NULL,                       -- 'sha256:<hex>'
    schema_version     TEXT NOT NULL,                       -- semver
    ontology_version   INT,                                 -- nullable; not all files declare it
    template_kind      TEXT NOT NULL REFERENCES kind_descriptor(template_kind),
    framework_profile  TEXT,                                -- 'agent-assurance' or NULL
    title              TEXT,
    docs_url           TEXT,
    created            DATE,                                -- TOML `created` field
    created_at         TIMESTAMPTZ,                         -- ISO 8601 if file uses it
    meta_extras        JSONB NOT NULL DEFAULT '{}'::jsonb,  -- everything else under [meta]
    ingested_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT instance_file_path_sha_unique UNIQUE (source_path, content_sha256),
    CONSTRAINT instance_file_profile_consistency CHECK (
        framework_profile IS NULL OR framework_profile IN ('agent-assurance', 'AGDF')
    )
);

CREATE INDEX instance_file_template_kind_idx ON instance_file (template_kind);
CREATE INDEX instance_file_profile_idx       ON instance_file (framework_profile);

-- spec.md §11. Optional [provenance] table.
CREATE TABLE provenance (
    instance_file_id    UUID PRIMARY KEY REFERENCES instance_file(id) ON DELETE CASCADE,
    source_path         TEXT NOT NULL,
    source_sha256       TEXT NOT NULL,                       -- 'sha256:<hex>'
    source_bytes        BIGINT NOT NULL,
    captured_at         TIMESTAMPTZ,                         -- advisory
    extraction_method   TEXT,                                -- advisory
    source_description  TEXT,                                -- advisory
    extras              JSONB NOT NULL DEFAULT '{}'::jsonb,

    CONSTRAINT provenance_sha_form CHECK (source_sha256 ~ '^sha256:[0-9a-f]{64}$'),
    CONSTRAINT provenance_bytes_nonneg CHECK (source_bytes >= 0)
);

-- One row per entity instance (REQ:foo, U1, ART:bundle, C5, etc.).
CREATE TABLE entity (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    qualified_id       TEXT NOT NULL,                       -- e.g., 'REQ:auth-001', 'U1', 'ART:x'
    prefix             TEXT NOT NULL,                       -- extracted prefix or full id for regex-keyed kinds
    entity_kind        TEXT NOT NULL REFERENCES entity_kind_descriptor(entity_kind),
    declared_in        UUID NOT NULL REFERENCES instance_file(id) ON DELETE CASCADE,
    ijb_primitive      ijb_primitive NOT NULL DEFAULT 'thing',
    ijb_class          ijb_class     NOT NULL DEFAULT 'instance',

    -- Promoted commonly-queried attributes; everything else lives in payload.
    -- NULL when not applicable to the entity_kind.
    priority           priority_level,                      -- REQ, REG
    unit_status        unit_status,                         -- units
    review_status      review_status,                       -- readiness-gate artifact_classes
    likelihood         risk_level,                          -- THREAT
    impact             risk_level,                          -- THREAT
    residual           residual_risk,                       -- THREAT
    smoke_status       smoke_decision,                      -- SMOKE / smoke-validation
    weight             NUMERIC,                             -- units (for critical-path)

    payload            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT entity_qualified_id_unique UNIQUE (qualified_id)
);

CREATE INDEX entity_kind_idx        ON entity (entity_kind);
CREATE INDEX entity_declared_in_idx ON entity (declared_in);
CREATE INDEX entity_payload_gin     ON entity USING GIN (payload jsonb_path_ops);

-- One row per asserted edge. Either target_entity_id or target_label is set.
-- target_label exists for predicates whose range is free-form
-- (relation_descriptor.target_freeform = TRUE), e.g. contract.verified_by,
-- contract.applies_to.
CREATE TABLE relation (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    predicate          TEXT NOT NULL REFERENCES relation_descriptor(predicate),
    source_entity_id   UUID NOT NULL REFERENCES entity(id) ON DELETE CASCADE,
    target_entity_id   UUID REFERENCES entity(id) ON DELETE CASCADE,
    target_label       TEXT,                                -- free-form target
    asserted_in        UUID NOT NULL REFERENCES instance_file(id) ON DELETE CASCADE,
    attrs              JSONB NOT NULL DEFAULT '{}'::jsonb,  -- edge attributes if any
    -- IJB tags on the edge row itself. All relation rows are
    -- (path, instance) — the descriptor row is (path, structural).
    ijb_primitive      ijb_primitive NOT NULL DEFAULT 'path',
    ijb_class          ijb_class     NOT NULL DEFAULT 'instance',
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT relation_target_exactly_one CHECK (
        (target_entity_id IS NOT NULL)::int + (target_label IS NOT NULL)::int = 1
    )
);

-- An edge is uniquely identified by (predicate, source, target) — duplicates
-- across files collapse into one row.
CREATE UNIQUE INDEX relation_typed_edge_unique
    ON relation (predicate, source_entity_id, target_entity_id)
    WHERE target_entity_id IS NOT NULL;

CREATE UNIQUE INDEX relation_freeform_edge_unique
    ON relation (predicate, source_entity_id, target_label)
    WHERE target_label IS NOT NULL;

CREATE INDEX relation_source_idx    ON relation (source_entity_id);
CREATE INDEX relation_target_idx    ON relation (target_entity_id);
CREATE INDEX relation_predicate_idx ON relation (predicate);


-- ============================================================
-- 6. Invariant: single producer per artifact (spec.md §5)
-- ============================================================
--
-- Each ART:<id> must have exactly one `produces` edge pointing TO it.
-- PostgreSQL forbids subqueries in partial-index predicates, so this
-- invariant CANNOT be expressed as a unique partial index that filters
-- by entity_kind. Implementers SHOULD enforce it via either:
--   (a) a deferred constraint trigger on `relation` that re-checks the
--       count when `predicate = 'produces'` and the target row's
--       entity_kind is 'artifact', or
--   (b) the post-ingestion invariant view in §8.2 below, run as a
--       gate step before the ingestion commits.
-- A naive unique partial index on (target_entity_id) WHERE predicate =
-- 'produces' would also reject legitimate non-artifact produces edges
-- (FEAT->OUT, units->OUT), so it is NOT included here.


-- ============================================================
-- 7. Convenience views
-- ============================================================

-- DAG units (implementation-dag).
CREATE OR REPLACE VIEW dag_unit AS
SELECT
    e.id,
    e.qualified_id        AS unit_id,
    e.declared_in,
    e.unit_status         AS status,
    e.weight,
    e.payload->>'title'   AS title,
    e.payload->>'tier'    AS tier,
    e.payload
FROM entity e
WHERE e.entity_kind = 'unit';

-- depends_on edges between units, projected as a graph.
CREATE OR REPLACE VIEW dag_edge AS
SELECT
    r.id            AS edge_id,
    s.qualified_id  AS from_unit,
    t.qualified_id  AS to_unit,
    s.weight        AS from_weight,
    t.weight        AS to_weight,
    r.asserted_in
FROM relation r
JOIN entity   s ON s.id = r.source_entity_id
JOIN entity   t ON t.id = r.target_entity_id
WHERE r.predicate = 'depends_on'
  AND s.entity_kind = 'unit'
  AND t.entity_kind = 'unit';

-- Requirement → test coverage (traceability).
CREATE OR REPLACE VIEW requirement_coverage AS
SELECT
    req.id                          AS requirement_id,
    req.qualified_id                AS requirement,
    req.priority,
    COUNT(DISTINCT t.id) FILTER (WHERE t.entity_kind = 'test') AS test_count,
    ARRAY_AGG(DISTINCT t.qualified_id)
        FILTER (WHERE t.entity_kind = 'test')                  AS verifying_tests
FROM entity req
LEFT JOIN relation r ON r.source_entity_id = req.id AND r.predicate = 'verified_by'
LEFT JOIN entity   t ON t.id = r.target_entity_id
WHERE req.entity_kind IN ('requirement', 'regulation')
GROUP BY req.id, req.qualified_id, req.priority;

-- Readiness-gate status per artifact_class.
CREATE OR REPLACE VIEW gate_status AS
SELECT
    ac.qualified_id           AS artifact_class,
    ac.review_status          AS status,
    g.qualified_id            AS gate_id,
    g.payload->>'description' AS gate_description,
    ac.declared_in
FROM entity ac
LEFT JOIN relation r ON r.target_entity_id = ac.id AND r.predicate = 'artifact_class'
LEFT JOIN entity   g ON g.id = r.source_entity_id  AND g.entity_kind = 'gate'
WHERE ac.entity_kind = 'artifact_class';


-- ============================================================
-- 8. Invariant queries (run post-ingestion or as scheduled checks)
-- ============================================================

-- 8.1 depends_on / blocks inverse symmetry (spec.md §5).
--     Every (a depends_on b) MUST have a matching (b blocks a).
--     Returns rows that violate.
CREATE OR REPLACE VIEW invariant_violations_depends_blocks AS
SELECT
    s.qualified_id AS missing_blocks_from,
    t.qualified_id AS missing_blocks_to
FROM relation d
JOIN entity   s ON s.id = d.source_entity_id
JOIN entity   t ON t.id = d.target_entity_id
WHERE d.predicate = 'depends_on'
  AND NOT EXISTS (
      SELECT 1 FROM relation b
      WHERE b.predicate = 'blocks'
        AND b.source_entity_id = d.target_entity_id
        AND b.target_entity_id = d.source_entity_id
  );

-- 8.2 Single producer per artifact (spec.md §5).
CREATE OR REPLACE VIEW invariant_violations_multi_producer AS
SELECT
    art.qualified_id        AS artifact,
    COUNT(*)                AS producer_count,
    ARRAY_AGG(src.qualified_id) AS producers
FROM relation r
JOIN entity art ON art.id = r.target_entity_id
JOIN entity src ON src.id = r.source_entity_id
WHERE r.predicate = 'produces'
  AND art.entity_kind = 'artifact'
GROUP BY art.id, art.qualified_id
HAVING COUNT(*) <> 1;

-- 8.3 depends_on cycle detection.
-- Table refs are schema-qualified because SQL functions run under the
-- caller's search_path; bare `entity` would fail when called from a
-- session that has not SET search_path TO dagtoml.
CREATE OR REPLACE FUNCTION dagtoml.find_depends_on_cycles()
RETURNS TABLE(cycle TEXT[]) LANGUAGE sql AS $$
    WITH RECURSIVE walk(start_id, current_id, path, has_cycle) AS (
        SELECT id, id, ARRAY[qualified_id], FALSE
        FROM dagtoml.entity
        WHERE entity_kind = 'unit'
        UNION ALL
        SELECT w.start_id,
               t.id,
               w.path || t.qualified_id,
               t.qualified_id = ANY(w.path)
        FROM walk w
        JOIN dagtoml.relation r ON r.source_entity_id = w.current_id AND r.predicate = 'depends_on'
        JOIN dagtoml.entity   t ON t.id = r.target_entity_id
        WHERE NOT w.has_cycle
    )
    SELECT DISTINCT path FROM walk WHERE has_cycle;
$$;

-- 8.4 Cross-document REQ: resolution.
--     Every entity referenced as a 'verified_by' / 'realizes' / etc. target
--     MUST resolve to an existing entity row.
CREATE OR REPLACE VIEW invariant_violations_unresolved_refs AS
SELECT
    src.qualified_id AS source,
    r.predicate,
    r.target_label   AS unresolved_target
FROM relation r
JOIN entity   src ON src.id = r.source_entity_id
JOIN relation_descriptor rd ON rd.predicate = r.predicate
WHERE r.target_entity_id IS NULL
  AND r.target_label IS NOT NULL
  AND rd.target_freeform = FALSE;
