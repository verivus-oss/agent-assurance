# Design record: the `state-mutation` kind

Created 2026-07-26. Status: **proposal on a branch, FIVE review rounds complete,
NOT merged.**
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

## Round 3 review outcome and what changed

Three verdicts, not four: the Gemini job died on a gateway transport timeout
with zero output (`raw_findings/r3-gemini.md`). All three that returned withheld
approval.

**Codex and Grok independently named the same blocker, and it reproduced.**
Round 2 closed the absent/blank/wrong-typed conflation for SCALAR fields. The
same conflation survived one structural level up, in the typed TABLE accessors,
and RKC02 was enforced through one.

`tableOf` answers false both for an absent key and for a key holding a
non-table. That is the right answer when a table is REQUIRED and the wrong one
when a field is FORBIDDEN. So a `mutation-claim` carrying
`execution_proof = [{ scheme = "provider-receipt", ... }]`, a fully populated
provider receipt in an array of tables rather than a table, passed the Go
primary in both auto and explicit mode while Python and Rust rejected it. The
document is closure-valid, so nothing else caught it either. Codex found the
array-of-tables variant, which is materially worse than the bare scalar Grok
started from: the proof material is real and complete, and only its TOML shape
differs.

Fixed with `hasKey` in Go, so RKC02 asks whether the field is PRESENT rather
than whether it is well-formed. Regression fixture
`examples/negative/mutation-claim-array-proof.toml`, deliberately closure-valid,
asserted in CI against all three.

**Mistral found the same class applied to the REQUIRED tables**, where the
consequence is only a dishonest diagnostic: `mutation = 1` was reported as
"missing required `[mutation]` table" by all three. Accept/reject parity held,
so this was not a bypass, and Mistral scoped it correctly as such. It was still
worth fixing, because SPEC 12.8.2 now says in as many words that a
present-but-wrong-typed element MUST NOT be treated as absent, and the
implementations were contradicting the repo's own new rule. All three now
distinguish the two cases at both table sites.

The pattern across rounds 2 and 3 is one bug wearing three costumes: a typed
accessor that collapses "absent" and "present but wrong shape" into a single
skip path. It was closed for proof scalars in round 2, for the forbidden proof
key and both required tables in round 3.

**What the board confirmed by execution rather than assertion.** Grok
reproduced the round-2 fixes as fixed, including whitespace-only scheme and
finality. Grok and Mistral both differential-tested the new calendar checks
across roughly 25 cases (year 0000, month and day 00, February 29 in 1900,
2000, 2100 and 2024, second 60 and 61, hour 24, minute 60, fractional-digit
boundaries) and found no divergence, no overflow and no panic. Both endorsed
the unconditional `second <= 60` reading of RFC3339 5.6 rather than
IERS-table awareness, which would put versioned external data inside a byte
contract. All three re-ran the CI closure sweep and got 90 files.

**The SPEC 12.8.2 normalization decision survived, with a caveat.** Grok and
Mistral both independently endorsed requiring that NO normalization is applied.
Grok tested the escape hatch and reported that constraining a grammar to one
encoding works for closed ASCII token vocabularies but for a free-form
`target_id` requires forbidding raw non-ASCII or mandating percent-encoding,
which is feasible but harsh. The caveat: Gemini raised the original objection
and, because its job timed out, never replied to the answer.

## Round 4 review outcome: a split board, and the adjudication

Codex, Grok and Devin. Devin is new to the series and reviewed for the first
time. **Two withheld approval and one approved**, and they disagreed about the
same behaviour, which makes the adjudication the substance of this round.

All three, plus the initiator independently before the verdicts returned
(`initiator-kind-dispatch-r4.md`), reached the same observation. Take the
hollow-proof negative, set `meta.template_kind = 1` or delete it, honestly
re-root to the SPEC 12.8 one-record source-hash closure, and the document
passes every layer in all three implementations. Kind validators dispatch on
the selector and correctly say "not my kind"; closure pin resolution read the
malformed selector as ABSENT and returned no pins and no errors.

- **Codex: blocker.** Reproduced by execution, with the same fallback root the
  initiator computed. Remedy asked for: reject absent OR non-string.
- **Devin: blocker.** Found it by reading the source, having been unable to run
  `cargo`, `go` or `git` at all. Same remedy: reject missing or non-string.
- **Grok: approved.** Reproduced the same behaviour and argued it is partly BY
  DESIGN, citing SPEC 12 at `spec.md:972-985`.

**Grok is right about the half that matters for the remedy, and the two
blocker-callers are wrong about it.** SPEC 12 says, in one sentence:

> Producers that want a file outside the rule's scope MUST give it a
> non-spec-reserved `template_kind` (or no `template_kind` at all).

So absence is a ratified escape from conformance scope, exactly like a
non-reserved string such as `"review-bundle"`. Rejecting absence, as both
blockers asked, would break behaviour the spec guarantees. Grok also showed the
control that settles the security question: with a CORRECT kind string, a
hollow re-rooted proof still fails the required pins, so this was never a false
accept of a document claiming to be a `state-mutation`.

**But Grok is wrong to leave it entirely.** SPEC 2.3 says `template_kind` IS a
string. A value that is present but not a string is neither of the two ratified
escapes. It is malformed, and reading it as absent silently drops every pinned
closure record. That is the pin-free fall-through all three implementations'
own docstrings say does not exist.

So the fix is **narrower than two reviewers demanded and broader than the third
allowed**: a present-but-non-string `template_kind` is now a closure-layer
error in all three; absent and non-reserved-string remain legal and are
asserted as such in the verification log so a future change cannot quietly
remove the escape hatch.

This is the first round where the board split, and the split was productive:
the approving reviewer supplied the reasoning that made the other two's remedy
wrong, and the blocking reviewers supplied a defect the approving one was
willing to file as optional hygiene.

**Also fixed, found by Grok:** `scheme not in schemes` has no type guard, so a
table-typed `scheme` or `finality_basis` raised
`TypeError: unhashable type: 'dict'`. It exits 1, so it failed closed, but a
traceback is not a defect report and it hid which invariant fired. The
primaries already handled this cleanly through the round-2 three-state
accessor.

**What the board confirmed:** the round-3 RKC02 fix holds against every shape
Grok tried, including `[[execution_proof]]` array-of-tables headers and dotted
`execution_proof.*` keys. Codex re-ran the full suite and the CI-shaped closure
sweep at 90 files. Grok found no further typed-accessor accept path inside
documents that declare a correct kind string.

**On whether this is converging.** Codex says structurally defect-prone; Grok
says converging on accept-path severity but process-fragile. They agree
completely on the remedy, and so does Devin: a shared `conformance/cases/`
corpus that every implementation is driven from, rather than ad hoc negatives
listed by hand in `validate.yml`. Grok assessed it case by case and concluded
it would have caught rounds 2 and 3, but only if cases assert defect classes
rather than bare exit codes, since round 3's diagnostic defect had correct
exit codes throughout. That is now the top open item.

## The conformance corpus, built after round 4

All three round-4 reviewers named the same remedy, so it was built rather than
reviewed again. It is `conformance/cases/{state-mutation,mutation-claim}/`,
driven by the pre-existing `conformance/runner.py` through all three
implementations.

**Building it immediately found that CI was red for a second, separate
reason.** `conformance/runner.py` treats a case directory with no
`PY_VALIDATORS` entry as a hard failure, and
`conformance/cases/state-mutation/` was added back in `cff386b` without one.
So the conformance step had been failing since that commit, through four
review rounds, and nobody ran it, including the initiator and including
reviewers who reported running "the CI-shaped" checks. The lesson is narrow
and worth stating: "I ran the CI checks" meant, in every round, a hand-picked
subset of the workflow.

That is the same enumerated-list hazard Grok and Mistral flagged in round 3,
and it had now caused two separate CI failures on this branch. Both directions
are fixed: `PY_VALIDATORS` gains both kinds, and the repo-wide closure sweep no
longer enumerates `conformance/cases/<kind>/invalid` exclusions at all but
derives them from the path shape, matching what the Rust and Go discovery paths
always did. Verified by adding an unregistered invalid tree and confirming the
sweep stays green.

**The corpus asserts defect classes, which was Grok's specific condition.**
Every invalid case carries an `error_contains` sidecar. Grok's argument for
this was concrete: an exit-code corpus would have passed round 3's diagnostic
defect, where all three implementations rejected the document and two named the
wrong reason. The mechanism was negative-controlled by planting an unmatchable
substring and confirming the runner fails all three implementations on it,
because a corpus that silently asserts nothing is worse than no corpus.

**Two valid cases are regression guards, not examples.**
`escape-hatch-absent-template-kind` and `escape-hatch-non-reserved-kind` are
asserted MUST-ACCEPT precisely because two round-4 reviewers asked for that
behaviour to be rejected. SPEC §12 ratifies both escapes in one sentence. If a
later change makes those cases fail, the change is wrong, and the corpus now
says so mechanically rather than in a design document nobody re-reads.

One pre-existing case was also wrong: `required-pin-missing-proof` declared
`source_bytes = 417` against a 416-byte capture, so it failed for two reasons
and proved neither.

## Round 5 review outcome: the corpus reviewed as an artefact

Codex, Grok, Devin. Gemini timed out for the third consecutive round, this time
with a 15 minute idle timeout set, dying at the same 5m08s as before, so the
ceiling is inside the gateway adapter and not caller-controllable. **The board
has been three reviewers since round 3** and the record should say so.

**Two approved, one blocked, and the blocker was right.**

All three reviewers plus the initiator independently ran the acid test and got
the same result: reverting each of the four fixes this series produced turns
the corpus red, on the case that names that defect, as a VERDICT failure rather
than a needle miss. Sibling precision held in every run. That is the strongest
evidence in the series that something works, four independent reproductions of
the same table.

**Codex's blocker: a needle that matched without discriminating.**
`hollow-proof.expected.toml` asserted only `"RKM02"`, and the RKC02 diagnostic
contains that string incidentally, since it names the invariants a proved
record must face ("so that RKM02, RKM04 and RKM06 apply to it"). Codex proved
the consequence by swapping the sidecar onto `array-proof`, which still passed.

Grok saw the same looseness and graded it a follow-up. Codex demonstrated it
and graded it a blocker. **Codex was right, and the difference between noticing
a weakness and demonstrating it is what decided the severity.** This is the
sharpest instance in five rounds of why the review asks for constructed
evidence rather than reasoning.

Running the full cross-product rather than Codex's single pair showed the
problem was worse than reported: **four** sidecars failed to discriminate.
`unbound-proof`'s bare `"RKM04"` matched four other cases, because both
timestamp fixtures cite RKM04 while explaining the field is bound.

Three fixes followed, only the first of which Codex asked for:

1. `hollow-proof` and `unbound-proof` now pin the fields and the recomputation
   phrase that only they report.
2. **`error_not_contains` was added to the runner.** `hollow-proof` cannot be
   separated from `required-pin-missing-proof` by any presence-only needle,
   because the latter's output is a strict SUPERSET of the former's. It now
   asserts the closure layer stayed silent, which is the case's actual claim.
3. **`conformance/discrimination.py` runs the whole cross-product in CI.** One
   reviewer found one instance by guessing a pair; the general check finds all
   of them and prevents recurrence. Negative-controlled by restoring the bare
   needle and confirming it reports all three collisions.

**Grok's coverage finding, independently correct:** RKM06 was enforced in all
three implementations with no fixture at all. It has one now
(`scheme-finality-incoherent`), which matters because RKM06 is the mitigation
that kept `provider-receipt` in the ontology after round 1, where a reviewer
wanted the scheme removed. Without that invariant tested, the round-1 objection
stands unanswered.

**Devin executed this round** (round 4's dispatch had refused it `cargo`, `go`
and `git`) and worked in a clean scratch worktree, which is the right method.
Its approval was still too generous: it swap-tested exactly the two pairs the
review request named as already fixed and found them fixed. Codex tested a pair
the request did not name. Confirming what someone else already flagged is the
weakest form of the same technique.

### What is still open

- **The round-4 fix and the corpus itself are unreviewed**, which is the
  standing that produced the round-2, round-3 and round-4 blockers in turn. The
  corpus is the higher risk of the two: it is the artefact future changes will
  be judged against, so a wrong assertion in it is worse than a wrong line of
  validator code. The negative control proves the mechanism fires, not that
  every needle is the right needle.
- **The corpus does not yet cover the other kinds.** `api-snapshot` has cases
  but no sidecars on most of them, and `traceability`, `review-readiness`,
  `kind-descriptor` and `profile-descriptor` have no corpus at all. The
  enumerated-list fix is repo-wide, but the defect-class discipline is so far
  only applied to the two mutation kinds.
- **Nothing forces a new kind to arrive with conformance cases.** Registering a
  kind directory is now required (the runner fails without a `PY_VALIDATORS`
  entry), but a kind with no directory at all is still invisible to the corpus,
  which is exactly how `mutation-claim` reached round 3 untested.
- **Two reviewers have now been unable to execute anything.** Mistral in round
  2 (whose blocker did not reproduce) and Devin in round 4 (whose did). Devin
  ran with gateway `permissionMode: "auto"`, which refuses `cargo`, `go` and
  `git`. Either dispatch it with `dangerous` or treat it as a static analyst by
  design, but record which.
- **Gemini has not reviewed round 3, round 4, or the SPEC 12.8.2 additions it
  objected to.** Its round-3 job timed out with no output. The normalization
  decision it contested now has two independent endorsements and no reply from
  the objector.
- **Never run end to end:** promotion from `mutation-claim` to `state-mutation`
  is asserted in prose and has never been executed as a scripted operation
  through all three validators (Grok, round 4).
- **No normative consumer algorithm.** The kinds say what a producer must
  write and what a validator must check, but not how a consumer decides whether
  a `provider-receipt` is good enough, how scheme ranks against finality, or
  how any of this binds to the tiers under `profiles/agent-assurance/tiers/`,
  which do not reference these kinds at all (Grok, round 4).
- The `provider-receipt` retention decision stands against one reviewer's
  round-1 blocker, with the same reviewer reversing position in round 2 and
  arguing FOR retention. It remains the operator's to reverse.
- Vocabulary source still differs between reference and primaries: Python loads
  the closed vocabularies from the profile ontology at run time, both primaries
  compile them in. A profile that extends `execution_proof_scheme` or
  `finality_basis` will be accepted by the reference and rejected by the
  primaries until they are rebuilt. Recorded in RKM02's `enforcement_boundary`.
  Grok named the absence of a CI lock diffing the two as a live drift hazard.
- **Enumerated lists in CI remain a structural hazard.** Round 2 found the
  closure sweep's `--exclude` list red because a new directory was not added to
  it. Grok and Mistral both flagged that the kind-descriptor list at
  `validate.yml:391` and the closure exclude list have the same shape: the
  primaries discover `conformance/cases/*/invalid` generically while the Python
  steps enumerate. Adding a kind will silently break a sweep again. Not fixed,
  because it is repo-wide rather than specific to these kinds.
