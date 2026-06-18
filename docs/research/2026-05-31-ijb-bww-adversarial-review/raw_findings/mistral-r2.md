# Round-2 Re-Review: BWW Representational Analysis of IJB Six Primitives

**Reviewer:** Mistral Vibe  
**Date:** 2026-05-31  
**Task:** Re-adjudicate round-1 "not defensible" verdict against actual spec bytes with new context: (1) free-text deviation is intentional-by-design (`spec.md` §10.3 / 677-712), (2) grok's category-error rebuttal that BWW is wrong benchmark for a self-declared projection/observation substrate.  
**Method:** Byte-grounded verification against `/srv/repos/external/verivus-oss/agent-assurance/`.  

---

## Executive Re-Verdict

**REFRAMED.** The round-1 headline "absolute claim not defensible by BWW" was **correct for a modeling grammar**, but IJB **never claims to be a modeling grammar**. On its own declared terms — a projection/observation substrate that "refuses to abstract" (`faq.md:15`) — the six primitives are **complete-for-purpose**. BWW is a category error when applied without subtracting the explicitly-disclaimed territory. The free-text deviation is **intentional and classified**, not a defect. Net: **headline requires reframing from "not defensible" to "not defensible *as a modeling grammar*, but defensible *as a projection substrate*".**

---

## Answer to the Four Questions

### 1. Is BWW the right benchmark?

**No — grok's category-error charge is correct.**

IJB explicitly disclaims being a modeling grammar that represents full business and social phenomena. Evidence:
- `faq.md:7`: "This is a projection framework. Modeling implies interpretation and abstraction. This framework **projects facts into space without interpretation**."
- `faq.md:15`: "This framework has six primitives and **refuses to abstract**."
- `primitives.md:139`: "The descriptive layer is **queried, never drawn**."
- `canonical-assertion-grammar.md:19` Non-Goal: "**Model full FCO-IM metaconcepts**."
- `faq.md:66-70`: "How do I model uncertainty? **You do not model it**."
- `faq.md:72-74`: Future state, counterfactuals, strategy, causation — all explicitly **out of scope**.

BWW (Wand & Weber) was built to evaluate **modeling grammars** (ER, UML, BPMN, NIAM) that claim to represent the full range of business and social phenomena. Applying BWW to IJB **without first subtracting the explicitly-disclaimed territory mis-categorizes the artifact**. IJB's scope is **observation-only, interpretation-free, projection-only** — a fundamentally different category from the grammars BWW was designed to assess.

### 2. Does the binary-`path` n-ary deficit remain a flaw?

**No — it becomes an accepted scope boundary.**

Round-1 correctly identified that both `path-struct` and `path-inst` in `canonical-assertion-grammar.md:60-62` hardcode exactly one `from=` and one `to=` with no provision for n-ary participants or relation-instance attributes. However, this is **deliberate and within Non-Goals**:
- `canonical-assertion-grammar.md:60-62`: `path-struct = ... "from=" ref "," "to=" ref ...` and `path-inst = ... "from=" ref "," "to=" ref ...` — **strictly binary by grammar**.
- `canonical-assertion-grammar.md:19` Non-Goal: "**Model full FCO-IM metaconcepts**."

Since IJB explicitly disclaims modeling full FCO-IM metaconcepts, and since n-ary relations are a FCO-IM metaconcept, the binary-path limitation is **not a flaw but a deliberate scope boundary**. Within IJB's declared scope (projection of observed facts), binary paths are **sufficient and complete-for-purpose**.

### 3. Does the intentional free-text deviation change round-1 assessment?

**Yes — it changes from defect to accepted scope boundary.**

Round-1 flagged the free-text/prose deviation as the "real circumvention surface" / clarity defect. `spec.md` §10.3 (677-712) explicitly documents this as **intentional by design**:
- `spec.md:677-681`: "DAG-TOML **deviates from this restriction** [IJB's prose ban]. The format treats prose fields ... as **first-class entity content**. This is a **known and intentional deviation** because the DAG-TOML use case ... requires substantive explanatory prose."
- `spec.md:683-689`: **Default classification**: `ijb_primitive = "observed"` — prose treated as authored descriptive fact.
- `spec.md:691-696`: **Normative override**: where prose carries normative force, additionally tagged `ijb_primitive = "constraint"`, `ijb_constraint_type = "policy"`.

Since the deviation is **documented, intentional, and classified** with defined semantics, it is **not a defect** but an **accepted scope boundary** for the human+agent use case.

### 4. Revised verdict on the headline

**REFRAME.** The round-1 verdict "absolute claim not defensible" **does not survive** when measured against IJB's **actual declared scope**. However, it **does survive** when measured against the **category of modeling grammars** that BWW was designed to evaluate.

- **Within IJB's declared scope** (projection/observation substrate): The six primitives **are complete-for-purpose**. The binary path, the free-text classification, the rejection of abstraction — all are **deliberate design choices**, not failures.
- **Against the category of modeling grammars**: The six primitives **cannot represent** full business and social phenomena (n-ary relations, uncertainty, causation, strategy, etc.), and IJB **explicitly disclaims** this territory.

Therefore, the accurate verdict is: **"The absolute 'all business reality can be described with six primitives' claim is not defensible *as a modeling grammar* by the BWW standard, but it IS defensible *as a projection/observation substrate* within IJB's explicitly declared scope."**

This is not a concession to grok on rhetoric — it is a **byte-grounded recognition** that IJB's self-declared scope places it outside the category of artifacts BWW was designed to evaluate. Applying BWW without subtracting the disclaimed territory **is** a category error.

---

## Byte-Cited Rebuttal to Round-1 Self

Round-1's "not defensible" verdict was **conditional on treating IJB as a modeling grammar**. The spec bytes prove this premise false:

| Round-1 Assumption | Spec Reality | Citation |
|---|---|---|
| IJB claims to represent business reality | IJB **projects facts into space without interpretation** | `faq.md:7` |
| IJB abstracts | IJB **refuses to abstract** | `faq.md:15` |
| Descriptive layer is drawn | Descriptive layer is **queried, never drawn** | `primitives.md:139` |
| Full metaconcepts are in scope | **Non-Goal: Model full FCO-IM metaconcepts** | `canonical-assertion-grammar.md:19` |
| Free-text deviation is accidental | Deviation is **known and intentional** | `spec.md:677-679` |
| Free-text is unclassified | Default `ijb_primitive="observed"`, normative override `ijb_primitive="constraint"`+`policy` | `spec.md:683-696` |
| Binary path is a flaw | Binary path is **grammar-enforced** and FCO-IM metaconcepts are **Non-Goal** | `canonical-assertion-grammar.md:60-62,19` |

The single highest-confidence finding from round-1 — the binary-path n-ary deficit — **remains factually true** but **loses its normative force** because it is **within Non-Goals**. What was a flaw under one categorical framing becomes a boundary marker under the correct one.

---

## What This Means for BWW Analysis of IJB

1. **BWW is the wrong benchmark** for IJB in its declared scope. To apply BWW correctly, you must first **subtract** all explicitly disclaimed territory (abstraction, interpretation, causation, uncertainty, counterfactuals, strategy, full FCO-IM metaconcepts). What remains is so narrow that BWW's criteria no longer meaningfully apply.

2. **If you insist on applying BWW**, you must do so **honestly**: acknowledge that IJB **never claims** to be a modeling grammar, and therefore any BWW "deficiencies" are **category errors** rather than expressive failures. The six primitives are **complete for the scope they claim**.

3. **The free-text deviation** is not a circumvention surface or clarity defect. It is a **documented, classified design choice** that serves the human+agent use case. The classification scheme (`observed` default, `constraint`+`policy` override) preserves IJB conformance while accommodating prose.

4. **The binary path** is not a flaw. It is a **deliberate scope boundary** consistent with the Non-Goal of not modeling full FCO-IM metaconcepts.

---

## Final Verdict

**Headline: REFRAMED.**

> The absolute "all business reality can be described with six primitives" claim is **not defensible as a modeling grammar by the BWW standard**, but **is defensible as a projection/observation substrate within IJB's explicitly declared scope**.

**Reasoning:** IJB's founding documents repeatedly and explicitly disclaim being a modeling grammar (`faq.md:7,15`, `primitives.md:139`, `canonical-assertion-grammar.md:19`). It self-declares as a projection framework that "refuses to abstract" and "projects facts into space without interpretation." Applying BWW without subtracting the disclaimed territory mis-categorizes the artifact. Within its actual scope, the six primitives are complete-for-purpose, the binary path is an accepted boundary, and the free-text deviation is intentional and classified.

**Honesty check:** grok's category-error rebuttal **changes my mind**. The round-1 verdict was correct for the wrong category. The bytes force the reframing.
