# Exa Deep Researcher — Stream F — Capability envelopes

Model: `exa-research-pro`. Cost: $1.54. Searches: 77. Pages crawled: ~114.
Research ID: `r_01ks6qhr5cmjz9bwb5xqvqhnd5` (2026-05-22).

Researches how an artifact's "capability envelope" can be declared in
machine-checkable form for the spec's abstraction-class type-safety
primitive.

**Note on this wave's completeness.** Stream F was launched as a four-way
parallel (Codex, Gemini, Grok via `llm-cli-gateway`, plus this Exa Deep
Researcher). The three `llm-cli-gateway` outputs aged out of the
gateway's job-result store before they could be retrieved and are
unrecoverable. The Exa Deep Researcher report below is the only Stream F
output that survived. Future re-runs of the three CLI agents would be
useful for triangulation; the gateway's job-retention behaviour should
be diagnosed before launching another long-async multi-stream wave.

---

## Core principle

A capability envelope must be a machine-checkable, canonical, and enforceable declaration of what an artifact is allowed to do at boundary crossing (e.g., allowed syscalls, file I/O scope, network prohibition, acceptable dependencies, and resource bounds) so that class violations cascade-break downstream regardless of signature validity ([WASM Component Model](https://component-model.bytecodealliance.org/design/wit.html)).

## Survey highlights — what matters to adopt, what to avoid

- **WASM Component Model + WIT:** interface types express explicit imports/exports and boundary interfaces; supports load-time validation and runtime traps; suitable for modular capability boundaries and attenuation via limited imports/exports. [Component Model docs](https://component-model.bytecodealliance.org/design/wit.html), [Explainer](https://github.com/WebAssembly/component-model/blob/main/design/mvp/Explainer.md).

- **CDDL / CBOR:** CDDL defines data shapes for CBOR and supports deterministic CBOR canonicalization when combined with canonicalization rules (useful for canonical signing); schema validation rejects unexpected fields but enforcement depends on validators. [RFC 8610](https://datatracker.ietf.org/doc/html/rfc8610), [dCBOR guidance](https://developer.blockchaincommons.com/dcbor).

- **OCaps lineage (E, Pony, CapTP, Cap'n Proto):** object-capability systems provide strong attenuation semantics and safe delegation patterns; Cap'n Proto declares interfaces and supports capability passing; these models demonstrate fine-grained, composable attenuation that is valuable to emulate. [Cap'n Proto](https://capnproto.org), [E language](http://erights.org), [Spritely CapTP](https://spritelyproject.org/news/what-is-captp.html).

- **Seccomp-bpf:** kernel-enforced syscall whitelists evaluated at runtime; violations produce kill/errno/trap behaviors; excellent for syscall-surface reduction but not expressive enough for whole-envelope semantics alone. [seccomp docs](https://www.kernel.org/doc/html/v4.19/userspace-api/seccomp_filter.html).

- **SELinux / AppArmor / Smack:** kernel LSM mandatory-access-control provides expressive type-enforcement policies for file, socket, IPC access; denies are enforced at syscall/object-access time and are appropriate for system-level envelope enforcement. [Linux LSM docs](https://docs.kernel.org/admin-guide/LSM/index.html).

- **CHERI:** hardware-enforced pointer capabilities provide monotonic attenuation and provenance for memory/control authority — very strong enforcement when available, but requires CHERI toolchain and platform. [CHERI ISA report](https://www.cl.cam.ac.uk/techreports/UCAM-CL-TR-951.pdf).

- **Capsicum:** descriptor-based capability mode (FreeBSD) supports monotonic rights reduction and capability-mode confinement; good model for descriptor-level attenuation. [Capsicum paper](https://papers.freebsd.org/2010/rwatson-capsicum.pdf).

- **Genode:** capability-passing microkernel framework with static configuration of component sessions; strong for expressing pre-declared envelopes in system composition. [Genode Foundations](https://genode.org/documentation/genode-foundations-23-05.pdf).

- **Java SecurityManager (JEP 411):** runtime stack-inspection model was brittle and viral in practice; deprecation demonstrates risks of general-purpose runtime permission evaluation for supply-chain/legal-grade attestations. [JEP 411](https://openjdk.org/jeps/411).

- **Macaroons & OAuth scopes:** macaroons provide cryptographic attenuable caveats; OAuth scopes are coarse-grained strings — useful for delegation ideas but insufficient alone for fine-grained artifact envelopes. [Macaroons paper (NDSS 2014)](https://www.ndss-symposium.org/wp-content/uploads/2017/09/04_3_1.pdf), [RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749).

- **OPA / Rego, AWS / GCP IAM:** policy languages and IAM systems show how declarative rules and conditionals scale; OPA/Rego is highly expressive and suited to verifying artifact metadata as a gate. [OPA docs](https://openpolicyagent.org/docs/policy-language), [AWS IAM](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html), [GCP IAM](https://docs.cloud.google.com/iam/docs/allow-policies).

- **in-toto layouts:** supply-chain layouts express expected commands/materials/products and verify step-by-step provenance; good precedent for declarative, signed expectations.

- **Verified languages (Verus / Dafny / F\* / Lean):** static verification enforces properties at compile/verify-time and produces high assurance for critical components; not a runtime envelope mechanism but excellent for proving class invariants at build-time. [Verus guide](https://verus-lang.github.io/verus/guide).

## Key synthesis — design properties that win

- Must be canonicalizable for legal-grade signatures (deterministic encoding) — [dCBOR guidance](https://developer.blockchaincommons.com/dcbor).
- Must be expressible as a strongly-typed envelope that validators can check without Turing-complete evaluation (no eval, no remote includes) — [RFC 8610](https://datatracker.ietf.org/doc/html/rfc8610).
- Must support grammar-level attenuation or explicit delegation semantics so downstream actors can receive strictly smaller envelopes (attenuation monotonicity exemplified by OCaps and Capsicum) — [Capsicum paper](https://papers.freebsd.org/2010/rwatson-capsicum.pdf), [CapTP intro](https://spritelyproject.org/news/what-is-captp.html).
- Minimize attack surface: prefer compact binary canonical formats (CBOR with deterministic rules) and small, well-specified schemas verified by multiple independent implementations — [CBOR/COSE drafts](https://www.potaroo.net/ietf/all-ids/draft-ietf-cose-rfc8152bis-struct-01.html).

## Selected approach (hybrid): CBOR canonical serialization + typed envelope schema

**Rationale.** CBOR + deterministic canonicalization gives unique bytes for signing (legal-grade COSE signatures); typed schema gives strong, static validation and makes attenuation explicit. Both are implementable in safe Rust/Go/C with existing libraries and have modest attack surface versus full DSL eval engines. [RFC 8610](https://datatracker.ietf.org/doc/html/rfc8610), [COSE draft](https://www.potaroo.net/ietf/all-ids/draft-ietf-cose-rfc8152bis-struct-01.html), [dCBOR guidance](https://developer.blockchaincommons.com/dcbor).

## Design checklist (policy requirements enforced by schema)

- **Deterministic canonicalization:** require canonical CBOR (dCBOR) before signature verification.
- **No Turing-complete primitives inside the envelope;** expressions are declarative lists/sets, bounded integers, patterns (globs) only.
- **Attenuability:** envelope fields are monotonic sets; downstream may present a subset envelope signed/derived via cryptographic attenuation (e.g., macaroons-like caveats or re-signing with restricted claims).
- **Enforcement layers:** schema validation at load-time; runtime enforcement by LSM/seccomp/CHERI/Capsicum per deployment.

## Concrete kind-descriptor schema (compact CDDL-like, maps to CBOR)

```cddl
cbor-compression-envelope = {
  class-id: tstr,                ; e.g. "compression-lib.v1"
  allowed_syscalls: [ tstr ],    ; e.g. ["read","write","open","close","stat"]
  permitted_paths: [ tstr ],     ; globs or prefixes
  network_allowed: bool,         ; false => no network syscalls or sockets
  dependency_whitelist: [ tstr ],
  cpu_bounds: { max_cpu_ms: uint, max_cpu_percent: (uint / null) },
  memory_bounds: { max_bytes: uint }
}
```

Example instance (CBOR-serializable; shown in JSON-like form for readability):

```json
{
  "class-id": "compression-lib.v1",
  "allowed_syscalls": ["read","write","open","close","stat"],
  "permitted_paths": ["/data/compress/*", "/tmp/*"],
  "network_allowed": false,
  "dependency_whitelist": ["zlib", "lzma"],
  "cpu_bounds": {"max_cpu_ms": 1000, "max_cpu_percent": null},
  "memory_bounds": {"max_bytes": 104857600}
}
```

Producer serializes this with canonical CBOR rules, then signs via COSE using a DID key reference. [COSE draft](https://www.potaroo.net/ietf/all-ids/draft-ietf-cose-rfc8152bis-struct-01.html), [DID core](https://www.w3.org/TR/did-core/).

## Validation error example

Observed artifact metadata (manifest) shows `observed_syscalls: ["open","read","socket"]`. Schema rule: `network_allowed == false` disallows any syscall in a network-syscall set (e.g., `socket`, `connect`, `sendto`). Validator canonicalizes manifest + envelope, runs schema check, produces deterministic rejection:

```
ValidationError: ConstraintViolation
  class-id: compression-lib.v1
  violation: network syscall observed: "socket"
  location: /observed_syscalls[2]
```

## Stream B integration (producer: legal-grade attestation)

- Producer constructs the CBOR envelope instance, canonicalizes to canonical CBOR, and creates a COSE signature over the bytes using a DID-based key (signer referenced via did:key or other DID method).
- The attestation object contains: `canonical-cbor-envelope`, `cose_signature`, `signer_did`, `envelope_schema_id`, `timestamp`, optional notarization metadata.
- The signed attestation is published with artifact provenance metadata (or embedded in the artifact repository) so verifiers can retrieve it deterministically.

## Stream C integration (independent verifier steps)

- Retrieve signed attestation + canonical-cbor-envelope bytes and signer DID.
- Canonicalize the received envelope independently (require canonical CBOR rules) and verify COSE signature against the DID public key.
- If signature verifies, validate artifact-observed metadata (observed syscalls, runtime traces, SBOM, static analysis results) against the envelope schema: check `allowed_syscalls` subset, `permitted_paths` matching, `network_allowed == false`, dependency whitelist, and resource bounds.
- If any check fails, mark artifact as non-compliant and cascade-break downstream consumption (deny automation, raise legal attestation exception); otherwise mark as verified for downstream use. [in-toto concepts](https://in-toto.io/), [OPA docs](https://openpolicyagent.org/docs/policy-language).

## Implementation and enforcement notes

- Use multi-implementation, safe parsers in Rust/Go/C to parse canonical CBOR and schema (CDDL or generated typed bindings) to reduce parser-trust issues.
- Combine static validation (CBOR/schema) with runtime enforcement: LSM (SELinux/AppArmor) and seccomp for syscalls, Capsicum/CHERI when available, to ensure violations produce hard enforcement at boundary crossing.

## Attenuation semantics

Model delegation as monotonic set reduction (only narrower `allowed_syscalls` / `permitted_paths` / `deps`) and either re-sign or cryptographically attenuate (macaroon-like caveat chaining) when handing envelopes to downstream entities.

## Closing point

This concrete, canonical-CBOR + typed-envelope approach preserves machine-checkability, legal-grade signability, deterministic verification, explicit attenuability, and practical enforcement via existing kernel/runtime mechanisms while minimizing attack surface by avoiding Turing-complete or remote-eval constructs.
