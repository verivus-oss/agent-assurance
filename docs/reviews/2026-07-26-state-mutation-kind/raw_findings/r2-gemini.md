# Round 2, Gemini: NOT APPROVED

Returned text, reproduced as received. Em dashes normalized to commas per the
repo writing convention; nothing else altered.

I have retrieved the diff, read the changed files, compiled the Rust and Go
primaries locally, and executed differential testing against the Python
reference. Here is my review based entirely on evidence.

**Priority 1: SPEC 12.8.2**

- **Injectivity:** Prehashing via digest scalars (`sha256:<hex>`) successfully
  ensures injectivity. Because the delimiter (`\n`) cannot be forged inside the
  fixed-width hex string, the collision path from Round 1 is structurally
  closed.
- **Optional inputs:** Prohibiting a `when-present` form is the correct call. If
  the bound tuple allowed optional inputs, an attacker could silently drop
  fields to forge a binding, rendering the commitment meaningless.
- **Double commitment:** Placing `binds_sha256` in the `closure_root` (12.8.1)
  is sound and mechanically linear. The generator hashes the `[mutation]` fields
  to compute `binds_sha256`, embeds it in `[execution_proof]`, and then computes
  the `closure_root` over the document. There is no circularity or
  update-ordering hazard.
- **Underspecification:** The text "UTF-8 bytes of the field's value"
  successfully resolves timestamp normalization, as section 9.2 forbids native
  TOML date-times; timestamps are strings, so their bytes are simply the
  string's UTF-8. It implicitly resolves the `sha256:` prefix (the prefix is
  part of the string value, so it is hashed). However, it **fails to resolve
  Unicode form**. A string encoded in NFC has different UTF-8 bytes than the
  same string in NFD, leading to different hashes for visually identical
  documents. The text must mandate a normalization form.

**Priority 2: Rust and Go ports (differential testing)**

I constructed differential tests targeting edge cases and found severe parity
breaks.

- **Divergence 1 (type silencing and RKM04):** When a bound field is present but
  has the wrong TOML type (e.g. `effect_sha256 = 12345`), Python correctly emits
  a type defect ("is not a digest scalar") and explicitly skips RKM04 at
  `validators/validate_state_mutation.py:318` because
  `all(isinstance(..., str))` fails. The Rust primary
  (`tools/dagtoml-validate-rs/src/main.rs:3814`) and the Go primary
  (`tools/dagtoml-validate-go/main.go:3783`) use typed getters that silently
  discard the integer. They incorrectly report the field as missing ("is
  required") and then proceed to compute RKM04 over hallucinated empty strings,
  outputting a bogus mismatch against
  `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
  (the empty string hash).
- **Divergence 2 (short-circuiting):** If the `[mutation]` table is missing,
  Python reports the missing table and cascades errors for all missing bound
  fields. Rust and Go short-circuit and emit only the missing table error.

**Priority 3: `mutation-claim` and RKC02**

The claim/proof split holds. `mutation-claim` outright rejects any
`[execution_proof]` (RKC02), while `state-mutation` requires it (RKM02). A
document cannot masquerade as one while being read as the other.
`claim-record.v1` is a coherent third abstraction: an observation is external
state, an execution is a proved action, and a claim is an unverified intent.
Promotion is mechanical because both kinds share the identical `[mutation]`
schema and validation logic.

**Priority 4: round-1 fixes**

- Non-injective bound tuple: fixed by the prehashed encoding.
- RKM03 bypass: fixed. `proof_locator` is now regex-constrained and rejects
  arbitrary payloads.
- `provenance.source_sha256`: fixed. Python, Rust and Go now explicitly validate
  its presence and type.
- Hollow proof: fixed. The `scheme` and `finality_basis` fields are now
  required.
- `provider-receipt` retention: retaining this is the correct semantic decision.
  A Web2 API response (HTTP 200 OK) is a real state mutation without a
  cryptographic proof. Forcing a producer to drop the event or lie and use
  `tee-quote` corrupts the data. Policy layers can reject `provider-receipt` if
  their threat model requires cryptography.

**BLOCKER: the Rust and Go primaries diverge fundamentally from the Python
reference in handling wrong types, causing them to silently discard user data
and execute RKM04 on hallucinated inputs.** When a bound field is present but
has the wrong type, Python correctly reports the type violation and skips RKM04.
Rust (`main.rs:3814`) and Go (`main.go:3783`) use typed getters that silently
coerce the wrong-type value to missing. They report the field as "required"
(discarding the provided data) and then execute RKM04 by hashing an empty
string, yielding a bogus defect against the empty-string SHA-256. This breaks
the exact parity claim and masks type violations in the primaries.

---

## Initiator note on Gemini's round-2 blocker

Recorded because the severity claim did not survive checking, while the finding
did. Accept/reject parity HOLDS for the wrong-typed case: all three
implementations reject `effect_sha256 = 12345`. What diverged was the
DIAGNOSTIC, and the criticism of it is correct and was acted on. Both primaries
now report the type defect and skip RKM04 rather than reporting a mismatch
against a tuple no producer wrote. See `r2-fixes` in the design record.

Gemini's Unicode-normalization finding on 12.8.2 was independently raised by
Grok and Codex and is addressed in the SPEC text.
