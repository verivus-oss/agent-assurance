# Grok (grok-build) independent research report

Run via `llm-gateway` with the `exa` MCP server enabled, always-approve mode.
Identical context block as the other agents. Output below is verbatim.

---

**External Research Report: DAG-TOML Specification Design and IJB
Primitives — Independent Analysis via Exa MCP Searches**

This report draws exclusively from 12+ targeted external searches and page
fetches via the Exa MCP server (web_search_exa, web_search_advanced_exa,
web_fetch_exa, plus parallel queries on foundational ontologies, TOML usage,
self-describing schemas, AI governance frameworks, spec anti-patterns, and
DAG build systems). No local repository content was inspected. Searches
spanned philosophical upper ontologies, configuration-language design,
supply-chain attestation systems, and graph-based engineering practices.
Citations are real, publicly retrievable URLs with one-line annotations.

## 1. IJB Primitives Prior Art — The Six-Primitive Cut

Upper ontologies developed over decades reveal that a six-primitive
engineering taxonomy is a radical simplification rather than a natural
convergence. BFO (Basic Formal Ontology) centers on a SNAP/SPAN
(continuant/occurrent) and independent/dependent continuant split, with
roles, qualities, and fiat parts; it is realist and reductionist. DOLCE
(Descriptive Ontology for Linguistic and Cognitive Engineering) uses
endurant/perdurant/quality/abstract plus time-indexed mereology and is
explicitly descriptive/cognitive. SUMO offers a much larger lattice
(~1000 terms) mixing universals and particulars. UFO layers endurants
(UFO-A), perdurants (UFO-B), and intentional/social entities (UFO-C) with
rigidity, anti-rigidity, and moment universals. Bunge-Wand-Weber (BWW)
starts from "things" possessing properties that participate in systems
under natural laws; later critiques note it lacks constructs for
institutional or intentional objects. Situation calculus and event calculus
treat situations/fluents/events or time-periods/events/fluents as primitives
for action and change, foregrounding the frame problem and narrative time.
W3C PROV reduces to Entity/Activity/Agent plus derivation, generation,
usage, and time-stamped relations — three core classes, not six.

The IJB set (thing/scope/path/observed/constraint/time) plus
structural/instance class markers sits closest to lightweight
systems-engineering or method-engineering taxonomies rather than any of the
above. It risks category collapse: "thing" elides BFO's independent/
dependent and DOLCE's endurant/perdurant distinctions; "scope" and "path"
are introduced without axiomatized parthood, dependence, or
spatial-temporal location theories that the philosophical ontologies treat
as foundational; "observed" and "constraint" straddle the observed vs.
structural line that DOLCE and UFO separate carefully. No prior ontology
uses exactly this sextet; attempts to force-fit it will produce the same
alignment failures documented between BFO/DOLCE/GFO/SUMO (low equivalence
rates, 2–82 % in automated interchange experiments). The design is
engineering-pragmatic but philosophically under-motivated.

**Cited sources:**

- http://woa07.dibris.unige.it/papers/mascardi.pdf — Detailed side-by-side
  of DOLCE vs. BFO vs. SUMO commitments.
- http://www.loa.istc.cnr.it/wp-content/uploads/2020/02/FoundationalChoicesBorgoMasoloPUB.pdf
  — DOLCE-core six-category temporal-particulars analysis.
- https://www.w3.org/TR/prov-dm/ and https://www.w3.org/TR/prov-o/ — PROV's
  minimal Entity/Activity/Agent + time/derivation model.
- https://arxiv.org/pdf/2308.01597 — Modern DOLCE re-examination.
- https://eprints.qut.edu.au/11093/ and
  https://link.springer.com/article/10.1007/s10270-008-0082-3 — BWW core
  and later systemist extensions/critiques.
- https://www-formal.stanford.edu/jmc/sitcalc.pdf and
  http://www.doc.ic.ac.uk/~rak/papers/event%20calculus.pdf — Situation vs.
  event calculus primitives.

## 2. TOML-Based Spec Design

TOML succeeded as a human-first configuration language precisely because it
is deliberately limited: unambiguous mapping to hash tables, no top-level
arrays, strict key uniqueness, UTF-8 only, and a small type set.
pyproject.toml (PEP 621) demonstrates the canonical pattern for spec
evolution inside TOML: a small normative core
(`[build-system]`, `[project]`, `[tool.*]` namespace) plus an explicit
"dynamic" list for fields that back-ends may later fill, plus JSON-Schema
sidecars for illustration and validate-pyproject enforcement. Cargo.toml
keeps `[package]` at the top, sorts keys conventionally, reserves
`[package.metadata]` and `[workspace.metadata]` as arbitrary tool space that
Cargo itself ignores, and documents that external tools must not rely on
Cargo's parser for their own keys. TOML 1.0+ froze syntax for backward
compatibility; pre-1.0 churn taught the cost of evolving the grammar itself.

Pitfalls repeatedly observed: (1) TOML has no native schema or versioning
story — authors therefore bolt on external JSON Schema (Taplo supports
`$schema` directives, catalog lookup, and per-rule formatting) or Python
validators; (2) complex nested or streaming data is painful (no top-level
arrays, no streaming); (3) dotted keys and table/array-of-tables
interactions create ordering and redefinition foot-guns; (4) once a large
corpus exists, Hyrum-style implicit interfaces appear around formatting,
key ordering, and which subsets of TOML a given tool actually tolerates.
Projects that stay small and pair TOML with an external validator (Taplo +
JSON Schema, or Python tomllib + custom rules) fare best. Just (justfile)
and dprint-plugin-toml show that even command-runner and formatter authors
treat TOML as "nice syntax, validate elsewhere."

**Cited sources:**

- https://packaging.python.org/en/latest/specifications/pyproject-toml/ —
  PEP 621 design.
- https://doc.rust-lang.org/nightly/cargo/reference/manifest.html and
  https://doc.rust-lang.org/style-guide/cargo.html — Cargo manifest
  conventions.
- https://toml.io/en/v1.1.0 and
  https://github.com/toml-lang/toml/blob/main/toml.md — Official spec.
- https://taplo.tamasfe.dev/ and
  https://taplo.tamasfe.dev/configuration/using-schemas.html — Taplo schema
  directives.
- https://github.com/casey/just — justfile as another real-world
  TOML(ish) configuration surface.

## 3. Kind-Descriptor / Self-Describing-Schema Patterns

Self-describing mechanisms fall into two families: in-band (JSON-LD
`@context`, ProtoBuf FileDescriptor, CUE definitions that are also values)
and out-of-band (SHACL shapes, OpenAPI components/schemas, Dhall types
imported separately). CUE is the most interesting modern example: types
and values unify, order-independent unification replaces inheritance, and
it can both consume and emit OpenAPI/ProtoBuf/JSON Schema while being
strictly more expressive (closed structs, comprehensions, injection).
OpenAPI's components.schemas and ProtoBuf descriptors work well inside
their ecosystems but suffer conversion loss and the "lowest common
denominator" problem when round-tripped. SHACL is deliberately post-hoc
shapes, not self-describing data; mixing it with OWL frequently produces
the reification and predicate-vs-event modeling debt described in recent
analyses.

Common failure modes:

- circular or version-skewed self-description (a context or descriptor that
  itself depends on the instance it describes);
- expressivity cliffs — once you outgrow the host language you must subset
  or escape (OWL profiles, structural OpenAPI subsets for CRDs);
- tooling that silently drops extension fields or annotations, turning
  "self-describing" into "mostly describing";
- drift between the descriptor document and the validator that actually
  runs in CI.

Kind-descriptor files in TOML would inherit the same risks unless paired
with an independent validator that also consumes the descriptors themselves.

**Cited sources:**

- https://cuelang.org/docs/introduction/ and
  https://cuelang.org/docs/concept/how-cue-works-with-openapi/ — CUE's
  unified schema+data model and OpenAPI/ProtoBuf interop.
- https://www.w3.org/TR/shacl/ — SHACL.
- https://www.chiply.dev/post-schema-languages — Comparative map of schema
  languages.
- https://www.w3.org/TR/json-ld11/ — JSON-LD context mechanism.

## 4. Agent Assurance / AI Agent Governance Specs

The mature provenance and supply-chain lineage (W3C PROV → in-toto → SLSA
provenance predicates, SPDX/CycloneDX SBOMs, G7 AI SBOM guidance) has been
rapidly grafted onto AI/agent governance. NIST AI RMF (Govern/Map/Measure/
Manage) is voluntary and outcome-oriented; ISO/IEC 42001 supplies a
certifiable AI management system (AIMS) with Annex A controls; the EU AI
Act imposes hard obligations on high-risk and GPAI systems (data
governance, transparency, human oversight, post-market monitoring). SLSA +
in-toto + Sigstore/DSSE now ships by default in GitHub Actions and npm; G7
work explicitly calls for SBOMs that include model provenance and
training-data sourcing.

Documented failure modes are already visible in production. SLSA attests
the build pipeline, not the semantic safety or intent of the artifact; the
2026 "Mini Shai-Hulud" npm worm carried valid SLSA L3 provenance because
the compromise occurred inside the trusted runner after OIDC token theft.
SBOMs for AI remain incomplete for weights, fine-tuning data, and agent
tool graphs; G7 guidance itself notes that autonomy level is future work.
Evidence fatigue is reported when every step (build, test, SBOM generation,
VEX, VSA) produces another signed envelope that downstream policy engines
must evaluate. Gate gaming appears when projects optimize for the minimal
attestation that passes the verifier rather than the substantive control.
Over-attestation without corresponding runtime policy enforcement (OPA/Rego
or equivalent) simply shifts the attack surface to the policy layer and
the verifier's root of trust.

**Cited sources:**

- https://www.nist.gov/itl/ai-risk-management-framework and
  https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf — NIST AI RMF.
- https://slsa.dev/spec/v1.2/build-provenance — Current SLSA provenance.
- https://slsa.dev/blog/2022/04/slsa-is-no-free-lunch and
  https://lyrie.ai/research/research/2026-05-12-slsa-provenance-paradox —
  Real-world demonstration that provenance verifies pipeline, not content.
- https://industrialcyber.co/sbom/cisa-g7-partners-release-sbom-for-ai-guidance-to-boost-ai-supply-chain-transparency-and-cybersecurity-resilience/
  — G7 AI SBOM minimum elements.
- https://www.w3.org/TR/prov-dm/ — Foundational provenance model.

## 5. Spec-Design Failure Modes

Hyrum's Law ("with enough users, the implementation becomes the
interface") is already observable in every widely adopted specification
language. OWL's history is the textbook case of bloat: OWL 1 Full was
undecidable in practice; OWL 2 introduced profiles (EL, QL, RL) and a new
Functional syntax precisely because users and tool authors could not live
with the full expressivity or the RDF serialization pain. Alignments
between BFO/DOLCE/GFO/SUMO routinely achieve low equivalence and require
both equivalence and subsumption mappings; automated interchange tools
report 36 % average success. IETF "rough consensus and running code"
(RFC 7282) deliberately privileges "humming" and addressed minority
objections over simple majorities; it works for protocols with running
code but produces glacial or ambiguous results for purely declarative
artifacts. W3C's "two independent implementations" CR-exit rule guarantees
syntactic interop but has not prevented semantic drift or profile
fragmentation.

The recurring pattern for self-describing or ontology-heavy specs is that
the descriptive apparatus itself becomes a source of drift and maintenance
cost. Once the kind-descriptor or ontology file is more complex than the
instances it governs, the cost of keeping them synchronized exceeds the
benefit for most contributors.

**Cited sources:**

- https://www.hyrumslaw.com/ — Canonical statement.
- https://www.sciencedirect.com/science/article/abs/pii/S1570826808000413
  and https://www.cs.ox.ac.uk/boris.motik/pubs/ghmppss08next-steps.pdf —
  OWL 1→2 expressivity and syntax problems.
- https://datatracker.ietf.org/doc/html/rfc7282 — IETF rough-consensus
  mechanics.
- https://www.w3.org/TR/rdf12-semantics/ and
  https://www.w3.org/TR/owl2-profiles/ — Ongoing attempts to manage the
  consequences of prior over-expressivity choices.

## 6. DAG-Shaped Traceability

Build systems (Bazel, Pants, Buck, Dagger) treat the declared dependency
graph as an over-approximation of the actual DAG; the build is only sound
when actual ⊆ declared. Topological sort (Kahn's algorithm) and cycle
detection are non-negotiable; Bazel's Skyframe and Pants both surface
cycles as hard errors because a cycle means "no legal build order exists."
Critical-path analysis (longest weighted path through the DAG) is exactly
the PERT/CPM notion repurposed for incremental builds: Bazel
`query maxrank` surfaces the longest chain so humans can see what dominates
wall time. PROV derivation chains and in-toto supply-chain graphs are also
DAGs; cycles would indicate impossible causal histories.

Anti-patterns observed in practice:

1. undeclared or implicit dependencies (Bazel's "actual vs. declared"
   checks exist precisely because humans forget);
2. cycles introduced by mutual module coupling or accidental self-reference
   in large refactored monorepos;
3. transitive bloat that turns the critical path into a critical morass;
4. treating the DAG as documentation rather than enforceable contract —
   once the graph is only advisory, drift is immediate.

Software traceability papers that model requirements-to-code-to-test as a
DAG inherit the same topological and critical-path mathematics; any spec
that claims "traceability" without enforcing acyclicity and
declared-vs-actual correspondence is repeating a 40-year-old lesson.

**Cited sources:**

- https://bazelbuild.github.io/bazel/site/en/concepts/dependencies.html and
  https://bazel.build/query/guide — Bazel's explicit declared-dependency
  DAG contract.
- https://github.com/bazelbuild/bazel/issues/12204 — Cycle handling
  discussion.
- https://ocw.mit.edu/courses/6-042j-mathematics-for-computer-science-spring-2015/mit6_042js15_session17.pdf
  — Formal DAG, chain, antichain, and critical-path definitions.
- https://slsa.dev/spec/v1.2/build-provenance — SLSA provenance as a
  causal DAG.

---

## TOP RISKS FOR THIS SPEC

- The six-primitive ontology is a novel engineering cut with no established
  precedent; alignment failures with BFO/DOLCE/UFO/BWW are likely.
- TOML + external Python validators create a single point of failure.
- Self-describing kind descriptors in TOML will be subject to Hyrum's Law.
- SLSA/in-toto-style attestations verify pipeline, not intent or content.
- Evidence volume from multi-layer attestations will produce compliance
  theater and reviewer fatigue unless aggressive trimming/VSA mechanisms
  are mandatory.
- DAG enforcement is only as strong as the validator.
- Ontology drift between core/ and profiles/agent-assurance/ is almost
  inevitable without continuous cross-validation tooling.
- "Gate gaming" is the rational response of any organization measured on
  the existence of artifacts rather than on the substantive safety those
  artifacts are supposed to demonstrate.

## RECOMMENDATIONS

- Treat the six primitives as a pragmatic starting vocabulary, not an
  upper ontology; publish explicit mapping tables to BFO/DOLCE/UFO and
  document the collapses and extensions required.
- Make the Python validators (not the TOML text) the normative enforcement
  layer; require that every kind descriptor be consumed by the validator
  in CI before any example may be added.
- Add mandatory critical-path and cycle checks (or reuse existing DAG
  libraries) to the implementation-dag and traceability validators.
- Require that every attestation or assertion bundle used for "agent
  assurance" be accompanied by a machine-checked policy (Rego or
  equivalent) that actually consumes the attestation; unsigned or
  unpolicy-checked artifacts must be rejected at the verifier.
- Introduce explicit "VSA-style" trimming and inheritance for deployment
  tiers.
- Version the ontology and schema independently but require that any bump
  to `ontology_version` triggers a full re-validation of all kind
  descriptors and canonical examples.
- Publish a "threat model for the spec itself" (who can game the gates,
  who benefits from evidence inflation, how drift occurs).
- Before claiming production readiness for agentic systems, run red-team
  exercises that attempt to produce passing artifacts for knowingly unsafe
  or incorrect agent behavior; treat any success as a spec defect, not an
  implementation defect.

This research indicates that the DAG-TOML + IJB approach is a coherent
engineering response to a real problem, but it inherits every classic
failure mode of self-describing specifications, lightweight ontologies, and
attestation-based governance. Success will depend less on the elegance of
the six primitives than on the rigor and independence of the enforcement
tooling and the willingness to treat gaming and drift as first-class
threats.
