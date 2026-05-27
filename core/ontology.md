# Core: Ontology

**The DAG-TOML ontology formalises the entity types, the closed
relation vocabulary, and the extension points used across every core
schema and every profile.** It is the single place a reader or a
downstream tool consults to answer questions like:

- *What can a `REQ:` link to, and via which predicate?*
- *Is the relation vocabulary open or closed?*
- *What does `priority` mean, and what values does it take?*
- *What does `ontology_version` track, and how does it relate to
  `schema_version`?*

The prose definition lives in this file. A machine-readable companion
lives at [ontology.toml](ontology.toml).

---

## 1. Two version pins

Two version fields appear in DAG-TOML files. They track different
things and MUST be bumped independently.

| Field | Lives in | Pins |
|---|---|---|
| `schema_version` | `[meta]` on every DAG-TOML file | The file *shape* — required fields, allowed values for kind enums, structural validation. It is a semver string and is bumped per [spec.md §8](../spec.md#8-versioning-policy). |
| `ontology_version` | `[meta]` on traceability files (and any future file that participates in the relation graph) | The *relation vocabulary* — which entities exist, which predicates connect them, and which sub-kinds are valid. It is a monotonic positive integer snapshot. |

Current versions:

- `schema_version = "0.1.0"`
- `ontology_version = 1`

After the first public release, a backwards-compatible addition to
the ontology (a new entity, a new predicate, a new value in an
extensible vocabulary) increments `ontology_version` from `1` to `2`,
then `3`, and so on. A breaking change (renaming or removing a
predicate, changing direction or cardinality) also increments
`ontology_version` and may require a major `schema_version` bump when
it affects file shape or validator conformance.

**Pre-publication note.** This spec is in a pre-release drafting
phase. Until the first public release, `schema_version` stays at
`"0.1.0"` and `ontology_version` stays at `1` regardless of
intervening edits. The first public stable schema can become
`schema_version = "1.0.0"` when maintainers are ready to promise
schema stability; ontology snapshots still advance as integers.

---

## 2. Entities

DAG-TOML names seventeen entity kinds across the three core template
kinds (nine in traceability, plus DAG units and DAG artifacts, plus
six in review-readiness; `OUT:` is shared between traceability outputs
and DAG terminal outputs). Each entity has an ID prefix that is
unique across the ecosystem.

### Core traceability entities

| Prefix | Section | Meaning |
|---|---|---|
| `INT:` | `[[intents]]` | A user or business intent. Top of the trace. |
| `FEAT:` | `[[features]]` | A user-visible capability. |
| `REQ:` | `[[requirements]]` | A normative, testable requirement. |
| `REG:` | `[[regulations]]` | A legal, policy, or regulatory obligation. |
| `DEC:` | `[[decisions]]` | A design or policy decision. |
| `IMP:` | `[[implementations]]` | An implementation work package. |
| `CODE:` | `[[code]]` | A concrete code artifact (file + optional symbol). |
| `TEST:` | `[[tests]]` | A verification artifact. |
| `OUT:` | `[[outputs]]` | A user-visible output or deliverable. |

### Implementation-DAG entities

| Prefix / shape | Section | Meaning |
|---|---|---|
| `U01`, `U02`, `U07a`, … | `[units.*]` | Implementation-DAG units. |
| `ART:` | `[units.*].produces` / `.consumes` | Internal artifact flowing between units. |
| `OUT:` | `[units.*].produces` | Final deliverable leaving the DAG (shared prefix with traceability outputs). |

### Review-readiness entities

| Prefix / shape | Section | Meaning |
|---|---|---|
| `A01`, `A02`, … | `[[artifact_classes]]` | A review artifact class. |
| `G01`, `G02`, … | `[[gates]]` | A readiness gate keyed to one artifact class. |
| `C01`, `C02`, … | `[[contracts]]` | A declared contract. |
| `E01`, `E02`, … | `[[claims]]` | A strong review claim. |
| `EV01`, `EV02`, … | `[[evidence]]` | A piece of proof artifact. |
| `M01`, `M02`, … | `[[matrix]]` | A claim ↔ evidence linkage row. |

Profile-defined entities (`GUAR:`, `INV:`, `NG:`, `THREAT:`, `SMOKE:`,
`TRIG:` from the Agent Assurance Profile) are declared in the profile
ontology extension at
[`../profiles/agent-assurance/ontology.toml`](../profiles/agent-assurance/ontology.toml).
That file carries its own `ontology_version` that tracks only the
profile's vocabulary; the core ontology version above is unaffected
by profile additions.

---

## 3. Relations — closed predicate vocabulary

Relations in DAG-TOML are a **closed vocabulary**: the core ontology
defines every predicate, where it may appear, and what it may target.
Profiles MAY add new entity kinds; profiles MAY add new relation
predicates **only inside their own ontology extension and MUST
namespace them** (e.g. `agent-assurance:mitigates` — see §3.3). The
**core** relation vocabulary itself stays closed: after the first
tagged release, any addition to the core relation predicate set
bumps `ontology_version` and is a breaking change (see §1).
Pre-publication, drafts are revised in place without bumps. The
intent is that any downstream tool consuming a traceability graph
can enumerate the full core predicate set without reading
profile-specific code, and can detect profile-defined predicates by
their namespace prefix.

The following table is authoritative for `ontology_version = 1`.

### 3.1 Traceability and DAG relations

| Predicate | Field name | Source entity | Allowed target entities | Cardinality | Inverse |
|---|---|---|---|---|---|
| derived from | `derived_from` | `INT` | `INT` | 0..* | — |
| realized by | `realized_by` | `INT` | `FEAT`, `REQ` | 0..* | `realizes` |
| realizes | `realizes` | `FEAT` → `INT`; `CODE` → `IMP`, `REQ`; `OUT` → `FEAT`, `INT` | as shown | 0..* | `realized_by` (FEAT, OUT side) |
| constrained by | `constrained_by` | `FEAT` | `REQ`, `REG` | 0..* | `constrains` |
| implemented by | `implemented_by` | `FEAT` | `IMP` | 0..* | `implements` |
| produces | `produces` | `FEAT` (in traceability); also units in DAG | `OUT` (in traceability); `ART`, `OUT` (in DAG) | 0..* | — |
| constrains | `constrains` | `REQ` → `FEAT`, `IMP`; `REG` → `REQ`, `IMP` | as shown | 0..* | `constrained_by` (FEAT side) |
| verified by | `verified_by` | `REQ`, `REG` | `TEST` | 0..* | `verifies` |
| addresses | `addresses` | `DEC` | `REQ`, `REG` | 0..* | — |
| shapes | `shapes` | `DEC` | `IMP`, `CODE` | 0..* | — |
| supersedes | `supersedes` | `DEC`, contracts | same entity kind as source | 0..* | — |
| implements | `implements` | `IMP` | `FEAT`, `REQ` | 0..* | `implemented_by` |
| guided by | `guided_by` | `IMP` | `DEC` | 0..* | — |
| code (group) | `code` | `IMP` | `CODE` | 0..* | — |
| tests (group) | `tests` | `IMP` | `TEST` | 0..* | — |
| downstream outputs | `downstream_outputs` | `IMP` | `OUT` | 0..* | — |
| verifies | `verifies` | `TEST` | `REQ`, `REG` | 0..* | `verified_by` |
| depends on | `depends_on` | DAG unit | DAG unit | 0..* | `blocks` (MUST be exact inverse) |
| blocks | `blocks` | DAG unit | DAG unit | 0..* | `depends_on` |
| consumes | `consumes` | DAG unit | `ART` | 0..* (each entry MUST match a `produces`) | — |

### 3.2 Review-readiness relations

The review-readiness schemas use a separate, equally closed set of
predicates. Sources/targets here match the `LINK_FIELDS` mapping in
the reference `validate_review_readiness.py` validator shipped with
the upstream DAG-TOML tooling repository.

| Predicate | Field name | Source entity | Allowed target entities | Cardinality | Inverse |
|---|---|---|---|---|---|
| artifact class | `artifact_class` | gates | artifact_classes | 1 (singular) | — |
| depends on (contracts) | `depends_on` | contracts | contracts | 0..* | — |
| supersedes (contracts) | `supersedes` | contracts | contracts | 0..* | — |
| related to | `related_to` | contracts | contracts | 0..* | — |
| applies to | `applies_to` | contracts | unconstrained label | 0..* | — |
| verified by (contracts) | `verified_by` | contracts | unconstrained label | 0..* | — |
| claim (matrix) | `claim` | matrix | claims | 1 (singular) | — |
| claim id (alias) | `claim_id` | matrix | claims | 1 (singular) | — (alias of `claim`) |
| evidence (matrix) | `evidence` | matrix | evidence | 1 (singular) | — |
| evidence id (alias) | `evidence_id` | matrix | evidence | 1 (singular) | — (alias of `evidence`) |

Profile-defined predicates live in profile ontology extensions and are
not part of the core relation vocabulary above.

### 3.3 Closed-vs-open extension points (summary)

- **Entity kinds (core):** closed — adding a new entity to the core
  ontology requires a core `ontology_version` bump.
- **Entity kinds (profiles):** open — profiles MAY add new entity
  kinds with new prefixes (`GUAR:`, `THREAT:`, etc.) inside their own
  ontology extension files. After first publication, each addition
  bumps the **profile's** `ontology_version`, not the core one.
- **Relation predicates:** **closed in the core ontology.** Profiles
  MAY define their own predicates, but MUST namespace them in their
  ontology extension (e.g. `agent-assurance:mitigates`).
- **`requirement_kind`, `test_kind` (core):** open — profiles MAY
  extend the value sets via their own ontology extension. After
  first publication, adding a value to a core attribute vocabulary
  bumps the core `ontology_version`; adding a value to a profile-only
  attribute vocabulary (e.g. `trigger_kind`) bumps the profile's
  `ontology_version`. `schema_version` only bumps if the on-file
  shape changes.
- **Status enums** (DAG units, review-readiness): closed. Changes
  require a major `schema_version` bump.

### 3.4 Direction and inverse pairs

Several predicates form explicit inverse pairs. Validators SHOULD check
inverse consistency where both ends are present in the same document.

| Predicate | Inverse | Required to match |
|---|---|---|
| `realizes` | `realized_by` | when both ends are in the same document |
| `constrains` | `constrained_by` | when both ends are in the same document |
| `verifies` | `verified_by` | when both ends are in the same document |
| `implements` | `implemented_by` | when both ends are in the same document |
| `depends_on` | `blocks` | **MUST match exactly** (DAG hard invariant) |

---

## 4. Per-entity attributes the ontology fixes

Beyond their structural fields, several entities carry attributes
whose value sets are part of the ontology — not just per-file schema.

### Requirements

```toml
[[requirements]]
id               = "REQ:checkout-totals-include-tax"
requirement_kind = "functional"   # see spec.md §3
priority         = "must"         # must | should | could
statement        = "..."
```

- **`priority`** — closed set `must | should | could`. Used by
  release-train policy packs to decide what may slip versus what
  blocks a cut. Default if omitted is `must`.
- **`requirement_kind`** — extensible (see [traceability-kind.toml](traceability-kind.toml)).

### Tests

- **`test_kind`** — extensible (see [traceability-kind.toml](traceability-kind.toml)).

### Decisions

- **`supersedes`** — links MUST NOT form a cycle. Validators reject
  cyclic decision chains.

---

## 5. Hard invariants the ontology adds (beyond per-kind invariants)

In addition to the per-kind hard invariants in
[spec.md §5](../spec.md#5-hard-invariants), the ontology imposes:

1. **Every relation target ID resolves.** A predicate value that names
   an entity not present in the document is a validation error.
2. **Predicate targets respect the allowed-target list in §3.** A
   `REQ:` may not be the target of `derived_from`; an `INT:` may not
   be the target of `verified_by`.
3. **Every `REQ:` and `REG:` has at least one downstream realisation
   path** through `constrains` and/or `verified_by` (the downstream
   fields the truth-source traceability validator enforces for
   requirements and regulations).
4. **`derived_from` and `supersedes` chains are acyclic.**
5. **`CODE:` and `TEST:` entries point to concrete repo paths**
   (`path` field is required).

---

## 6. Machine-readable companion

The same vocabulary is encoded for tools in
[ontology.toml](ontology.toml). The TOML file is generated from this
prose definition (or vice versa); they MUST agree, and an
ontology-aware validator SHOULD reject a document that names a
relation predicate or entity kind absent from the **loaded core
ontology plus any applicable profile ontology extensions** (the
profile extension a document declares via `framework_profile`). A
validator that loads only the core ontology MUST scope its rejection
rule to documents that carry no `framework_profile`.

---

## 7. Why an ontology at all

Two reasons, both load-bearing for this project:

- **Knowledge transfer.** A new contributor or downstream integrator
  can answer "what can `REQ:` link to?" by reading one table instead
  of triangulating across the validator code, the per-kind doc, and
  the worked examples.
- **Interoperability.** Tools that read DAG-TOML graphs (impact
  analysis, audit pipelines, release-train evaluators) can be
  ontology-agnostic in their core and load the vocabulary at run-time.
  A new profile that adds entities or extends value sets becomes a
  data change, not a code change.

---

## 8. IJB primitive mapping (substrate annotation)

Every block in this ontology — and every conforming instance file —
reduces to one of the six IJB primitives (Thing, Scope, Path,
Observed, Constraint, Time). The full mapping is normative and is
spelled out in [spec.md §10](../spec.md#10-foundation-ijb); the
substrate documents themselves live under
[`foundations/ijb/`](../foundations/ijb/) (start with
[`primitives.md`](../foundations/ijb/primitives.md) and
[`canonical-assertion-grammar.md`](../foundations/ijb/canonical-assertion-grammar.md)).

The on-disk encoding of the mapping is:

- Every `[[entities]]` block in this ontology and the profile
  extension carries `ijb_primitive = "thing"`, `ijb_class =
  "structural"`. A per-document entity declaration
  (`[[requirements]]`, `[[threats]]`, etc.) is the corresponding
  `thing/instance` fact.
- Every `[[relations]]` block carries `ijb_primitive = "path"`,
  `ijb_class = "structural"`. Each instance edge in an authored
  document — `verified_by = [...]`, `consumes = [...]`, and so on —
  is the corresponding `path/instance` fact.
- Every `[[attribute_vocabularies]]` block and the `[extension_rules]`
  table carry `ijb_primitive = "constraint"`, `ijb_constraint_type =
  "structural"`. Per-instance attribute values (`priority = "must"`,
  `residual_risk = "accepted"`) are `observed/instance` facts.
- The `[meta]` fields `framework_profile` and `template_kind` are
  `scope/structural`; `schema_version` and `ontology_version` are
  `constraint/structural`. These are documented inline in each
  ontology file under `[meta.ijb_field_primitives]`.

The mapping is enforced by
[`validators/validate_ijb_conformance.py`](../validators/validate_ijb_conformance.py).
The validator runs against this file, the profile ontology extension,
every kind-descriptor (no-op for descriptor files; the descriptor
surface is covered by `validate_kind_descriptor.py`), and every
conforming instance file. For instance files it loads this ontology
plus the profile ontology named in `[meta].framework_profile`, then
checks that every entity prefix used and every relation predicate
used resolves to a declared structure carrying an `ijb_primitive`.

Two clarifications from SPEC §10 that bear repeating here:

- **The `ijb_*` annotation fields are agent-assurance metadata that
  mirrors IJB's own distinctions where they exist**, not a literal
  IJB grammar fragment. IJB's `canonical-assertion-grammar` document
  uses `class=structural|instance` on `thing` and `path`, and
  `type=structural|policy|observed` on `constraint`; this ontology
  uses `ijb_class` and `ijb_constraint_type` to mirror those
  distinctions. `observed` and `time` have no class field in IJB and
  this ontology does not add one.
- **Free-text fields are an explicit deviation from IJB grammar.**
  IJB restricts free text to inside quoted `rule=` values. DAG-TOML
  carries substantive prose fields (`prose`, `statement`, `summary`,
  `description`, …). The deviation is declared in SPEC §10.3: prose
  defaults to `observed/instance`, and where a prose field carries
  normative force (a contract `statement`, a requirement
  `statement`, a hard-invariant `statement`) it is also tagged
  `constraint/policy`. The structural validator does not enforce
  the prose-classification ban in v0.1.0; a v0.2.0 reality-check
  validator may.
