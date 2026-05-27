# Examples

Minimal examples of DAG-TOML files.

## Files in this directory

Short, focused examples that show the shape of a single
`template_kind`:

- [`minimal-implementation-dag.toml`](minimal-implementation-dag.toml)
  — two units, one artifact.
- [`minimal-traceability.toml`](minimal-traceability.toml) — one
  requirement, one test, one code reference.
- [`minimal-review-readiness/`](minimal-review-readiness/) — a complete
  bundle of `readiness-gate` + `contract-declaration` +
  `evidence-matrix`, using the validator-compatible shape.

These examples are validator-compatible against the reference
validators shipped with the upstream tooling repository at the same
schema version. Run the validators against any of them as a sanity
check.

## Worked Agent Assurance Profile example

A larger, real-world Agent Assurance Profile bundle (four prose
documents plus eight DAG-TOML files for a Rust performance milestone)
is published with the upstream tooling repository, not in this spec
repo. It is referenced in [profiles/agent-assurance/overview.md](../profiles/agent-assurance/overview.md)
for context only.
