# Research: Usability of the IJB Six-Primitive Model

> **STATUS: RESEARCH ONLY.** External-literature assessment of the IJB modeling
> approach. Not a decision, not a spec change, not normative. Findings are applied
> to IJB *by analogy* — no cited source evaluated IJB directly.

**Date**: 2026-05-31
**Method**: Exa deep-research harness — 6 search angles, 28 sources fetched, 131
falsifiable claims extracted, top 25 adversarially verified (3-vote; 2/3 refutes
kills a claim). 22 confirmed, 3 killed. 111 agents.
**Question**: Is IJB's claim that *all business reality* can be described with six
primitives (Things, Scopes, Paths, Observed, Constraints, Time) — facts queried then
projected into space, never drawn directly — a usable foundation? Assessed on
expressive adequacy, practitioner ergonomics, and prior art.

---

## Verdict

A usable **constrained core**, but the absolute "all business reality" claim is **not
defensible**. The ergonomic bet (minimal, prescriptive, low-ceremony) and the prior-art
lineage (fact-based / Object-Role Modeling) are sound. But by the Bunge-Wand-Weber
standard a fixed six-construct grammar is diagnosable for deficit/overload/redundancy/
excess; small physicalist primitive sets specifically break on social/institutional/
business constructs; binary `Paths` can't natively do n-ary relations or relation
attributes without reification; and deontic facts (obligation/permission/prohibition/
right) resist clean placement and risk overloading `Constraint`. Net: usable as a
deliberately minimal prescriptive core *with explicit projection separation*, but it
will systematically under-represent n-ary relations, relation-instance attributes,
deontic/normative facts, and social-construct semantics unless it adds reification
patterns and a domain-semantic layer — and forcing reduction to fixed primitives invites
workaround behavior when the model misfits real work.

> **⚠️ SUPERSEDED BY ROUND-2 MULTI-MODEL CONSENSUS (see end of doc).** This "not
> defensible" headline was upheld 2-1 in round-1 multi-model review, then **reframed
> 3-0** in a round-2 rebuttal once reviewers accounted for IJB's self-declared scope
> (projection/observation substrate, not a modeling grammar) and the intentional
> free-text design. The durable verdict is now: **not defensible *as a BWW modeling
> grammar*; defensible *as a projection substrate within IJB's declared scope*.** The
> binary-`path` deficit is real but reclassified from *flaw* to *accepted scope
> boundary*. See "ROUND-2 RESOLUTION" at the end.

## Confirmed findings (with verification vote + sources)

### Strengths

**Practitioner ergonomics favor the design** `[3-0]`
Enterprise tolerance for new modeling concepts is "very low"; simple, low-ceremony,
highly prescriptive approaches get adopted while high-formality general-purpose
languages (ADLs, heavy UML/MDE) see little uptake — "features requiring greater degrees
of formality end up being less frequently used."
- Woods & Bashroush, *JSS* 2015 — https://www.sciencedirect.com/science/article/abs/pii/S0164121214002052
- Shipman & Marshall, *CSCW* 1999 — https://ics.uci.edu/~corps/phaseii/ShipmanMarshall-FormalityConsideredHarmful-JCSCW.pdf

**Closest viable prior art = ORM / fact-based modeling, which also shows the fix** `[3-0]`
ORM "views the world in terms of objects playing roles; facts are assertions that objects
play roles. An n-ary fact has n roles." A small fixed fact-oriented primitive set
(objects, roles, facts, constraints) that is **natively n-ary** — the direct analogue
IJB should emulate to escape the binary-relation limit.
- Halpin, ORM white paper — https://www.orm.net/pdf/ORMwhitePaper.pdf
- https://link.springer.com/chapter/10.1007/978-3-540-72677-7_2 ; https://www.orm.net/pdf/EncDBS.pdf
- (Repo already references this lineage: `foundations/ijb/fco-im-integration.md`.)

### Weaknesses

**The "all business reality" claim must meet completeness AND clarity (BWW)** `[3-0]`
Wand & Weber (1993): a grammar is ontologically expressive only if it describes all
phenomena "completely and clearly"; four diagnosable defects — construct deficit
(incompleteness), overload, redundancy, excess (clarity). Applied historically to NIAM,
ER, UML, BPMN — so applying it to IJB's six primitives is in-domain.
- https://www.researchgate.net/publication/229741860_On_the_ontological_expressiveness_of_information_systems_analysis_and_design_grammars

**Minimality is not free** `[3-0]`
"If a grammar cannot represent some type of ontological construct… descriptions will be
deficient." Corroborated: perceived ontological deficiencies negatively associated with
usefulness/ease-of-use (Recker, Rosemann, Green & Indulska, *MISQ* 2011, n=528).
Qualifier: BPMN work (Recker et al., *EJIS* 2010) found not all predicted deficits become
critical — matching the "likely deficiencies" (probabilistic) framing.
- https://aisel.aisnet.org/cgi/viewcontent.cgi?article=1043&context=icis1990

**Small physicalist primitive sets break on business constructs** `[3-0]`
BWW "well-suited for… concrete things such as materials, but not for… social constructs,"
and the abstract primitives "do not lend themselves easily to a mapping of empirical
systems such as business organizations." Bluntly (SSRN assessment): Bunge's ontology "has
no place for human intentions… corporations… money… contracts… Lacking constructs for such
objects, [it] is an inappropriate foundation for conceptual modeling." **Central risk for
IJB applied to business reality.**
- Rosemann & Wyssusek, AMCIS 2005 — https://www.researchgate.net/publication/27482205_Enhancing_the_Expressiveness_of_the_Bunge-Wand-Weber_Ontology

**Generality-vs-power trade-off when patching with templates** `[2-1]` (weaker)
Adding domain templates "leads to static conceptual structures for rather narrow domains.
The universality… gets lost." Named independently as the Power/Generality Trade-Off
(Springer 2018; Frank, *BISE* 2014). Caveat: source authors think their own approach
partly escapes it, so "unavoidable" is slightly stronger than the source supports.
- https://link.springer.com/chapter/10.1007/978-3-319-91704-7_14 ; https://link.springer.com/article/10.1007/s12599-014-0350-4

**Binary `Paths` can't do n-ary relations / relation attributes without reification** `[3-0]`
W3C: a property "link[s] two individuals"; relations among >2 things, or attributes of a
relation instance (certainty, strength), require reifying the relation into a new class —
which "limit[s]… OWL constructs and create[s] a maintenance problem." IJB shares this with
RDF/triples unless it adds reification.
- https://www.w3.org/TR/swbp-n-aryRelations/

**Deontic facts resist `Constraint`** `[3-0]`
Obligation/permission/prohibition/right have "no settled place" even in mature BFO;
obligations can't be binary relations because "absolute obligations" bind an agent with no
specific second party. Collapsing them into `Constraint` risks **construct overload**.
- Donohue, "Toward a BFO-Based Deontic Ontology", CEUR Vol-2137 — https://ceur-ws.org/Vol-2137/ws_SoLe_paper_1.pdf

**The describe-then-project seam is exactly where users rebel** `[3-0]`
Aquanet: given a formal object/relation layer, users "circumvented the more powerful
knowledge representation mechanism" and encoded meaning spatially instead. Imposed,
misfitting formal systems get evaded (SAP "feral systems"; hacked-around MDE tools).
**Nuance: failure mode is "imposition + misfit → evasion," not "minimalism is doomed."**
- https://ics.uci.edu/~corps/phaseii/ShipmanMarshall-FormalityConsideredHarmful-JCSCW.pdf
- https://dl.acm.org/doi/10.1145/1985793.1985858 ; https://www.inderscience.com/info/inarticle.php?artid=10239 ; https://link.springer.com/article/10.1007/s12599-025-00943-5

## Refuted claims (killed by adversarial verification — do NOT cite as support)

- ❌ `[0-3]` "Fixed-structure modeling forces users to conform and is a root cause of failure." Overstated; evidence points to *misfit*, not *fixedness*. (dl.acm.org/10.1145/1985793.1985858)
- ❌ `[0-3]` "ORM is ergonomically superior to ER (natural language, populated diagrams)." Do **not** claim ORM is provably easier than ER. (orm.net white paper)
- ❌ `[1-2]` "Rights/obligations' transferability forces them into an information-entity category." Placement is genuinely unsettled. (CEUR Vol-2137)

## Caveats

No cited source evaluated IJB itself — the BWW/BFO diagnostics are applied by analogy
(legitimate as a *benchmark argument*, not a direct measurement). The ergonomics
generalization leans on a single industrial case study (Woods & Bashroush, n=1), mitigated
by corroborating UML/MDE/MBSE adoption surveys. The workaround literature establishes that
*imposed, misfitting* formal systems get evaded — not that minimal/anti-abstraction
modeling is inherently doomed. Theory areas are slow-moving (1993–2025); source age is not
a staleness concern.

## Open questions (carried into a follow-on research pass)

1. Does IJB's `Observed` + `Constraint` actually provide a reification mechanism for
   relation-instance attributes and n-ary relations (as ORM predicates / RDF reification
   do), or does it inherit the binary-`Path` limit with no remedy?
2. How does IJB represent deontic facts (obligations/permissions/prohibitions/rights) —
   collapsed into `Constraint`? If so, does that incur construct overload per W&W clarity?
3. Does the strict description/projection separation help or hurt adoption, given Aquanet
   found users preferred to encode meaning *in* the spatial layout?
4. **Has IJB ever been subjected to an actual Bunge-Wand-Weber representational analysis**
   (mapping each of the six primitives to ontological constructs to surface deficit/
   overload/redundancy/excess), and what do the spec's own kind-files reveal about
   identity/versioning, aggregation, modality, and counterfactuals?

**Follow-on run: COMPLETE — see the BWW representational analysis appended below.**

---

# Follow-on: A Bunge–Wand–Weber Representational Analysis of the IJB Six Primitives

> **STATUS: RESEARCH ONLY.** Byte-grounded analysis of IJB's own spec against the BWW
> framework. **Caveat on rigor:** the adversarial-verify pass did NOT run (the workflow's
> shared token pool was already past the 600k self-cap at launch, so the `nearCeiling()`
> guard skipped verification). The mappings below are an *analyst construction* with
> file:line citations the synthesizer read directly — they are NOT independently refuted.
> Run date 2026-05-31; 14 agents, 140 tool calls.

## Headline

**Has IJB ever had a BWW analysis? No — this is the first.** No formal BWW representational
analysis existed in the repo; the only prior artifacts are this doc (analogical/benchmark)
and `docs/research/2026-05-22-spec-foundations-research/01-exa-deep-researcher.md` §5
(comparative warning). The closed primitive set is confirmed: `IJB_PRIMITIVES =
("thing","scope","path","observed","constraint","time")` (`validators/validate_ijb_conformance.py:56`),
matching `foundations/ijb/primitives.md` and the "all business reality… six primitives"
claim (`primitives.md:7`).

**Result of doing it now:** only `thing→Thing` is a clean 1:1 BWW map. The set shows
construct **overload** (`thing` across Thing/Class/Property; `constraint` absorbing deontic
facts), **deficit** (n-ary relations, relation-instance attributes), **redundancy**
(`thing`-structural and `scope` both reach Class; `observed` and `thing` both carry
Property), and **excess** (`time` and `observed.by=` have no BWW substantial referent). The
absolute "all business reality" claim is **not defensible** by the BWW standard; the
engineered minimal core is.

## BWW representational mapping table

| IJB primitive | Maps to BWW construct(s) | Verdict | Evidence |
|---|---|---|---|
| `thing` | Thing + Class/Kind (`instance_of=`/`class=structural`) + Property (`identity=`) | **OVERLOAD (3-way)** | `primitives.md:11-13`; grammar `:53-54,:86,:115`; `spec.md:631,:665`; `core/ontology.toml:53,:108` |
| `scope` | Class/Kind (property-defined grouping) | clean-ish, **REDUNDANT** w/ `thing`-structural | `primitives.md:31-32,:44`; `spec.md:635-636`; grammar `:56-58` |
| `path` | struct → mutual property/coupling; inst → acts-on Event; `moves=` = cargo | **OVERLOAD + binary DEFICIT** | grammar `:61-62`; `primitives.md:51-54`; `core/ontology.toml:213-219` |
| `observed` | Event + History entry; `by=` has no BWW analogue | reasonable; `by=` is **EXCESS** | grammar `:68,:95,:107`; `primitives.md:71-72` |
| `constraint` | State law / lawful state space | reasonable but **OVERLOADED** (deontic) | grammar `:64,:104`; `primitives.md:88-89,:102` |
| `time` | none — ordering index of History | **EXCESS** | grammar `:66,:93,:119`; `primitives.md:107-108`; `spec.md:668` |

## The four deficiencies

- **Deficit (most consequential):** binary `path` can't express n-ary relations or
  relation-instance attributes; both `path-call` arms fix `from=`/`to=` with no participant
  or attribute slot (`canonical-assertion-grammar.md:61-62,:25`); no objectification construct.
- **Overload:** (a) `thing` = Thing + Class/Kind + Property; (b) `constraint` absorbs deontic
  facts (`primitives.md:88-102`; replay "restricts <target>" `grammar:104`) — a clarity defect.
- **Redundancy:** BWW Class via both structural `thing` and `scope`; BWW Property values
  via both `thing` attributes and `observed` (`spec.md:667`).
- **Excess:** `time` has no BWW substantial referent (and `spec.md:668` overloads it onto
  durations); `observed.by=` (observer) has no BWW analogue.

## The four open questions answered

1. **Reification / n-ary — NO remedy; binary `path` by design.** `path-call` is strictly
   two-endpoint, no attribute slot (`grammar:61-62`); `observed` carries only
   `{id,asserts,by,time,within}` (`:68`); uncertainty is declared out-of-model
   ("How do I model uncertainty? You do not model it." `faq.md:66-70`). The only
   reification-like capability is event-occurrence timestamping with a closed schema — not
   ORM/RDF relation-instance reification. Deliberate: Non-Goal "Model full FCO-IM
   metaconcepts" (`grammar:19`).
2. **Deontic — collapsed into `constraint`; genuine W&W overload.** No dedicated construct
   (`primitives.md:88-102`). The overload diagnosis stands; the *correct* deontic taxonomy is
   unsettled (the transferability→information-entity sub-claim was refuted `[1-2]` upstream).
3. **Projection separation — right architecture, documented risk seam.** "Queried, never
   drawn"; "multiple projections from same facts" (`primitives.md:139,:144`). Aquanet risk is
   concentrated where the core *misfits*; "fixedness is the root cause" was refuted `[0-3]`,
   so separation is not inherently harmful.
4. **Identity/versioning/aggregation/modality/counterfactuals.** Identity = a stated *method*
   (`identity=token`, `grammar:53-54`), not a versioned value. Aggregation = `scope` grouping,
   not mereology ("scopes never trap things" `primitives.md:44`). Modality = only deontic-via-
   `constraint`; future/planned state out of scope (`faq.md:72-74`). Counterfactuals explicitly
   unmodeled (`faq.md:66-70`).

## What this means for the spec

- **Worth fixing:** (1) **n-ary relations + relation-instance attributes** — the true deficit;
  ORM-style objectification is the template, but it collides with the FCO-IM Non-Goal, so it's
  a deliberate-scope decision. (2) **Deontic overload of `constraint`** — a typed sub-kind/slot
  (aim for "a deontic slot exists," not the canonical taxonomy).
- **Acceptable by design:** the minimal core + describe-then-project split (research-rated
  sound); the `thing`/`scope` redundancy and `time`/`by=` excess — the price of legible primitives;
  free-text prose in DAG-TOML is an intentional documented deviation (`spec.md:677-693`).
- **Out of scope:** uncertainty, future state, counterfactuals (`faq.md:66-74`); full FCO-IM
  metaconcepts (`grammar:19`).

## Rigor note

The §2 table and §3 diagnoses are byte-cited analyst constructions; **the adversarial-verify
pass was skipped** (token-pool over self-cap at launch), so they are not third-party refuted.
The 3 claims refuted in the parent research (fixedness-as-root-cause `[0-3]`, ORM-easier-than-ER
`[0-3]`, deontic-transferability `[1-2]`) were correctly discounted in the answers above. All
BWW mappings remain *by-analogy* — no external source evaluated IJB directly. A standalone
verify pass over this table would raise confidence and is cheap to run.

## Stats

6 angles · 28 sources fetched · 131 claims extracted · 25 verified · 22 confirmed · 3 killed · 9 after synthesis · 111 agent calls.

---

# VERIFICATION RESULTS

> **STATUS: VERIFY PASS COMPLETE.** The standalone adversarial-verify pass flagged
> as "skipped" in the Rigor note above has now been run against the cited bytes.
> Each mapping/answer claim was re-checked line-by-line in the spec; verdicts below
> supersede the analyst-asserted verdicts in the table where they differ.

**Verify pass: 7/13 mapping+answer claims confirmed against bytes, 5 corrected (softened), 1 refuted.**

| claim id | verdict | what the bytes actually showed | correction |
|---|---|---|---|
| M1 `thing` | partially-confirmed | `thing` = Thing + Class/Kind is solid (structural Thing is the class; instance via `instance_of=`/`class=instance` is the member) — grammar `:53-54,:115`, `spec.md:631,:665`. But the Property leg rests only on `identity=`, described as an identity *method* (`grammar:86`); the spec routes the primary Property role to `constraint` (`spec.md:633`) and `observed` (`:667`). | Restate as a **2-way** Thing/Class overload + a minor embedded identity-method parameter — not a full 3-way Thing/Class/Property overload. |
| M2 `scope` | **refuted** | `scope` is "Contexts in which things exist" with a `within` containment relation (`primitives.md:31-32,:44`; grammar `:56-58`) — a **composite/container**, not a set defined by shared properties (the BWW Class/Kind definition). `scope-def` lacks the `identity=` field `thing-struct` carries, and `scope-use` (`thing=`/`within=`) is unique. | The Class/Kind mapping is **unjustified**; map `scope-def` → structural composite/container, `scope-use` → part-of/membership. The "redundant with structural `thing`" claim is **overstated** (field asymmetry + unique `scope-use` form), so the `thing`/`scope` Class **redundancy** falls with it. |
| M3 `path` | confirmed | Both `path` arms hardcode exactly one `from=`/one `to=` → strictly binary (grammar `:61-62`); structural arm = coupling, instance arm = event-bearing (`grammar:93`: instance `path` is a valid `time(event=...)` target, `thing` is not). Overload + binary deficit grounded in grammar, not analogy. | Minor: cite the definition sentence at `primitives.md:50` (not :51 — :51-54 is the Properties list); optionally add `grammar:93` to evidence for the instance/event leg. |
| M4 `observed` | confirmed | `observed-call` carries a `by=` recorder slot (grammar `:68,:95`); replay records an event with `by` attribution (`:107`); facts are "witnessed" (`primitives.md:71-72`). `by=` has no BWW observer construct → **excess** holds. | Minor: `observed` maps most cleanly to a **History entry** (Event = the asserted assertion + `time`); `by=` excess confirmed. |
| M5 `constraint` | partially-confirmed | All four citations land exactly. Overload is real: `constraint-type = structural / policy / observed` (`grammar:70`) plus mixed ontic/deontic examples (`primitives.md:92-98`) put deontic norms and ontic limits in one form. But the definition says constraints "restrict movement, not existence" (`:102`) — disclaiming the static-state reading the "State law" label asserts. | **Mislabeled BWW construct:** restriction over traversal/transitions is a **transformation law / lawful event space**, not a state law / lawful state space. Map `constraint` → transformation law (dominant reading); tie the overload to the `constraint-type` enum + the mixed examples specifically. |
| M6 `time` | partially-confirmed | `time` only ever binds a timestamp to another event-bearing assertion (`grammar:66,:93,:119`); no class field, no standalone referent. `spec.md:668` overloads the token onto durations (`duration_s`, `estimated_ttr`) not just points → **excess** + duration-overload both real. | Soften the headline: `primitives.md:110-115` attributes more than pure ordering (Appearance/Disappearance/State change/Traversal eligibility). Byte-safe claim: "defined as a dimension/ordering index, exists in grammar only as a bound timestamp with no class field" — still a sound excess argument. |
| D1 n-ary deficit | confirmed | Both `path` arms fix exactly one `from=`/one `to=`, no participant or attribute slot (`grammar:61-62`) — strictly binary, no fan-in/out, no objectification. The deficit is grammar-grounded. | None. |

## Adjusted findings

Byte-verification leaves the analysis substantially intact but trims one over-reach and three mislabels. **Confirmed against bytes (not merely analyst-asserted):** the binary-`path` n-ary **deficit** (M3, D1) — the single most consequential finding — is solid and grammar-grounded; the `constraint` deontic/ontic **overload** (M5) is real; `time` and `observed.by=` **excess** (M4, M6) hold; and `thing` carries a genuine construct **overload** (M1). **Softened:** the `thing` overload is **2-way** (Thing/Class), not 3-way — the Property leg is just an embedded identity-*method* field, so `thing` does not meaningfully carry a domain Property. The `constraint` BWW label is corrected from **state law → transformation law** (it restricts movement/transitions, explicitly "not existence"). The `time` headline is softened from "only an ordering index" to "an ordering-index dimension with no independent grammatical existence." **Refuted:** `scope` → **Class/Kind is unjustified** — `scope` is a composite/container (context with `within`), not a property-defined set; this also **dissolves the `thing`/`scope` Class redundancy** claim and weakens one of the two redundancy legs (the `observed`/`thing` Property redundancy at `spec.md:667` is untouched).

**Net effect on the headline conclusion:** unchanged in substance. The set still exhibits overload (`thing` 2-way, `constraint` deontic), deficit (n-ary relations, relation-instance attributes), excess (`time`, `observed.by=`), and at least one redundancy leg (`observed`/`thing` Property) — so the absolute "all business reality" claim remains **not defensible** by the BWW standard, while the engineered minimal core stands. The only structural change is dropping `scope`→Class/Kind and the `thing`/`scope` redundancy from the diagnosis, and relabeling `constraint` to transformation law. The top-level verdict — **"usable constrained core; absolute claim not defensible"** — holds and is now byte-verified rather than analyst-asserted.

---

# MULTI-MODEL ADVERSARIAL REVIEW (codex · grok · mistral)

> **STATUS: RESEARCH ONLY.** Independent cross-provider adversarial review of the BWW
> analysis, dispatched via the llm-cli gateway to **codex, grok, and mistral** (fresh
> context, repo + sqry access, refute-by-default). Verbatim reviews in
> `docs/research/2026-05-31-ijb-bww-adversarial-review/raw_findings/{codex,grok,mistral}.md`.
> This supersedes the single-provider (Claude) verify pass above as the stronger standard.
> Codex independently ran `validate_ijb_conformance.py` over the ontologies/kind-files — all passed (structural conformance only, not BWW completeness).

## Cross-model tally (per claim)

| claim | codex | grok | mistral | consensus |
|---|---|---|---|---|
| M1 `thing` 3-way→2-way overload | partial | refuted (over-read) | partial | **2-way confirmed; Property leg killed by all 3** |
| M2 `scope`→Class/Kind | refuted-of-original (confirmed) | refuted-of-original (confirmed) | refuted-of-original (confirmed) | **UNANIMOUS: scope is a container, not Class/Kind; redundancy leg dissolves** |
| M3 `path` overload+binary | partial | partial | confirmed | **binary deficit unanimous; "coupling/Event" split is loose analogy (codex, grok)** |
| M4 `observed`+`by=` excess | partial | partial | confirmed | **History-entry map + `by=` excess hold; `by=` is *necessary provenance*, not bloat** |
| M5 `constraint` state-law→transformation-law | partial | refuted (mislabel) | partial | **UNANIMOUS: "state law" wrong → transformation/event law** |
| M6 `time` excess | partial | **refuted** | partial | **CONTESTED — see divergence below** |
| D1 n-ary deficit | partial | partial | confirmed | **UNANIMOUS load-bearing finding; "no attribute slot" overstated (`within=`/`moves=` exist)** |
| D2 Property redundancy | partial | **refuted (false premise)** | partial-weak | **redundancy essentially falls — `thing` carries no BWW Property** |
| D3 excess (`time`+`by=`) | confirmed | split (`by=` yes, `time` no) | confirmed | **`by=` excess holds; `time` excess contested** |
| Q1 no reification / by design | partial | confirmed | confirmed | **confirmed; partial escape via reifying-things + `observed(asserts=)`** |
| Q2 deontic→`constraint` overload | confirmed | partial | confirmed | **real but QUALIFIED — the 3-way `constraint-type` enum is a mitigating discriminator** |
| Q3 projection separation | confirmed | confirmed | confirmed | **UNANIMOUS, strengthened — it's the central architectural invariant** |
| Q4 identity/aggregation/modality/counterfactuals | partial | confirmed | confirmed | **confirmed (codex: counterfactual cite should be faq:72-78, not 66-70)** |

## Where all three converge (high confidence)

- **The binary-`path` n-ary deficit (D1/M3) is the unassailable, load-bearing finding** — all three call it grammar-hard (`canonical-assertion-grammar.md:60-62`, one `from=`/one `to=`) and the smoking gun is the explicit Non-Goal "Model full FCO-IM metaconcepts" (`:19`). Refinement: "no attribute slot" is **overstated** — `path` has fixed `within=`/`moves=` fields; the precise deficit is *no open participant set and no arbitrary relation-instance attributes*.
- **Three corrections from the verify pass are upheld unanimously:** `thing` is 2-way (Thing/Class) not 3-way (Property leg killed — `identity=` is a method; values live on `observed` per `spec.md:667`); `scope`→Class/Kind is refuted (it's a container, "scopes never trap things"); `constraint` is **transformation/event law**, not state law ("restricts movement, not existence", `primitives.md:102`).
- **Q2 deontic overload is real but *qualified*:** the `constraint-type = structural/policy/observed` enum (`grammar:70`) is a normative, enforced discriminator — not one undifferentiated bucket — so the clarity defect is milder than the analysis framed.

## Where they diverge (must be surfaced, not averaged away)

**1. The headline conclusion — split 2-1.** Codex and Mistral **uphold** "usable core; absolute claim not defensible," both naming the binary-path deficit as decisive. **Grok refutes the "not defensible" half as a category error:** IJB's founding docs repeatedly disclaim being a modeling grammar — "projection framework… projects facts into space without interpretation" (`faq.md:7`), "refuses to abstract" (`faq.md:15`), "queried, never drawn" (`primitives.md:139`), Non-Goal "model full FCO-IM metaconcepts" (`grammar:19`). BWW was built to judge grammars (ER/UML/BPMN) that *claim* to represent all business/social phenomena. Grok's case: applying BWW to a deliberately observation-only, interpretation-free substrate, without first subtracting the explicitly disclaimed territory, mis-categorizes the artifact — so read in its actual bounded scope, the six primitives are *complete-for-purpose*.

**2. `time` excess (M6/D3) — contested.** Grok refutes the excess label (Time has five explicit controls and "nothing exists outside time", `primitives.md:106-125` — a first-class dimension, not a thin ordering index); codex and mistral soften but retain it. Net: `time` excess is **weak/contested**, not firm.

**3. Property redundancy (D2) — collapses.** Grok refutes the premise outright (`thing` carries no BWW Property); the other two grade it weak. The redundancy diagnosis essentially **falls out** of the analysis.

## What all three say the analysis MISSED

- **Free-text/prose deviation is the real circumvention surface** (`spec.md:677-712`): DAG-TOML intentionally allows prose fields, default-classed `observed` and dual-tagged `constraint`+`policy` when normative. Codex and Grok both flag this as a **larger clarity/excess risk than the deontic overload** — it's the unbounded channel through which "strategy/culture/risk-posture" (the forbidden answers) can re-enter the substrate untyped.
- **`moves=` is an open, document-local, untyped carrier of domain semantics** on paths (Grok, Mistral) — an excess vector parallel to free text.
- **No BWW System/Composition construct** — no scope-of-scopes or composite-thing decomposition; "scopes never trap things" blocks mereology (Grok, Mistral). A genuine deficit for org-structure/system-boundary modeling the analysis didn't name.
- **`scope-def` vs `scope-use` asymmetry** is its own latent overload within `scope` (Codex, Mistral).

## Net adjusted conclusion (incorporating the dissent)

The **byte-level findings are robust and now cross-provider-verified**: the binary-`path` n-ary/relation-attribute **deficit is the durable, framing-independent result** (unanimous), and the three verify-pass corrections (M1 2-way, M2 scope-refuted, M5 transformation-law) stand. Two of the original weaknesses **weaken further** under three-model scrutiny — `time` excess (contested) and Property redundancy (collapsed) — and the deontic overload is **qualified** by the typed-enum discriminator.

The **interpretive headline is genuinely contested 2-1.** The honest landing:
- *If* IJB is judged as a modeling grammar, the absolute "all business reality" claim is **not defensible** (codex, mistral) — the binary-path deficit alone suffices.
- *But* IJB explicitly and repeatedly disclaims being a modeling grammar; read in its declared scope as an observation-only projection substrate, the six primitives are **complete-for-purpose**, and the BWW critique risks being a **category error** (grok).

**The framing-independent takeaway:** the one finding that survives every model and both framings is the **binary-`path` deficit** — IJB cannot natively express n-ary relations or relation-instance attributes, *by deliberate design* (the FCO-IM Non-Goal). Whether that is a "flaw" or an "accepted scope boundary" is exactly the modeling-grammar-vs-projection-substrate question the three models split on — and is the real decision for the spec owners, not a fact the analysis can settle.

---

# ROUND-2 RESOLUTION — the split resolves to 3-0 reframe

> **STATUS: RESEARCH ONLY.** Round-2 rebuttal dispatched to **codex and mistral** (the two
> that upheld "not defensible" in round 1) with two added inputs: (1) the free-text
> deviation is **intentional-by-design** (`spec.md` §10.3 / 677-712), and (2) grok's
> category-error argument verbatim. They were asked to defend or revise against bytes.
> Verbatim re-reviews: `docs/research/2026-05-31-ijb-bww-adversarial-review/raw_findings/{codex,mistral}-r2.md`.

## Outcome: both reviewers revised. Consensus is now 3-0 to REFRAME.

> **codex (r2):** *"I revise my round-1 verdict… Grok's category-error objection is mostly
> correct… Not defensible as a full BWW-style business modeling grammar; defensible, with
> caveats, as a deliberately scoped projection/observation substrate."*
>
> **mistral (r2):** *"REFRAMED… grok's category-error rebuttal changes my mind. The round-1
> verdict was correct for the wrong category. The bytes force the reframing."*

All three models now agree:

1. **The headline reframes, it does not stand unqualified.** The durable verdict:
   > Not defensible **as a BWW-style modeling grammar** (binary `path`, no n-ary/objectification, closed forms, deliberate exclusion of uncertainty/causality/intent/counterfactuals) — **but** that is not the artifact IJB claims to be. **As a projection/observation substrate read in its declared scope, the six primitives are plausibly complete-for-purpose.**
   Grounds: `faq.md:5-9` ("No. This is a projection framework… projects facts into space without interpretation"), `faq.md:13-15` ("refuses to abstract"), `primitives.md:129-144` ("queried, never drawn"), `core-specification.md:9-15` ("the visualization is not the model"), Non-Goals `canonical-assertion-grammar.md:15-19`.

2. **The binary-`path` deficit is reclassified: flaw → accepted scope boundary.** The byte fact (`grammar:60-62`, one `from=`/one `to=`) is unchanged and still limits adoption in n-ary domains, but it sits squarely inside the explicit Non-Goal "Model full FCO-IM metaconcepts" (`grammar:19`) and IJB's definition of paths as movement connections, not general predicates (`fco-im-integration.md:5-7,:14-19`). It is a deliberate restriction, not an internal contradiction.

3. **The free-text deviation is NOT a defect.** Both reviewers withdrew the round-1
   "circumvention surface / clarity defect" framing. `spec.md:677-712` documents it as a
   *known and intentional* DAG-TOML deviation with a defined classification (default
   `observed`; normative → `constraint`+`policy`). It remains a tooling risk surface to
   watch, but it is a declared design boundary, not evidence the six primitives fail.

## The one surviving actionable critique (codex)

Codex declines to withdraw the criticism *entirely*, on a narrow, concrete point: the
**literal sentence** "All business reality can be described using six primitives"
(`primitives.md:7`, `README.md:14`) is **overbroad on its face** and invites exactly the
modeling-grammar reading the rest of the corpus rejects. The low-cost fix is wording — e.g.
"all **projectable** business facts" / "all factual business descriptions **in IJB's
scope**." That single edit would pre-empt repeat BWW-style objections without changing any
primitive.

## Net resolution

The multi-model adversarial process did its job: a 2-1 split, cross-examined against bytes,
**converged to 3-0**. The byte-level findings (the binary-`path` deficit chief among them)
are **factually intact**; their **normative force dissolves** once IJB is judged on its own
declared scope rather than as a modeling grammar. The only standing recommendation is a
**wording change to `primitives.md:7`** to scope the "all business reality" claim. The
six-primitive substrate itself is sound for what IJB declares it to be.
