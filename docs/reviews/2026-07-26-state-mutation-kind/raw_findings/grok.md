# Grok, round 1 verdict (verbatim, abridged to findings and verdict)

Job `9f720fdf-19f1-42b4-9fdc-30bd5e4c66c2`, exit 0. Target `8290eb3`.

---

## What I ran (not trusted from the design record)

Independent recompute of `source_sha256`, `binds_sha256`, the five-record
`closure_root`, and the honest three-record root for the no-proof fixture: all
match the committed files. All listed Python validators, the 87-file sweep, and
both primaries exercised.

## Claim 1: `required` vs `when-present` asymmetry

**Deletion of `[execution_proof]` fails the closure gate in all three
implementations. Verified.** Python, Rust and Go all FAIL with the same two
missing required pins. Contrast confirmed: the api-snapshot
`unwitnessed-three-record.toml` conformance case PASSES Rust provenance mode.

**But "no usable proof can still validate" is false as a general claim.**

Crafted a hollow document: `[execution_proof]` present with only `proof_sha256`
and `binds_sha256` (correct binds), no `scheme`, no `finality_basis`.

| Gate | Hollow result |
|---|---|
| Rust primary | PASSED |
| Go primary | PASSED |
| Python closure | PASSED |
| Python provenance | PASSED |
| Python `validate_state_mutation.py` | FAILED (RKM02 completeness) |

Deletion is triad-caught. Hollowing is not. A primary-only consumer will accept
a document that reads as a state-mutation with no typed proof at all. An empty
`[execution_proof]` table with no keys IS triad-rejected; the hole is
incomplete-but-pinned-digest proof.

## Claim 2: RKM04

Example binding recomputes correctly. Tuple membership excluding
`provenance.source_sha256` is sound: the capture is already in the 12.8 stream.

**Second-implementer byte identity: not good enough.** `spec.md` has zero hits
for `binds_sha256`, `bound tuple`, `RKM04`, or `state-mutation`. The canonical
form lives only in `validate_state_mutation.py:103-117` and kind prose. 12.8.1
pin emission is digest-only; the bound tuple mixes free strings with digest
scalars, so it is the same shape but not the same type contract. Underspecified:
timestamp normalization, Unicode form of `target_id`, whether the `sha256:`
prefix is part of the hashed value, whether binds is always SHA-256. Rust and Go
do not implement RKM04: the unbound fixture PASSES both under
`--mode provenance`.

## Claim 3: contested decision

The other side, properly: mandatoriness in the kind collapses "typed mutation
record" with "proof-strength policy", forbids recording real mutations before a
receipt exists (async finality, provider lag, offline windows), forces
kind-switching across a single business event's lifecycle, and departs from
api-snapshot's graduated witness model.

Observed cost: a producer with a real mutation and no proof has no kind in this
profile. No companion intent or pending-mutation kind ships in this commit. The
structural win that does justify kind-level mandatoriness is claim 1's deletion
asymmetry.

## Claim 4: vocabulary

Including `provider-receipt` does not restore "omit the proof table", but it
does restore a weak proof class that fully satisfies RKM02. At SPEC no scheme is
verified, so `provider-receipt` is the honest label for "counterparty said so",
and listing it is better than forcing producers to lie with `tee-quote`. The
graduated-strength problem is deferred to an unshipped conformance profile.

`finality_basis` is one claimed-durability axis and is coherent as producer
claim metadata, but there is no scheme/finality coherence matrix: `zk-receipt` +
`ledger-final`, `ledger-transaction` + `provider-acknowledged`, and
`provider-receipt` + `ledger-final` are all legal today.

## Claim 5: ontology version

Bump 1 to 2 is correct under the profile's own `version_bump_rule` for a
main-published profile gaining attribute values. Hygiene note: `PROFILE.toml`
and `api-snapshot-kind.toml` still carry `ontology_version = 1` while the
ontology and the new kind say 2.

## Claim 6: gaps

Missed gaps the initiator did not list:

1. `provenance.source_sha256` is a kind `required_field` but is unenforced by
   `validate_state_mutation.py`. A crafted document with no `[provenance]` at
   all passes Rust, Go, Python closure, and Python kind validation.
2. No scheme by finality coherence rules.
3. No companion kind for unproved mutations.
4. The "all three negatives fail provenance" claim is true for
   `validate_provenance.py`, not for primary `--mode provenance`.

## Verdict

**Blocker: RKM04 is a load-bearing hard invariant without a SPEC-normative byte
contract, and without primary enforcement.** Until the bound-tuple record form
is written next to SPEC 12.8 as normative text, not a TODO, no unconditional
approval.

Not the blocker, and holds under inspection: the deletion asymmetry is real in
all three implementations; the positive digests recompute independently; the
ontology bump is correct.
