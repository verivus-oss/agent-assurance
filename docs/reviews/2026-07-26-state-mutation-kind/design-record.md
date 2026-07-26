# Design record: the `state-mutation` kind

Created 2026-07-26. Status: **proposal on a branch, NOT reviewed, NOT merged.**
The repo rule of no initiator self-approval applies: this needs an independent
multi-LLM design review dispatched via `tools/review-request-dag.toml`, with
evidence persisted under `docs/reviews/`, before it can land.

## Why this exists

The W3C ADACG reviewer's second round asked for a `state-mutation` kind with a
mandatory `execution_proof` block, on the grounds that observation is cheap and
mutation is where the liability lives. An `api-snapshot` explicitly "asserts
nothing about authorization, ordering, or finality", so it cannot evidence a
completed state change.

## The decision that shaped it

The reviewer proposed hardwiring "ledger tx hash plus TEE quote, or ZK receipt"
into the kind. Two objections were raised in review and both are reflected here.

1. **Hardwiring specific proving systems** makes the kind KYA-3-only by
   construction and collapses the graduated model. Resolved by a closed
   `execution_proof_scheme` vocabulary plus a `finality_basis` vocabulary, with
   WHICH schemes are acceptable left to the consuming conformance profile.
   The kind fixes that a proof exists; policy fixes whether it is strong enough.

2. **A bare transaction hash proves a transaction happened, not that THIS
   authorization produced THAT effect.** Resolved by `binds_sha256` plus RKM04.

The contested question was whether the proof should be mandatory in the kind at
all, or whether mandatoriness belongs entirely in the tier binding. The board
split. The deciding argument, and the one adopted: a record NAMED
`state-mutation` that carries no proof is a record whose name asserts more than
its content, so the proof is mandatory here and unproved entries must use a
different, observation-shaped or intent-shaped kind name. Scheme acceptability
remains policy.

## The structural property worth keeping

All five pinned closure records for this kind are `required`, deliberately
unlike the api-snapshot witness pinned `when-present`.

- A witness may legitimately be absent, so deleting it and honestly re-rooting
  produces a valid unwitnessed document. That is ratified behaviour
  (`conformance/cases/api-snapshot/valid/unwitnessed-three-record.toml`).
- An execution proof may not be absent, so the same manoeuvre removes two
  REQUIRED pins and fails the closure gate in all three implementations.

`examples/negative/state-mutation-no-proof.toml` proves it: the fixture deletes
`[execution_proof]` and honestly recomputes the root over the three remaining
records, and the closure validator reports both missing required pins.

## What was verified locally

Run from this worktree with `PYTHONPATH=validators`:

| Check | Target | Result |
|---|---|---|
| `validate_closure_root.py` | `examples/minimal-state-mutation.toml` | PASSED (five-record root, independently recomputed before it was written into the file) |
| `validate_provenance.py` | same | PASSED against the shipped capture |
| `validate_state_mutation.py` | same | PASSED |
| `validate_kind_descriptor.py` | the kind | PASSED |
| `validate_abstraction_class.py` | the kind | PASSED |
| `validate_profile_descriptor.py` | `PROFILE.toml` | PASSED (INV07 accepts the four new pins) |
| `validate_ijb_conformance.py` | the ontology | PASSED |
| closure sweep as CI invokes it | whole tree | PASSED, 87 files |
| `state-mutation-no-proof` | closure | REJECTED, two missing required pins |
| `state-mutation-unbound-proof` | closure PASSES by design; kind layer | REJECTED, RKM04 |
| `state-mutation-inlined-proof` | closure PASSES by design; kind layer | REJECTED, RKM03 closed key set |

All three negatives also fail `validate_provenance.py` on a deliberate
`source_bytes` mismatch, per the `examples/negative/` convention.

## Round 1 review outcome and what changed

Four independent reviewers (Codex, Gemini, Grok, Mistral). **All four withheld
approval.** Verbatim verdicts in `raw_findings/`. Every blocker below was
demonstrated by a crafted document, not asserted, and every fix is verified.

**Codex, decisive blocker: the bound-tuple encoding was non-injective.** The
original form inlined values as `<field> <value>\n`, while `operation` and
`performed_at` accepted any non-empty string. A newline inside a value forges a
different field assignment with an identical digest. Codex built two distinct
valid documents sharing `sha256:136b…e645`. One `binds_sha256` bound two
mutations, which defeats RKM04 entirely.

Fixed by **prehashing every value**: each record is now
`<field> sha256:<64 hex>\n` over the UTF-8 bytes of the value, so no
attacker-controlled byte reaches a delimiter position and the record type
contract becomes identical to the SPEC 12.8.1 pins. This removes the attack
class rather than filtering for it. Value grammars (RFC3339 UTC, bare-token
`operation`, URI-shaped `target_id`) were added as defence in depth, not as the
control. Regression fixture: `state-mutation-operation-injection.toml`.

**Grok, blocker: RKM04 had no SPEC-normative byte contract and no primary
parity.** `spec.md` contained no mention of bound tuples at all. Fixed by
adding **SPEC 12.8.2 Bound tuples** as normative text next to 12.8.1, including
the prehashing requirement and its rationale, and the rule that bound tuples
have no `when-present` form. Primary parity for the kind-layer invariants
remains open and is recorded below.

**Codex: RKM03 was bypassable.** A raw proof payload pasted into
`proof_locator` validated cleanly, since the key was permitted with no format
constraint. Closed key sets are necessary, not sufficient. Fixed with an
enforced URI grammar, and `proof_locator` is now REQUIRED, since a proof pinned
only by digest with no way to fetch it is a claim rather than evidence.

**Grok: `provenance.source_sha256` was a declared required field the validator
never checked.** A document with no `[provenance]` table passed everything.
Fixed.

**Grok: hollow proofs pass the primaries.** An `[execution_proof]` carrying only
the two pinned digests is closure-valid in all three implementations; only the
Python kind layer sees that no typed proof is present. This is the recorded
RKM02 boundary and cannot be closed without porting the kind layer, so it is
now pinned down by fixture `state-mutation-hollow-proof.toml` and wired into CI
rather than left theoretical. My original claim that the kind "cannot be
downgraded" was true for deletion and false for hollowing; the descriptor and
CHANGELOG now say so.

**Gemini, blocker: `provider-receipt` subverts the mandatory-proof rule**, since
a hashed HTTP 200 satisfies the schema. Grok argued the opposite: the SPEC layer
verifies no scheme, so removing the honest label for "counterparty said so" does
not make weak evidence unrepresentable, it makes producers mislabel it as
`tee-quote`. **Retained, with mitigation**, and the reasoning is recorded in the
ontology notes so the decision is visible rather than implicit. The mitigation is
new invariant **RKM06**: a scheme may only claim durability its evidence class
can carry, so `provider-receipt` can never assert ledger finality and
`tee-quote` may claim only `none`. That also closes Grok's separate finding that
no scheme-by-finality coherence rule existed. **This one is a judgment call and
is reversible; it is flagged for the operator.**

**Mistral: `ontology_version` should stay at 1.** Rejected on evidence, 3 to 1.
Codex, Gemini and Grok each independently confirmed the bump to 2 is correct for
a profile already published on main. Recorded in `raw_findings/mistral.md`.
Separately, Grok's hygiene note was accepted: `PROFILE.toml` and
`api-snapshot-kind.toml` now also say 2.

## Known gaps, stated rather than assumed away

1. **CLOSED.** The primaries now implement RKM02, RKM03, RKM04, RKM06 and
   RKC02. Previously: Only the closure
   layer (RKM01) has triad parity, because the pins are ordinary SPEC 12.8.1
   records, and deletion of the proof is therefore triad-caught (a missing
   required pin). The remaining kind-layer checks are Python-only, exactly as
   RKV02 and RKV03 are for api-snapshot. A port is not scheduled. The split is
   recorded in RKM02's `enforcement_boundary` field rather than papered over
   with an aspirational `enforced_by_primaries`.
2. **Conformance corpus is minimal.** `conformance/cases/state-mutation/` now
   exists with one valid and one invalid case; the api-snapshot split is
   richer and this should grow before merge.
3. **CLOSED in round 1.** The bound-tuple byte form is now normative at SPEC
   12.8.2.
4. **The bound tuple does not cover `provenance.source_sha256`.** Both Gemini
   and Grok examined this and independently concluded the boundary is right:
   the capture is already a pinned closure record, and the external system
   producing the proof has no knowledge of the agent's capture digest, so
   including it would require the target to sign the agent's own observation.
   Treated as resolved unless round 2 disagrees.
5. **CLOSED.** `mutation-claim` ships as the companion kind: identical
   `[mutation]` table so promotion is mechanical, three-record closure, and
   RKC02 forbidding `[execution_proof]` in either direction.
6. **`provider-receipt` retention is a judgment call** (see round 1 above),
   made against one reviewer's blocker. Reversible by deleting one vocabulary
   value and its RKM06 row.


## Round 2 additions: companion kind and primary parity

Both remaining gaps from round 1 are closed.

**`mutation-claim`.** All three substantive reviewers named the same cost of
the mandatory-proof decision: a producer with a genuine mutation and no proof
had no kind, which does not make the case disappear, it makes producers
mislabel it. The companion kind carries an identical `[mutation]` table so
promotion is mechanical (add the proof table, change `template_kind`, re-root),
pins three closure records, and declares abstraction class `claim-record.v1`
distinct from both `observation-record.v1` and `execution-record.v1`.

RKC02 enforces the split in BOTH directions: a claim must not carry
`[execution_proof]` (or a proved record could escape RKM02, RKM04 and RKM06 by
renaming itself), and a proof-bearing document must use `state-mutation`. This
cannot be a closure rule, because a stream can pin the presence of a field but
never its absence, so it is a kind-layer invariant with a negative fixture
asserted against all three implementations.

**Primary parity.** `validateMutationKinds` (Go) and `mutation_kinds` (Rust)
port RKM02, RKM03, RKM04, RKM06 and RKC02, wired into both auto dispatch and an
explicit `--mode mutation-kinds`. The motivating case was Grok's hollow proof:
an `[execution_proof]` carrying only the two pinned digests is closure-valid,
so before the port a primary-only consumer accepted a state-mutation with no
typed proof at all. It is now rejected by all three.

Cross-implementation parity verified on the bound tuple, which is the byte-level
contract that matters most:

| Implementation | expected `binds_sha256` for the unbound fixture |
|---|---|
| Python | `sha256:7a5604ab…fda87` |
| Rust | `sha256:7a5604ab…fda87` |
| Go | `sha256:7a5604ab…fda87` |

Both primaries pass every positive (`state-mutation`, `mutation-claim`, and the
unrelated `api-snapshot` control) and reject all five state-mutation negatives
plus the RKC02 claim-with-proof negative. The RFC3339, operation-token and
URI-shape grammars are hand-rolled in both, matching the Python regexes, since
the Rust crate carries no regex dependency by policy.

Repo-wide closure sweep as CI invokes it: PASSED, 90 files.

**That sweep claim was wrong when written, and round-2 review caught it.** The
conformance case added in the same commit is a tracked file, and the Python
sweep in CI enumerated its exclusions by directory, listing
`conformance/cases/implementation-dag/invalid` and
`conformance/cases/api-snapshot/invalid` but not `state-mutation/invalid`. So CI
was red on this branch as committed, on a deliberately closure-invalid fixture
that the primaries' own discovery step already skipped generically. The claim
went stale the moment the fixture landed and the verification was not re-run.
Fixed in round 2 by adding the exclusion; the sweep now genuinely passes at 90
files.

## Round 2 review outcome and what changed

Four independent reviewers again (Codex, Gemini, Grok, Mistral). **All four
withheld approval.** Verbatim verdicts in `raw_findings/r2-*.md`. Three named
blockers reproduced against the code; one did not.

**One root cause produced two of the three blockers.** Both primaries reached
string fields through an accessor that returned the same "nothing here" answer
for an absent key and for a key holding a non-string, then defaulted to `""` and
skipped any check keyed on a non-empty value.

- **Grok, decisive: blank vocabulary tokens.** `scheme = ""` and
  `finality_basis = ""` passed both primaries in auto and explicit mode while
  the Python reference rejected them. This reopened the hollow-proof class
  round 1 named, from a new direction: the earlier fix closed ABSENT proof
  fields, so this document satisfies key presence, carries both pinned digests,
  is closure-valid, and declares no proving system at all.
- **Codex: wrong-typed proof fields.** `scheme = 1`, `finality_basis = 2`,
  `proof_locator = 3` bypassed the closed vocabulary, RKM06 and the RKM03
  locator grammar simultaneously, for the same reason.

Fixed by giving both ports a three-state accessor (`Field`/`fieldOf`:
absent, present-but-not-a-string, string) and checking vocabulary membership
with no empty-string and no wrong-type escape. Regression fixtures
`state-mutation-blank-scheme.toml` and `state-mutation-wrong-typed-proof.toml`,
both deliberately closure-valid so the kind layer is demonstrably the only thing
that can reject them.

**Codex: Python accepted Unicode decimal digits in `performed_at`.** The
divergence ran the opposite way to the others: `\d` on a Python str pattern
matches U+0662 and friends, so the REFERENCE accepted `٢026-07-26T10:15:00Z`
while both ASCII primaries rejected it. The primaries were right; RFC3339 is
ASCII. Fixed in Python. Fixture
`state-mutation-unicode-digit-timestamp.toml`.

**Gemini: wrong-typed bound field produced a bogus RKM04 defect.** Severity
overstated, finding correct. Accept/reject parity held (all three reject), but
the primaries reported the field "required", discarded the value, then computed
the bound tuple over empty strings and reported a mismatch against a tuple no
producer wrote, burying the real type defect. Both ports now skip RKM04 unless
every bound field is a string, matching the Python guard.

**Mistral: RFC3339 single-fractional-digit divergence. Did NOT reproduce.**
`2026-07-26T10:15:00.1Z` is 22 characters, not 21, so all three accept it. The
arithmetic error is consistent with Mistral's own statement that it could not
execute the binaries, and it was the only round-2 blocker that failed to survive
contact with a running implementation. Recorded in `raw_findings/r2-mistral.md`
rather than quietly dropped.

**Also fixed, found by the initiator's own differential run before the verdicts
returned:** `performed_at = "2026-99-26T10:15:00Z"` passed all three, because
every implementation checked digit positions and not calendar validity. That
field is a member of the RKM04 bound tuple and carries the freshness claim, so
an impossible instant was being bound into the proof. All three now validate
month, day (against the month, with the leap-year rule), hour, minute and second
(60 permitted, per RFC3339 5.6). No round-2 reviewer found this independently.

**SPEC 12.8.2 gaps, raised independently by Grok, Gemini and Codex.** The
section did not fix a Unicode normalization form, did not state that a
non-string bound field is an error rather than an absent one, and did not freeze
the field-path grammar the way 12.8.1 does (Grok's point: a path containing 0x20
or 0x0A would reintroduce at the label boundary exactly the ambiguity prehashing
removes at the value boundary). All three are now normative text. Normalization
is resolved by REQUIRING that none is applied, with the reasoning stated: making
recomputation depend on a Unicode version would defeat reproducibility from
bytes alone.

### What is still open

- SPEC 12.8.2 has been reviewed once, and the round-2 additions to it have not.
- `mutation-claim` still has no conformance cases.
- The `provider-receipt` retention decision now stands against one reviewer's
  round-1 blocker with a second reviewer (Gemini, round 2) independently
  reversing position and arguing FOR retention. It remains the operator's to
  reverse.
- Vocabulary source still differs between reference and primaries: Python loads
  the closed vocabularies from the profile ontology at run time, both primaries
  compile them in. A profile that extends `execution_proof_scheme` or
  `finality_basis` will be accepted by the reference and rejected by the
  primaries until they are rebuilt. Recorded in RKM02's `enforcement_boundary`.
