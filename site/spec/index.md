# DAG-TOML Specification

Status: Draft Specification

Schema version: 0.1.0

The normative source is `spec.md` in the repository:

https://github.com/verivus-oss/agent-assurance/blob/main/spec.md

## Root Table

Every DAG-TOML file has a root `[meta]` table:

```toml
[meta]
schema_version = "0.1.0"
template_kind = "implementation-dag"
docs = "https://agent-assurance.dev/spec/"
```

`schema_version` pins the file shape. `ontology_version`, when present, pins the relation vocabulary snapshot.

## Core Kinds

- `implementation-dag`
- `traceability`
- `readiness-gate`
- `contract-declaration`
- `evidence-matrix`
- `kind-descriptor`
- `profile-descriptor`

## Key Rules

- DAG-TOML is a format specification, not an execution runtime.
- Validators enforce structural and semantic conformance.
- Closure roots make upstream evidence brittleness explicit.
- Profiles may extend core kinds but must not reuse spec-reserved semantics.
