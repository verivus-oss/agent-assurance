# DAG-TOML

[![Validate](https://github.com/verivus-oss/agent-assurance/actions/workflows/validate.yml/badge.svg)](https://github.com/verivus-oss/agent-assurance/actions/workflows/validate.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/verivus-oss/agent-assurance/badge)](https://scorecard.dev/viewer/?uri=github.com/verivus-oss/agent-assurance)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

**Declarative policy, workflow, and review evidence for
agent-driven development.**

DAG-TOML is a public specification for describing how software agents
plan work, sequence dependencies, cite evidence, declare their
abstraction boundaries, and prove readiness for human review. It is
intentionally a data format, not an execution runtime. Runtimes and
sandboxes decide what an agent may do; DAG-TOML describes what the
agent intends to do, in what order, what evidence is required, what
upstream artifacts the work depends on, and whether the work is ready
for review.

## Why this matters

If an AI agent can generate 10,000 lines of code in seconds, manually
reading the diff to catch a subtle supply-chain mutation is impossible.
*Writing the code is becoming the new assembly language.* The work
shifts upward — to **provable intent** (mathematically validating what
a change *means*) and **structural governance** (mapping and enforcing
the logic graph of an artifact, so abstraction boundaries are never
silently violated).

DAG-TOML is the data substrate for both. It is only "too complex" if
you are building a bicycle. If you are building autonomous,
self-generating infrastructure, provable clarity is the minimum barrier
to entry.

## Status

| Surface | `schema_version` | `ontology_version` | Stability |
| --- | --- | --- | --- |
| Core DAG-TOML schema | `0.1.0` | n/a | Draft Specification |
| Core ontology | `0.1.0` | `1` | Draft Specification |
| Agent Assurance Profile | `0.1.0` | `1` | Draft Specification |
| Cost Profile | `0.1.0` | `1` | Draft Specification |
| Disclosure Profile | `0.1.0` | `1` | Draft Specification |

The public repository was minted at `v0.1.0` on 2026-05-27. The document
maturity remains `Draft Specification`: `schema_version` is a semver
string that pins the file shape; `ontology_version` is a monotonic
positive integer snapshot that pins the relation vocabulary. They
intentionally use different versioning forms because consumers ask
different questions of each surface. Release tags are separate from the
document maturity label.

The first public stable schema can become `schema_version = "1.0.0"`
when maintainers are ready to promise schema stability. The core and
profile ontologies stay at `ontology_version = 1` until the first
post-publication vocabulary change, then advance to `2`, `3`, and so
on.

## Start Here

Choose by reader role.

### If you want to understand the format

| Goal | Read |
| --- | --- |
| The normative specification | [spec.md](spec.md) |
| Field-level reference | [docs/field-reference.md](docs/field-reference.md) |
| Runtime / non-runtime boundary | [docs/architecture.md](docs/architecture.md) |
| Why TOML + safe-language validators (no JSON Schema) | [spec.md §9.1](spec.md#91-why-no-json-schema-layer) |
| Adoption guidance | [docs/adoption.md](docs/adoption.md) |

### If you want to author DAG-TOML

| Goal | Read |
| --- | --- |
| Coordinate agent work as a DAG | [core/implementation-dag-kind.toml](core/implementation-dag-kind.toml) |
| Trace intent to requirements, code, tests, outputs | [core/traceability-kind.toml](core/traceability-kind.toml) |
| Gate work before review | [core/readiness-gate-kind.toml](core/readiness-gate-kind.toml), [core/contract-declaration-kind.toml](core/contract-declaration-kind.toml), [core/evidence-matrix-kind.toml](core/evidence-matrix-kind.toml) |
| See minimal conforming files | [examples/](examples/) |
| Validate source-code symbols against a traceability file | [docs/language-validators.md](docs/language-validators.md) (Rust, Go, TypeScript, Java) |

### If you want to enforce policy

| Goal | Read |
| --- | --- |
| Declare abstraction boundaries and capability envelopes | [spec.md §13](spec.md#13-abstraction-class-and-capability-envelope) |
| Propagate brittleness through upstream evidence | [spec.md §12](spec.md#12-the-closure-root-rule-brittleness-propagation) |
| Add stronger assurance controls (gates, threat models, smoke validations, rollback plans, adapter contracts, gate-decisions) | [profiles/agent-assurance/overview.md](profiles/agent-assurance/overview.md) |
| Pick a deployment tier (`solo` ⊂ `team` ⊂ `group` ⊂ `organization` ⊂ `enterprise`) | [profiles/agent-assurance/tiers/README.md](profiles/agent-assurance/tiers/README.md) |
| Forbid an agent from approving its own self-modifying gate-decision (INV06) | [profiles/agent-assurance/gate-decision-kind.toml](profiles/agent-assurance/gate-decision-kind.toml) (search for `INV06`) |
| Account for cost as a first-class artifact | [profiles/cost/PROFILE.toml](profiles/cost/PROFILE.toml), [profiles/cost/cost-record-kind.toml](profiles/cost/cost-record-kind.toml) |
| Redact or selectively disclose evidence | [profiles/disclosure/PROFILE.toml](profiles/disclosure/PROFILE.toml), [profiles/disclosure/disclosure-attestation-kind.toml](profiles/disclosure/disclosure-attestation-kind.toml), [profiles/disclosure/redaction-manifest-kind.toml](profiles/disclosure/redaction-manifest-kind.toml), [profiles/disclosure/selective-disclosure-proof-kind.toml](profiles/disclosure/selective-disclosure-proof-kind.toml) |

### If you want to implement a validator

| Goal | Read |
| --- | --- |
| Primary safe-Rust validator | [tools/dagtoml-validate-rs/](tools/dagtoml-validate-rs/) |
| Primary safe-Go validator | [tools/dagtoml-validate-go/](tools/dagtoml-validate-go/) |
| Python reference validators (cross-check, not normative) | [validators/](validators/) |
| TOML parser-conformance harnesses (`toml-test`) | [Makefile](Makefile) — `toml-conformance` (Go-parser) and `toml-conformance-rs` (Rust-parser) |
| Per-kind contract (what each `*-kind.toml` declares) | the `*-kind.toml` descriptors under [core/](core/) and [profiles/](profiles/) |
| IJB substrate (the meta-ontology that every kind binds to) | [foundations/ijb/](foundations/ijb/), [spec.md §10](spec.md#10-foundation-ijb) |

## Repository Map

```text
spec.md                         Normative file-format specification
CHANGELOG.md                    Per-release notes (calendar UTC tags)
GOVERNANCE.md                   Decision rules and release process
core/                           Core kind descriptors and ontology
profiles/agent-assurance/       Optional Agent Assurance Profile
                                + 5 deployment tiers (solo→enterprise)
profiles/cost/                  Optional Cost Profile (cost-record kind)
profiles/disclosure/            Optional Disclosure Profile
foundations/ijb/                IJB substrate reference material
examples/                       Minimal conforming documents per kind
validators/                     Python reference validators (cross-check)
tools/dagtoml-validate-rs/      Primary safe-Rust validator
tools/dagtoml-validate-go/      Primary safe-Go validator
tools/dagtoml-rdf/              Rust generator → RDF/Turtle
tools/dagtoml-rdf-go/           Go port of dagtoml-rdf
tools/dagtoml-duckdb/           Rust generator → DuckDB
tools/dagtoml-duckdb-go/        Go port of dagtoml-duckdb
tools/toml-test-decode-rs/      toml-test conformance shim (Rust parser)
skills/                         Authoring skills that emit governed packages
docs/                           Non-normative architecture and process notes
reference/database/             Non-normative DB schemas (Postgres, SQLite,
                                DuckDB, RDF/Turtle+SHACL, Neo4j)
schemas/                        Reserved for generated editor schemas
Makefile                        Developer convenience targets (toml-conformance{,-rs,-all})
```

The machine-readable contract lives in the `*-kind.toml` descriptors and
the ontology files. Validators read those declarations and enforce both
structural rules and graph-shaped semantic invariants.

## Validation tooling

DAG-TOML is validated by three independent implementations on every
push and pull request. Divergence between primary and reference is a
build break.

| Layer | Implementation | Role |
| --- | --- | --- |
| Syntax | [Taplo](https://taplo.tamasfe.dev/) | TOML 1.0 lint, duplicate-key detection |
| Parser conformance | `toml-lang/toml-test` suite | Verifies the parsers the primary validators import (`BurntSushi/toml` for Go, `toml 0.8` crate for Rust) |
| Semantics — **primary** | `tools/dagtoml-validate-rs/` (safe Rust, `#![forbid(unsafe_code)]`) | Authoritative for profile-descriptor, the disclosure-profile kinds, §2.2 and §2.5–§2.7 meta surface, §11.1 `[provenance.encryption]`, §12.8 `[provenance].source_sha256` closure roots, and gate-decision INV06 |
| Semantics — **primary** | `tools/dagtoml-validate-go/` (safe Go, no `unsafe` import) | Same surface as Rust; CI runs both against every canonical example + tier file + profile descriptor on each push, and both must exit 0 |
| Semantics — reference / migration backlog | `validators/*.py` | Cross-check on the primaries' surface, plus legacy CI-enforced surfaces still awaiting Tier-1 ports (cost-record, abstraction-class §13, rollback-plan trigger closure, implementation-dag, traceability, review-readiness, IJB conformance) |
| Symbol traceability (optional) | `validators/validate_code_symbols.py` (sqry-backed) | Confirms `[[code]]` symbols in traceability files exist in real Rust/Go/TypeScript/Java sources |

Why a Rust + Go + Python triad: the specification is for security and
legal-grade artifacts; one implementation cannot self-vouch. Rust and
Go are the two **primary** language ecosystems where safe-by-default
parsers exist (`#![forbid(unsafe_code)]` Rust crates, `unsafe`-free
Go modules); Python is the historical reference, cross-check, and the
temporary home for explicitly documented legacy surfaces until they are
ported to Tier 1.

## Local Validation

```sh
# Python deps for the reference validators
python3 -m pip install -r requirements.txt

# Install Taplo per https://taplo.tamasfe.dev/cli/installation/
taplo lint

# Build the primary validators (one-time, ~30s)
cd tools/dagtoml-validate-rs && cargo build --release && cd -
cd tools/dagtoml-validate-go && go build -o /tmp/dagtoml-validate-go ./... && cd -

# Parser conformance (BurntSushi for Go, toml 0.8 for Rust)
make toml-conformance-install
make toml-conformance-all   # runs both Go-parser and Rust-parser suites

# Spot-check a canonical example through every validator
./tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs \
  --repo-root . examples/minimal-implementation-dag.toml
/tmp/dagtoml-validate-go --repo-root . examples/minimal-implementation-dag.toml
python3 validators/validate_implementation_dag.py examples/minimal-implementation-dag.toml
python3 validators/validate_traceability.py examples/minimal-traceability.toml
python3 validators/validate_review_readiness.py \
  examples/minimal-review-readiness/review_readiness.toml
python3 validators/validate_ijb_conformance.py core/ontology.toml
python3 validators/validate_closure_root.py --discover .         # SPEC §12
python3 validators/validate_abstraction_class.py --repo-root . \
  core/*-kind.toml profiles/*/*-kind.toml                        # SPEC §13
```

CI runs the full validator matrix (~25 steps) on every push and pull
request: syntax lint, manifest drift, both primary validators against
every canonical example + tier file + profile descriptor, Python
cross-checks, IJB conformance, closure-root, abstraction-class +
capability-envelope, kind-descriptor structural rules, rollback-plan
trigger_kind closure, provenance bindings, skill packages, language
fixture, and the banned-marker / leaked-internal-path scan. See
[.github/workflows/validate.yml](.github/workflows/validate.yml) for
the source of truth.

## Contributing

Issues are open for specification ambiguities, missing edge cases,
validator defects, example improvements, and profile proposals. Start
with [CONTRIBUTING.md](CONTRIBUTING.md); the issue templates are
designed to capture the smallest useful amount of information.

A PR that changes a `template_kind` MUST update the matching
`*-kind.toml` descriptor, the ontology entries it references, and the
affected example under `examples/` in the same change — no drift
between prose and machine-readable form. Every PR updates
[CHANGELOG.md](CHANGELOG.md) under `[Unreleased]`.

All contributions are accepted under the Apache License, Version 2.0.
Security reports should follow [SECURITY.md](SECURITY.md), not public
issues.

## Governance

The repository uses a maintainer-led specification process. Material
specification changes require an issue, a pull request, passing
validators, and maintainer review; substantive changes to spec / core /
profile / validator surfaces additionally require an independent
multi-LLM review under [tools/review-request-dag.toml](tools/review-request-dag.toml)
before merge. See [GOVERNANCE.md](GOVERNANCE.md) for decision rules
and release expectations.

## License

This specification is licensed under the
[Apache License, Version 2.0](LICENSE).
