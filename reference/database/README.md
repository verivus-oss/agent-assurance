# Reference database storage

This directory provides **non-normative** storage guidance and executable
examples. TOML ontologies and kind descriptors remain authoritative. These
tables do not add a template kind, a JSON Schema layer, or a runtime.

[MANIFEST.toml](MANIFEST.toml) identifies the artifacts and registry counts.
[vocabulary-storage.toml](vocabulary-storage.toml) assigns every discovered
vocabulary an explicit disposition and identifies actual enforcing columns.
At source commit `7353cd1209d8f4defa36e5cbd8eaa49bfe82b102`, the ontologies
declare 50 vocabularies and 216 literal values, including 123 values in closed
vocabularies. Generation and checks derive those populations from the tree.
An empty catalog, such as `license`, remains an explicit declaration.

## Catalogs and constrained fields

PostgreSQL, SQLite, and DuckDB catalog **every declared value** in
`attribute_value_allowed`, including values also represented by native enums.
Catalog membership and column enforcement are different properties. Optional
`backing_enum_type` and legacy SQLite `backing_check_constraint` metadata are
discovery hints. The mapping and executed probes identify enforcement sites.

Existing `entity` columns retain priority, unit/review status, likelihood,
impact, residual-risk, and smoke-check-status constraints. `runtime_document`
adds three disjoint projections:

| Kind | Required columns | Optional column |
| --- | --- | --- |
| `adapter-contract` | `runtime_kind`, `runtime_network_policy`, `runtime_clock_policy` | `adapter_id_derivation` |
| `adapter-registry-binding` | `adapter_ref_syntax` | none |
| `gate-decision` | `gate_decision_verdict` | none |

Columns belonging to another kind must be SQL NULL. The named
`runtime_document_kind_shape` check uses explicit `IS NOT NULL` predicates
for required columns. NULL means absence or inapplicability, never malformed
TOML. PostgreSQL/DuckDB use enum columns; SQLite uses binary-comparison CHECK
constraints and STRICT tables. A composite FK binds the projection's ID and
kind to the same `instance_file` row. Duplicate projections, dangling parents,
and mismatched parent kinds are rejected. The new relationship restricts
parent deletion. The helper provides no deletion or garbage-collection API.

Views `adapter_contract_document`, `adapter_registry_binding_document`, and
`gate_decision_document` expose projections with source metadata. PostgreSQL
and DuckDB use schema `dagtoml`; SQLite prefixes names with `dagtoml_`.

`severity_tier` and `override_rule_operator` remain runtime-operand catalogs
with five and nine tokens respectively. They add no document fields or rule
evaluation. The other authority catalogs likewise describe operands inside
opaque rule strings. Pattern vocabularies, capability domain keys, profile
namespace partitions, extensible strings, and loaded registry-scheme extensions
retain their distinct specification rules.

## Source bytes and indexes

`runtime_document.source_toml` holds the exact original bytes.
`instance_file.content_sha256` is `sha256:` plus their 64 lowercase hex
characters. Provenance describes a different subject: the cited upstream
source's prefixed hash and byte **count** in `provenance.source_sha256` and
`provenance.source_bytes`.

The helper validates and projects one captured root buffer without reopening
it. Existing validators resolve cited local provenance inputs separately under
the trusted repository root. The helper does not fetch registries, evidence,
fixture references, or artifacts.

| Index | Source and behavior |
| --- | --- |
| `source_path` | Caller-supplied nonempty, NUL-free UTF-8 identity label, preserved exactly |
| schema, ontology, and kind columns | Validated meta values; permitted absent ontology version is NULL |
| `framework_profile` | Original `agent-assurance` or `AGDF` spelling; only profile identity comparison uses the alias |
| `title`, `docs_url` | Optional string `meta.title` and `meta.docs` |
| `created` | Native TOML date or valid exact `YYYY-MM-DD` string |
| `created_at`, provenance `captured_at` | Offset datetime or valid offset-bearing RFC3339 string normalized to UTC; local datetime and malformed offsets stay unindexed |
| `meta_extras`, provenance `extras` | Supported optional properties excluding individually indexed keys |
| provenance identity/count | Its own validated path, canonical prefixed hash, and nonnegative signed 64-bit byte count |
| provenance optional text | `extraction_method` and `source_description` when representable |
| `ingested_at` | Engine-generated ingestion time |

Optional JSON indexes support NUL-free strings/keys, booleans, finite floats,
integers from -9007199254740991 through 9007199254740991, and recursive
arrays/tables of those values. An unsupported top-level extra property is
omitted as a whole. Native dates/times, larger integers, nonfinite floats, and
nested NUL-containing strings/keys remain in the original bytes. Unsupported
optional scalar indexes become NULL. Every omission appears in
`unindexed_fields` as a literal path-segment array. Mandatory identity fields
cannot be omitted. PostgreSQL requires UTF8 server and client encoding.

JSON audit ignores object key order and equivalent Unicode escapes. It preserves
array order, exact strings, property presence, and boolean versus numeric types.
Numbers compare as exact decimal JSON values, so `1` and `1.0` agree. Text JSON
with duplicate keys is rejected. Indexes are not completeness/authenticity claims.

## Initialize and ingest

Install optional drivers separately from ordinary TOML validators:

```sh
python3 -m pip install --require-hashes -r requirements/database.txt
python3 -m pip install --require-hashes --no-binary tomli -r requirements/toml.txt
```

Load the engine's `schema.sql` and `seed.sql` into a fresh private destination.
Those files leave `reference_contract` and `runtime_document` empty. Rust/Go
DuckDB loader outputs are likewise seed-only artifacts. Initialize explicitly
before ingesting documents or other instance data:

```sh
python3 reference/database/ingest_runtime_document.py \
  --engine sqlite --destination .local/reference.db \
  initialize --exclusive-unpublished
python3 reference/database/ingest_runtime_document.py \
  --engine sqlite --destination .local/reference.db \
  ingest examples/minimal-adapter-contract.toml examples/minimal-gate-decision.toml
python3 reference/database/ingest_runtime_document.py \
  --engine sqlite --destination .local/reference.db audit
```

Initialization requires exclusive ownership of an unpublished, empty destination.
It checks the executed catalog and exercises accepted/rejected SQL writes. Each
probe has valid setup in its own transaction and always rolls back. Setup
failure is not constraint rejection. Initialization then publishes one contract
row. It refuses populated destinations and is not a production write probe.
An empty, already initialized destination must have the same bundle identity.

The bundle digest uses `_contract.py`, `bundle_digest`: a versioned ASCII domain,
zero separator, unsigned 64-bit big-endian entry count, then path-byte length,
canonical UTF-8 relative path, and raw SHA-256 bytes for each sorted entry.
Its population includes specification prose, discovered ontologies, kind/profile
descriptors, assertion grammar, storage mapping, Python validators and database
support modules, engine lock, and pinned dependencies. Missing or escaping paths
fail. SQL artifacts are hashed separately and verified by execution to avoid a
seed/hash cycle. The bare 64-character lowercase bundle digest never substitutes
for a document hash or `closure_root`. One database belongs to one immutable bundle.

`Store` accepts a dedicated idle connection and an optional callback returning a
fresh connection to the same destination. PostgreSQL uses preparatory autocommit
reads and an explicit outer transaction. SQLite enables and reads back foreign
keys and requires CHECK constraints enabled before BEGIN. Embedded DuckDB has one
writer process and serializes callers within it; another writable process is
refused. An active caller transaction is rejected without commit or rollback.

Ingestion supports the three kinds above, agent-assurance/AGDF, and schema major
zero. It runs metadata, provenance, IJB, closure, controlling-descriptor/capability,
and implemented kind checks, reporting that scope. Adapter/binding INV04 prohibits
execution, registry contact, fixture dereference, artifact verification, and trust
or policy evaluation. Gate INV01 through INV06 remain, including provider and
model-family independence for self-modification. Loose observed-line shape checks
are not a complete assertion-grammar parser.

A batch writes metadata, optional provenance, and the projection atomically.
Repeated `(source_path, content_sha256)` identities return an existing ID only
after full byte, projection, bundle, metadata and provenance comparison.
Metadata-only or conflicting rows fail without upsert. Changed bytes create a
new version; identical bytes at another path create a separate occurrence.
Transient conflicts use bounded whole-operation retries.
If a pre-commit error is followed by a failed rollback acknowledgement, the
helper reports `rollback-unconfirmed` and preserves the original failure in
the diagnostic. Dispose of that connection before another operation.

Success follows commit acknowledgement. After acknowledgement loss, a fresh
connection reconciles the complete batch before reporting committed state or
retrying an absent batch. Unavailable/conflicting reconciliation returns
`commit-outcome-unknown`. Inspect the destination before acting on that outcome;
it is not a rollback claim.

## Audit, migration, and adoption

`audit` reparses and revalidates supported stored documents, rehashes their bytes,
and compares deterministic indexes, projections, provenance, and bundle identity.
Affected metadata-only rows are explicit failures. Other kinds are outside the
reported population. Administrator SQL changes are outside the ingestion
interface; vocabulary constraints alone cannot prove blob/index agreement.
Audit checks local integrity, not signatures or evidence authenticity.

Rebuild side by side. Retain the old database, load and initialize a fresh one,
then replay every original source version. `replay_runtime_documents.py` accepts
a TOML manifest with one record per selected legacy row:

```toml
[[sources]]
source_path = "the-original-identity.toml"
source_file = "archive/original-version.toml"
content_sha256 = "sha256:<the legacy row's 64 lowercase hex characters>"
```

`source_file` resolves relative to the manifest directory. Replay checks bytes
against the legacy hash and validates every source before one batch write.
Missing/invalid versions produce explicit failed entries and prevent the batch
from writing; valid entries remain visibly pending. The helper never reconstructs
source from metadata or entity JSON. Supply `--report` for the persistent report.
Switch consumers only after replay, audit, population reconciliation, and consumer
queries pass. Rollback switches consumers to the retained old database.

Consumers of the former 152-row SQL catalogs must accommodate the complete
catalog, including enum-backed values. Parent-deletion policies must account for
the restrictive FK. Registry extensions require a rebuilt destination with their
new trusted bundle. This helper does not migrate arbitrary entity/relation
payloads, add cross-document inheritance, or establish agentfederator runtime
enforcement.

## Executed gates and residual work

[engine-lock.toml](engine-lock.toml) pins PostgreSQL 14.0/16.14, SQLite
3.38.0/3.53.2, and DuckDB 1.5.0/1.5.3. SQLite checks Python's actual linked
library. Both DuckDB driver locks include the timestamp-conversion dependency.
libSQL compatibility is unverified and requires a separate lane.

Receipts bind connected engine versions, source commit/tree, bundle/artifact
hashes, exact executed catalogs, SQL probes, and storage/protocol outcomes.
Missing engines, wrong versions, stale receipts, empty specimens, and failed
setup cannot satisfy the full gate. `validators/check_database_vocabularies.py`
executes fresh artifacts and writes one selected-lane receipt.
`validators/check_attribute_values.py --receipts ...` requires the complete engine
and loader matrix. Its explicit `--declarations-only` mode reports omitted
execution. It never infers SQL behavior by parsing schema or seed text.
The required aggregate invokes it through `check_sql_source_access.py`, which
makes SQL source unavailable except through the opaque hash API. Its receipt
controls reject absent lanes, stale source/binaries, altered probe populations,
failed outcomes, and missing connection or replay checks.
`generate_allowed_values.py --write` replaces only the unique marked catalog
block in each seed; default mode detects generation drift.

`.github/workflows/database-vocabularies.yml` builds each pinned lane and both
loaders, then runs `database-vocabulary-gate` with `always()`. The aggregate
requires every dependency to succeed and all eight artifact-bound receipts.
`runtime_ci.py` builds the primary validators and pinned syscall instrument,
runs the independent specimens and invariant-ownership gate, and exercises
SQL, validator, ownership, and discovery failure controls. Review and local
test artifacts stay under gitignored `.local/`; CI uploads only its selected
`.local/database-ci/` results, never local review directories.

The existing required `validate` job retains the state-mutation database
round-trip until maintainers establish and verify the new required aggregate
in both repository rulesets and classic branch protection. Failed and skipped
dependency candidates must demonstrate merge blocking before that transition
is complete. A workflow definition alone does not establish branch protection.

The mapping carries explicit residuals derived from every descriptor:

| Population | Disposition |
| --- | --- |
| Adapter/binding INV01 through INV03 | Implemented owners, independent accepted/rejected fixtures in every route |
| Adapter/binding INV04 | Instrumented scope boundaries |
| Adapter emits and fixture sections | Required nonempty, well-formed collections |
| Gate `decision.cited_bundles` | Open `enforce-gate-decision-cited-bundles` |
| Other required sections | Individual open `audit-required-section-instance-enforcement` entries |
| Smoke INV01 through INV03 and `smoke.decision` storage | Open `promote-smoke-validation-result-decision`; smoke-check status columns and shared IJB remain |
| Assertion-bundle/log-record INV01 through INV03 | Open dedicated-validator follow-ups |
| Spec-contract/threat-model INV01/INV02 | Open dedicated-validator follow-ups |
| API snapshot kind-only digest suffix grammar | Open `tighten-api-snapshot-digest-shape`; closure and sub-part consistency remain |

Graph/RDF artifacts retain separate models and checks. The Neo4j seed's
incomplete kind/entity population is recorded in
[ISS-002](../../docs/issues/2026-05-23-iss-002-graph-cypher-seed-incomplete.md).
Complete SQL catalogs and this ingestion path do not imply universal kind
validation or complete graph ingestion.
