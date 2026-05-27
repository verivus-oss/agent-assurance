# Examples

This directory contains concrete examples of single-path traversals that demonstrate the framework without collapsing back into diagrams.

## Available Examples

### [01: Purchase Approval Traversal](01-purchase-approval-traversal.md)

A purchase request (PR-2847) moving through organizational approval over 72 hours.

**Demonstrates:**
- Single path crossing multiple organizational scopes
- Observable delays against time constraints
- Multiple perspectives viewing the same facts
- Complete factual grounding in observations
- All six primitives without introducing new concepts

**Key learning:** How to describe and project one traversal without interpretation.

### [02: Incident Response Traversal](02-incident-response-traversal.md)

A database performance degradation (Incident-5847) propagating through systems and triggering incident response over 33 minutes.

**Demonstrates:**
- Parallel paths (technical remediation + organizational communication)
- Observable propagation through dependent systems without implied causation
- Multiple constraint types (SLOs, response times, policies, access controls)
- State changes as timestamped observations (Normal → Degraded → Recovered)
- Four distinct perspectives (on-call engineer, incident commander, database team, post-incident reviewer)
- Time-sensitive operations with detection lag and response metrics

**Key learning:** How to show technical incident response and organizational coordination as observable facts without asserting root cause or blame.

### [03: Data Pipeline Traversal](03-data-pipeline-traversal.md)

A batch of customer transaction records (347,829) moving through a data pipeline with quality validation, partial failures, and retry paths over 31 minutes.

**Demonstrates:**
- Data as observable thing moving through processing stages
- Quality constraints as gates (validation splits data into pass/fail paths)
- Partial success explicitly shown (98.35% pass, 1.65% fail, 85.4% recovery on retry)
- Branching and merging paths (main path, quarantine path, retry path)
- Multiple technical scopes (ingestion, transformation, storage, serving)
- Resource constraints (executor limits, write rate limits, encryption requirements)
- Four perspectives (data engineer monitoring quality, analyst waiting for data, platform team managing infrastructure, orchestration viewing full flow)

**Key learning:** How to show data movement with observable quality splits and retry mechanics without implying causation for failures or judging success rates.

### Example 04 is intentionally omitted

The original IJB repository carried an internal worked example at slot
04 that is not part of this public foundation. The numbering jumps from
03 to 05 to preserve cross-reference stability with the upstream
examples that are shipped here; no public 04 will be added in this
ordering.

### [05: Canonical Assertion Worked Example](05-canonical-assertion-worked-example.md)

A compact badge-access approval traversal recorded in canonical assertion grammar, replayed into plain language, and mapped into projection.

**Demonstrates:**
- Tight machine-usable assertion syntax
- Structural vs instance separation in one substrate
- Observation as explicit metadata over prior assertions
- Constraint checking by observed sequence
- Replay from canonical records into plain language
- Projection mapping from same assertion set

**Key learning:** How to make IJB assertions parseable, reviewable, and projectable without importing a separate modeling notation.

### [06: Hybrid Environment Traversal](06-hybrid-environment-traversal.md)

A fictional logistics organization retrieving one shipment view across a datacenter, an Azure tenant, and an AWS tenant in a single observed traversal.

**Demonstrates:**
- One application family distributed across on-prem, Azure, and AWS
- Cross-environment retrieval without new architecture abstractions
- Datacenter system-of-record plus AWS telemetry enrichment
- Explicit network, identity, and timing constraints
- One description supporting multiple infrastructure views

**Key learning:** How to describe a hybrid enterprise estate factually by following one real traversal across all three environments.

### [07: Hybrid Environment Canonical Assertions](07-hybrid-environment-canonical-assertions.md)

A grammar-backed version of the hybrid datacenter, Azure, and AWS traversal, recorded as canonical assertions and replayed into plain language and projection.

**Demonstrates:**
- Machine-usable hybrid infrastructure assertions
- One hybrid request expressed as structural and instance paths
- Explicit constraint and observation records across environments
- Replay from canonical records into operational language
- Projection mapping without introducing architecture abstractions

**Key learning:** How to represent a multi-environment enterprise traversal in one parseable substrate while preserving IJB projection discipline.

---

## Starting Point: Single Path Traversal

The first non-dangerous move is to sketch one single interaction:

**"Following one path across scopes over time."**

Not a full system. Just one factual traversal.

## Example Structure

Each example should contain:

1. **Factual description** - The six primitives as facts
   - What things exist
   - What scopes they're in
   - What paths connect them
   - What was observed
   - What constraints apply
   - How time orders it all

2. **Spatial projection** - How those facts map to space
   - Object placement
   - Scope rendering
   - Path routing
   - Observation overlays
   - Constraint visualization
   - Time controls

3. **Reality check** - Verification
   - Can you point at something and name its primitive?
   - Does the visualization introduce new concepts?
   - Can multiple roles view the same facts at different distances?

## Anti-Patterns to Avoid

Do NOT create examples that:
- Explain strategy or intent
- Imply causality
- Suggest correctness
- Replace the description
- Invent concepts beyond the six primitives

## Example Scenarios (Potential Future)

Additional scenarios that could be described using the framework:

- Document routing through review cycles with delays
- Service request crossing organizational boundaries
- Compliance check traversing regulatory scopes
- Merger/acquisition scenario (scopes changing over time)
- Real-time operational scenario (high-frequency observations)
- Cross-language software build pipeline
- Multi-region data replication with lag visibility

Each scenario should be factual, observable, and describable using only the six primitives.
