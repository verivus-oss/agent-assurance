-- DAG-TOML reference SQLite / libSQL (Turso) schema (non-normative).
--
-- Sibling of reference/database/postgres/schema.sql, adapted to SQLite's
-- type system. Works on:
--   * SQLite >= 3.38 (uses STRICT tables, JSON1 built-in, expression
--     DEFAULTs, partial indexes, recursive CTEs, FK enforcement)
--   * libSQL / Turso (SQLite-compatible fork — same DDL works)
--
-- Translation table from the PG reference:
--   PG                                          SQLite/libSQL
--   ──                                          ─────────────
--   CREATE TYPE x AS ENUM (...)                 TEXT CHECK (x IN (...))
--   JSONB                                       TEXT (use json_* / -> for queries)
--   UUID                                        TEXT (16-byte hex via randomblob)
--   text[]                                      TEXT holding a JSON array
--   gen_random_uuid()                           lower(hex(randomblob(16)))
--   CREATE OR REPLACE FUNCTION ... RETURNS TABLE   recursive VIEW
--   GIN index on JSONB                          (not modelled — SQLite has no
--                                                equivalent; queries use json1)
--   CREATE SCHEMA x; SET search_path TO x;      (no schemas in SQLite — table
--                                                names carry the prefix)
--
-- All STRICT tables for SQLite >= 3.38. STRICT enforces the declared
-- column types, which gives us the same shape discipline as PG. libSQL
-- supports STRICT identically.
--
-- Foreign keys: SQLite enforces FKs only when `PRAGMA foreign_keys = ON;`
-- is set on the connection. The pragma is declared once below; the seed
-- and any ingestion path MUST set it too.

PRAGMA foreign_keys = ON;


-- ============================================================
-- 1. Registry tables
-- ============================================================

CREATE TABLE dagtoml_kind_descriptor (
    template_kind     TEXT PRIMARY KEY,
    layer             TEXT NOT NULL CHECK (layer IN ('core', 'profile:agent-assurance', 'profile:disclosure', 'profile:cost', 'profile:com.verivus.runtime')),
    descriptor_path   TEXT NOT NULL,
    requires_profile  TEXT,
    notes             TEXT
) STRICT;

CREATE TABLE dagtoml_entity_kind_descriptor (
    entity_kind        TEXT PRIMARY KEY,
    id_prefix_pattern  TEXT NOT NULL,
    layer              TEXT NOT NULL CHECK (layer IN ('core', 'profile:agent-assurance', 'profile:disclosure', 'profile:cost', 'profile:com.verivus.runtime')),
    defining_kind      TEXT NOT NULL REFERENCES dagtoml_kind_descriptor(template_kind),
    ijb_primitive      TEXT NOT NULL CHECK (ijb_primitive IN ('thing','scope','path','observed','constraint','time')),
    ijb_class          TEXT NOT NULL CHECK (ijb_class IN ('structural','instance')),
    description        TEXT
) STRICT;

CREATE TABLE dagtoml_relation_descriptor (
    predicate       TEXT PRIMARY KEY,
    -- JSON arrays of entity_kind names. SQLite has no array type.
    -- Use json_each(domain) / json_each(range) to inspect.
    domain          TEXT NOT NULL CHECK (json_valid(domain)),
    range           TEXT NOT NULL CHECK (json_valid(range)),
    inverse_of      TEXT REFERENCES dagtoml_relation_descriptor(predicate),
    cardinality     INTEGER,
    is_acyclic      INTEGER NOT NULL DEFAULT 0 CHECK (is_acyclic IN (0,1)),
    target_freeform INTEGER NOT NULL DEFAULT 0 CHECK (target_freeform IN (0,1)),
    ijb_primitive   TEXT NOT NULL CHECK (ijb_primitive IN ('thing','scope','path','observed','constraint','time')),
    ijb_class       TEXT NOT NULL CHECK (ijb_class IN ('structural','instance')),
    layer           TEXT NOT NULL CHECK (layer IN ('core', 'profile:agent-assurance', 'profile:disclosure', 'profile:cost', 'profile:com.verivus.runtime')),
    namespace       TEXT,
    notes           TEXT
) STRICT;

CREATE TABLE dagtoml_attribute_vocabulary (
    attribute              TEXT PRIMARY KEY,
    applies_to_entity      TEXT CHECK (applies_to_entity IS NULL OR json_valid(applies_to_entity)),
    applies_to_template    TEXT CHECK (applies_to_template IS NULL OR json_valid(applies_to_template)),
    ijb_constraint_type    TEXT NOT NULL CHECK (ijb_constraint_type IN ('structural','policy','observed')),
    extensible             INTEGER NOT NULL CHECK (extensible IN (0,1)),
    default_value          TEXT,
    layer                  TEXT NOT NULL CHECK (layer IN ('core', 'profile:agent-assurance', 'profile:disclosure', 'profile:cost', 'profile:com.verivus.runtime')),
    -- backing_check_constraint names the schema-level CHECK list that
    -- enforces the closed value set (SQLite-side analogue of PG's
    -- backing_enum_type). NULL = extensible vocab, checked via
    -- dagtoml_attribute_value_allowed instead.
    backing_check_constraint TEXT
) STRICT;

CREATE TABLE dagtoml_attribute_value_allowed (
    attribute   TEXT NOT NULL REFERENCES dagtoml_attribute_vocabulary(attribute),
    value       TEXT NOT NULL,
    PRIMARY KEY (attribute, value)
) STRICT;


-- ============================================================
-- 2. Instance tables
-- ============================================================

CREATE TABLE dagtoml_instance_file (
    -- 32-char lowercase hex of a 16-byte random blob. Supplied via an
    -- expression DEFAULT so inserts can omit the value. (SQLite's
    -- STORED/VIRTUAL "generated columns" require an expression over
    -- OTHER columns; this is a plain DEFAULT, not a generated column.)
    id                 TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    source_path        TEXT NOT NULL,
    content_sha256     TEXT NOT NULL,
    schema_version     TEXT NOT NULL,
    ontology_version   INTEGER,
    template_kind      TEXT NOT NULL REFERENCES dagtoml_kind_descriptor(template_kind),
    framework_profile  TEXT CHECK (framework_profile IS NULL OR framework_profile IN ('agent-assurance','AGDF')),
    title              TEXT,
    docs_url           TEXT,
    created            TEXT,             -- ISO date string
    created_at         TEXT,             -- ISO 8601 timestamp string
    meta_extras        TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(meta_extras)),
    ingested_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    UNIQUE (source_path, content_sha256)
) STRICT;

CREATE INDEX idx_instance_file_template_kind ON dagtoml_instance_file (template_kind);
CREATE INDEX idx_instance_file_profile       ON dagtoml_instance_file (framework_profile);

-- spec.md §11. Optional [provenance] table.
CREATE TABLE dagtoml_provenance (
    instance_file_id    TEXT PRIMARY KEY REFERENCES dagtoml_instance_file(id) ON DELETE CASCADE,
    source_path         TEXT NOT NULL,
    source_sha256       TEXT NOT NULL CHECK (source_sha256 GLOB 'sha256:????????????????????????????????????????????????????????????????'),
    source_bytes        INTEGER NOT NULL CHECK (source_bytes >= 0),
    captured_at         TEXT,
    extraction_method   TEXT,
    source_description  TEXT,
    extras              TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(extras))
) STRICT;

CREATE TABLE dagtoml_entity (
    id                 TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    qualified_id       TEXT NOT NULL UNIQUE,
    prefix             TEXT NOT NULL,
    entity_kind        TEXT NOT NULL REFERENCES dagtoml_entity_kind_descriptor(entity_kind),
    declared_in        TEXT NOT NULL REFERENCES dagtoml_instance_file(id) ON DELETE CASCADE,
    ijb_primitive      TEXT NOT NULL DEFAULT 'thing'    CHECK (ijb_primitive IN ('thing','scope','path','observed','constraint','time')),
    ijb_class          TEXT NOT NULL DEFAULT 'instance' CHECK (ijb_class     IN ('structural','instance')),

    -- Promoted commonly-queried attributes. NULL when not applicable.
    priority           TEXT CHECK (priority      IS NULL OR priority      IN ('must','should','could')),
    unit_status        TEXT CHECK (unit_status   IS NULL OR unit_status   IN ('pending','in_progress','done','blocked','deferred')),
    review_status      TEXT CHECK (review_status IS NULL OR review_status IN ('draft','blocked','ready','in_review','rereview_needed')),
    likelihood         TEXT CHECK (likelihood    IS NULL OR likelihood    IN ('negligible','low','medium','high','critical')),
    impact             TEXT CHECK (impact        IS NULL OR impact        IN ('negligible','low','medium','high','critical')),
    residual           TEXT CHECK (residual      IS NULL OR residual      IN ('accepted','mitigated','open')),
    smoke_status       TEXT CHECK (smoke_status  IS NULL OR smoke_status  IN ('pass','fail','inconclusive')),
    weight             REAL,

    payload            TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(payload)),
    created_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
) STRICT;

CREATE INDEX idx_entity_kind        ON dagtoml_entity (entity_kind);
CREATE INDEX idx_entity_declared_in ON dagtoml_entity (declared_in);

CREATE TABLE dagtoml_relation (
    id                 TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    predicate          TEXT NOT NULL REFERENCES dagtoml_relation_descriptor(predicate),
    source_entity_id   TEXT NOT NULL REFERENCES dagtoml_entity(id) ON DELETE CASCADE,
    target_entity_id   TEXT REFERENCES dagtoml_entity(id) ON DELETE CASCADE,
    target_label       TEXT,
    asserted_in        TEXT NOT NULL REFERENCES dagtoml_instance_file(id) ON DELETE CASCADE,
    attrs              TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(attrs)),
    ijb_primitive      TEXT NOT NULL DEFAULT 'path'     CHECK (ijb_primitive IN ('thing','scope','path','observed','constraint','time')),
    ijb_class          TEXT NOT NULL DEFAULT 'instance' CHECK (ijb_class     IN ('structural','instance')),
    created_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),

    CHECK ((target_entity_id IS NOT NULL) + (target_label IS NOT NULL) = 1)
) STRICT;

-- Edge uniqueness (separate partial-unique indexes for the two target
-- forms, mirroring the PG schema).
CREATE UNIQUE INDEX uq_relation_typed_edge
    ON dagtoml_relation (predicate, source_entity_id, target_entity_id)
    WHERE target_entity_id IS NOT NULL;
CREATE UNIQUE INDEX uq_relation_freeform_edge
    ON dagtoml_relation (predicate, source_entity_id, target_label)
    WHERE target_label IS NOT NULL;

CREATE INDEX idx_relation_source    ON dagtoml_relation (source_entity_id);
CREATE INDEX idx_relation_target    ON dagtoml_relation (target_entity_id);
CREATE INDEX idx_relation_predicate ON dagtoml_relation (predicate);


-- ============================================================
-- 3. Convenience views
-- ============================================================

CREATE VIEW dagtoml_dag_unit AS
SELECT
    e.id,
    e.qualified_id AS unit_id,
    e.declared_in,
    e.unit_status  AS status,
    e.weight,
    json_extract(e.payload, '$.title') AS title,
    json_extract(e.payload, '$.tier')  AS tier,
    e.payload
FROM dagtoml_entity e
WHERE e.entity_kind = 'unit';

CREATE VIEW dagtoml_dag_edge AS
SELECT
    r.id           AS edge_id,
    s.qualified_id AS from_unit,
    t.qualified_id AS to_unit,
    s.weight       AS from_weight,
    t.weight       AS to_weight,
    r.asserted_in
FROM dagtoml_relation r
JOIN dagtoml_entity   s ON s.id = r.source_entity_id
JOIN dagtoml_entity   t ON t.id = r.target_entity_id
WHERE r.predicate = 'depends_on'
  AND s.entity_kind = 'unit'
  AND t.entity_kind = 'unit';

CREATE VIEW dagtoml_requirement_coverage AS
SELECT
    req.id           AS requirement_id,
    req.qualified_id AS requirement,
    req.priority,
    COUNT(DISTINCT CASE WHEN t.entity_kind='test' THEN t.id END) AS test_count,
    json_group_array(DISTINCT t.qualified_id)
        FILTER (WHERE t.entity_kind='test')                       AS verifying_tests
FROM dagtoml_entity req
LEFT JOIN dagtoml_relation r ON r.source_entity_id = req.id AND r.predicate = 'verified_by'
LEFT JOIN dagtoml_entity   t ON t.id = r.target_entity_id
WHERE req.entity_kind IN ('requirement','regulation')
GROUP BY req.id, req.qualified_id, req.priority;

CREATE VIEW dagtoml_gate_status AS
SELECT
    ac.qualified_id           AS artifact_class,
    ac.review_status          AS status,
    g.qualified_id            AS gate_id,
    json_extract(g.payload, '$.description') AS gate_description,
    ac.declared_in
FROM dagtoml_entity ac
LEFT JOIN dagtoml_relation r ON r.target_entity_id = ac.id AND r.predicate = 'artifact_class'
LEFT JOIN dagtoml_entity   g ON g.id = r.source_entity_id  AND g.entity_kind = 'gate';


-- ============================================================
-- 4. Invariant views (post-ingestion gate queries)
-- ============================================================

-- 4.1 depends_on / blocks symmetry (spec.md §5).
CREATE VIEW dagtoml_inv_depends_blocks AS
SELECT
    s.qualified_id AS missing_blocks_from,
    t.qualified_id AS missing_blocks_to
FROM dagtoml_relation d
JOIN dagtoml_entity   s ON s.id = d.source_entity_id
JOIN dagtoml_entity   t ON t.id = d.target_entity_id
WHERE d.predicate = 'depends_on'
  AND NOT EXISTS (
      SELECT 1 FROM dagtoml_relation b
      WHERE b.predicate = 'blocks'
        AND b.source_entity_id = d.target_entity_id
        AND b.target_entity_id = d.source_entity_id
  );

-- 4.2 Single producer per artifact (spec.md §5).
CREATE VIEW dagtoml_inv_multi_producer AS
SELECT
    art.qualified_id            AS artifact,
    COUNT(*)                    AS producer_count,
    json_group_array(src.qualified_id) AS producers
FROM dagtoml_relation r
JOIN dagtoml_entity art ON art.id = r.target_entity_id
JOIN dagtoml_entity src ON src.id = r.source_entity_id
WHERE r.predicate = 'produces'
  AND art.entity_kind = 'artifact'
GROUP BY art.id, art.qualified_id
HAVING COUNT(*) <> 1;

-- 4.3 depends_on cycle detection — recursive CTE wrapped as a view.
-- SQLite has no stored functions; consumers SELECT * FROM this view.
CREATE VIEW dagtoml_inv_depends_cycles AS
WITH RECURSIVE walk(start_id, current_id, path_json, has_cycle) AS (
    SELECT id, id, json_array(qualified_id), 0
    FROM dagtoml_entity
    WHERE entity_kind = 'unit'
    UNION ALL
    SELECT w.start_id,
           t.id,
           json_insert(w.path_json, '$[#]', t.qualified_id),
           CASE
               WHEN EXISTS (
                   SELECT 1 FROM json_each(w.path_json) j
                   WHERE j.value = t.qualified_id
               ) THEN 1 ELSE 0
           END
    FROM walk w
    JOIN dagtoml_relation r ON r.source_entity_id = w.current_id AND r.predicate = 'depends_on'
    JOIN dagtoml_entity   t ON t.id = r.target_entity_id
    WHERE w.has_cycle = 0
)
SELECT DISTINCT path_json AS cycle FROM walk WHERE has_cycle = 1;

-- 4.4 Unresolved cross-document references.
CREATE VIEW dagtoml_inv_unresolved_refs AS
SELECT
    src.qualified_id AS source,
    r.predicate,
    r.target_label   AS unresolved_target
FROM dagtoml_relation r
JOIN dagtoml_entity src ON src.id = r.source_entity_id
JOIN dagtoml_relation_descriptor rd ON rd.predicate = r.predicate
WHERE r.target_entity_id IS NULL
  AND r.target_label IS NOT NULL
  AND rd.target_freeform = 0;
