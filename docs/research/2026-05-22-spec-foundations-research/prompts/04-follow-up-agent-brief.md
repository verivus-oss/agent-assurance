# Follow-up agent brief — sent to Codex / Gemini / Grok

After the user's design-directives turn, all three delegated agents
were sent a single combined prompt covering Streams A, B, C, and D.
None saw the others' output. The Codex version is the longest and is
reproduced first; Gemini and Grok received structurally identical
prompts with section lengths compressed for token economy.

Job IDs:

- Codex (2nd attempt after `--search` flag removed): `52998c97-663a-4ac8-8566-456f238fbab1`
- Gemini: `a1bba74a-87ef-45c1-934c-48fadc1c1b94`
- Grok: `9fdc0084-a2d0-4ab4-a1e5-06a3d9e67af3`

## Codex version (full)

```
You are doing INDEPENDENT external research using the `exa` MCP server (web_search_exa, web_search_advanced_exa, get_code_context_exa). Use Exa extensively. Do NOT read any local repo.

CONTEXT (read once, don't quote back):
A public spec called "DAG-TOML / IJB / Agent Assurance" exists. The user has just rejected several common remedies and stated a design ethos. The ethos binds everything below:

ETHOS (binding):
- TRUST IS THE CURRENCY — this is security/legal-grade, not a convenience tool.
- BRITTLENESS IS A FEATURE — invalidations must propagate visibly; silent coercion or papering-over is wrong.
- PROCESS-TRUST, NOT ARTIFACT-TRUST — supply-chain attacks compromise artifacts while leaving them surface-valid; trust shifts to the process that produced the artifact.
- PRODUCER-SIDE RESPONSIBILITY — consumers verify only the last artifact, make provenance possible for the next.

OFF THE TABLE:
- JSON Schema (JSON has insurmountable problems for this context: silent coercion, no canonical form, no comments, permissive parsing culture).
- Novel cryptography (must compose existing primitives).

MANDATED:
- Primary normative validator implementations in safe Rust + safe Go + safe C; everything else is a port.

YOUR ASSIGNMENT — four research streams. Cover ALL FOUR. Use Exa hard on each (8–15 searches per stream).

== Stream A: Kind-descriptor / self-describing-schema drift mitigation ==
Survey existing mechanisms that keep prose and machine form aligned in long-lived specs: content hashing, bidirectional generation, schema-as-data, AST-level fingerprinting, executable specifications, golden-master testing, property-based contracts, literate programming with extraction, CUE definitions, Dhall types, ProtoBuf descriptors, JSON-LD contexts, SHACL shapes, OpenAPI components, grafana/thema lineages, CognitiveLayers/clayers, RFC 7873 (canonicalization), etc. Then PROPOSE a novel mechanism that fits the ethos above (must surface drift as visible failure, multi-language safe-parse compatible, no JSON Schema).

== Stream B: Legal-grade one-shot immutable attestation ==
This is the most important and novel question. Survey EVERY relevant existing primitive: in-toto, SLSA v1.2, Sigstore/Fulcio/Rekor, RATS RFC 9334, Entity Attestation Token RFC 9711, COSE RFC 9052, SCITT, C2PA, DSSE, eIDAS qualified electronic signatures (QES), age (FiloSottile), Sequoia-PGP, RFC 6962/9162 transparency logs, RFC 3161 TSP (time-stamping), OpenSSF Scorecard, X.509 + CRL/OCSP, RFC 9711 EAT, Witness Statements, blockchain timestamping, Apple Notarization, MS Authenticode, WebAuthn for non-repudiation, FIDO Device Onboarding.

REQUIREMENTS the design must meet (per the user):
- One-shot, single-use per sha256-hashed artifact
- Immutable — no upgrades, no application to previous versions
- Sha256 minimum
- Legally provable INTENT to sign (not just key use — explicit ceremony, declaration, QES properties)
- Withdrawable / time-bounded keys; signatures revocable; revocation itself attested
- Upstream changes INTENTIONALLY break downstream hashes — this is the signalling mechanism
- Producer-side responsibility; consumer only checks the last artifact
- Current crypto stacks only
- Must apply to anyone who ships an artifact

Gap analysis: identify what no existing system handles. Then PROPOSE a composite design.

KNOWN FAILURE MODES TO AVOID:
- Provenance paradox (SLSA-attested TanStack worm)
- Evidence fatigue
- Verifier root-of-trust shift (over-attestation moves attack surface to verifier)
- Legal non-repudiation gaps (key compromise, post-dating, unprovable intent)

== Stream C: Separation-of-duty gate validation ==
Mechanical patterns so an agent (human, program, LLM) cannot validate its own work. Cycle: intent → action → proof → audit. ISO-9001-like. Survey: ISO 9001 audit-separation, ISO/IEC 17021, ISO 19011, two-party control (FIPS 140-3 dual control, banking key ceremonies), threshold signatures (FROST, BLS, Shamir), MPC for verification, trusted third-party witnesses, transparency logs, reproducible builds (rb-tools, Bazel remote exec), capability isolation, in-toto layouts, SCITT receipts, Stackelberg-auditor research (arXiv 2605.06340), Governance Gauntlet (Zenodo 19689504).

Then PROPOSE mechanical patterns binding for the spec: which verification steps MUST be performed by an entity distinct from the producer; what cryptographic/procedural mechanisms make this enforceable.

== Stream D: Alternative formats / new-format design ==
Brittleness is a FEATURE here. Survey: TOML, JSON (rejected), YAML (rejected — Norway problem), CBOR + RFC 8949 deterministic encoding, ASN.1 + DER, CDDL, S-expressions, EDN, KDL, RON, NestedText, Pkl, Nickel, Dhall, CUE, KCL, Jsonnet, Starlark, capnproto, FlatBuffers, RFC 8785 JCS (JSON canonicalisation — rejected for using JSON), COSE canonical form.

Evaluate on these axes:
1. Human readable/editable
2. Deterministic canonical form (stable hashing)
3. Cryptographic provenance (one-to-one text↔hash)
4. Producer-side responsibility friendliness
5. BRITTLENESS AS FEATURE — rejects ambiguity, silent type coercion, defaults that hide intent
6. Multi-language safe parsing (Rust, Go, C primary)
7. No remote includes, no eval, Turing-incomplete
8. Schema mechanism that does not require JSON Schema

Verdict: which existing format wins, or do we create something new? If new, sketch design goals, syntax, canonicalisation algorithm.

== OUTPUT ==
Four sections (A, B, C, D), each ~400–700 words. Per section: 5–10 cited URLs with one-line annotations. Then a final "DESIGN RISKS ACROSS STREAMS" (5–8 bullets) and "BUILD ORDER" (suggest which stream to ship first and why). ~3000–5000 words total. Be skeptical, independent, brief on rationale.
```

## Gateway parameters used

- Codex: `model=latest`, `mcpServers=["exa"]`, `sandboxMode=read-only`, `idleTimeoutMs=3000000`
- Gemini: `model=latest`, `mcpServers=["exa"]`, `approvalMode=yolo`, `idleTimeoutMs=3000000`
- Grok: `model=latest`, `mcpServers=["exa"]`, `alwaysApprove=true`, `idleTimeoutMs=3000000`

## Gemini diff

Gemini's prompt was structurally identical; the Stream A/B/C/D survey lists were compressed slightly (fewer named references per stream) to reduce token cost.

## Grok diff

Grok's prompt was the most compressed: ~30% shorter than Codex's, with one-line section descriptions instead of paragraph form, retaining the binding ethos, OFF THE TABLE, MANDATED, and OUTPUT sections intact.
