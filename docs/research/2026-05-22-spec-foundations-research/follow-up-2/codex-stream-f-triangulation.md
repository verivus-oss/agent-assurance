# Codex (gpt-5.5) — Stream F triangulation (second opinion)

Run via `llm-gateway` with Exa MCP, sandbox read-only, ~26 Exa searches.
Job ID: `d7653d70-ef9e-4337-884c-35d4c5d29308`. Duration: 202s.

Tasked with second-opinion on the Exa Deep Researcher's capability-envelope
recommendation. Codex was asked to verify specific claims via Exa, not
re-derive from scratch.

---

## 1. CDDL At This Layer: Partially Agree

CDDL is a good wire-schema language for a CBOR envelope, but it is not a good attenuation semantics language. RFC 8610 can define map structure, optional fields, groups, alternatives, and closed-map behavior: if map members remain unmatched, the map does not validate. It also warns that map matching can become non-deterministic for overlapping group expressions and that tools cannot generally detect all such bad specs automatically ([RFC 8610](https://rfc-editor.org/rfc/rfc8610.html)).

CDDL also does not determine deterministic serialization order; CBOR itself does that. RFC 8949 says deterministic CBOR map keys are sorted by bytewise lexicographic order of deterministic encodings ([RFC 8949](https://www.rfc-editor.org/rfc/rfc8949.html)). A newer CBOR serialization draft adds CDDL controls like `.det`, but that is about embedded serialization constraints, not attenuation semantics ([draft-ietf-cbor-serialization](https://datatracker.ietf.org/doc/draft-ietf-cbor-serialization/02/)).

**Recommendation:** use CDDL only for structural validity. Define attenuation as a separate normative algebra over parsed envelope values: subset for sets, path-language containment for path grants, numeric `<=` for bounds, boolean `false <= true`, and explicit forbidden-field rules. Do not pretend CDDL proves monotonic narrowing.

## 2. dCBOR For Legal-Grade Signing: Partially Agree, With Caution

RFC 8949 deterministic CBOR is stable enough to sign if the profile is nailed down. dCBOR is attractive because it narrows RFC 8949 choices: it reduces integral floats to integers, collapses NaN to a single encoding, forbids duplicate keys, normalizes text, and removes several CBOR ambiguities ([draft-mcnally-deterministic-cbor-17](https://datatracker.ietf.org/doc/draft-mcnally-deterministic-cbor/17/)). But it is still an Internet-Draft expiring August 16, 2026, not an RFC.

The implementation story is uneven. Rust `serde_cbor` is archived and implemented RFC 7049-era CBOR, with the maintainer explicitly recommending other crates ([pyfisch/cbor](https://github.com/pyfisch/cbor)). Go `fxamacker/cbor` looks much healthier and explicitly supports RFC 8949 Core Deterministic Encoding, duplicate-key handling, and separate canonical presets ([fxamacker/cbor](https://github.com/fxamacker/cbor/tree/master)). But even that ecosystem has had subtle canonicalization and duplicate-key edge cases in COSE/signing contexts ([fxamacker/cbor #369](https://github.com/fxamacker/cbor/issues/369)). Rust `ciborium` only recently added RFC 8949 canonicalization after using RFC 7049-style ordering ([enarx/ciborium #144](https://github.com/enarx/ciborium/issues/144)). C libraries are also fragmented: QCBOR's stable line says map sorting is the main missing RFC 8949 feature, while dCBOR support is in v2 alpha/dev work ([QCBOR README](https://github.com/laurencelundblade/QCBOR/blob/master/README.md)).

**Recommendation:** do not say "dCBOR" generically in a legal-grade spec yet. Say "RFC 8949 Core Deterministic Encoding plus these additional frozen profile rules," borrowing dCBOR rules where desired. Pin test vectors and require byte-for-byte conformance across Rust, Go, and C.

## 3. COSE_Sign1 + DID-Bound Keys: Disagree As Stated

COSE_Sign1 is a good compact signing container for one signer. RFC 9052 defines the COSE_Sign1 structure and its signature input (`Sig_structure`) over well-defined bytes ([RFC 9052](https://rfc-editor.org/rfc/rfc9052.html)). DID binding is plausible for key discovery and verification relationships: DID Core defines `assertionMethod`, `capabilityInvocation`, and key revocation-by-removal from the latest DID Document ([DID Core](https://www.w3.org/TR/did/)).

But this does not give legal-grade non-repudiation by itself. eIDAS QES requires a qualified certificate and qualified signature creation device, not merely a DID key ([European Commission eSignature](https://ec.europa.eu/digital-building-blocks/sites/spaces/DIGITAL/pages/467109069/What%2Bis%2BeSignature)). COSE can carry or reference X.509 certificates using RFC 9360, which explicitly points to existing trust chaining and revocation checking ([RFC 9360](https://rfc-editor.org/rfc/rfc9360.html)). That is the route toward eIDAS-compatible validation, not bare DID keys.

Attenuability is also not provided by COSE_Sign1. You need either re-signing of narrowed envelopes or a caveat/delegation structure with formal verification. Revocation propagation is not automatic either. DID Core's current-document rule can invalidate old signatures unless versioned resolution and timestamp policy are specified; W3C DID discussions flag this exact revocation-vs-rotation ambiguity ([w3c/did #386](https://github.com/w3c/did-core/issues/386), [#483](https://github.com/w3c/did-core/issues/483)).

**Recommendation:** use COSE_Sign1 for technical integrity, but add X.509/QC binding for legal mode, timestamping, revocation policy, and a transparency or closure-root log. Treat DID as an identifier layer, not the legal trust anchor.

## 4. Seven Envelope Fields: Partially Agree

The fields are a useful minimum, not a complete capability envelope. For real compression or transform libraries, missing dimensions matter.

IPC and shared memory are absent. Capsicum's documentation explicitly calls out process descriptors and anonymous shared memory as capability-relevant resources ([FreeBSD capsicum(4)](https://man.freebsd.org/cgi/man.cgi?query=capsicum&sektion=4)). macOS sandbox profiles cover Mach messaging and other IPC ([macOS sandbox notes](https://bdash.net.nz/posts/sandboxing-on-macos/)). Cryptographic material access is absent: "read a private key file" and "invoke a signing key handle" are different capabilities. Clock access is absent; WASI separates clocks as their own API family ([WASI Preview 2](https://github.com/WebAssembly/WASI/blob/main/docs/Preview2.md)). Randomness is absent; WASI also separates random APIs. Environment access is absent; WASI Preview 2 includes `wasi-cli`, and capability discussions call out environment variables as a separate grant. Process spawning is only implicit in syscalls and should be explicit.

**Recommendation:** add first-class fields for `process_spawn`, `ipc`, `shared_memory`, `env`, `clock`, `random`, and `crypto_keys`, where crypto grants distinguish read/export from sign/decrypt/use-only.

## 5. Enforcement Fragmentation: Disagree With The Portability Claim

"LSM/seccomp/Capsicum/CHERI per deployment" is not a portable enforcement story. Linux seccomp documentation is blunt: syscall filtering is not a sandbox and should be combined with LSMs or other mechanisms for logical behavior and information flow ([Linux seccomp docs](https://www.kernel.org/doc/html/latest/userspace-api/seccomp_filter.html)). Seccomp also cannot inspect pointer-referenced data such as path strings, which means it cannot directly enforce `permitted_paths` globs ([seccomp eBPF paper](https://tianyin.github.io/pub/seccomp-ebpf.pdf)).

Capsicum is not a syscall-name allowlist model. It is a file-descriptor capability model that restricts global namespaces and narrows rights on existing descriptors ([FreeBSD capsicum(4)](https://man.freebsd.org/cgi/man.cgi?query=capsicum&sektion=4)). macOS `sandbox-exec` has richer path/network/Mach-style policy but is deprecated as a public tool, and the lower-level profile language is private/undocumented ([sandbox-exec manpage](https://keith.github.io/xcode-man-pages/sandbox-exec.1.html), [Mark Rowe](https://bdash.net.nz/posts/sandboxing-on-macos/)).

**Recommendation:** define a portable semantic capability model, then publish per-platform conformance classes. The common subset is small: coarse syscall denial, FD/preopen restrictions, no-network, limited process spawning. Path glob semantics do not survive cleanly across all three.

## 6. Linux Syscall Names In The Example: Disagree

A signed envelope should not use Linux syscall names as the primary abstraction. POSIX.1-2017 defines source-level system interfaces, not a portable syscall ABI ([POSIX Base Specifications](https://pubs.opengroup.org/onlinepubs/9699919799.2018edition/mindex.html)). Linux's syscall interface is stable, but the kernel documentation says syscall numbers differ by architecture ([Linux syscall ABI](https://github.com/torvalds/linux/blob/master/Documentation/ABI/stable/syscalls)). BSD/macOS diverge in names and semantics: FreeBSD's Linux compatibility page lists Linux-specific calls like `clone`, `epoll`, `openat2`, `statx`, and `splice` as missing, emulated, or different ([FreeBSD LinuxSourceCompatibility](https://wiki.freebsd.org/LinuxSourceCompatibility)).

WASI Preview 2 is a better candidate abstraction for portable capability names: filesystem, sockets, clocks, random, CLI/env, HTTP, and IO are distinct versioned interfaces ([WASI Preview 2](https://github.com/WebAssembly/WASI/blob/main/docs/Preview2.md); [wasi-sockets](https://github.com/WebAssembly/wasi-sockets/); [wasi-filesystem](https://github.com/WebAssembly/wasi-filesystem/)).

**Recommendation:** replace `allowed_syscalls` with `allowed_operations` from a spec-owned vocabulary. Linux syscall filters become one backend compilation target, not the canonical contract.

## 7. "Compression Opens Socket" Example: Partially Agree

Runtime enforcement can catch it. If `network_allowed: false` compiles to a seccomp profile that blocks `socket()` or related syscalls, the process fails at runtime. Seccomp can also log violations depending on action and audit settings ([seccomp docs](https://kernel.org/doc/html/v5.17/userspace-api/seccomp_filter.html)).

But the violation is not cryptographically observable downstream unless the runtime produces a signed attestation that records the policy, the attempted violation, and the resulting artifact state. A signed envelope only says "producer declared no network." It does not prove the artifact never tried. Supply-chain systems solve this by signing execution metadata: in-toto records command execution, return value, materials, products, stdout/stderr, and signs link metadata ([in-toto-run](https://in-toto.readthedocs.io/en/latest/command-line-tools/in-toto-run.html)). SLSA similarly treats provenance as an explicit attestation that must be verified, not as a raw artifact signature ([SLSA verification](https://slsa.dev/spec/v1.2/verifying-artifacts)).

**Recommendation:** add a `runtime_observation_attestation` or `policy_execution_attestation` type. A downstream consumer should see signed evidence: envelope digest, enforcement backend, policy compiler version, event log digest, violation status, and artifact digest.

## Where The Exa Deep Recommendation Is Solid

- CBOR plus COSE is a strong compact binary substrate.
- Avoiding JSON Schema, eval, remote includes, and Turing-complete policy in the signed canonical form is the right instinct.
- Monotonic attenuation is the correct security shape.
- Producer-side signed declarations fit the "trust-as-currency" model.
- Runtime enforcement must be deployment-specific; no single OS primitive covers all targets.

## Where The Recommendation Is Weak Or Wrong

- CDDL is being overloaded as if it can express attenuation semantics.
- dCBOR is promising but not final enough to name as the legal-grade canonicalization dependency without freezing a profile.
- DID-bound keys do not equal eIDAS/QES-grade non-repudiation.
- The field set misses IPC, env, clocks, randomness, spawning, and crypto-key-use capabilities.
- Linux syscall names are the wrong portable abstraction.
- Runtime blocking is not the same as downstream cryptographic evidence.

## What I'd Change

Keep CDDL + deterministic CBOR + COSE, but revise the spec as:

1. `schema = CDDL`; `semantics = separate attenuation calculus`.
2. `canonicalization = RFC 8949 Core Deterministic Encoding + frozen profile rules`, not unqualified draft dCBOR.
3. `signature = COSE_Sign1`; `legal_profile = COSE + RFC 9360 X.509/QC + timestamp + revocation`.
4. Replace `allowed_syscalls` with portable `allowed_operations`, with Linux/BSD/macOS/WASI backend mappings.
5. Expand envelope fields for IPC, shared memory, env, clock, randomness, process spawning, and crypto key handles.
6. Add signed runtime/provenance attestations so "opened a socket" becomes cryptographic evidence, not just a local enforcement event.
