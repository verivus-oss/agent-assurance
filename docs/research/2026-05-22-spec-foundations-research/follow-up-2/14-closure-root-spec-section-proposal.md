# Proposed spec.md section — `closure_root` and the brittleness-propagation rule

**Status:** proposal for the spec maintainer. Not yet in `spec.md`.
**Date:** 2026-05-22.
**Author:** drafted from the research dossier under `docs/research/2026-05-22-spec-foundations-research/`.

---

## Instructions to the spec maintainer

### Proposed section number and title

**§12. The closure-root rule (brittleness propagation)**

### Placement in spec.md

Insert *immediately after* the existing §11 (`[provenance]` table and the
`[provenance.encryption]` sub-table at §11.1) and *before* the heading
that today follows §11 (the file currently ends after §11.1, so the new
§12 becomes the new tail of the document).

Nothing else needs to be renumbered. The existing §11 / §11.1 numbering
is preserved. Subsequent sections — none today — would shift by one.

### Top-level section vs. subsection of §11

**Recommendation: top-level §12, not a subsection of §11.**

`[provenance]` (§11) is an OPTIONAL informational annotation that records
*where this file came from*. The closure-root rule is a mandatory
mechanic that governs *what happens to downstream hashes when upstream
changes*. Folding it under §11 would imply it is only relevant when a
file carries a `[provenance]` table — but the rule applies to *any*
artifact that cites upstream evidence, including kind descriptors,
evidence matrices, gate-decision instances, and disclosure-profile
attestations that do not necessarily use the `[provenance]` block. The
two concepts are adjacent (both concern upstream linkage) but the rule
is broader in scope and stronger in normative force, so it warrants its
own section.

### Why this section is needed now

The brittleness-propagation rule appears only in the research synthesis
documents under
[`docs/research/2026-05-22-spec-foundations-research/`](../) — most
sharply in
[`08-follow-up-synthesis.md`](../08-follow-up-synthesis.md) (Stream B,
"brittleness propagation — the load-bearing innovation") and in the user's
binding design directive in
[`06-user-design-directives.md`](../06-user-design-directives.md) ("any
upstream attestation update intentionally breaks the downstream sha —
this is the signal mechanism for 'something changed; recheck'"). The
research convergence is exceptionally tight (four independent sources
arrived at the same mechanic), and the user has named it as one of the
spec's two load-bearing properties. Today the rule is invisible to
implementers reading only `spec.md`; that means the first wave of
runtimes will quietly restore the standard PKI behaviour (preserve
signature validity under upstream change), which silently collapses the
spec's brittleness-as-feature ethos. The rule must be normative and
spec-layer before any runtime profile concretizes the envelope format.

---

## Proposed section text (drafted for direct insertion into spec.md)

## 12. The closure-root rule (brittleness propagation)

DAG-TOML documents do not stand alone. Most conforming artifacts cite
upstream evidence: a `traceability` document cites requirement sources,
an `evidence-matrix` cites test-run digests, an `assertion-bundle`
cites adapter contracts, a `disclosure-attestation` cites the
unredacted artifact it disclosed selectively. This section defines a
single normative rule governing the relationship between an upstream
artifact's identity and the downstream artifact that depends on it:
**upstream changes MUST break downstream hashes.** The rule is the
opposite of the property most existing PKI infrastructure attempts to
preserve, and the inversion is intentional.

### 12.1 The rule

Every DAG-TOML document that cites upstream evidence MUST carry a
`closure_root` field whose value is a cryptographic digest over the
canonical concatenation of:

1. Every upstream artifact hash this document depends on, in canonical
   sorted order.
2. Every upstream revocation snapshot known to the producer at the time
   of document emission, in canonical sorted order.

The digest algorithm MUST be SHA-256 or stronger. Weaker algorithms
(MD5, SHA-1) are forbidden. The exact set of cited upstream artifacts
is the closure of every field whose ontology mapping is `cites_upstream`
(declared in the relevant `*-kind.toml` descriptor), every
`[provenance].source_sha256` entry, and every `[[evidence_*]]` entry
that carries an upstream digest.

`closure_root` is part of the document's signable content. Any signed
envelope wrapping the document MUST cover the `closure_root` field. The
producer MUST emit `closure_root` before any signing ceremony.

`closure_root` MUST appear at the root level of the document (sibling to
`[meta]`, `[provenance]`, and the kind-specific tables) as a single
string value of the form `sha256:<lowercase-hex-digest>` (or
`sha384:`, `sha512:`, etc., for stronger digests).

### 12.2 The cascade-break property

When any upstream artifact's hash changes, or any upstream revocation
list adds an entry that affects the closure this document depended on,
a downstream document that recomputes `closure_root` MUST produce a
different value. Any signed envelope wrapping the downstream document
MUST then become invalid until the document is re-emitted with a
refreshed closure and a new signing ceremony.

This behaviour is intentional. Verification fails visibly; consumers
observe the break locally without traversing upstream history.

### 12.3 Producer responsibility

Producers of a downstream document MUST:

1. Carry the current upstream closure into the document's
   `closure_root` field.
2. Carry the current upstream-revocation snapshot into the document's
   provenance evidence (and into the inputs to `closure_root`).
3. Re-emit a new signed document — with a new `closure_root`, a new
   signing ceremony, and a new artifact SHA-256 — whenever any upstream
   artifact or revocation snapshot changes.

A producer MUST NOT re-sign a downstream document under an unchanged
`closure_root` value when any input to that closure has changed.

### 12.4 Consumer responsibility

A consumer MUST verify that the document's `closure_root` value is
covered by the document's signed envelope (i.e. that the envelope
verifies against bytes that include the declared `closure_root`). The
consumer MUST NOT traverse upstream history to validate the closure;
the closure root makes upstream change locally observable, and
upstream traversal is the producer's responsibility, not the
consumer's.

### 12.5 What this section does NOT specify

This section is envelope-agnostic and primitive-agnostic. The
following are explicitly out of scope and are owned by profiles or by
RUNTIME-SPEC documentation:

- Signing-envelope format (CMS_Sign1 in ASN.1 DER, COSE_Sign1 in
  deterministic CBOR, DSSE, or any future envelope).
- Asymmetric signing primitive (Ed25519, ECDSA, RSA-PSS, ML-DSA, etc.).
- Transparency-log target (SCITT, Rekor, self-hosted Trillian, or
  none).
- Key-aging policy, revocation-publication cadence, and timestamp
  authority selection.
- The exact canonical-concatenation algorithm used to compute
  `closure_root` over the inputs of §12.1 (see §12.7).

A profile that layers concrete cryptography on top of this rule MUST
preserve §12.1–§12.4 verbatim and MUST NOT introduce mechanisms that
suppress the cascade-break property of §12.2.

### 12.6 Worked example

```toml
[meta]
schema_version = "1.0.0"
template_kind  = "evidence-matrix"
docs           = "https://github.com/verivus-oss/agent-assurance/blob/main/spec.md"

# closure_root is a SHA-256 over the canonical concatenation of every
# upstream artifact hash this document depends on plus every upstream
# revocation snapshot known at emission time. A change to any input
# flips this value, which flips the document's own SHA-256, which
# invalidates any signed envelope wrapping the document.
closure_root = "sha256:6b1a8c5d2e3f4a7b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b"

[provenance]
source_path   = "REQUIREMENTS.md"
source_sha256 = "sha256:a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90"
source_bytes  = 8421
captured_at   = "2026-05-22T14:00:00Z"

# kind-specific tables follow…
```

### 12.7 Non-normative warning — this inverts standard PKI behaviour

Implementers familiar with X.509, PKIX, CMS, or PGP will recognise that
those systems are designed to *preserve* signature validity when
upstream artifacts change. A certificate signed today remains valid
tomorrow; revocation is a separate, out-of-band channel that consumers
poll. The closure-root rule deliberately reverses that property.

Implementers MUST NOT introduce mechanisms that paper over closure-root
changes. The following are forbidden:

- Re-signing a downstream document with a stale `closure_root` to
  preserve envelope validity through an upstream change.
- Storing `closure_root` in unsigned envelope attributes
  (`unsignedAttrs`, `unprotectedHeader`, or equivalent) where it is not
  covered by the signature.
- Defining "soft revocations" that update an upstream revocation list
  without flipping downstream closure-root values.
- Caching closure-root inputs across upstream versions (a "last-known-
  good" closure that survives an upstream change is the failure mode
  this section exists to prevent).

The brittleness is the feature. A downstream document whose signature
silently survives an upstream change is indistinguishable, to the
consumer, from a downstream document whose upstream was never
compromised. The closure-root rule makes that distinction mechanical.

---

## Implementer guidance (non-normative companion to the section)

### Common mistakes the section explicitly forbids

- **Re-signing on upstream change without a fresh producer ceremony.**
  A producer who refreshes only `closure_root` and re-signs with the
  same key, without the ceremony that establishes legal intent at the
  profile layer, has restored the X.509 behaviour the section
  forbids. Every closure-root refresh is a new signing event.
- **Storing `closure_root` in unsigned attributes.** Envelope formats
  (CMS, COSE) distinguish signed from unsigned attributes;
  `closure_root` MUST live in the signed payload.
- **Computing `closure_root` over a non-canonical concatenation.** Two
  validators that compute the closure over the same logical inputs
  in different byte order will produce different digests and will
  disagree on whether an envelope verifies. The profile that
  concretizes the digest computation MUST pin the canonical-
  concatenation algorithm explicitly.
- **Treating revocation as a soft signal.** A revocation that does
  not flow into `closure_root` does not propagate. Either it is in
  the closure or it is not in the spec.
- **Treating `closure_root` as a free-form audit field.** The field
  is normative payload, not human-readable metadata. Validators
  MUST reject documents whose `closure_root` value does not match
  the expected hash shape.

### Composition with existing `[meta]` and `[provenance]` fields

- `closure_root` is a *root-level field*, sibling to `[meta]` rather
  than a field inside it. This mirrors the spec.md placement of
  `[provenance]` (also root-level) and avoids implying that the
  closure root is `[meta]`-style discovery metadata. Like
  `[provenance]`, it travels with the document and is part of the
  signable surface.
- `[provenance].source_sha256` is *one input* to `closure_root` (when
  a document carries a `[provenance]` table). It is not a substitute.
  A document MAY carry a `[provenance]` table without a `closure_root`
  if and only if the document cites no upstream evidence (rare for
  conforming artifacts; the `[provenance]` table by itself implies at
  least one upstream input).
- `[meta].embargo_until` and `[meta].confidentiality` (§2.7) are
  declared posture and do NOT participate in `closure_root`. They
  change without breaking downstream hashes. This is intentional:
  posture is a policy declaration, not an upstream-evidence input.

### Interaction with the disclosure profile

Selective-disclosure proofs and redaction manifests in
[`profiles/disclosure/`](../../../../profiles/disclosure/) introduce a
question this section must answer: when a producer publishes a redacted
form of an artifact, does the redaction flip the upstream's
`closure_root` (and therefore break every downstream that depends on
it)?

**Recommendation:** No. Redaction does NOT flip the source artifact's
`closure_root`. The unredacted artifact and its redacted disclosure
are two distinct artifacts with two distinct SHA-256 values; the
redacted form carries its own `closure_root` that cites the unredacted
form as upstream. The unredacted artifact's `closure_root` is
unaffected by the act of publishing a redaction.

**Reasoning:** The closure-root rule fires on *changes to upstream
evidence*. Redaction is the production of a new, derived artifact; it
does not change the upstream artifact's bytes or its declared closure.
Consumers of the redacted form recompute against the *redacted form's*
closure root and verify against the *redacted form's* envelope.
Consumers of the unredacted form (those authorised to see it) are
unaffected. This preserves the property that closure-root cascade-breaks
are reserved for *real* upstream change — not for derivation events
that produce parallel artifacts.

Profile-layer text in [`profiles/disclosure/`](../../../../profiles/disclosure/)
SHOULD restate this clarification so disclosure-profile implementers
do not assume the closure-root rule forces a cascade on every
redaction.

---

## Risks and open questions

### Non-versioned upstream sources (live feeds, mutable URLs)

**Risk:** The closure-root rule assumes upstream artifacts have stable
digests. A live feed (HTTP endpoint that returns different bytes at
different times) breaks this assumption — the producer has no upstream
hash to commit into the closure.

**Recommendation:** Forbid live feeds as direct closure-root inputs.
A producer that wants to depend on data from a mutable source MUST
first snapshot that source into a digest-pinned artifact, then cite
the snapshot. The closure-root rule then applies to the snapshot, not
to the live source. Profile-layer text MAY define a "snapshot-of"
relation that captures the binding between snapshot and live source as
audit metadata, but the closure root MUST be computed over the
snapshot.

### Cycles

The existing spec.md §5 hard invariants forbid cycles in `[[depends_on]]`
inside an implementation-DAG. The closure-root rule extends this to all
upstream-evidence citation: **the closure graph induced by
`closure_root` inputs MUST be acyclic.** A document MUST NOT, directly
or transitively, cite an upstream artifact whose own closure depends on
this document. Validators that walk closure inputs MUST detect and
reject closure cycles. (The §5 enforcement mechanism — graph traversal
in the reference validators — extends naturally; no new machinery is
required at the spec layer.)

### Canonical concatenation algorithm

**Open question.** §12.1 specifies *what* `closure_root` is computed
over (the closure of upstream hashes plus the closure of revocation
snapshots, both in canonical sorted order). It does not specify the
byte-level canonical-concatenation algorithm (length-prefixing vs.
delimiter-separated, sort key collation, handling of duplicate inputs).

**Recommendation:** Defer to a profile or to a future
`§12.8 Canonical concatenation` subsection in spec.md. The most likely
target is dCBOR-based canonical concatenation (consistent with the
research dossier's Stream D convergence on dCBOR for wire/signing,
even when authored artifacts remain TOML). The choice MUST be made
before the first reference runtime ships; until then, the rule is
specified at the *property* level (cascade-break on any input change)
and runtimes that interoperate MUST pin the algorithm out-of-band.

Profiles that pin the algorithm MUST do so in their
`profile-descriptor` document (per spec.md §6.1) so consumers can
enumerate it without reading code.

---

## Cross-reference targets (for the spec maintainer's editorial pass)

Sections in `spec.md` that should gain a back-reference to §12 when this
proposal lands:

- §2.7 (confidentiality / license / embargo) — note that posture
  fields are deliberately NOT closure-root inputs.
- §5 (Hard invariants) — note that closure-graph acyclicity extends
  §5's cycle prohibition.
- §11 (`[provenance]` table) — note that `source_sha256` is a
  closure-root input when the document also carries upstream
  evidence outside `[provenance]`.
- §11.1 (`[provenance.encryption]`) — clarify that the closure-root
  rule fires on the SHA-256 declared by `source_sha256` regardless
  of whether the digest is computed over plaintext or ciphertext
  (the cascade-break property is unchanged).

The reverse direction — back-references from §12 to those sections —
is already drafted into the proposed section text above.
