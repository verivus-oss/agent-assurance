# SPEC: FCO-IM integration for IJB

Slug: 20260420-fco-im-integration

## Summary
Adopt the Population-Backed Substrate option for FCO-IM integration so IJB gains grounding, verification, and resistance to semantic drift without becoming a full conceptual modeling methodology.

## Goals
- Strengthen descriptive grounding.
- Preserve IJB as a projection framework.
- Improve replay, traceability, and review.
- Reduce semantic drift.

## Non-Goals
- Turn IJB into FCO-IM.
- Introduce a new notation system.
- Replace the six primitives.
- Require full FCO-IM training.
- Allow visualization to invent meaning.

## Design Principle
Borrow discipline, not identity.

IJB remains projection framework. FCO-IM strengthens descriptive substrate only.

## Adoption Decision
Accepted option: Population-Backed Substrate.

Operational meaning:
- Every structural construct includes at least one concrete instance.
- Every observation records `asserts`, observer, time, and scope.
- Every element states identity method and structural-or-instance status.
- Every constraint states target, scope, restriction, and type.
- Every review challenges assertions and examples.

## Incorporated Capabilities
- Canonical verbalized assertions.
- Mandatory concrete examples.
- Separation of structure vs recorded observation.
- Lightweight identification and constraint discipline.
- Validation by replay into human language.

## Requirements

### Canonical verbalized assertions
Every IJB element MUST be expressible as a natural-language assertion. If it cannot be said clearly, it cannot exist in the model.

Core forms:
- Thing: "Thing X exists."
- Scope: "Scope Y exists."
- Scope placement: "Thing X exists within Scope Y."
- Path: "Path P connects Thing A to Thing B within Scope S."
- Observed: "Observation O records that <assertion> occurred at Time T by Observer Z."
- Constraint: "Constraint C restricts Target T within Scope S."
- Time: "Event E occurred at Time T."

### Mandatory concrete examples
Every structural construct MUST include at least one real instance. No exceptions.

Example:
- Structure: `Path order_fulfillment connects Order to Shipment`
- Instance: `Path order_fulfillment_10027 connects Order-10027 to Shipment-88411`

### Structure vs recorded observation
This separation is mandatory.

- Structure defines what can exist.
- Observation defines what was actually recorded.
- Never mix them.

Every observation must include:
- What was observed.
- Who observed it.
- When.
- In what scope.

When canonical assertion grammar is used:
- This spec remains authoritative for semantics.
- `01_SPEC__20260420-canonical-assertion-grammar.md` is authoritative for encoding.

### Identification and constraints
Every element must answer:
- What is it.
- How is it identified.
- Is it structural or instance.
- Is it same as something else.

Every constraint must define:
- What it applies to.
- Where it applies.
- What it restricts.
- What type it is.

Constraint types:
- Structural.
- Policy.
- Observed.

### Validation by replay
System must be able to say back the model. If it cannot, model is wrong.

Required capabilities:
- Replay any element as plain language.
- Trace visual elements to assertions.
- Allow domain experts to challenge statements.

Key questions:
- What is this?
- Who recorded it?
- When?
- Is it structure or observation?
- What constraint applies?

## Integration into IJB primitives
- Things: Must be identifiable and verbalizable.
- Scopes: Define meaning boundaries, not visual grouping.
- Paths: Must connect identified Things explicitly.
- Observed: First-class recorded assertion with actor, time, and context.
- Constraints: Must be explicit, never implied visually.
- Time: Applies to both structure and observation.

## Constraints
Projection rules remain unchanged.

Still forbidden:
- Inventing concepts.
- Explaining intent.
- Implying causality.

New capabilities:
- Trace to assertions.
- Show examples.
- Distinguish structure vs observation.
- Replay view as language.

## Compliance Criteria
Valid IJB + FCO-IM integration must:
- Trace every visual element to an assertion.
- Include concrete examples.
- Separate structure and observation.
- Define identity and constraints clearly.
- Support replay into human language.

## Closing Position
FCO-IM makes IJB grounded. IJB makes FCO-IM navigable.

Substrate becomes precise. Projection stays clean.

## Token Rules
- Single-sentence summary.
- Bullets over long narrative paragraphs.
- Direct verbs. No filler.
- Keep six primitives explicit.
