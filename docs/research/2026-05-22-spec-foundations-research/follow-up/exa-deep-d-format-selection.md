# Exa Deep Researcher — Stream D — Alternative formats / new-format design

Model: `exa-research`. Cost: $0.93. Searches: 54. Pages crawled: ~130.
Research ID: `r_01ks6kackkhzfdckbt1e5a9zn5` (2026-05-22).

Axes (per the ethos): 1. human readable/editable; 2. deterministic canonical
form; 3. one-to-one text↔parse-tree; 4. rejects silent coercion; 5. supports
comments; 6. non-JSON-Schema schema mechanism; 7. safe parsers in Rust/Go/C;
8. mature ecosystem; 9. acceptable verbosity for graph data.

---

## Format-by-axis verdicts

### TOML (current)

- 1: Yes — designed as a human-friendly config language
- 2: Partial — no built-in canonical byte serialization; spec maps unambiguously to a hash table but provides no canonical hashable encoding
- 3: Mostly — textual keys map to a unique table structure; aliasing/anchors absent
- 4: Yes — no implicit JS-style coercion; types are explicit
- 5: Yes — line comments with `#` supported
- 6: No — TOML has no built-in schema (validation is external)
- 7: Mixed — very mature Rust support (toml crate used by Cargo) and mature Go libraries; C parsers exist but are less mature
- 8: Mature for config use, broad adoption for apps but not strong for cryptographic canonicalisation
- 9: Poor for graphs — no native graph primitives or concise referencing; becomes verbose for graph structures

**Verdict**: Good human config format but fails deterministic canonical hashing and schema requirements for legal/security-grade specs.

### CBOR (RFC 8949) — with deterministic encoding (CDE)

- 1: No (binary) — not human-friendly, though diagnostic text exists
- 2: Yes when using Core Deterministic Encoding (CDE) rules — RFC + CDE drafts define canonical deterministic encoding for signing/hashing
- 3: Yes — CBOR data model maps to CBOR items (no anchors)
- 4: Yes — explicit typed encoding, no silent coercion at CBOR level
- 5: No — no native comment facility in the binary format
- 6: Yes — CDDL is the standard schema language for CBOR/JSON
- 7: Yes — multiple mature implementations in Rust/Go/C (serde_cbor, TinyCBOR, libcbor, etc.)
- 8: Mature in embedded/security protocols (COSE, etc.)
- 9: Good — compact and efficient for graphs when schema-driven, but verbose to author by hand (binary native)

**Verdict**: Excellent machine canonical format (with CDE) + schema (CDDL) for signing and validators; not human-friendly as a primary normative authoring format.

### ASN.1 + DER (canonical)

- 1: Partial — ASN.1 text is human-readable for spec authors, but DER is binary and not convenient to hand-edit
- 2: Yes — DER is canonical/unique encoding by design (Distinguished Encoding Rules) and used for signatures
- 3: Yes — one-to-one representation given the ASN.1 type definitions and DER rules
- 4: Yes — strict typing; deviations are rejected
- 5: Comments exist in ASN.1 module source but not in DER payloads
- 6: Yes — ASN.1 itself is a schema language (modules, imports)
- 7: Yes — very mature implementations in C (OpenSSL), Rust crates (asn1-rs, der-parser), and some Go support
- 8: Very mature — foundational in PKI and S/MIME
- 9: Good (compact binary), but binary form is not human authored

**Verdict**: Extremely strong on brittleness/determinism and multi-language parser availability; poor as a human-editable primary artifact unless you layer a textual authoring format.

### Canonical S-expressions (RFC/Rivest)

- 1: Yes — textual, Lisp-like, concise for human editors
- 2: Yes — canonical S-expression representation is explicitly defined for unique encoding
- 3: Yes — one-to-one mapping between canonical textual form and parse tree
- 4: Neutral — S-exprs are data; coercion semantics are left to consumers (no silent coercion by the format itself)
- 5: Partial — comments are generally not part of canonical form; implementations differ
- 6: No built-in schema — validation is by external validators (validator-as-spec works well)
- 7: Parsers available in Rust (lexpr), Go (chewxy/sexp), C (various small libs)
- 8: Moderate — used in crypto circles, not a huge ecosystem like JSON/YAML
- 9: Good — compact for graph-like structures; canonicalization supports stable hashing

**Verdict**: Very attractive for deterministic, textual, one-to-one requirements — lacks a standardized schema language but fits a validator-as-spec philosophy.

### EDN

- 1: Yes — human friendly, Clojure data notation
- 2: No — no standard canonicalization
- 3: Mostly — direct mapping to data structures, no anchors
- 4: Yes — no implicit coercion; types explicit at reader level
- 5: Partial — many implementations accept `;` comments (Clojure convention) though spec is not prescriptive
- 6: No — no standard schema; validation external
- 7: Parsers in Rust and Go exist but less mature; C parsers rare
- 8: Niche ecosystem
- 9: Decent expressivity for graphs but verbosity varies

### KDL

- 1: Yes — designed as a human-friendly document language
- 2: No — no standardized canonical byte serialization in spec
- 3: Yes — one-to-one node/argument/property model with no aliasing
- 4: Yes — type annotations explicit; no implicit coercion expected
- 5: Yes — supports `//` and `/* */` comments
- 6: Yes — KDL Schema exists
- 7: Good Rust & Go support; C limited
- 8: Growing, moderate maturity
- 9: Reasonable for trees; graphs require explicit modeling (can be verbose)

### RON

- 1: Yes — readable, Rust-like syntax
- 2: No — no canonical byte serialization defined
- 3: Yes — direct mapping to Serde values (no anchors)
- 4: Mostly — extensions can enable implicit conveniences; default is explicit
- 5: Yes — `//` and `/* */` comments supported
- 6: No — relies on host language types (Serde) rather than a separate schema
- 7: Excellent Rust support; Go/C parsers scarce
- 8: Niche but stable in Rust ecosystem
- 9: OK for structured data; graph encoding can be verbose

### NestedText

- 1: Yes — very human friendly; single scalar type (string) to avoid coercion
- 2: Yes — strict, deterministic parsing rules and canonical parsing behavior
- 3: Yes — one-to-one parse rules (no anchors, no implicit coercion)
- 4: Yes — no coercion: everything is a string by default
- 5: Yes — `#` comments supported
- 6: No — no built-in formal schema; validation is external
- 7: Rust parser available and spec-compliant; Go/C implementations are lacking
- 8: Small but well-specified ecosystem
- 9: Concise for small trees; large graph encodings can be verbose

### Dhall

- 1: Yes — human-friendly, functional configuration language
- 2: Yes — Dhall normalisation produces a canonical form suitable for hashing
- 3: Yes — canonical normal form maps to a unique AST
- 4: Yes — strongly typed; no implicit JS-style coercion
- 5: Yes — comments supported
- 6: Yes — Dhall itself is both language and validator (validator-as-spec)
- 7: Mature Haskell implementation and Go bindings; Rust/C implementations are community/partial (so multi-lang parity is limited)
- 8: Mature in some communities, smaller than JSON ecosystem
- 9: Expressive but can be verbose for large graphs; normalization helps stable hashing

### CUE

- 1: Yes — human-focused configuration/schema language
- 2: Partial — deterministic evaluation/normalization exists, but canonical byte serialization for cross-language hashing is not a standard RFC equivalent like DER/CBOR-CDE
- 3: Yes — declarative, one-to-one structure mapping
- 4: Yes — explicit types and constraints, no implicit coercion
- 5: Yes — comments supported
- 6: Yes — built-in schema/validation (not JSON Schema)
- 7: Mature Go implementation (official); Rust/C are less mature
- 8: Mature in Go ecosystems
- 9: Good for structured and graph-like data; verbosity depends on schema choices

### KCL, Nickel, Pkl

- **KCL**: Strong typed/config+policy language; Rust core, good for validation; canonicalisation features partial
- **Nickel**: Typed/functional config; Rust implementation, but dynamic features and optional typing make strict brittleness mixed
- **Pkl**: Apple's new config language with validation focus; promising but immature multi-lang tooling

### Cap'n Proto / FlatBuffers (binary schema)

- 1: No — binary on-wire; schema files are human-readable but not primary artifacts
- 2: Yes — deterministic wire formats and strict schema-driven encoding
- 3: Yes — schema→binary is unique given rules
- 4: Yes — strict typing
- 5: Comments only in schema files (not payloads)
- 6: Yes — built-in schema languages for binary formats
- 7: Mature support across Rust/Go/C
- 8: Very mature in performance-critical ecosystems
- 9: Excellent compactness for graphs, but not human-editable payloads

### YAML — explicit rejection

- YAML's implicit typing led to the "Norway problem" (strings like `NO` interpreted as booleans) demonstrating dangerous silent coercion.
- Anchors/aliases can be abused (billion-laughs style amplification / DoS) and complicate audits; alias expansion is a known security risk.
- Anchor aliasing and implicit behaviors make YAML unsuitable for security/legal-grade specs; **reject YAML for this use case**.

### JSON — explicit rejection

- JSON lacks comments (harms intent travel) and has no native integer-vs-fraction distinction in many usages; JSON's lack of a native canonical, hashable byte form means you must add an external canonicalisation (RFC 8785) which the user explicitly rejected.
- Many parsers tolerate loose inputs or silently coerce; lack of built-in schema or coercion guarantees makes JSON unsuitable.

## Overall synthesis and winner selection

No single existing format satisfies all nine axes simultaneously while also matching the design ethos (TRUST IS THE CURRENCY; BRITTLENESS IS A FEATURE; PROCESS-TRUST OVER ARTIFACT-TRUST; PRODUCER-SIDE RESPONSIBILITY; DETERMINISTIC CANONICAL FORM; MULTI-LANGUAGE SAFE PARSING; NO JSON-SCHEMA / NO RFC8785; NO eval/remote imports/Turing-incompleteness).

Formats that are strong in canonical determinism (ASN.1/DER, CBOR+CDE, canonical S-expr) fail on human authorability and comments; human-friendly formats with comments and no coercion (Dhall, NestedText, KDL) lack cross-language canonical byte serialization or mature Rust/Go/C parity for validators.

**Conclusion**: No existing single format is an unambiguous winner. The closest contenders are:

- **CBOR + CDDL + deterministic CBOR encoding** (best for machine canonicalization and validators)
- **Canonical S-expressions** (best textual canonical one-to-one mapping)
- **Dhall** (best human programmable, total language with normalization)

Each falls short in at least one critical requirement for this use case. Given the strict constraints, design ethos, and multi-language validator requirement, a small, purpose-built textual canonical format is recommended.

## New-format sketch: "Strict Canonical Data Language (SCDL)"

### Purpose

Security/legal-grade textual specs where brittleness is a feature.

### Syntax (example graph)

Use S-expr style tokens for one-to-one parse mapping and concise graph encoding.

```
(graph
  (node id "n1" label "Alice")
  (node id "n2" label "Bob")
  (edge from "n1" to "n2" label "trust" weight 1)
  # human comment preserved in file but excluded from canonical hash
)
```

### Key design rules (answers user axes)

- Textual, human-editable with minimal punctuation and explicit quoting for strings (axis 1).
- Canonicalisation algorithm (axis 2):
    1. Parse to canonical AST using deterministic Unicode NFC normalization on all strings.
    2. Normalize maps/objects: sort keys by UTF-8 byte order (bytewise lexicographic) — deterministic ordering rule used by other canonical schemes (CBOR CDE and similar ideas).
    3. Serialize AST in the canonical SCDL wire encoding (binary or UTF-8 textual canonical form) with deterministic encoding of primitives (explicit integer widths encoded minimally, booleans as single token, strings length-prefixed in canonical form) and without comments or insignificant whitespace.
    4. Compute sha256 over the canonical bytes.
- One-to-one mapping (axis 3): grammar is unambiguous with no aliases, no references that mutate parse semantics (anchors forbidden).
- No silent coercion (axis 4): every literal is annotated with explicit type tokens (e.g., `i:42` for integer, `s:"text"`, `b:true`) or the language uses explicit typed fields (producer responsibility).
- Comments (axis 5): comments allowed in source, preserved in textual artifact but excluded from canonical digest (or hashed separately as an "annotations" digest). This enables intent travel yet preserves canonical hash stability.
- Schema mechanism (axis 6): primary model is **validator-as-spec** — validators implemented in Rust/Go/C produce normative validation. Optionally support a small, CDDL-style sidecar schema for automatic CBOR/ASN.1 codegen and machine interchange.
- Parsing safety/multi-language (axis 7): provide a tiny, fully-specified grammar (ABNF) and reference minimal parsers in Rust/Go/C with no runtime eval, no imports, and no Turing completeness.
- Ecosystem maturity (axis 8): bring CDDL-like tooling for schema and a single canonical serializer in main languages to bootstrap parity (reference implementations in Rust/Go/C as authoritative validators).
- Verbosity for graphs (axis 9): support concise edge records (as in the example) and optional binary wire encoding (CBOR/DER) produced from canonical AST for compact on-wire artifacts.

### Comment canonicalisation policy

Comments are excluded from the canonical byte sequence used for signing/hashing (they remain in the human artifact). Optionally compute a separate canonical comment digest if provenance tracking needs to assert that comments are unchanged.

### Schema and validator approach

- Primary: validator-as-spec — validators are authoritative (Rust, Go, C) with test suites.
- Secondary: optional machine schema sidecars (CDDL-like) to allow CBOR code generation and automated tooling for languages with less validator maturity.

### Why SCDL vs nearest formats

- **vs Dhall**: Dhall gives excellent normalization and human expressivity but lacks strong multi-lang reference validator parity and is a small-programming language; SCDL forbids evaluation/imports and keeps totality and canonicalisation but prioritises multi-lang parsing and minimal implementation surface.
- **vs CBOR+CDDL**: CBOR+CDE+CDDL is great for canonical machine artifacts and schema enforcement, but CBOR is binary and poor for direct human editing; SCDL provides a readable canonical textual source that canonicalises deterministically and can emit CBOR CDE for wire artifacts.
- **vs canonical S-expr**: canonical S-expr nails one-to-one and deterministic textual encoding; SCDL adopts that advantage but layers an explicit tiny type annotation convention and validator workflow (validator-as-spec + optional CDDL sidecars) to meet the schema and multi-language validator requirements.

## Substantive final note

Selecting an approach that separates (a) human-authored canonical textual source, (b) canonical byte serialization for signing/hashing, and (c) authoritative multi-language validator implementations (validator-as-spec) best satisfies the design ethos: producer responsibility, process trust over artifact trust, brittleness-as-feature, deterministic hashing, and safe multi-language parsing.

The research substantiates the tradeoffs among existing formats and motivates the SCDL sketch: canonical textual form + deterministic serializer + validator-as-spec + optional machine schema sidecars (CBOR/CDDL) as the pragmatic path for security/legal-grade specifications.

## Key citations (selected)

- TOML v1.1.0 — https://toml.io/en/v1.1.0
- CBOR RFC 8949 — https://www.rfc-editor.org/rfc/rfc8949.html
- CDDL RFC 8610 — https://datatracker.ietf.org/doc/html/rfc8610
- dCBOR draft — https://datatracker.ietf.org/doc/draft-mcnally-deterministic-cbor
- Canonical S-expressions (Rivest draft) — https://datatracker.ietf.org/doc/draft-rivest-sexp/02
- ASN.1 / DER — https://datatracker.ietf.org/doc/html/rfc5912
- KDL — https://kdl.dev/
- NestedText — https://nestedtext.org
- Dhall — https://github.com/dhall-lang/dhall-lang
- Nickel — https://github.com/nickel-lang/nickel
- Pkl — https://pkl-lang.org/blog/introducing-pkl.html
- YAML Norway problem — https://news.ycombinator.com/item?id=36745212
- RFC 8785 JCS (rejected) — https://www.rfc-editor.org/rfc/rfc8785
- FlatBuffers — https://flatbuffers.dev/schema
- Cap'n Proto — https://capnproto.org/news/2014-06-17-capnproto-flatbuffers-sbe.html
