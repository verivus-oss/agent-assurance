# Exa Deep Researcher — Stream A — Kind-descriptor / self-describing-schema drift

Model: `exa-research`. Cost: $1.16. Searches: 70. Pages crawled: ~160.
Research ID: `r_01ks6k93rr0jn5kps3b70v98fm` (2026-05-22).

Identical context block to other agents. Brittleness-as-feature ethos.

---

# Self-Describing Schema Drift Mitigation — Survey + Design for "Brittleness as Feature"

## Mechanisms surveyed (each: how drift surfaces; Rust/Go/C compat; JSON dependence; empirical track record)

### 1) Content hashing of prose and executable doc examples

- **Mechanism**: Extract executable examples and prose from documentation (docstrings, *-kind.toml `description`), run the examples or produce a canonical fingerprint of the prose contents, and verify that outputs or fingerprints match expected values embedded in docs. Typical tool examples: Python doctest, Sphinx doctest, Rust documentation tests (`cargo test --doc`), and content-addressing ideas like ndcontent.
- **How drift surfaces**: Visible failure — mismatched outputs or mismatched content hashes cause explicit test/report failures; doctest tools print expected vs actual outputs and fail the build.
- **Multi-language compatibility**: Concept is language-agnostic but tool support varies — Rust has integrated doc tests; Go has example tests (not exactly doctest prose); C requires external tooling or literate frameworks.
- **JSON anchoring**: Not required — works against source prose and examples rather than JSON schema encodings.
- **Empirical track record**: Widely used in Python and Rust to keep docs and code aligned; effective at surfacing doc–code drift in practice.

### 2) Bidirectional generation (docs ⇄ descriptor)

- **Mechanism**: Toolchains that generate docs from descriptors and can regenerate descriptors from docs (or otherwise keep both linked by strong includes/tags). Examples include AsciiDoc tag includes, mdBook/asciidoc plugins, Sphinx autodoc and JSON-LD context generators.
- **How drift surfaces**: Mixed — when generation is strict (XML/DocBook + schema validation) drift causes visible failures; when generation is permissive (AsciiDoc, loose Markdown) drift can silently accumulate unless generation/round-trip checks are enforced.
- **Multi-language compatibility**: Tool-dependent; many generators are language-agnostic but some implementations (e.g., mdBook) are Rust-based.
- **JSON anchoring**: Not required; JSON-LD variants do use JSON anchoring but textual documentation generators typically operate on Markdown/AsciiDoc.
- **Empirical track record**: Strong where round-trip/generation is enforced (DocBook ecosystems); weaker where docs are generated without reverse checks.

### 3) Schema-as-data (CUE, Dhall, CDDL, Proto FileDescriptor, ASN.1)

- **Mechanism**: Represent schema itself as data in a typed/config language enabling composition, validation, subsumption checks, and machine reasoning. Notable examples: CUE's schema-as-data model, Dhall, CDDL (for CBOR), ProtoBuf FileDescriptor, ASN.1 modules.
- **How drift surfaces**: Strong visible failure when you apply formal compatibility checks (subsumption, normalization); CUE supports subsumption checks to detect incompatible changes.
- **Multi-language compatibility**: CUE is implemented in Go (primary evaluator) but the schema-as-data concept works across languages; ProtoBuf and ASN.1 have mature implementations in Rust/Go/C.
- **JSON anchoring**: Some schema-as-data formats are JSON/CBOR-anchored (CDDL for CBOR/JSON), others (CUE, ProtoBuf, ASN.1) are not strictly JSON-anchored.
- **Empirical track record**: ProtoBuf and ASN.1 are battle-tested; CUE is newer but gaining adoption.

### 4) AST-level fingerprinting / deterministic encodings

- **Mechanism**: Parse data/schema into an AST or canonical representation and compute a deterministic fingerprint; canonicalization reduces false positives caused by formatting/ordering differences. Technologies include deterministic CBOR (RFC 8949), COSE canonical encoding, JSON Canonicalization Scheme (JCS, RFC 8785) and XML C14N (RFC 3076).
- **How drift surfaces**: Visible failure when fingerprints diverge — deterministic encodings enable cryptographic comparisons; semantic equivalence can be preserved while superficial edits are ignored if canonicalization is AST-based.
- **Multi-language compatibility**: Deterministic CBOR and canonical encodings are implementable in Rust, Go, and C; JCS is JSON-centric and thus tied to JSON tooling.
- **JSON anchoring**: JCS is JSON-anchored; CBOR & COSE are not JSON-anchored and often preferred when JSON's permissiveness is unacceptable.
- **Empirical track record**: Deterministic CBOR and XML C14N are used in cryptographic signing & verification where canonical forms are essential.

### 5) Executable specifications (Cucumber/Gherkin, property-based testing, formal specs)

- **Mechanism**: Encode specs as executable checks (Gherkin acceptance tests, property-based tests, model-checking/formal proofs in TLA+/Coq/Lean) and run them to validate behavior against prose/spec intent.
- **How drift surfaces**: Visible failure — executable specs fail when code diverges from spec; property-based testing surfaces edge-case mismatches.
- **Multi-language compatibility**: Tool-dependent; property-based frameworks exist across languages.
- **JSON anchoring**: Not required.
- **Empirical track record**: Strong in BDD and high-assurance contexts.

### 6) Golden-master / Approval testing

- **Mechanism**: Capture canonical outputs (rendered docs, serialized validation traces) as gold files; changes must be human-approved (or tests fail) before acceptance.
- **How drift surfaces**: Visible failure — any change to the rendered/serialized output triggers a diff and requires explicit approval (hard CI failure until approved).
- **Multi-language compatibility**: Language-agnostic since it compares outputs; implementations exist across ecosystems.
- **JSON anchoring**: Not required.
- **Empirical track record**: Proven valuable in legacy refactoring and ensuring UI/serialized outputs remain stable.

### 7) Literate programming with extraction (noweb, Org-babel, WEB)

- **Mechanism**: Combine prose and code in one document, weave/tangle to produce both human-readable docs and compilable code, execute code blocks embedded in prose (Org-babel).
- **How drift surfaces**: Visible failure where extracted code fails to compile or run; silent drift can occur when docs are not executed/tested.
- **Multi-language compatibility**: Org-babel supports many languages including Rust/Go/C.
- **JSON anchoring**: Not required.
- **Empirical track record**: Strong in reproducible research and docs-driven code.

### 8) Lineages (grafana/thema)

- **Mechanism**: Treat schema change as first-class — express ordered lineages of schema versions, provide translation/lenses between versions, emit lacunas when translation is incomplete. Project example: grafana/thema uses CUE and lineages.
- **How drift surfaces**: Visible failure or explicit lacuna reports — translation/validation steps expose mismatch and potential loss when a new schema cannot be mapped into an older one cleanly.
- **Multi-language compatibility**: Depends on availability of a spec evaluator (CUE's evaluator is currently Go-based), but the lineage concept is language-agnostic in principle.
- **JSON anchoring**: Not required; Thema uses CUE.
- **Empirical track record**: Experimental and promising but not yet widely adopted.

### 9) Content-addressed descriptors (CIDs, clayers, CHIP-0007)

- **Mechanism**: Bind descriptors and artifacts to content hashes (CIDs) so any change produces a different identifier; systems like IPFS use Merkle DAGs and multiformats for self-describing content addressing.
- **How drift surfaces**: Visible failure when CID mismatches occur; silent drift can occur if systems accept stale CIDs.
- **Multi-language compatibility**: Implementation-agnostic — libraries for hash generation/parsing exist in Rust, Go, and C.
- **JSON anchoring**: Not required.
- **Empirical track record**: Strong in decentralized storage and reproducible artifact addressing (IPFS/Git).

### 10) Bidirectional lenses (Cambria / edit lenses)

- **Mechanism**: Declare composable, bidirectional transformations between schema versions so edits on any representation can be round-tripped and correctness properties (put/get laws) are enforced.
- **How drift surfaces**: Visible failure — lens properties are violated when updates cannot be translated back and forth.
- **Multi-language compatibility**: Conceptually language-agnostic but current tooling (Cambria) is JSON/JS/TS-focused.
- **JSON anchoring**: Cambria is JSON-centric in current implementations.
- **Empirical track record**: Strong research foundations; implementations are experimental.

### 11) JSON-LD contexts + remote-context risk

- **Mechanism**: JSON-LD contexts map JSON terms to IRIs and can be fetched remotely at runtime; this introduces a dependency on remote authoritative context documents.
- **How drift surfaces**: Both — visible failure if context cannot be dereferenced; silent acceptance if a malicious or changed remote context is accepted and silently reinterprets data semantics.
- **JSON anchoring**: Inherently JSON-anchored by design.
- **Empirical track record**: The risk of runtime remote context changes is acknowledged; mitigations (vetting & caching contexts) are recommended.

### 12) SHACL shapes (RDF) — expressivity vs validation

- **Mechanism**: Express validation constraints (shapes) for RDF graphs; validation produces structured, detailed validation reports.
- **How drift surfaces**: Visible failure — SHACL validation yields explicit reports with offending nodes/paths; severity levels allow strict enforcement.
- **Multi-language compatibility**: SHACL is implementable in many languages.
- **JSON anchoring**: Not required — SHACL operates on RDF.
- **Empirical track record**: Mature in semantic-web and knowledge-graph communities.

### 13) ProtoBuf field reservations & unknown-field behavior

- **Mechanism**: Field numbers are the stable identifiers at wire-level; `reserved` declarations prevent reuse of field numbers/names; unknown fields are preserved in the binary wire form for forward compatibility.
- **How drift surfaces**: Mixed — unknown-field preservation supports forward compatibility (silent acceptance) but reuse of field numbers or mishandled unknown fields can silently corrupt semantics; `reserved` enforcement produces visible errors when enforced by tooling.
- **Multi-language compatibility**: Core Protobuf toolchain supports Rust/Go/C implementations.
- **JSON anchoring**: Not required — wire format is binary.
- **Empirical track record**: Proven at massive scale but field-number best practices are critical.

## Cross-cutting comparison focused on "Brittleness as Feature"

- **Visible-failure-first approaches that best match the user ethos**: AST-level fingerprinting + deterministic encodings, schema-as-data with formal compatibility checks (CUE), SHACL validation, golden-master approval testing, and bidirectional lenses/lineages (when enforced strictly) all surface drift as explicit failures.
- **Silent-acceptance risk mechanisms**: Content-addressed descriptors can be silent if stale CIDs are accepted; ProtoBuf unknown-field forwarding is intentionally permissive; JSON-LD remote contexts are a serious silent-acceptance risk if remote contexts are trusted at runtime without vetting.
- **Multi-language considerations**: The strongest cross-language portability comes from binary canonicalization (CBOR deterministic), schema-as-data formats with multi-implementation support (ProtoBuf, ASN.1), and language-agnostic fixtures/golden-masters.
- **JSON anchoring risk**: The user explicitly rejects JSON Schema. Mechanisms depending on JSON (JCS, Cambria current impl, JSON-LD contexts) inherit JSON's permissive culture and are therefore less desirable unless replaced with AST-level canonicalization or binary canonical encodings (deterministic CBOR/COSE).

## Design: Novel mechanism that fits the ethos — KindLock

### Requirements (mapped to features)

- A: Content-hashed binding between prose and validator behavior (Rust + Go + C primaries).
- B: Multi-implementation conformance fixtures as the ultimate ground truth.
- C: AST-level fingerprinting so whitespace-preserving formatting does not break hashes but semantic changes do.
- D: Drift surfaces in CI as a hard failure with a clear, actionable diff.

### Design summary

**1) Canonical Prose AST Extraction.** For each *-kind.toml descriptor, extract the `description` fields and structured prose sections. Parse each prose field into a small structured AST that captures constrained statements about the schema (field names, cardinalities, allowed values, invariants expressed in a limited prose DSL or well-structured sentences). Use a disciplined prose style to keep prose machine-parseable. The AST is defined as a small, stable grammar that captures semantic atoms — property rules, examples, and constraints.

**2) Prose AST Normalization + Deterministic Serialization.** Normalize ASTs (sort maps, normalize identifiers, canonicalize numeric forms). Serialize deterministically using deterministic CBOR per RFC 8949 rather than JSON text to avoid JSON parsing permissiveness. Compute a SHA-256 over the canonical serialization to produce the ProseCID.

**3) Validator AST/IR Extraction and Canonicalization.** For each validator implementation (Rust/Go/C), provide an extraction tool or compiler plugin that emits a canonical validation AST/IR describing its validation rules. The IR must be expressive enough to represent validators' logic but constrained to a canonical subset (no arbitrary code execution), enabling deterministic serialization and hashing.

**4) Content-hash binding (ProseHash ↔ ValidatorHash).** For a given *-kind.toml kind K, produce a binding object in a registry/descriptors index that records: kind name, prose-prosha (ProseCID), per-implementation validator-hashes (RustHash, GoHash, CHash), plus links to the fixture suite version and conformance status. The binding may be encoded as a signed, content-addressed record (e.g., multiformats CID-like structure).

**5) Conformance fixtures as ultimate ground truth.** Define a canonical fixture format (language-agnostic) expressed as deterministic CBOR records: each fixture includes an input instance, expected validation outcome (pass/fail), and optionally an explanation mapping to prose statements. All validator implementations must run the fixture suite and produce deterministic trace outputs (also canonicalized and hashed). If any implementation's trace differs, the binding is considered invalid and CI fails.

**6) AST-level fingerprinting rules.** Prose ASTs ignore whitespace, editorial punctuation variants, and formatting but retain semantic atoms (names, constraints, example values). Validator IR normalizes control-flow and focuses on declarative constraint expressions. Implementation: deterministic CBOR serialization of normalized AST/IR then SHA-256.

**7) CI enforcement & diff reporting (hard failure requirement).** CI job steps on every commit/PR:

1. Extract Prose AST → produce ProseHash.
2. For each validator impl (Rust/Go/C): extract ValidatorIR → produce ValidatorHash; run fixture suite → produce fixture run trace.
3. Compare ProseHash ↔ declared binding; compare ValidatorHashes ↔ declared binding; compare fixture-run traces to canonical fixture outputs.
4. If any mismatch: fail CI; produce a structured drift report including:
   - Human-friendly prose AST rendering of the prose rule(s) involved
   - Validator IR excerpt with side-by-side diff of normalized AST nodes
   - Fixture trace diffs showing concrete failing example input(s) and expected/actual outcomes

The CI diff must be machine-parsable JSON/CBOR (for automation) and a human-readable text rendering for reviewers.

**8) Tooling and bootstrapping.** Provide small reference implementations (extractors + normalizers) in Rust, Go, and C that produce the validator IR and run fixtures; these are the canonical implementations used by CI. Keep these extractors deliberately small and auditable. Use a minimal, well-documented prose-authoring guideline (templates + required declarative fragments) in *-kind.toml to maximize parseability.

### Why this fits the ethos

- **Brittleness is by design**: the system intentionally fails CI on any semantic mismatch between prose and validator behavior.
- **Avoiding JSON**: deterministic CBOR as the canonical serialization for fingerprints to avoid JSON's permissive culture.
- **Multi-language bootstrapping**: reference extractors/emitters in Rust/Go/C to establish trusted, auditable tools.
- **Conformance fixtures as ground truth**: golden-master/approval testing practices make fixtures the final arbiter.

### Example CI failure message

> "Prose (ProseHash: Qm...) asserts field `status` must be one of [\"open\",\"closed\"]; Rust validator (RustHash: abcd...) permits `status` = `null`. Fixture #12 expects validation failure for input X but Rust validator accepted it. See AST diff: (prose) allowed-values != (validator) allowed-values."

Machine-parsable payload (canonical CBOR snippet) includes: ProseHash, ValidatorHashes, failing fixture ID, normalized AST nodes for both sides, and side-by-side failing example input/expected/actual traces (all CBOR-deterministic).
