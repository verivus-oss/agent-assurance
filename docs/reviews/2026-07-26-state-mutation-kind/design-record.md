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

### What is still open

- The bound-tuple grammar is now normative (SPEC 12.8.2) and implemented three
  times, but SPEC 12.8.2 itself has had no independent review: it was written
  in response to a round-1 blocker and reviewed by nobody yet.
- `mutation-claim` has no conformance cases.
- The `provider-receipt` retention decision still stands against one reviewer's
  blocker and remains the operator's to reverse.
