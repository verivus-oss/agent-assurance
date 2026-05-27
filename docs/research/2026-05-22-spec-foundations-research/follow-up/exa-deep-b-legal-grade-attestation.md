# Exa Deep Researcher — Stream B — Legal-grade one-shot immutable attestation

Model: `exa-research-pro`. Cost: $2.22. Searches: 64. Pages crawled: ~187.
Research ID: `r_01ks6k8dwpnrb5zqgenfvvj0cq` (2026-05-22).

User-binding requirements (paraphrased): one-shot per sha256 artifact;
immutable; sha256 floor; legally provable intent; withdrawable/time-bounded;
brittleness-propagating downstream; producer-side responsibility; current
crypto only; mandatory for shippers.

---

## Requirements (binding)

1. Single artifact binding: exactly one SHA-256-hashed artifact, single-use.
2. Immutable: attestation does not transfer to other versions; no upgrades to signed artifact.
3. Hash floor: SHA-256 minimum; stronger allowed.
4. Legally provable INTENT: explicit evidence that the signer intended to sign (qualified signature properties, signing ceremony record, policy binding).
5. Withdrawable / time-bounded: keys age out; signatures revocable; revocation itself attested.
6. Brittleness-propagating: upstream revocation/updates intentionally break downstream attestations as a signal.
7. Producer-side responsibility: producers bear provenance burden; consumers verify last artifact.
8. Only existing crypto primitives.
9. Mandatory for shipped artifacts (policy requirement).

## Survey summary (concise mappings against the nine requirements)

### Group: in-toto, SLSA v1.2, Sigstore (Fulcio/Rekor), DSSE

- **in-toto** [spec](https://github.com/in-toto/attestation/blob/main/spec/README.md): binds artifact hashes and formal provenance predicates (reqs 1, 7 satisfied); does not mandate legal-intent attributes, built-in revocation, or brittleness propagation (partial 3; not 4, 5, 6, 9).
- **SLSA v1.2** [reqs](https://slsa.dev/spec/v1.2/requirements): prescriptive producer responsibility and immutable provenance requirements (reqs 1, 2, 7 satisfied); requires strong build/posture controls but does not itself provide legally-provable intent constructs or first-class revocation propagation (partial 3; partial/none 4, 5, 6, 9).
- **Sigstore / Fulcio / Rekor** [docs](https://docs.sigstore.dev/cosign/signing/overview): signs artifact hashes with ephemeral certs, records entries in append-only transparency log (reqs 1, 2, 7, 8 satisfied; short-lived keys help time-bounding) but does not by itself produce EU-style qualified-signature evidence of intent nor an attested revocation mechanism that intentionally breaks downstream hashes (partial 4, 5, 6).
- **DSSE** [protocol](https://github.com/secure-systems-lab/dsse/blob/master/protocol.md): simple binary signing envelope (reqs 1, 2, 7, 8 satisfied) but lacks legal-intent attributes, timestamp/revocation attestation mechanisms, and brittleness propagation semantics (not 4, 5, 6, 9).

### Standards & credential frameworks: RATS, EAT, COSE, SCITT, C2PA

- **RATS (RFC 9334)**: architecture for attester/verifier/relier with freshness, evidence, and trust-model primitives; strong fit for attestation lifecycle (helps 4 via attestation evidence patterns and 5 via freshness) but does not itself define single-use one-artifact binding semantics or legal-intent signature policy equivalent to QES (partial 1, 4, 5; full for attestation roles).
- **EAT (RFC 9711)**: token claims for device/entity attestation—good for structured claims and freshness (helps 1, 3, 4 partially) but not a legal signature regime; revocation must be layered (partial).
- **COSE (RFC 9052)**: canonical binary signing/encryption primitives for CBOR; provides canonical cryptographic envelope primitives (helps 1, 3, 8) but leaves policy, legal intent, and revocation semantics to higher layers (partial/none 4, 5, 6, 9).
- **SCITT** [draft](https://datatracker.ietf.org/doc/draft-ietf-scitt-architecture/03): registry + transparency + signed statements; aligns with transparency logging and revocation recording needs (helps 2, 5, 7) but still leaves legal-intent metadata and intentional brittleness semantics to profiles (partial).
- **C2PA** [spec](https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html): strong manifest/claim model and signed provenance for media (good for binding and metadata, supports timestamps and revocation references) but its legal-intent semantics align to provenance rather than qualified electronic signature constructs (good for 1, 2, 3; partial 4, 5).

### Legal signature regimes: eIDAS (AES/QES) and US ESIGN/UETA

- **eIDAS (AES/QES)**: QES provides high-assurance, qualified certificates and QSCDs which give legal presumption of intent/non-repudiation and certificate lifecycle controls (addresses 4 strongly and 5 via qualified cert lifecycles), but QES expects specific trust-service provider policies and hardware protections—not a developer-native one-shot attestation format per se (useful building blocks for 4 and 5).
- **US ESIGN / UETA**: legal validity for electronic signatures contingent on demonstrable intent and record association (requirement 4 supported in law), but cryptographic or revocation specifics are not strictly mandated (legal intent is evidentiary rather than a technical format).

### Revocation, timestamp and public logs

- **RFC 3161 TSP**: trusted timestamp tokens bind data existence to a time; useful to assert signature existence before revocation/expiry (addresses 5 time-anchoring).
- **Certificate transparency (RFC 6962 / 9162) and append-only logs (Trillian)**: provide public append-only evidence and inclusion/consistency proofs to detect misissuance; logs help publish revocations and issuance events but do not by themselves make signatures brittle—policy must treat log-recorded revocations as invalidating downstream artifacts (partial for 5, 6).
- **X.509 PKI + CRL / OCSP (RFC 5280 / RFC 6960)**: standard revocation mechanisms; timely revocation invalidates certificate chains used to verify signatures (addresses 5, partial 6 depending on client checks).
- **OpenTimestamps / blockchain anchoring**: immutable proof of existence but not revocable—does not support intentional brittleness (good for immutable time anchoring, not 5/6).

### Code-signing notarization platforms

- **Apple Notarization and Microsoft Authenticode**: provide publisher identity, timestamping, and revocation checks with platform enforcement; supply producer responsibility and revocation handling but generally aim to preserve valid signatures rather than intentionally break downstream attestations on upstream change (helpful for 4, 5, 7 but not 1's single-use nor 6).

### Serialization and canonical encodings (non-JSON targets)

- **ASN.1 DER**: canonical DER provides deterministic encoding suitable for signature coverage and legal formats (used by CMS/CAdES).
- **deterministic CBOR (dCBOR)**: deterministic CBOR profiles exist to make CBOR suitable for cryptographic signing while preserving CBOR's extensibility for metadata.
- **COSE / CMS Sign1 envelopes**: COSE Sign1 (CBOR) and CMS/PKCS#7 (ASN.1 DER) are standard non-JSON envelope formats that can carry signed attributes, certificates, timestamps, and revocation references.

### Implementation primitives (safe Rust / Go / C)

- **Cryptography**: safe Rust libs (ring, signatory, Tink bindings) provide Ed25519/ECDSA/RSA/HMAC primitives; Go stdlib provides crypto/ed25519, crypto/ecdsa and RFC-compliant primitives; OpenSSL (C) provides broad support including TS APIs.
- **RFC 3161 TSA implementations**: sigstore/timestamp-authority (Go) and existing OpenSSL TS APIs (C) and Rust crates provide timestamp services.

### Brittleness propagation patterns (examples)

- **Use of revocation bitstrings/status lists** published in a log: a compact bitstring marks revoked indices; downstream verifiers treat any set bit as immediate invalidation (breakage) of attestations tied to that index.
- **Registry/log publication of delegation/endorsement changes**: transparency logs (Trillian/Rekor) record revocations or new versions; downstream artifacts that reference upstream hashes see mismatch and fail verification (causing intentional breakage).

## GAP analysis (named gaps)

**Gap 1 — Composition**: No single existing system provides the exact combination required: a one-shot, per-artifact SHA-256 attestation that also carries legally-provable signer INTENT (e.g., QES-equivalent evidence) plus a standardized revocation model that both (a) attests revocation events and (b) deliberately propagates brittleness to downstream artifacts. Existing tools supply parts: provenance binding (in-toto, SLSA), transparency and short-lived keys (Sigstore), legal-intent primitives (CAdES/CMS + eIDAS), and time-anchors (RFC 3161/Opentimestamps), but no single end-to-end profile composes them with mandated producer responsibility and intentional brittleness semantics.

**Gap 2 — Legal-intent evidence vs. automated ephemeral signing**: Sigstore/OpenPubkey patterns give strong workload identity but not the procedural, legally-qualified ceremony evidence (QES semantics) needed to meet eIDAS presumption; conversely QES presumes QTSP involvement and hardware QSCDs rather than ephemeral developer keys. A standardized, pragmatic bridge between QES-style evidence and automated developer signing is missing.

## Composite design (concise blueprint that fills the gap, using only existing crypto)

### Canonical envelope: CMS_Sign1 (ASN.1 DER)

The canonical outer envelope (deterministic bytes for legal admissibility) carries:

- **encapContentInfo** = OCTET STRING containing the artifact SHA-256 hash (single artifact only).
- **signedAttrs**: include CAdES attributes: signing-certificate-v2, signature-policy-identifier (policy OID), commitment-type-indication; plus a mandatory dCBOR metadata attribute (deterministic CBOR block) describing signing ceremony fields (user auth method, authenticator attestation, nonce, human-present flag).
- **signature**: produced by short-lived signer key (Ed25519 / or ECDSA / RSA-PSS) held in an authenticator enforcing user presence (WebAuthn/FIDO2 style) to provide explicit intent evidence.
- **unsignedAttrs**: include RFC 3161 TimeStampToken(s) for the signature and revocation evidence fields: CRL/OCSP responses and an HMAC-protected (signed) bitstring status list reference with log inclusion proof (Trillian/Rekor entry and inclusion proof).

### One-shot semantics & immutability

The envelope MUST include exactly one artifact hash and signature covers the signedAttrs (including the dCBOR ceremony record). Any new artifact version has a different SHA-256 hash and thus requires a new envelope; the envelope is immutable by DER encoding and signed attributes.

### Legally provable intent

The dCBOR ceremony record (canonical) contains human presence proof: authenticator attestation, user verification method, ephemeral key nonce, and counters; signedAttrs include CAdES policy OID and commitment type; when the signing key is backed by a QSCD or FIDO attester and the policy maps to an accepted signature policy (or QTSP), this provides evidence aligning with eIDAS/AES/QES concepts (policy binding + device attestation).

### Withdrawable / brittleness propagation

Short-lived signer keys are registered and revocations are published as signed revocation entries in a transparency log (Trillian/Rekor). A compact bitstring status list (indexing known short-lived key IDs) is generated, signed by the revocation authority, and recorded in the log. Verifiers treat any revocation bit-set for a signer key as immediate invalidation of attestations signed by that key (downstream verification fails intentionally—brittleness).

### Producer responsibility & mandatory policy

Shipper organizations require every released artifact to have a CMS_Sign1 envelope per the profile; producers perform build → SHA-256 → dCBOR ceremony record → sign (authenticator) → timestamp (RFC 3161) → publish to transparency log including revocation/CRL references (producer responsibility enforced by policy).

## Implementation mapping (safe stacks)

- **ASN.1 DER / CMS + CAdES**: use ASN.1 DER tooling (Rust asn1 crates / Go encoding/asn1 / OpenSSL in C) to generate CMS/CAdES structures.
- **dCBOR ceremony block**: encode with deterministic CBOR implementation (Rust dcbor crate / libcbor in C / CBOR libraries in Go with deterministic options).
- **Signatures & authenticators**: Ed25519/ECDSA via ring or signatory in Rust, crypto/ed25519 in Go, OpenSSL EVP in C; require authenticator attestation (WebAuthn/FIDO) to prove user presence.
- **Timestamping & logs**: RFC 3161 TSA (sigstore/timestamp-authority for Go; OpenSSL TS APIs for C; Rust RFC3161 crates) and publish envelope + revocation entries to Rekor/Trillian for inclusion proofs and bitstring status list anchoring.

## Operational rules (concise)

- **Canonical formats**: mandate ASN.1 DER for outer envelope and deterministic CBOR for embedded ceremony metadata.
- **Signing ceremony**: require authenticator attestation + user verification; include counters/nonces in dCBOR; sign as part of signedAttrs.
- **Revocation & brittleness**: publish revocations to an append-only log and update signed bitstring status lists; verifiers must treat revoked bits as immediate invalidations.
- **Policy binding**: signature-policy OIDs and CAdES attributes must be present and resolvable by verifiers.

## Key citations (selected)

- in-toto attestation framework — https://github.com/in-toto/attestation
- SLSA v1.2 — https://slsa.dev/spec/v1.2/requirements
- Sigstore — https://docs.sigstore.dev/cosign/signing/overview
- DSSE — https://github.com/secure-systems-lab/dsse
- RFC 9334 RATS — https://datatracker.ietf.org/doc/html/rfc9334
- RFC 9711 EAT — https://datatracker.ietf.org/doc/html/rfc9711
- RFC 9052 COSE — https://datatracker.ietf.org/doc/html/rfc9052
- RFC 5652 CMS — https://datatracker.ietf.org/doc/html/rfc5652
- RFC 5126 CAdES — https://datatracker.ietf.org/doc/html/rfc5126
- RFC 3161 TSP — https://www.ietf.org/rfc/rfc3161.txt
- RFC 6962 Certificate Transparency
- SCITT architecture draft — https://datatracker.ietf.org/doc/draft-ietf-scitt-architecture/
- C2PA spec — https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html
- eIDAS QES — https://www.e-signature.eu/en/3-types-of-eidas-signature-simple-advanced-and-qualified
- Trillian — https://transparency.dev
- dCBOR — https://datatracker.ietf.org/doc/draft-mcnally-deterministic-cbor
- Apple Notarization, Microsoft Authenticode — platform code-signing references
