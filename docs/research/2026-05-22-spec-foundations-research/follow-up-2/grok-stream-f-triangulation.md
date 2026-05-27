# Grok (grok-build) — Stream F triangulation (second opinion)

Run via `llm-gateway` with Exa MCP, always-approve. Job ID: `5f919bdc-d77a-4caf-a98c-cd379f57c61f`.
Duration: 112s. 14519 bytes stdout.

Tasked with second-opinion on the Exa Deep Researcher's capability-envelope
recommendation.

---

**SECOND OPINION: Declarative capability envelopes (hybrid dCBOR + CDDL + COSE_Sign1 + DID keys + monotonic attenuation)**

I used only the `exa` MCP server for all verification and counter-evidence. No local repository access occurred. Focus: skeptical cross-check of the seven specific claims against primary sources (IETF drafts/RFCs, ETSI CAdES, CHERI papers, WASI specs, capability enforcement literature). Goal: find what a prior deep report likely overstated or missed.

## 1. CDDL as schema language; monotonic attenuation semantics; "MUST NOT include field X"

**Position:** CDDL (RFC 8610, 2019) is the correct *structural* choice for CBOR-shaped envelopes and is already used (non-normatively) inside COSE RFC 9052. It is weak-to-inadequate for strong negative constraints and for encoding *monotonic set-reduction* semantics without heavy prose supplementation.

**Evidence:**

- RFC 8610 defines groups, structs, tables, choices (`/`), optional (`?`), ranges, cuts (`^` for "exclusive or" in maps), and control operators (`.size`, `.regexp`, `.lt`/`.le`/`.gt`/`.ge`/`.eq`, `.within`, `.and`, `.cbor`). It excels at positive shape and occurrence.
- Negative patterns ("MUST NOT contain key X" or "forbidden field") have no first-class negation. Workarounds (omitting the key entirely + prose "must not be present", or complex `.not`-style via application logic) are common but error-prone and non-compositional for lists (e.g., "allowed_syscalls may only shrink").
- Monotonic attenuation (macaroon-style: a derived envelope must be a subset of the parent on sets like syscalls/paths/net) is a *semantic invariant*, not a schema feature. CDDL can type the container (array of `tstr` or `uint`) but cannot enforce "every element in child must appear in parent" or "no new elements" without external validators or prose + tests. The draft dCBOR document itself shows similar limits when numeric reduction interacts with maps.
- Alternatives in the CBOR ecosystem remain limited: ABNF + prose (IETF default), or CDDL plus custom predicates. No widely adopted CBOR schema language is dramatically better at negation.

**Recommendation:** Use CDDL for the wire shape and required/optional fields. Move attenuation monotonicity, "MUST NOT introduce", and set-reduction rules to a dedicated "Semantics" section with executable tests (or a small reference validator). Do not claim CDDL alone suffices for policy.

## 2. dCBOR readiness for legal-grade signing

**Position:** Not ready. dCBOR (draft-mcnally-deterministic-cbor-17, 12 Feb 2026) remains an active *individual* Internet-Draft, not an RFC or CBOR WG consensus document. It carries material risks for canonicalization stability and interop.

**Evidence (direct from draft):**

- Status: "I-D Exists", intended Standards Track, expires 16 Aug 2026. Replaces draft-bormann-cbor-dcbor; now co-authored by CBOR WG participants but still individual submission.
- Core rules (definite length only, preferred serialization, bytewise lex key order, no duplicate keys, NFC strings, single quiet NaN, numeric reduction of integral floats to ints) are stricter than RFC 8949 §4.2.
- Documented pitfall: Numeric reduction can turn otherwise-valid CBOR maps into invalid dCBOR (e.g., `{10: "ten", 10.0: "float ten"}` becomes duplicate-key after reduction). Applications "need to avoid" such cases.
- Implementation status (Section 4): Complete reference in Swift/Rust (Blockchain Commons), TypeScript; Ruby (partial, "checking of dCBOR exclusions not yet implemented"). No production-grade Go or C entries listed. Primary consumer appears to be Gordian Envelope.
- Security considerations focus on decoder validation failures producing non-identical byte streams — exactly the attack surface for signed envelopes.

**Recommendation:** Treat dCBOR as experimental/niche for now. For legal-grade or high-assurance signing, either (a) use strict RFC 8949 deterministic encoding + application-level rules + explicit test vectors, or (b) wait for dCBOR to reach RFC + demonstrate broad, maintained ports in safe primary languages (Rust/Go/C). The numeric-reduction edge cases and narrow impl surface are real counter-evidence to "ready."

## 3. COSE_Sign1 + DID-bound keys for legal-grade non-repudiation, attenuability, revocation, eIDAS/CAdES

**Position:** COSE_Sign1 (RFC 9052, 2022) is solid, mature CBOR signing with clear Sig_structure canonicalization. It is *not* a drop-in for legal-grade qualified non-repudiation in the eIDAS/QES sense, nor does it natively provide attenuation or revocation propagation.

**Evidence:**

- RFC 9052 defines COSE_Sign1 cleanly (protected + unprotected headers, payload, signature) and Sig_structure for ToBeSigned (context "Signature1", body_protected, external_aad, payload). Widely implemented for IoT/constrained use.
- DID keys: Technically feasible (did:key and similar resolve to COSE_Key-like material). Used in some W3C VC/DID flows.
- eIDAS / QES / CAdES: ETSI TS 101 733 (CAdES, CMS Advanced Electronic Signatures) is the dominant lineage for qualified/advanced signatures under the eIDAS Regulation. It layers CMS (ASN.1/PKCS#7) with mandatory content-type, signing-certificate, signature-policy-identifier, signing-time, commitment-type, plus validation data (CRL/OCSP refs, timestamps, archive-time-stamps, long-term-validation). No equivalent normative profile for COSE appears in the ETSI/IETF cross-references. COSE is not ASN.1 CMS; qualified signatures typically require QTSP-issued qualified certificates + specific preservation formats.
- Attenuation/revocation: COSE has no built-in caveats or macaroon-style first-party attenuation. Revocation is delegated to the key material (X.509 CRL/OCSP for traditional PKI; DID-specific status lists or doc updates for pure DID methods). Propagation timing and "grace periods" are application concerns.
- Counter-evidence on "legal-grade": High-assurance non-repudiation in regulated contexts (EU QES, certain financial/government) privileges formats with long-term validation, archive stamps, and QTSP infrastructure — CAdES/XAdES/PAdES territory.

**Recommendation:** Excellent for technical integrity, provenance, and constrained environments. For true legal non-repudiation, profile COSE under a qualified-signature framework or accept it as "technical signature" and layer separate legal wrappers. Attenuation and revocation must be specified at the envelope/application layer (e.g., chained signed claims with monotonic reduction + status mechanisms).

## 4–6. Seven fields, enforcement portability, Linux syscall names

**Position:** The seven fields are a reasonable minimal core but incomplete. Linux syscall names in a CDDL example are a portability and correctness liability. Enforcement is inherently fragmented; only abstract capability *interfaces* travel well.

**Evidence:**

- Missing or underspecified: environment variables (LD_*, TMPDIR, locale), IPC (Unix domain sockets, shm, fd passing/SCM_RIGHTS, signals), clocks (wall vs monotonic; precision/side-channel exposure), process spawning/fork/exec/shebang, randomness sources (getrandom vs /dev/urandom), crypto material access (keyrings, sealed keys, HSM), rlimits, cwd, ptrace, namespaces, io_uring, etc. Recent manifest-driven systems (e.g., layered Landlock + Seatbelt + protocol brokers) explicitly list env stripping, spawn blocking, secret scanning, and hostname vs port distinctions as first-class.
- Portability: seccomp-bpf (Linux), Capsicum (FreeBSD rights on descriptors + capability mode), macOS Seatbelt/sandbox-exec (profile language), OpenBSD pledge/unveil, Landlock (Linux 5.13+ path-based), CHERI (hardware fat-pointer capabilities, complements MMU, not a software layer portable to commodity CPUs without specific silicon). CHERI paper emphasizes hybrid model and RISC philosophy but is ISA-specific. No single kernel primitive is portable; "per deployment" is accurate.
- Syscall names: Linux `openat`/`socket`/`connect` etc. are not POSIX-2017 APIs (the latter are higher-level and implemented differently). BSD/Solaris/macOS diverge in availability, semantics, and numbering. WASI Preview 2 (component model, WIT) is deliberately *not* syscall-based: it uses versioned resource handles (`wasi:filesystem/types@0.2.0`, `wasi:sockets/tcp`, `wasi:cli/environment`, `wasi:clocks/*`, `wasi:random/*`, `wasi:http/outgoing-handler`). No ambient authority; explicit preopens and interposition for attenuation. Sockets proposal has a detailed POSIX-compatibility matrix showing many flags/behaviors are emulated or omitted (always non-blocking at core, etc.).
- Counter-evidence: Using Linux syscall lists in the schema couples the declarative form to one OS and makes cross-platform (Rust/Go/C) enforcement and auditing brittle.

**Recommendation:** Replace or supplement raw syscall names with abstract capability descriptors (WASI WIT worlds/interfaces preferred for portability, or a small POSIX-subset vocabulary with explicit platform notes). Add explicit top-level sections or groups for: `environment`, `clocks_and_random`, `ipc_and_fds`, `spawn_and_exec`, `crypto_sources`. Keep the seven as the security-critical compute/network/fs core; treat the rest as "ambient authority surface that must be declared or denied."

## 7. "Compression library opens socket = broken contract" — cryptographic observability

**Position:** Violation is observable to the *local enforcer* at runtime. It is not cryptographically observable/provable to a downstream consumer without an additional remote-attestation layer binding the measurement of the binary + the enforcement policy + the observed call to the signed envelope. The claim as stated overreaches.

**Evidence:**

- A signed envelope (dCBOR/CDDL + COSE_Sign1) attests the *declaration* and its producer. A runtime that detects an out-of-envelope syscall (via seccomp, Landlock, WASI host, etc.) can log or kill. That log is only as trustworthy as the runtime/TEE that produced it.
- True cryptographic observability to third parties requires (at minimum) RATS-style attestation (RFC 9334 architecture): hardware/software measurement of the binary, signed policy, and a signed violation record or quote that the consumer can verify against the original envelope. Without it, the consumer has only the runtime's word — too late, and forgeable by a compromised host.
- Capability literature (macaroons, Capsicum/CHERI, WASI) consistently treats enforcement as local; auditability for disputes requires extra machinery (evidence records, TPM/CHERI provenance, or full execution traces under attestation).

**Recommendation:** Either (a) scope the claim to "locally enforceable with auditable logs under a trusted runtime," or (b) add an explicit attestation profile (measurement + signed violation evidence) for consumers who need non-repudiable proof of breach. The latter is the only path to the stronger wording.

## What the prior deep report most likely missed or understated

- **dCBOR status and pitfalls:** Still pre-RFC with documented numeric-reduction hazards that directly affect canonical signing stability.
- **Legal format mismatch:** COSE_Sign1 is not CAdES/ETSI-qualified territory; eIDAS QES has a long, specific CMS-based lineage with archival and QTSP requirements.
- **WASI Preview 2 as the portable substrate:** Far better model for declarative, attenuable, cross-language capabilities than Linux syscall strings. WIT worlds give exactly the "what this component may import" surface needed for envelopes.
- **Attestation gap for Q7:** Observability to consumers is not automatic from the signed contract + runtime enforcement; it requires a binding attestation architecture.
- **Field completeness and ambient authority:** Real deployed manifest systems (Landlock + Seatbelt brokers, WASI hosts) treat env, spawn, clocks/random, and IPC as first-class surfaces. Omitting them creates easy bypasses.
- **Enforcement reality:** CHERI is hardware (future path), not a current portable software primitive. The "per deployment" story is correct but implies audit and TCB fragmentation that must be documented.
- **Monotonicity lives outside the schema:** CDDL + COSE gives structure and signature; the "only ever restrict further" rule is a separate, testable semantic layer.

## Overall verdict

**Solid** (with caveats): The hybrid technical direction (canonical CBOR + CDDL structural contracts + COSE signing + DID keys + monotonic attenuation as a design ethos) is coherent for producer-responsibility, process-trust envelopes in constrained or high-integrity settings. No JSON Schema, no Turing-complete primitives, no remote includes — all aligned with the stated ethos and safe-language primary targets.

**Weak** (needs explicit fixes): dCBOR readiness and interop claims; raw Linux syscall names for portability; "cryptographically observable to downstream" without attestation; legal-grade non-repudiation language (COSE ≠ QES/CAdES); completeness of the seven fields; and under-specification of how monotonicity and negative constraints are actually enforced beyond the schema.

**What I would change:**

- Make the schema use abstract capability descriptors (WASI WIT or a small platform-neutral vocabulary) rather than Linux syscall names.
- Add explicit groups/fields for environment, clocks/randomness, IPC/fds, spawn/exec, and crypto sources.
- Separate "structural schema (CDDL)" from "attenuation semantics + negative rules (prose + reference validator + tests)".
- Downgrade or caveat dCBOR to "experimental narrowing; RFC 8949 deterministic + strict rules is the safer baseline today."
- Clarify COSE_Sign1 scope as technical integrity/provenance; add separate profile or wrapper language for any regulated legal non-repudiation use.
- Add (optional but recommended) attestation binding for violation evidence when the consumer must have cryptographic proof rather than runtime assertion.
- Document the fragmented enforcement surface and the recommended portable abstraction layer explicitly.

The core idea is sound and worth pursuing, but several concrete claims need tempering or additional specification layers to survive skeptical review and real-world multi-OS, multi-language deployment. The report found a promising direction; the details require the precision the ethos itself demands.
