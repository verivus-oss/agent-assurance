---
id: ISS-002
title: `reference/database/graph/schema.cypher` UNWIND data is missing disclosure + cost + profile-descriptor entries
status: open
severity: medium
opened: 2026-05-23
opened_in_commit: 9996826
classification: reference-implementation drift
---

## Symptom

`reference/database/graph/schema.cypher` is one of four reference
database implementations the spec ships (postgres / sqlite / duckdb /
cypher). Three of those four are at parity with the ontology at HEAD
(20 template_kinds / 27 entity_kinds / 31 relation_predicates).
The Cypher seed is **stale by data**, not just by count comments:

| UNWIND block | Cypher seed (HEAD) | Ontology truth |
|---|---:|---:|
| `KindDescriptor` (template kinds) | 15 | 20 |
| `EntityKind` | 23 | 27 |
| `RelationPredicate` | 31 | 31 |

Specifically missing from the Cypher seed:

**5 template_kinds:**

- `disclosure-attestation` (profile:disclosure)
- `redaction-manifest` (profile:disclosure)
- `selective-disclosure-proof` (profile:disclosure)
- `cost-record` (profile:cost)
- `profile-descriptor` (core meta kind added pre-disclosure)

**4 entity_kinds:**

- `disclosure_attestation` (DISC prefix, profile:disclosure)
- `redaction` (RED, profile:disclosure)
- `selective_disclosure_proof` (SDP, profile:disclosure)
- `cost_record` (COST, profile:cost)

**0 relation_predicates** — these were added by the §12 commit
(`cites_upstream` predicate) and were merged into the Cypher
UNWIND block during the §12 work. That row is present.

Current status at commit 9996826: the count-mirror gate
(`validators/check_attribute_values.py`) reports clean against
`MANIFEST.toml [verification.graph].expected_node_counts = {
KindDescriptor = 20, EntityKind = 27, RelationPredicate = 31 }`.
But the actual UNWIND data in the Cypher file does not match those
expectations. The gate cross-checks `expected_node_counts` against
the ontology, not against the Cypher data — so the Cypher data drift
is invisible to the gate.

## Why it matters

Anyone using the Cypher reference (`neo4j` adopters; downstream
property-graph importers; users of the `graph/schema.cypher` as
documentation) sees an incomplete ontology. A Neo4j instance loaded
from the current `schema.cypher` would have:

- Zero `:KindDescriptor` nodes for any disclosure-profile or
  cost-profile kind.
- Zero `:EntityKind` nodes for `DISC`, `RED`, `SDP`, `COST`.
- An `r.predicate` value referring to a `:RelationPredicate` that
  doesn't exist for any disclosure-profile or cost-profile edge.

This is a silent reference-implementation regression. The other
three engine reference seeds (postgres/sqlite/duckdb) are current;
only Cypher lags. Without a gate, the gap grows on every profile
addition.

## Safeguard (what would prevent recurrence)

### Safeguard A — direct data gate (cheap, no new tooling)

Extend `validators/check_attribute_values.py` to count the
`MERGE (k:KindDescriptor ...)`, `MERGE (k:EntityKind ...)`, and
`MERGE (p:RelationPredicate ...)` invocations in `schema.cypher`
(line-grep on `^    {template_kind:`, `^    {entity_kind:`,
`^    {predicate:`) and compare against the ontology-derived
counts. Drift fails CI.

```python
# Sketch inside derive_seed_counts():
cypher = (repo_root / "reference/database/graph/schema.cypher").read_text()
cypher_counts = {
    "KindDescriptor": len(re.findall(r"^\s*\{template_kind:", cypher, re.MULTILINE)),
    "EntityKind": len(re.findall(r"^\s*\{entity_kind:", cypher, re.MULTILINE)),
    "RelationPredicate": len(re.findall(r"^\s*\{predicate:", cypher, re.MULTILINE)),
}
```

This catches the symptom (count drift) but not the content drift
within a row (e.g. a typo in a `predicate` value).

### Safeguard B — generator tool (proper fix, more work)

Write `tools/dagtoml-cypher` parallel to `tools/dagtoml-rdf`:

- Reads `core/ontology.toml` + `profiles/*/ontology.toml` + every
  `*-kind.toml`.
- Emits `reference/database/graph/schema.cypher` deterministically.
- Has a `verify` subcommand that re-parses and counts.
- Wired into CI: if the generator output differs from the
  checked-in file, CI fails with "regenerate via `cargo run -p
  dagtoml-cypher -- --repo-root . -o reference/database/graph/schema.cypher`".

This mirrors the RDF pattern (`tools/dagtoml-rdf` already exists
and is run by `validators/check_manifest_drift.sh`). The Cypher
generator removes the entire hand-maintained-data-class of drift,
not just count drift.

### Safeguard C — convention safeguard

In `CONTRIBUTING.md` (or a new contributors note), document that
"adding a new profile or kind MUST also regenerate
`reference/database/graph/schema.cypher` via `tools/dagtoml-cypher`,
or alternatively update the UNWIND blocks by hand". Without
Safeguard A or B in place, this is the only defence.

## Resolution steps (the actionable fix)

### Path 1 — small fix now (Safeguard A + manual data sync)

1. Add 5 template-kind rows to `schema.cypher:88-104` UNWIND
   block:
   ```cypher
   {template_kind: 'profile-descriptor',      layer: 'core'},
   {template_kind: 'disclosure-attestation',  layer: 'profile:disclosure'},
   {template_kind: 'redaction-manifest',      layer: 'profile:disclosure'},
   {template_kind: 'selective-disclosure-proof', layer: 'profile:disclosure'},
   {template_kind: 'cost-record',             layer: 'profile:cost'},
   ```
2. Add 4 entity-kind rows to `schema.cypher:109-134` UNWIND block:
   ```cypher
   {entity_kind: 'disclosure_attestation', id_prefix: 'DISC', layer: 'profile:disclosure'},
   {entity_kind: 'redaction',              id_prefix: 'RED',  layer: 'profile:disclosure'},
   {entity_kind: 'selective_disclosure_proof', id_prefix: 'SDP', layer: 'profile:disclosure'},
   {entity_kind: 'cost_record',            id_prefix: 'COST', layer: 'profile:cost'},
   ```
3. Update the existing comments at `schema.cypher:88`, `:109`,
   `:141` to remove the "missing" call-outs added during the
   methodology session.
4. Extend `validators/check_attribute_values.py` with the regex
   counters in Safeguard A above. New surface gated; future
   profile additions can't silently skip Cypher.

### Path 2 — generator tool (more work, higher resilience)

1. Scaffold `tools/dagtoml-cypher` from `tools/dagtoml-rdf` as a
   template (same `--repo-root` flag, same ontology-walk shape).
2. Emit `schema.cypher` deterministically. Use comparators to
   ensure the generator output is byte-identical across runs.
3. Add `verify` subcommand that exits 1 if checked-in file
   differs from regenerated.
4. Wire into `validators/check_manifest_drift.sh` the same way
   the RDF generator is wired today.
5. Delete the Path-1 regex counters; the generator + verify
   subsumes them.

## Acceptance criteria

- A clean Neo4j load of `schema.cypher` contains 20 KindDescriptor
  nodes, 27 EntityKind nodes, 31 RelationPredicate nodes.
- `validators/check_attribute_values.py --rdf` (or successor)
  reports `OK` for the Cypher data row counts.
- Adding a new profile (e.g. a hypothetical `profiles/foo/`)
  fails CI on Cypher drift until the schema is updated, exactly
  the way it now fails for postgres / sqlite / duckdb.
- This issue header gets `closed_by: <commit-sha>` and a closing
  note naming which safeguard (A or B) was adopted.

## Worked counter-example

If Safeguard B had existed before the disclosure profile was
added, the disclosure commit would have failed CI on `cypher
drift` until the schema was regenerated, blocking the merge. The
profile would have shipped with all four reference engines at
parity, not three.
