# Gemini (gemini-3.1-pro-preview) — Stream F triangulation (second opinion)

Run via `llm-gateway` with Exa MCP, YOLO mode. Job ID: `62285181-6d0d-4d31-a160-624c008b7640`.
Duration: 139s. 13435 bytes stdout.

Tasked with second-opinion on the Exa Deep Researcher's capability-envelope
recommendation.

---

# Second Opinion Report: Declarative Capability Envelopes for Trust-Infrastructure Spec

The Exa Deep Researcher report presents a compelling foundation for declarative capability envelopes, leaning heavily into a compact, binary-first, structurally typed architecture. The ethos of "trust-as-currency" and "producer-side responsibility" is directionally correct. However, a skeptical, independent review of the proposed stack—dCBOR, CDDL, COSE_Sign1, DID-bound keys, and OS-level enforcement—reveals significant technical, legal, and architectural fractures. The recommended stack severely underestimates the difficulty of semantic cross-language canonicalization, the rigid legal requirements of European digital signatures, and the fundamental realities of OS-level sandbox fragmentation.

---

## 1. Is CDDL the right schema language? Handle attenuation (monotonic set-reduction)? "MUST NOT include field X" patterns?

**Position:** CDDL is an excellent structural definition language, but it is fundamentally the wrong tool for expressing monotonic set-reduction and negative constraints.

**Evidence:** CDDL (RFC 8610) is designed to describe the *shape* of valid CBOR data via Parsing Expression Grammar (PEG) semantics. It excels at defining what a structure *must* look like, but it lacks native logical negation. While JSON Schema natively supports the `"not"` keyword (allowing explicit exclusion of fields), CDDL relies on positive structural typing. To enforce a rule like "MUST NOT include field X," one must either exhaustively enumerate all permitted fields (disallowing open maps) or rely on complex, non-standard control operators that are not ergonomically suited for capability attenuation.

Furthermore, capability attenuation (monotonic set-reduction) is not a structural property; it is a *logical* property. If a parent envelope grants network access, and the child attenuates it to restrict network access, CDDL cannot natively express the relational constraint that "Child Envelope $\subseteq$ Parent Envelope".

**Recommendation:** Retain CDDL strictly for defining the static serialization shape of the envelope. Do not use it for attenuation rules. For capability attenuation, integrate a dedicated logic layer such as Macaroons, Biscuit (Datalog-based caveats), or leverage WebAssembly Component Model capability typing (WIT worlds), which natively enforces capability subsetting at the interface level.

## 2. Is dCBOR ready for legal-grade signing?

**Position:** Absolutely not. dCBOR (`draft-mcnally-deterministic-cbor`) is actively unstable and introduces severe, unresolved semantic hazards that break cross-language interoperability.

**Evidence:** As of early 2026, `draft-mcnally-deterministic-cbor` is at its 17th draft and faces serious implementation roadblocks in major languages. A critical example is the "numeric reduction" rule, which mandates that floating-point values mathematically equivalent to integers (e.g., `1.0`) must be deterministically coerced and encoded as integers (e.g., `1`).

This aggressive coercion breaks map semantics in languages like Go. In February 2025, the maintainers of the predominant Go CBOR library (`fxamacker/cbor`) flagged issue #632 regarding dCBOR support: converting floats to integers dynamically introduces duplicate map keys if both `1.0` and `1` were originally present. Because Go maps strictly enforce unique keys and iterate non-deterministically, the library maintainers noted that complying with dCBOR would require dropping entire maps to avoid silent data corruption. A standard that forces major language implementations to silently drop data or break native map semantics is not ready for legal-grade non-repudiation.

**Recommendation:** Abandon strict dCBOR numeric reduction. Instead, utilize the simpler, widely supported RFC 7049 Canonical CBOR subset, and strictly prohibit floating-point types in the capability envelope at the schema level.

## 3. Is COSE_Sign1 + DID-bound keys the right signing surface for eIDAS QES / CAdES?

**Position:** No. COSE_Sign1 with raw DID-bound keys fundamentally fails to meet the legal requirements of eIDAS Qualified Electronic Signatures (QES).

**Evidence:** The eIDAS regulation dictates that a QES must be supported by a Qualified Certificate for Electronic Signatures, issued by a Qualified Trust Service Provider (QTSP) residing on a Member State's Trusted List (EUTL). It also mandates the use of a Qualified Signature Creation Device (QSCD). Raw Decentralized Identifiers (DIDs) are not recognized as legal-grade trust anchors under eIDAS unless they are cryptographically bound to an X.509 PKI structure (e.g., the `did:x509` method).

Furthermore, while the EU has modernized its formats, standard eIDAS QES validates against CMS (CAdES), PDF (PAdES), XML (XAdES), or ASiC containers. To achieve legal-grade COSE signatures, you cannot use vanilla `COSE_Sign1`. You must use the newly published (March 2026) ETSI TS 119 152-1 standard, which defines **CB-AdES** (COSE Advanced Electronic Signatures). CB-AdES explicitly requires COSE headers to include `xRefs` (X.509 certificate references), `rRefs` (CRL/OCSP revocation data), and specific cryptographic time-stamps (`sigTst`, `arcTst`) to support long-term non-repudiation and closure-root rules.

**Recommendation:** Mandate compliance with ETSI TS 119 152-1 (CB-AdES) for the signature surface. Require the envelope to support `xRefs` and `rRefs` headers, and mandate X.509 bridging for any DID utilized in a legal-grade context.

## 4. The seven envelope fields — what's missing?

**Position:** The proposed seven fields (`class-id`, `allowed_syscalls`, `permitted_paths`, `network_allowed`, `dependency_whitelist`, `cpu_bounds`, `memory_bounds`) are dangerously incomplete and leave massive attack surfaces unprotected.

**Evidence:** Modern capability models—such as FreeBSD's Capsicum and the WASI Preview 2 Component Model—identify several critical capability domains missing from this list:

1. **Environment Variables:** Often used to inject malicious payloads, alter linker behavior (`LD_PRELOAD`), or leak AWS/cloud credentials.
2. **Clocks / Time:** Wall-clock and monotonic clock access are fundamental requirements for cryptographic timing attacks and covert channel communication. WASI explicitly isolates `wasi:clocks/wall-clock`.
3. **Randomness:** Access to the OS entropy pool (`wasi:random`). Inability to control entropy breaks deterministic execution and reproducible builds.
4. **IPC and Process Spawning:** Shared memory mapping, signals, and the ability to fork/exec child processes.

**Recommendation:** Expand the capability taxonomy. At a minimum, add `permitted_env`, `clock_access`, `entropy_access`, and `ipc_bounds`.

## 5. Enforcement-layer fragmentation: realistic for a portable spec?

**Position:** Punting capability enforcement to the underlying OS (seccomp, Capsicum, macOS sandbox) guarantees the failure of the specification as a portable standard.

**Evidence:** The semantics of resource access across Linux, FreeBSD, and macOS are fundamentally irreconcilable at the syscall layer. As extensively documented in Jonathan Anderson's research on Unix sandboxing ("A comparison of Unix sandboxing techniques"), Linux's `seccomp-bpf` suffers from fundamental Time-Of-Check-To-Time-Of-Use (TOCTTOU) vulnerabilities when dealing with file paths. `seccomp` operates on system calls where paths are merely memory pointers; it cannot safely or atomically resolve `permitted_paths` dynamically without a complex, trusted userspace broker.

Conversely, FreeBSD's Capsicum restricts the global namespace entirely via `cap_enter()` and operates purely on capability-laden file descriptors. macOS uses `sandbox-exec` with a proprietary Scheme-like language to govern Mach IPC and paths. Attempting to map a single `permitted_paths` directive securely and uniformly across these three radically different paradigms is practically impossible without building an entire virtualization layer.

**Recommendation:** Do not rely on OS-native sandboxing for portable capability enforcement. The specification must dictate that enforcement occurs at the runtime or virtual machine layer (e.g., a WebAssembly runtime) where the host environment can provide a uniform, abstract capability broker.

## 6. Handling syscall-naming portability

**Position:** Hardcoding Linux syscall names into a cross-platform trust envelope is an architectural dead end.

**Evidence:** Syscall names and numbers are not just OS-specific; they are architecture-specific. A Linux x86_64 syscall table is entirely different from a Linux ARM64 syscall table. Relying on POSIX-2017 provides false comfort, as modern filesystem, networking, and memory operations heavily utilize non-POSIX extensions (e.g., Linux `openat2`, `io_uring`). Tying an envelope to Linux syscalls completely alienates Windows, macOS, and BSD environments, violating the ethos of multi-language, multi-platform safe parsing.

**Recommendation:** Eradicate the concept of "syscalls" from the envelope. Abstract system access into semantic capability interfaces. The WebAssembly System Interface (WASI) Preview 2 uses High-level WIT (WebAssembly Interface Type) interfaces—such as `wasi:filesystem/types` and `wasi:http/outgoing-handler`. The spec should define its capabilities using these standard, semantic, OS-agnostic interfaces.

## 7. Cryptographically observable failure vs runtime enforcement

**Position:** Runtime enforcement betrays the "producer-side responsibility" ethos. A broken contract must be cryptographically observable *before* execution.

**Evidence:** Under the Exa Deep proposal, if a compression library maliciously or accidentally opens a socket, the violation is only caught at runtime when the OS sandbox (e.g., seccomp) kills the process. The artifact has already been shipped, deployed, and instantiated. Because the envelope only describes what the host *allows*, rather than what the artifact *requires*, a downstream consumer cannot cryptographically verify that the artifact is safe prior to executing it.

In contrast, a statically verifiable capability model—like the WASM Component Model—requires the artifact to declare its dependencies. A WASM component explicitly declares its required imports in its WIT world (e.g., `import wasi:sockets/tcp`). A downstream consumer can statically parse the binary, observe the requested capabilities, compare them against the trust envelope, and cryptographically reject the artifact in the CI/CD pipeline, long before runtime.

**Recommendation:** Reverse the polarity of the envelope. The envelope must not just dictate what the host enforces; it must be cryptographically bound to the static capability imports of the artifact itself, ensuring that capability requirements are statically observable and verifiable.

---

## Final Synthesis

### Solid

- **Trust-as-currency & Brittleness-as-feature:** Shifting away from ambient authority to explicit, brittle capability grants is the correct philosophical approach for modern trust infrastructure.
- **Format Selection:** CBOR is the correct serialization format. It allows for highly efficient, memory-safe parsing in systems languages (Rust/C/Go) without the parsing ambiguities inherent to JSON or the bloat of XML.
- **Producer-side responsibility:** Forcing the producer to explicitly declare and sign the operational bounds of their software fundamentally improves supply-chain security.

### Weak

- **Enforcement Layer:** Punting enforcement to fragmented OS primitives (seccomp/Capsicum) ensures the spec will never be truly portable. OS sandboxing is too semantically divergent.
- **dCBOR Instability:** Relying on a draft standard that breaks map semantics in major languages undermines the goal of multi-language safe parsing.
- **Legal Standing:** Raw COSE + DIDs completely ignore the rigid, X.509-heavy requirements of European eIDAS QES regulations.
- **Capability Taxonomy:** The proposed 7 fields miss critical attack vectors (time, randomness, environment variables).

### What I'd Change

1. **Pivot to WASI Preview 2 (Component Model):** Discard OS-level syscalls and fragmented sandboxing entirely. Adopt the WebAssembly Component Model and its WIT interfaces (`wasi:filesystem`, `wasi:http`, `wasi:clocks`) as the canonical capability vocabulary. This solves portability, provides comprehensive capability fields, and enables *statically observable* capability validation.
2. **Adopt CB-AdES for Signatures:** Upgrade the signing surface from raw `COSE_Sign1` to ETSI TS 119 152-1 (CB-AdES). Mandate X.509 bridge support (`xRefs`, `rRefs`) to ensure the artifacts meet eIDAS QES requirements for legal-grade non-repudiation.
3. **Use Datalog for Attenuation, not CDDL:** Restrict CDDL to validating the static shape of the CBOR serialization. Implement monotonic set-reduction and attenuation caveats using a dedicated logic-based authorization language (e.g., Biscuit/Datalog), which mathematically guarantees that derived capabilities are strict subsets of their parents.
4. **Downgrade to Canonical CBOR:** Drop the bleeding-edge `dCBOR` requirement in favor of RFC 7049 Canonical CBOR to ensure immediate, stable support across Go, Rust, and C ecosystems.
