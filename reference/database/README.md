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

Build DuckDB's maintained native binding with the selected CPython installation
and its matching development headers. At baseline
`12cb56dd0a6ce892d51930554080e2411ec35521`, the reference used the installed
native package without binding it to a retained build identity. The replacement
recipe pins supplier archives, prepares the existing binding and records the
exact native artifacts. There is no installed-package fallback.

```sh
cd tools/dagtoml-duckdb-native-go
GOTOOLCHAIN=go1.26.10 go run . --version 1.5.3 \
  --python /absolute/path/to/python \
  --cache /absolute/path/to/archive-cache \
  --output /absolute/path/to/repository/.local/database-ci/duckdb-driver/1.5.3/cpython-311
```

The output ABI directory must match the interpreter. Set
`DAGTOML_DUCKDB_VERSION=1.5.0` when selecting the floor build. Supplier origin
identities remain in `requirements/database*.txt` for advisory matching. Those
files describe native inputs and are not installation instructions. The local
variant retires optional Python ecosystem conversion; UUID output is canonical
text and timezone-aware timestamp output is UTC. See the native builder README
for supported platforms, input inventories and remaining audit boundaries.

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
support modules, native PostgreSQL Go sources and module locks, the complete native DuckDB recipe, engine lock,
and pinned dependencies. Missing or escaping paths
fail. SQL artifacts are hashed separately and verified by execution to avoid a
seed/hash cycle. The bare 64-character lowercase bundle digest never substitutes
for a document hash or `closure_root`. One database belongs to one immutable bundle.

`Store` accepts a dedicated idle connection and an optional callback returning a
fresh connection to the same destination. PostgreSQL uses preparatory autocommit
reads and an explicit outer transaction. SQLite enables and reads back foreign
keys and requires CHECK constraints enabled before BEGIN. Embedded DuckDB has one
writer process and serializes callers within it; another writable process is
refused. An active caller transaction is rejected without commit or rollback.

The private-lane concurrency harness replaces the executor dependency from
`4069dfababe2b74bb1ed7fc8795cc0a8263e7943` with explicit worker threads.
Initialization and repeated-write races still use two simultaneous contenders;
the SQLite lock-exhaustion probe uses one. Results preserve input order and
worker exceptions fail the lane. A shared deadline bounds waiting, and startup
or deadline failure releases peers at the supplied barrier. Python cannot
cancel a stuck native driver call: a failed lane must abandon its private
destination and process. No partial worker results become a successful receipt.
Worker controls run under the cold import guard; persistent engine lanes
separately exercise the real initialization and writer outcomes. This does not
complete native driver, subprocess or build dependency audits.

Receipt source binding replaces the inherited-environment Git calls from
`a867058bc03a98c9b1a478543b690f046fe25a7d` with the owned Git transport.
It verifies the selected repository root and named commit, ignores inherited
Git location/index/configuration overrides, and records complete status and
tracked-diff digests. The clean-receipt gate also rejects untracked content.
The DuckDB external-writer probe shares the bounded native child transport
with the cold-guard launcher: both own and reap their child, drain both output
streams, and fail on deadline or output overflow. These Python import-boundary
repairs do not establish absence inside Git, database engines or build tools.

The byte comparison also repairs index-cache assumptions measured at
`543bc3e3665131854ad7b109d59b562e28664f3f`. A clean Git status is accompanied
by direct SHA-256 comparison of committed, indexed and working contents and
Git executable modes. The `git-source-bytes-v1` delta is length framed and
does not render a Git patch or apply content filters. Link text is captured;
symlinked ancestors, special file types, unmerged entries and unassessed
submodules refuse binding. Checkouts whose raw bytes differ through content
normalization remain working files. Source identities still do not attest the
runtime environment or complete the native dependency audit.

The PostgreSQL connector requires text connection parameters and an optional
text database name. It normalizes string subclasses to their underlying text
and rejects NUL before loading the driver or opening a connection. Invalid
text raises `StorageError` with code `setup`; nontext raises `TypeError`.
The connector at `7d871361d4275860dab54b628894a54d20d977e6` loaded the
Psycopg Python stack. It is replaced by the [native reference session](../../tools/dagtoml-postgres-go/README.md),
whose prepared Go sources replace the supplier's password-file matcher and
connection-error redactors. PostgreSQL uses separate protocol parameters,
actual server transaction state and primary-message/SQLSTATE errors. Its
Python bridge preserves the reference store's supported values and abandons
the owned child on timeout or malformed framing. Build the native client
before using PostgreSQL; the private CI runner builds it automatically.
The executed lane runs with site disabled and guards both the main thread
and new workers. Receipts require that guard, the current driver source and
dependency identities, and the retained executable/build record. These
client checks do not complete the server, compiler or wider tool audits.

The DuckDB connector uses the installed native interface. Its destination is
text, either supplied directly or returned by the filesystem path protocol.
It reads the underlying text of a string subclass and rejects NUL bytes before
opening the destination. Byte paths and nontext protocol results are rejected.
This entry-point repair targets the connector at
`eaefe4ca6146fcfd3a433a183c102f5a283922b6`; native binding, engine and build
dependency audits remain separate requirements.

The maintained native reference connector uses structured DuckDB errors and
returns only their primary message in the original exception class. An error
without a valid structured primary message becomes a neutral native error.
The connection starts in structured error mode. If a caller disables that
mode, errors stay neutral until the setting is restored. The prepared SDK
does not register caller-frame replacement scans. These boundaries were
repaired after actual missing-table errors on
`c7c58b131d8c6d03a2c512a30ae61ea69c25124f` exposed a forbidden parser
import and query context in the public error.

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
`commit-outcome-unknown` with the attempted source paths, prefixed content hashes,
and contract-bundle digest. Initialization reports its contract identity instead
of a document batch. Inspect the destination before acting on that outcome;
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

The API snapshot digest follow-up covers `validators/validate_api_snapshot.py`
`_DIGEST_RE`, `is_digest`, and its three `validate_one` call sites:
`snapshot.request.descriptor_sha256`, `snapshot.response.body_sha256`, and
`witness.attestation_sha256`. It must preserve declared algorithms and lengths
while adding independent whole-string shape controls across implementations.

Graph/RDF artifacts retain separate models and checks. The Neo4j seed's
incomplete kind/entity population is recorded in
[ISS-002](../../docs/issues/2026-05-23-iss-002-graph-cypher-seed-incomplete.md).
Complete SQL catalogs and this ingestion path do not imply universal kind
validation or complete graph ingestion.

The native RDF tool's `check-prefix-shapes --repo-root .` gate reads
`rdf/shapes.ttl`, parses Turtle with the same parser as `verify`, and
evaluates the identifier-prefix query subset used by the three declared
prefix shapes. It exercises targeted label graphs with accepted and
rejected prefixes, absent labels, and unrelated classes. Unsupported
query forms or selected-shape properties fail the gate. This replaces
the Python SHACL processor previously used by that specific CI check;
it does not provide general SHACL conformance or validate the other
hand-authored graph invariants.

Native enum hints in `vocabulary-storage.toml` describe PostgreSQL and DuckDB
types, including retained compatibility types. Every engine compares its complete
backing-hint metadata with the mapping. These hints do not assert column
enforcement; the mapped use sites and executed write probes establish that.
