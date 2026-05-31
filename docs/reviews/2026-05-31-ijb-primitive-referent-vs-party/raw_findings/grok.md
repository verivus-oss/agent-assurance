# IJB Primitive #1 Decision Review — Grok (fresh-context independent)

**Date**: 2026-05-31 (review execution)  
**Session**: docs/reviews/2026-05-31-ijb-primitive-referent-vs-party/  
**Role**: Fresh-context independent reviewer per review_prompt.md (adjudicate `referent` challenger vs `party` standing recommendation for first IJB primitive: "the thing an assertion is about").  
**Evidence protocol**: sqry semantic_search (symbols first) + literal grep -w exact-token scans (re-ran all collision baselines myself; never trusted initiator numbers or summaries). Full read of both proposals (06-drafts-for-party.md, 07-drafts-for-referent.md), prior 00-05, and all mandated ground-truth bytes in upstream /srv/repos/external/verivus-oss/agent-assurance/ (primitives.md §1, canonical-assertion-grammar.md replay templates, why-this-matters.md brand text, spec.md §10 tables, enterprise.toml, validate_ijb_conformance.py + validate_kind_descriptor.py, core/profile ontologies, AGENTS.md). 04/05 upstream citations re-confirmed for drift. Standard slopscan (tools/README.md#standard-slopscan discipline applied to factual claims): no hallucinated paths, no invented legal/lexical facts in either draft. Every finding cites file:line + severity.

**Ground-truth files inspected** (per review_bundle.toml:35-40 + prompt):  
- foundations/ijb/primitives.md (§1 existence definition)  
- foundations/ijb/canonical-assertion-grammar.md (replay + "dereference referenced assertion IDs")  
- foundations/ijb/why-this-matters.md (brand)  
- profiles/agent-assurance/tiers/enterprise.toml (party usage)  
- validators/validate_ijb_conformance.py + validate_kind_descriptor.py (ijb_primitive surface + check_references)  
- spec.md §10 (normative mapping tables)  
- core/ontology.toml + profiles/*/ontology.toml (current `thing` pins)  
- tools/review-request-dag.toml (policy dispatch)  
- AGENTS.md (IJB conformance rules)

---

## Per-axis verdicts (1–6)

**1. Official meaning of primitive #1** (file:line evidence):  
primitives.md:11-13 ("### 1. Things **What they are:** Objects that exist"; "Key principle: Visual form indicates existence, not importance or authority."); canonical-assertion-grammar.md:98-101 ("Structural Thing <id> exists.", "Thing <thing> exists within Scope <within>."); spec.md:631 ("[[entities]] ... `thing` `structural`"), 654 ("[kind] ... `thing`"), 665 ("Entity declarations ... `thing` `instance`"); grammar:52-54 (thing-call ABNF), 32 ("Replay must dereference referenced assertion IDs"). #1 is the **existence** primitive ("objects that exist"). `referent` (07-drafts-for-referent.md:34 citing WordNet sense 2: "the first term in a proposition; the term to which other terms relate"; 07:113-116 calls it a "deliberate definitional shift" from existence-first to reference-first) is a **category-error reframe** of the same shape that sank `matter` (topic/case drift + proceedings idiom). It changes the anchor from visual/existence fact to "thing the assertion refers to." 07 draft itself flags the rewrite of primitives.md §1 as required. `party` (06) preserves the existence reading with only softening, no reframe. Verdict: **party**

**2. Internal collision** (re-ran myself; sqry first then grep -w):  
`referent` 0 / `referents` 0 structural (grep -w outside docs/reviews/2026-05-31-ijb-primitive-referent-vs-party/ + style policy: only 4 English uses in tools/werner-style-policy.toml:277,330,332,607 as "the thing referred to"; 0 as schema term). `reference` family **saturated**: 725 `\breference\b`, 345 `\breferences\b`, 117 `\breferenced\b` (across 238/177/75 files). Core surfaces: validators/validate_kind_descriptor.py:185 (def check_references + --check-references-exist mode + kind.references/hard_invariants.enforced_by paths), canonical-assertion-grammar.md:32 ("dereference **referenced** assertion IDs"), reference/database/ (dirs + schemas), spec.md cross-refs (21+), AGENTS.md:3, etc. Proximity confusion ("the referent" vs "the reference" / "dereference the referent ID") is live in code, prose, conversation — exactly the "strongest argument against `referent`" per prompt:52-57. `party` 95 hits (excl current review dir): all ordinary English or "third-party" (e.g. enterprise.toml:63 "third-party re-derivation party"; core/traceability-kind.toml:81 example "DEC:tax-engine-third-party"; disclosure/ontology.toml:95 redaction_reason value "third-party"; profiles/*/PROFILE.toml comments; no schema role as primitive; no [[parties]]). Verdict: **party** (major — disqualifying proximity)

**3. Legal / regulatory risk**:  
Neither is GDPR-style hard blocker (confirmed: spec.md, ontologies, validators contain zero "data subject" primitive language; "third party" only as redaction_reason vocab value + ordinary prose). `party` loaded surfaces (per 05:27-29 + 06 §3): GDPR Art.4(10) "third party", EU SCCs "the Parties", NIST SP 800-63C "relying party" / "authorized party", contract "parties" / "third-party re-derivation party" (enterprise.toml:63). `referent`: pure semiotics term of art (07:28-43 cites M-W/OED/WordNet/Ogden&Richards 1923); zero legal TOA in GDPR/contract/agency/securities/data-protection per 07:214-218. Relative audit-misinterpretation exposure **higher for `party`** in regulated contexts (agent-assurance target). 07 correctly scores this axis for referent. Verdict: **referent**

**4. Brand / tone**:  
IJB brand: "Resistance to abstraction" (why-this-matters.md:61), "plain-spoken, grounded, professional but not elevated, anti-abstraction" (AGENTS.md:29-31, spec.md:575-589 IJB substrate, 03-deeper-side-by-side.md:22-23). `referent` dominant modern sense **academic/semiotics** (07:28-43) — exact failure mode that eliminated `subject` ("philosophy word" per eliminated list in prompt:32 and 01/02 reviews). `party` is plain business English (lawyers/auditors/HR register per 06:27, 05:14-17) with participation baggage (acknowledged). Brand "plain-spoken" (why-this-matters.md:61) weights heavily against academic term for foundational primitive. Verdict: **party** (major)

**5. Replay & ergonomics**:  
Both drafts adopt **identical softening** (06 §2: "Do not use the primitive noun literally in high-frequency replay output"; 07 §2: same strategy + "human-facing replay is **identical**"). Templates: "Priya-Nair exists within Scope Corporate-Operations." (no noun). Human replay identical; noun only for rare formal prose. Differences are mechanical: grammar keys (`party=` vs `referent=` in scope(thing=..., per canonical-assertion-grammar.md:58), potential [[parties]]/[[referents]] sections, error classes (future NoSuchPartyError vs NoSuchReferentError), and the existence-vs-reference reframe itself. Current grammar still hardcodes "thing(" (52) + "Thing ... exists" (98). 07:159-164 notes referent symmetry (equal for people/artifacts); 06:35-36 notes party natural for people, strained for artifacts. Softening mutes replay objection; ergonomics **tie** (implementation delta identical). Verdict: **tie**

**6. Directional ambiguity (referent-specific)**:  
07:28 quotes M-W headword: "one that refers **or** is referred to." 07 §3 pins IJB to passive only ("the assertion refers; the referent is referred to"; 07:201-204). Dictionary gloss is bidirectional ("X or its converse"). This is a **precision liability** in a precision-first framework (IJB six-primitive discipline, primitives.md, spec.md §10). `party` has no built-in converse ambiguity. Even with SPEC §10.6 pinning, the English word carries the "or." Verdict: **party**

---

## Findings list (file:line, severity, candidate)

- canonical-assertion-grammar.md:32 ("Replay must dereference **referenced** assertion IDs") + validators/validate_kind_descriptor.py:185 (def check_references, --check-references-exist, kind.references validation) + 725 `\breference\b` / 345 `\breferences\b` / 117 `\breferenced\b` hits: **major against referent** (proximity confusion in core enforcement surface)
- primitives.md:13 ("Objects that exist") + "Visual form indicates existence, not importance or authority" + canonical-assertion-grammar.md:98-101 ("Thing <id> exists") + spec.md:631/654/665 (all `thing` pins for entities/kinds/instances): **major against referent** (existence-primitive reframe is category shift)
- why-this-matters.md:61 ("Resistance to abstraction") + spec.md:575-589 (IJB plain substrate): **major against referent** (academic semiotics tone)
- 07-drafts-for-referent.md:115-116 (explicitly "deliberate definitional shift" from existence to reference framing + "This is the single change that makes this a SPEC-level decision"): **minor against referent** (overstates seamlessness of reframe)
- 05-codex-party-vs-matter-full.md:12 (cites PRIMITIVES.md:11 — actual file is lowercase primitives.md on Linux FS; line 97 vs actual grammar replay at 98): **minor process note** (drift; core claim accurate)
- enterprise.toml:63 ("third-party re-derivation party") + core/traceability-kind.toml:81 (example ID "DEC:tax-engine-third-party") + disclosure/ontology.toml:95 (redaction_reason "third-party"): **minor against party** (awkward ordinary English; no schema role)
- tools/werner-style-policy.toml:277/330/332/607 (pre-existing English "referent" = "the thing referred to" in style rules + verified_by labels): **neutral** (unrelated to primitive; 07 draft correctly disambiguates)
- All paths cited in 06-drafts-for-party.md and 07-drafts-for-referent.md resolve (primitives.md, canonical-assertion-grammar.md, validate_ijb_conformance.py:154, enterprise.toml:60, review-request-dag.toml, spec.md §10 etc.): **clean** (no hallucinated files)
- 04-claude-party-vs-matter-full.md:10/16/126 (explicitly notes agent-assurance sources absent from its context; cites only 01/03): **minor process note** (04 did not inspect bytes directly; 05/07 citations mostly resolve with minor variance)
- review_bundle.toml:52-63 baseline (referent/referents=0 pre-review) + sqry/grep re-runs: **confirmed** (0 structural outside review/ + style policy)
- No invented legal facts (GDPR/SCCs/NIST citations in 05/06/07 match standard public sources; no hard-blocker claims): **clean**
- No "[[parties]]" or "[[referents]]" or ijb_primitive="party|referent" in any ontology/kind/example (all still "thing"): **clean** (decision not yet ported)

---

## Terminal recommendation

**adopt_party**

(The concrete reason `referent`'s cost is disqualifying: proximity collision with the saturated `reference` family (725+ hits with direct enforcement surface at validate_kind_descriptor.py:185 and canonical-assertion-grammar.md:32 "dereference referenced assertion IDs") plus academic semiotics tone (violating why-this-matters.md:61 "Resistance to abstraction" brand and the plain-spoken discipline that eliminated `subject`) outweigh the legal-exposure edge on axis 3; the existence-to-reference reframe (primitives.md:13 vs 07:113-116) introduces unnecessary conceptual drift for the foundational existence primitive already pinned in spec.md §10.2 tables.)

---

## The decisive factor

The saturated `reference`/`referenced`/`dereference` family (725 "reference", 345 "references", 117 "referenced" incl. core validator `check_references` at validate_kind_descriptor.py:185 and grammar "dereference referenced assertion IDs" at canonical-assertion-grammar.md:32) plus `referent`'s academic semiotics register make it a precision and brand liability for IJB's first primitive in a plain-spoken, anti-abstraction substrate (why-this-matters.md:61); `party`'s ordinary-English surface carries no schema role today and is the lower-risk continuation of the existence reading already normative in primitives.md §1 and spec.md §10.2.

---

**Process attestation**: All claims above derive from direct byte inspection (sqry semantic_search on symbols first for ijb_primitive / reference surfaces, then grep -w exact tokens for whole-repo counts excluding the active review dir; full reads of every mandated file and both drafts; path existence + line verification for 04/05 citations; slopscan for hallucinated paths/facts in 06/07). Initiator summaries in 00-07 were **never** treated as evidence. Minor drift in 04/05 citations noted but does not alter substantive findings. No concrete_unresolvable_blocker (both candidates are viable; choice is trade-off on inspected bytes).

**Output location**: This file written verbatim to raw_findings/grok.md per review_prompt.md:90.