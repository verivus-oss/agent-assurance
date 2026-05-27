# Codex (gpt-5.5) — follow-up streams A/B/C/D

Run via `llm-gateway` with Exa MCP, sandbox read-only, reasoning effort high.
~21KB stdout, ~25 Exa searches across the four streams.

---

Independent external research only; I did not inspect the local repository.

## A. Kind-Descriptor / Self-Describing-Schema Drift Mitigation

The common pattern across long-lived specs is not "better prose" or "better schema"; it is making drift mechanically observable. OpenAPI keeps prose, components, media types, and schema fragments in one normative document, but still leaves parts of behavior undefined or delegated to tooling. SHACL and JSON-LD show how external machine constraints can describe graph-shaped meaning, but the prose-context split remains a drift surface. Protobuf descriptors are strong because the schema is data: generated code, reflection, and descriptor sets all derive from one machine object. Dhall goes further with semantic hashes over normalized expressions, catching transitive change rather than text churn. CUE's unification model is useful because independent constraint layers compose and fail loudly. Grafana Thema is especially relevant: it treats schema evolution as lineages, sequences, lenses, and lacunae, making translation gaps first-class.

The failure pattern is clear: prose and machine form diverge when either one is treated as commentary. The remedy should not be a JSON Schema substitute. It should be a binding artifact that makes prose, examples, validator behavior, and descriptor hash mutually dependent.

**Proposal: Kind Descriptor Lockstep Ledger (KDLL).**

Each DAG-TOML kind has a closed, acyclic, data-only descriptor written in the same strict canonical format as the artifacts it governs. The descriptor contains field definitions, type rules, allowed references, canonicalization rules, error codes, example fixtures, counterexample fixtures, and required provenance slots. Every normative prose paragraph gets a stable anchor and a digest. Every descriptor rule names the prose anchor it implements. Every prose anchor that uses normative terms must name at least one descriptor rule. Build and release fail if there is any unpaired normative prose, any unpaired rule, any changed prose digest without a descriptor version bump, or any changed descriptor digest without refreshed conformance fixtures.

The fingerprint should be two-layered. `text_digest` hashes canonicalized normative source text, including comments and anchors. `ast_digest` hashes the parsed descriptor AST in canonical order. Drift is a visible failure if either changes unexpectedly. This avoids pure semantic hashing hiding legally meaningful wording changes, while still allowing the validator to compare AST behavior. Each validator implementation in safe Rust, safe Go, and safe C must emit the same descriptor digest, the same error-code corpus, and the same canonical output bytes for the golden suite. A fourth implementation is a port only if it consumes the descriptor and passes those locks.

KDLL should also define **rule witnesses**: for each rule, at least one valid example and one invalid counterexample. Property-based generators derive from the descriptor but do not become normative. The descriptor release bundle contains the descriptor, prose digest map, fixture corpus, canonical AST hash, and validator conformance hashes. A downstream artifact embeds only the descriptor digest and release receipt. Consumers verify the last artifact; producers carry the burden of updating descriptors, fixtures, and prose together. Brittleness is the point: drift breaks the producer's release, not the consumer's trust.

**Sources:**

- https://docs.dhall-lang.org/discussions/Safety-guarantees.html — Dhall semantic integrity checks show transitive change detection and loud failure.
- https://discourse.dhall-lang.org/t/why-does-term-order-not-impact-semantic-hashes/651 — Dhall semantic hashes and normalized binary representation.
- https://cuelang.org/docs/concept/how-cue-enables-data-validation/ — CUE unification, closed structs, multi-source constraints.
- https://developers.google.com/protocol-buffers/docs/reference/cpp/google.protobuf.descriptor — Protobuf descriptors model schema as inspectable data.
- https://www.w3.org/TR/shacl/ — SHACL machine-checkable graph constraints.
- https://www.w3.org/TR/json-ld11/ — JSON-LD term-to-IRI binding.
- https://spec.openapis.org/oas/v3.2 — OpenAPI shows component reuse and the limits of prose-plus-schema specs.
- https://github.com/grafana/thema/blob/main/docs/overview.md — Thema's lineage, lens, and lacuna model.

## B. Legal-Grade One-Shot Immutable Attestation

No existing system satisfies the whole requirement set. in-toto and SLSA describe process provenance, but they do not prove human or organizational legal intent to sign a specific digest exactly once. Sigstore improves identity, key lifecycle, and transparency, but keyless signing is still mostly "this identity controlled a key at this time," not "this signer performed a legally meaningful ceremony declaring intent." Rekor, CT, RFC 9162-style logs, SCITT, and RFC 3161 timestamping prove existence, ordering, or inclusion; they do not solve intent. QES under eIDAS is the closest legal primitive, but it does not model supply-chain closure, one-shot artifact binding, or downstream hash propagation. RATS/EAT can attest platform state, not legal will. Authenticode, Apple notarization, and package signatures are operational distribution controls, not general legal-grade process attestations.

**Gap:** existing systems distribute evidence, then force verifiers to decide how much evidence is enough. That creates evidence fatigue and shifts the root of trust to verifier policy. Worse, SLSA-style provenance can attest a compromised but policy-conforming pipeline. The TanStack-worm class of failure is not solved by more attestations if the producing process is already captured. Legal non-repudiation also remains weak under key compromise, post-dated claims, delegated automation, and ambiguous signing UI.

**Proposal: One-Shot Intent Attestation (OSIA).**

OSIA is a composite, not new crypto. The signed object is a canonical COSE or DSSE envelope containing an `intent_statement`: artifact SHA-256 or stronger digest, artifact media type, kind descriptor digest, exact version, upstream closure root, signer identity, authority basis, key validity interval, revocation endpoint/log, ceremony transcript digest, and a declaration such as "I intend to sign exactly this artifact digest for release as version X." The declaration is not UI chrome; it is signed payload.

Signing uses existing stacks:

- COSE_Sign1 or DSSE for envelope binding.
- QES or qualified electronic seal where legal non-repudiation is required.
- Sigstore/Fulcio/Rekor or X.509 PKI for identity and transparency.
- RFC 3161 timestamp token for independent time.
- SCITT receipt for append-only statement registration.
- Optional RATS/EAT evidence for release environment state.

One-shot behavior is enforced by a transparency-backed uniqueness rule: `(signer authority, artifact_sha256, intent_scope)` may be registered once. A later signature over the same bytes is a new intent statement with a new reason, not an upgrade. Prior versions are never patched. Upstream changes intentionally alter the downstream closure root, then the downstream artifact hash, then its OSIA digest. That visible break is the supply-chain alarm.

Revocation is append-only. A revocation statement references the original signature, artifact digest, log index, reason code, effective time, and authority. It is signed by a time-bounded revocation key or the original signer while valid, timestamped, and logged. Revocation never mutates the original attestation; it creates a later legal fact. Producers must include current revocation snapshots in the next artifact's closure root. Consumers check the final artifact's OSIA bundle, not the whole upstream history. The final producer is responsible for making upstream provenance possible.

For automated shippers, intent is organizational: an HSM or qualified seal key signs only after a release policy ceremony completes. For humans, a QSCD/WebAuthn/HSM step should display digest, artifact name, version, and declaration, and require explicit assent. WebAuthn alone is not legal intent, but it is useful ceremony evidence when bound into the signed transcript.

**Sources:**

- https://github.com/in-toto/attestation/tree/main/spec — Attestation framework layers.
- https://slsa.dev/spec/v1.2/ — SLSA v1.2 provenance.
- https://github.com/sigstore/docs/blob/main/content/en/cosign/signing/overview.md — Sigstore keyless signing.
- https://www.rfc-editor.org/rfc/rfc9334 — RATS architecture.
- https://www.rfc-editor.org/rfc/rfc9711 — Entity Attestation Token.
- https://www.rfc-editor.org/rfc/rfc9052 — COSE.
- https://datatracker.ietf.org/doc/html/draft-ietf-scitt-architecture — SCITT.
- https://www.rfc-editor.org/rfc/rfc3161 — RFC 3161 TSP.
- https://eur-lex.europa.eu/eli/reg/2014/910 — eIDAS/QES.
- https://www.rfc-editor.org/rfc/rfc6962 — Certificate Transparency.

## C. Separation-of-Duty Gate Validation

The core rule should be simple: no entity may complete the validation gate for an artifact it produced. "Entity" must mean more than username. It should include signing key, service account, organization unit, build worker identity, model lineage, and delegated authority class. Otherwise, an agent can split itself into two labels and self-approve.

The standards pattern is mature. ISO 9001 internal audit practice emphasizes objectivity, competence, evidence, and risk-based audit planning. ISO 19011 makes independence and evidence-based auditing explicit. ISO/IEC 17021 exists because third-party certification only matters if the certifier is competent and impartial. FIPS 140-3 and key-management ceremonies add dual control and role separation. in-toto layouts already separate project owner and functionaries. Reproducible-build systems show a powerful mechanical audit: independent rebuilders compare bytes, not promises. Transparency logs and SCITT receipts make the audit trail public and append-only. Threshold signatures make collusion more expensive, but they are not enough unless the threshold policy requires distinct control domains.

**Binding pattern: Intent → Action → Proof → Audit.**

- Intent is signed before work begins by the release authority.
- Action is performed by the producer or build executor.
- Proof is recorded by an instrumentation or provenance recorder that cannot modify the artifact.
- Audit is performed by an independent gate validator before final release signing.

The spec should mandate distinct entities for at least these steps:

1. Canonical parse and descriptor validation of the artifact.
2. Reproduction or deterministic regeneration where the artifact type permits it.
3. Provenance closure calculation and upstream revocation snapshot.
4. Final conformance corpus execution across Rust, Go, and C validators.
5. OSIA ceremony witnessing or policy-gate confirmation.
6. Transparency-log submission and receipt verification.

Enforcement should be cryptographic and procedural. Each role signs a statement with a role-qualified credential. The final release policy includes `not_same_as` constraints: producer key must not equal validator key; validator service must not run in the same build job; audit signer must be issued under an independent role OID or SCITT registration policy; threshold release must include at least one independent validator share. Object-capability isolation should ensure the validator has read-only artifact access and append-only statement authority, not write access to the artifact. A build system can produce candidate evidence, but the audit credential must live outside that build system.

For LLM or autonomous agents, "different prompt" is not separation. If the same agent instance, same model deployment, or same controller can produce and approve, it is self-validation. Acceptable separation is a different controlled service with separate credentials, separate logs, and a policy that rejects shared ancestry where required. This will be irritating; that is the feature. The audit trail must break visibly when independence is missing.

Strategic-auditee research reinforces the point: predictable audits are gameable, and sample-size manipulation can hide drift. The spec should require randomized or externally scheduled audits for ongoing processes, minimum evidence floors, and suspicion escalation. But for artifact release, the gate is deterministic: no independent audit statement, no valid final artifact.

**Sources:**

- ISO 9001 audit guidance — https://www.iso.org/files/live/sites/tc176sc2/files/documents/ISO%209001%20Auditing%20Practices%20Group%20docs/Auditing%20to%20ISO%209001%202015/APG-InternalAudit2015.pdf
- ISO 19011 audit principles — https://committee.iso.org/files/live/sites/tc176/files/PDF%20APG%20New%20Disclaimer%2012-2023/ISO-TC%20176-TF_APG-ISO_19011_2018.pdf
- ISO/IEC 17021 — https://www.iso.org/news/2006/09/Ref1028.html
- FIPS 140-3 — https://csrc.nist.gov/pubs/fips/140-3/final
- FROST RFC 9591 — https://www.rfc-editor.org/rfc/rfc9591
- Reproducible builds — https://reproducible-builds.org/docs/formal-definition/
- rebuilderd — https://github.com/kpcyrd/rebuilderd
- Stackelberg auditor model — https://arxiv.org/html/2605.06340
- Governance Gauntlet — https://zenodo.org/records/19689504

## D. Alternative Formats / New-Format Design

No surveyed existing format cleanly wins.

TOML is the closest human-authored base: readable, comments, explicit booleans, duplicate-key rejection, and decent Rust/Go/C parsing prospects. But TOML has no standard canonical form, permits representation choices that complicate one-to-one hashing, includes floats and timestamps with implementation latitude, and treats comments as non-semantic. For this domain, "comments are only for humans" is not enough if legal review text is part of what was signed.

YAML is out. YAML 1.2 narrowed the boolean problem, but deployed parser culture still carries YAML 1.1 surprises, anchors, tags, indentation hazards, and implicit typing history. JSON is out for the reasons already stated; RFC 8785 JCS is useful evidence that canonicalization is hard, not a reason to revive JSON here.

CBOR with deterministic encoding, CDDL, COSE, and emerging CBOR Common Deterministic Encoding is excellent for signed wire bundles. It fails human-editability. ASN.1 DER has the same shape: mature canonical binary, poor authoring ergonomics, and historically sharp parser edges. Cap'n Proto and FlatBuffers are efficient schema/wire systems, not legal-grade human source formats.

KDL is attractive: readable, comments, node structure, C/Rust/Go implementations. But its flexible identifiers, slashdash comments, type annotations, number model, and schema language ancestry make it too broad without a severe profile. EDN is elegant but casual, extensible, and reader-dependent. NestedText is human-friendly and intentionally simple, but it lacks enough native typing and schema machinery. Dhall, Nickel, Pkl, KCL, Jsonnet, and Starlark are configuration languages with evaluation. Some are total or sandboxed, but the mandate says no remote includes, no eval, and C primary validation. CUE is the strongest schema language candidate, but it is still an evaluator and Go-centric; use its ideas, not its runtime, for the normative validator.

**Verdict: create a strict profile/new format: Canonical DAG-TOML (CDT).**

Design goals:

- Human-readable, line-oriented, UTF-8 only.
- Canonical bytes are the signed artifact; non-canonical input is invalid in release mode.
- Comments are allowed but parsed as anchored trivia and included in canonical text hashing.
- No floats, no NaN/Inf, no local time, no implicit defaults, no duplicate keys, no mixed arrays, no unbounded integers.
- Integers are canonical decimal only; binary data is lowercase base16 with explicit type.
- Strings have one escape form; Unicode scalar validity required; no normalization.
- Tables and keys appear in canonical sorted order; producers format before signing; validators reject non-canonical order.
- References are explicit `@id` links inside a declared DAG; cycles are invalid.
- Includes, environment reads, macros, eval, imports, anchors, merge keys, computed keys, and schema-driven default insertion are forbidden.
- Schema is a CDT kind descriptor, not JSON Schema: closed records, required/optional fields, tagged unions, bounded arrays, regex by named deterministic profile, and stable error codes.

Canonicalization algorithm:

1. Decode UTF-8; reject BOM, invalid scalars, forbidden controls, CR-only newlines.
2. Parse with bounded depth and bounded token sizes.
3. Reject non-canonical lexical forms immediately: key order, integer spelling, string escapes, comments placement, array layout.
4. Build AST with comment trivia attached to the following node or file header.
5. Validate descriptor constraints.
6. Emit canonical text with LF, one key per line, sorted tables, sorted keys, stable comment placement.
7. SHA-256 or stronger over emitted bytes; AST digest separately for rule compatibility.

Use CBOR/COSE only for attestation bundles, not authored artifacts. That gives humans a brittle text format and machines a mature signing envelope.

**Sources:**

- TOML v1.1.0 — https://toml.io/en/v1.1.0
- YAML 1.2 changes — https://yaml.org/spec/1.2.2/ext/changes/
- RFC 8949 CBOR — https://www.rfc-editor.org/rfc/rfc8949
- RFC 8610 CDDL — https://www.rfc-editor.org/rfc/rfc8610
- CBOR CDE draft — https://datatracker.ietf.org/doc/draft-ietf-cbor-cde/
- RFC 8785 JCS — https://www.rfc-editor.org/rfc/rfc8785
- KDL — https://github.com/kdl-org/kdl
- NestedText — https://nestedtext.org/en/latest/
- Dhall — https://docs.dhall-lang.org/
- CUE — https://cuelang.org/docs/concept/how-cue-enables-data-validation/

## DESIGN RISKS ACROSS STREAMS

- Legal intent is jurisdiction-sensitive. QES/eIDAS gives a strong EU path, but global equivalence will require policy profiles, not one universal legal claim.
- "Consumer verifies only last artifact" can hide upstream evidence fatigue inside the producer. The closure root must be audited and logged, or the producer becomes an opaque trust oracle.
- Canonical text with comments included is stricter than most developers expect. Tooling must make non-canonical edits fail early and clearly.
- Safe C is a mandate but still risky. The C validator should be small, allocation-bounded, fuzzed, and treated as a conformance peer, not a convenience port.
- Separation-of-duty can be faked by organizational aliases. Identity policy must define control-domain separation, not just distinct key IDs.
- Revocation creates liveness pressure. If revocation status cannot be snapshotted, release must fail rather than assume validity.
- Descriptor/prose lockstep can become bureaucratic if every editorial change breaks release. The spec needs a clear normative/non-normative boundary.
- Deterministic rebuild gates are artifact-type dependent. The spec should require them where possible and require explicit "not reproducible" declarations where not.

## BUILD ORDER

1. Ship **D: Canonical DAG-TOML/CDT** first. Everything else depends on stable bytes, safe parsers, and deterministic hashes.
2. Ship **A: KDLL descriptors** next. Once the format is stable, bind kind rules, prose anchors, fixtures, and validator conformance.
3. Ship **C: separation-of-duty gates** third. Gates need concrete artifacts and descriptors to validate.
4. Ship **B: OSIA attestation** last as the legal/security capstone. It should sign stable artifacts, descriptor digests, gate statements, and provenance closure roots, not a moving target.
