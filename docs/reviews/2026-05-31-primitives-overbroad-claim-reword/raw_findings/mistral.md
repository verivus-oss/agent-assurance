# Review Findings — 2026-05-31 primitives overbroad claim reword

## Per-item verdicts

### 1. Accuracy / does it fix the overbreadth?
**Verdict: PASS**
- primitives.md:7 NEW scoped claim to "business reality that IJB projects — what exists and what was observed" matches corpus: faq.md:7-9 "projects facts into space without interpretation", faq.md:13-15 "refuses to abstract", core-specification.md:9-15 "You are not visualizing the business... projecting the same description".
- README.md:14 NEW "observable facts about what exists, how it moves, and what was witnessed" is consistent with primitives.md:7 and core-specification.md:21-27 (factual substrate).

### 2. Over-correction?
**Verdict: PASS**
- No hedging introduced. "what exists and what was observed" / "observable facts" are plain-spoken, anti-abstraction, brand-consistent with why-this-matters.md and faq.md:13-15.

### 3. Accuracy of the new bounding clause
**Verdict: PASS**
- primitives.md:7: "IJB describes facts, not intent, causality, interpretation, or hypothetical futures" matches canonical-assertion-grammar.md:18-19 Non-Goals "Encode intent, causality, or interpretation. Model full FCO-IM metaconcepts." Cross-reference is correct and resolvable.
- README.md:14: "observable facts about what exists, how it moves, and what was witnessed" aligns with faq.md:66-84 (disclaims strategy, future state, hypotheticals, uncertainty).

### 3a. Em-dash/semicolon punctuation vs hyphen
**Verdict: PASS**
- primitives.md:7 OLD used " - " (hyphen with spaces); NEW uses " — " (em-dash with spaces) and ";" before "IJB describes facts". Em-dash is stronger, matches README.md style, and semicolon correctly joins independent clauses. Consistent with document style.

### 4. Parallelism & completeness
**Verdict: PASS**
- primitives.md:7 and README.md:14 are now consistent and parallel.
- No other occurrences of the overbroad claim found in normative `foundations/ijb/` or `core/` files. Remaining matches are in review/research docs (non-normative).

### 5. No semantic/normative change
**Verdict: PASS**
- Only prose in `foundations/ijb/primitives.md` and `foundations/ijb/README.md` touched. No primitives added/removed/renamed. No grammar, ontology, validator, or *-kind.toml changes. No closure_root/sha. Purely textual scoping.

---

## Findings list

| file:line | severity | issue |
|---|---|---|
| foundations/ijb/primitives.md:7 | NONE | Reword accurately scopes claim to IJB-projected facts; bounding clause matches canonical-assertion-grammar.md:18-19 Non-Goals |
| foundations/ijb/README.md:14 | NONE | Reword consistent with primitives.md:7; "observable facts" matches corpus |
| foundations/ijb/primitives.md:7 | minor | "what was observed" vs README.md:14 "what was witnessed" — trivial synonym variance, no semantic drift |

---

## Terminal recommendation

**approve**

The reword precisely scopes the overbroad claim to IJB's declared territory (projectable/observed facts), matches all corpus references, preserves the anti-abstraction brand, and touches only non-normative prose with no functional change.
