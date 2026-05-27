-- DAG-TOML reference DuckDB schema (non-normative).
--
-- DuckDB sits between PostgreSQL and SQLite in expressive power:
--   * native ENUM types (PG-style — CREATE TYPE x AS ENUM (...))
--   * native LIST<T> arrays (no JSON encoding needed for domain/range)
--   * native UUID, JSON, TIMESTAMPTZ
--   * recursive CTEs
--   * no GIN-style JSON indexes; no stored functions in the PG sense
--     (use macros + views; recursive CTE wrapped in a view for cycle
--     detection, same as the SQLite reference)
--
-- This file is a PORT of reference/database/postgres/schema.sql adapted
-- to DuckDB's type system. The translation table:
--   PG                                      DuckDB
--   --                                      ------
--   JSONB                                   JSON
--   UUID DEFAULT gen_random_uuid()          UUID DEFAULT uuid()
--   text[]                                  VARCHAR[]
--   TIMESTAMPTZ DEFAULT now()               TIMESTAMPTZ DEFAULT now()
--   CREATE OR REPLACE FUNCTION              CREATE OR REPLACE MACRO (table-returning)
--   GIN index on jsonb_path_ops             (omitted — DuckDB rewrites scans)
--   CREATE SCHEMA … SET search_path TO …    same, supported
--
-- Verified against duckdb v1.5+ (Variegata). Loads with
--   duckdb dagtoml.duckdb < schema.sql
-- then seed.sql in the same session.

CREATE SCHEMA IF NOT EXISTS dagtoml;
SET search_path = dagtoml;


-- ============================================================
-- 1. IJB primitive enums (spec.md §10)
-- ============================================================

CREATE TYPE ijb_primitive AS ENUM (
    'thing', 'scope', 'path', 'observed', 'constraint', 'time'
);
CREATE TYPE ijb_class      AS ENUM ('structural', 'instance');
CREATE TYPE ijb_constraint_type AS ENUM ('structural', 'policy', 'observed');
CREATE TYPE spec_layer     AS ENUM ('core', 'profile:agent-assurance', 'profile:disclosure', 'profile:cost');


-- ============================================================
-- 2. Closed attribute-vocabulary enums (ontology extensible = false)
-- ============================================================

CREATE TYPE priority_level    AS ENUM ('must', 'should', 'could');
CREATE TYPE unit_status       AS ENUM ('pending', 'in_progress', 'done', 'blocked', 'deferred');
CREATE TYPE review_status     AS ENUM ('draft', 'blocked', 'ready', 'in_review', 'rereview_needed');
CREATE TYPE risk_level        AS ENUM ('negligible', 'low', 'medium', 'high', 'critical');
CREATE TYPE residual_risk     AS ENUM ('accepted', 'mitigated', 'open');
CREATE TYPE smoke_decision    AS ENUM ('pass', 'fail', 'inconclusive');
CREATE TYPE gate_verdict      AS ENUM ('pass', 'fail');
CREATE TYPE severity_tier     AS ENUM ('info', 'low', 'medium', 'high', 'critical');
CREATE TYPE runtime_kind      AS ENUM ('wasi-component', 'oci-action', 'os-sandbox');
CREATE TYPE network_policy    AS ENUM ('denied', 'loopback-only', 'allowlist', 'open');
CREATE TYPE clock_policy      AS ENUM ('injected', 'source-date-epoch', 'monotonic-from-zero', 'host-wall-clock');
CREATE TYPE adapter_id_derivation AS ENUM ('content-hash', 'nonce', 'external');
CREATE TYPE adapter_ref_syntax    AS ENUM ('content-hash', 'name-version-pin');
CREATE TYPE override_rule_op  AS ENUM ('=', '!=', '<', '<=', '>', '>=', 'IN', 'AND', 'OR');


-- ============================================================
-- 3. Registry tables
-- ============================================================

CREATE TABLE dagtoml.kind_descriptor (
    template_kind     VARCHAR PRIMARY KEY,
    layer             spec_layer NOT NULL,
    descriptor_path   VARCHAR NOT NULL,
    requires_profile  VARCHAR,
    notes             VARCHAR
);

CREATE TABLE dagtoml.entity_kind_descriptor (
    entity_kind        VARCHAR PRIMARY KEY,
    id_prefix_pattern  VARCHAR NOT NULL,
    layer              spec_layer NOT NULL,
    defining_kind      VARCHAR NOT NULL REFERENCES dagtoml.kind_descriptor(template_kind),
    ijb_primitive      ijb_primitive NOT NULL,
    ijb_class          ijb_class     NOT NULL,
    description        VARCHAR
);

CREATE TABLE dagtoml.relation_descriptor (
    predicate       VARCHAR PRIMARY KEY,
    domain          VARCHAR[] NOT NULL,
    range           VARCHAR[] NOT NULL,
    inverse_of      VARCHAR,                  -- soft FK; many predicates have no inverse
    cardinality     INTEGER,
    is_acyclic      BOOLEAN NOT NULL DEFAULT FALSE,
    target_freeform BOOLEAN NOT NULL DEFAULT FALSE,
    ijb_primitive   ijb_primitive NOT NULL,
    ijb_class       ijb_class NOT NULL,
    layer           spec_layer NOT NULL,
    namespace       VARCHAR,
    notes           VARCHAR
);

CREATE TABLE dagtoml.attribute_vocabulary (
    attribute              VARCHAR PRIMARY KEY,
    applies_to_entity      VARCHAR[],
    applies_to_template    VARCHAR[],
    ijb_constraint_type    ijb_constraint_type NOT NULL,
    extensible             BOOLEAN NOT NULL,
    default_value          VARCHAR,
    layer                  spec_layer NOT NULL,
    backing_enum_type      VARCHAR
);

CREATE TABLE dagtoml.attribute_value_allowed (
    attribute   VARCHAR NOT NULL REFERENCES dagtoml.attribute_vocabulary(attribute),
    value       VARCHAR NOT NULL,
    PRIMARY KEY (attribute, value)
);


-- ============================================================
-- 4. Instance tables
-- ============================================================

CREATE TABLE dagtoml.instance_file (
    id                 UUID PRIMARY KEY DEFAULT uuid(),
    source_path        VARCHAR NOT NULL,
    content_sha256     VARCHAR NOT NULL,
    schema_version     VARCHAR NOT NULL,
    ontology_version   INTEGER,
    template_kind      VARCHAR NOT NULL REFERENCES dagtoml.kind_descriptor(template_kind),
    framework_profile  VARCHAR,
    title              VARCHAR,
    docs_url           VARCHAR,
    created            DATE,
    created_at         TIMESTAMPTZ,
    meta_extras        JSON NOT NULL DEFAULT '{}'::JSON,
    ingested_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source_path, content_sha256),
    CHECK (framework_profile IS NULL OR framework_profile IN ('agent-assurance', 'AGDF'))
);

-- spec.md §11. Optional [provenance] table.
CREATE TABLE dagtoml.provenance (
    instance_file_id    UUID PRIMARY KEY REFERENCES dagtoml.instance_file(id),
    source_path         VARCHAR NOT NULL,
    source_sha256       VARCHAR NOT NULL,
    source_bytes        BIGINT  NOT NULL CHECK (source_bytes >= 0),
    captured_at         TIMESTAMPTZ,
    extraction_method   VARCHAR,
    source_description  VARCHAR,
    extras              JSON NOT NULL DEFAULT '{}'::JSON,
    CHECK (regexp_matches(source_sha256, '^sha256:[0-9a-f]{64}$'))
);

CREATE TABLE dagtoml.entity (
    id                 UUID PRIMARY KEY DEFAULT uuid(),
    qualified_id       VARCHAR NOT NULL UNIQUE,
    prefix             VARCHAR NOT NULL,
    entity_kind        VARCHAR NOT NULL REFERENCES dagtoml.entity_kind_descriptor(entity_kind),
    declared_in        UUID NOT NULL REFERENCES dagtoml.instance_file(id),
    ijb_primitive      ijb_primitive NOT NULL DEFAULT 'thing',
    ijb_class          ijb_class     NOT NULL DEFAULT 'instance',

    -- Promoted commonly-queried attributes; NULL when not applicable.
    priority           priority_level,
    unit_status        unit_status,
    review_status      review_status,
    likelihood         risk_level,
    impact             risk_level,
    residual           residual_risk,
    smoke_status       smoke_decision,
    weight             DOUBLE,

    payload            JSON NOT NULL DEFAULT '{}'::JSON,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX entity_kind_idx        ON dagtoml.entity (entity_kind);
CREATE INDEX entity_declared_in_idx ON dagtoml.entity (declared_in);

CREATE TABLE dagtoml.relation (
    id                 UUID PRIMARY KEY DEFAULT uuid(),
    predicate          VARCHAR NOT NULL REFERENCES dagtoml.relation_descriptor(predicate),
    source_entity_id   UUID NOT NULL REFERENCES dagtoml.entity(id),
    target_entity_id   UUID REFERENCES dagtoml.entity(id),
    target_label       VARCHAR,
    asserted_in        UUID NOT NULL REFERENCES dagtoml.instance_file(id),
    attrs              JSON NOT NULL DEFAULT '{}'::JSON,
    ijb_primitive      ijb_primitive NOT NULL DEFAULT 'path',
    ijb_class          ijb_class     NOT NULL DEFAULT 'instance',
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK ((target_entity_id IS NOT NULL)::INTEGER + (target_label IS NOT NULL)::INTEGER = 1)
);

CREATE INDEX relation_source_idx    ON dagtoml.relation (source_entity_id);
CREATE INDEX relation_target_idx    ON dagtoml.relation (target_entity_id);
CREATE INDEX relation_predicate_idx ON dagtoml.relation (predicate);


-- ============================================================
-- 5. Convenience views
-- ============================================================

CREATE OR REPLACE VIEW dagtoml.dag_unit AS
SELECT
    e.id,
    e.qualified_id AS unit_id,
    e.declared_in,
    e.unit_status  AS status,
    e.weight,
    e.payload->>'title' AS title,
    e.payload->>'tier'  AS tier,
    e.payload
FROM dagtoml.entity e
WHERE e.entity_kind = 'unit';

CREATE OR REPLACE VIEW dagtoml.dag_edge AS
SELECT
    r.id           AS edge_id,
    s.qualified_id AS from_unit,
    t.qualified_id AS to_unit,
    s.weight       AS from_weight,
    t.weight       AS to_weight,
    r.asserted_in
FROM dagtoml.relation r
JOIN dagtoml.entity   s ON s.id = r.source_entity_id
JOIN dagtoml.entity   t ON t.id = r.target_entity_id
WHERE r.predicate = 'depends_on'
  AND s.entity_kind = 'unit'
  AND t.entity_kind = 'unit';

CREATE OR REPLACE VIEW dagtoml.requirement_coverage AS
SELECT
    req.id           AS requirement_id,
    req.qualified_id AS requirement,
    req.priority,
    COUNT(DISTINCT CASE WHEN t.entity_kind='test' THEN t.id END) AS test_count,
    list(DISTINCT t.qualified_id) FILTER (WHERE t.entity_kind='test') AS verifying_tests
FROM dagtoml.entity req
LEFT JOIN dagtoml.relation r ON r.source_entity_id = req.id AND r.predicate = 'verified_by'
LEFT JOIN dagtoml.entity   t ON t.id = r.target_entity_id
WHERE req.entity_kind IN ('requirement','regulation')
GROUP BY req.id, req.qualified_id, req.priority;


-- ============================================================
-- 6. Invariant views
-- ============================================================

CREATE OR REPLACE VIEW dagtoml.inv_depends_blocks AS
SELECT
    s.qualified_id AS missing_blocks_from,
    t.qualified_id AS missing_blocks_to
FROM dagtoml.relation d
JOIN dagtoml.entity   s ON s.id = d.source_entity_id
JOIN dagtoml.entity   t ON t.id = d.target_entity_id
WHERE d.predicate = 'depends_on'
  AND NOT EXISTS (
      SELECT 1 FROM dagtoml.relation b
      WHERE b.predicate = 'blocks'
        AND b.source_entity_id = d.target_entity_id
        AND b.target_entity_id = d.source_entity_id
  );

CREATE OR REPLACE VIEW dagtoml.inv_multi_producer AS
SELECT
    art.qualified_id      AS artifact,
    COUNT(*)              AS producer_count,
    list(src.qualified_id) AS producers
FROM dagtoml.relation r
JOIN dagtoml.entity art ON art.id = r.target_entity_id
JOIN dagtoml.entity src ON src.id = r.source_entity_id
WHERE r.predicate = 'produces'
  AND art.entity_kind = 'artifact'
GROUP BY art.id, art.qualified_id
HAVING COUNT(*) <> 1;

-- Cycle detection wrapped as a view (DuckDB doesn't have stored
-- functions in the PG sense; consumers `SELECT * FROM
-- dagtoml.inv_depends_cycles`).
CREATE OR REPLACE VIEW dagtoml.inv_depends_cycles AS
WITH RECURSIVE walk(start_id, current_id, path, has_cycle) AS (
    SELECT id, id, [qualified_id], FALSE
    FROM dagtoml.entity
    WHERE entity_kind = 'unit'
    UNION ALL
    SELECT w.start_id,
           t.id,
           list_concat(w.path, [t.qualified_id]),
           list_contains(w.path, t.qualified_id)
    FROM walk w
    JOIN dagtoml.relation r ON r.source_entity_id = w.current_id AND r.predicate = 'depends_on'
    JOIN dagtoml.entity   t ON t.id = r.target_entity_id
    WHERE NOT w.has_cycle
)
SELECT DISTINCT path FROM walk WHERE has_cycle;

CREATE OR REPLACE VIEW dagtoml.inv_unresolved_refs AS
SELECT
    src.qualified_id AS source,
    r.predicate,
    r.target_label   AS unresolved_target
FROM dagtoml.relation r
JOIN dagtoml.entity src ON src.id = r.source_entity_id
JOIN dagtoml.relation_descriptor rd ON rd.predicate = r.predicate
WHERE r.target_entity_id IS NULL
  AND r.target_label IS NOT NULL
  AND rd.target_freeform = FALSE;
