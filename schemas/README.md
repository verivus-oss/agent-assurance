# schemas/

This directory does not hold the machine-readable schema for
DAG-TOML. **The schema lives in TOML**, distributed across the
`*-kind.toml` files in `core/` and `profiles/agent-assurance/` and the
ontology files at `core/ontology.toml` and
`profiles/agent-assurance/ontology.toml`. Together those files
declare every required field, every closed value set, and every
relation predicate that a conforming document must respect. The
reference validators under `validators/` consume those declarations
and apply both structural and semantic checks.

A separate JSON Schema layer would duplicate what the kind
descriptors already declare. We decided against publishing one — see
the spec change at `spec.md §9` (Validation).

## When this directory will hold something

If editor inline-validation (Taplo, Even Better TOML for VSCode, IntelliJ
TOML plugin) becomes a meaningful adoption ask, the right answer is to
**generate** Taplo-compatible schemas from the kind descriptors at
build time and publish them here. That preserves a single source of
truth (the kind descriptors) and avoids the maintenance burden of
hand-authored parallel JSON Schemas.

There is no generator today. When the demand surfaces, the work is:

1. Add a `tools/generate_taplo_schema.py` that walks each
   `*-kind.toml`, the matching ontology entries, and the SPEC root
   table to emit a JSON Schema per `template_kind`.
2. CI invokes the generator on every push; the generated artifacts
   land under this directory under names like
   `<template-kind>.taplo.schema.json`.
3. Documentation in `CONTRIBUTING.md` explains how an editor user
   wires a `taplo.toml` to load the generated schemas.

Until then, this directory is intentionally empty (this README
aside).
