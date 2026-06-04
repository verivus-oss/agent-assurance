# Architecture

**How DAG-TOML relates to the systems around it.**

This document is non-normative. The normative spec is [spec.md](../spec.md).
The intent here is to make explicit which jobs DAG-TOML does, which jobs it
delegates, and where consumer software typically slots in.

---

## 1. What DAG-TOML is

DAG-TOML is a **format**: a family of TOML schemas (`implementation-dag`,
`traceability`, `readiness-gate`, `contract-declaration`,
`evidence-matrix`, plus the four Agent Assurance Profile kinds) plus a
machine-readable contract — the `*-kind.toml` descriptors and the
`ontology.toml` files — that says what a conforming document must look
like and which graph-shaped invariants must hold.

It is data, not behaviour. A DAG-TOML file describes intent, dependency
structure, evidence expectations, and review readiness. It does not run
agents, schedule work, sign artifacts, issue identities, or execute
rollbacks. Those are jobs for the runtime layer.

---

## 2. The four roles

Software that touches DAG-TOML files generally falls into one of four
roles. Any single project may play more than one role, but the roles are
distinct concerns.

### 2.1 Validator

A validator reads a candidate DAG-TOML file plus the descriptors and
ontology files it claims to conform to, and emits pass/fail (plus a
diagnostic report). Validators enforce both layers of the contract from
[spec.md §9](../spec.md):

- **Structural** — required fields, allowed values, ID prefix patterns,
  relation predicates.
- **Semantic** — graph-shaped invariants that cannot be expressed as a
  flat schema (`blocks` inverse of `depends_on`, `critical_path` as the
  longest weighted path, cross-document `REQ:` reference resolution,
  acyclic `derived_from` / `supersedes` chains).

The reference validators in [validators/](../validators/) are stdlib-only
Python; they exist to prove that the contract is enforceable from the
declarations and to provide a fixed point against which other
implementations can compare. Conformance is defined by the spec, not by
any particular validator.

### 2.2 Per-repository runtime

A per-repository runtime is the thing that actually drives agents inside
a working tree. It is responsible for:

- Identity, sandboxing, and permission enforcement (which DAG-TOML
  intentionally does not specify; see the [README](../README.md) on
  OpenShell-style sandboxes).
- Reading the implementation DAG to decide which units to attempt, in
  what order, and with what parallelism.
- Writing back the artifacts the spec expects — traceability entries,
  evidence rows, readiness gates, profile artifacts.
- Persisting whatever local state it needs (a SQLite or embedded
  document store is common). DAG-TOML does not prescribe a storage
  schema; runtimes are free to use whatever backing store fits.

A runtime treats DAG-TOML as the source of truth for *what the work is*
and uses its own database as the source of truth for *what has happened
so far*. The on-disk TOML files are the contract; the database is the
runtime's bookkeeping.

### 2.3 Fleet control plane

A control plane sits above many repositories and reduces the readiness
signal across them into a single release-shaped decision. It is the
component most callers of "is this release ready?" actually want.

Control planes read (they do not write) the review-readiness bundle
described in
[core/readiness-gate-kind.toml](../core/readiness-gate-kind.toml),
[core/contract-declaration-kind.toml](../core/contract-declaration-kind.toml),
and [core/evidence-matrix-kind.toml](../core/evidence-matrix-kind.toml).
When the Agent Assurance Profile is in play they also read the profile's
spec contract, threat model, smoke validation, and rollback plan.

The pattern is intentionally pull-based: each repository publishes its
readiness artifacts to a known location and the control plane reads
them. The spec is the wire format. Nothing in this repository assumes a
particular transport, scheduler, or UI.

### 2.4 Consumer tooling

Consumer tooling is everything else that reads or writes DAG-TOML on a
human's behalf — IDE plugins, CI jobs that lint planning bundles, dashboards,
report generators, scaffolders. These tools should read the
`*-kind.toml` descriptors directly rather than baking in field lists. The
descriptors carry the prose explanation, the required-field rules, and
the hard-invariant pointers; that is the supply of truth the tooling
should pull from.

Editor inline-validation (Taplo, Even Better TOML, IntelliJ TOML) is the
one area where the spec anticipates a derived artifact — a Taplo-shaped
JSON Schema **generated** from the kind descriptors at build time and
published under [schemas/](../schemas/). That generator does not exist
today; see [schemas/README.md](../schemas/README.md) and
[spec.md §9.1](../spec.md). Hand-authored JSON Schemas are explicitly
out of scope.

---

## 3. The boundary between spec and runtime

A useful test for whether something belongs in the spec or in a runtime
is to ask: *if I changed this, would conforming files have to change?*
If yes, it is a spec concern. If no, it is a runtime concern.

Another way to say the same thing: DAG-TOML declares **what** a unit of
work, traceability graph, or review artifact is; runtimes decide **how**
to execute, persist, transport, or display it.

| Question | DAG-TOML answer | Runtime / control-plane answer |
| --- | --- | --- |
| What is this document? | `[meta].template_kind`, `schema_version`, optional `framework_profile` | Which loader/parser to call |
| Where is the spec? | Optional `[meta].docs` URL | Cache, pin, or ignore network retrieval |
| What must be true? | Required fields, ontology entries, hard invariants | How and when to evaluate those checks |
| What work exists? | Units, relations, evidence rows, profile declarations | Queueing, scheduling, retries, ownership, persistence |
| What is out of scope? | Execution model, sandbox, identity, signing, transport | Concrete implementation choices |

Examples of runtime concerns that look like they might belong in the
spec but do not:

- How agents are authenticated and what they are allowed to do.
- Whether execution happens in containers, microVMs, or local shells.
- The retry policy when a unit fails, and what counts as failure.
- The on-disk layout of any database the runtime keeps.
- How review-readiness signals are transported from a repository to a
  control plane.

Examples of spec concerns that look runtime-shaped but are not:

- The set of allowed `trigger_kind` values in a rollback plan (the
  Agent Assurance Profile's ontology fixes this so two runtimes agree).
- The fact that `blocks` is the inverse of `depends_on` (a runtime that
  silently broke this would produce DAGs no other tool could consume).
- The cross-document reference shape (`REQ:slug`, `ART:slug`,
  `IMP:slug`, etc.) — see [spec.md §4](../spec.md).

---

## 4. Version negotiation between runtime and spec

A runtime that loads a file pins two things from [meta]:

- `schema_version` — the file shape. A runtime MUST reject files whose
  `schema_version` major component exceeds the version the runtime
  supports.
- `ontology_version` — the relation vocabulary. Files in the relation
  graph carry this independently of `schema_version`; the two bump on
  independent cadences. See [core/ontology.md §1](../core/ontology.md).

Pre-publication, both stay at their declared draft values
(`schema_version = "0.1.0"`, `ontology_version = 1` for core,
`ontology_version = 1` for the Agent Assurance Profile) regardless of
intervening edits, until the first public release. A runtime built
against pre-publication snapshots should not assume those values are
frozen for all time; they will
eventually bump under the policy in [spec.md §8](../spec.md).

---

## 5. The IJB substrate layer

DAG-TOML sits on top of the IJB ("It's Just Business") substrate. IJB
is the framework that says every projectable business fact in its
scope reduces to exactly six primitives — `thing`, `scope`, `path`,
`observed`, `constraint`, `time` — and forbids any other
categorisation at the substrate level.
The full primitive reference lives at
[foundations/ijb/primitives.md](../foundations/ijb/primitives.md);
the canonical assertion grammar IJB itself uses lives at
[foundations/ijb/canonical-assertion-grammar.md](../foundations/ijb/canonical-assertion-grammar.md).

The layering in this repository is:

```
┌────────────────────────────────────────────────────────────────────┐
│  Validators (validate_*.py)                                        │
│  Read the kind descriptors and ontology files; enforce structural  │
│  and semantic invariants on conforming documents.                  │
├────────────────────────────────────────────────────────────────────┤
│  Profile extensions  (profiles/agent-assurance/)                   │
│  Add entity prefixes (GUAR, INV, THREAT, SMOKE, TRIG, ...) and     │
│  attribute vocabularies (likelihood, impact, trigger_kind, ...)    │
│  on top of the core ontology. Carries its own `ontology_version`.  │
├────────────────────────────────────────────────────────────────────┤
│  Core kind descriptors  (core/*-kind.toml)                         │
│  Declare required fields, allowed values, hard invariants, and     │
│  reference the ontology's entities + relations + vocabularies.     │
├────────────────────────────────────────────────────────────────────┤
│  Core ontology  (core/ontology.{md,toml})                          │
│  Closed relation vocabulary, entity inventory, attribute value     │
│  sets, extension rules. Every block carries an `ijb_primitive`     │
│  annotation declaring which IJB primitive it reduces to.           │
├────────────────────────────────────────────────────────────────────┤
│  IJB substrate  (foundations/ijb/)                                 │
│  Six primitives, canonical assertion grammar, reality-check rule.  │
│  Reference material; not loaded by validators directly.            │
└────────────────────────────────────────────────────────────────────┘
```

Concretely, every `[[entities]]` block in the ontology is an IJB
structural Thing; every `[[relations]]` block is an IJB structural
Path; every `[[attribute_vocabularies]]` block (and the
`[extension_rules]` table) is an IJB structural Constraint. The
machine-checkable surface of this layering is the
[`validate_ijb_conformance.py`](../validators/validate_ijb_conformance.py)
validator, which ensures every block declares its primitive, every
declared value is one of the six, and every entity prefix and
relation predicate used in an instance document resolves to a
primitive-typed structural declaration. The full primitive mapping is
normative and lives in [spec.md §10](../spec.md#10-foundation-ijb)
with prose support in
[core/ontology.md §8](../core/ontology.md#8-ijb-primitive-mapping-substrate-annotation).

`foundations/ijb/` itself is reference material — primitive
definitions, canonical-assertion-grammar SPEC, FCO-IM integration
notes, worked examples. The validators do not parse the IJB documents
at runtime; they enforce the agent-assurance encoding of the IJB
mapping that lives in the ontology files. Updates to the IJB
substrate are upstream changes; updates to the agent-assurance
encoding live in this repo.

---

## 6. What this repository does not ship

The reference validators are the only executable artifact in this
repository. There is no runtime, no control plane, and no consumer
tooling published from here. Those live in separate repositories and
are paired with this spec by version pin.

If you are looking for a runtime to drive agents against a real working
tree, or a control plane to aggregate readiness across many
repositories, those are downstream of this spec, not part of it.
