**Critique Report: Opus consultant proposal for `MANIFEST.toml [counts].attribute_values` (HEAD 99e18dba38ec3b4c6234b77bac7a87b0f2e6cdfc)**

### 1. Verification of the Opus report's evidence

- **8-surface mirror table (Opus §2)**: **Partially confirmed, with material errors and omissions.**
  Cited mirror locations + numbers all match the files. The "stale" bolding is directionally correct.
  **However**:
  (a) The "Actual seed file row counts" column for attribute_value_allowed (**74, 109, 109**) is **refuted** — all three seeds contain exactly **106** text rows today (re-counted via INSERT/INSERT-block tuple regex).
  (b) Missed surfaces: `duckdb/seed.sql:5` header has "Counts (verified at load): 19/26/30/37/81" (verbatim stale duplicate of hardcodes); `sqlite/seed.sql:11-14` has its own stale block. Postgres top comments now match [counts] for blocks but not values.
  (c) template_kinds "actual" 20 in Opus table relies on the synthetic +1 in check_manifest_drift.sh:62 (only 19 *-kind.toml files exist on disk: 6+9+3+1).

- **Historical `81 → 84 → 106 → 170` claim**: **CONFIRMED** via `git log -p -- reference/database/MANIFEST.toml | grep attribute_values`. Exact deltas appear in that order.

- **"106 ≈ today's sqlite/duckdb seed-row count (109)"**: **Directionally confirmed, numerically imprecise.** Current seeds are uniformly 106. The qualitative "historical tracked seed rows" reading holds; the specific 109 figure does not appear in current seeds or git blame at HEAD.

- **"actual seed file row counts 74, 109, 109"**: **REFUTED_WITH_EVIDENCE**. All engines emit 106 tuples in their text `attribute_value_allowed` blocks. Postgres is *not* lower for these text rows.

- **Two arithmetic errors alleged in structural-analysis.md §2**: **CONFIRMED** (independently re-derived):
  - core: blocks=10, values=39, closed=22 (analysis said `(9, ~24, 22)`)
  - agent-assurance: blocks=24, values=91, closed=51 (analysis said `(24, ~108, 51)`)
  Per-row wrong, totals (41/170/99) accidentally survived.

All other Opus §1 micro-claims (drift script ignores the field, zero consumers, identical extensible semantics) confirmed.

### 2. Critique of the recommendation

**§4.1 MANIFEST split**: Correct in intent and mechanics. The categorical distinction is real and was the source of the 170/99/106 confusion. Field names `_declared` / `_closed` are defensible. No third name for "seed-row-count" belongs in `[counts]` — that figure is an *engine modeling artifact* and lives properly under the per-`[verification.*]` `expected_seed_counts` tables.

**§4.2 Validator**: Correct and minimal. Will catch future `values=[...]` edits that don't bump the manifest. Does not address the other 7+ mirror surfaces (by design per 4.6).

**§4.3 Wire-in**: Correct and follows the existing pattern.

**§4.4 SPEC §10 paragraph**: **Incorrect — clearest overclaim.**
- `grep -n attribute_values SPEC.md` returns zero today.
- MANIFEST:8-10 explicitly: "This file is NOT a DAG-TOML kind ... normative = false".
- Adding a "MUST distinguish ... Mixing is prohibited" rule to the normative SPEC creates a category error. The rule is project-internal documentation discipline, not a constraint on DAG-TOML authors / runtimes.
- Natural home: expanded MANIFEST.toml comment block at lines 30-38, or reference/database/README.md.

**Self-concerns Opus listed (§5)**: mostly the right ones, but missed (a) the seed.sql header comments as additional rot surfaces, (b) the synthetic +1 meta kind-descriptor hack that already makes template_kinds=20 slightly non-obvious, (c) the per-engine `expected_seed_counts.*.attribute_value_allowed` (79/54) being *semantically different* from any ontology-derived number (post-enum-promotion text-row counts).

**PR-scoping (§4.6)**: honest for the *narrow* question that blocked the two reviewers, but can-kicking for the root cause Opus himself diagnosed in §3 (the mirror pattern itself). Minimum honest PR would add assertions that the three `expected_seed_counts` blocks match row counts actually present in their corresponding seed.sql files.

### 3. What you would do differently

I would **modify** the Opus recommendation with two concrete changes and one addition:

1. **Drop §4.4 entirely** (no SPEC.md edit). Replace with a tighter comment block update inside MANIFEST.toml:30-38 documenting the two new fields + derivation recipe, stating that the only authoritative numbers for the ontology surface live in [counts] and are CI-gated, and cross-referencing the per-verification.* sections for engine-specific emission counts.

2. **Improve the validator** (one extra line): after computing declared/closed, emit the current text-row emission count (106) as diagnostic output labelled "attribute_value_allowed_text_rows (all engines, current seeds)". Three-way distinction (170 declared / 99 closed / 106 emitted) visible in CI without adding a third persisted field.

3. **Expand follow-up scope** (in PR description or new 4.7 bullet): the three seed.sql header comments must be deleted or turned into generated content in the same follow-up that touches the hardcodes. They are the most misleading on-disk copies.

Rest of Opus (the split, exact validator, wire-in, names, decision to keep both numbers) is correct.

### 4. Decision matrix

| Option | What it buys | What it costs | Residual risk |
|--------|--------------|---------------|---------------|
| **Opus (E) as written** | Resolves 170-vs-99 deadlock; producer-side gate; value-vs-block asymmetry visible; both numbers documented. | ~35-line Python file; two new TOML keys; SPEC edit reaching outside spec's stated scope. | Other 7+ mirror surfaces remain silently stale. |
| **Modified (E')** (drop SPEC, expand MANIFEST comment, +diagnostic line, call out seed headers in follow-up) | Same immediate win + stricter scoping hygiene; avoids polluting normative SPEC. | Same cost; slightly more comment text. | Same broader-rot risk (now explicitly flagged). |
| **(A) Set to 170 + gate only that** | Simple. | Re-ignites reviewer fight on next ticket; hides the 99 enforcement surface. | Future "why 170 when only 99 enforced?" questions. |
| **(D) Delete the field** | Removes ambiguity; no new names to bikeshed. | Loses documented size of ontology starter-value surface. | Anyone who wants it computes by hand. |
| **Full mirror cleanup in one PR** | Closes entire brittleness gap in one visible change. | Larger diff; updates to all three expected_seed_counts; tool changes. | Scope creep / pushback on "why are we touching seeds?". |

### 5. Bottom line

I would **modify** the Opus recommendation (drop the SPEC §10 paragraph, keep the split+validator+wire-in, add the seed-header call-out to the follow-up scope); the maintainer should apply the MANIFEST edit, the new `validators/check_attribute_values.py`, and the `check_manifest_drift.sh` append exactly as Opus wrote them in §4.1-4.3, expand the MANIFEST.toml comment block in place of §4.4, and treat the broader mirror-rot items (including the three seed.sql headers) as an immediate follow-up on the same branch rather than a vague later PR.
