# Claude's own Exa searches — key URLs and findings

These are the targeted Exa searches Claude ran in parallel with the three
delegated agents and the Exa Deep Researcher. They cover overlapping ground
to provide independent verification of points raised by the other streams.

## 1. TOML spec design

- [Schema definition · toml-lang/toml issue #629](https://github.com/toml-lang/toml/issues/629)
  — TOML maintainers explicitly reject in-band schema validation; XSD-like
  side documents are the recommended path.
- [brunoborges/toml-schema](https://github.com/brunoborges/toml-schema) —
  TOML-in-TOML schema proposal; demonstrates the form but acknowledges the
  validation ecosystem doesn't exist.
- [Documenting how to validate TOML with JSON schema](https://github.com/toml-lang/toml/discussions/1038)
  — Confirms TOML-to-JSON mapping issues (null, NaN, Inf, date formats).
- [Backward Compatibility | TOML/DeepWiki](https://deepwiki.com/toml-lang/toml/4.3-backward-compatibility)
  — TOML 1.x backward-compat discipline; additive-only changes.
- [TOML Explained: The Config Format That's Replacing YAML](https://codetidy.dev/blog/what-is-toml)
  — Explicitly lists TOML limitations: no schema language, less ecosystem
  support, not great for data interchange.
- [tomlval v1.0.0](https://pypi.org/project/tomlval/1.0.0/) — Example of
  Python-only TOML validator pattern.

## 2. AI provenance / attestation formats

- [draft-kamimura-vap-framework-00 (IETF)](https://datatracker.ietf.org/doc/draft-kamimura-vap-framework/00/)
  — Verifiable AI Provenance Framework; maps the IETF stack (SCITT, RATS,
  EAT, COSE) to AI provenance layers.
- [AI Provenance Formats landscape (Invariant Systems)](https://invariantsystems.io/landscape)
  — Side-by-side of AIIR, in-toto, SLSA, SPDX, CycloneDX, Sigstore.
- [Provenance Tracking — TAILOR Handbook of Trustworthy AI](https://prafra.github.io/jupyter-book-TAILOR-D3.2/Accountability/L3.Provenance_tracking.html)
  — Discusses PROV-O, P-PLAN, OPMW as backbones for AI provenance.
- [SLSA vs in-toto vs Sigstore: Attestation Compared](https://safeguard.sh/resources/blog/software-attestation-framework-comparison)
  — Clarifies the layered relationship: in-toto defines the format, SLSA
  defines build provenance, Sigstore is the signing/verification layer.
- [AI Bill of Materials (AI-BOM): Standards and Tooling in 2026](https://aicompliancevendors.com/guides/ai-bom-tools)
  — Maps CycloneDX ML-BOM and SPDX 3.0 AI Profile to EU AI Act Annex IV.
- [Agentic AI Compliance 2026: One Enforcement Layer](https://agenticrail.nz/resources/ai-governance-frameworks-2026/)
  — Notes that EU AI Act Art. 12, ISO 42001 A.6.1.6, and NIST RMF MEASURE
  2.5 all converge on cryptographic receipts for gate decisions.

## 3. Ontology drift, schema bloat, ontology failure modes

- [Do You Need An Upper Ontology? (Kurt Cagle, 2026-05)](https://ontologist.substack.com/p/do-you-need-an-upper-ontology)
  — Recent essay: "Every effort to create an upper ontology that serves
  both as a precise computational foundation and as a broad interoperability
  framework has either failed outright or survived by becoming so general
  as to require substantial domain-specific work to make it useful."
- [Ontology Evolution: Not the Same as Schema Evolution (Noy 2004)](https://scispace.com/papers/ontology-evolution-not-the-same-as-schema-evolution-nd3gy6o1ib)
  — Foundational paper; ontology versioning has dimensions schema versioning
  doesn't.
- [Linked Data Schemata: A Decentralized Vocabulary Lifecycle](https://doras.dcu.ie/22976/1/SemanticWebJournal2018Linked%20data%20schemata-v9.pdf)
  — 33% of surveyed ontologies contain ontology-hijacking violations; 12%
  contain dangling dependencies on missing ontologies.
- [Feasibility of Automated Foundational Ontology Interchangeability](https://link.springer.com/chapter/10.1007/978-3-319-13704-9_18)
  — SUGOI tool, DOLCE/BFO/GFO interchange experiments at 2-82%, avg 36%.
- [Ontological Anti-Patterns (Guizzardi et al.)](https://www.sciencedirect.com/science/article/abs/pii/S0169023X15000373)
  — Empirically uncovered error-prone modeling structures in
  ontology-driven conceptual models.
- [A Comparison of Upper Ontologies (Mascardi)](http://woa07.dibris.unige.it/papers/mascardi.pdf)
  — Detailed seven-way comparison.
- [How Enterprise Ontologies Decay (Alation, 2026-04)](https://www.alation.com/blog/living-ontologies-enterprise-ai/)
  — "The ontology you ship on day one is already drifting by day thirty."

## 4. DAG traceability and critical-path

- [X-RMTV: Integrated Requirement Modeling, Traceability, Verification](https://www.mdpi.com/2079-8954/12/10/443)
  — 10 types of requirement relationships; algorithm for trace path
  generation.
- [How to Analyze Requirements Traceability in Neo4j](https://www.reqview.com/blog/requirements-traceability-analysis-neo4j/)
  — Practical pattern: traceability graphs in graph databases enable
  consistency checks.
- [5 reasons why a requirements traceability matrix is not enough](https://blogs.itemis.com/en/5-reasons-why-a-requirements-traceability-matrix-is-not-enough)
  — Manual RTMs deteriorate; need automated propagation.
- [Finding the critical path (Lattice)](https://blog.thelattice.in/readme/finding-the-critical-path)
  — Detailed walkthrough of Bellman-Ford-based critical path; weight
  assignment pitfalls.
- [Longest Path in a DAG: A Practical Guide](https://thelinuxcode.com/longest-path-in-a-directed-acyclic-graph-dag-a-practical-guide-for-real-systems/)
  — Topological sort + DP; cycle detection essential; edge-weight semantics
  must be explicit.

## 5. Self-describing schemas, kind-descriptor patterns

- [The Schema Language Question (Charlie Holland)](https://www.chiply.dev/post-schema-languages)
  — Comparative map of Avro/JSON Schema/Protobuf/CUE/Dhall trade-offs.
- [The Logic of CUE](https://cuelang.org/docs/concept/the-logic-of-cue/) —
  Values, types, and constraints in one lattice; backwards-compatibility
  decidable.
- [Schema Definition use case | CUE](https://cuelang.org/docs/concept/schema-definition-use-case/)
- [Descriptors - Buf Docs](https://buf.build/docs/reference/descriptors/) —
  ProtoBuf descriptors are file-centric; the file-vs-type impedance is a
  known foot-gun.
- [Schema evolution in Avro, Protocol Buffers and Thrift (Kleppmann 2012)](https://martin.kleppmann.com/2012/12/05/schema-evolution-in-avro-protocol-buffers-thrift.html)
  — Canonical guide to schema-evolution semantics in three systems.
- [grafana/thema README](https://github.com/grafana/thema/blob/main/README.md)
  — Schema *change* as a first-class system property; "lineages" of
  iteratively appended schemas.

## 6. Spec-design failure modes

- [W3C Recommendation Track Readiness Best Practices](https://www.w3.org/guide/standards-track/)
  — Incubation; market need; rough consensus before charter.
- [W3C Process - Recommendation Track](https://www.w3.org/2003/06/Process-20030618/tr)
  — "Two independent and interoperable implementations" guidance.
- [RFC 7282: On Consensus and Humming in the IETF](https://www.rfc-editor.org/rfc/rfc7282)
  — Canonical "rough consensus and running code" document.
- [Hyrum's Law](https://www.hyrumslaw.com/) — Canonical statement.
- [Database Decay and How to Avoid It](https://people.cs.rutgers.edu/~dd903/assets/papers/bigdata16.pdf)
  — Real-world DBA practice diverges sharply from "3NF then evolve" theory.
- [Datomic - The Ten Rules of Schema Growth](https://blog.datomic.com/2017/01/the-ten-rules-of-schema-growth.html)
  — Growth vs. breakage as a top-level distinction.

## 7. UFO / fact-based modeling / REA depth

- [UFO Story (Guizzardi)](https://inf.ufes.br/~gguizzardi/UFO-Story.pdf) —
  How UFO got built; emphasis on relators, qua individuals, roles as
  anti-rigid types.
- [Role Modeling: The Problem of Disjoint Allowed Types](https://nemo.inf.ufes.br/wp-content/papercite-data/pdf/the_role_of_foundational_ontology_for_conceptual_modeling_and_domain_ontology_representation_2006.pdf)
  — Why encoding roles as scopes loses essential semantics.
- [FCO-IM Home](http://fco-im.nl/) — Fact expressions; 100%
  conceptualization principle.
- [REA Ontology Foundation (Geerts & McCarthy)](https://www.researchgate.net/publication/228583572_The_Ontological_Foundation_of_REA_Enterprise_Information_Systems)
  — Resource/Event/Agent + duality axioms.

## 8. AI governance / attestation / gate gaming

- [Attestable Audits (arXiv 2506.23706)](https://arxiv.org/pdf/2506.23706)
  — TEE-based audit; addresses verification challenges.
- [Robust ML Auditing using Prior Knowledge (ICML 2025)](https://proceedings.mlr.press/v267/garcia-bourree25a.html)
  — Formal proof that audits relying on public priors can be fooled by
  platform manipulation.
- [Strategic Auditee Gaming Under Continuous Compliance Monitoring](https://arxiv.org/html/2605.06340)
  — Continuous auditing as a T-round Stackelberg game; cover-regime
  impossibility.
- [Declaration to Proof - Cryptographic Governance Evidence](https://attestedintelligence.com/diligence/declaration-to-proof)
  — Sealed artifacts, signed receipts, evidence bundles verifiable offline.
- [AI Attestation: Cryptographic Compliance Evidence (GLACIS)](https://www.glacis.io/guide-ai-attestation)
  — Maps to EU AI Act Art. 12 logging requirements.
- [Governance-Aware Agent Telemetry (GAAT, arXiv 2604.05119)](https://arxiv.org/html/2604.05119v1)
  — Closes the telemetry-to-enforcement loop with OPA-compatible rules,
  sub-200ms latency.
