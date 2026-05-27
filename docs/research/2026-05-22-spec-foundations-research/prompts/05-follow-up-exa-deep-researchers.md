# Follow-up Exa Deep Researcher prompts (4 streams)

Four separate Deep Researcher jobs, one per follow-up research stream.
Stream B used `exa-research-pro` (most comprehensive) per the user's
direction that legal-grade attestation needs careful exploration; the
other three used `exa-research` (balanced).

## Stream A — Kind-descriptor drift

Research ID: `r_01ks6k93rr0jn5kps3b70v98fm`. Model: `exa-research`.
Cost: $1.16. Searches: 70.

```
Research the design space for "self-describing schema drift mitigation" in long-lived specifications. The context: a TOML-based spec ships *-kind.toml descriptor files (a kind-of-kind meta-schema). Prose, machine-readable descriptors, multiple safe-language validators, and instance examples all need to stay aligned over years. JSON Schema is rejected (JSON has silent coercion, no canonical form, permissive parsing culture). The design ethos demands BRITTLENESS AS FEATURE — drift must surface as visible failure, not as silent acceptance.

Comprehensively survey existing mechanisms for keeping prose and machine-readable form aligned:

1. Content hashing of prose, bound into the descriptor and verified by validators — e.g., docstring fingerprints, doctest extraction, Sphinx + doctest, Rust's `cargo test --doc`, Python's `doctest`, `ndcontent` content addressing.
2. Bidirectional generation — descriptor generates prose and vice versa; e.g., AsciiDoc tag includes, MDBook plugins, Sphinx autodoc, JSON-LD context generators.
3. Schema-as-data — the schema is itself an instance of the meta-schema; CUE (https://cuelang.org/), Dhall types, ProtoBuf FileDescriptor, ASN.1 modules, RFC 8610 CDDL.
4. AST-level fingerprinting — JCS (RFC 8785, rejected because JSON-based), COSE canonical encoding, deterministic CBOR (RFC 8949), C14N XML canonicalization (RFC 3076 — also rejected for being XML-based).
5. Executable specifications — Cucumber/Gherkin, property-based testing (QuickCheck, Hypothesis, proptest), TLA+, Alloy, Lean / Coq proof-carrying specs.
6. Golden-master testing / approval testing — every change requires explicit re-approval of the rendered output.
7. Literate programming with extraction — `noweb`, `Org-babel`, Knuth's WEB system.
8. Lineages — grafana/thema (https://github.com/grafana/thema) which makes schema *change* a first-class system property.
9. Content-addressed descriptors — CognitiveLayers / clayers (https://github.com/CognitiveLayers/clayers); CHIP-0007 metadata; IPFS-style content addressing.
10. Bidirectional lenses — Cambria (https://dl.acm.org/doi/10.1145/3447865.3457963) for schema evolution with edit lenses.
11. JSON-LD contexts + remote context risk (https://iolanta.tech/articles/remote-contexts-considered-harmful/).
12. SHACL shapes (https://www.w3.org/TR/shacl/) vs. data; expressivity vs. validation.
13. ProtoBuf reserved fields, field numbers, unknown-field behavior.

For each: how does it surface drift? Does it surface as a visible failure or as silent acceptance? Is it compatible with multi-language safe-language parsers (Rust, Go, C)? Does it require JSON-anchored tooling? What's the empirical track record?

Propose a NOVEL mechanism that fits the ethos:
- Content-hashed binding between prose (in *-kind.toml's `description` and section text) and validator behavior (Rust + Go + C primaries).
- Multi-implementation conformance fixtures as the ultimate ground truth.
- AST-level (not text-level) fingerprinting so that whitespace-equivalent re-formatting does NOT spuriously invalidate, but semantic changes DO.
- Drift must surface in CI as a hard failure, with a clear "this prose says X, the validator does Y, here's the diff".

Deliver: ~2000–3000 words with citations, evaluation matrix, and design sketch.
```

## Stream B — Legal-grade one-shot immutable attestation

Research ID: `r_01ks6k8dwpnrb5zqgenfvvj0cq`. Model: `exa-research-pro`.
Cost: $2.22. Searches: 64.

```
Research the design space for "legal-grade one-shot immutable attestations". The requirements (binding):

1. Each attestation binds to exactly one SHA-256-hashed artifact, single-use.
2. Immutable — no upgrades to a signed artifact; the attestation does not transfer to other versions.
3. SHA-256 is the floor; stronger hashes permitted.
4. Legally provable INTENT to sign — not merely "the key was used", but explicit evidence of intent (qualified electronic signature properties under eIDAS, signing ceremony, declaration accompanying the signature, etc.).
5. Withdrawable / time-bounded — keys must age out; signatures must be revocable / invalidatable; revocation is itself attested.
6. Brittleness-propagating — when an upstream attestation is updated or revoked, downstream artifact hashes are INTENTIONALLY broken; that breakage is the signal mechanism for "something changed, recheck".
7. Producer-side responsibility — consumers verify only the last artifact and make provenance possible for the next; producers bear the burden.
8. Built only from existing cryptographic primitives — no novel crypto.
9. Mandatory for any entity that ships an artifact.

Comprehensively survey existing systems for each requirement and identify the GAP:

- in-toto attestation framework (https://in-toto.io/) — predicate/statement/envelope model
- SLSA v1.2 build provenance (https://slsa.dev/spec/v1.2/) — what attestations DON'T cover
- Sigstore / Fulcio / Rekor (https://www.sigstore.dev/) — keyless signing; transparency log
- DSSE Dead Simple Signing Envelope (https://github.com/secure-systems-lab/dsse)
- RATS architecture RFC 9334 (https://datatracker.ietf.org/doc/html/rfc9334) — attester/verifier/relying-party
- Entity Attestation Token RFC 9711 (https://datatracker.ietf.org/doc/html/rfc9711)
- COSE RFC 9052 (https://datatracker.ietf.org/doc/html/rfc9052)
- SCITT (Supply Chain Integrity, Transparency and Trust) IETF WG
- C2PA Content Credentials (https://c2pa.org/specifications/) — manifests, hash binding, claim signing
- eIDAS qualified electronic signatures, advanced electronic signatures, qualified preservation services — what makes a signature "legally provable" in EU law
- US federal ESIGN Act and UETA — what makes a signature legally binding
- RFC 3161 Time-Stamping Protocol — proving "this signature existed at time T"
- RFC 6962 / 9162 Certificate Transparency — append-only logs with cryptographic inclusion proofs
- X.509 PKI + CRL (RFC 5280) and OCSP (RFC 6960) — revocation mechanisms
- WebAuthn / FIDO2 / FIDO Device Onboarding — non-repudiation via authenticator-bound keys
- age / Sequoia-PGP / PGP — signing primitives
- OpenPubkey (Bastion Zero) — OIDC-bound signing
- Witness statements / threshold attestations
- Trillian (Google's append-only log)
- Apple Notarization, Microsoft Authenticode — code signing with revocation chains
- Blockchain timestamping / OpenTimestamps (https://opentimestamps.org/)

For each: (a) which of the 9 requirements it satisfies fully, (b) which it satisfies partially, (c) which it does not address.

Then characterize the GAP — what no existing system covers, particularly:
- The combination of one-shot binding + legally provable intent + withdrawal-that-propagates-as-brittleness
- How to make upstream changes intentionally cascade-break downstream signatures (the opposite of what most signing systems try to provide — most try to preserve signature validity)
- How producer-side responsibility differs from current consumer-must-check-everything models

Finally, propose a composite design that fills the gap by combining existing primitives. The design must:
- Use only existing crypto
- Be implementable across safe Rust + safe Go + safe C
- Refuse JSON-based formats (JSON has silent coercion + no canonical form + permissive parsing culture incompatible with the ethos)

Deliver: a structured report (~3000 words) with citations and named gaps.
```

## Stream C — Separation-of-duty validation

Research ID: `r_01ks6k9p13ym0bfj9x0ytbb1rd`. Model: `exa-research`.
Cost: $1.67. Searches: 93.

```
Research "separation-of-duty for software/AI gate validation". The premise: an agent (human, program, LLM) cannot validate its own work. The mechanical cycle must be: intent → action → proof → audit, auditable in an ISO-9001-like sense. The validator must be mechanically distinct from the producer.

Survey:

1. ISO 9001 / ISO/IEC 17021 / ISO 19011 audit-separation principles — who can audit whom, competence requirements, independence of auditing bodies.
2. Two-party control / "two-man rule" — NSA/DoD heritage, FIPS 140-3 dual control, banking key ceremonies.
3. Threshold signatures — FROST (https://eprint.iacr.org/2020/852), BLS, Shamir secret sharing, m-of-n signing.
4. Multi-party computation (MPC) for verification — secure aggregation, MPC-based attestation.
5. Trusted third-party witnesses — notaries (digital and traditional), transparency logs (Certificate Transparency, Trillian, Sigstore Rekor), SCITT receipts, Witness Statements.
6. Reproducible builds — rb-tools (https://reproducible-builds.org/), Bazel remote execution + reproducibility, Tekton Chains, Bitcoin's deterministic builds.
7. Capability-based isolation — sandboxes where the producer cannot write to validator-readable surfaces; OCaps, WASI.
8. in-toto layouts — multi-party supply chain workflows; functionaries with cryptographic roles.
9. Recent academic work — Stackelberg auditor-auditee games (https://arxiv.org/html/2605.06340) showing impossibility of single-auditor designs; Robust ML Auditing using Prior Knowledge (https://proceedings.mlr.press/v267/garcia-bourree25a.html).
10. Governance Gauntlet dual-rubric pattern (https://zenodo.org/records/19689504) — adversarial integrity rubric in parallel with primary loop.
11. Attestable Audits with TEEs (https://arxiv.org/pdf/2506.23706) — cryptographic attestation that audit code ran on the declared model.
12. Mandatory access control (Bell-LaPadula, Biba), no-write-up no-read-down policies.
13. Banking SoD: maker/checker, ICFR controls under SOX § 404, COBIT.

For each: (a) what threat does it mitigate, (b) what does it cost (in process friction, in trust assumptions), (c) is it composable with cryptographic attestation, (d) does it survive the "gate gaming" failure mode where an agent optimises for the minimal attestation that passes.

Then propose mechanical patterns for software/AI agent assurance:
- Which steps in intent → action → proof → audit MUST be done by an entity distinct from the producer?
- How is "distinct entity" enforced cryptographically? (separate key, separate root of trust, threshold signing, witness statement, transparency log)
- How does the audit step work when the auditor is itself another agent that might game?
- How do you compose this with the requirement that consumers only verify the last artifact (producer-side responsibility)?

Deliver: ~2000–3000 words with citations, threat-model table, and proposed patterns.
```

## Stream D — Alternative formats / new format

Research ID: `r_01ks6kackkhzfdckbt1e5a9zn5`. Model: `exa-research`.
Cost: $0.93. Searches: 54.

```
Research "data formats suitable for security/legal-grade specifications where brittleness is a feature, not a bug". Compare alternatives to TOML for the use case below.

USE CASE: A TOML-based public specification ships normative kind-descriptor files, instance examples, and machine-readable ontology files. The spec is the input to safe-language validators (primary in Rust, Go, and C). Hard invariants are enforced in validator code. The design ethos:
- TRUST IS THE CURRENCY
- BRITTLENESS IS A FEATURE (silent type coercion, permissive parsing, optional fields with magic defaults are ACTIVELY WRONG)
- PROCESS-TRUST OVER ARTIFACT-TRUST
- PRODUCER-SIDE RESPONSIBILITY
- DETERMINISTIC CANONICAL FORM (so artifacts can be sha256-hashed)
- MULTI-LANGUAGE SAFE PARSING (Rust/Go/C primary)
- NO JSON Schema, NO JSON-anchored canonicalisation (RFC 8785 JCS is rejected)
- NO eval, NO remote imports, Turing-incomplete

EVALUATION AXES:
1. Human readable and editable
2. Has a deterministic canonical form for stable hashing
3. One-to-one mapping between text and parse tree (no aliasing, no anchors, no `&`/`*`)
4. Rejects silent type coercion (Norway problem, JS-style)
5. Supports comments (intent travels with artifact)
6. Has a non-JSON-Schema schema mechanism (or none at all, validator-as-spec)
7. Safe parsers in Rust, Go, and C
8. Mature ecosystem
9. Acceptable verbosity for graph data

CANDIDATES TO EVALUATE (give a verdict per format):

- **TOML** (current) — https://toml.io/en/v1.1.0
- **CBOR** (RFC 8949) with deterministic encoding requirement
- **ASN.1 + DER** (canonical) — used in X.509, S/MIME, RFC 5912
- **CDDL** (RFC 8610) as schema language for CBOR/JSON
- **S-expressions** (canonical S-exprs, RFC draft Rivest)
- **EDN** (Extensible Data Notation from Clojure) — https://github.com/edn-format/edn
- **KDL** (KDL Document Language) — https://kdl.dev/
- **RON** (Rusty Object Notation) — https://github.com/ron-rs/ron
- **NestedText** — https://nestedtext.org/ (Python ecosystem; explicit no-coercion)
- **Pkl** (Apple) — https://pkl-lang.org/
- **Nickel** (Tweag) — https://nickel-lang.org/
- **Dhall** — https://dhall-lang.org/
- **CUE** — https://cuelang.org/
- **KCL** — https://kcl-lang.io/
- **Jsonnet** / **Starlark** — note: typically rejected for Turing-incompleteness or eval concerns
- **capnproto / FlatBuffers** — binary schemas
- **Concise Data Description Language (CDDL)** standalone

Also evaluate **YAML** explicitly (Norway problem, billion-laughs, anchor aliasing — and conclude it should be rejected) and **JSON** (no comments, silent coercion in many parsers, no canonical form, no integers — conclude reject).

Verdict per format on axes 1–9. Identify a winner among existing formats, or conclude that no existing format meets all criteria and a new format should be designed.

If a new format is recommended, sketch:
- Syntax (with one example showing graph data)
- Canonicalisation algorithm
- How comments are handled in canonicalisation (excluded from hash, but preserved in text — or hashed separately?)
- Schema mechanism (validator-as-spec? small CDDL-like sidecar? inline annotations?)
- Comparison to nearest existing format and why the new one is needed

Deliver: ~2500–3500 words with citations, format-by-axis matrix, and either a clear winner or a new-format sketch.
```
