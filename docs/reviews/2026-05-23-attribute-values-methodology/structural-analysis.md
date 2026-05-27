# Structural-semantic analysis — `[counts].attribute_values`

Generated against HEAD `99e18dba38ec3b4c6234b77bac7a87b0f2e6cdfc`,
sqry index rebuilt 2026-05-22T23:48Z (46 files, 7,393 nodes,
8,783 edges).

This document anchors the methodology-convergence decision. The two
agents agree on data-acquisition method and tooling shape; they
differ on whether to filter by `extensible`. The structural evidence
below resolves *what the field can possibly mean* by showing what
the rest of the system actually does with `extensible` and with
`[counts].attribute_values`.

---

## 1. The field in question

**`reference/database/MANIFEST.toml:37`** (current head):

```toml
attribute_values       = 170   # union across all attribute-vocabulary
                               # allowed values (BOTH closed and
                               # extensible) summed across core +
                               # agent-assurance + disclosure + cost
                               # ontologies. [...]
```

Sibling fields on the same `[counts]` table (lines 33–36):

```toml
template_kinds         = 20
entity_kinds           = 27
relation_predicates    = 31
attribute_vocabularies = 41
```

CI-gated by `validators/check_manifest_drift.sh`:
**lines 33–36 yes, line 37 no.** (`grep -n attribute_val
validators/check_manifest_drift.sh` shows only
`attribute_vocabularies` is in the script's block-count loop;
`attribute_values` is never read.)

---

## 2. The closed-vs-extensible declaration model

**`core/ontology.toml:644–645`** (the authoritative semantic):

```toml
attribute_vocabularies_default = "see_each_entry_extensible_field"
extensible_attributes = ["requirement_kind", "test_kind"]
```

Each `[[attribute_vocabularies]]` block in any ontology MUST
carry an `extensible = true|false` field; that field is the
per-vocabulary declaration of whether the value set is closed
or open. Counts at HEAD (independently derived from
`tomllib.loads(...)`):

| Ontology | `[[attribute_vocabularies]]` blocks | sum of `len(values)` | of which `extensible=false` |
|---|---:|---:|---:|
| `core/ontology.toml` | 9 | ~24 | 22 |
| `profiles/agent-assurance/ontology.toml` | 24 | ~108 | 51 |
| `profiles/disclosure/ontology.toml` | 4 | 18 | 4 |
| `profiles/cost/ontology.toml` | 3 | 22 | 22 |
| **Total** | **41** | **170** | **99** |

(`attribute_vocabularies = 41` matches the MANIFEST line 36;
**both 170 and 99 are correct counts under different
filters**.)

---

## 3. Code that consumes `extensible` (the structural evidence)

Two validators branch on `extensible` to gate membership
enforcement. Both have **identical semantics**: extensible-true
vocabularies accept any value; extensible-false vocabularies
reject unseen values.

### 3.1 `tools/dagtoml-validate-rs/src/main.rs:520–542`

```rust
fn check_vocab(
    attribute: &str,
    value: Option<&str>,
    vocabs: &BTreeMap<String, (Vec<String>, bool)>,
    location: &str,
) -> Vec<String> {
    let Some((values, extensible)) = vocabs.get(attribute) else {
        return vec![format!(
            "{}: ontology missing attribute_vocabulary `{}` (cannot enforce closure)",
            location, attribute
        )];
    };
    let Some(v) = value else {
        return vec![format!("{}: `{}` must be a string", location, attribute)];
    };
    if values.iter().any(|x| x == v) {
        return Vec::new();
    }
    if *extensible {                                           // <-- THE GATE
        return Vec::new();
    }
    vec![format!(
        "{}: `{} = \"{}\"` is not in the closed vocabulary {:?}",
        location, attribute, v, values
    )]
}
```

### 3.2 `validators/validate_disclosure.py:85–106`

```python
def _check_vocab(attribute, value, vocabs, location):
    spec = vocabs.get(attribute)
    if spec is None:
        return [f"{location}: ontology missing attribute_vocabulary "
                f"`{attribute}` (cannot enforce closure)"]
    if not isinstance(value, str):
        return [f"{location}: `{attribute}` must be a string"]
    if value in spec["values"]:
        return []
    if spec["extensible"]:                                      # <-- THE GATE
        # extensible vocabularies accept new values silently — SPEC layer
        # only enforces shape (string), not membership.
        return []
    return [
        f"{location}: `{attribute} = \"{value}\"` is not in the closed "
        f"vocabulary {spec['values']}"
    ]
```

### 3.3 Diagram — the enforcement substrate

```
                  ontology file
        ┌─────────────────────────────────────────┐
        │ [[attribute_vocabularies]]              │
        │ attribute  = "decider_class"            │
        │ values     = ["llm_consensus", ...]     │
        │ extensible = false   ◄─── per-vocab tag │
        └────────────────────┬────────────────────┘
                             │
                             ▼
        ┌─────────────────────────────────────────┐
        │ load_vocabs() — same shape both langs   │
        │   Rust : (Vec<String>, bool)            │
        │   Python: {"values": [...], "ext": bool}│
        └────────────────────┬────────────────────┘
                             │
                             ▼
        ┌─────────────────────────────────────────┐
        │ check_vocab(attribute, value)           │
        │                                         │
        │ value ∈ values  →  PASS                 │
        │ value ∉ values  →                       │
        │     extensible = true   →  PASS  ◄─── 71 extensible value slots silently widened
        │     extensible = false  →  REJECT◄─── 99 closed value slots actually enforced
        └─────────────────────────────────────────┘
```

**Implication:** of the 170 declared values, only **99 are part
of the enforceable closure surface**. The other 71 are starter
lists / catalog entries that the validator passes through
unchanged.

---

## 4. Code that consumes `[counts].attribute_values`

`grep -rn 'attribute_values' validators/ tools/ --include='*.py'
--include='*.rs' --include='*.go' --include='*.sh'` (run at HEAD):

```
(zero matches)
```

**Zero consumers.** Nothing in the validator suite, the Rust /
Go primary validators, the reference-DB tooling, or the drift
script reads `[counts].attribute_values`. The closest neighbours
are:

- `validators/check_manifest_drift.sh:47–85` — reads
  `attribute_vocabularies` (line 36 of MANIFEST), **not**
  `attribute_values`.
- `tools/dagtoml-duckdb/src/main.rs:21–27` — has a hardcoded
  `EXPECTED_COUNTS` table that mirrors `[counts]` by name
  (`kind_descriptor`, `entity_kind_descriptor`,
  `relation_descriptor`, `attribute_vocabulary`,
  `attribute_value_allowed`) but **does not include
  `attribute_values`** and is itself stale at HEAD
  (kind_descriptor = 19, real value 20).
- `tools/dagtoml-duckdb-go/main.go:36–45` — same stale mirror.

```
        ┌─────────────────────────────────────────────┐
        │  reference/database/MANIFEST.toml [counts]  │
        ├─────────────────────────────────────────────┤
        │ template_kinds = 20         ◄── line 33     │
        │ entity_kinds = 27           ◄── line 34     │
        │ relation_predicates = 31    ◄── line 35     │
        │ attribute_vocabularies = 41 ◄── line 36     │
        │ attribute_values = 170      ◄── line 37     │
        └────────────┬────────────────────────────────┘
                     │
                     │ (read by)
                     ▼
        ┌─────────────────────────────────────────────┐
        │ validators/check_manifest_drift.sh          │
        │   line 47: TOTAL_VOCABS = block-count       │
        │            for attribute_vocabularies       │
        │   line 67: M_VOCABS = manifest_count        │
        │            attribute_vocabularies           │
        │   line 85: report attribute_vocabularies    │
        │                                             │
        │   (attribute_values: NEVER READ)            │
        └─────────────────────────────────────────────┘
                     ▲
                     │ (mirror, stale, by-name only)
                     │
        ┌────────────┴────────────────────────────────┐
        │ tools/dagtoml-duckdb/src/main.rs:21         │
        │ tools/dagtoml-duckdb-go/main.go:40          │
        │   const EXPECTED_COUNTS = [                 │
        │       kind_descriptor=19,    (stale, real=20)
        │       entity_kind_descriptor=26, (stale, real=27)
        │       relation_descriptor=30,(stale, real=31)
        │       attribute_vocabulary=37,(stale, real=41)
        │       attribute_value_allowed=81,            │
        │       — note: NOT attribute_values, a       │
        │       — DIFFERENT field name (seed rows)    │
        │   ]                                          │
        └─────────────────────────────────────────────┘
```

---

## 5. Semantic map — what `attribute_values` CAN mean

| Interpretation | Number at HEAD | Code that consumes this number | Other interpretations |
|---|---:|---|---|
| (A) All declared values (closed + extensible starter lists) | **170** | none | "documented catalog size" |
| (B) Enforceable closure (extensible = false only) | **99** | none directly; matches the rejection-surface the validators in §3 actually enforce | "enforceable enum surface" |
| (D) Delete the field | n/a | n/a; no consumer exists today | "unused metric" |

**No code reads this field.** The only constraint on its value is
human-readable documentation. The choice between (A), (B), and (D)
is therefore a documentation-intent decision, not a code-correctness
decision.

If the spec maintainer were to add a future consumer:

- A consumer asking "how many tokens of closure does the validator
  enforce?" wants (B) = 99 (matches §3 rejection surface 1:1).
- A consumer asking "what is the documented surface area of the
  spec's attribute-value space?" wants (A) = 170 (matches the
  ontology-as-published surface).
- A consumer asking "how many distinct attribute-value bindings ship
  in the reference databases?" wants neither — it wants
  `expected_seed_counts.attribute_value_allowed`, which is a third
  number (currently stale per Codex finding F-001).

---

## 6. The reviewers' positions, anchored to §3 and §4

- **Reviewer A (grok) → (A) = 170.** Argues from symmetry: the
  other four `[counts]` fields count declarations without filtering,
  so should this one. Field has no enforcement consumer (§4 confirms
  this), so the "declaration count" interpretation is the lower-risk
  default. Comment at MANIFEST:37 already encodes this reading.

- **Reviewer B (codex) → (B) = 99.** Argues from the enforcement
  substrate: §3 shows that only `extensible = false` values are
  actually rejected by validators. The remaining 71 values are not
  enforced; counting them inflates a number whose only plausible
  future consumer would be an enforcement-surface metric.

**Both positions are internally consistent.** The disagreement is
on whether the field describes *declared ontology surface* (A) or
*enforceable closure* (B). The structural evidence in §3 is the
canonical signal for B; the structural evidence in §4 (zero
consumers) is the canonical signal for D.

---

## 7. Recommendation framing

Given:

- §4 shows there is no current consumer.
- §3 shows the only `extensible`-discriminating logic in the
  codebase treats `extensible=false` as "the enforceable subset".
- The MANIFEST comment at :37 currently asserts (A) but was
  written without acknowledging §3.

The choice is between three honest positions, each with a clear
mechanical recipe:

1. **Adopt (A) + relabel the field's intent as "documented
   declaration surface".** Set 170, keep the comment as is, add the
   Python validator both agents recommended. Trade-off: the number
   is symmetric with the rest of `[counts]` but does not
   correspond to any code behaviour.

2. **Adopt (B) + rename the field to `closed_attribute_values` or
   add a `attribute_values_closed` companion.** Set 99, add a
   one-line SPEC reference at §10.4 ("the closed-surface size is
   used by …"), add the Python validator with an `extensible=false`
   filter. Trade-off: requires breaking the symmetry, but the
   number then corresponds 1:1 with the enforcement rejection
   surface at `dagtoml-validate-rs:520–542` and
   `validate_disclosure.py:85–106`.

3. **Adopt (D) — delete the field.** No consumer exists; the
   `attribute_vocabularies` count at line 36 already documents the
   block count; the actual closure surface is recoverable from the
   ontology files on demand. The Python validator both agents
   recommended is still useful — but as a documentation tool, not a
   gate. Trade-off: drops a documentation crutch but removes the
   ambiguity entirely.

Each option is mechanically achievable from the present tree in
under 30 minutes of edits.
