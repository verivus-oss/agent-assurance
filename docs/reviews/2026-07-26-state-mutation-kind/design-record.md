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

## Known gaps, stated rather than assumed away

1. **The primaries do not implement RKM03 or RKM04, and only half of RKM02.** Only the closure
   layer (RKM01) has triad parity, because the pins are ordinary SPEC 12.8.1
   records, and deletion of the proof is therefore triad-caught (a missing
   required pin). The remaining kind-layer checks are Python-only, exactly as
   RKV02 and RKV03 are for api-snapshot. A port is not scheduled. The split is
   recorded in RKM02's `enforcement_boundary` field rather than papered over
   with an aspirational `enforced_by_primaries`.
2. **No conformance cases yet.** `conformance/cases/state-mutation/` should
   mirror the api-snapshot valid/invalid split before merge.
3. **`binds_sha256` canonical form is defined only in the Python validator and
   the kind prose.** If this kind proceeds, the tuple's byte form belongs in
   the spec next to SPEC 12.8, not in an implementation.
4. **The bound tuple does not cover `provenance.source_sha256`.** That is
   arguable: the proof binds the mutation, and the capture is separately pinned
   into the closure. Review should confirm the boundary is right.
