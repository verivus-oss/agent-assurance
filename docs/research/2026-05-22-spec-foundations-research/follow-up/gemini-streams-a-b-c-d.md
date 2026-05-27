# Gemini (gemini-3.1-pro-preview) — follow-up streams A/B/C/D

Run via `llm-gateway` with Exa MCP, YOLO mode, 21035 bytes stdout.
Note: Gemini's Stream D proposal coincidentally re-uses the name "DAG-TOML"
for its proposed format profile — this is the *existing project name*, not
a new format. Read as "a strict TOML profile for this project".

Note: Gemini hit Exa rate-limit errors mid-run (5x
`web_search_advanced_exa` errors) but completed with substantive output.

---

Here is the independent, skeptical research report on the four designated streams. The analysis adheres strictly to the mandated ethos: trust is the currency, brittleness is a feature, process-trust over artifact-trust, and producer-side responsibility.

## == Stream A: Kind-descriptor / self-describing-schema drift mitigation ==

**Survey & Evaluation**
The industry standard for schema definition—JSON Schema—is foundationally broken for high-assurance environments due to its culture of permissive parsing, silent type coercion, and lack of a deterministic canonical form. Moving beyond JSON Schema, the survey evaluated several advanced mechanisms for drift mitigation:

1. **CUE & Dhall (Type Systems):** Both provide excellent, constraint-based validation where types and values are unified. However, they are fundamentally evaluative languages. Relying on an evaluation engine introduces non-determinism and massive attack surfaces for primary normative validators written in C or Go.
2. **Grafana/Thema (Lineages):** Thema uses CUE to define backwards-compatible-by-construction schema lineages. It excels at tracking evolution, but its reliance on complex CUE evaluations makes it unsuitable for a dumb, strict parser model.
3. **PactFlow / Bidirectional Generation:** Excellent for API testing by ensuring the consumer and provider contracts match. However, it relies on testing infrastructure rather than cryptographic guarantees embedded in the artifacts themselves.
4. **CognitiveLayers (clayers):** A Rust-based framework that addresses specification drift by generating SHA-256 content hashes of both the specification XML nodes (AST) and the mapped code artifacts. It treats specifications as a verifiable graph, flagging drift instantly if the code changes without a spec update.
5. **AST-Level Fingerprinting:** By hashing the Abstract Syntax Tree rather than raw text, systems can ignore cosmetic changes while cryptographically catching structural modifications.

**Gap Analysis**
Existing mechanisms either rely on permissive external tooling (linters, CI checks) or heavy evaluative runtimes (CUE/Dhall). None strictly enforce the "brittleness as a feature" ethos at the point of consumption without dragging in a massive dependency tree. If a schema drifts from the artifact, the artifact should violently and visibly fail to parse, rather than relying on a separate CI step to catch the drift.

**Proposed Novel Mechanism: "Cryptographic AST-Fingerprinted Lineages"**
To fit the ethos, drift mitigation must be pushed to the cryptographic layer and enforced by the parser itself, completely stripping out the concept of "evaluation."

* **The Mechanism:** Every kind-descriptor (schema) is parsed into an Abstract Syntax Tree (AST). All non-semantic data (comments, whitespace) is discarded. The AST nodes are lexicographically sorted and serialized into a deterministic byte array, which is then hashed using SHA-256 to create a `SchemaFingerprint`.
* **Producer Responsibility:** When a producer generates an artifact, the generator embeds the `SchemaFingerprint` directly into the artifact's metadata header.
* **Validator Brittleness:** The normative validators (in Rust/Go/C) are hardcoded with the `SchemaFingerprint` they expect. When the validator reads the artifact, it first compares the embedded fingerprint against its internal fingerprint. If they diverge by even a single bit, the parser intentionally panics and aborts. There is no "backwards compatibility mapping" at runtime.
* **Visible Drift:** If the kind-descriptor evolves, a new fingerprint is generated. The producer must explicitly run a one-time, offline migration script to generate the new artifact. Drift is surfaced as a total systematic failure to load, forcing human intervention and re-attestation.

**Citations:**

1. [CognitiveLayers (clayers) Documentation](https://lib.rs/crates/clayers) — Analyzed for its approach to using SHA-256 hashes on specification ASTs to detect code-spec drift.
2. [CUE Language Configuration Use Cases](https://cuelang.org/docs/concept/configuration-use-case/) — Evaluated for constraint-based validation; rejected due to the complexity of the evaluation engine.
3. [Grafana Thema Lineages](https://github.com/grafana/thema) — Reviewed for backwards-compatible-by-construction schema evolution.
4. [Dhall Configuration Language](https://dhall-lang.org/) — Evaluated as a programmable configuration language; rejected due to Turing-incompleteness still allowing heavy computational loops.
5. [PactFlow Bi-Directional Contract Testing](https://pactflow.io/) — Analyzed for testing-based drift mitigation; rejected as it relies on CI pipelines rather than cryptographic artifact binding.
6. [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) — Reviewed for emerging standards on stable fingerprints for tool contracts to prevent silent API failures.
7. [SimpleModeling Executable Specifications](https://github.com/simplemodeling/simplemodeling) — Evaluated for generating Scala3 schemas; lacks cross-language safety.
8. [JSON Schema Limitations](https://json-schema.org/) — Explicitly rejected per user constraints due to permissive parsing and lack of strict canonicalization.

---

## == Stream B: Legal-grade one-shot immutable attestation ==

**Survey & Evaluation**
The landscape of supply chain attestation is highly fragmented between developer-convenience tools and rigid, legal-grade cryptographic standards.

1. **Sigstore / Fulcio / Rekor / SLSA v1.2:** This stack has won the open-source supply chain. However, it relies heavily on short-lived, ephemeral certificates bound to OIDC identities (e.g., logging in with GitHub). While great for automation, it fails the "legal intent to sign" requirement. A compromised CI token can generate a signature without human intervention.
2. **RATS (RFC 9334) & EAT (RFC 9711):** Remote Attestation Procedures and Entity Attestation Tokens provide excellent hardware-rooted trust. They verify the physical state of the machine generating the artifact, but do not necessarily bind the human operator's legal intent.
3. **COSE (RFC 9052):** CBOR Object Signing and Encryption provides the ideal, lightweight, binary-safe cryptographic envelope, vastly superior to JSON Web Signatures (JWS).
4. **eIDAS QES (Qualified Electronic Signatures):** The European standard for legal non-repudiation. QES requires a Secure Signature Creation Device (SSCD)—usually a hardware smart card—and is legally equivalent to a handwritten signature. It is the only standard that robustly proves *intent*, as it requires a physical PIN/touch.
5. **SCITT (Supply Chain Integrity, Transparency, and Trust):** Provides append-only transparency logs that issue cryptographic "receipts," proving an attestation was made at a specific point in time.

**Gap Analysis**
Sigstore suffers from the "provenance paradox" where the root of trust shifts to OIDC providers (Google/Microsoft), negating producer-side responsibility. SLSA provenance is mutable (can be superseded). EATs prove the machine's state but not the human's legal intent. eIDAS QES proves intent but lacks the metadata structure for software supply chains.

**Proposed Composite Design: "QES-anchored COSE Attestations with SCITT Receipts"**
To achieve legal-grade, one-shot, immutable attestation, we must compose COSE, QES, and SCITT into a single pipeline that places the entire burden of proof on the producer.

* **The Payload:** The artifact is hashed using SHA-256. This hash, along with the producer's claims, is formatted as a strict CBOR payload.
* **The Intent (QES):** The payload is wrapped in a `COSE_Sign1` envelope. The signing operation MUST be performed by a hardware-backed key (e.g., FIDO2/YubiKey or eIDAS SSCD). The hardware must be configured to require a physical touch or PIN for *every single operation*. This physically instantiates legal non-repudiation; automation is intentionally impossible.
* **Immutability & One-Shot (SCITT):** Once signed, the COSE object is submitted to a SCITT transparency log. The log returns a SCITT Receipt (a Merkle inclusion proof). The producer appends this receipt to the COSE envelope. The attestation is now immutable; there is no "v2" upgrade. If the artifact changes, a completely new QES signature and SCITT receipt are required.
* **Producer-Side Responsibility:** The consumer (Relying Party) performs exactly two checks: (1) Verify the SCITT receipt against the public log's root hash. (2) Verify the QES signature using the public key attached to the receipt. The consumer does not re-validate the artifact's build process; they trust the legal weight of the producer's QES.

**Citations:**

1. [RFC 9334 RATS Architecture](https://www.rfc-editor.org/rfc/rfc9334.txt) — Analyzed for attester/verifier architectural roles.
2. [RFC 9052 COSE Structures](https://www.rfc-editor.org/rfc/rfc9052.txt) — Selected as the underlying cryptographic envelope for binary-safe signing.
3. [RFC 9711 Entity Attestation Token (EAT)](https://www.rfc-editor.org/rfc/rfc9711.txt) — Evaluated for hardware-rooted claims formatting.
4. [SCITT Architecture Draft](https://datatracker.ietf.org/doc/draft-ietf-scitt-architecture/) — Utilized for immutable transparency receipts and non-repudiation logging.
5. [eIDAS Regulation (EU) No 910/2014](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=uriserv:OJ.L_.2014.257.01.0073.01.ENG) — Analyzed for Qualified Electronic Signatures (QES) and legal non-repudiation requirements.
6. [SLSA v1.2 Provenance](https://slsa.dev/spec/v1.0/provenance) — Evaluated and rejected as the primary attestation layer due to reliance on CI/CD automation rather than human intent.
7. [Sigstore / Rekor](https://sigstore.dev/) — Evaluated for transparency logging; rejected Fulcio due to OIDC ephemeral identity weaknesses.
8. [C2PA Specifications](https://c2pa.org/specifications/specifications/1.0/specs/C2PA_Specification.html) — Reviewed for its integration of COSE and hardware trust in media provenance.

---

## == Stream C: Separation-of-duty gate validation ==

**Survey & Evaluation**
The core vulnerability in most supply chains is that the entity compiling the code also signs the provenance. If the pipeline is compromised, the signature is valid but the artifact is malicious ("marking your own homework").

1. **ISO 9001 (Audit-Separation):** Dictates that auditors cannot audit their own work. In software, this means the build pipeline cannot be the validation pipeline.
2. **FIPS 140-3 (Dual Control / Two-Party Control):** Mandates that critical security parameters must be handled by two independent entities.
3. **Threshold Signatures (FROST / BLS):** Cryptographic Multi-Party Computation (MPC). FROST (RFC 9591) allows $t$-of-$n$ parties to collaboratively generate a single Schnorr signature without ever assembling the private key in one place.
4. **in-toto Layouts:** Defines a supply chain sequence where specific steps MUST be signed by specific functionary keys.

**Gap Analysis**
In-toto is excellent for tracking steps, but it still relies on discrete signatures that a consumer must evaluate, violating "producer-side responsibility" (the consumer shouldn't have to verify 10 different signatures from a pipeline). Standard dual-control policies are organizational, not technical. We need a mechanism where the technical output *cannot exist* unless the organizational separation was enforced.

**Proposed Mechanism: "Stackelberg Auditing via FROST Threshold Signatures"**
We enforce separation-of-duty not through policy, but through applied cryptography, ensuring the final artifact only carries a single, verifiable signature if and only if dual control was achieved.

* **The Setup:** We establish a FROST threshold signature scheme requiring 2-of-2 participants: The Producer Node and the Independent Auditor Node. These nodes must operate in completely separate administrative and physical domains (fulfilling ISO 9001 and FIPS 140-3).
* **The Process:**
    1. The Producer generates the artifact and signs their intent, creating `Signature Share 1`.
    2. The Independent Auditor Node detects the artifact, pulls the raw source from an immutable reference, and attempts a bit-for-bit reproducible build.
    3. If and only if the Auditor's reproduced hash exactly matches the Producer's hash, the Auditor generates `Signature Share 2`.
* **Cryptographic Enforcement:** The two signature shares are combined to create a single, valid COSE signature. If the Auditor refuses to sign (due to a build mismatch or policy failure), the final signature *mathematically cannot be created*.
* **Consumer View:** The consumer sees only one final signature. Because it is a FROST aggregate, the consumer knows mathematically that both the Producer and the separate Auditor agreed on the state of the artifact. The burden of auditing is shifted entirely to the producer's environment.

**Citations:**

1. [FROST: Flexible Round-Optimized Schnorr Threshold Signatures (RFC 9591)](https://www.rfc-editor.org/rfc/rfc9591.txt) — Selected as the cryptographic mechanism to enforce multi-party dual control.
2. [ISO 9001:2015 Clause 9.2.2](https://www.iso.org/standard/62085.html) — Sourced for the absolute requirement of audit-separation in quality management systems.
3. [FIPS 140-3 Security Requirements](https://csrc.nist.gov/publications/detail/fips/140/3/final) — Analyzed for Two-Party Control requirements regarding Critical Security Parameters.
4. [in-toto Framework Specifications](https://in-toto.io/in-toto-spec/) — Evaluated for supply chain layout mapping and functionary step validation.
5. [Reproducible Builds](https://reproducible-builds.org/) — Utilized as the verification mechanism for the Independent Auditor Node.
6. [Stackelberg Auditing in Supply Chains](https://arxiv.org/abs/2104.03202) — Reviewed for game-theory applications in pre-emptive adversarial auditing.

---

## == Stream D: Alternative formats / new-format design ==

**Survey & Evaluation**
The specification requires a configuration/schema format that is readable, has a deterministic canonical form, supports cryptographic provenance, and can be parsed strictly in safe Rust/Go/C without an evaluation engine.

1. **JSON / YAML:** YAML is fatally flawed due to extreme complexity (the Norway problem, node anchors). JSON lacks comments and suffers from floating-point ambiguity.
2. **JCS (RFC 8785 JSON Canonicalization Scheme):** Solves JSON's canonicalization problem (sorting keys, fixing floats), but inherits JSON's lack of comments and poor readability for massive configurations.
3. **Pkl / Dhall / CUE / Nickel / KDL:** Highly expressive, but they cross the line into programming languages. They require JIT compilers, interpreters, or heavy evaluation phases. This violates the ethos; a normative parser in C should not need a bytecode interpreter to read a configuration file.
4. **CBOR / ASN.1 DER:** Deterministic and excellent for machines, but completely fail the human-readability requirement for configuration authoring.
5. **TOML:** Extremely human-readable, minimal, and maps cleanly to hash tables. However, standard TOML lacks a strict, cross-language canonicalization algorithm for cryptographic hashing.

**Gap Analysis**
There is no existing format that bridges the gap between "dumb, human-readable data" and "cryptographically rigid canonical serialization." We need the readability of TOML but the cryptographic rigidity of JCS.

**Proposed Design: "Strict Canonical TOML Profile"** *(Gemini called this "DAG-TOML" — the same name as the existing project. Read as "a strict canonical TOML profile" to avoid collision.)*
Since no existing format wins outright without compromise, we propose a strict, novel profile of TOML designed explicitly for cryptographic serialization and schema-without-eval.

* **Syntax:** Strict subset of TOML v1.0. Completely declarative. No variables, no imports, no evaluation.
* **Deterministic Canonicalization Algorithm:** To hash a file, the parser applies an algorithm similar to JCS (RFC 8785) but mapped to TOML primitives:
    1. Parse the document into an AST.
    2. Discard all comments and whitespace.
    3. Recursively sort all table (dictionary) keys strictly by UTF-16 code unit order.
    4. Normalize all floats to IEEE 754 double-precision standard representations.
    5. Serialize the AST back into a minimal byte-stream.
* **Brittleness as Feature:** The format strictly prohibits coercion. If a schema expects an integer `1` and the user provides `1.0`, the parser panics. There is no implicit casting.
* **Schema-as-Data:** Files begin with a reserved `[__kind_descriptor__]` table. This table includes the `SchemaFingerprint` from Stream A. The parser reads this table first, computes the expected schema structure, and if the remaining document deviates structurally, it aborts parsing.

**Citations:**

1. [RFC 8785 JSON Canonicalization Scheme (JCS)](https://www.rfc-editor.org/rfc/rfc8785.txt) — Analyzed for its deterministic sorting and serialization algorithms.
2. [TOML v1.0.0 Specification](https://toml.io/en/v1.0.0) — Selected as the base syntax for its human readability.
3. [Pkl Configuration Language Comparison](https://pkl-lang.org/main/0.25.3/introduction/comparison.html) — Evaluated and rejected due to its requirement for an evaluation engine.
4. [KDL Document Language Discussion](https://github.com/kdl-org/kdl/discussions/389) — Reviewed for node-based configuration; rejected due to lack of existing deterministic hashing standards.
5. [Nickel Language Rationale](https://github.com/nickel-lang/nickel/blob/master/RATIONALE.md) — Analyzed for gradual typing; rejected due to Turing-completeness.
6. [CBOR RFC 8949](https://www.rfc-editor.org/rfc/rfc8949.txt) — Evaluated for canonical binary representation.
7. [YAML Norway Problem](https://hitchdev.com/strictyaml/why/implicit-typing-removed/) — Cited as justification for removing YAML entirely.

---

## == DESIGN RISKS ACROSS STREAMS ==

* **Canonicalization Fragility (Stream D & A):** The entire architecture relies on canonicalization. If the Rust, Go, and C parsers have even slight discrepancies in how they handle Unicode normalization or floating-point truncation, hashes will silently diverge, rendering valid signatures invalid and causing catastrophic ecosystem gridlock.
* **Evidence Fatigue / Payload Bloat (Stream B):** Combining COSE envelopes, QES public key certificates, SCITT receipts, and canonical TOML payloads will result in massive artifact headers.
* **The Provenance Paradox in Dual Control (Stream C):** If the Independent Auditor Node utilizes the same underlying compiler toolchain, base OS image, or dependency graph as the Producer Node, a compromised upstream dependency (e.g., a backdoored `gcc`) will deterministically compromise both nodes. The threshold signature will successfully generate, effectively laundering a supply chain attack through a high-assurance validation gate.
* **Revocation Latency and QES Keys (Stream B):** Hardware-backed QES keys are highly secure, but revocation via CRL or OCSP notoriously fails-open or suffers from high latency.
* **Migration Paralysis (Stream A):** By enforcing strict AST-fingerprint matching, schema evolution requires absolute synchronization between producers and consumers. Un-updated consumers will immediately crash, potentially causing severe availability outages.

---

## == BUILD ORDER ==

**Stream D (Format) MUST be shipped first.** The entire architecture is dependent on a stable, deterministic serialization format. Without the strict canonical TOML profile and its strictly conforming Rust/Go/C parsers, you cannot generate the ASTs required for Stream A (Drift Mitigation). Furthermore, you cannot reliably hash the payloads required for Stream B (Attestation) or reproduce the artifacts for Stream C (Gate Validation) if the underlying data format suffers from parser ambiguity or silent coercion. The canonicalization algorithm is the mathematical bedrock upon which all cryptographic signatures and hashes in the subsequent streams rely; if it shifts, the entire trust chain crumbles.
