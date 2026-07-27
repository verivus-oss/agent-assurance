-- DAG-TOML reference seed data (non-normative).
--
-- Mirrors core/ontology.toml + profiles/agent-assurance/ontology.toml +
-- core/*-kind.toml + profiles/agent-assurance/*-kind.toml.
--
-- This is a checked-in snapshot for convenience. The intended workflow is
-- to (re)generate this file from the ontology TOMLs at build time so the
-- schema never drifts. Treat hand-edits here as a smell.
--
-- Counts (verified against ontology files; matches MANIFEST.toml):
--   * 21 template kinds        (6 core + 9 agent-assurance + 3 disclosure + 1 cost + 1 com.verivus.runtime + 1 meta `kind-descriptor`)
--   * 27 entity kinds          (17 core + 6 agent-assurance + 3 disclosure + 1 cost)
--   * 31 relation rows         (26 core + 5 contract-namespaced variants)
--                              The ontology declares 31 [[relations]] blocks,
--                              some sharing a predicate name (e.g., depends_on
--                              for units vs. contracts). Per-scope variants are
--                              emitted as namespaced predicates here:
--                                contract:depends_on
--                                contract:supersedes
--                                contract:verified_by
--                              Aliases `claim_id` / `evidence_id` are emitted
--                              as their own rows because the ontology declares
--                              them as separate [[relations]] entries.
--                              The 31st row is the cross-document
--                              `cites_upstream` marker added by SPEC §12.
--   * 48 attribute vocabularies (12 core + 27 agent-assurance + 4 disclosure + 3 cost + 2 com.verivus.runtime)

SET search_path TO dagtoml, public;

-- ============================================================
-- kind_descriptor (20 rows: 6 core + 9 agent-assurance + 3 disclosure + 1 cost + 1 meta)
-- The 15th row is the `kind-descriptor` template_kind itself, declared
-- in spec.md and used as the `template_kind` of every *-kind.toml file.
-- ============================================================
INSERT INTO kind_descriptor (template_kind, layer, descriptor_path, requires_profile) VALUES
    ('kind-descriptor',                'core', 'spec.md',                                                       NULL),
    ('implementation-dag',             'core', 'core/implementation-dag-kind.toml',                             NULL),
    ('traceability',                   'core', 'core/traceability-kind.toml',                                   NULL),
    ('readiness-gate',                 'core', 'core/readiness-gate-kind.toml',                                 NULL),
    ('contract-declaration',           'core', 'core/contract-declaration-kind.toml',                           NULL),
    ('evidence-matrix',                'core', 'core/evidence-matrix-kind.toml',                                NULL),
    ('profile-descriptor',             'core', 'core/profile-descriptor-kind.toml',                             NULL),
    ('spec-contract',                  'profile:agent-assurance', 'profiles/agent-assurance/spec-contract-kind.toml',             'agent-assurance'),
    ('threat-model',                   'profile:agent-assurance', 'profiles/agent-assurance/threat-model-kind.toml',              'agent-assurance'),
    ('smoke-validation',               'profile:agent-assurance', 'profiles/agent-assurance/smoke-validation-kind.toml',          'agent-assurance'),
    ('rollback-plan',                  'profile:agent-assurance', 'profiles/agent-assurance/rollback-plan-kind.toml',             'agent-assurance'),
    ('adapter-contract',               'profile:agent-assurance', 'profiles/agent-assurance/adapter-contract-kind.toml',          'agent-assurance'),
    ('adapter-registry-binding',       'profile:agent-assurance', 'profiles/agent-assurance/adapter-registry-binding-kind.toml',  'agent-assurance'),
    ('assertion-bundle',               'profile:agent-assurance', 'profiles/agent-assurance/assertion-bundle-kind.toml',          'agent-assurance'),
    ('assertion-log-record',           'profile:agent-assurance', 'profiles/agent-assurance/assertion-log-record-kind.toml',      'agent-assurance'),
    ('gate-decision',                  'profile:agent-assurance', 'profiles/agent-assurance/gate-decision-kind.toml',             'agent-assurance'),
    ('disclosure-attestation',         'profile:disclosure',      'profiles/disclosure/disclosure-attestation-kind.toml',         'disclosure'),
    ('redaction-manifest',             'profile:disclosure',      'profiles/disclosure/redaction-manifest-kind.toml',             'disclosure'),
    ('selective-disclosure-proof',     'profile:disclosure',      'profiles/disclosure/selective-disclosure-proof-kind.toml',     'disclosure'),
    ('cost-record',                    'profile:cost',            'profiles/cost/cost-record-kind.toml',                          'cost'),
    ('api-snapshot',                   'profile:com.verivus.runtime', 'profiles/com.verivus.runtime/api-snapshot-kind.toml',        'com.verivus.runtime'),
    ('state-mutation',                 'profile:com.verivus.runtime', 'profiles/com.verivus.runtime/state-mutation-kind.toml',      'com.verivus.runtime'),
    ('mutation-claim',                 'profile:com.verivus.runtime', 'profiles/com.verivus.runtime/mutation-claim-kind.toml',      'com.verivus.runtime');

-- ============================================================
-- entity_kind_descriptor (24 rows: 17 core + 6 agent-assurance + 3 disclosure + 1 cost)
-- All are (thing, structural) per IJB conformance rules KD1.
-- id_prefix_pattern values match the ontology's `id_prefix` (for fixed
-- prefixes) or `id_pattern` (for regex-keyed entity kinds) verbatim.
-- ============================================================
INSERT INTO entity_kind_descriptor
    (entity_kind, id_prefix_pattern, layer, defining_kind, ijb_primitive, ijb_class, description) VALUES
    -- Core: traceability (9)
    ('intent',          'INT',           'core', 'traceability',         'thing', 'structural', 'User/business intent; top of trace.'),
    ('feature',         'FEAT',          'core', 'traceability',         'thing', 'structural', 'User-visible capability.'),
    ('requirement',     'REQ',           'core', 'traceability',         'thing', 'structural', 'Normative, testable requirement.'),
    ('regulation',      'REG',           'core', 'traceability',         'thing', 'structural', 'Legal/policy/regulatory obligation.'),
    ('decision',        'DEC',           'core', 'traceability',         'thing', 'structural', 'Design or policy decision.'),
    ('implementation',  'IMP',           'core', 'traceability',         'thing', 'structural', 'Implementation work package.'),
    ('code',            'CODE',          'core', 'traceability',         'thing', 'structural', 'Concrete code artifact.'),
    ('test',            'TEST',          'core', 'traceability',         'thing', 'structural', 'Verification artifact.'),
    ('output',          'OUT',           'core', 'traceability',         'thing', 'structural', 'User-visible output or deliverable.'),
    -- Core: implementation-dag (2)
    ('unit',            'U\d+[a-z]?',    'core', 'implementation-dag',   'thing', 'structural', 'DAG unit (regex-keyed).'),
    ('artifact',        'ART',           'core', 'implementation-dag',   'thing', 'structural', 'Internal artifact flowing between DAG units.'),
    -- Core: readiness-gate (2)
    ('artifact_class',  'A\d+',          'core', 'readiness-gate',       'thing', 'structural', 'Review artifact class.'),
    ('gate',            'G\d+',          'core', 'readiness-gate',       'thing', 'structural', 'Readiness gate keyed to artifact class.'),
    -- Core: contract-declaration (1)
    ('contract',        'C\d+',          'core', 'contract-declaration', 'thing', 'structural', 'Declared contract.'),
    -- Core: evidence-matrix (3)
    ('claim',           'E\d+',          'core', 'evidence-matrix',      'thing', 'structural', 'Strong claim.'),
    ('evidence',        'EV\d+',         'core', 'evidence-matrix',      'thing', 'structural', 'Proof artifact.'),
    ('matrix',          'M\d+',          'core', 'evidence-matrix',      'thing', 'structural', 'Claim↔evidence linkage.'),
    -- Profile: agent-assurance (6)
    ('guarantee',       'GUAR',          'profile:agent-assurance', 'spec-contract',  'thing', 'structural', 'Measurable guarantee.'),
    ('invariant',       'INV',           'profile:agent-assurance', 'spec-contract',  'thing', 'structural', 'Invariant the implementation MUST not violate.'),
    ('non_goal',        'NG',            'profile:agent-assurance', 'spec-contract',  'thing', 'structural', 'Explicit non-goal of the change.'),
    ('threat',          'THREAT',        'profile:agent-assurance', 'threat-model',   'thing', 'structural', 'Identified threat to the change/system.'),
    ('smoke_check',     'SMOKE',         'profile:agent-assurance', 'smoke-validation','thing', 'structural', 'Smoke-validation check entry.'),
    ('rollback_trigger','TRIG',          'profile:agent-assurance', 'rollback-plan',  'thing', 'structural', 'Pre-declared rollback trigger condition.'),
    -- Profile: disclosure (3)
    ('disclosure_attestation',     'DISC', 'profile:disclosure', 'disclosure-attestation',     'thing', 'structural', 'Signed posture statement that a named subject was disclosed at a given posture.'),
    ('redaction',                  'RED',  'profile:disclosure', 'redaction-manifest',         'thing', 'structural', 'A byte-range or field-path inside a source artifact that was removed before publication.'),
    ('selective_disclosure_proof', 'SDP',  'profile:disclosure', 'selective-disclosure-proof', 'thing', 'structural', 'A commitment a recipient can verify to confirm the publisher knew the omitted content.'),
    -- Profile: cost (1)
    ('cost_record',                'COST', 'profile:cost',       'cost-record',                'thing', 'structural', 'A single cost-record entry: declared cost of one costed action, witnessed by `producer_id` at `incurred_at`, decided by `decider_class`.');

-- ============================================================
-- relation_descriptor (31 rows: one per [[relations]] block in
-- core/ontology.toml). Predicate names that appear more than once in
-- the ontology with different domain/range tuples are namespaced as
-- `<scope>:<predicate>` (currently only `contract:*`) so the PK on
-- `predicate` remains usable as the FK target from `relation`.
-- All are (path, structural).
-- ============================================================
INSERT INTO relation_descriptor
    (predicate, domain, range, inverse_of, cardinality, is_acyclic, target_freeform, ijb_primitive, ijb_class, layer) VALUES
    -- Traceability family (17 of the 30)
    ('derived_from',           ARRAY['intent'],                       ARRAY['intent'],                                       NULL,            NULL, FALSE, FALSE, 'path', 'structural', 'core'),
    ('realized_by',            ARRAY['intent'],                       ARRAY['feature','requirement'],                        'realizes',      NULL, FALSE, FALSE, 'path', 'structural', 'core'),
    ('realizes',               ARRAY['feature','code','output'],      ARRAY['intent','implementation','requirement','feature'], 'realized_by', NULL, FALSE, FALSE, 'path', 'structural', 'core'),
    ('constrained_by',         ARRAY['feature'],                      ARRAY['requirement','regulation'],                     'constrains',    NULL, FALSE, FALSE, 'path', 'structural', 'core'),
    ('implemented_by',         ARRAY['feature'],                      ARRAY['implementation'],                               'implements',    NULL, FALSE, FALSE, 'path', 'structural', 'core'),
    ('produces',               ARRAY['feature','unit'],               ARRAY['output','artifact'],                            NULL,            NULL, FALSE, FALSE, 'path', 'structural', 'core'),
    ('constrains',             ARRAY['requirement','regulation'],     ARRAY['feature','implementation','requirement'],       'constrained_by',NULL, FALSE, FALSE, 'path', 'structural', 'core'),
    ('verified_by',            ARRAY['requirement','regulation'],     ARRAY['test'],                                         'verifies',      NULL, FALSE, FALSE, 'path', 'structural', 'core'),
    ('addresses',              ARRAY['decision'],                     ARRAY['requirement','regulation'],                     NULL,            NULL, FALSE, FALSE, 'path', 'structural', 'core'),
    ('shapes',                 ARRAY['decision'],                     ARRAY['implementation','code'],                        NULL,            NULL, FALSE, FALSE, 'path', 'structural', 'core'),
    ('supersedes',             ARRAY['decision'],                     ARRAY['decision'],                                     NULL,            NULL, TRUE,  FALSE, 'path', 'structural', 'core'),
    ('implements',             ARRAY['implementation'],               ARRAY['feature','requirement'],                        'implemented_by',NULL, FALSE, FALSE, 'path', 'structural', 'core'),
    ('guided_by',              ARRAY['implementation'],               ARRAY['decision'],                                     NULL,            NULL, FALSE, FALSE, 'path', 'structural', 'core'),
    ('code',                   ARRAY['implementation'],               ARRAY['code'],                                         NULL,            NULL, FALSE, FALSE, 'path', 'structural', 'core'),
    ('tests',                  ARRAY['implementation'],               ARRAY['test'],                                         NULL,            NULL, FALSE, FALSE, 'path', 'structural', 'core'),
    ('downstream_outputs',     ARRAY['implementation'],               ARRAY['output'],                                       NULL,            NULL, FALSE, FALSE, 'path', 'structural', 'core'),
    ('verifies',               ARRAY['test'],                         ARRAY['requirement','regulation'],                     'verified_by',   NULL, FALSE, FALSE, 'path', 'structural', 'core'),
    -- DAG / readiness-gate family (4)
    ('depends_on',             ARRAY['unit'],                         ARRAY['unit'],                                         'blocks',        NULL, TRUE,  FALSE, 'path', 'structural', 'core'),
    ('blocks',                 ARRAY['unit'],                         ARRAY['unit'],                                         'depends_on',    NULL, TRUE,  FALSE, 'path', 'structural', 'core'),
    ('consumes',               ARRAY['unit'],                         ARRAY['artifact'],                                     NULL,            NULL, FALSE, FALSE, 'path', 'structural', 'core'),
    ('artifact_class',         ARRAY['gate'],                         ARRAY['artifact_class'],                               NULL,            1,    FALSE, FALSE, 'path', 'structural', 'core'),
    -- Contract-scoped variants (5) — distinct ontology blocks with the
    -- same predicate name but contract domain/range. Namespaced here
    -- so PK uniqueness holds.
    ('contract:depends_on',    ARRAY['contract'],                     ARRAY['contract'],                                     NULL,            NULL, TRUE,  FALSE, 'path', 'structural', 'core'),
    ('contract:supersedes',    ARRAY['contract'],                     ARRAY['contract'],                                     NULL,            NULL, TRUE,  FALSE, 'path', 'structural', 'core'),
    ('related_to',             ARRAY['contract'],                     ARRAY['contract'],                                     NULL,            NULL, FALSE, FALSE, 'path', 'structural', 'core'),
    ('applies_to',             ARRAY['contract'],                     ARRAY[]::TEXT[],                                       NULL,            NULL, FALSE, TRUE,  'path', 'structural', 'core'),
    ('contract:verified_by',   ARRAY['contract'],                     ARRAY[]::TEXT[],                                       NULL,            NULL, FALSE, TRUE,  'path', 'structural', 'core'),
    -- Evidence-matrix family (4) — claim/claim_id and evidence/evidence_id
    -- are distinct ontology entries (aliases). Both rows kept so the FK
    -- lookup works for either spelling.
    ('claim',                  ARRAY['matrix'],                       ARRAY['claim'],                                        NULL,            1,    FALSE, FALSE, 'path', 'structural', 'core'),
    ('claim_id',               ARRAY['matrix'],                       ARRAY['claim'],                                        NULL,            1,    FALSE, FALSE, 'path', 'structural', 'core'),
    ('evidence',               ARRAY['matrix'],                       ARRAY['evidence'],                                     NULL,            1,    FALSE, FALSE, 'path', 'structural', 'core'),
    ('evidence_id',            ARRAY['matrix'],                       ARRAY['evidence'],                                     NULL,            1,    FALSE, FALSE, 'path', 'structural', 'core'),
    -- Closure-root marker (SPEC §12) — kind descriptors apply this as
    -- `ontology_mapping = "cites_upstream"` on required fields/sections
    -- that carry upstream artifact references. Source/range are
    -- unconstrained labels: the closure-root rule fires uniformly across
    -- every conforming kind regardless of which concrete entity kinds a
    -- profile defines.
    ('cites_upstream',         ARRAY[]::TEXT[],                       ARRAY[]::TEXT[],                                       NULL,            NULL, TRUE,  TRUE,  'path', 'structural', 'core');

-- ============================================================
-- attribute_vocabulary (46 rows: 12 core + 27 agent-assurance + 4 disclosure + 3 cost; agent-assurance includes subject_class/provider_id/model_family_id for gate-decision INV06)
-- ============================================================
INSERT INTO attribute_vocabulary
    (attribute, applies_to_entity, applies_to_template, ijb_constraint_type, extensible, default_value, layer, backing_enum_type) VALUES
    -- Core (9)
    ('requirement_kind',  ARRAY['requirement'],     NULL, 'structural', TRUE,  NULL,  'core', NULL),
    ('test_kind',         ARRAY['test'],            NULL, 'structural', TRUE,  NULL,  'core', NULL),
    ('priority',          ARRAY['requirement'],     NULL, 'structural', FALSE, 'must','core', 'priority_level'),
    ('unit.status',       ARRAY['unit'],            NULL, 'structural', FALSE, NULL,  'core', 'unit_status'),
    ('review.status',     ARRAY['artifact_class'],  ARRAY['readiness-gate'], 'structural', FALSE, NULL, 'core', 'review_status'),
    -- Core disclosure-posture vocabularies (spec.md §2.7) — see
    -- core/ontology.toml. Stored as TEXT + attribute_value_allowed
    -- rather than promoted to PG enums (the design rule from
    -- reference/database/README.md applies: open vocabs stay text;
    -- closed ones MAY be promoted to enums, but new spec additions
    -- live as text rows until an explicit promotion lands).
    ('confidentiality',                  NULL, NULL, 'policy', FALSE, NULL, 'core', NULL),
    ('license',                          NULL, NULL, 'policy', TRUE,  NULL, 'core', NULL),
    ('framework_profile_namespace',      NULL, NULL, 'structural', FALSE, NULL, 'core', NULL),
    ('provenance.encryption.hash_is_over', NULL, NULL, 'structural', FALSE, NULL, 'core', NULL),
    ('closure_root.digest_algorithm',      NULL, NULL, 'structural', TRUE,  NULL, 'core', NULL),
    -- Profile (24)
    ('trigger_kind',                ARRAY['rollback_trigger'], NULL, 'structural', TRUE,  NULL, 'profile:agent-assurance', NULL),
    ('likelihood',                  ARRAY['threat'],           NULL, 'structural', FALSE, NULL, 'profile:agent-assurance', 'risk_level'),
    ('impact',                      ARRAY['threat'],           NULL, 'structural', FALSE, NULL, 'profile:agent-assurance', 'risk_level'),
    ('residual_risk',               ARRAY['threat'],           NULL, 'structural', FALSE, NULL, 'profile:agent-assurance', 'residual_risk'),
    ('smoke.decision',              NULL, ARRAY['smoke-validation'], 'structural', FALSE, NULL, 'profile:agent-assurance', 'smoke_decision'),
    ('status',                      ARRAY['smoke_check'],      NULL, 'structural', FALSE, NULL, 'profile:agent-assurance', 'smoke_decision'),
    ('runtime_kind',                NULL, ARRAY['adapter-contract'], 'structural', FALSE, NULL, 'profile:agent-assurance', 'runtime_kind'),
    ('runtime_network_policy',      NULL, ARRAY['adapter-contract'], 'structural', FALSE, NULL, 'profile:agent-assurance', 'network_policy'),
    ('runtime_clock_policy',        NULL, ARRAY['adapter-contract'], 'structural', FALSE, NULL, 'profile:agent-assurance', 'clock_policy'),
    ('input_hash_method',           NULL, ARRAY['adapter-contract'], 'structural', TRUE,  NULL, 'profile:agent-assurance', NULL),
    ('adapter_id_derivation',       NULL, ARRAY['adapter-contract'], 'structural', FALSE, NULL, 'profile:agent-assurance', 'adapter_id_derivation'),
    ('gate_decision_verdict',       NULL, ARRAY['gate-decision'],    'structural', FALSE, NULL, 'profile:agent-assurance', 'gate_verdict'),
    ('severity_tier',               NULL, ARRAY['gate-decision'],    'structural', FALSE, NULL, 'profile:agent-assurance', 'severity_tier'),
    ('override_decision_method',    NULL, ARRAY['gate-decision'],    'structural', TRUE,  NULL, 'profile:agent-assurance', NULL),
    ('override_rule_operator',      NULL, ARRAY['gate-decision'],    'structural', FALSE, NULL, 'profile:agent-assurance', 'override_rule_op'),
    ('evidence_root_algorithm',     NULL, ARRAY['gate-decision'],    'structural', TRUE,  NULL, 'profile:agent-assurance', NULL),
    ('signer_class',                NULL, ARRAY['gate-decision'],    'structural', TRUE,  NULL, 'profile:agent-assurance', NULL),
    ('authority_role',              NULL, ARRAY['gate-decision'],    'structural', TRUE,  NULL, 'profile:agent-assurance', NULL),
    ('autonomy_tier',               NULL, ARRAY['gate-decision'],    'structural', TRUE,  NULL, 'profile:agent-assurance', NULL),
    ('record_signature_algorithm',  NULL, ARRAY['assertion-log-record'], 'structural', TRUE, NULL, 'profile:agent-assurance', NULL),
    ('record_hash_algorithm',       NULL, ARRAY['assertion-log-record'], 'structural', TRUE, NULL, 'profile:agent-assurance', NULL),
    ('record_canonical_form',       NULL, ARRAY['assertion-log-record'], 'structural', TRUE, NULL, 'profile:agent-assurance', NULL),
    ('registry_scheme',             NULL, ARRAY['adapter-registry-binding'], 'structural', TRUE, NULL, 'profile:agent-assurance', NULL),
    ('adapter_ref_syntax',          NULL, ARRAY['adapter-registry-binding'], 'structural', FALSE, NULL, 'profile:agent-assurance', 'adapter_ref_syntax'),
    -- Profile: disclosure (4)
    ('disclosure_posture',          ARRAY['disclosure_attestation'],     NULL, 'structural', FALSE, NULL, 'profile:disclosure', NULL),
    ('redaction_method',            ARRAY['redaction'],                  NULL, 'structural', TRUE,  NULL, 'profile:disclosure', NULL),
    ('redaction_reason',            ARRAY['redaction'],                  NULL, 'structural', TRUE,  NULL, 'profile:disclosure', NULL),
    ('proof_scheme',                ARRAY['selective_disclosure_proof'], NULL, 'structural', TRUE,  NULL, 'profile:disclosure', NULL),
    -- Profile: cost (3) — Stream G Cost-Witnessed Decision.
    ('decider_class',               ARRAY['cost_record'],                NULL, 'structural', FALSE, NULL, 'profile:cost',       NULL),
    ('cost_dimension_category',     ARRAY['cost_record'],                NULL, 'structural', FALSE, NULL, 'profile:cost',       NULL),
    ('cost_citing_kind',            ARRAY['cost_record'],                NULL, 'structural', FALSE, NULL, 'profile:cost',       NULL),
    -- Core: SPEC §13 capability envelope + abstraction class.
    ('capability_envelope.domain',  NULL, NULL, 'structural', FALSE, NULL, 'core', NULL),
    ('abstraction_class.id_pattern', NULL, NULL, 'structural', FALSE, NULL, 'core', NULL),
    -- Profile: agent-assurance cross-provider self-modification (gate-decision INV06).
    ('subject_class',       NULL, ARRAY['gate-decision'], 'structural', TRUE, NULL, 'profile:agent-assurance', NULL),
    ('provider_id',         NULL, ARRAY['gate-decision'], 'structural', TRUE, NULL, 'profile:agent-assurance', NULL),
    ('model_family_id',     NULL, ARRAY['gate-decision'], 'structural', TRUE, NULL, 'profile:agent-assurance', NULL),
    -- Profile: com.verivus.runtime (4) — api-snapshot closed witness vocabularies,
    -- and the state-mutation execution-proof vocabularies. RKM06 constrains which
    -- finality_basis each execution_proof_scheme may claim; that pairing is a kind
    -- invariant, not a column constraint, so it is not representable here.
    ('witness_scheme',        NULL, ARRAY['api-snapshot'], 'structural', FALSE, NULL, 'profile:com.verivus.runtime', NULL),
    ('attester_observed',     NULL, ARRAY['api-snapshot'], 'structural', FALSE, NULL, 'profile:com.verivus.runtime', NULL),
    ('execution_proof_scheme', NULL, ARRAY['state-mutation'], 'structural', FALSE, NULL, 'profile:com.verivus.runtime', NULL),
    ('finality_basis',        NULL, ARRAY['state-mutation'], 'structural', FALSE, NULL, 'profile:com.verivus.runtime', NULL);

-- Allowed values for non-enum-backed (i.e., extensible) vocabularies.
-- Enum-backed values are enforced by the Postgres enum type itself, so
-- their allowed values do not need to be repeated here.
INSERT INTO attribute_value_allowed (attribute, value) VALUES
    ('requirement_kind', 'functional'),
    ('requirement_kind', 'non_functional'),
    ('requirement_kind', 'policy'),
    ('requirement_kind', 'interface'),
    ('requirement_kind', 'performance'),
    ('requirement_kind', 'correctness'),
    ('requirement_kind', 'operational'),
    ('test_kind', 'unit'),
    ('test_kind', 'integration'),
    ('test_kind', 'e2e'),
    ('test_kind', 'audit'),
    ('test_kind', 'property'),
    ('test_kind', 'robustness'),
    ('test_kind', 'benchmark'),
    ('trigger_kind', 'error_rate_threshold'),
    ('trigger_kind', 'behavioral_anomaly_detected'),
    ('trigger_kind', 'determinism_regression'),
    ('trigger_kind', 'perf_regression'),
    ('trigger_kind', 'memory_safety_regression'),
    ('trigger_kind', 'data_corruption'),
    ('trigger_kind', 'windows_ci_regression'),
    ('trigger_kind', 'validator_failure'),
    ('trigger_kind', 'missing_evidence'),
    ('trigger_kind', 'manual_override'),
    ('input_hash_method', 'sha256-bytes'),
    ('input_hash_method', 'sha256-jcs'),
    ('input_hash_method', 'sha256-cbor-deterministic'),
    -- override_decision_method (extensible per profile ontology)
    ('override_decision_method', 'single-signer'),
    ('override_decision_method', 'm-of-n'),
    ('override_decision_method', 'co-signed-human-ai'),
    -- evidence_root_algorithm (extensible)
    ('evidence_root_algorithm', 'sha256-merkle-sorted-leaves'),
    ('evidence_root_algorithm', 'sha256-merkle-index-order'),
    -- signer_class (extensible)
    ('signer_class', 'human'),
    ('signer_class', 'ai_agent'),
    ('signer_class', 'service'),
    -- authority_role (extensible)
    ('authority_role', 'author'),
    ('authority_role', 'peer'),
    ('authority_role', 'team-lead'),
    ('authority_role', 'release-captain'),
    ('authority_role', 'security-officer'),
    ('authority_role', 'auditor'),
    -- autonomy_tier (extensible)
    ('autonomy_tier', 't0'),
    ('autonomy_tier', 't1'),
    ('autonomy_tier', 't2'),
    ('autonomy_tier', 't3'),
    -- record_signature_algorithm (extensible)
    ('record_signature_algorithm', 'ed25519'),
    ('record_signature_algorithm', 'ecdsa-p256'),
    -- record_hash_algorithm (extensible)
    ('record_hash_algorithm', 'sha256'),
    -- record_canonical_form (extensible)
    ('record_canonical_form', 'deterministic-cbor'),
    ('record_canonical_form', 'rfc8785-jcs'),
    -- registry_scheme (extensible)
    ('registry_scheme', 'file'),
    ('registry_scheme', 'https'),
    ('registry_scheme', 'oci'),
    ('registry_scheme', 'ipfs'),
    -- Core disclosure-posture vocab values (spec.md §2.7)
    ('confidentiality', 'public'),
    ('confidentiality', 'restricted'),
    ('confidentiality', 'confidential'),
    ('confidentiality', 'trade-secret'),
    ('confidentiality', 'embargoed'),
    ('framework_profile_namespace', 'spec-reserved'),
    ('framework_profile_namespace', 'reverse-dns'),
    ('provenance.encryption.hash_is_over', 'plaintext'),
    ('provenance.encryption.hash_is_over', 'ciphertext'),
    -- Core closure-root digest-algorithm vocab values (SPEC §12.1).
    -- Extensible — stronger digests MAY be added; weaker (MD5, SHA-1)
    -- are forbidden by the spec text.
    ('closure_root.digest_algorithm', 'sha256'),
    ('closure_root.digest_algorithm', 'sha384'),
    ('closure_root.digest_algorithm', 'sha512'),
    -- Profile: disclosure vocab values
    ('disclosure_posture', 'full'),
    ('disclosure_posture', 'partial'),
    ('disclosure_posture', 'withheld'),
    ('disclosure_posture', 'embargoed'),
    ('redaction_method', 'byte-range-delete'),
    ('redaction_method', 'field-path-delete'),
    ('redaction_method', 'field-path-mask'),
    ('redaction_method', 'blob-replace'),
    ('redaction_reason', 'pii'),
    ('redaction_reason', 'secret'),
    ('redaction_reason', 'trade-secret'),
    ('redaction_reason', 'license-restricted'),
    ('redaction_reason', 'third-party'),
    ('redaction_reason', 'regulatory'),
    ('redaction_reason', 'other'),
    ('proof_scheme', 'merkle-leaf-omission'),
    ('proof_scheme', 'field-commitment-omission'),
    ('proof_scheme', 'blob-commitment-substitution'),
    -- Profile: cost vocab values (Stream G Cost-Witnessed Decision).
    -- decider_class (8): the class of entity that incurred the cost.
    ('decider_class', 'deterministic_check'),
    ('decider_class', 'llm_single'),
    ('decider_class', 'llm_consensus'),
    ('decider_class', 'human_reviewer'),
    ('decider_class', 'tee_attested_compute'),
    ('decider_class', 'notarisation'),
    ('decider_class', 'transparency_log_write'),
    ('decider_class', 'other'),
    -- cost_dimension_category (7): closed set of cost dimensions.
    ('cost_dimension_category', 'token_equivalent'),
    ('cost_dimension_category', 'compute_time_seconds'),
    ('cost_dimension_category', 'storage_bytes'),
    ('cost_dimension_category', 'bandwidth_bytes'),
    ('cost_dimension_category', 'human_review_time_seconds'),
    ('cost_dimension_category', 'energy_equivalent'),
    ('cost_dimension_category', 'evidence_run_count'),
    -- cost_citing_kind (7): the kinds whose execution may pay a cost.
    ('cost_citing_kind', 'gate-decision'),
    ('cost_citing_kind', 'evidence-matrix'),
    ('cost_citing_kind', 'assertion-bundle'),
    ('cost_citing_kind', 'smoke-validation'),
    ('cost_citing_kind', 'threat-model'),
    ('cost_citing_kind', 'rollback-plan'),
    ('cost_citing_kind', 'other'),
    -- Core: SPEC §13 capability_envelope.domain (9 closed values, WASI Preview 2 WIT vocab).
    ('capability_envelope.domain', 'filesystem'),
    ('capability_envelope.domain', 'sockets'),
    ('capability_envelope.domain', 'http'),
    ('capability_envelope.domain', 'clocks'),
    ('capability_envelope.domain', 'random'),
    ('capability_envelope.domain', 'environment'),
    ('capability_envelope.domain', 'process_spawn'),
    ('capability_envelope.domain', 'ipc'),
    ('capability_envelope.domain', 'crypto_keys'),
    -- Core: SPEC §13 abstraction_class.id_pattern (one closed pattern value).
    ('abstraction_class.id_pattern', '<slug>.v<integer>'),
    -- Profile: agent-assurance subject_class (extensible; 2 closed values for INV06 triggering).
    ('subject_class', 'downstream-change'),
    ('subject_class', 'self-modification'),
    -- Profile: agent-assurance provider_id (extensible; closed-but-extensible identifiers).
    ('provider_id', 'anthropic'),
    ('provider_id', 'openai'),
    ('provider_id', 'google'),
    ('provider_id', 'xai'),
    ('provider_id', 'mistralai'),
    ('provider_id', 'meta'),
    ('provider_id', 'deepseek'),
    ('provider_id', 'qwen'),
    ('provider_id', 'human'),
    ('provider_id', 'other'),
    -- Profile: agent-assurance model_family_id (extensible; distinct axis from provider_id).
    ('model_family_id', 'claude'),
    ('model_family_id', 'gpt'),
    ('model_family_id', 'gemini'),
    ('model_family_id', 'grok'),
    ('model_family_id', 'mistral'),
    ('model_family_id', 'llama'),
    ('model_family_id', 'deepseek'),
    ('model_family_id', 'qwen'),
    ('model_family_id', 'human'),
    ('model_family_id', 'other'),
    -- Profile: com.verivus.runtime witness vocabularies (6).
    ('witness_scheme', 'tls-notary'),
    ('witness_scheme', 'provider-signature'),
    ('witness_scheme', 'tee-quote'),
    ('attester_observed', 'request'),
    ('attester_observed', 'response'),
    ('attester_observed', 'both'),
    -- Profile: com.verivus.runtime mutation vocabularies (8). Closed and
    -- non-enum-backed, exactly like the witness pair above, so their values
    -- belong here rather than in a CHECK list or an enum type.
    ('execution_proof_scheme', 'ledger-transaction'),
    ('execution_proof_scheme', 'provider-receipt'),
    ('execution_proof_scheme', 'tee-quote'),
    ('execution_proof_scheme', 'zk-receipt'),
    ('finality_basis', 'none'),
    ('finality_basis', 'provider-acknowledged'),
    ('finality_basis', 'ledger-confirmed'),
    ('finality_basis', 'ledger-final');
