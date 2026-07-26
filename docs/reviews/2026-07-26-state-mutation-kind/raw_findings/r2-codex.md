# Round 2, Codex: NOT APPROVED

Final verdict message, reproduced as received. Em dashes normalized to commas
per the repo writing convention; nothing else altered. The full session
transcript ran to 663 KB (gateway job `a2493e39-c0e5-4172-a5a1-6d493e955560`,
correlation `d2492a70-1cd4-451b-b699-8f8362dfc2eb`); this is its conclusion.

Not approved.

- Both primaries built successfully. Shipped positives and negatives produced
  the expected verdicts, and claim promotion worked mechanically after adding a
  proof, changing kind, and recomputing the root.
- The original newline collision is fixed for the current five-field tuple: the
  legacy streams collided; prehashed streams differed. The operation-injection
  fixture is rejected by all three.
- 12.8.2 correctly defines UTF-8 leaf hashing and prevents optional membership.
  The double commitment is acyclic: fields produce `binds_sha256`, then proof
  digest, then closure root. It still lacks a generic declaration format, a
  non-string value rule, and 12.8.1's explicit frozen path grammar.
  (`spec.md:1210`, `spec.md:1280`)
- Differential testing found that Python accepts Unicode decimal digits in
  `performed_at`, while Rust and Go reject them. More seriously, the primaries
  accept wrong-typed proof fields.

Starting from the valid fixture, I retained valid closure pins and set:

```toml
scheme = 1
finality_basis = 2
proof_locator = 3
```

Python rejects all three. Both release primaries exit 0 in both
`--mode mutation-kinds` and auto-dispatch. Rust checks only key presence, then
silently skips non-strings; Go does the same.
(`validators/validate_state_mutation.py:270`,
`tools/dagtoml-validate-rs/src/main.rs:3942`,
`tools/dagtoml-validate-go/main.go:3898`)

The Python closure sweep also fails on the new tracked invalid conformance case
because CI excludes only the implementation-DAG and api-snapshot invalid
directories, not `state-mutation/invalid`.
(`.github/workflows/validate.yml:383`)

**BLOCKER: MUTATION-PRIMARY-TYPE-BYPASS.** Rust and Go accept a
`state-mutation` whose required scheme, finality, and proof locator are
integers, contradicting claimed RKM02/RKM03/RKM06 parity and allowing a
proof-shaped record with no usable typed proof.
