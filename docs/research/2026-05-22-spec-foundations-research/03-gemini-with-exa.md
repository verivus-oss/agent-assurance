# Gemini (gemini-3.1-pro-preview) independent research report

Run via `llm-gateway` with the `exa` MCP server enabled, YOLO approval mode.
Identical context block as the other agents. Output below is verbatim.

---

Here is an independent, external research synthesis evaluating the
foundations, precedents, and potential pitfalls of the DAG-TOML specification
design. This analysis draws heavily on ontology engineering, specification
design, and recent advancements in agentic AI governance.

## 1. IJB Primitives Prior Art

The IJB meta-ontology proposes a six-primitive foundation (`thing`, `scope`,
`path`, `observed`, `constraint`, `time`). When compared to established upper
ontologies like the Basic Formal Ontology (BFO), the Unified Foundational
Ontology (UFO), and business-centric models like FCO-IM and W3C PROV, this
six-primitive set sits somewhere between a highly abstract philosophical
ontology and a communication-oriented modeling layer.

UFO and Bunge-Wand-Weber (BWW) strictly separate *objects* (endurants) from
*events* (perdurants) and heavily utilize *tropes* (moments/properties that
exist only in relation to a subject). The IJB `thing` and `time`/`observed`
primitives loosely map to these, but risk conflating the persistence of an
object with its state at a given time. W3C PROV relies on three core nodes:
`Entity`, `Activity`, and `Agent`. A known category error in PROV — which IJB
risks repeating — is failing to properly separate the *Agent* (the
responsible actor) from the *Activity* (the `path` or process). If a `thing`
in IJB is used interchangeably as both data and actor without strict class
markers, provenance validation breaks down.

Furthermore, FCO-IM (Fully Communication Oriented Information Modeling)
warns against arbitrary abstraction. FCO-IM successfully collapses the
distinction between "object types" and "fact types," treating all concepts
as communicative facts. IJB's rigid six-primitive structure risks "premature
normalization" — forcing complex enterprise realities (like nested
delegations of authority) into a narrow `path` or `constraint` box,
stripping away the nuanced soft semantics that domain experts actually
communicate.

**Citations:**
- [A UML and OWL description of Bunge's upper-level ontology model](https://link.springer.com/article/10.1007/s10270-008-0082-3) — Details how foundational ontologies (BWW, UFO) handle state changes and tropes, warning against over-simplifying temporal properties.
- [PROV-DM: The PROV Data Model (W3C)](https://www.w3.org/TR/2013/REC-prov-dm-20130430/Overview.html) — Outlines the strict separation of Entities, Activities, and Agents necessary for cryptographic provenance chains.
- [CaseTalk - NIAM, ORM and FCO-IM](https://casetalk.com/articles/explained/474-niam,-orm-and-fco-im) — Explains how FCO-IM collapses the object/fact divide to preserve literal business communication, a warning against rigid abstractions.
- [Towards a Reference Ontology for Business Models](https://link.springer.com/chapter/10.1007/11901181_36) — Compares REA (Resource-Event-Agent) with other ontologies, highlighting that economic/business realities require explicit resource transfer concepts that generic primitives often miss.

## 2. TOML-Based Spec Design

Basing a complex, declarative specification entirely on TOML (without a
native JSON Schema layer) is a polarizing architectural choice. TOML was
explicitly designed for configuration, not for complex data interchange or
schema definition. Ecosystems like Python (`pyproject.toml`) and Rust
(`Cargo.toml`) have popularized TOML because it is unambiguous and minimal.
However, these communities have faced severe friction when attempting to
enforce complex validation rules.

The lack of a native JSON-Schema equivalent for TOML forces projects to map
TOML structures into JSON Schema validators (e.g., the `taplo` language
server or `validate-pyproject`). This translation exposes inherent TOML
limitations: TOML does not support `null` values in arrays, handles
floating-point anomalies (NaN/Inf) differently than JSON, and becomes
extremely verbose when dealing with deeply nested structures (e.g., arrays
of tables). Furthermore, TOML lacks a native mechanism for `$ref` (reusable
fragments) or polymorphic payloads (`oneOf`/`anyOf`). If DAG-TOML enforces
hard invariants exclusively via custom Python validators rather than a
declarative schema, it creates a massive barrier to entry for tooling in
other languages. If the Python validator is the only source of truth, the
specification effectively becomes "whatever the Python code does."

**Citations:**
- [Documenting how to validate TOML with JSON schema (toml-lang)](https://github.com/toml-lang/toml/discussions/1038) — Highlights the impedance mismatch between TOML and JSON Schema, specifically around `null` arrays and numeric representations.
- [TOML schema (toml-lang issue 1057)](https://github.com/toml-lang/toml/issues/1057) — Details the community struggle to build a native TOML schema language.
- [YAML vs TOML: expressiveness, strictness, tradeoffs](https://inteist.com/yaml-vs-toml/) — Summarizes TOML's limitations, noting that while it prevents indentation errors, its lack of references (like YAML anchors) makes repeated, complex schema structures dangerously verbose.
- [Cargo.toml Schema Generation (rust-lang/cargo PR 14683)](https://github.com/rust-lang/cargo/pull/14683) — Demonstrates that even the creators of the largest TOML ecosystem (Rust/Cargo) eventually capitulate to generating JSON Schemas to enable ecosystem tooling.

## 3. Kind-Descriptor / Self-Describing Schema Patterns

A "schema of schemas" (where `*-kind.toml` describes the ontology) often
falls victim to "ontology drift," where the prose description of the schema
diverges from its machine-enforced reality. The semantic web community
experienced this with OWL/RDF. Formal ontologies reward completeness, but
past a certain point, completeness becomes a maintenance liability.

Modern self-describing systems succeed when they embrace closed-world
validation over open-world inference. For example, the telecom industry uses
SHACL to validate OpenAPI schemas because OpenAPI's logical operators
(`anyOf`, `allOf`) are too ambiguous for strict compliance. Similarly, tools
like CUE and Protobuf's `FileDescriptorSet` embed the schema tightly with
the data. When DAG-TOML relies on prose descriptions tied to Python
validators, it risks the "completeness trap": the more relations defined in
the `*-kind.toml`, the more brittle the validator becomes. Projects like
`spec-schema.org` and `CognitiveLayers` (clayers) solve this by establishing
strict, bidirectional content hashes between Markdown prose and YAML/XML
layers, ensuring drift is detected in CI. Without a mechanism to
cryptographically bind the prose of KD1-KD3 to the Python validation logic,
DAG-TOML will drift.

**Citations:**
- [How Enterprise Ontologies Decay — And How to Stop It (Alation)](https://www.alation.com/blog/living-ontologies-enterprise-ai/) — Explores the "completeness trap" of formal ontologies and how they inevitably drift from reality if not tightly coupled to execution.
- [EricssonResearch/openapi-to-rdf](https://github.com/EricssonResearch/openapi-to-rdf/blob/main/CONVERSION_DOC.md) — Demonstrates how SHACL is used to clamp down on ambiguous, self-describing OpenAPI schemas to enforce single-valued constraints.
- [How CUE works with Protocol Buffers](https://cuelang.org/docs/concept/how-cue-works-with-protocol-buffers/) — Shows how self-describing schemas (Protobuf) require an extraction layer (CUE) to actually enforce advanced business constraints consistently.
- [CognitiveLayers / clayers (GitHub)](https://github.com/CognitiveLayers/clayers) — A modern approach to specification design that uses content hashes to prevent drift between human-readable specs and machine-readable artifacts.

## 4. Agent Assurance & AI Agent Governance Specs

The agent assurance landscape is currently fragmenting between advisory
frameworks (NIST AI RMF) and certifiable management systems (ISO/IEC 42001).
The critical gap identified by recent research is that existing frameworks
assume a static "intended purpose" that can be documented pre-deployment.
Autonomous, agentic AI fundamentally breaks this assumption because its
execution paths are non-deterministic.

Supply chain security (SLSA, SBOM) offers a cautionary tale for agent
assurance. The recent "Mini Shai-Hulud" worm exploited the "Provenance
Paradox": the malware shipped with valid SLSA Build Level 3 attestations.
SLSA faithfully reported that the pipeline built the code, but it could not
attest to the *safety* of the code. This is a fatal risk for DAG-TOML's
`assertion-bundle` and `disclosure-attestation` kinds: over-attestation
leads to evidence fatigue. If an agent simply signs a log stating "I
executed this tool," the system is cryptographically secure but behaviorally
blind. ISO 42001 auditors require per-action operational receipts (e.g.,
HMAC-signed, chained JSON logs that prove a human oversight gate was checked
*before* a model invoked a tool). DAG-TOML must focus on runtime behavioral
constraints, not just static structural provenance.

**Citations:**
- [The Provenance Paradox: Why SLSA Signing Couldn't Stop the TanStack Worm](https://lyrie.ai/research/research/2026-05-12-slsa-provenance-paradox) — A critical analysis showing that cryptographic attestations prove origin, not safety, highlighting the danger of "provenance theatre."
- [ISO/IEC 42001 and Agentic AI: Satisfying Controls with Cryptographic Receipts](https://agenticrail.nz/blog/iso-42001-agentic-ai/) — Explains that ISO auditors require chained, per-action cryptographic receipts of gate decisions, not just static policy documents.
- [Why Agentic AI Breaks Every Existing Governance Framework](https://www.zerodaydawn.com/p/why-agentic-ai-breaks-every-existing) — Argues that frameworks requiring pre-deployment specification of purpose (like the EU AI Act) fail when agents autonomously plan and invoke cross-boundary tools.
- [NIST AI Risk Management Framework: Agentic Profile](https://labs.cloudsecurityalliance.org/agentic/agentic-nist-ai-rmf-profile-v1/) — Proposes that agentic governance requires continuous telemetry (action velocity, delegation depth) rather than static risk assessments.

## 5. Spec-Design Failure Modes

DAG-TOML's reliance on custom Python validators and TOML semantics makes it
highly susceptible to Hyrum's Law: "With a sufficient number of users of an
API, it does not matter what you promise in the contract: all observable
behaviors of your system will be depended on by somebody." Because DAG-TOML
lacks a declarative schema standard (like JSON Schema), the idiosyncrasies
of the Python validator *become* the de facto specification. If the Python
validator silently ignores a duplicated TOML key, users will rely on that
behavior.

Historically, the IETF's mandate of "rough consensus and running code" and
the W3C's "two independent implementations" rule exist precisely to break
this dependency on a single reference implementation. Furthermore, DAG-TOML
risks the "OWL/RDF Trap": being too expressive to actually validate. If the
specification tries to satisfy Postel's Law ("be liberal in what you
accept") by allowing infinite extensibility in the `*-kind.toml`
descriptors, it will inevitably lead to schema bloat. The contract testing
community (e.g., PactFlow) has proven that when schemas are too flexible,
consumers rely on undocumented edge cases, meaning the specification is a
fiction the moment it is published.

**Citations:**
- [Schemas Can Be Contracts | Introducing Drift](https://pactflow.io/blog/schemas-can-be-contracts/) — Details how polymorphic schemas and optional fields lead to API drift, where the observable behavior overrides the spec (Hyrum's Law).
- [IETF RFC 3935 - A Mission Statement for the IETF](https://www.ietf.org/rfc/rfc3935.txt) — The foundational document outlining why "running code" and interoperability outrank theoretical completeness in standard design.
- [Meet Hyrum and Postel (Nordic APIs)](https://nordicapis.com/meet-hyrum-and-postel/) — Explores the conflict between Postel's Law (leniency) and Hyrum's Law (accidental dependencies).
- [OWL 2 Web Ontology Language Profiles (W3C)](https://www.w3.org/TR/2012/REC-owl2-profiles-20121211/) — Shows how the W3C had to create heavily restricted "Profiles" because the full semantic standard was too computationally expensive and expressive to be implemented.

## 6. DAG-Shaped Traceability

Representing software traceability and implementations as Directed Acyclic
Graphs (DAGs) is mathematically sound but practically fraught. In software
engineering, defining the "critical path" through a DAG of artifacts is
vastly different from traditional project management (PERT/CPM). The
Critical Path Method (CPM) assumes deterministic task durations and infinite
resources. In software — and especially in non-deterministic agent
workflows — this assumption collapses.

If DAG-TOML utilizes a `critical_path` invariant defined as the "longest
weighted path," it is borrowing a CPM concept that ignores resource
bottlenecks and execution uncertainty. Critical Chain Project Management
(CCPM) has proven more effective for software because it models resource
constraints rather than just graph topology. Furthermore, automated
traceability systems struggle with "chain-based recovery." A DAG of
requirements pointing to artifacts pointing to tests is useless if the
intermediate nodes lose semantic meaning. If the DAG-TOML enforces hard
invariants like "blocks is inverse of depends_on," it must also guard
against semantic dilution across long traversal chains, ensuring that a
change in a root requirement accurately invalidates downstream gate
decisions.

**Citations:**
- [Critical Path vs Critical Chain in High-Uncertainty Environments](https://agileccpm.com/resources/critical-chain-vs-path/) — Explains why traditional Critical Path (CPM) fails in software/IT due to its inability to handle resource constraints and duration variability.
- [Systematizing Software Artifacts Traceability via Associations](https://arxiv.org/html/2603.16208) — Research on the difficulty of maintaining multi-hop traceability chains (e.g., requirement -> code -> test).
- [Advantages and Disadvantages of the Critical Path Method](https://thelinuxcode.com/advantages-and-disadvantages-of-the-critical-path-method-cpm-in-modern-project-engineering/) — Notes that while CPM provides clarity on zero-float paths, it is highly fragile; one slipped task restructures the entire DAG.
- [Seamless and Traceable Requirements](https://arxiv.org/html/2502.18617v2) — Discusses relation propagation in traceability DAGs, emphasizing that relations must be formally verified, not just structurally linked.

---

## TOP RISKS FOR THIS SPEC

1. **The Python Monoculture Risk:** By rejecting JSON Schema and relying
   entirely on Python validators to enforce shape and invariants, DAG-TOML
   violates the W3C "two implementations" rule. The bugs and edge-case
   parsings of the Python tool will inadvertently become the standard
   (Hyrum's Law).
2. **The Provenance Paradox (Evidence Fatigue):** `assertion-bundle` and
   `traceability` structures risk recreating the SLSA vulnerability.
   Cryptographically proving an agent took an action does not prove the
   action was safe.
3. **Category Errors in the Meta-Ontology:** The six-primitive IJB ontology
   lacks the precision of W3C PROV (Entity/Activity/Agent). Overloading a
   `thing` to act as both passive data and active agent will lead to broken
   traceability chains.
4. **TOML Verbosity and Lack of `$ref`:** Representing deeply nested,
   DAG-shaped semantic graphs in TOML will result in unreadable
   arrays-of-tables.
5. **The Critical Path Fallacy:** Defining `critical_path` via simple graph
   weights (CPM) is fundamentally incompatible with the non-deterministic
   reality of AI agents, which are heavily resource- and context-constrained.
6. **Ontology Drift:** Separating the textual rules of `KD1-KD3` from the
   execution logic ensures they will drift.

## RECOMMENDATIONS

1. **Adopt a Multi-Language Validation Baseline:** Immediately generate a
   baseline JSON Schema (or CUE/SHACL equivalent) for the structural parsing
   of the TOML files.
2. **Shift from Provenance to Behavioral Receipts:** Update
   `assertion-log-record` and `gate-decision` to require cryptographic
   linking (e.g., `prev_receipt_id`) and runtime context.
3. **Clarify the Agent/Activity Divide in IJB:** Explicitly define how the
   IJB ontology maps to W3C PROV.
4. **Deprecate CPM "Critical Path" Metrics:** Replace with probabilistic
   (PERT) or resource-constrained (CCPM) metadata fields.
5. **Implement Content-Hashing for Kind-Descriptors:** Borrow from `clayers`
   and `spec-schema` by requiring that the Python validators verify a
   content hash of the `*-kind.toml` prose.
6. **Mandate the "Two Implementations" Rule:** Halt the finalization of the
   spec until the hard invariants have been successfully written and tested
   in a second, statically typed language (e.g., Rust or Go).
