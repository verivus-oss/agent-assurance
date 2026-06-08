# AGENTS.md

This file provides guidance for agent-based contributors working with code in this repository.

## What this repo is

This is the **public specification** for DAG-TOML — a family of TOML schemas
describing how software-engineering agents plan, sequence, and prove their
work. It is **not** a runtime; reference runtimes consume files written to
this spec and live in separate repositories.

`spec.md` is the authoritative prose. `README.md` is the entry point for
readers. Three layers:

- **Core DAG-TOML** (`core/`) — three template kinds: `implementation-dag`,
  `traceability`, `review-readiness` (which expands into `readiness-gate` +
  `contract-declaration` + `evidence-matrix`).
- **Agent Assurance Profile** (`profiles/agent-assurance/`) — optional
  extension adding nine kinds: `spec-contract`, `threat-model`,
  `smoke-validation`, `rollback-plan`, plus the runtime-facing
  `adapter-contract`, `adapter-registry-binding`, `assertion-bundle`,
  `assertion-log-record`, `gate-decision`. Selected by
  `framework_profile = "agent-assurance"` in `[meta]`. The profile also
  ships five deployment tiers (`profiles/agent-assurance/tiers/{solo,
  team, group, organization, enterprise}.toml`) — these are NOT a new
  kind; each tier file is a self-contained `contract-declaration`
  instance. See `profiles/agent-assurance/tiers/README.md`.
- **IJB foundation** (`foundations/ijb/`) — the meta-ontology described
  in `spec.md §10`. Every entity, relation, attribute vocabulary, kind
  descriptor table, and example block carries `ijb_primitive` (one of
  `thing | scope | path | observed | constraint | time`) plus a class
  marker. Enforced by `validators/validate_ijb_conformance.py`.
- **No JSON Schema layer.** The machine-readable contract lives in
  TOML — the `*-kind.toml` descriptors and the ontology files. The
  Python validators under `validators/` enforce both structural and
  semantic rules by reading those declarations. `schemas/` exists but
  is reserved for future generated Taplo schemas (editor tooling);
  no hand-authored JSON Schemas are planned. See `spec.md §9` and
  `schemas/README.md` for the rationale.

## Commands

All checks run via the GitHub Actions workflow `.github/workflows/validate.yml`.
To reproduce locally (Python ≥ 3.11, plus the dependencies in
`requirements.txt` — currently just `networkx`, used by the DAG validator —
and the [Taplo](https://taplo.tamasfe.dev/) CLI for TOML syntax linting):

```bash
# One-time setup
python3 -m pip install -r requirements.txt
# Install Taplo: see https://taplo.tamasfe.dev/cli/installation/ —
# CI uses the pinned release binary from tamasfe/taplo on GitHub.

# Lint every TOML for syntax errors and duplicate keys
taplo lint

# Parse every TOML in the repo with the TOML 1.1 reference parser
# (validators/_toml11.py wraps tomli >= 2.4.0; stdlib tomllib is 1.0-only).
# Install it first: pip install --no-binary tomli -r requirements/toml.txt
python3 -c 'import sys, pathlib; sys.path.insert(0, "validators"); import _toml11 as tomllib; [tomllib.loads(p.read_text()) for p in pathlib.Path(".").rglob("*.toml") if not any(x.startswith(".") for x in p.parts)]'

# Validate every kind descriptor (the *-kind.toml files)
for f in core/*-kind.toml profiles/agent-assurance/*-kind.toml; do
  python3 validators/validate_kind_descriptor.py "$f" --repo-root . --check-references-exist
done

# Validate a single descriptor
python3 validators/validate_kind_descriptor.py core/traceability-kind.toml --repo-root . --check-references-exist

# Validate the canonical core examples (strict mode, as CI does)
python3 validators/validate_implementation_dag.py examples/minimal-implementation-dag.toml
python3 validators/validate_traceability.py     examples/minimal-traceability.toml
python3 validators/validate_review_readiness.py examples/minimal-review-readiness/review_readiness.toml
python3 validators/validate_review_readiness.py examples/minimal-review-readiness/contract_declaration.toml
python3 validators/validate_review_readiness.py examples/minimal-review-readiness/evidence_matrix.toml

# IJB conformance — runs on ontologies, every kind descriptor, and core examples
python3 validators/validate_ijb_conformance.py core/ontology.toml
python3 validators/validate_ijb_conformance.py profiles/agent-assurance/ontology.toml
for f in core/*-kind.toml profiles/agent-assurance/*-kind.toml; do
  python3 validators/validate_ijb_conformance.py "$f"
done

# Deployment tier files are contract-declaration instances
for f in profiles/agent-assurance/tiers/*.toml; do
  python3 validators/validate_review_readiness.py "$f"
done
```

The canonical `examples/minimal-review-readiness/` is a **directory**
containing three files (`review_readiness.toml`, `contract_declaration.toml`,
`evidence_matrix.toml`) — not a single file. All other minimal examples are
flat TOML files at the top of `examples/`.

Runtime-facing profile examples beyond `gate-decision` (`adapter-contract`,
`adapter-registry-binding`, `assertion-bundle`, `assertion-log-record`)
currently have no dedicated semantic validator. CI parses them as TOML,
runs the primary Rust and Go validators for shared meta/provenance/IJB
surface, and runs `validate_ijb_conformance.py` as a Python cross-check.
For these files today the instance IJB surface is intentionally small
(roughly one `id` field plus any declared ontology-predicate values).
The conformance pass is therefore mostly a structural-shape lock: any
future content that introduces a `PREFIX:slug`-shaped token under a
validated key, or a non-conforming `units.<id>` table key, will fail CI.
Their kind descriptors get the full kind-descriptor, §13
abstraction/capability-envelope, and IJB validator passes in Rust, Go,
and Python.

CI also enforces:
- No bare `kind = ...` field in `examples/` (must use role-specific names —
  see below).
- No hardcoded internal repository paths (specifically anything under
  the internal source tree mount) leaking into the public repo.
- Every canonical example and tier file listed in `validate.yml` exists.

## Architecture concepts that span files

### The two version pins

Every file carries `schema_version` (semver, file shape). Files participating
in the relation graph also carry `ontology_version` (integer, relation
vocabulary). They bump **independently** — see `core/ontology.md §1`.
Pre-publication, `schema_version` stays at `"0.1.0"` and
`ontology_version` stays at `1` regardless of edits. The first public
stable schema can become `schema_version = "1.0.0"` when maintainers are
ready to promise schema stability; ontology snapshots remain monotonic
positive integers.

### The `*-kind.toml` (kind-descriptor) pattern

Each `template_kind` is documented by a self-contained TOML file with
`template_kind = "kind-descriptor"` and a `[kind]` table carrying prose,
required fields, hard-invariant pointers, and example pointers. These live
in `core/*-kind.toml` and `profiles/agent-assurance/*-kind.toml`. When you
edit one, the matching example under `examples/` and any cross-referenced
ontology entries (`core/ontology.toml`, `profiles/agent-assurance/ontology.toml`)
must move together — CI checks the `kind.example.file`,
`kind.hard_invariants.enforced_by`, and `kind.references` paths all exist.

### Role-specific field names (no bare `kind`)

`spec.md §3` is firm about this: never use `kind` as a field name in
instance documents. Use the role-specific variants:

- `template_kind` (root `[meta]` only)
- `requirement_kind` in `[[requirements]]`
- `test_kind` in `[[tests]]`
- `trigger_kind` in `[[rollback.triggers]]`

The CI step "Verify no banned markers" greps for bare `kind =` in `examples/`
and fails the build. Validators MUST also accept legacy `kind` as a synonym
(deprecation removed before the first stable `schema_version = "1.0.0"`),
but new content must not introduce it.

### Hard invariants vs. structural validation

Graph-shaped invariants listed in `spec.md §5` — `blocks` is the
inverse of `depends_on`, each `ART:` has exactly one producer,
`critical_path` is the longest weighted path, cross-document `REQ:`
references resolve — are enforced by the Python validators under
`validators/`, reading the contract declared in the `*-kind.toml`
descriptors and the ontology files. Don't propose moving them into a
JSON Schema layer — there is none, and `spec.md §9.1` explains why
one would be a category error in a TOML spec.

### IJB primitives on every declaration

`spec.md §10` makes IJB the structural foundation. Every `[[entities]]`,
`[[relations]]`, and `[[attribute_vocabularies]]` block in the ontology
files MUST carry `ijb_primitive` (one of `thing | scope | path | observed
| constraint | time`) plus a class marker (`ijb_class` is `structural` or
`instance`; for attribute vocabularies it's `ijb_constraint_type` ∈
`{structural, policy, observed}`). Every `*-kind.toml` follows rules
KD1–KD3: the `[kind]` table is `(thing, structural)`; each
`[[kind.required_fields]]`, `[[kind.required_sections]]`,
`[[kind.hard_invariants]]`, and `[kind.relation_to_ontology]` is
`(constraint, structural)`; each `[[kind.example]]` is `observed`. When
you add or rename anything in those tables, run
`validators/validate_ijb_conformance.py` against the changed file before
opening a PR — it's the fastest signal that the new declaration is
properly tagged.

### Deployment tiers are instances, not a kind

Tier files under `profiles/agent-assurance/tiers/` form a documented
ladder (`solo ⊂ team ⊂ group ⊂ organization ⊂ enterprise`), but
inheritance is **not** a schema feature — each file lists its complete
contract set and is validated independently as a `contract-declaration`.
Don't propose adding cross-document inheritance to `contract-declaration`;
the rationale is in `profiles/agent-assurance/tiers/README.md`.
`verified_by` strings in tier files (e.g.,
`"adapter-contract:authority-check@1"`) are free-form labels at the SPEC
layer — they reference runtime artifacts.

### Profile alias

Legacy files may carry `framework_profile = "AGDF"` (the internal codename).
Readers SHOULD treat it as a synonym for `"agent-assurance"`. Don't rename
it back in new content.

## Conventions for spec changes

From `CONTRIBUTING.md`:

- A PR that changes a `template_kind` MUST update the matching `*-kind.toml`
  descriptor, the ontology entries it references, and the affected example
  under `examples/` in the same change — no drift between prose and
  machine-readable form.
- Every PR updates `CHANGELOG.md` under `[Unreleased]`.
- Filenames: instance examples use `UPPERCASE_DESCRIPTIVE.toml`; kind
  descriptors use the `*-kind.toml` suffix; generic templates use
  `*_TEMPLATE_GENERIC.toml`.
- TOML style: UTF-8 no BOM, 2-space indent, multi-line arrays one item per
  line with trailing commas.

## Out of scope here

- Runtime implementations (separate repos). Reference *database schemas*
  for ingesting DAG-TOML instances live under `reference/database/` as
  **non-normative** implementer guidance — they are derived from the
  ontology files and `*-kind.toml` descriptors, not authoritative.
- Closed-source profile variants.
- Renaming the root `[meta]` table — `spec.md §2.1` explains why it stays.
