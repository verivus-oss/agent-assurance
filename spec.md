# DAG-TOML Specification

**Document maturity:** Draft Specification
**Schema version:** 0.1.0
**Status:** public draft release (see
[GOVERNANCE.md §Releases](GOVERNANCE.md#releases))

The draft maturity label describes the stability of this document. It
is distinct from `schema_version`, which pins the on-file compatibility
contract for DAG-TOML documents. Release tags use calendar-versioned UTC
timestamps during pre-1.0 development unless a release explicitly binds to
the schema version, as `v0.1.0` does for the initial public draft. Tags are
separate from document maturity labels.

If an AI agent can generate 10,000 lines of functional code in seconds,
relying on a human to manually read the diff to catch a subtle
supply-chain mutation is impossible. *Writing the code is becoming the
new assembly language.* The work shifts upward, to two problems that
were previously too expensive to solve at scale:

- **Provable Intent** — mathematically validating what a change *means*,
  not what bytes it touched.
- **Structural Governance** — mapping and enforcing the logic graph of
  an artifact, so abstraction boundaries are never silently violated.

DAG-TOML is the data substrate for both. It is only "too complex" if
you are building a bicycle. If you are building autonomous,
self-generating infrastructure, provable clarity is the minimum barrier
to entry.

This document defines the file format, root-table shape, versioning rules,
and extension model for DAG-TOML.

---

## 1. Scope

DAG-TOML is a family of TOML schemas for describing how software-engineering
agents plan, sequence, and prove their work. A DAG-TOML file is a single
TOML document whose **root `[meta]` table** declares its kind, schema
version, and (optionally) the profile it belongs to.

DAG-TOML is a **format specification**. It does not prescribe an execution
model. Reference implementations consume DAG-TOML files and may persist
state in databases of their choosing; those implementations are out of
scope for this document.

DAG-TOML separates **what** a conforming document declares from **how**
software acts on it:

| Layer | Owns |
|---|---|
| DAG-TOML document | Identity, dependency shape, traceability, evidence expectations, review state, profile assertions |
| Validator | Structural and semantic conformance checks against this spec, kind descriptors, and ontologies |
| Runtime / control plane | Scheduling, sandboxing, execution, retries, persistence, signing, transport, UI, and policy enforcement |

---

## 2. Root table

Every DAG-TOML file MUST have a `[meta]` table at the root with at least
these fields:

```toml
[meta]
schema_version  = "0.1.0"                # semver string
template_kind   = "implementation-dag"   # see §3
docs            = "https://github.com/verivus-oss/agent-assurance/blob/main/spec.md"
# framework_profile = "agent-assurance"  # optional; omit for core
```

### 2.1 Why `[meta]` and not `[dag-toml]`

This spec inherits the root-table convention from existing tooling that
already consumes thousands of TOML files in this shape. A renamed root
table would force a coordinated v2 schema event across runtimes,
validators, examples, and policy packs for no semantic gain. The
`template_kind` field already discriminates between formats; a wrapping
root table would be redundant.

### 2.2 `schema_version`

`schema_version` is a semver string (e.g. `"0.1.0"`). Validators MUST
reject files whose `schema_version` major component is higher than the
validator supports. Minor and patch components signal additive,
backwards-compatible changes.

`schema_version` pins the **file shape** only. The **relation
vocabulary** (which entities exist, which predicates connect them) is
pinned separately by `ontology_version` (see
[core/ontology.md](core/ontology.md)). Both bumps MAY occur
independently.

`ontology_version`, when present, is a monotonic positive integer
snapshot rather than semver. A graph consumer uses it to decide whether
it understands the complete entity, predicate, and vocabulary contract
for the document. The integer is intentionally different from
`schema_version`: ontology changes are vocabulary snapshots, while
schema changes are file-shape compatibility events.

### 2.3 `template_kind`

`template_kind` is a string identifying the schema the file conforms to.
The values defined by this spec are:

| `template_kind` value | Defined in | Profile |
|---|---|---|
| `implementation-dag` | [core/implementation-dag-kind.toml](core/implementation-dag-kind.toml) | core |
| `traceability` | [core/traceability-kind.toml](core/traceability-kind.toml) | core |
| `readiness-gate` | [core/readiness-gate-kind.toml](core/readiness-gate-kind.toml) | core |
| `contract-declaration` | [core/contract-declaration-kind.toml](core/contract-declaration-kind.toml) | core |
| `evidence-matrix` | [core/evidence-matrix-kind.toml](core/evidence-matrix-kind.toml) | core |
| `kind-descriptor` | self-describing (see §2.4) | core |
| `profile-descriptor` | [core/profile-descriptor-kind.toml](core/profile-descriptor-kind.toml) | core |
| `spec-contract` | [profiles/agent-assurance/spec-contract-kind.toml](profiles/agent-assurance/spec-contract-kind.toml) | agent-assurance |
| `threat-model` | [profiles/agent-assurance/threat-model-kind.toml](profiles/agent-assurance/threat-model-kind.toml) | agent-assurance |
| `smoke-validation` | [profiles/agent-assurance/smoke-validation-kind.toml](profiles/agent-assurance/smoke-validation-kind.toml) | agent-assurance |
| `rollback-plan` | [profiles/agent-assurance/rollback-plan-kind.toml](profiles/agent-assurance/rollback-plan-kind.toml) | agent-assurance |
| `adapter-contract` | [profiles/agent-assurance/adapter-contract-kind.toml](profiles/agent-assurance/adapter-contract-kind.toml) | agent-assurance |
| `assertion-bundle` | [profiles/agent-assurance/assertion-bundle-kind.toml](profiles/agent-assurance/assertion-bundle-kind.toml) | agent-assurance |
| `gate-decision` | [profiles/agent-assurance/gate-decision-kind.toml](profiles/agent-assurance/gate-decision-kind.toml) | agent-assurance |
| `assertion-log-record` | [profiles/agent-assurance/assertion-log-record-kind.toml](profiles/agent-assurance/assertion-log-record-kind.toml) | agent-assurance |
| `adapter-registry-binding` | [profiles/agent-assurance/adapter-registry-binding-kind.toml](profiles/agent-assurance/adapter-registry-binding-kind.toml) | agent-assurance |
| `disclosure-attestation` | [profiles/disclosure/disclosure-attestation-kind.toml](profiles/disclosure/disclosure-attestation-kind.toml) | disclosure |
| `redaction-manifest` | [profiles/disclosure/redaction-manifest-kind.toml](profiles/disclosure/redaction-manifest-kind.toml) | disclosure |
| `selective-disclosure-proof` | [profiles/disclosure/selective-disclosure-proof-kind.toml](profiles/disclosure/selective-disclosure-proof-kind.toml) | disclosure |
| `cost-record` | [profiles/cost/cost-record-kind.toml](profiles/cost/cost-record-kind.toml) | cost |

Each `*-kind.toml` is itself a DAG-TOML document with
`template_kind = "kind-descriptor"`. The descriptor carries the prose
explanation, the required-field rules, hard-invariant pointers, and
the worked-example pointer for the kind it describes, in one
machine-readable document that LLM agents and humans can both consume.
A reference validator for the descriptor format lives at
[validators/validate_kind_descriptor.py](validators/validate_kind_descriptor.py).

Profiles MAY define additional `template_kind` values; values defined by
this spec MUST NOT be reused by extensions with different semantics.

### 2.4 The kind-descriptor recursion boundary

`kind-descriptor` is itself a `template_kind`. The natural question is
"what describes the kind-descriptor kind?" Answer: a single
self-describing file would be the recursion stop. This spec does not
ship that self-descriptor; the descriptor format is defined
normatively by §2.3 above (the table and the paragraph following it)
and by
[validators/validate_kind_descriptor.py](validators/validate_kind_descriptor.py).
Recursion stops here; tooling MUST NOT require a
`kind-descriptor-kind.toml` to exist.

### 2.5 `framework_profile`

`framework_profile` is OPTIONAL. Absence indicates the file uses only
core DAG-TOML. The spec-reserved values defined by this
spec are:

- `agent-assurance` — see [profiles/agent-assurance/](profiles/agent-assurance/)
- `disclosure` — see [profiles/disclosure/](profiles/disclosure/)
- `cost` — see [profiles/cost/](profiles/cost/)

Profile names occupy a single global namespace observed across every
ecosystem that consumes DAG-TOML. To make collisions structurally
impossible, this spec partitions that namespace:

1. **Unprefixed names** (matching `^[a-z][a-z0-9-]*$`, kebab-case) are
   **reserved for spec-reserved profiles** that ship in this repository under
   `profiles/<name>/`. Other organisations MUST NOT publish a profile
   under an unprefixed name. The set of unprefixed names this spec
   acknowledges is the table in §2.3 — see the
   `profile-descriptor` files at `profiles/<name>/PROFILE.toml`
   (per §6.1) for the authoritative enumeration. A validator MUST
   reject any `framework_profile` value matching the unprefixed
   pattern that does not appear in the loaded profile-descriptor set.
2. **Reverse-DNS names** (matching `^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)+$`,
   so they contain at least one dot) are **reserved for
   non-spec-reserved (private or third-party) profiles**. Adopters
   under their own domain MUST publish profiles under their reverse-DNS
   prefix — e.g. `com.example.internal`, `org.acme.compliance`. No
   central authority registers these names; the DNS namespace itself
   provides uniqueness without infrastructure on the spec's side.
3. **Other shapes** (mixed case, underscores at the start, single
   labels with dots elsewhere) are reserved for future use and MUST
   NOT appear in `framework_profile` today.

> **Internal codename note.** Earlier drafts of the Agent Assurance
> Profile used the codename **AGDF**. Files in the wild may still carry
> `framework_profile = "AGDF"`; readers SHOULD treat that value as an
> alias for `"agent-assurance"` until those files are migrated. The
> alias predates the namespacing partition above and is honored on a
> grandfather basis only — no new aliases of unprefixed spec-reserved names
> will be added.

The machine-readable contract describing a profile (its spec-reserved
status, the kinds it contains, the profiles it extends, its license
and confidentiality posture) is the `profile-descriptor` kind defined
in §6.1.

### 2.6 Other `[meta]` fields

Per-kind specs define additional fields (`title`, `created`, file
pointers, etc.). The fields above are the only ones common to all
DAG-TOML files.

`docs` is an OPTIONAL URL string pointing to the human-readable
specification for the file's `template_kind`. It exists for agents,
editors, and automation that discover a DAG-TOML file without already
knowing this repository. Public examples and kind descriptors SHOULD set
`docs` to the canonical specification or descriptor URL when a stable URL
is available. Validators MUST NOT require network access to read `docs`;
the field is discoverability metadata, not a conformance dependency.

When `docs` is set, the URL MUST start with `https://` and MUST NOT
contain a query string (`?…`) or fragment-encoded session state. The
field is intended to remain citable across mirrors and archives;
schemes other than `https://` and query-string parameters defeat
that intent. A bare `#anchor` is permitted.

See [docs/field-reference.md](docs/field-reference.md) for a compact
field-reference index across the root metadata, core kinds, and Agent
Assurance Profile kinds.

### 2.7 Confidentiality, license, and embargo

DAG-TOML files travel across organisational boundaries. The spec
provides three small, informational `[meta]` fields so a file's
disclosure posture is machine-readable without prescribing key
management or transport security (both of which are RUNTIME-SPEC):

```toml
[meta]
confidentiality = "public"            # see closed set below
license         = "Apache-2.0"        # SPDX-style label or LicenseRef-*
embargo_until   = "2026-09-01"        # RFC 3339 date; see rule below
```

**`confidentiality`** is OPTIONAL. When present, the value MUST be
drawn from the closed set declared in
[core/ontology.toml](core/ontology.toml) under the
`confidentiality` attribute vocabulary:

`public | restricted | confidential | trade-secret | embargoed`

Absence is equivalent to no declared posture and SHOULD be treated
as `public` only when the file is published openly. Validators MUST
NOT change file behaviour based on this value; the field is a
declared posture that editors, CI mirrors, control planes, and
auditors act on. The vocabulary is closed by design (additions to
the set bump the core `ontology_version`).

**`license`** is OPTIONAL and free-form. The value SHOULD be either
a current SPDX identifier (e.g. `Apache-2.0`, `MIT`,
`CC-BY-SA-4.0`) or, for non-SPDX licenses, the literal prefix
`LicenseRef-` followed by an opaque identifier
(e.g. `LicenseRef-Proprietary`,
`LicenseRef-Internal-Group-Only`). The spec does not track the SPDX
list (it changes faster than the spec); validators MUST treat the
value as a string-shaped declared posture and MUST NOT attempt to
resolve it against an external license registry.

**`embargo_until`** is OPTIONAL when `confidentiality` is any value
other than `"embargoed"`. **It is REQUIRED when
`confidentiality = "embargoed"`** — an embargoed file with no
embargo expiry is structurally invalid because the embargo has no
fall-off date. The value MUST be an RFC 3339 `full-date` (e.g.
`2026-09-01`) or `date-time` (e.g.
`2026-09-01T00:00:00Z`, `2026-09-01T12:30:00+01:00`) string.
Validators MUST reject values that do not match this syntactic
shape, and MUST also reject `embargo_until` whose syntactic shape
is invalid even when `confidentiality` is not `"embargoed"`.
Validators MUST NOT compare the value against the current
wall-clock; they only check syntax and the cross-field requirement
above. Treating an embargoed file as public before the wall-clock
crosses `embargo_until` is a RUNTIME-SPEC behaviour.

Per-type rules for the three fields above:

- `confidentiality`: if the key is present, the value MUST be a
  string drawn from the closed set; non-string values are rejected.
- `license`: if the key is present, the value MUST be a non-empty
  string; non-string and empty-string values are rejected.
- `embargo_until`: if the key is present, the value MUST be a
  string matching RFC 3339 `full-date` or `date-time`.

The closed `confidentiality` vocabulary, the free-form `license`
shape, and the conditional-requirement rule above are declared in
the core ontology and enforced by the reference validators (see §9).

These three fields are **declared posture**, not upstream evidence.
Per §12.9, posture fields are deliberately NOT inputs to the
closure-root digest — they MAY change without flipping a downstream
`closure_root`.

---

## 3. Naming conventions for inner fields

A previous version of this spec used the single word `kind` at multiple
nesting levels (template discriminator, requirement category, test type,
rollback trigger). That name reuse made schemas ambiguous and made JSON
Schema authoring hard. **This spec uses role-specific field names for
every category-style field** and reserves `template_kind` for the root.

| Field | Where it appears | Allowed values |
|---|---|---|
| `template_kind` | `[meta]` | See §2.3 |
| `requirement_kind` | `[[requirements]]` (traceability) | `functional`, `non_functional`, `policy`, `interface`, `performance`, `correctness`, `operational` (extensible) |
| `test_kind` | `[[tests]]` (traceability) | `unit`, `integration`, `e2e`, `audit`, `property`, `robustness`, `benchmark` (extensible) |
| `priority` | `[[requirements]]` (traceability) | `must`, `should`, `could` (closed; default `must`) |
| `trigger_kind` | `[[rollback.triggers]]` (rollback plan; Agent Assurance Profile) | see [profiles/agent-assurance/rollback-plan-kind.toml](profiles/agent-assurance/rollback-plan-kind.toml) and the profile ontology |
| `[result].decision` | smoke-validation (Agent Assurance Profile) | `pass`, `fail`, `inconclusive` |
| `[[checks]].status` | smoke-validation (Agent Assurance Profile) | `pass`, `fail`, `inconclusive` |

The full closed value sets for profile-defined attributes
(`trigger_kind`, smoke `decision`/`status`, threat `likelihood`/
`impact`/`residual_risk`) are declared in
[profiles/agent-assurance/ontology.toml](profiles/agent-assurance/ontology.toml).

### 3.1 Backwards-compatibility aliases

To accommodate existing files, validators conforming to this spec MUST
also accept the legacy field name `kind` in these locations and treat it
as a synonym for the role-specific name. Validators MAY emit a
deprecation warning. The legacy alias will be removed before the first
stable `schema_version = "1.0.0"`.

---

## 4. ID conventions

DAG-TOML files identify entities with short prefixed strings:

| Prefix | Used for |
|---|---|
| `U01`, `U02`, `U07a`, … | Implementation-DAG units |
| `ART:<slug>` | Internal artifact flowing between units |
| `OUT:<slug>` | Final deliverable leaving the DAG |
| `INT:<slug>` | Intent |
| `FEAT:<slug>` | Feature |
| `REQ:<slug>` | Requirement |
| `REG:<slug>` | Regulation / policy |
| `DEC:<slug>` | Decision |
| `IMP:<slug>` | Implementation note |
| `CODE:<slug>` | Code reference |
| `TEST:<slug>` | Test reference |

Slugs are short kebab-case identifiers. IDs are local to a single
DAG-TOML document set; cross-document references use the same prefix
followed by the document path or external URL.

The full entity inventory, the closed relation vocabulary, attribute
value sets, and extension rules are formalised in
[core/ontology.md](core/ontology.md) (prose) and
[core/ontology.toml](core/ontology.toml) (machine-readable).

---

## 5. Hard invariants

Every conforming validator MUST enforce these invariants on every
DAG-TOML file of the relevant kind:

### Implementation DAG

1. `blocks` is the **exact inverse** of direct `depends_on`.
2. Each `ART:` ID has **exactly one producer** unit.
3. Each `consumes` entry **must match an existing `produces` entry**.
4. `layer` ordering **follows dependency ordering**.
5. `[computed]` values are **derived from `units`** — entry/leaf, max
   parallel, LOC totals, and critical path (longest weighted path).

### Traceability

1. Every `REQ:` referenced from a unit, code, or test exists in
   `[[requirements]]`.
2. Every `[[tests]]` entry references at least one `REQ:`.
3. `requirement_kind` and `test_kind` values, if constrained by the
   profile in use, MUST be drawn from that profile's allowed set.

### Review Readiness

1. `template_kind` is one of `readiness-gate`, `contract-declaration`,
   `evidence-matrix`.
2. Status values are drawn from: `draft`, `blocked`, `ready`,
   `in_review`, `rereview_needed`.
3. Cross-references to the implementation DAG and traceability files,
   when present, MUST resolve.

The **machine-readable contract** for these invariants lives in the
`*-kind.toml` descriptors in [core/](core/) and
[profiles/agent-assurance/](profiles/agent-assurance/), plus the
ontology entries at [core/ontology.toml](core/ontology.toml) and
[profiles/agent-assurance/ontology.toml](profiles/agent-assurance/ontology.toml).
The reference validators under [validators/](validators/) read those
declarations and enforce both the structural rules (required fields,
allowed values, type) and the graph-shaped semantic rules ("`blocks`
is the exact inverse of `depends_on`", "`critical_path` is the
longest weighted path through the DAG", cross-document `REQ:`
reference resolution). No separate JSON Schema layer is shipped or
planned — see §9 for the rationale.

The §5 cycle prohibition is extended in §12.9 to the **closure
graph** induced by `closure_root` inputs: a document MUST NOT,
directly or transitively, cite an upstream artifact whose own
closure depends on this document.

---

## 6. Extension model

A **profile** is a named, optional extension that:

1. Defines new `template_kind` values (each with its own schema).
2. MAY constrain the allowed value sets of role-specific fields
   (`requirement_kind`, `test_kind`, `trigger_kind`).
3. MAY add new `[meta]` fields, but MUST NOT redefine fields specified
   by this document.
4. MUST be selectable by setting `framework_profile = "<profile-name>"`
   in `[meta]`.
5. MUST be described by a single `profile-descriptor` document at
   `profiles/<name>/PROFILE.toml` (for spec-reserved unprefixed profiles) or
   wherever the publisher chooses to ship it (for reverse-DNS-named
   profiles). See §6.1.
6. MUST follow the namespacing partition in §2.5: spec-reserved profiles
   take unprefixed kebab-case names; non-spec-reserved profiles MUST use a
   reverse-DNS name.

Spec-reserved profiles published by this spec are documented in
[profiles/agent-assurance/](profiles/agent-assurance/),
[profiles/disclosure/](profiles/disclosure/), and
[profiles/cost/](profiles/cost/). Each ships a
`profile-descriptor` document (§6.1) so machine consumers can
enumerate the contained kinds without scanning the directory.

### 6.1 The `profile-descriptor` kind

`profile-descriptor` is a meta-meta-layer kind: it documents profiles
the way `kind-descriptor` (§2.3, §2.4) documents `template_kind`s.
A profile-descriptor is a single TOML document with
`template_kind = "profile-descriptor"` and a `[profile]` table
declaring:

| Field | Required | Meaning |
|---|---|---|
| `name` | yes | The exact string used as `framework_profile` in conforming documents. MUST conform to the §2.5 namespacing partition. |
| `namespace` | yes | `"spec.reserved"` for spec-reserved profiles; the reverse-DNS prefix for others (e.g. `"com.example"`). MUST be consistent with `name`. |
| `owner` | yes | Free-form short string identifying the publishing organisation. |
| `license` | yes | SPDX identifier or `LicenseRef-…` (per §2.7). |
| `extends` | yes | Array of zero or more profile names this profile layers on top of. An empty array marks a base profile. Cycles are rejected. Inheritance is declarative: a consumer that loads a descriptor walks `extends` to construct the effective entity / kind / vocabulary set. |
| `ontology` | yes | Repo-relative path to the profile's `ontology.toml`. |
| `contained_kinds` | yes | Closed array of every `template_kind` slug the profile introduces. Each slug MUST resolve to a `*-kind.toml` descriptor whose `[meta].describes_kind` matches the slug. |
| `closure_records` | optional | Array of tables pinning instance-local digest fields of contained kinds as closure inputs (§12.8.1). Each entry declares `contained_kind` / `field` / `presence` and is validated under INV07 (`core/profile-descriptor-kind.toml`). |
| `confidentiality` | optional | Per §2.7. |
| `embargo_until` | optional | Per §2.7. |

A profile-descriptor MUST also follow the IJB substrate rules
(§10): the `[profile]` table is `(thing, structural)`; its
declared fields are agent-assurance metadata mirroring IJB's
structural-Thing role. The reference validator is
[`validators/validate_profile_descriptor.py`](validators/validate_profile_descriptor.py).

The kind itself is described by its own `*-kind.toml` descriptor at
[`core/profile-descriptor-kind.toml`](core/profile-descriptor-kind.toml).
That descriptor is a regular `kind-descriptor` (§2.3); the recursion
boundary at §2.4 still applies — there is no
`profile-descriptor-kind-descriptor.toml`.

Validators walking `extends` MUST:

1. Reject any `extends` entry that does not name a loaded
   profile-descriptor.
2. Reject any cycle in the `extends` graph.
3. Treat the effective set of contained kinds and ontology entries
   as the **union** of the named profile and every transitively
   extended profile.
4. Treat the effective `closure_records` set as the same union, and
   reject duplicate (`contained_kind`, `field`) pairs after the
   union (§12.8.1, INV07).

The spec does not prescribe a registry of non-spec-reserved profiles. A
consuming organisation that wants to inherit from a private profile
MUST ship the parent profile's descriptor alongside the child.

The Agent Assurance Profile (this spec's reference profile) is
documented in [profiles/agent-assurance/](profiles/agent-assurance/).

---

## 7. File and naming conventions

- **Encoding:** UTF-8, no BOM.
- **Indentation:** spaces only, two per level.
- **Arrays:** multi-line arrays use one item per line with trailing
  commas.
- **Filenames:** uppercase descriptive names (e.g.
  `implementation_dag.toml`). Templates ship as `*_TEMPLATE_GENERIC.toml`
  for repo-neutral variants.
- **Repo-shaped variants:** if a template is published in both a generic
  and a repo-shaped form, the repo-shaped form uses the suffix
  `-_SLUG_.toml` and substitutes path conventions.

---

## 8. Versioning policy

- `schema_version` follows semver and pins file shape. While this
  document is a Draft Specification, the current value is `"0.1.0"`;
  the first public stable schema can become `"1.0.0"` when maintainers
  are ready to promise schema stability.
- Adding optional fields, new `template_kind` values, or new profile
  values is a **minor** schema bump after the first stable release.
- Removing fields, changing field semantics, or tightening validation is
  a **major** schema bump after the first stable release and ships with
  a migration note.
- Deprecation warnings precede removal by at least one minor version.
- `ontology_version` is a monotonic positive integer snapshot. Core and
  profile ontologies stay at `1` until the first vocabulary change after
  publication, then advance to `2`, `3`, and so on.
- Adding, removing, renaming, or changing the cardinality/direction of
  an entity, predicate, or attribute vocabulary value bumps the relevant
  core or profile `ontology_version`. Breaking vocabulary changes MAY
  also require a `schema_version` bump when they affect file shape or
  validator conformance.
- Release tags use calendar-versioned UTC timestamps
  (`v<YYYY-MM-DD>T<HH-MM-SS>Z`) and are separate from both fields.

---

## 9. Validation

A conforming DAG-TOML document is validated against TOML-native
artifacts; this spec does not ship JSON Schema.

The contract has two layers, both expressed in TOML:

1. **Structural contract** — declared by the `*-kind.toml` descriptors
   ([core/](core/) and [profiles/agent-assurance/](profiles/agent-assurance/))
   plus the ontology entries in [core/ontology.toml](core/ontology.toml)
   and [profiles/agent-assurance/ontology.toml](profiles/agent-assurance/ontology.toml).
   Required fields, allowed values, ID prefix patterns, and relation
   predicates all live there.
2. **Semantic contract** — graph-shaped invariants that cannot be
   expressed as a flat schema: `blocks` is the exact inverse of
   `depends_on`, `critical_path` is the longest weighted path,
   cross-document `REQ:` reference resolution, `derived_from` and
   `supersedes` chains are acyclic, etc. These live in
   `[[kind.hard_invariants]]` entries inside each descriptor (with
   `enforced_by` pointers).

Both layers are enforced by the reference validators under
[validators/](validators/). The validators read the `*-kind.toml`
descriptors and the ontology files and apply the rules to a candidate
document. This spec does not require any particular validator
implementation; conformance is defined by the prose rules in this
document and by the structural/semantic contracts above.

### 9.1 Why no JSON Schema layer

JSON Schema would be a second declaration of what the kind
descriptors already declare in TOML — exactly the duplication the
descriptor pattern was introduced to eliminate. It also covers a
strict subset (structure only); semantic invariants always require a
companion validator. The cost of authoring and keeping in sync a
parallel JSON Schema would buy at most a marginal improvement over
running the reference validators.

If editor inline-validation (Taplo, Even Better TOML, IntelliJ TOML)
becomes a meaningful adoption ask, the right answer is to generate a
Taplo-compatible JSON Schema from the kind descriptors at build time
and publish it under [schemas/](schemas/) as a derived artifact. That
preserves a single source of truth. The generator does not exist
today; see [schemas/README.md](schemas/README.md) for the rationale
and the work plan.

### 9.2 TOML language version and 1.1 feature disposition

**Parser conformance version: TOML 1.1.0.** The primary normative
implementations parse TOML **1.1.0** (Rust `toml` 1.1, Go
`BurntSushi/toml` v1.6.0, Python `tomli` ≥ 2.4.0). This is a
*cross-implementation parity* decision, not an authoring-surface
expansion: pinning all three parsers to the same released TOML version is
what lets them agree byte-for-byte on every fixture (the foundational
invariant; see §9 and the conformance suite). It does **not** by itself
license any TOML 1.1 syntax in conforming documents.

**Conforming-document syntax surface: TOML 1.0.** A feature does **not**
enter the conforming surface merely because the parser accepts it. Every
syntactic feature that TOML 1.1.0 adds over 1.0.0 is enumerated below
with an explicit disposition. All are **forbidden**: the conforming
DAG-TOML document surface is the TOML **1.0** syntax. The rationale is the
same one that motivates the closure-root rule (§12): a DAG-TOML document
is a SHA-256-bound, audit-grade artifact, and a tight canonical surface —
one obvious way to write a given value — keeps a document's bytes (and so
its hash) meaningful and its content reviewable without decoding.

| TOML 1.1.0 feature (over 1.0.0) | Disposition | Rationale |
|---|---|---|
| Seconds-optional times (`17:45`, also in local/offset date-times) | **Forbidden** | Drops explicit precision and admits two byte-forms of a moment; a SHA-bound artifact requires the full `HH:MM:SS` form. (Also moot: DAG-TOML carries dates/times as quoted strings, e.g. `created = "YYYY-MM-DD"`, never as native TOML date/time values.) |
| `\xHH` hex string escapes (`"\x41"`) | **Forbidden** | A redundant second encoding of characters already writable as literals or `\uXXXX`; redundant encodings weaken canonical form and force a reviewer to decode bytes to see content. |
| `\e` escape (ESC, U+001B) | **Forbidden** | A C0 control character has no legitimate place in a governance document and is a terminal-injection / obfuscation vector. (The existing string rules already discourage control characters; this makes the 1.1 affordance explicitly off-limits.) |
| Newlines (multi-line layout) inside inline tables | **Forbidden** | Multiple valid layouts for the same fragment widen the canonical surface; nested structure is expressed with standard tables / arrays-of-tables, which the kind descriptors already require. |
| Trailing commas inside inline tables | **Forbidden** | A second valid byte-representation of the same inline table; forbidden for the same canonical-form reason. |

**Default-forbid catch-all.** Any TOML 1.1.0 (or later) syntactic
addition **not** explicitly permitted by a row above is **forbidden** in
conforming documents. No feature may enter the conforming surface by
parser default alone; admitting one is a deliberate, reviewed change to
this section.

**Enforcement and backward compatibility.** Several of the forbidden
forms have no place to land in a conforming document in the first place:
no descriptor declares a field whose type is a native TOML date/time, so
the seconds-optional-time form cannot occur (dates and times are carried
as quoted strings, e.g. `created = "YYYY-MM-DD"`). The remaining forbids
are on *syntactic variants* of constructs the documents do use — inline
tables appear (in their TOML 1.0 single-line form), and §9.2 forbids only
their 1.1 multi-line / trailing-comma spellings; basic strings appear, and
§9.2 forbids only the new `\xHH` and `\e` escapes within them. For those,
the forbid is a genuine normative constraint this section adds, made
explicit rather than left to parser default (satisfying the requirement
that dispositions be declared, not inherited). Because no existing
conforming document uses any TOML 1.1-only feature, this disposition
invalidates nothing: every document valid before the 1.1 parser adoption
remains valid after it.

---

## 10. Foundation: IJB

The DAG-TOML format is **IJB-substrate-shaped**. Every entity, every
relation predicate, and every attribute vocabulary in the ontology
reduces to one of the six IJB primitives (Thing, Scope, Path,
Observed, Constraint, Time). The full mapping is normative for the
ontology layer and is enforced by
[`validators/validate_ijb_conformance.py`](validators/validate_ijb_conformance.py)
(see §10.4).

IJB itself ships under [`foundations/ijb/`](foundations/ijb/) in this
repository as relicensed (Apache-2.0) reference material. Readers
SHOULD start at
[`foundations/ijb/primitives.md`](foundations/ijb/primitives.md) for
the primitive definitions and at
[`foundations/ijb/canonical-assertion-grammar.md`](foundations/ijb/canonical-assertion-grammar.md)
for the strict assertion syntax IJB itself uses.

### 10.1 The annotation fields

Every ontology block (`[[entities]]`, `[[relations]]`,
`[[attribute_vocabularies]]`, `[extension_rules]`) and every kind
descriptor block (`[kind]`, `[[kind.required_fields]]`,
`[[kind.required_sections]]`, `[[kind.hard_invariants]]`,
`[[kind.example]]`, `[kind.relation_to_ontology]`) carries an
`ijb_primitive` field with value drawn from the closed set:

`thing | scope | path | observed | constraint | time`

Where the IJB grammar distinguishes structural from instance forms
(`thing` and `path` per
[`foundations/ijb/canonical-assertion-grammar.md`](foundations/ijb/canonical-assertion-grammar.md)
lines 52-62), the same blocks also carry an `ijb_class` field:

`structural | instance`

For `constraint`, IJB uses a different field name (`type=structural|policy|observed`,
per the same source lines 64-70). Agent-assurance mirrors that
distinction with an `ijb_constraint_type` field whose values map
1:1 to IJB's `type`.

`observed` and `time` have no class field in IJB itself; they are
instance-by-nature, and agent-assurance does not add a redundant
class field for them. The `ijb_*` annotation fields on agent-assurance
ontology blocks are **agent-assurance metadata that mirrors IJB's
own distinctions where they exist**, not a literal IJB grammar
fragment.

### 10.2 The mapping (normative)

#### Structural ontology declarations

These appear in `core/ontology.toml`,
`profiles/agent-assurance/ontology.toml`, and the structural blocks
of every `*-kind.toml`.

| Block | `ijb_primitive` | `ijb_class` / `ijb_constraint_type` |
|---|---|---|
| `[[entities]]` (all entity kinds) | `thing` | `structural` |
| `[[relations]]` (all predicates) | `path` | `structural` |
| `[[attribute_vocabularies]]` | `constraint` | `structural` \| `policy` \| `observed` (see note) |
| `[extension_rules]` | `constraint` | `structural` |
| `[meta].framework_profile` | `scope` | `structural` |
| `[meta].template_kind` | `scope` | `structural` |
| `[meta].schema_version` (pins file shape) | `constraint` | `structural` |
| `[meta].ontology_version` (pins relation vocabulary) | `constraint` | `structural` |

> **Note on `[[attribute_vocabularies]]`.** Most attribute
> vocabularies in this spec declare structural-shape constraints (a
> closed value set the data MUST belong to) and use
> `ijb_constraint_type = "structural"`. Vocabularies that declare a
> **policy posture** the SPEC layer does not enforce mechanically
> (e.g. `confidentiality`, `license`, `disclosure_posture`) use
> `ijb_constraint_type = "policy"`. The `observed` value is reserved
> for vocabularies declaring observation-classification rules and is
> not used by anything shipping today, but the validator accepts it.

#### Kind-descriptor blocks (in `*-kind.toml`)

| Block | `ijb_primitive` | `ijb_class` / `ijb_constraint_type` |
|---|---|---|
| `[kind]` | `thing` | `structural` |
| `[[kind.required_fields]]` | `constraint` | `structural` |
| `[[kind.required_sections]]` | `constraint` | `structural` |
| `[[kind.hard_invariants]]` | `constraint` | `structural` |
| `[[kind.example]]` | `observed` | (no class field; instance-by-nature) |
| `[kind.relation_to_ontology]` | `constraint` | `structural` (declares which ontology entries the kind uses; a structural meta-constraint) |

#### Instance facts (in DAG-TOML documents authored against a kind)

| Item | `ijb_primitive` | `ijb_class` / `ijb_constraint_type` |
|---|---|---|
| Entity declarations (`[[requirements]]`, `[[checks]]`, …) | `thing` | `instance` |
| Relation usages (`verified_by = [...]`, `consumes = [...]`) | `path` | `instance` |
| Attribute values (`priority = "must"`, `decision = "pass"`) | `observed` | (no class field) |
| Timestamps (`created`, `duration_s`, `estimated_ttr`) | `time` | (no class field) |

Per the IJB pairing rule
([`foundations/ijb/canonical-assertion-grammar.md`](foundations/ijb/canonical-assertion-grammar.md)
line 120), every structural relation declaration MUST be satisfied by
at least one instance edge in some conforming document. The reference
validators do not enforce cross-document pairing; instance-edge
existence is the responsibility of the consuming repository.

### 10.3 Free-text fields and the explicit deviation from IJB grammar

IJB's canonical-assertion-grammar SPEC
([`foundations/ijb/canonical-assertion-grammar.md`](foundations/ijb/canonical-assertion-grammar.md)
line 31) restricts free text to inside quoted `rule=` values:

> Free text is allowed only inside quoted `rule=` values.

DAG-TOML deviates from this restriction. The format treats prose
fields (`prose`, `statement`, `summary`, `description`, `notes`,
`title`, `rationale`, `context`, `consequence`, `detection`,
`mitigation`, `scope_covered`, `known_exclusions`, `next_step`,
`purpose`) as first-class entity content. This is a known and
intentional deviation because the DAG-TOML use case (machine-readable
contracts that humans and LLM agents both author and review) requires
substantive explanatory prose, not the assertion-only substrate IJB
itself targets.

The deviation is handled by classifying every free-text field:

- **Default**: `ijb_primitive = "observed"`. The prose is treated as
  an authored descriptive fact about its containing entity. Per §10.1
  and the `[[kind.example]]` row of §10.2, `observed` is
  instance-by-nature and carries no class field; no `ijb_class`
  annotation accompanies the default classification.
- **Normative override**: where a prose field carries normative force
  (a contract `statement`, a requirement `statement`, a hard-invariant
  `statement`), the field is *additionally* tagged
  `ijb_primitive = "constraint"`, `ijb_constraint_type = "policy"`.
  The same field surface carries both an observed-instance role (the
  authored act of writing it) and a constraint-policy role (the rule
  it asserts).

A v0.2.0 iteration MAY ship a stricter validator that enforces IJB's
prose ban (rejecting prose outside `rule=`-style fields). For v0.1.0,
the deviation is documented here and not enforced.

### 10.4 The conformance validator

[`validators/validate_ijb_conformance.py`](validators/validate_ijb_conformance.py)
enforces the structural surface of the mapping. Specifically, it
requires:

1. Every `[[entities]]` block in `core/ontology.toml` and
   `profiles/agent-assurance/ontology.toml` declares `ijb_primitive`
   and `ijb_class`.
2. Every `[[relations]]` block declares `ijb_primitive` and
   `ijb_class`.
3. Every `[[attribute_vocabularies]]` block declares `ijb_primitive`
   and `ijb_constraint_type`.
4. Every kind-descriptor block (`[kind]`, `[[kind.required_fields]]`,
   `[[kind.required_sections]]`, `[[kind.hard_invariants]]`,
   `[[kind.example]]`, `[kind.relation_to_ontology]`) declares the
   `ijb_*` fields its row of the §10.2 mapping requires, and
   declares NO `ijb_*` fields the mapping does not require
   (e.g. `[[kind.example]]` MUST NOT declare `ijb_class`, and
   `[kind]` MUST NOT declare `ijb_constraint_type`).
5. Every `ijb_primitive` value is one of the six.
6. Every `ijb_class` value is `structural` or `instance`; every
   `ijb_constraint_type` value is `structural`, `policy`, or
   `observed`.
7. For any conforming DAG-TOML instance document: every entity
   prefix used resolves through the ontology to a structure with a
   declared `ijb_primitive`; every relation predicate used resolves
   similarly.

Out of scope for v0.1.0:

- Free-text reality-check forbidden-concept matching
  (`strategy`/`culture`/`alignment`/`risk posture` per the IJB
  README). Fragile substring matching defers to v0.2.0.
- Cross-document instance-pairing enforcement for structural
  relations (the IJB grammar's line-120 pairing rule).

### 10.5 Profile-specific stance: threat-model "Risk analysis"

The Agent Assurance Profile's `threat-model` kind is described
externally as "Risk analysis of the change itself" (see
[profiles/agent-assurance/overview.md](profiles/agent-assurance/overview.md)
and the descriptor's `summary` field). The phrase "Risk analysis" is
a **kind-purpose label**, not an in-data abstraction.

Concretely, every field in a threat-model instance file reduces to
one of the six primitives: `THREAT:` entries are `thing/instance`;
`likelihood`, `impact`, and `residual_risk` are `observed/instance`
attribute values drawn from closed `constraint/structural`
vocabularies in the profile ontology; mitigation references are
`path/instance` to `TEST:` things.

The IJB README's reality check
([`foundations/ijb/README.md`](foundations/ijb/README.md)) names
"risk posture" as a forbidden answer to the question
"what is that?" when pointed at a substrate element. The phrase
does **not** appear in this spec as a field name, value, kind
label, or conforming-instance concept; it appears only here and in
the matching threat-model-kind.toml note where its forbidden status
is itself the topic. "Risk analysis" (which does appear as a
kind-purpose label) is a domain-level descriptor of what the kind
does and is permitted as kind-purpose metadata rather than as
in-data substrate.

## 11. Optional `[provenance]` table

DAG-TOML instance files that are **generated from a separate source
artifact** (for example, a Markdown skill description, an external
specification page, a workflow design doc) MAY declare a single
root-level `[provenance]` table recording where the file came from.
The table is OPTIONAL. When present it MUST carry at least:

- `source_path` (string, relative to repo root) — the originating
  artifact.
- `source_sha256` (string, `sha256:<hex-digest>`) — the SHA-256 of
  that artifact's bytes at the time the TOML file was generated.
- `source_bytes` (integer) — byte length of the source artifact.

And SHOULD carry:

- `captured_at` (RFC 3339 timestamp).
- `extraction_method` (free-form short string identifying how the
  TOML was produced, e.g. `manual-analysis`, `regex-extract`,
  `agent-conversion`).
- `source_description` (free-form short string).

`[provenance]` is not a `template_kind`-bearing block; it is a
cross-kind metadata annotation. Any kind MAY accept it. Validators
that recognise the table MUST verify that:

1. `source_path` resolves to an existing file under repo root.
2. The SHA-256 of that file equals `source_sha256` (modulo the
   `sha256:` prefix).
3. `source_bytes` equals the byte length of that file.

A divergence on (2) or (3) is a hard validation failure: the
generated TOML no longer faithfully records the source artifact it
was produced from. The reference validator is
[`validators/validate_provenance.py`](validators/validate_provenance.py).
Files without a `[provenance]` table are silently ignored by that
validator.

`[provenance]` is informational at the schema layer: removing it
from a file does not change the file's `template_kind`-defined
shape. Its purpose is auditability, not interoperability.

When the document also carries upstream evidence outside
`[provenance]` (kind-specific citation fields, evidence-matrix
entries), `source_sha256` is **one input** to the §12 closure-root
digest. It is not a substitute for `closure_root`.

### 11.1 Optional `[provenance.encryption]` sub-table

A `[provenance]` table MAY carry a `[provenance.encryption]`
sub-table when the referenced source artifact is stored in an
encrypted form. The spec deliberately does NOT touch keys,
recipient lists, key-management URIs, or signing material — those
are RUNTIME-SPEC. The sub-table only records the **shape** of the
encryption arrangement so that a consumer recomputing the hash
knows what bytes the hash was computed over:

```toml
[provenance.encryption]
sealed       = true
hash_is_over = "plaintext"   # closed set: "plaintext" | "ciphertext"
scheme_hint  = "age"          # informational; e.g. "age", "pgp", "kms-envelope"
```

Field semantics:

- **`sealed`** (boolean, REQUIRED when the sub-table is present) —
  asserts the file at `source_path` is the encrypted form. If
  `sealed = false`, the sub-table MUST NOT appear; describe an
  unencrypted source via the bare `[provenance]` table.
- **`hash_is_over`** (string, REQUIRED) — value MUST be drawn from
  the closed set `"plaintext" | "ciphertext"`. When `"plaintext"`,
  `source_sha256` is the digest of the decrypted bytes (so the
  validator at this layer cannot recompute it without keys, and
  SHOULD treat the byte-length / digest check as advisory only).
  When `"ciphertext"`, `source_sha256` is the digest of the
  encrypted bytes on disk (so the standard §11 invariants apply
  unmodified).
- **`scheme_hint`** (string, OPTIONAL) — short free-form label
  identifying the encryption scheme family. Purely informational;
  validators MUST NOT key behaviour off this field.

The reference validator
([`validators/validate_provenance.py`](validators/validate_provenance.py))
recognises the sub-table:

1. When `hash_is_over = "ciphertext"`, the standard SHA-256 and
   byte-length recomputation applies as before.
2. When `hash_is_over = "plaintext"`, the validator emits an
   advisory note and skips the recomputation. A repo MAY layer a
   separate decrypt-and-verify step (out of scope for this spec)
   to close that gap.

The `[provenance.encryption]` sub-table lets the
"encrypted-blob-with-hash-reference" pattern be specified without
the spec touching keys; every adopter that needs it would otherwise
invent an incompatible convention.

The §12 closure-root rule fires on the SHA-256 declared by
`source_sha256` regardless of whether the digest is computed over
plaintext or ciphertext — the cascade-break property of §12.2 is
unchanged by the encryption shape recorded here.

---

## 12. The closure-root rule (brittleness propagation)

DAG-TOML documents do not stand alone. Most conforming artifacts cite
upstream evidence: a `traceability` document cites requirement sources,
an `evidence-matrix` cites test-run digests, an `assertion-bundle`
cites adapter contracts, a `disclosure-attestation` cites the
unredacted artifact it disclosed selectively. This section defines a
single normative rule governing the relationship between an upstream
artifact's identity and the downstream artifact that depends on it:
**upstream changes MUST break downstream hashes.** The rule is the
opposite of the property most existing PKI infrastructure attempts to
preserve, and the inversion is intentional.

### 12.1 The rule

Every conforming DAG-TOML document MUST carry a `closure_root` field.
At `schema_version = "0.1.0"`, the cross-kind normative byte-level
input is `[provenance].source_sha256`, computed as specified in
§12.8. Profiles MAY promote instance-local digest fields of their
contained kinds into the closure stream via **profile-pinned closure
records** declared in the profile-descriptor (`closure_records`,
§6.1; byte-level rules in §12.8), and MAY add canonical record forms
for kind-specific `cites_upstream`, `[[evidence_*]]`, and
revocation-snapshot inputs. All such additions MUST preserve the
cascade-break property in §12.2.

A document is **conforming** for the purposes of this section if and
only if its `[meta].template_kind` value is **spec-reserved** — i.e. is
either:

- a kind declared by `core/*-kind.toml` (see §3 for the closed list);
- a kind declared by a spec-reserved profile's `profiles/<name>/*-kind.toml`;
- one of the meta kinds `kind-descriptor` or `ontology`.

TOML documents that use **non-spec-reserved** `template_kind` values — for
example process-artefact files declaring `template_kind =
"review-bundle"`, `"claim-analysis-finding-set"`, or other strings
that no `*-kind.toml` descriptor declares — are out of conformance
scope. The closure-root rule does not apply to them, and the
reference validator's `--discover` mode skips them.

Conformance is keyed strictly to the `template_kind` *value*, not to
the file's purpose, directory, or producer. A file declaring a
spec-reserved kind (e.g. an `implementation-dag` document under
`tools/`, `skills/`, or anywhere else in the repository) IS
conforming and MUST carry `closure_root`. Producers that want a
file outside the rule's scope MUST give it a non-spec-reserved
`template_kind` (or no `template_kind` at all).

The reference validator
[`validators/validate_closure_root.py`](validators/validate_closure_root.py)
derives the spec-reserved-kind set from `core/*-kind.toml` and
`profiles/*/*-kind.toml` at run time, so new spec or profile kinds
automatically come under §12 the moment their `*-kind.toml`
descriptor lands.

The digest algorithm MUST be SHA-256 or stronger. Weaker algorithms
(MD5, SHA-1) are forbidden. The default SPEC-level input set is every
`[provenance].source_sha256` entry, plus every profile-pinned closure
record that §12.8 derives from the document's kind (when a loaded
profile pins records for that kind). Further profile/runtime-layer
inputs MAY include the closure of fields whose ontology mapping is
`cites_upstream` (declared in the relevant `*-kind.toml` descriptor),
`[[evidence_*]]` entries that carry upstream digests, and upstream
revocation snapshots known to the producer at emission time, provided
the profile pins their byte-level record forms.

`closure_root` is part of the document's signable content. Any signed
envelope wrapping the document MUST cover the `closure_root` field. The
producer MUST emit `closure_root` before any signing ceremony.

`closure_root` MUST appear at the root level of the document (sibling
to `[meta]`, `[provenance]`, and the kind-specific tables) as a single
string value of the form `sha256:<lowercase-hex-digest>` (or
`sha384:`, `sha512:`, etc., for stronger digests). Because TOML
attributes every bare `key = value` to the most-recently-opened
`[table]`, `closure_root` MUST appear **before the first `[table]`
header** in the document — typically the first non-comment line — so
the TOML parser binds it to the document root rather than to
`[meta]` or a later table.

The field is required on every document, including documents that
cite no upstream evidence. A self-contained document — one whose
§12.8 source-hash input set and any profile-pinned closure inputs are
both empty — MUST emit the **canonical empty-closure sentinel**:

```toml
closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
```

This is the SHA-256 digest of zero bytes (`SHA-256("")`). Validators
MUST recognise this value as the canonical empty-closure sentinel,
treat it as equivalent in structural meaning to "no upstream
evidence", and reject any document that omits `closure_root`
entirely. The sentinel preserves the brittleness graph as a
total function: every conforming document participates, including
roots of the citation tree.

Stronger-digest analogues of the empty-closure sentinel:

| Algorithm | Sentinel value |
|---|---|
| `sha256` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `sha384` | `38b060a751ac96384cd9327eb1b1e36a21fdb71114be07434c0cc7bf63f6e1da274edebfe76f65fbd51ad2f14898b95b` |
| `sha512` | `cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e` |

### 12.2 The cascade-break property

When any upstream artifact's hash changes, or any upstream revocation
list adds an entry that affects the closure this document depended on,
a downstream document that recomputes `closure_root` MUST produce a
different value. Any signed envelope wrapping the downstream document
MUST then become invalid until the document is re-emitted with a
refreshed closure and a new signing ceremony.

This behaviour is intentional. Verification fails visibly; consumers
observe the break locally without traversing upstream history.

### 12.3 Producer responsibility

Producers of a downstream document MUST:

1. Carry the current upstream closure into the document's
   `closure_root` field.
2. Carry the current upstream-revocation snapshot into the document's
   provenance evidence (and into the inputs to `closure_root`).
3. Re-emit a new signed document — with a new `closure_root`, a new
   signing ceremony, and a new artifact SHA-256 — whenever any upstream
   artifact or revocation snapshot changes.

A producer MUST NOT re-sign a downstream document under an unchanged
`closure_root` value when any input to that closure has changed.

### 12.4 Consumer responsibility

A consumer MUST verify that the document's `closure_root` value is
covered by the document's signed envelope (i.e. that the envelope
verifies against bytes that include the declared `closure_root`). The
consumer MUST NOT traverse upstream history to validate the closure;
the closure root makes upstream change locally observable, and
upstream traversal is the producer's responsibility, not the
consumer's.

### 12.5 What this section does NOT specify

This section is envelope-agnostic and primitive-agnostic. The
following are explicitly out of scope and are owned by profiles or by
RUNTIME-SPEC documentation:

- Signing-envelope format (CMS_Sign1 in ASN.1 DER, COSE_Sign1 in
  deterministic CBOR, DSSE, or any future envelope).
- Asymmetric signing primitive (Ed25519, ECDSA, RSA-PSS, ML-DSA, etc.).
- Transparency-log target (SCITT, Rekor, self-hosted Trillian, or
  none).
- Key-aging policy, revocation-publication cadence, and timestamp
  authority selection.
- Profile-specific record forms beyond the §12.8
  `[provenance].source_sha256` source-hash closure.

A profile that layers concrete cryptography on top of this rule MUST
preserve §12.1–§12.4 verbatim and MUST NOT introduce mechanisms that
suppress the cascade-break property of §12.2.

### 12.6 Worked example

```toml
# closure_root is a SHA-256 over the SPEC §12.8 source-hash closure
# stream for [provenance].source_sha256. A change to that source hash
# flips this value, which flips the document's own SHA-256, which
# invalidates any signed envelope wrapping the document. It MUST appear
# before the first [table] header so TOML binds it to the document
# root rather than to [meta].
closure_root = "sha256:06e235a8becb8f467db6069eafb7192c71fb566977d222a7a7cd13011053d815"

[meta]
schema_version = "0.1.0"
template_kind  = "evidence-matrix"
docs           = "https://github.com/verivus-oss/agent-assurance/blob/main/spec.md"

[provenance]
source_path   = "REQUIREMENTS.md"
source_sha256 = "sha256:a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90"
source_bytes  = 8421
captured_at   = "2026-05-22T14:00:00Z"

# kind-specific tables follow…
```

A self-contained document (no upstream evidence) uses the empty-closure
sentinel:

```toml
# Empty-closure sentinel: SHA-256("") — declares "no upstream evidence"
# while keeping every conforming document in the brittleness graph.
closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

[meta]
schema_version = "0.1.0"
template_kind  = "implementation-dag"
docs           = "https://github.com/verivus-oss/agent-assurance/blob/main/spec.md"
# …
```

### 12.7 Forbidden mechanisms (non-normative warning)

Implementers familiar with X.509, PKIX, CMS, or PGP will recognise
that those systems are designed to *preserve* signature validity when
upstream artifacts change. A certificate signed today remains valid
tomorrow; revocation is a separate, out-of-band channel that consumers
poll. The closure-root rule deliberately reverses that property.

Implementers MUST NOT introduce mechanisms that paper over
closure-root changes. The following are forbidden:

- Re-signing a downstream document with a stale `closure_root` to
  preserve envelope validity through an upstream change.
- Storing `closure_root` in unsigned envelope attributes
  (`unsignedAttrs`, `unprotectedHeader`, or equivalent) where it is
  not covered by the signature.
- Defining "soft revocations" that update an upstream revocation list
  without flipping downstream closure-root values.
- Caching closure-root inputs across upstream versions (a
  "last-known-good" closure that survives an upstream change is the
  failure mode this section exists to prevent).

The brittleness is the feature. A downstream document whose signature
silently survives an upstream change is indistinguishable, to the
consumer, from a downstream document whose upstream was never
compromised. The closure-root rule makes that distinction mechanical.

### 12.8 Canonical source-hash closure

At `schema_version = "0.1.0"` this spec pins the byte-level closure
algorithm for the cross-kind source hash every conforming document can
declare: `[provenance].source_sha256`.

For each `[provenance].source_sha256` value, the producer emits one
UTF-8 input record:

```text
provenance.source_sha256 <sha256:64-lowercase-hex>\n
```

The producer sorts all such records by bytewise lexicographic order,
concatenates them exactly as UTF-8 bytes, computes the digest with the
algorithm named by the `closure_root` prefix (`sha256`, `sha384`, or
`sha512`), and serialises the result as `<algorithm>:<lowercase-hex>`.
For the empty input set the canonical stream is zero bytes, so the
expected value is the empty-closure sentinel for the selected digest
algorithm (§12.1).

#### 12.8.1 Profile-pinned closure records

A profile MAY promote instance-local digest fields of its contained
kinds into the closure stream by declaring them in its
profile-descriptor (§6.1). Each `[[profile.closure_records]]` entry
carries EXACTLY the three keys `contained_kind`, `field`, and
`presence`; unknown keys are rejected (INV07):

```toml
[[profile.closure_records]]
contained_kind = "api-snapshot"
field          = "snapshot.request.descriptor_sha256"
presence       = "required"
```

Declaration constraints (invariant INV07, declared in
`core/profile-descriptor-kind.toml` and enforced by the
profile-descriptor validators):

- `contained_kind` MUST be a member of the post-`extends`-union
  `contained_kinds` of the declaring profile.
- `field` MUST match `^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*$`, applied
  to the decoded TOML string scalar. Lookup is segment-wise from the
  document root; the emitted record label is the identical string.
  `field` MUST NOT begin with `meta.`, MUST NOT name a §12.9 posture
  field, MUST NOT be `closure_root`, and MUST NOT be
  `provenance.source_sha256` (already a SPEC-layer record;
  double-pinning is rejected).
- `presence` MUST be `"required"` or `"when-present"`.
- `closure_records` entries union across `extends` exactly like
  `contained_kinds`; duplicate (`contained_kind`, `field`) pairs
  after the union are rejected.

**Record emission.** For each pinned field present in the document,
the value MUST be `sha256:` followed by 64 lowercase hex digits
(pinned records are sha256-only at `schema_version = "0.1.0"`;
widening to `sha384`/`sha512` is a deliberate future change to this
section) and emits exactly one UTF-8 record:

```text
<field> <sha256:64-lowercase-hex>\n
```

(single 0x20 separator, single trailing 0x0A; identical shape to the
`provenance.source_sha256` record). A `required` field that is absent
is a validation error. A `when-present` field that is absent emits no
record. A present pinned field whose value is malformed is a
validation error. Pinned records join the §12.8 stream: the union of
the `provenance.source_sha256` records and all pinned records is
sorted bytewise, concatenated, and digested exactly as specified
above. The empty-input sentinel rule is unchanged.

**Pin resolution.** Pins resolve by `template_kind` over the full
loaded profile-descriptor set (kind names are namespace-partitioned
per §6.1, so a `template_kind` maps to at most one profile). A
document whose `template_kind` is pinned by a loaded descriptor MUST
have those pins applied in EVERY validation mode that checks
`closure_root`, regardless of the document's `framework_profile`
value. Additionally, such a document whose `framework_profile` is
missing or does not resolve to a loaded profile-descriptor MUST be
rejected by the closure check. Validators MUST NOT fall through to a
pin-free closure for a document of a pinned kind.

Profile-pinned closure records extend the §12.2 cascade-break
property rather than weakening it: removing a pinned `when-present`
input (for example a witness attestation digest) removes its record
and therefore changes the expected `closure_root`.

Beyond the instance-local digest fields covered by §12.8.1, the full
byte-level algorithm for kind-specific `cites_upstream` fields,
`[[evidence_*]]` upstream digests, revocation snapshots,
duplicate-input policy, and closure-cycle traversal remains profile /
runtime work until a future `schema_version` promotes those record
forms into normative spec text. Profiles that pin additional record
forms MUST do so in their `profile-descriptor` document (per §6.1) so
consumers can enumerate them without reading code. Additional profile
record forms MUST preserve §12.1-§12.4 and MUST NOT suppress the
cascade-break property of §12.2.

#### 12.8.2 Bound tuples

A profile MAY require a kind to commit a set of its own fields to an
external verifier, by declaring a **bound tuple**: a digest, carried
in the document, over a named set of that document's fields. The
external artefact (a TEE quote's report data, a zero-knowledge
receipt's public inputs, a ledger commitment, a signed payload)
carries the same digest, so a verifier can confirm the artefact
commits to THIS document's values and not merely that some artefact
exists. Confirming that the external artefact carries the value is
RUNTIME-SPEC; this section fixes only the bytes.

The canonical form is deliberately close to §12.8.1, and identical in
its type contract:

```text
<field> <sha256:64-lowercase-hex>\n
```

- One record per declared field, in the same shape as a pinned
  closure record: dotted path, single 0x20, value, single 0x0A.
- The digest is taken over the **UTF-8 bytes of the field's value**,
  NOT over its textual form in the document. Values are therefore
  PREHASHED, never inlined.
- Records are sorted bytewise, concatenated, and the tuple digest is
  the SHA-256 of that stream, expressed as `sha256:` followed by 64
  lowercase hex digits.
- A declared field that is absent is a validation error. Bound
  tuples have no `when-present` form: a tuple with optional members
  would let a producer choose what the proof commits to.
- A declared field that is present but is not a string is a
  validation error. It MUST NOT be coerced, and MUST NOT be treated
  as absent: substituting the empty string for it would compute a
  tuple over values no producer wrote.
- Field paths are frozen by the profile that declares them and MUST
  match the §12.8.1 pinned-record grammar
  `[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*`. A path containing 0x20 or 0x0A
  would reintroduce at the label boundary exactly the ambiguity
  prehashing removes at the value boundary.
- Values are hashed as the exact UTF-8 bytes carried in the document,
  with **no Unicode normalization** applied by either producer or
  verifier. Two documents whose values are canonically equivalent but
  differently encoded (NFC versus NFD) therefore produce different
  tuple digests. This is deliberate: normalizing would make the
  verifier's recomputation depend on a Unicode version, and a bound
  tuple must be reproducible from bytes alone. A profile that needs
  equivalent strings to bind identically MUST constrain the field's
  grammar so that only one encoding is representable.

**Prehashing is normative and load-bearing.** Inlining values makes
the encoding non-injective: a value containing 0x0A forges a
different field-to-value assignment with an identical tuple digest,
so one bound tuple would bind two distinct documents. Digest scalars
are fixed-width and carry no attacker-controlled bytes in delimiter
position, which removes the class of attack rather than filtering for
it. Profiles MAY additionally constrain the grammar of the bound
fields, and SHOULD do so for any field that would otherwise accept
arbitrary text, but grammar constraints are defence in depth and MUST
NOT be relied on in place of prehashing.

A bound tuple is not a closure input. It commits a document to an
external artefact; §12.8 and §12.8.1 commit a document to its own
upstream inputs. A profile that wants the tuple digest to cascade
MUST also pin it as a closure record under §12.8.1, in which case it
appears in both streams and the two remain independently computable.

### 12.9 Interaction with other sections

- §2.7 (`confidentiality`, `license`, `embargo_until`) — posture
  fields are declared policy, **not** closure-root inputs. They
  change without breaking downstream hashes. This is intentional:
  posture is a policy declaration, not upstream evidence.
  Profile-pinned closure records (§12.8.1) are subject to the same
  exclusion: INV07 rejects any pin naming a posture field or a
  `meta.*` path, so posture-only changes remain cascade-free even
  for documents of pinned kinds.
- §5 (Hard invariants) — the closure graph induced by
  `closure_root` inputs MUST be acyclic. A document MUST NOT,
  directly or transitively, cite an upstream artifact whose own
  closure depends on this document. Validators that walk closure
  inputs MUST detect and reject closure cycles; this extends the
  §5 cycle prohibition from intra-DAG `depends_on` to inter-document
  evidence citation.
- §11 (`[provenance]`) — `source_sha256` is one input to
  `closure_root` whenever a `[provenance]` table declares it.
  `closure_root` itself remains MANDATORY at the document root per
  §12.1 regardless of whether `[provenance]` appears; a
  provenance-only document still emits `closure_root` (the canonical
  empty-closure sentinel only when no §12.8 source-hash records are
  present).
  `[provenance]` annotates origin, but never substitutes for
  `closure_root`.
- Profiles — the disclosure profile (`profiles/disclosure/`)
  introduces a question this section must answer: when a producer
  publishes a redacted form of an artifact, does the redaction flip
  the upstream's `closure_root`? **No.** The unredacted artifact and
  its redacted disclosure are two distinct artifacts with two
  distinct SHA-256 values; the redacted form carries its own
  `closure_root` that cites the unredacted form as upstream. The
  unredacted artifact's `closure_root` is unaffected by the act of
  publishing a redaction. The closure-root rule fires on *changes
  to upstream evidence*, not on the production of a derived
  artifact.

### 12.10 Live feeds and mutable upstream sources

Live feeds (HTTP endpoints that return different bytes at different
times) have no stable digest and MUST NOT be cited as direct
closure-root inputs. A producer that wants to depend on data from a
mutable source MUST first snapshot that source into a digest-pinned
artifact, then cite the snapshot. The closure-root rule then applies
to the snapshot, not to the live source. Profile-layer text MAY
define a "snapshot-of" relation that captures the binding between
snapshot and live source as audit metadata, but the closure root MUST
be computed over the snapshot.

### 12.11 Migration note for pre-§12 producers

This section adds a new mandatory root-level field to every
conforming document. Producers that emitted DAG-TOML documents
before §12 landed MUST update those documents to carry
`closure_root` before they can be re-validated. The migration
procedure is mechanical:

1. **Identify every conforming document you produce.** A document
   is conforming if its `[meta].template_kind` is one of the kinds
   declared by `core/*-kind.toml` or by a spec-reserved profile's
   `*-kind.toml`, or is the meta kind `kind-descriptor` /
   `ontology`. See §12.1.
2. **Choose the closure value.** If the document has no §12.8
   `[provenance].source_sha256` input and no profile-pinned upstream
   evidence inputs — no fields with the `cites_upstream` ontology
   mapping, no `[[evidence_*]]` rows with upstream digests, and no
   revocation snapshots — emit the canonical empty-closure sentinel:
   ```toml
   closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
   ```
   Otherwise, compute the `[provenance].source_sha256` subset per
   §12.8. Any additional kind-specific upstream fields or revocation
   snapshots are profile/runtime-layer inputs until their record forms
   are pinned by the profile descriptor or by a future `schema_version`.
3. **Place it before the first `[table]` header.** TOML attributes
   every bare `key = value` to the most-recently-opened table, so
   `closure_root` MUST appear at the top of the file — typically
   immediately after the leading comment block and before
   `[meta]` — so the parser binds it to the document root rather
   than to `[meta]`. See the worked example in §12.6.
4. **Re-emit and re-sign.** Any signed envelope wrapping the
   document MUST cover the new `closure_root` value (§12.1). Stale
   envelopes from before this migration MUST be regenerated; this
   is intentional per the cascade-break property of §12.2.

The reference validator at
[`validators/validate_closure_root.py`](validators/validate_closure_root.py)
will reject documents missing the field with an error message that
includes the canonical sentinel, so producers can copy the
migration value directly from validator output.

This is a backwards-incompatible change at the conformance layer.
Per §8 it would normally require a major `schema_version` bump after
the first stable release, but the rule is being introduced while this
document is still a Draft Specification. The draft schema therefore
stays at `"0.1.0"` and producers that have not yet shipped to stable
consumers simply add `closure_root` and continue.

---

## 13. Abstraction class and capability envelope

§12 made every conforming document brittle against upstream
*identity* drift. This section makes every conforming document
brittle against upstream *behavioural* drift. Together the two
form the structural-governance half of the spec's load-bearing
deliverables (see the introduction's "Provable Intent + Structural
Governance" framing).

A signed artefact whose signature is valid but whose runtime
behaviour silently exceeds its declared role is the supply-chain
attack §12 cannot detect on its own. SLSA Level 3 passed on the
2024 compression-library backdoor because the signature was real
and the build was reproducible — and the artefact still shipped a
remote-execution backdoor in a library whose declared job was data
compression. The signature was right; the *class* was wrong. This
section gives the spec a vocabulary for that distinction.

### 13.1 The rule

Every `*-kind.toml` descriptor MAY declare:

- A single `[kind.abstraction_class]` table whose `id` field names
  the class the kind belongs to (e.g. `data-transform.v1`,
  `evidence-citation.v1`).
- A single `[kind.capability_envelope]` table declaring the
  resource bounds and per-domain capability grants permitted to
  instances of this kind.

When both are declared, the producer asserts that conforming
instance documents — and any runtime that executes against them —
stay inside the envelope. A consumer reading the descriptor
treats the declared envelope as the contract.

Both declarations are OPTIONAL at `schema_version = "0.1.0"`. A
kind descriptor that omits them does not assert a class boundary
and consumers cannot reject downstream artefacts on behavioural
grounds. Adopters who want the brittleness-propagation property
of §13.4 MUST declare both.

When declared, both blocks are part of the kind descriptor's
canonical bytes and therefore flow into the descriptor's
`closure_root` per §12.1. Changing the abstraction class or the
capability envelope flips the descriptor's closure root, which
flips every downstream instance's closure root that cited it,
which invalidates every signed envelope wrapping those instances.
**The class is the contract; class changes cascade-break.**

### 13.2 `[kind.abstraction_class]`

```toml
[kind.abstraction_class]
id          = "data-transform.v1"
description = "Reads bounded input, writes bounded output, no I/O outside declared preopens."
ijb_primitive       = "constraint"
ijb_constraint_type = "structural"
```

- `id` (REQUIRED when the block is present) — a versioned class
  identifier of the form `<slug>.v<integer>`. The slug is
  free-form and producer-attested (drawn from the producer's
  internal taxonomy or an industry vocabulary; the spec does
  not enumerate slugs). The `v<integer>` suffix is required and
  monotonic — class identity is versioned so a consumer can
  reject downstream artefacts whose class version exceeds the
  one their envelope was authored against.
- `description` (REQUIRED) — a non-empty free-form prose
  description of what the class admits, in producer's own words.
  Auditors read this; validators do not.
- IJB tags as shown.

### 13.3 `[kind.capability_envelope]`

The envelope is organised by *capability domain*, not by primitive
operation. Each domain is a sub-table — denied via `denied = true`
or scoped via fields that constrain the grant. Resource bounds
(CPU + memory) are declared separately.

The closed set of capability domains, drawn from the WASI Preview 2
WIT vocabulary (see `[follow-up-2/16-stream-f-synthesis-v2.md]`)
for portability across enforcement backends:

| Domain | Denies / scopes |
|---|---|
| `filesystem` | preopens + read / write / exec sub-allowances |
| `sockets` | tcp / udp / ip-resolve sub-allowlists |
| `http` | outgoing-handler hosts + concurrency cap |
| `clocks` | wall vs monotonic + precision cap |
| `random` | entropy source declaration |
| `environment` | named variable allowlist |
| `process_spawn` | which programs + argv patterns |
| `ipc` | shared memory / signals / fd-passing |
| `crypto_keys` | read vs use vs generate, per key id |

The schema-layer shape (in TOML at the kind-descriptor layer):

```toml
[kind.capability_envelope]
spec_version = "0.1.0"
ijb_primitive       = "constraint"
ijb_constraint_type = "structural"

# Resource bounds
[kind.capability_envelope.cpu_bounds]
max_cpu_ms      = 1000
max_cpu_percent = 50

[kind.capability_envelope.memory_bounds]
max_bytes = 104857600

# Capability grants — each is `denied = true` to forbid the whole
# domain, or a sub-table to scope it. A domain whose table is
# entirely missing is treated as `denied = true` (fail closed).
[kind.capability_envelope.filesystem]
preopens      = ["/data/input/*", "/tmp/scratch/*"]
read_allowed  = true
write_allowed = false
exec_allowed  = false

[kind.capability_envelope.sockets]
denied = true

[kind.capability_envelope.http]
denied = true

# clocks / random / environment / process_spawn / ipc / crypto_keys
# omitted → fail closed (no grant).
```

The full table of grant sub-tables is normative and is declared
jointly by (a) the closed `capability_envelope.domain` vocabulary
in `core/ontology.toml`, (b) the per-domain shape checks enforced
by `validators/validate_abstraction_class.py`, and (c) this
section's prose. Per §2.4, tooling MUST NOT require a
`kind-descriptor-kind.toml` to exist; the validator + ontology +
SPEC §13 are the recursion-stop surfaces.

### 13.4 The cascade-break property

When a kind descriptor declares an abstraction class and/or a
capability envelope, those declarations participate in the
descriptor's `closure_root` (§12.1). The cascade-break property
flows naturally:

1. A producer signs an instance document whose kind cited
   descriptor D version V (closure-root C_V).
2. The maintainer of D widens the envelope (e.g. grants
   `sockets.tcp_allowlist = ["*"]`). C_V → C_V+1.
3. Every instance document signed against C_V is now
   structurally invalid; the signed envelope no longer covers
   the new closure root.
4. Re-signing requires the producer to inspect the widened
   envelope and consciously re-attest.

This is the brittleness-as-feature property §13 was added for.
**The signature does not survive a class change.** A producer
who refreshes the signature without inspecting the widened
envelope has produced new evidence under the new contract, not a
ratification of the old one.

### 13.5 What this section does NOT specify

- **The wire format.** This section specifies the
  *kind-descriptor* layer (TOML). The corresponding canonical
  CBOR wire shape for cross-runtime signing is a separate
  document (Stream F V2's `capability-envelope` CDDL).
- **The attenuation calculus.** "Child envelope ⊆ parent
  envelope" needs a normative algorithm. It is referenced here
  (`child grant for each domain is a subset of parent's`) but
  pinned in a separate executable specification per the
  multi-language safe-language strategy (Stream D).
- **The signing tier.** Whether the descriptor is signed under
  technical-tier COSE_Sign1 or legal-tier CB-AdES (ETSI TS 119
  152-1) is profile/runtime choice. Either tier carries the
  closure root.
- **The enforcement backend.** Linux seccomp+landlock, FreeBSD
  Capsicum, macOS sandbox-exec, Wasmtime — the spec specifies the
  semantic contract; the runtime chooses the implementation.
- **Static observability for WASM artefacts.** The Stream F V2
  proposal recommends WASM Component Model + WIT imports as the
  preferred enforcement vector. That layer is RUNTIME-SPEC and
  is described under `[docs/research/2026-05-22-spec-foundations-research/follow-up-2/16-stream-f-synthesis-v2.md]`.
- **The `runtime-observation-attestation` kind.** Recommended
  follow-up for non-WASM artefacts (native binaries, scripts,
  containers); not declared by this section.

### 13.6 IJB conformance

Both blocks are IJB `constraint` primitives:

- `[kind.abstraction_class]` is `(constraint, structural)` — it
  declares a structural rule about what the kind admits.
- `[kind.capability_envelope]` is `(constraint, structural)` at
  the table level. Each per-domain grant sub-table is `(constraint,
  structural)` as well; resource-bound integer fields are
  `(constraint, structural)` with `ijb_constraint_type =
  "structural"` since they bound an observed property.
- Per-instance behaviour (the artefact actually staying inside
  the envelope at runtime) is `(observed, instance)`, but that
  observation is the subject of a separate
  `runtime-observation-attestation` kind, not this section.

### 13.7 Closed-vocabulary participation

This section introduces no new attribute vocabularies *that
constrain instance values*. The capability domains
(`filesystem` / `sockets` / `http` / `clocks` / `random` /
`environment` / `process_spawn` / `ipc` / `crypto_keys`) are the
closed set of legal sub-table names under
`[kind.capability_envelope]`. Adding a new domain is a SPEC
amendment that bumps `schema_version`.

### 13.8 Worked example — `data-transform.v1`

```toml
# In core/<some-data-transform-kind>.toml:

[kind.abstraction_class]
id          = "data-transform.v1"
description = "Bounded compute over bounded inputs, no I/O outside declared preopens, no networking."
ijb_primitive       = "constraint"
ijb_constraint_type = "structural"

[kind.capability_envelope]
spec_version = "0.1.0"
ijb_primitive       = "constraint"
ijb_constraint_type = "structural"

[kind.capability_envelope.cpu_bounds]
max_cpu_ms      = 1000
max_cpu_percent = 50

[kind.capability_envelope.memory_bounds]
max_bytes = 104857600  # 100 MB

[kind.capability_envelope.filesystem]
preopens      = ["/data/input/*", "/tmp/scratch/*"]
read_allowed  = true
write_allowed = true
exec_allowed  = false

[kind.capability_envelope.sockets]
denied = true

[kind.capability_envelope.http]
denied = true

[kind.capability_envelope.clocks]
wall_clock_allowed      = false
monotonic_clock_allowed = true
precision_cap_ms        = 10

# random / environment / process_spawn / ipc / crypto_keys
# all omitted → fail closed (denied by default).
```

A consumer reading this descriptor knows: the runtime executing an
instance of this kind MAY read/write files under the named
preopens, MAY check the monotonic clock with ≥10ms precision, MAY
spend at most 1s CPU and 100MB RAM. The runtime MUST NOT open
sockets, MUST NOT make HTTP requests, MUST NOT spawn child
processes, MUST NOT read environment variables, MUST NOT access
crypto keys. If the actual runtime exceeds any of these
boundaries, the instance violates the class contract.

### 13.9 Forbidden mechanisms (non-normative warning)

Implementers MUST NOT:

- Re-sign an instance document under an unchanged `closure_root`
  after widening the kind descriptor's capability envelope. The
  closure root MUST flip; if it does not, the implementer has
  introduced the same papering-over hazard §12.7 enumerates.
- Treat a missing capability domain table as an implicit grant.
  Missing-domain = denied; the failure mode is fail-closed.
- Encode capability declarations outside `[kind.capability_envelope]`
  in ad-hoc kind-specific fields. The vocabulary is closed at the
  domain level; novel domains require a SPEC amendment.

### 13.10 Backwards-compatible introduction

This section is additive. Existing kind descriptors that do not
declare `[kind.abstraction_class]` or `[kind.capability_envelope]`
remain conformant under `schema_version = "0.1.0"`. They simply
do not gain the brittleness-propagation property §13.4 describes.

Adopters retrofit their existing kinds incrementally. A
follow-up effort under
`[docs/issues/2026-05-23-iss-002-graph-cypher-seed-incomplete.md]`-
adjacent issues (filed when the §13 surface is populated) will
track which spec/profile kinds have been retrofitted and which
remain.

## 14. Security Considerations

DAG-TOML is a declarative document format and conformance surface. A
valid DAG-TOML file MUST NOT be interpreted as proof that a workflow
was safe, authorized, complete, reviewed, executed, or successfully
enforced. Syntax validity, IJB conformance, profile conformance, and
validator success are necessary inputs to review, not substitutes for a
security decision.

The specification intentionally separates evidence description from
runtime authority:

- `closure_root` binds an instance to the descriptor, ontology, and
  profile bytes it claims to depend on. It detects drift in that
  closure; it does not prove the closed-over content is correct,
  benign, complete, or approved by an appropriate party.
- Signature, registry, trust-anchor, adapter, assertion, gate, and
  verifier fields identify evidence and decision records. They do not,
  by themselves, establish that a signing key was uncompromised, that a
  registry was trustworthy, that an adapter was faithful, or that a
  gate was appropriately scoped for the deployment.
- `[kind.capability_envelope]` declares a kind-level capability
  contract. It is not a sandbox, a kernel policy, a container profile,
  or an access-control mechanism. Runtime systems that execute
  workflows MUST enforce their own isolation and authorization policies
  and treat the envelope as an auditable declaration to compare against
  observed behaviour.
- `[provenance]` and `[provenance.encryption]` describe source
  material and optional encryption posture. They do not decrypt,
  retrieve, authorize access to, or validate the semantic correctness of
  that source material.
- `confidentiality`, `license`, `disclosure_posture`, and
  `embargo_until` fields express metadata and review posture. They do
  not enforce secrecy, license compliance, embargo release, retention,
  or deletion.

Consumers SHOULD threat-model at least the following classes of attack
before relying on published DAG-TOML material:

- stale or malicious descriptors that are still syntactically valid;
- misleading provenance where the cited source exists but does not
  support the claim being made;
- compromised signing identities, registries, adapters, validators, or
  CI workflows;
- over-broad capability envelopes that normalize more runtime authority
  than a workflow actually needs;
- incomplete closure sets that omit material facts, policies, or
  profile-specific constraints; and
- disclosure artifacts that prove a relationship to source bytes while
  still leaking sensitive facts through identifiers, locators, timing,
  counts, or metadata.

Producers publishing DAG-TOML artifacts SHOULD publish the smallest
closure that is sufficient for verification, pin external references
where possible, document non-obvious trust assumptions, and avoid
claiming security properties that are supplied only by local runtime,
deployment, key-management, or access-control systems.

## 15. Privacy Considerations

DAG-TOML documents are designed to make claims, evidence, provenance,
and review decisions inspectable. That same inspectability can expose
personal data, confidential business information, regulated data, or
operationally sensitive metadata even when the document body contains no
secret payload.

Fields that can carry or imply sensitive information include, but are
not limited to, IDs, titles, `source_path`, source hashes and byte
counts, timestamps, actor or reviewer identifiers, signing identities,
registry coordinates, relation edges, redaction locators, disclosure
subjects, cost records, model or tool names, and free-text rationale
fields. Hashes and closure roots can also become correlators when the
same private source or descriptor appears in more than one publication.

Before publishing, producers SHOULD perform data minimization and
context-specific disclosure review:

- remove or generalize unnecessary personal names, account names,
  hostnames, paths, ticket numbers, customer identifiers, and internal
  project names;
- prefer stable pseudonymous identifiers when the real-world identity is
  not required for verification;
- review free-text fields for accidental secrets, personal data,
  confidential facts, and legally privileged material;
- ensure redaction manifests do not reveal more through locators,
  reasons, counts, or ordering than the publication intends to disclose;
- treat `confidentiality`, `license`, `disclosure_posture`, and
  `embargo_until` as advisory metadata unless an external control plane
  enforces the corresponding handling rule; and
- document any residual privacy assumptions that verifiers must know in
  order to interpret a public artifact correctly.

Selective-disclosure and redaction-related artifacts can reduce the
amount of source material exposed, but they are not a complete privacy
solution. A faithful redaction proof may still reveal that a sensitive
source exists, that a subject was considered, that a category of data
was removed, or that two artifacts share the same underlying source.
Privacy review therefore remains a publication responsibility outside
the TOML syntax itself.
