# Grok (grok-build) — follow-up streams A/B/C/D

Run via `llm-gateway` with Exa MCP, always-approve mode, 19713 bytes stdout.

---

## Stream A: Kind-descriptor / self-describing-schema drift mitigation

External research across tools, papers, and projects reveals that schema drift—where descriptors, examples, ontologies, and validators diverge—is a persistent failure mode in self-describing systems. Content hashing with bidirectional traceability emerges as the strongest practical defense when brittleness is treated as a feature rather than a bug.

CognitiveLayers/clayers implements exactly this pattern: layered XML documents (Prose, Terminology, Relation, Artifact, Revision, etc.) with per-node SHA-256 content hashes on both specification and target code. The `artifact --drift` command detects divergence automatically in CI; a Merkle DAG repository enables structural diffs and element-level deduplication. Changes to either side invalidate the mapping visibly. The open layer model lets new namespaces/schemas be added without mutating existing ones. This aligns directly with producer-side responsibility: the producer of a kind-descriptor commits a hashed artifact; downstream consumers verify only the final hash chain.

CUE provides the complementary "schema-as-data" engine. Its unification model treats types and values uniformly, supports order-independent patching (critical for evolution without invalidating prior definitions), and generates OpenAPI/JSON Schema from concise constraints. Cross-field invariants (e.g., `x: y` and `y: x` for diagonals) are expressible where JSON Schema fails. Dhall offers strong static typing and deterministic evaluation but is repeatedly criticized for verbosity and poor performance on large Kubernetes-scale configs; CUE wins on composability and migration tooling (`cue import`, `cue trim`).

Protocol Buffers demonstrate controlled self-description via `FileDescriptorProto` / `DescriptorPool` plus the Editions mechanism (2023+). Wire-safe changes (add fields with defaults, reserved numbers) and explicit reservation of field numbers/names prevent reuse ambiguities. Unknown fields and retention options give runtime reflection without breaking old consumers. The descriptor is the schema carried with the data—self-describing by construction.

Supporting techniques include:

- Golden-master / characterization testing (Nat Pryce/Steve Freeman, Michael Feathers, ApprovalTests): capture full execution traces (stable vs. unstable fields classified explicitly), normalize non-determinism at serialization time, store as behavioral specs. Diffs surface unintended changes immediately. Modern variants (tryscript, session files) emphasize shardable, fast-CI scenarios with layered assertions.
- SHACL (and openapi-to-rdf converters): immutable shapes as contracts. The Solid versioning pattern uses `dct:replaces`/`dct:isReplacedBy`, `vs:term_status` (unstable→testing→stable→archaic), and stable namespaces. Only metadata additions are allowed on published shapes; breaking changes require new shapes. This prevents silent drift.
- Other observed patterns: Prisma-style deterministic `storageHash` + no-emit workflows (canonical JSON as single source of truth for all tooling), SpecSync bidirectional Markdown↔code validation with cross-project graphs, Cambria edit lenses for bidirectional schema translation, pyrmute-style multi-version migration chains with type-safe transforms, and Schema Sentinel for YAML/JSON structural diffing + environment drift reports.

**Proposed mechanism fitting the ethos (no JSON Schema, no novel crypto, primary validators in safe Rust/Go/C):** Treat every `*-kind.toml` (and its ontology entries, hard invariants, examples) as a first-class node in a content-addressed, layered manifest (inspired by clayers). Each node carries a SHA-256 over its canonical form. The ontology version and IJB primitive tags are part of the hash input. CUE (or a safe subset) expresses the structural + relational constraints; a small CDDL or CUE-derived checker validates conformance. Golden-master tests (with explicit stable/unstable classification) cover validator behavior against the canonical examples. A change to any upstream ontology entry, a required field, or an example immediately invalidates the dependent kind-descriptor hash—brittleness propagates visibly to every downstream consumer and tier file. Producer (the spec author) is responsible for updating the manifest and all affected examples in one atomic, hash-changing commit. Consumers verify only the final manifest root hash plus the last artifact they receive. Primary implementation: safe Rust library for the manifest DAG + CUE evaluation + golden harness; Go and C ports follow. This makes drift a first-class, mechanically enforced event rather than a social process.

Cited sources (selection):

- https://github.com/CognitiveLayers/clayers
- https://cuelang.org/docs/concept/data-validation-use-case/
- https://protobuf.dev/programming-guides/editions/
- https://github.com/jlevy/tbd/blob/main/packages/tbd/docs/guidelines/golden-testing-guidelines.md
- https://github.com/EricssonResearch/openapi-to-rdf
- https://github.com/CorvidLabs/spec-sync
- https://dl.acm.org/doi/10.1145/3447865.3457963 (Cambria)
- https://github.com/mferrera/pyrmute
- https://cloudplane.org/blog/why-cue
- https://pv.wtf/posts/taming-the-beast (CUE/Jsonnet/Dhall)

---

## Stream B: Legal-grade one-shot immutable attestation

Current standards separate concerns usefully but none fully satisfy the conjunction: one-shot per sha256 artifact, immutable once issued, legally provable intent (non-repudiation + timestamp), withdrawable keys without retroactive forgery, upstream changes intentionally breaking downstream hashes, producer-side responsibility (consumer verifies only the last artifact), and current crypto only.

in-toto (with ITE-5 DSSE envelope) + SLSA provenance predicates give structured, signed claims about materials/products/steps. Thresholds on steps already encode separation of duty. DSSE provides the PAE-wrapped, multi-signature envelope used across ecosystems. SLSA levels add hardening expectations (L3+ for hardened platforms, reproducible builds). Weakness: primarily build-focused; long-lived layout keys or missing transparency create replay/equivocation risks.

Sigstore (Fulcio + Rekor + cosign) popularized keyless signing: OIDC identity → short-lived certificate → ephemeral key destroyed after use + append-only transparency log. Excellent for "no long-lived key to steal." Weakness: still depends on central Fulcio/Rekor availability and correct OIDC trust; verification often requires log presence.

SCITT formalizes the transparency log as the audit surface for signed statements about artifacts. C2PA provides end-to-end provenance chains (strong for media, applicable to artifacts). DSSE is the common carrier.

RATS (RFC 9334) supplies the role model: Attester produces Evidence; Verifier appraises against policy + endorsements/reference values and emits Attestation Results for Relying Party. Passport model (Verifier returns result to Attester for presentation) vs. Background-Check (Relying Party forwards Evidence). Layered and composite Attesters match real devices. EAT (RFC 9711) defines the token format—CBOR/COSE or JSON/JWT with attestation claims (UEID, SUEID, hwmodel, swname/version, submodules, eat_nonce for freshness, profiles). COSE provides compact, modern signing for CBOR.

RFC 3161 Time-Stamp Protocol (TSP) is the legal-grade anchor: a TSA signs a hash (messageImprint) with policy OID, serial, genTime, optional nonce/accuracy. The token proves existence at a point in time. Critical for non-repudiation when private keys later change or are revoked. Long-term validity requires careful CRL/OCSP handling or re-timestamping; the spec explicitly discusses cessation-of-operation and keyCompromise revocation. eIDAS Qualified Electronic Signatures (QES) give legal equivalence to handwritten signatures in the EU; combined with TSP they provide the strongest current non-repudiation.

Gaps relative to requirements:

- Most systems optimize for ongoing pipelines rather than one-shot-per-artifact.
- Key withdrawal/rotation often either breaks historical verification (bad) or allows equivocation (worse). Short-lived + transparency mitigates but introduces liveness/centralization.
- Producer responsibility is partially present (in-toto layouts name authorized functionaries) but rarely enforced as "consumer only looks at the final hash + signature."
- Upstream hash breakage is not a first-class propagation rule.
- Legal-grade timestamping (RFC 3161 + QES) is under-used in software artifact pipelines.
- Evidence fatigue and root-of-trust shift risks are real when Verifier policy or Endorser keys drift.

**Composite design (ethos-compliant):** One-shot DSSE(in-toto Statement with subject = sha256(artifact) + predicate containing materials including upstream kind-descriptor or prior attestation hash). Wrap or augment with EAT claims for entity metadata. Immediately obtain an RFC 3161 TSA timestamp on the DSSE hash (or the inner statement hash). Use COSE for the CBOR path or JWS for JSON. For keys: producer generates an ephemeral keypair per artifact (or per batch under a short-lived OIDC/Fulcio-style cert), signs once, destroys the private key. Withdrawal is implicit—new attestations simply use new keys; old ones remain valid only for their exact artifact hash. Upstream change (new ontology version or new kind hash) forces a new subject/materials set whose hash differs; any cached downstream reference breaks visibly on re-verification. Transparency log (SCITT-style or Rekor) is optional for public audit but not required for basic one-shot verification. Consumer (relying party) verifies: signature (current crypto), timestamp freshness/policy, exact subject hash match, and (optionally) the last link in the materials chain. No consumer needs the full history—only the terminal artifact + its attestation envelope. This satisfies producer-side responsibility and makes brittleness (hash mismatch on upstream drift) a deliberate, visible signal.

Cited sources (selection):

- https://github.com/in-toto/specification/blob/master/in-toto-spec.md (and ITE-5 DSSE)
- https://www.ietf.org/rfc/rfc9334.html (RATS)
- https://datatracker.ietf.org/doc/html/rfc9711 (EAT)
- https://www.rfc-editor.org/rfc/rfc3161 (TSP)
- https://humanassisted.github.io/JACS/concepts/attestation-comparison.html
- https://safeguard.sh/resources/blog/provenance-attestation-signing-practical-glossary
- https://secure-pipelines.com/ci-cd-security/artifact-provenance-attestations-slsa-in-toto/
- https://www.ietf.org/rfc/rfc9334.html and related EAT/COSE drafts
- SLSA and Sigstore documentation

---

## Stream C: Separation-of-duty gate validation

Separation of duty (SoD) is a control, not a protocol feature. The strongest patterns combine mechanical enforcement (thresholds, distinct processes) with independent audit.

in-toto layouts are the clearest software-native example: a signed layout declares steps and authorized functionaries (by key). A step can require threshold > 1 (multiple independent links must agree). Inspections are client-side steps distinct from production steps. Sublayouts allow delegation while preserving the chain. The verifier (in-toto-verify or equivalent) is a separate artifact from the recorder (in-toto-run/record). This matches the ethos cycle: intent (owner-signed layout) → action (functionary produces signed link with materials/products) → proof (link) → audit (independent verifier applies policy, possibly with its own layout/inspections).

ISO 9001 (quality management), ISO/IEC 17021 (conformity assessment bodies), and ISO 19011 (auditing) codify independence: auditors must be independent of the auditee; two-party control and documented segregation of duties are expected for high-integrity processes. FIPS 140-3 explicitly requires dual control and split knowledge for many cryptographic module operations.

Cryptographic SoD uses threshold signatures (FROST for Schnorr-style, BLS with Shamir, classical MPC). No single party holds a usable key; k-of-n must cooperate. This is stronger than "two people type passwords" because the key material itself is never reconstructed in one place.

Transparency logs (Certificate Transparency RFC 6962/9162 lineage, Rekor, SCITT) provide append-only, publicly auditable records. Reproducible builds allow independent parties to re-execute and compare outputs. Stackelberg auditing models treat the auditee as leader and auditor as follower in a game where the auditor's verification strategy is known and the producer must commit first.

Mechanical patterns that force distinct validator:

- Different binaries / privilege domains (producer runs in CI tenant; validator runs in admission controller or user installer).
- Threshold layouts: at least two functionaries from different organizations or hardware roots must sign identical results.
- Dual-control gates: a human or second automated quorum must countersign before the artifact hash is considered "released."
- Independent re-execution: validator can demand a fresh reproducible build or cross-check against a transparency log entry it fetched itself.
- The cycle is enforced by requiring the layout to name distinct roles for "produce evidence" vs. "appraise evidence" and by making the appraisal policy itself a signed, versioned artifact that the validator consumes separately.

These patterns make the validator's compromise or collusion detectable (mismatched thresholds, log absence, reproducible mismatch) rather than invisible.

Cited sources (selection):

- https://github.com/in-toto/specification/blob/master/in-toto-spec.md (thresholds, layouts, separation of recording vs. verification)
- ISO 9001/17021/19011 family
- FIPS 140-3
- FROST / BLS / MPC literature and IETF drafts
- RFC 6962/9162 and SCITT work
- SLSA reproducible-build guidance
- RATS architecture

---

## Stream D: Alternative formats / new format

No existing format is perfect on all axes simultaneously. TOML wins readability and human editability but lacks a universally agreed deterministic canonical form (key ordering, whitespace, string escapes, integer vs. float representation). YAML/JSON suffer the same plus significant whitespace and key-order variance. Starlark/Jsonnet introduce limited evaluation (risky for "no eval"). Dhall and Nickel are excellent for safe, deterministic, typed configuration but verbose and slower; Pkl is Apple-polished but ecosystem-limited.

CBOR (RFC 8949) + the emerging dCBOR profile (draft-mcnally-deterministic-cbor) is the strongest for cryptographic use: definite-length only, preferred serialization, lexicographically ordered map keys, numeric reduction (integral floats become integers, single canonical NaN), NFC strings, duplicate-key rejection. Implementations exist in Rust, Swift, TypeScript, Ruby with test vectors. CDDL provides schema without JSON Schema. ASN.1 DER offers battle-tested canonical binary form used in every legal PKI document, but human readability and tooling friction are high. capnproto/FlatBuffers give zero-copy speed and schema evolution but are less friendly for ad-hoc human authoring. KDL, RON, EDN, NestedText improve readability over JSON but still require a defined canonicalization layer for hashing.

Safe multi-language parsing (no Turing-complete eval, bounded resource use) favors CBOR, strict TOML subsets, and ASN.1 DER over anything with embedded expressions. Producer responsibility is helped by formats where the "last artifact" is a single hashable blob whose canonical form is unambiguous.

**Verdict:** Do not invent a wholly new syntax. Define a strict, canonical TOML profile (sorted keys, explicit string normalization, integer/float discipline, no superfluous whitespace in canonical form) for human authoring of kind-descriptors and examples. Mandate that the normative attestation / wire form is dCBOR (or a CBOR+CDDL profile) emitted from the TOML source. Primary validators (Rust first, then Go, C) parse the canonical form directly. This preserves readability where humans edit while giving cryptographic tools a deterministic, compact, multi-language-safe representation. Schema lives in CDDL (for the CBOR side) or CUE constraints (for the unification/validation side)—never hand-written JSON Schema.

Cited sources (selection):

- https://datatracker.ietf.org/doc/draft-mcnally-deterministic-cbor/ (dCBOR)
- https://datatracker.ietf.org/doc/html/rfc8949 (CBOR)
- https://datatracker.ietf.org/doc/html/rfc9711 (EAT uses CBOR/COSE and JSON paths)
- https://cuelang.org/ and Dhall comparisons
- https://github.com/in-toto/specification (DSSE/JSON usage)
- ASN.1/DER and RFC 3161 (TSP) usage in PKI
- KDL, Pkl, Nickel project sites and comparisons
- capnproto / FlatBuffers documentation

---

## DESIGN RISKS ACROSS STREAMS

- Centralization creep: Sigstore/SCITT/Rekor-style logs solve equivocation but create liveness and governance dependencies. A fully offline one-shot design (ephemeral key + TSA timestamp) is safer for the ethos but harder to deploy at scale.
- Verifier complexity as bypass vector: rich layouts and multi-layer attestations are powerful; if the validator binary itself becomes large or has too many transitive dependencies, it becomes the new attack surface. Keep the core verifier tiny (safe Rust/Go/C) and push policy into signed data.
- Long-term key / algorithm agility vs. immutability: RFC 3161 already contemplates re-timestamping and careful revocation; any composite design must specify migration without allowing historical forgery.
- Evidence fatigue and root-of-trust shift: too many nested attestations or frequent policy changes cause operators to disable checks. The "consumer verifies only the last artifact" rule is the antidote but requires ruthless minimization of what the final envelope must contain.
- Format fragmentation: a TOML-for-humans + dCBOR-for-machines split is pragmatic but doubles the surface that must be kept in sync. Any canonicalizer bug is a security bug.
- Adoption vs. purity: existing projects already use DSSE+in-toto+Sigstore. A purist ethos-compliant profile may see slow uptake unless it is a strict, optional strengthening rather than a fork.

---

## BUILD ORDER (pragmatic, ethos-preserving)

1. Formalize the kind-descriptor manifest as a content-addressed, IJB-tagged, hash-chained artifact (Stream A core). Update all `*-kind.toml` files, examples, and ontology entries together with the new manifest format. Add golden tests for the validator itself.
2. Define the composite one-shot attestation envelope (DSSE + EAT claims + RFC 3161 timestamp + explicit upstream material hash) and the withdrawal/rotation rules. Produce reference Rust producer + verifier.
3. Enforce separation-of-duty mechanically in the reference tooling: distinct recorder vs. verifier processes, threshold examples for every gate, independent appraisal policy as a signed artifact.
4. Ratify the dual-format profile (strict canonical TOML authoring surface → dCBOR normative form + CDDL) and implement safe parsers in Rust (primary), Go, and C. Port the rest.
5. Only after the above: optional transparency integration and higher-level policy tooling.

This sequence makes drift, provenance, duty separation, and format determinism first-class, mechanically verifiable properties rather than hopes. Trust accrues to the process (signed layouts, hashed manifests, distinct verifiers, canonical bytes) rather than any single artifact surface.
