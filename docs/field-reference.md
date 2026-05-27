# Field Reference

This is a compact index for humans, agents, and editor tooling. The
normative rules remain in [spec.md](../spec.md), the `*-kind.toml`
descriptors, and the ontology files.

## Root Metadata

Every DAG-TOML document starts with `[meta]`.

| Field | Type | Required | Applies to | Purpose |
| --- | --- | --- | --- | --- |
| `schema_version` | string | yes | all files | Semver file-shape version. Validators reject unsupported major versions. |
| `template_kind` | string | yes | all files | Selects the kind descriptor and validator behavior. |
| `docs` | string URL | no | all files | Points agents/tools to the human-readable spec or descriptor. Informational only. |
| `framework_profile` | string | no | profile files | Selects an optional profile such as `agent-assurance`. |
| `ontology_version` | integer | kind-dependent | ontology-backed files | Pins entity, relation, and attribute vocabulary. |
| `title` | string | kind-dependent | examples and authored files | Human-readable document title. |
| `created` | date string | kind-dependent | authored files | Document creation date. |

`docs` is deliberately optional. Validators MUST NOT fetch it during
normal validation; local descriptors and ontology files remain the source
of truth.

## Core Kinds

| `template_kind` | Main sections | Key fields | Validator |
| --- | --- | --- | --- |
| `implementation-dag` | `[units.<id>]`, `[computed]` | `depends_on`, `blocks`, `produces`, `consumes`, `files_modify`, `estimated_loc`, `status`, `layer` | `validators/validate_implementation_dag.py` |
| `traceability` | `[[requirements]]`, `[[tests]]`, `[[code]]`, optional intent/feature/regulation/decision/output sections | `id`, `requirement_kind`, `test_kind`, `priority`, `verifies`, `verified_by`, `constrains`, `path` | `validators/validate_traceability.py` |
| `readiness-gate` | readiness entries | `id`, `status`, evidence/review references | `validators/validate_review_readiness.py` |
| `contract-declaration` | contract entries | `id`, `status`, contract/evidence references | `validators/validate_review_readiness.py` |
| `evidence-matrix` | evidence rows | `id`, evidence target, status/reference fields | `validators/validate_review_readiness.py` |
| `kind-descriptor` | `[kind]`, `[[kind.required_fields]]`, `[[kind.required_sections]]`, `[[kind.hard_invariants]]`, `[[kind.example]]`, `[kind.relation_to_ontology]` | `describes_kind`, `name`, `summary`, `prose`, `enforced_by`, `predicates_used` | `validators/validate_kind_descriptor.py` |

## Agent Assurance Profile Kinds

| `template_kind` | Main sections | Key fields | Validator coverage |
| --- | --- | --- | --- |
| `spec-contract` | guarantee/contract declarations | profile-specific guarantee and scope fields | IJB conformance plus TOML parse |
| `threat-model` | `[[threats]]` | `likelihood`, `impact`, `residual_risk`, `detection`, `mitigation` | IJB conformance plus TOML parse |
| `smoke-validation` | `[[checks]]`, `[result]` | `status`, `decision`, `evidence` | IJB conformance plus TOML parse |
| `rollback-plan` | rollback trigger/action sections | `trigger_kind`, owner/action fields | IJB conformance plus TOML parse |
| `adapter-contract` | adapter identity/runtime/fixture sections | `runtime_kind`, runtime policies, fixture references | IJB conformance plus TOML parse |
| `assertion-bundle` | assertion bundle entries | canonical assertion lines, provenance, input hashes | IJB conformance plus TOML parse |
| `gate-decision` | decision/result sections | `verdict`, cited bundles, constraints | IJB conformance plus TOML parse |
| `assertion-log-record` | append-only log record sections | record hash/signature fields, bundle citation | IJB conformance plus TOML parse |
| `adapter-registry-binding` | registry binding sections | `registry_scheme`, trust anchors, policy constraints | IJB conformance plus TOML parse |

The profile's closed value sets live in
[profiles/agent-assurance/ontology.toml](../profiles/agent-assurance/ontology.toml).

## What vs How

| DAG-TOML declares | Runtime decides |
| --- | --- |
| Document kind and schema version | Which parser and command path to use |
| Dependency and artifact graph | Scheduling, retries, concurrency, and execution backend |
| Required evidence and review state | UI, notifications, persistence, and approval workflow |
| Relation vocabulary and allowed values | Storage indexes, caches, and query acceleration |
| Optional `docs` pointer | Whether to fetch, cache, or ignore external docs |
