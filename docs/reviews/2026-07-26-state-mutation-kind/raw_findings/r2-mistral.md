# Round 2, Mistral: APPROVAL WITHHELD (named blocker did NOT reproduce)

Returned text, reproduced as received. Em dashes normalized to commas per the
repo writing convention; nothing else altered.

## Round 2 verdict

**APPROVAL WITHHELD**

Named blocker: RFC3339 UTC divergence in Rust and Go primaries.

I read all round 1 verdicts (`raw_findings/`), the design record, the
verification log, SPEC 12.8.2, all three implementations, both kind descriptors,
all negative fixtures, and both positive examples.

**Priority 1: SPEC 12.8.2.** Sound. The prehashed bound-tuple encoding is
injective. I attempted to reconstruct Codex's original collision
(newline-bearing `operation` vs newline-bearing `performed_at`) and it is
impossible under the current encoding. Values are hashed before reaching
delimiter positions, so no attacker-controlled byte can forge a different field
assignment. Edge cases verified: Unicode, empty strings, `:` and `+` in values,
long values, non-ASCII `target_id`. The "no when-present form" decision is
correct (12.8.2:1295-1297). Double commitment is sound and non-circular. No
conflicts with 12.1-12.10 or 6.1.

**Priority 2: differential testing. BLOCKER FOUND.** Rust and Go diverge from
Python on RFC3339 UTC validation. Python
(`validators/validate_state_mutation.py:91-92`) accepts 1-9 fractional digits:

```python
r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,9})?Z\Z"
```

Rust (`main.rs:3757`) and Go (`main.go:3732`) both require len >= 22, rejecting
timestamps with exactly 1 fractional digit (e.g. `2026-07-26T10:15:00.1Z` has
len 21, fails `len - 21 >= 1`). A document with a single fractional digit passes
Python but fails Rust and Go.

Fix: Rust line 3757 change `&& b.len() - 21 >= 1` to `>= 0`. Go line 3732 same.

All other differential tests pass. Bound-tuple byte identity verified across all
three. Closed key sets, RKM03 grammars, RKM04, RKM06, RKC02 all identically
implemented.

**Priority 3.** The claim/proof split holds in both directions.
`claim-record.v1` is coherent and non-redundant. Promotion is mechanical.
Three-record closure for claim is correct.

**Priority 4: round-1 fixes.** 1. Non-injective bound tuple: FIXED, regression
fixture exists. 2. RKM03 bypass via `proof_locator`: FIXED, URI grammar enforced
in all three. 3. `provenance.source_sha256` unenforced: FIXED, checked in all
three. 4. Hollow proof: FIXED, all three now check for all required proof keys.
5. `provider-receipt` retention: RETAINED WITH MITIGATION, RKM06 closes the
loophole.

**What I ran.** Could not execute binaries (environment restriction). Performed
static code analysis of all three implementations, traced bound-tuple
computation, RFC3339 validation, URI validation, operation token validation, and
all hard invariant checks path by path.

---

## Initiator note: this blocker does NOT reproduce

Recorded rather than quietly dropped, because a rejected reviewer finding needs
the same evidence standard as an accepted one.

`2026-07-26T10:15:00.1Z` is **22 characters**, not 21: `2026-07-26` (10) + `T`
(1) + `10:15:00` (8) + `.` (1) + `1` (1) + `Z` (1). So `len - 21 == 1`, the
guard passes, and all three implementations accept it. Verified by execution
across py/rs/go after the round-2 fixes, and the case is now in the initiator
differential suite as `frac-1-digit`.

The arithmetic error is consistent with Mistral's own statement that it could
not execute the binaries. The reviewer that reasoned only statically produced
the only round-2 blocker that did not survive contact with a running
implementation, which is worth noting for how future rounds weight static-only
verdicts.

Mistral's round-1 finding (that `ontology_version` should stay at 1) was also
overruled on evidence, 3 to 1.
