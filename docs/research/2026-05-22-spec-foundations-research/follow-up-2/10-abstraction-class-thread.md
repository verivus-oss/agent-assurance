# Abstraction-class thread — original 3-part draft (2026-05-22)

Drafted in response to the user's recovered Grok-share conversation
about secure .toml hosting / zero-trust framing, where the user named
the missing supply-chain-security primitive: a valid signature on a
corrupted abstraction is useless.

This was the first version of the thread. A refactored 5-part version
that incorporates the user's "overkill" lineage rebuttal is at
[`12-canonical-thread.md`](./12-canonical-thread.md).

---

## 1/3 — The silent class violation

Modern supply-chain security is broken in a way our tools cannot see.

When the compression-library backdoor shipped, SLSA Level 3 passed. Valid signature. Trusted builder. Reproducible build. Every defense we have — green.

And it shipped a remote-execution backdoor in a library whose entire job was compressing data.

The signature was real. The *artifact* had been corrupted at the abstraction layer — the layer our tooling has no vocabulary for.

---

## 2/3 — Architectural type safety

Think of it as type safety, but for software supply chains.

`0A` is a valid hex value. It is not a valid decimal value. The bytes are identical — what changed is *the class you declared*.

When we adopt a dependency, we implicitly declare its class: "this is a compression library." That declaration should bind. A compression library compresses. It does not open outbound sockets.

SLSA verifies *who signed*. It doesn't verify *what was signed against the class it claimed to be*.

A valid signature on a corrupted abstraction is useless. We've been checking envelopes while ignoring the letter inside.

---

## 3/3 — Process-trust over signature-trust

The fix isn't more attestation. It's a new primitive:

**Declared abstraction class → machine-verified behavioral envelope → fail-closed at the boundary.**

Producers declare what the artifact IS. Consumers verify the artifact's observable behavior stays inside the class. If a "compression library" tries to open a socket, the *contract* breaks — regardless of whether the signature is technically valid.

This is what brittleness-as-a-feature actually means. The class is the contract. Class violations cascade-break downstream. We stop trusting the envelope and start verifying the letter.

Until supply-chain tooling can answer "what is this thing allowed to do?", every signed package is just a sealed letter we never read.

---

## What this changes in the spec (companion analysis)

1. **Stream A (kind descriptors) doubles in scope.** Today's kind descriptors describe `[meta]` + field shape. They must now also declare the artifact's **capability envelope**: which syscalls / network / filesystem / process-spawn primitives are inside the declared class, and which are class violations. Inspiration: WASM Component Model + WIT, OCaps, eBPF verifier patterns, SELinux/AppArmor type enforcement, Java SecurityManager (failure mode lessons), seccomp-bpf profiles, Wasmtime capability denials.

2. **Stream B (attestation) gains a third invariant.** Producer signs (a) hash of bytes, (b) hash of declared class, (c) attestation that bytes were verified to stay inside class envelope at build time, by an entity distinct from the producer (Stream C separation-of-duty applies here). Consumer's verification becomes: signature valid AND class declaration intact AND no upstream class change broke the chain. Three independent checks, any failure fails closed.

3. **Stream D (format) opens up.** TOML has no native way to express capability bounds. Better candidates: CDDL with capability-tag extensions, WIT (Component Model interface types), a small purpose-built DSL where the *grammar itself* refuses to express constructs outside a declared class.

4. **Existing primitives that compose into the new design:** WASM Component Model + WIT (interface types as capability boundaries); in-toto layout `expected_command` / `expected_materials` / `expected_products` (already partial capability declaration); eBPF verifier (proof-carrying code at load time; rejects programs that violate the class); capability-based OS research (CHERI, capsicum, Genode); Java's deprecated SecurityManager (failure modes to *avoid*); macaroons and OAuth scopes (capability tokens, attenuable).

5. **The Grok share conversation's "zero trust, sort of" pivot lines up exactly with this.** Zero Trust at the network layer = "verify every request against policy." Zero Trust at the artifact layer = "verify every artifact against its declared class on every boundary crossing." Cloudflare Access verifies the user. The new primitive verifies the artifact.
