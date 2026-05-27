# Codex (gpt-5.5) independent research report

Run via `llm-gateway` with the `exa` MCP server enabled, sandbox mode
read-only, reasoning effort high. Codex did 18 Exa searches.

Identical context block as the other agents. Output below is verbatim.

---

I did not inspect the local repo. I used external Exa research across
ontology, TOML specs, schema self-description, assurance frameworks, spec
governance, and DAG scheduling/traceability.

## 1. IJB Primitives Prior Art

A six-primitive ontology of `thing | scope | path | observed | constraint |
time` has precedent only in the broad sense that upper ontologies try to keep
top-level categories small. It does not map cleanly to the dominant prior
art. BFO separates continuants from occurrents and is careful about
type-vs-instance and time-indexed relations; DOLCE/SUMO take different
upper-level commitments; W3C PROV centers provenance on entity, activity, and
agent; Bunge-Wand-Weber uses thing/property/state/event/transformation-like
modeling categories. See BFO discussion in
[Smith's BFO paper](https://philpapers.org/archive/SMIOCM.pdf),
BFO time notes in
[BFO OWL-Time material](https://github.com/BFO-ontology/BFO/blob/master/docs/OWL-TIME/bfo-owl-time-introduction.tex),
BWW critique in [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=951803),
and PROV in [W3C PROV-DM](https://www.w3.org/TR/2013/REC-prov-dm-20130430/Overview.html).

The main risk is category collapse. `thing` can absorb artifacts, agents,
assertions, files, plans, and institutional objects. `observed` is epistemic,
not ontological. `constraint` is normative or logical. `path` can mean graph
edge, filesystem path, derivation chain, or proof route. `scope` can mean
context, namespace, boundary, or authorization domain. `time` can be instant,
duration, ordering, version, or lifecycle phase. That mixture can be useful
pragmatically, but it should not be sold as a clean upper ontology. It is
closer to a disciplined annotation scheme.

The `ijb_class = structural | instance` marker echoes type/instance
distinctions, but BFO's strictness is a warning: if class markers are
attached uniformly to entities, relations, and attributes, users may infer
stronger semantics than validators actually enforce.

## 2. TOML-Based Spec Design

TOML is a strong choice for human-authored configuration and a risky choice
for large normative graph specifications. The TOML spec emphasizes readable
config, unambiguous mapping to hash tables, no duplicate keys, typed scalar
values, arrays, and tables; it also says comments are non-semantic. That is
useful discipline, but TOML has no native identity system, no imports, no
references, no constraints language, no null, and awkward ergonomics for
deeply nested graph data. See [TOML v1.1](https://toml.io/en/v1.1.0).

Cargo and pyproject are the most relevant success cases. Cargo shows the
importance of explicit versioning, compatibility behavior, warning on unknown
or misspelled fields, and careful migration when old clients encounter new
metadata; see Cargo's index schema versioning discussion in
[rust-lang/cargo#9161](https://github.com/rust-lang/cargo/pull/9161).
`pyproject.toml` shows the value of reserved tables, tool namespaces,
static-vs-dynamic metadata, and clearly owned extension areas; see the
[pyproject specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/).

Taplo shows the tooling lesson: TOML itself is not enough for editor
feedback, validation, completion, or schema association. Taplo leans on JSON
Schema for that layer, with schema-assignment rules and editor integration,
documented in [Taplo schema usage](https://taplo.tamasfe.dev/configuration/using-schemas.html)
and [Taplo schema development](https://taplo.tamasfe.dev/configuration/developing-schemas.html).

If DAG-TOML intentionally has no JSON Schema layer, then Python validators
are effectively normative. That is acceptable only if validator behavior,
canonicalization, diagnostics, version handling, and conformance fixtures
are treated as part of the spec.

## 3. Kind Descriptors And Self-Describing Schemas

Kind-descriptor files resemble several self-description systems, but each
prior art carries warnings. JSON-LD contexts map local terms to global IRIs,
but remote contexts can change, disappear, leak access patterns, or create
processing ambiguity; see the [JSON-LD API](https://json-ld.github.io/json-ld.org/spec/latest/json-ld-api/)
and [Remote contexts considered harmful](https://iolanta.tech/articles/remote-contexts-considered-harmful/).
SHACL makes graph constraints explicit, but inference, recursion, entailment
assumptions, and validation complexity can surprise implementers; see
[SHACL 1.2 Core](https://www.w3.org/TR/shacl12-core/).

OpenAPI components and `$ref` reduce duplication but often create codegen,
splitting, naming, and round-trip fidelity problems. Guidance like
[OpenAPI Done Right](https://www.caduh.com/blog/openapi-done-right) stresses
treating the spec as a contract, linting it, diffing it, and avoiding
uncontrolled free-form structures. ProtoBuf is a useful counterexample: it
works because field numbers, reserved fields, unknown-field behavior, and
compatibility rules are extremely disciplined; see
[Protocol Buffers proto3](https://developers.google.com/protocol-buffers/docs/proto3).

CUE and Dhall are also relevant. CUE unifies values, schemas, and
constraints with a normalization model; see [CUE introduction](https://cuelang.org/docs/introduction).
Dhall uses typed programmable configuration with normalization and import
integrity; see [Dhall programmable configuration](https://docs.dhall-lang.org/discussions/Programmable-configuration-files.html).

For DAG-TOML, KD1-KD3 rules should remain intentionally boring. The danger
is creating a mini ontology language whose prose, descriptors, validators,
and examples all drift apart.

## 4. Agent Assurance And Governance Specs

The Agent Assurance Profile sits in the same design space as provenance,
supply-chain attestation, and AI governance, but it needs stricter
anti-gaming semantics than ordinary documentation. W3C PROV separates
entities, activities, and agents, which is useful for modeling who did what,
using which inputs, at what time; see
[W3C PROV-DM](https://www.w3.org/TR/2013/REC-prov-dm-20130430/Overview.html).
SLSA provenance is even closer: it ties attestations to artifacts, builders,
build definitions, external parameters, dependencies, and verification
expectations; see [SLSA build provenance](https://slsa.dev/spec/v1.2/build-provenance).

AI governance frameworks add another layer. NIST AI RMF, ISO/IEC 42001, and
the EU AI Act emphasize risk management, documentation, logging,
transparency, human oversight, robustness, incident handling, and
post-market monitoring. A useful comparison is
[EU AI Compass's ISO 42001 / NIST AI RMF / EU AI Act mapping](https://euaicompass.com/iso-42001-nist-ai-rmf-eu-ai-act-mapping.html).
Operational ISO 42001 failure modes include treating AI risk as a generic
security checklist, weak impact assessments, missing competence evidence,
and empty corrective-action loops; see
[Lorikeet's ISO 42001 discussion](https://lorikeetsecurity.com/blog/iso-42001-ai-management-system-2026).

The skeptical point: assurance artifacts can become performative.
`assertion-bundle`, `assertion-log-record`, and `gate-decision` are valuable
only if they bind to immutable artifacts, independent verifier identity,
policy version, evidence quality, and explicit failure modes. If the same
agent generates the plan, evidence, assertion, and pass/fail decision, the
profile risks over-attestation and gate gaming.

## 5. Spec-Design Failure Modes

Hyrum's Law is central here: with enough users, every observable behavior
becomes a dependency, even if the spec disclaims it. Validator quirks,
example formatting, warning text, sort order, and permissive parsing can
become the real standard. See [Hyrum's Law](https://www.laws-of-software.com/laws/hyrum/).

The "rough consensus and running code" tradition is also relevant. Specs
harden best when independent implementations expose ambiguity before the
document freezes; see [RFC 3929](https://www.rfc-editor.org/rfc/rfc3929.txt).
The web platform's design principles also stress compatibility, graceful
failure, and simple solutions over clever abstractions; see
[W3C Web Platform Design Principles](https://www.w3.org/TR/design-principles/).

Ontology systems provide the negative examples. OWL/RDF's open-world
semantics often conflict with users' closed-world validation expectations:
absence of a fact is not falsity, and domain/range declarations are not
ordinary schema constraints. That mismatch is discussed in
[Open World Assumption considered harmful](https://douroucouli.wordpress.com/2020/09/04/the-open-world-assumption-considered-harmful/).
DAG-TOML's Python validators are probably closed-world, which is good, but
the spec should say that directly.

The likely failure mode is schema bloat plus ontology drift. Each new
optional field appears harmless, but users will encode workflows around it.
Each primitive gains local interpretations. Each validator release quietly
changes the operational meaning. Without conformance tests and independent
producers/consumers, the "spec" becomes whatever the reference validator
happens to accept.

## 6. DAG-Shaped Traceability

DAG traceability is a strong foundation only when relation types are kept
separate. Project scheduling literature uses DAGs for precedence constraints
and critical path analysis: tasks are nodes, dependencies are directed
edges, and the critical path is the longest weighted path through an acyclic
graph. See Neo4j's discussion of
[DAG critical path analysis](https://neo4j.com/blog/developer/dags-neo4j-critical-path-analysis),
Lattice's warning about
[critical path calculation pitfalls](https://blog.thelattice.in/readme/finding-the-critical-path.md),
and CPM/PERT discussion in [IJSRSET](https://ijsrset.com/IJSRSET24118029).

The hard invariants listed for DAG-TOML are good: `blocks` as inverse of
`depends_on`, exactly one producer per ART, and computed longest weighted
critical path. But they are also fragile. `depends_on` should be the
authoritative edge; `blocks` should be derived or mechanically checked, not
independently authored. "Exactly one producer" is clean for build artifacts,
but real assurance evidence often has multiple contributors, reviewers,
signers, or verifiers. Those roles should not be forced into producer
semantics.

Critical path is meaningful only if weights represent comparable quantities
such as duration, effort, or risk cost. If weights mix confidence, severity,
execution time, and review burden, the longest path becomes decorative.
Also, traceability links are not necessarily scheduling dependencies.
Evidence-supports-claim, adapter-implements-contract,
test-validates-requirement, and task-depends-on-task may form different
graphs with different acyclicity rules.

The anti-pattern is turning every relation into one global DAG. Some
assurance structures are cyclic over time because work iterates. Model
iterations as versioned nodes, not literal cycles.

## TOP RISKS

- The six IJB primitives mix ontological, epistemic, normative, temporal,
  and navigational categories, which can create subtle category errors.
- Python validators may become the hidden normative spec, especially if
  prose, examples, and implementation behavior diverge.
- Kind descriptors can drift from prose and validators unless there is a
  canonical generated form and conformance suite.
- Assurance artifacts may encourage over-attestation: lots of
  evidence-shaped files with weak connection to actual risk reduction.
- Gate decisions are gameable if the same agent can generate the work,
  evidence, assertions, and pass/fail rationale.
- TOML may become strained by cross-file identity, graph references,
  versioning, and large nested structures.
- `critical_path` can create false confidence if edge meanings or weights
  are not tightly constrained.
- Lack of independent implementations will let accidental reference-
  validator behavior harden into the de facto standard.

## RECOMMENDATIONS

- Define each IJB primitive with forbidden uses and category-error examples,
  not just positive examples.
- Treat the Python validator, canonical normalization rules, and conformance
  fixtures as normative parts of the spec.
- Make derived fields truly derived where possible: compute `blocks` and
  `critical_path`, or require exact validator verification.
- Version every kind descriptor and profile with explicit compatibility
  rules, reserved namespaces, and unknown-field behavior.
- Bind assurance records to immutable artifact identifiers, verifier
  identity, policy version, timestamps, and trust boundaries.
- Keep TOML conservative: no semantic comments, no mutable remote imports,
  stable IDs, deterministic ordering, and clear extension tables.
- Require at least two independent producer/consumer implementations before
  declaring core invariants stable.
- Red-team the assurance profile specifically for gate gaming, evidence
  fatigue, and plausible-but-empty assertion bundles.
