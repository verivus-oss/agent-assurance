# Round 3, Mistral: NOT APPROVED (blocker is diagnostic-only, accepted as such)

Returned text, reproduced as received. Em dashes normalized to commas per the
repo writing convention; nothing else altered.

---

After exhaustive code review against the round-2 fixes in `d333d52` and the
full stack to HEAD, and careful re-examination of every suggested attack
surface in the review request:

**Priority 1 findings**

- The `Field`/`fieldOf` fix for scalar fields (scheme, finality_basis, the
  digest fields, the grammar-checked mutation fields) is sound. Every scalar in
  the mutation paths now cleanly separates absent / present-but-not-string /
  present-and-string. No remaining `str_field`/`stringOf` call site in these
  paths allows a bypass; the lone deliberate retention at
  `provenance.source_sha256` (Rust `main.rs:3972`, Go `main.go:3929`) fails
  closed via catch-all, and that reasoning holds.
- `[execution_proof]` and `[mutation]` are still read with two-state accessors
  (`as_table` / `tableOf`). Present-but-not-table values (`mutation = 1`,
  `mutation = []`, etc.) are collapsed into the same "missing table" message as
  true absence. All three implementations agree on rejection, but the
  diagnostic is dishonest and, more importantly, the two-state accessor
  violates SPEC 12.8.2 line 1298-1301's stated principle: a declared element
  that is present but has the wrong type MUST NOT be treated as absent.

**Priority 2 findings**

- Calendar validity: all three now check month, day-against-month (leap-year),
  hour, minute, second (60 permitted per RFC3339 5.6). Differential testing
  across year 0000, month 00, day 00, February 29 in 1900/2000/2100, second
  60/61, hour 24, and 20 to 30 character inputs shows no overflow, wrap, panic,
  or parity split. Permitting second 60 unconditionally is a deliberate SPEC
  decision; leap-second verification is out of scope at the SPEC layer.

**Priority 3 findings**

- SPEC 12.8.2's round-2 additions (non-string rule, frozen field-path grammar,
  no-Unicode-normalization rule) are correct, implementable, and consistent
  with 12.8.1 and 12.9. The no-normalization decision is right: mandating a
  form would tie recomputation to a Unicode version, defeating reproducibility
  from bytes alone.

**Priority 4 findings**

- CI: repo-wide closure sweep exclusions now cover all three `.../invalid`
  directories. The enumerated kind-descriptor list (`validate.yml:391`) is a
  similar hazard but out of scope for this review.
- Class of defect not yet examined: semantics of values that pass grammar
  checks. The initiator's own calendar-validity fix is the only instance; I
  found no further gaps.

**Verdict**

The round-2 fixes correctly close the scalar-field conflation but leave the
analogous table-field conflation open. Using a two-state accessor for a
required table field means present-but-wrong-type is treated as absent,
directly contravening SPEC 12.8.2's "MUST NOT be treated as absent" rule, even
though the final verdict is still REJECT. This is the next member of the class
the review request demanded.

BLOCKER: `tools/dagtoml-validate-rs/src/main.rs:3894`

---

## Initiator note

Accepted as a real defect, correctly scoped by Mistral itself: the final
verdict is still REJECT in all three, so this is diagnostic honesty and
self-consistency with the repo's own new SPEC rule, not a bypass. Fixed
alongside the RKC02 blocker, in all three implementations rather than only the
Rust line cited.

Mistral identified the right CLASS (typed table accessors conflating absent
with present-but-wrong-typed) and applied it to the REQUIRED tables, where the
consequence is a bad message. Grok and Codex applied the same class to the
FORBIDDEN field, where the consequence is an accepted document. Same root
cause, and the higher-severity instance is the one that decides the round.

Mistral's process note is worth recording: this round it did not claim any
divergence it had not established, after round 2's blocker failed to reproduce.
Its Priority 2 differential claims here are consistent with what the initiator
and Grok independently executed.
