# Follow-up streams — consolidated synthesis

Cross-comparison of four independent research outputs per stream (Codex,
Gemini, Grok, Exa Deep Researcher). Raw reports live in
[`follow-up/`](./follow-up/).

The convergence is unusually tight — four independent sources arrived at the
same composite design for each of the four streams. Naming differs; mechanics
are the same.

## Stream A — Kind-descriptor drift: converged design

**All four sources converge on the same mechanism.** Different names:

| Source | Name |
|---|---|
| Codex | KDLL — Kind Descriptor Lockstep Ledger |
| Exa Deep | KindLock |
| Gemini | Cryptographic AST-Fingerprinted Lineages |
| Grok | Content-addressed layered manifest (clayers-inspired) |

**Mechanical core (the union):**

1. Each `*-kind.toml` descriptor extracts to a normalized AST. Prose
   `description` blocks also extract to a constrained-grammar prose-AST
   (disciplined templates, not free-form Markdown).
2. ASTs serialize via **deterministic CBOR (RFC 8949 + CDE)** — explicitly
   not JSON / JCS. SHA-256 over the canonical bytes yields a fingerprint
   per node.
3. Two-layer fingerprint per descriptor (Codex's contribution, strongest
   form): `text_digest` over canonical normative source text (comments and
   anchors included), and `ast_digest` over the parsed AST. Either changing
   without an explicit version bump is a CI hard failure.
4. Each of the three primary safe-language validators (Rust, Go, C) emits
   the same descriptor digest, the same error-code corpus, and the same
   canonical output bytes for a shared **golden-master conformance fixture
   suite**. The fixtures are language-agnostic, encoded in dCBOR.
5. Every normative prose paragraph gets a stable anchor; every descriptor
   rule names the prose anchor it implements; every prose anchor using
   normative terms must name a descriptor rule. Unpaired prose or rules
   fail CI.
6. Property-based generators derived from descriptors produce additional
   witness fixtures (one valid + one invalid example per rule, minimum).
   Generators are non-normative; their *output* fixtures are.
7. The descriptor release bundle = descriptor + prose digest map + fixture
   corpus + canonical AST hash + per-language validator conformance
   hashes. A downstream artifact embeds only the descriptor digest and
   release receipt.

**CI failure diff format** must be both machine-parsable (canonical dCBOR
with ProseHash, ValidatorHash diffs, failing fixture inputs/outputs) and
human-readable side-by-side (prose says X, validator does Y, fixture #N
expected Z got W).

**Brittleness is built in:** changing prose without bumping the descriptor
fails CI; changing the descriptor without refreshing fixtures fails CI;
validator divergence across Rust/Go/C fails CI.

## Stream B — Legal-grade one-shot immutable attestation: converged design

**Gap (all four agree):** no existing system combines all nine requirements.
The closest each system gets:

| System | Strengths | Critical gaps |
|---|---|---|
| in-toto + DSSE | Predicate/statement/envelope; subject sha256 binding | No legal intent; no built-in revocation propagation |
| SLSA v1.2 | Producer responsibility; build-pipeline provenance | Attests pipeline, not content (TanStack worm) |
| Sigstore / Fulcio / Rekor | Ephemeral keys + transparency log | OIDC root of trust is not legal intent |
| RATS (RFC 9334) + EAT (RFC 9711) | Platform attestation roles | Platform state, not legal will |
| COSE (RFC 9052) | CBOR signing envelope | Pure crypto — no policy/intent semantics |
| SCITT | Append-only signed statements + receipts | Profiles still owe legal-intent metadata |
| eIDAS QES | Strongest legal non-repudiation primitive | Doesn't model supply-chain closure or one-shot artifact binding |
| RFC 3161 TSP | Independent signing-time | Proves existence, not intent |
| RFC 6962 / 9162 CT, Trillian | Append-only public log | Logs publish facts; brittleness propagation is policy, not protocol |
| X.509 + CRL/OCSP | Revocation infrastructure | Designed to *preserve* signature validity, not break downstream hashes |
| C2PA | Manifest + claim signing for media | Provenance, not signature intent |
| WebAuthn/FIDO2 | Authenticator attestation, user presence | Not legal non-repudiation by itself; usable as ceremony evidence |

**Composite design (consensus):**

Names: Codex = **OSIA (One-Shot Intent Attestation)**; Gemini =
**QES-anchored COSE Attestations with SCITT Receipts**; Grok = **DSSE
in-toto + EAT + RFC 3161**; Exa Deep = **CMS_Sign1 + CAdES + dCBOR
ceremony + RFC 3161 + Trillian bitstring revocation**.

The composite (union of strongest pieces):

- **Outer envelope:** CMS_Sign1 in ASN.1 DER **OR** COSE_Sign1 in dCBOR.
  ASN.1 DER has stronger legal precedent (CAdES, eIDAS); COSE has lighter
  tooling and a cleaner pairing with dCBOR. **Profile-by-jurisdiction**
  rather than picking one globally.
- **Payload (the `intent_statement`):** artifact SHA-256+, artifact media
  type, kind descriptor digest, exact version, **upstream closure root**
  (the brittleness-propagation signal), signer identity, authority basis,
  key validity interval, revocation endpoint/log, ceremony transcript
  digest, and an explicit human-readable declaration ("I intend to sign
  exactly this artifact digest for release as version X"). **The
  declaration is signed payload, not UI chrome.**
- **Signed attributes (CAdES profile or COSE equivalent):**
  signing-certificate-v2, signature-policy-identifier (policy OID),
  commitment-type-indication (so legal intent is bound to the signature),
  signing-time, content-hash-algorithm.
- **Signing ceremony (the legal-intent layer):** key MUST be held in a
  QSCD or FIDO2 authenticator that enforces user presence/verification on
  every signing operation. The ceremony record is a deterministic-CBOR
  block bound into signedAttrs: authenticator attestation, user
  verification method, ephemeral key nonce, counters, human-present flag.
  Automated shippers use an HSM key that only signs after a release
  policy ceremony completes.
- **Timestamp:** RFC 3161 TSA token over the signature; required for
  long-term validity, captures existence before any later revocation.
- **Transparency:** publish to SCITT (or Rekor/Trillian) for append-only
  registration; the receipt's Merkle inclusion proof goes in
  `unsignedAttrs`.
- **One-shot uniqueness:** transparency-log-enforced rule that
  `(signer authority, artifact_sha256, intent_scope)` may be registered
  once. A second signature over the same bytes is a *new* intent
  statement with a different reason, never an upgrade.
- **Revocation = append-only fact, not mutation.** A revocation statement
  references the original signature, artifact digest, log index, reason
  code, effective time, authority. Signed by a time-bounded revocation
  key (or the original signer while valid), timestamped, logged. **It
  never mutates the original attestation; it creates a later legal
  fact.**
- **Brittleness propagation (the load-bearing innovation):** producers
  include the current upstream-revocation snapshot as part of every
  downstream artifact's *closure root*. Upstream changes flip the closure
  root → flip the downstream artifact's `intent_statement` hash → flip
  the downstream artifact's SHA-256. Verification fails visibly. This is
  the **opposite** of standard signing systems (which try to preserve
  signature validity under upstream change).
- **Consumer responsibility (minimal):** (1) verify final-artifact
  SHA-256 matches signed `intent_statement`; (2) verify signature against
  current revocation snapshot; (3) verify timestamp; (4) verify SCITT
  inclusion proof. **No upstream traversal required.**
- **Producer responsibility (full):** carry the closure root forward,
  refresh revocation snapshots, re-sign on any change.

**Cryptography used (no novel primitives):** Ed25519 / ECDSA / RSA-PSS;
SHA-256+; CBOR/CMS DER; existing RFC primitives end-to-end.

## Stream C — Separation-of-duty validation: converged design

**Universal rule (all four sources):** *No entity may complete the
validation gate for an artifact it produced.* "Entity" must mean signing
key, service account, organization unit, build worker identity, model
lineage, *and* delegated authority class — not just username. For LLM
agents specifically: same model deployment + same controller =
self-validation, regardless of prompt differences (Codex's emphasis).

**Cycle (binding pattern):** Intent → Action → Proof → Audit.

| Step | Who | Cryptographic enforcement |
|---|---|---|
| Intent | Release authority | Signed manifest with a key distinct from any high-privilege build/deploy key. If the originator is an agent, the intent key must not be the same key the agent uses for Action. |
| Action | Producer (builder / trainer / deployer) | Producer-key signature on the artifact. Producer must not hold the *only* signing key for Proof or Audit artifacts. |
| Proof | Independent Proof-Validator | One of: (a) independent reproducible-build re-builder with byte-for-byte match, (b) TEE-attested re-execution, (c) MPC aggregate proof, (d) threshold signer where producer holds no share. Always to a key with a distinct root of trust. |
| Audit | Independent auditor (separate org / role / TEE root) | Audit attestation published to a transparency log (SCITT / Rekor / Trillian) with valid inclusion proof. |

**Cryptographic `not_same_as` constraints** in the release policy
(Codex's contribution):

- producer key ≠ validator key
- validator service ≠ same build job
- audit signer issued under independent role OID / SCITT registration
- threshold release includes ≥1 independent validator share

**Object-capability isolation:** the validator gets read-only artifact
access + append-only statement authority; never write access to the
artifact.

**Anti-gaming layer (all four sources cite the same threats):**

- *Predictable audits are gameable.* For ongoing processes (not artifact
  release): require randomized or externally-scheduled audits, minimum
  evidence floors, suspicion escalation policies. (Stackelberg auditor
  game research, arXiv 2605.06340.)
- *Dual-rubric pattern (Governance Gauntlet):* run two orthogonal
  rubrics in parallel — passing both is materially harder than passing
  one for a strategic auditee.
- *Auditor-agent gaming:* auditor commits to audit policies publicly
  (Stackelberg commitment limits auditee optimization); auditor produces
  TEE-attested execution records; cross-auditor redundancy via threshold
  or MPC.
- For *artifact release specifically* (vs ongoing processes): the gate
  is deterministic — no independent audit statement, no valid final
  artifact.

**Composition with producer-side responsibility:** producers ship the
artifact + the bundled Proof attestation + the bundled Audit attestation
+ the SCITT inclusion proof. Consumer minimal verification:

1. artifact hash matches signed Producer attestation;
2. ≥1 independent Proof attestation signed under a trust anchor separate
   from the Producer;
3. Audit attestation in transparency log with valid auditor key or
   threshold signature.

That's it. No upstream traversal.

## Stream D — Format selection: converged verdict

**No existing format wins on all nine axes simultaneously.** The
research is unanimous on this point.

**Closest contenders (each fails on at least one critical axis):**

- **TOML 1.x:** wins readability, comments, explicit types, duplicate-key
  rejection, multi-language parser availability; **fails** deterministic
  canonical form, has no schema mechanism, has implementation latitude
  on floats and timestamps, treats comments as non-semantic.
- **Deterministic CBOR (RFC 8949 + CDE) + CDDL (RFC 8610):** wins
  canonical form, schema mechanism without JSON Schema, Rust/Go/C parser
  parity, no eval, no remote includes; **fails** human readability and
  has no comment facility in the binary form.
- **Canonical S-expressions (Rivest draft):** wins one-to-one textual
  mapping, canonical form, no anchors/aliases; **fails** comment
  semantics, no standardized schema language, smaller ecosystem.
- **ASN.1 + DER:** wins deterministic encoding, schema language, mature
  Rust/Go/C parsers, used in every legal PKI document; **fails** human
  authoring ergonomics.
- **Dhall:** wins normalization + semantic hashing + total-language
  guarantees; **fails** multi-language parser parity (Haskell primary,
  partial Rust/C), forbidden by the ethos because it has imports.
- **CUE:** wins schema-as-data; **fails** because it's an evaluator
  (Go-centric runtime), violating the no-eval mandate.
- **YAML:** **rejected** for Norway problem, anchor aliasing,
  billion-laughs DoS, implicit-typing culture.
- **JSON:** **rejected** for silent coercion, no comments, no canonical
  form (RFC 8785 JCS rejected per ethos).
- **KDL, RON, EDN, NestedText:** various partial fits; none win
  outright.
- **Cap'n Proto / FlatBuffers:** wins canonical wire + multi-language;
  fails human authoring.

**Verdict (consensus across all four sources):** create a strict
profile / new format. Three of four sources lean toward a **strict
canonical TOML subset for human authoring + dCBOR for wire/signing**;
one (Exa Deep) sketches an S-expr-inspired textual format (SCDL).

The strict-TOML-subset proposal (Codex names it **CDT — Canonical
DAG-TOML**) is the most pragmatic and the most aligned with the
existing project lineage:

- Human-readable, line-oriented, UTF-8 only.
- Canonical bytes are the signed artifact; non-canonical input is
  invalid in release mode.
- Comments are allowed but parsed as anchored trivia and included in
  canonical text hashing (so legal review text is part of what was
  signed).
- **Forbidden:** floats, NaN/Inf, local time, implicit defaults,
  duplicate keys, mixed arrays, unbounded integers, includes, env
  reads, macros, eval, imports, anchors, merge keys, computed keys,
  schema-driven default insertion.
- Integers are canonical decimal only; binary data is lowercase base16
  with explicit type.
- Strings have one escape form; Unicode scalar validity required; no
  normalization.
- Tables and keys appear in canonical sorted order; producers format
  before signing; validators reject non-canonical order.
- References are explicit `@id` links inside a declared DAG; cycles
  are invalid.
- Schema is a CDT kind descriptor (per Stream A), not JSON Schema:
  closed records, required/optional fields, tagged unions, bounded
  arrays, regex by named deterministic profile, stable error codes.

**Canonicalization algorithm:**

1. Decode UTF-8; reject BOM, invalid scalars, forbidden controls,
   CR-only newlines.
2. Parse with bounded depth and bounded token sizes.
3. Reject non-canonical lexical forms immediately: key order, integer
   spelling, string escapes, comment placement, array layout.
4. Build AST with comment trivia attached to the following node or file
   header.
5. Validate descriptor constraints.
6. Emit canonical text with LF, one key per line, sorted tables,
   sorted keys, stable comment placement.
7. SHA-256 (or stronger) over emitted bytes; AST digest separately for
   rule compatibility.

**dCBOR is used only for attestation bundles, not for authored
artifacts.** That gives humans a brittle text format and machines a
mature signing envelope.

## Convergent build order

Three of four sources (Codex, Grok, Gemini) explicitly recommend the
same sequence; Exa Deep is consistent with it:

1. **D first — Canonical DAG-TOML / CDT.** Everything else depends on
   stable bytes, safe parsers, and deterministic hashes.
2. **A second — KDLL/KindLock descriptors.** Once the format is stable,
   bind kind rules, prose anchors, fixtures, and validator conformance.
3. **C third — separation-of-duty gates.** Gates need concrete artifacts
   and descriptors to validate.
4. **B last — OSIA attestation.** The legal/security capstone. It signs
   stable artifacts, descriptor digests, gate statements, and provenance
   closure roots — not a moving target.

## Design risks (compiled across streams)

- **Legal intent is jurisdiction-sensitive.** QES/eIDAS gives a strong
  EU path; global equivalence requires per-jurisdiction policy profiles.
- **Closure-root opacity.** "Consumer verifies only last artifact" can
  hide upstream evidence fatigue inside the producer. The closure root
  must itself be audited and logged, or the producer becomes an opaque
  trust oracle.
- **Canonical text with comments is stricter than developers expect.**
  Tooling must make non-canonical edits fail early with a clear error.
- **Safe C is a mandate but still risky.** The C validator should be
  small, allocation-bounded, fuzzed, and treated as a conformance peer
  — never a "convenience port."
- **Organizational-alias gaming.** Separation-of-duty can be faked if
  identity policy doesn't define control-domain separation, only key
  IDs.
- **Revocation liveness pressure.** If revocation status cannot be
  snapshotted, release must fail-closed rather than assume validity.
- **Descriptor/prose lockstep can become bureaucratic.** Every editorial
  change shouldn't break release; the spec needs a clear
  normative/non-normative boundary.
- **Deterministic rebuild gates are artifact-type dependent.** Require
  them where possible; require an explicit "not reproducible"
  declaration where not.
- **Canonicalization fragility.** Rust, Go, and C canonicalizers
  diverging by even one Unicode-normalization rule will silently break
  every signature in the ecosystem. The canonicalizer is the highest-
  value attack surface.
- **TEE supply chain.** TEE-attested proof depends on TEE firmware
  vendors; treat as a trust assumption, not a guarantee.
- **Auditor-agent gaming.** Auditors that are themselves agents need
  Stackelberg-style commitments, dual rubrics, and cross-auditor
  redundancy — otherwise the audit is theatre.

## What's left to research / decide

- **Envelope choice:** CMS_Sign1 (ASN.1 DER + CAdES, strongest legal
  precedent in EU) vs COSE_Sign1 (dCBOR, lighter tooling). Likely a
  *profile-by-jurisdiction* decision, not one-size-fits-all.
- **Transparency log governance:** SCITT (IETF, in development) vs
  Rekor (operational today) vs self-hosted Trillian. SCITT is the
  designed target; Rekor is the bridge.
- **Prose-extraction grammar.** The Stream A design requires a
  constrained-grammar prose form so descriptors are machine-parseable.
  This needs explicit design — a small DSL or a strict
  "structured-statement" convention.
- **Property-based generator catalogue.** What generators ship as part
  of the conformance suite? Mostly from Hypothesis/proptest tradition,
  but the catalogue is project-specific.
- **Reproducible-build coverage map.** Which artifact kinds support
  bit-for-bit reproducibility, which need TEE/MPC alternatives, which
  must accept "not reproducible" declarations.
- **Key-aging policy.** How short is "short-lived" for signer keys?
  How are revocation snapshots refreshed (push vs pull, frequency)?
