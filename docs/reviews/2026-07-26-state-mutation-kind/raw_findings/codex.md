# Codex, round 1 verdict (verbatim)

Job `9a4e7438-1549-4f80-b391-8908ff2c66dc`, exit 0. Target `8290eb3`.

---

Not approved.

- All requested Python positive checks passed, including the 87-file closure sweep. Each requested negative failed for its stated invariant.
- I independently recomputed the example: `binds_sha256` is `sha256:bafc…e52b`; `closure_root` is `sha256:f4fd…f435`; capture digest and byte count also match.
- No Rust or Go primary binary exists locally, so I did not execute either. CI is wired to run their no-proof negative at validate.yml:863, but that is not executed parity evidence.

Claim review:

1. Required pins do reject a deleted proof in Python, as observed. The five pins are declared required at PROFILE.toml:72. However, a document without `proof_locator` also validates, so it can contain only unverifiable digest claims, not a usable proof. `proof_locator` is allowed but not required at validate_state_mutation.py:70.

2. RKM04 fails its central claim. The serializer emits unescaped `<field> <value>\n` records at validate_state_mutation.py:103, while `operation` and `performed_at` require only nonempty strings at validate_state_mutation.py:151. I constructed two distinct documents that both returned no state-mutation or closure errors and share `sha256:136b…e645`: one has a newline-bearing operation, the other a newline-bearing timestamp. Thus one proof binding can validate distinct tuples. Excluding `provenance.source_sha256` is a separately acknowledged limitation, but it is not the decisive flaw.

3. Making a proof mandatory is a defensible semantic position, but it has the stated cost. This profile contains only `api-snapshot` and `state-mutation` at PROFILE.toml:39, so it ships no companion intent or unproved-execution kind.

4. `provider-receipt` with `finality_basis = "none"` validates. Both are admitted independently by ontology.toml:94 and validate_state_mutation.py:177. This leaves proof strength entirely to an external policy. `provider-acknowledged` is counterparty acceptance, whereas ledger confirmation/finality are ledger-state properties, so `finality_basis` conflates different axes.

5. The ontology bump is correct: the prior ontology was version 1, this change is version 2 at ontology.toml:29, and the public-release rule requires it at ontology.toml:118.

6. The declared gaps are incomplete. In addition to the Python-only checks and missing conformance corpus, RKM04 has the collision above. RKM03 is also bypassable: I put a raw proof payload in `proof_locator` and the validator returned no errors, despite RKM03's prohibition at state-mutation-kind.toml:209.

**BLOCKER: RKM04 canonical bound-tuple encoding is non-injective, so it does not uniquely bind a proof to one mutation.**
