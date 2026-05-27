# DESIGN: FCO-IM integration options for IJB

Slug: 20260420-fco-im-integration-options

## Summary
Use selected FCO-IM discipline to strengthen IJB substrate quality without turning IJB into a full conceptual modeling method.

## Approach
- Extract only FCO-IM properties that reinforce IJB description-first rules.
- Reject FCO-IM elements that would replace IJB primitives or introduce a new visual language.
- Offer three adoption levels with clear cost, benefit, and fit.

## Structure
- Research basis.
- Three integration options.
- Decision and recommendation.

## Decisions
- Keep IJB six primitives unchanged.
- Keep projection rules unchanged.
- Apply FCO-IM only to descriptive substrate, not to visualization layer.
- Prefer verbalization, examples, identification, constraints, and replay over diagrammatic import.
- Adopt Option 2: Population-Backed Substrate as repository default.

## Research Basis
Observed from FCO-IM sources:
- FCO-IM models communication about a universe of discourse, not the universe directly.
- FCO-IM treats verbalized fact expressions as primary modeling material.
- FCO-IM uses concrete examples and population as part of validation, not as optional illustration.
- FCO-IM emphasizes elementary facts, explicit identification, and explicit constraints.
- FCO-IM validates models by regenerating readable language for domain experts.

Implication for IJB:
- Strong compatibility with IJB descriptive substrate.
- Low compatibility with any move toward new diagram notation or extra primitive layers.

## Option 1: Assertion Profile
Apply only verbalization and replay discipline.

What changes:
- Every Thing, Scope, Path, Observed, Constraint, and Time element must have a canonical assertion.
- Every projection element must trace to one assertion.
- Every review must include read-back in plain language.

What stays unchanged:
- No new repository structures.
- No mandatory instance population.
- No added identification scheme beyond current document needs.

Fit to IJB:
- Strong fit with projection discipline.
- Minimal disruption to current docs.

Benefits:
- Immediate improvement in clarity.
- Easy adoption across existing examples and specs.
- Low training cost.

Costs:
- Weak control over semantic drift.
- Weak support for identity disputes.
- Constraints remain under-specified unless authors add extra rigor manually.

Best for:
- Fast adoption.
- Existing docs retrofit.
- Teams that want stronger wording but not heavier process.

## Option 2: Population-Backed Substrate
Apply verbalization, concrete examples, structure/observation separation, identification, and replay.

What changes:
- Every structural construct must include at least one real instance.
- Every Observed item must record assertion, observer, time, and scope.
- Every element must state identity method and whether it is structural or instance.
- Every constraint must state target, scope, restriction, and type.
- Reviews must challenge both assertions and examples.

What stays unchanged:
- Six primitives remain complete.
- Visualization still adds no meaning.
- No FCO-IM diagram notation enters IJB.

Fit to IJB:
- Strongest balance between rigor and simplicity.
- Extends current spec naturally.

Benefits:
- Better grounding than Option 1.
- Better separation between structure and recorded fact.
- Better auditability for examples, constraints, and observations.
- Better resistance to semantic drift.

Costs:
- Higher authoring effort.
- More review discipline required.
- Existing docs need targeted rewrite to add instances and identifiers.

Best for:
- Canonical IJB documentation.
- New examples.
- Cross-team work where traceability matters.

## Option 3: FCO-Informed Fact Registry
Apply Option 2 and add a formal fact-expression registry as the canonical substrate.

What changes:
- Every modeled statement is stored as an explicit fact-expression record.
- Structural assertions and observed assertions are tracked as separate populations.
- Constraints are defined against fact expressions, roles, or populations.
- Projection views are generated only from registered assertions.
- Model checks include elementarity-style review to detect clustered or incomplete statements.

What stays unchanged:
- Visualization rules remain unchanged.
- IJB still does not become a process or intent modeling method.

Fit to IJB:
- Strong rigor.
- Highest risk of dragging IJB toward full conceptual modeling methodology.

Benefits:
- Maximum traceability.
- Strongest support for validation and replay.
- Strongest support for downstream transformation, tooling, and governance.

Costs:
- Highest complexity.
- Highest training burden.
- Real risk that practitioners start modeling the registry instead of describing the business.
- Likely overbuilt for Markdown-first repository use.

Best for:
- Tool-backed implementations.
- Large-scale governed repositories.
- Cases where automated checks and transformations are primary goals.

## Alternatives
- Full FCO-IM adoption: rejected because it replaces IJB framing with a full conceptual modeling method.
- No integration: rejected because it leaves IJB more exposed to semantic drift and weak validation.

## Risks
- Option 1 risk: weak identity and constraint discipline.
  Mitigation: require minimal identity fields in all new docs.
- Option 2 risk: authors may fake examples or treat them as decorative.
  Mitigation: require examples tied to observed or documented instances.
- Option 3 risk: method expansion overwhelms IJB.
  Mitigation: restrict to tool-backed environments only.

## Recommendation
Chosen option: Option 2.

Reason:
- It captures the FCO-IM capabilities most compatible with IJB.
- It strengthens the descriptive substrate without changing IJB identity.
- It preserves the core rule: visualization does not explain the business; it projects traceable facts.

Adopt Option 1 as a minimum baseline for legacy docs. Reserve Option 3 for future tool-backed work only.

## Sources
- FCO-IM home: https://www.fco-im.nl/
- FCO-IM analysis process paper page: https://www.fco-im.nl/papers/66-fco-imanalysisprocess
- FCO-IM papers index: https://www.fco-im.nl/papers
- Fact Oriented Modeling with FCO-IM book page: https://technicspub.com/fact-oriented-modeling/

## Token Rules
- Single-sentence summary.
- Bullets over long narrative paragraphs.
- Direct verbs. No filler.
- Keep IJB and FCO-IM roles distinct.
