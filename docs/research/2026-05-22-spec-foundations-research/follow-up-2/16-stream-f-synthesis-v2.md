# Stream F synthesis V2 — capability envelopes, revised

Four independent sources analyzed Stream F: the Exa Deep Researcher
(`exa-research-pro`, $1.54, 77 searches) plus three CLI agents giving
second-opinion triangulation (Codex/gpt-5.5 ~3.4 min, Gemini/3.1-pro
~2.3 min, Grok/grok-build ~1.9 min). The CLI agents were asked to
*verify and rebut* the Exa Deep recommendation, not re-derive it.

Convergence across the three triangulators is striking: they
independently arrived at the same six categorical critiques. The Exa
Deep proposal's strategic direction is endorsed; four specific design
choices need substantial revision; one major new primitive surfaced
that the original report missed entirely (CB-AdES).

This V2 supersedes the Exa Deep report (`exa-deep-f-capability-envelopes.md`)
as the canonical Stream F output. The Exa Deep file is preserved on
disk as historical record.

---

## 1. What survives — endorsed directions

All four sources agreed:

- **CBOR + COSE as the binary substrate.** Compact, memory-safe parsing
  in Rust/Go/C, no JSON-permissive parsing culture, mature signing
  primitives (RFC 9052).
- **Monotonic attenuation as the security shape.** Downstream
  envelopes can only narrow upstream ones. Capability tokens
  (macaroons), object-capability languages (E, Pony), Capsicum, CHERI
  all converge on this property.
- **No JSON Schema; no Turing-complete primitives in canonical form;
  no eval; no remote includes.** This is the right instinct.
- **Producer-side responsibility.** The producer declares and signs
  the operational bounds of their software; the consumer verifies
  against the declaration.
- **Per-deployment enforcement is inevitable.** No single OS primitive
  covers all targets. The spec must describe portable abstractions
  and accept per-platform conformance classes for enforcement.

These are the right invariants and remain unchanged.

## 2. What changes — six revisions to the Exa Deep proposal

### Revision 1 — Separate the schema layer from the attenuation calculus

**Original:** CDDL handles both the structural shape and the
attenuation semantics ("monotonic set-reduction").

**Revised:** CDDL handles the structural shape only. RFC 8610 has no
first-class negation; attenuation is a *logical* (relational)
property, not a structural one. Attenuation must live in a separate
normative algebra over parsed envelope values:

- Sets: child ⊆ parent (subset).
- Path-language grants: child paths contained in parent path-globs.
- Numeric bounds: child ≤ parent.
- Booleans: `false ≤ true` (more restricted is "smaller").
- Forbidden-field rules: enumerated separately, not as CDDL negations.

The attenuation calculus is enforced by the validator (per the
multi-language safe-language strategy) and shipped as executable test
fixtures so all three primary implementations (Rust/Go/C) produce
byte-identical accept/reject decisions on the same inputs.

**Citations:** [RFC 8610 §3.5 (control operators)](https://rfc-editor.org/rfc/rfc8610.html),
[RFC 8949 §4.2 (deterministic encoding)](https://www.rfc-editor.org/rfc/rfc8949.html).
JSON Schema's `not` keyword is what CDDL lacks — but JSON Schema is
off the table per the design ethos, and a small purpose-built
attenuation calculus is preferable to importing JSON Schema's
expressivity wholesale.

### Revision 2 — Replace draft dCBOR with frozen RFC 8949 profile

**Original:** dCBOR (draft-mcnally-deterministic-cbor) as the
canonicalization rule.

**Revised:** RFC 8949 Core Deterministic Encoding + frozen profile
rules, with floats prohibited at the schema level.

**Why:** All three triangulators independently flagged dCBOR as
unsuitable for legal-grade signing today. The numeric-reduction rule
("1.0 → 1") creates duplicate-key hazards documented in
[fxamacker/cbor #632](https://github.com/fxamacker/cbor) (Go) and
related issues. Implementation surface is thin: Swift and Rust have
complete dCBOR; Go is partial; C is missing. The draft expires
2026-08-16 and remains an individual submission, not a CBOR WG
consensus document.

**The frozen profile rules:**

- Definite length only.
- Preferred (shortest) serialization for each value.
- Bytewise lexicographic map-key order.
- No duplicate keys.
- NFC-normalized text strings.
- **Floats prohibited.** Honors the Stream D no-floats consensus and
  removes the entire numeric-reduction class of bugs.
- Integers are minimally encoded.
- Tags permitted only from a closed set (declared in the profile).

This profile is implementable today in any RFC 8949 library by
configuring a strict canonical mode. Test vectors pinned per the
multi-language strategy.

**Citations:** [RFC 8949](https://www.rfc-editor.org/rfc/rfc8949.html),
[draft-mcnally-deterministic-cbor-17](https://datatracker.ietf.org/doc/draft-mcnally-deterministic-cbor/17/) (rejected as canonicalization layer; rules cherry-picked).

### Revision 3 — CB-AdES (ETSI TS 119 152-1) for legal-grade signing

**Original:** COSE_Sign1 with DID-bound keys, claimed sufficient for
legal-grade non-repudiation.

**Revised:** COSE_Sign1 for *technical integrity*. For *legal-grade*
non-repudiation, profile under **CB-AdES (ETSI TS 119 152-1, published
March 2026)** — COSE Advanced Electronic Signatures.

**Why:** This is the most important single discovery from the
triangulation. Gemini surfaced ETSI TS 119 152-1, which appears to
have been published in March 2026 — almost certainly post-dating the
Exa Deep Researcher's training data. CB-AdES is to COSE what CAdES is
to CMS: the formal qualified-signature profile under the eIDAS
framework. It mandates COSE headers carrying:

- `xRefs` — X.509 certificate references (for trust-anchor binding).
- `rRefs` — CRL/OCSP revocation data references.
- `sigTst` — signature time-stamp tokens (RFC 3161 lineage).
- `arcTst` — archive time-stamp tokens for long-term validation.

This composes cleanly with the spec's Stream B closure-root rule:

- The closure root MUST be inside the signed payload.
- `xRefs` binds the signer's qualified certificate to the signature.
- `rRefs` lets the verifier check revocation status; revocation
  cascade-breaks downstream (matching the brittleness ethos).
- `sigTst` provides RFC 3161 time-stamping — independent proof that
  the signature existed at a declared time.
- `arcTst` enables eIDAS-grade long-term preservation.

**Two-tier signing model:**

- **Tier 1 — technical:** raw COSE_Sign1. For inter-agent / intra-
  substrate trust where legal non-repudiation is not required.
  Lighter; usable for high-volume signing.
- **Tier 2 — legal:** CB-AdES. For cross-organization release events,
  court-admissible artifacts, regulated industries. Heavier; usable
  where the artifact must survive legal challenge.

The spec specifies the *envelope*; the deployment chooses which tier.
Either tier carries the closure root.

**Citations:** [ETSI TS 119 152-1](https://www.etsi.org/standards) (CB-AdES, March 2026),
[RFC 9052 (COSE)](https://rfc-editor.org/rfc/rfc9052.html),
[RFC 9360 (COSE X.509 binding)](https://rfc-editor.org/rfc/rfc9360.html),
[RFC 3161 (TSP)](https://www.rfc-editor.org/rfc/rfc3161),
[eIDAS Regulation](https://eur-lex.europa.eu/eli/reg/2014/910).

### Revision 4 — WASI Preview 2 + WIT as the capability vocabulary

**Original:** Capability envelope field `allowed_syscalls` carrying
Linux syscall names (`read`, `write`, `open`, `close`, `stat`).

**Revised:** Capability envelope fields use **WASI Preview 2 WIT
interfaces** as the canonical vocabulary. Linux syscall filters
become one backend compilation target, not the canonical contract.

**Why:** All three triangulators converged on this. Linux syscall
names are not portable: numbers differ across architectures, BSD/
macOS diverge in semantics, POSIX-2017 is API-level (not syscall-
level), and the canonical envelope must be substrate-agnostic. WASI
Preview 2 is the only mature, OS-agnostic, capability-shaped
interface vocabulary in existence today:

- `wasi:filesystem/types@0.2.0` — file I/O with preopen restrictions
- `wasi:sockets/tcp@0.2.0` — TCP networking (separately, `wasi:sockets/udp`)
- `wasi:clocks/wall-clock@0.2.0` + `wasi:clocks/monotonic-clock`
- `wasi:random/random@0.2.0`
- `wasi:cli/environment@0.2.0` — environment variables
- `wasi:cli/exit@0.2.0` — process termination
- `wasi:http/outgoing-handler@0.2.0` — outbound HTTP
- `wasi:io/streams@0.2.0` — generic streaming

The envelope's `class-id` references the WIT *world* the artifact
imports. An artifact with `world: data-transform` cannot import
`wasi:sockets/tcp` at all — the *grammar of WIT itself refuses to
express the violation*, which is the strongest form of brittleness
the spec's ethos demands. (See Revision 6 for static observability.)

**Cross-platform mapping:** Implementations may compile WIT-declared
capabilities to whatever native enforcement layer is available
(seccomp+landlock on Linux, Capsicum on FreeBSD, sandbox-exec on
macOS, App Sandbox on iOS, etc.). The spec declares the *semantic
contract*; the runtime chooses the implementation.

**Citations:** [WASI Preview 2](https://github.com/WebAssembly/WASI/blob/main/docs/Preview2.md),
[wasi-filesystem](https://github.com/WebAssembly/wasi-filesystem),
[wasi-sockets](https://github.com/WebAssembly/wasi-sockets),
[WIT Reference (Component Model)](https://component-model.bytecodealliance.org/design/wit.html).

### Revision 5 — Expand the envelope fields

**Original:** Seven fields (`class-id`, `allowed_syscalls`, `permitted_paths`, `network_allowed`, `dependency_whitelist`, `cpu_bounds`, `memory_bounds`).

**Revised:** Map onto WIT interface dimensions. The envelope is
organized by capability *domain*, not by primitive *operation*:

```cddl
capability-envelope = {
  class-id: tstr,                              ; WIT world reference, e.g. "data-transform.v1"

  ; Resource bounds
  cpu-bounds: { max-cpu-ms: uint, max-cpu-percent: (uint / null) },
  memory-bounds: { max-bytes: uint },

  ; Capability grants (each: bool to deny entirely, or a sub-table to scope)
  filesystem: filesystem-grant / false,        ; preopens, read/write/exec scopes
  sockets: sockets-grant / false,              ; tcp/udp/ip-resolve, host/port allowlists
  http: http-grant / false,                    ; outgoing-handler grants
  clocks: clocks-grant / false,                ; wall vs monotonic; precision
  random: random-grant / false,                ; entropy source
  environment: environment-grant / false,      ; named var allowlist
  process-spawn: process-spawn-grant / false,  ; whether and which programs
  ipc: ipc-grant / false,                      ; shared memory, signals, fd-passing
  crypto-keys: crypto-keys-grant / false,      ; read vs use vs sign with which keys

  ; Dependencies (artifact-level, not capability-level)
  dependency-whitelist: [ tstr ],              ; canonical-form refs to upstream artifacts
}
```

The bool/sub-table choice for each grant makes the envelope readable:
`sockets: false` denies all networking; `sockets: { tcp-allowlist: [...] }`
scopes it.

**New fields beyond the original seven:**

- `clocks` — separated by precision (timing-attack surface).
- `random` — entropy source declaration (reproducible builds need
  this controlled).
- `environment` — environment variable allowlist (LD_PRELOAD attack
  surface).
- `process-spawn` — fork/exec declarations.
- `ipc` — shared memory, signals, fd-passing (the macOS Mach + Linux
  SCM_RIGHTS surface).
- `crypto-keys` — distinguishes read/export from sign-with/use-only.
- `http` — separate from raw sockets because HTTP semantics differ.

### Revision 6 — Static observability via WASM Component Model imports + runtime attestation profile

**Original:** "Compression library opens a socket" violation is caught
by runtime enforcement (seccomp etc.) and is cryptographically
observable downstream.

**Revised:** As stated, the original claim overreaches. The fix
has two complementary layers:

#### Layer A — Static observability at CI time (the strong form)

For artifacts that are WASM Components, the artifact itself declares
its *required imports* in its WIT world. Example:

```
package my-data-transform:lib;

world data-transform {
  import wasi:filesystem/types@0.2.0;
  // NOTE: does NOT import wasi:sockets/*
}
```

A consumer's CI tooling can statically parse the WASM binary, list
its imports, and **reject the artifact if its imports exceed the
declared `class-id`'s envelope**. This happens **before the artifact
ships**. No runtime needed.

**This is the strongest form of architectural type safety** —
exactly what the user's Turn 6 abstraction-class type-safety primitive
demanded. The "compression library opens a socket" violation becomes
a **parse-time error** at the consumer's gate, observable
cryptographically because:

1. Envelope is signed with closure-root (Stream B).
2. Envelope declares `class-id = "data-transform.v1"`.
3. WIT world `data-transform.v1` forbids `wasi:sockets/*` imports.
4. WASM binary's import section is part of its content hash.
5. Consumer's CI verifies: artifact's imports ⊆ envelope's grants.
6. Mismatch → CI rejects the artifact with the violation visible in
   the signed evidence chain.

#### Layer B — Runtime attestation profile (the supplementary form)

For non-WASM artifacts (native binaries, scripts, containers), static
observability is not possible — only runtime enforcement is. To make
runtime violations cryptographically observable downstream, the spec
adds a **`runtime-observation-attestation`** kind:

```cddl
runtime-observation-attestation = {
  artifact-id: tstr,
  artifact-content-hash: tstr,
  envelope-hash: tstr,                     ; the capability envelope this attests against
  enforcement-backend: tstr,               ; e.g. "linux-seccomp-landlock-v6.5"
  policy-compiler-version: tstr,
  observation-period: { from: time, to: time },
  events: [ event* ],
  violation-status: "none" / "soft" / "hard",
  artifact-state-after: tstr,              ; hash of artifact's post-run state
}
event = { kind: tstr, denied: bool, count: uint, sample-trace: tstr / null }
```

This attestation is itself signed (technical-tier COSE or legal-tier
CB-AdES) and carries a closure-root referencing the envelope.
Downstream consumers can verify: "Yes, an independent runtime
observer ran this artifact under this envelope, and the violation
status was `none`."

**The two layers compose:** WASM artifacts get static + runtime.
Native artifacts get runtime only. The spec recommends WASM
Component Model for high-stakes artifacts where static observability
is required by policy.

**Citations:** [WASM Component Model](https://component-model.bytecodealliance.org/),
[in-toto-run signed metadata](https://in-toto.readthedocs.io/en/latest/command-line-tools/in-toto-run.html),
[SLSA verification](https://slsa.dev/spec/v1.2/verifying-artifacts),
[RFC 9334 (RATS)](https://datatracker.ietf.org/doc/html/rfc9334).

## 3. Concrete revised envelope sketch

```cddl
; -- the capability envelope (canonical form: RFC 8949 deterministic CBOR + frozen profile) --

capability-envelope = {
  ; Identity
  class-id: tstr,                              ; e.g. "data-transform.v1"
  spec-version: tstr,                          ; envelope-schema version

  ; Resource bounds (always declared)
  cpu-bounds: { max-cpu-ms: uint, max-cpu-percent: (uint / null) },
  memory-bounds: { max-bytes: uint },

  ; Capability grants by WIT interface (each: false to deny, sub-table to scope)
  filesystem: filesystem-grant / false,
  sockets: sockets-grant / false,
  http: http-grant / false,
  clocks: clocks-grant / false,
  random: random-grant / false,
  environment: environment-grant / false,
  process-spawn: process-spawn-grant / false,
  ipc: ipc-grant / false,
  crypto-keys: crypto-keys-grant / false,

  ; Dependency declaration
  dependency-whitelist: [ tstr ],              ; canonical refs to upstream artifacts (closure-root members)
}

filesystem-grant = {
  preopens: [ tstr ],                          ; allowed preopen path prefixes
  read-allowed: bool,
  write-allowed: bool,
  exec-allowed: bool,
}

sockets-grant = {
  tcp-allowlist: [ host-port-pattern ] / false,
  udp-allowlist: [ host-port-pattern ] / false,
  ip-resolve-allowed: bool,
}

http-grant = {
  outgoing-host-allowlist: [ tstr ],           ; allowed host patterns
  max-concurrent-requests: uint,
}

clocks-grant = {
  wall-clock-allowed: bool,
  monotonic-clock-allowed: bool,
  precision-cap-ms: uint,                      ; bound timing-attack surface
}

random-grant = {
  entropy-source: "os" / "deterministic-seed" / "none",
  seed-if-deterministic: bytes / null,
}

environment-grant = {
  var-allowlist: [ tstr ],                     ; named variable allowlist
}

process-spawn-grant = {
  allowed-programs: [ tstr ],                  ; canonical-form artifact refs
  argv-pattern-allowlist: [ tstr ] / null,
}

ipc-grant = {
  shared-memory-allowed: bool,
  signals-allowed: [ tstr ] / false,
  fd-passing-allowed: bool,
}

crypto-keys-grant = {
  read-keys: [ key-id ],
  use-keys: [ key-id ],                        ; sign/decrypt with these
  generate-allowed: bool,
}

host-port-pattern = tstr                       ; e.g. "*.example.com:443"
key-id = tstr
```

**Compression library worked example:**

```cbor
{
  "class-id": "data-transform.v1",
  "spec-version": "1.0.0",
  "cpu-bounds": { "max-cpu-ms": 1000, "max-cpu-percent": null },
  "memory-bounds": { "max-bytes": 104857600 },
  "filesystem": {
    "preopens": ["/data/compress/*", "/tmp/*"],
    "read-allowed": true,
    "write-allowed": true,
    "exec-allowed": false
  },
  "sockets": false,
  "http": false,
  "clocks": false,
  "random": false,
  "environment": false,
  "process-spawn": false,
  "ipc": false,
  "crypto-keys": false,
  "dependency-whitelist": ["sha256:..."]
}
```

This is signed via either technical-tier COSE_Sign1 or legal-tier
CB-AdES. Either signature carries a closure-root over the envelope +
the artifact hash + every dependency hash.

**Class violation example:** the artifact attempts to import
`wasi:sockets/tcp`. CI parses the WASM binary, sees the import,
checks against the envelope's `sockets: false`, **rejects the
artifact at parse-time**. The violation is cryptographically
observable because the artifact's import list is part of its content
hash, and the closure-root signature binds the envelope to the
artifact.

## 4. Composition with the rest of the dossier

- **Stream A (KindLock).** The capability envelope IS a kind
  descriptor (or referenced by one). KindLock's two-layer fingerprint
  (text_digest + ast_digest) applies. The "envelope declares + WASM
  imports verified ⊆ envelope" check is a fixture in the conformance
  suite.
- **Stream B (closure-root + legal-grade attestation).** The
  envelope is signed; the signature carries the closure-root. The
  CB-AdES profile is added to Stream B's recommended legal-grade
  signing surface — this is the most important downstream change
  required by this V2. The closure-root proposal in
  `14-closure-root-spec-section-proposal.md` should be updated to
  explicitly cite CB-AdES as a permitted legal-tier envelope.
- **Stream C (separation-of-duty).** The `runtime-observation-
  attestation` must be signed by a runtime observer whose identity is
  cryptographically distinct from the artifact producer. Stream C's
  `not_same_as` rules apply.
- **Stream D (format selection).** TOML at the spec-document layer;
  canonical CBOR (RFC 8949 + frozen profile) at the wire layer. The
  capability envelope is one of the kinds that gets emitted to wire
  CBOR for signing — TOML stays as the human-authored form for
  spec-document content; CBOR is the canonical form for signing
  artifacts in transit.
- **Stream E (HW/SW/cognition layering).** Envelope enforcement
  layers: SW (validator parses canonical CBOR + verifies attenuation
  calculus) at the floor; HW (FPGA accelerated parse + verify) at
  the frontier; cognition (LLM-driven policy synthesis to produce
  envelopes for new artifact classes) at the authoring layer. All
  three doors stay open.
- **Stream G (cost-record).** Cost records can be cited from the
  `runtime-observation-attestation` so the auditor can see the cost
  of the observation run.
- **Section 15 (source-analysis profile proposal).** The
  semantic-extraction `claim_kind` set composes with capability
  envelopes — a `quotation` node citing a confidential source can
  declare an envelope grant for the snippet's exact bytes only.

## 5. What's still open after V2

1. **Formalize the attenuation calculus.** "Child ⊆ parent" needs a
   concrete algorithm. Decide whether to embed it in the spec
   directly or publish as a separate normative document
   (`spec-attenuation-calculus.md`). The latter is cleaner and lets
   it evolve independently.
2. **Pick the CDDL / WIT boundary.** CDDL describes the
   *capability envelope's canonical wire shape* (the document above);
   WIT describes the *artifact's import surface*. The two are
   distinct artifacts. Clarify in the spec.
3. **CB-AdES adoption path.** ETSI TS 119 152-1 is months old. Library
   support is nascent. The spec should declare CB-AdES as the
   recommended legal-grade profile but accept CMS/CAdES wrappers as
   an interim path while the COSE ecosystem catches up.
4. **`runtime-observation-attestation` kind.** Needs its own kind
   descriptor + conformance fixtures. Could be added to Stream F or
   spun out as Stream H ("Runtime evidence attestation").
5. **WIT vocabulary versioning.** WASI Preview 2 is at 0.2.0; future
   versions will introduce new interfaces. The envelope's `class-id`
   must reference a pinned WIT world version, not just a name.
6. **Native (non-WASM) artifact handling.** WASM Component Model
   gives static observability for free; native binaries need
   different machinery. Document the two paths and the trust
   trade-offs.
7. **Closed set for `enforcement-backend`** in `runtime-observation-
   attestation`. Define the initial set
   (`linux-seccomp-landlock-vN.M`, `freebsd-capsicum-vN.M`,
   `wasmtime-vN.M`, `wasmer-vN.M`, etc.) and the extension policy.

## 6. Final position

The Exa Deep Researcher's strategic direction was right: CBOR-based
canonical encoding, COSE signing, monotonic attenuation, producer-
side responsibility. Five specific design choices were wrong or
incomplete, and the triangulation surfaced them with high
confidence and concrete evidence.

The single most important downstream change: **Stream B should
adopt CB-AdES (ETSI TS 119 152-1) as the recommended legal-grade
COSE profile.** This is a brand-new (March 2026) ETSI standard that
the prior dossier did not know about; it provides exactly the
qualified-electronic-signature framework Stream B's legal-intent
requirement needs. Without it, Stream B's COSE choice is technical-
grade only.

The second most important change: **WASI Preview 2 WIT interfaces
become the canonical capability vocabulary.** This solves the
Linux-syscall portability problem, gives every primary safe-language
implementation (Rust/Go/C) the same vocabulary to validate against,
and enables *static* cryptographic observability for WASM artifacts —
which is what the user's Turn 6 abstraction-class type-safety
primitive actually requires.

The third: **separate the schema layer (CDDL) from the attenuation
calculus.** CDDL is the wrong tool for set-reduction proofs. The
attenuation calculus belongs in a small purpose-built executable
specification that ships with conformance fixtures across the three
primary safe-language implementations.

V2 is the canonical Stream F output. The Exa Deep report remains on
disk as the historical first draft.
