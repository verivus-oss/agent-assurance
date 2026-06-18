# Adversarial review — BWW representational analysis of the IJB six primitives

You are a **fresh-context, independent adversarial reviewer**. Your job is to try to
**refute** a Bunge-Wand-Weber (BWW) representational analysis of the IJB primitive set by
re-reading the actual spec bytes. Default to skepticism. Verify everything against bytes;
do **not** accept the analysis's own summary as evidence.

## Repo

`/srv/repos/external/verivus-oss/agent-assurance/`

## What to review

The analysis under review is the **"Follow-on: A Bunge–Wand–Weber Representational
Analysis"** section (and its VERIFICATION RESULTS) in:
`docs/research/2026-05-31-ijb-six-primitive-usability.md`

Read it, then independently check it against the ground-truth spec bytes:
- `foundations/ijb/primitives.md` (the six primitive definitions)
- `foundations/ijb/canonical-assertion-grammar.md` (ABNF productions, replay templates, validation rules)
- `foundations/ijb/faq.md` (out-of-model declarations: uncertainty, future state, counterfactuals)
- `spec.md` §10 (IJB mapping tables) and §12 (closure/sha)
- `core/ontology.toml`, the `*-kind.toml` descriptors, `validators/validate_ijb_conformance.py`

IJB's six primitives are the closed set `thing, scope, path, observed, constraint, time`
(`validators/validate_ijb_conformance.py:56`).

## BWW background (the fixed mapping target)

BWW ontological constructs: Thing; Property (intrinsic/mutual/emergent); Class (shared
property) and Kind (2+ shared properties); State, State law, Lawful state space; Event,
Lawful event space; Transformation, Lawful transformation; History; Coupling/binding
(acts-on); System/composition/decomposition. Four deficiency types to judge:
**construct deficit** (incompleteness), **construct overload** (one grammar construct →
≥2 ontological constructs), **construct redundancy** (≥2 grammar constructs → same
ontological construct), **construct excess** (grammar construct → no ontological construct).

## The 13 claims to adjudicate (verify or refute each, with file:line)

**Mappings:**
- **M1 `thing`** → Thing + Class/Kind + Property — claimed 2-way overload (Thing/Class), Property leg is only the `identity=` method.
- **M2 `scope`** → claimed **NOT** Class/Kind but a composite/container (context with `within`); the `thing`/`scope` Class redundancy is therefore claimed dissolved.
- **M3 `path`** → coupling (structural) / acts-on Event (instance); strictly **binary** (one `from=`/one `to=`) — overload + binary deficit.
- **M4 `observed`** → Event + History entry; `by=` observer slot has no BWW analogue (excess).
- **M5 `constraint`** → **transformation law / lawful event space** (NOT state law; it "restricts movement, not existence"); overloaded by absorbing deontic facts via `constraint-type = structural/policy/observed`.
- **M6 `time`** → no independent BWW referent (bound timestamp only, no class field); `spec.md:668` overloads the token onto durations — excess.

**Deficiencies:**
- **D1** binary `path` cannot express n-ary relations or relation-instance attributes (no participant/attribute slot in `path-call`).
- **D2** redundancy: BWW Property carried by both `thing` attributes and `observed` (`spec.md:667`). (Note: the `thing`/`scope` Class redundancy was already withdrawn per M2.)
- **D3** excess: `time` and `observed.by=` have no BWW referent.

**Open-question answers:**
- **Q1** IJB has **no reification** for relation attributes / n-ary relations; uncertainty is declared out-of-model (`faq.md:66-70`); by design (Non-Goal "model full FCO-IM metaconcepts", `canonical-assertion-grammar.md:19`).
- **Q2** deontic facts collapsed into `constraint` → construct overload.
- **Q3** strict descriptive-vs-spatial separation: "queried, never drawn"; multiple projections from same facts (`primitives.md:139,:144`).
- **Q4** identity = a method not a versioned value; aggregation = scope grouping not mereology; modality = only deontic-via-constraint; counterfactuals unmodeled.

**Overall claim to test:** "IJB is a usable *constrained core*, but the absolute 'all
business reality can be described with six primitives' claim is **not defensible** by the
BWW standard." — sound, overstated, or understated?

## Required output (write to your findings file AND return it)

For each of the 13 claims: `id | verdict (confirmed | partially-confirmed | refuted) |
the bytes you actually found (quote file:line) | correction if any`. Then:
- **Errors you caught** the analysis got wrong (wrong BWW construct, wrong line, unjustified analogy).
- **Anything the analysis MISSED** (a primitive defect, a deficit category, an overload it didn't flag).
- **Verdict on the overall claim** in one paragraph, with your single highest-confidence reason.

Decide on inspected bytes, not on the analysis's framing. If a BWW mapping is justified
only by plausible analogy rather than the primitive's actual definition/grammar, say so.
Write your full review to the path given in the task, and also return it as your final message.
