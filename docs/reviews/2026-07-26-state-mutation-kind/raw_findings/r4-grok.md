# Round 4, Grok: APPROVED (no blocker)

Condensed from the returned text; the full verdict ran to 13 KB. Em dashes
normalized to commas per the repo writing convention. Gateway job
`aba8571d-76fc-410f-b64a-33e2d3e03eb5`.

Grok was the only round-4 reviewer to approve, and the only one to identify why
the `template_kind` behaviour is partly BY DESIGN. That reasoning is what
narrowed the fix.

## Priority 1: round-3 fix verified by execution

The RKC02 fix holds against every shape tried: the shipped
`mutation-claim-array-proof.toml`, root `execution_proof = 1`, `= true`,
`= "hollow"`, `= []`, a `[[execution_proof]]` array-of-tables header, and
dotted `execution_proof.*` keys (which parse as a table). All fail py/rs/go.
`hasKey` at `tools/dagtoml-validate-go/main.go:80-87`, used at `main.go:3971`.

Required-table diagnostics now distinguish present-but-wrong-typed from absent
for true root-level keys. Note Grok initially saw the old "missing" message and
debugged it to a TOML artefact: a bare `mutation = 1` written after a table
header nests INTO that table rather than sitting at the root. The fix is
correct; the first test was wrong.

All eleven mutation negatives fail all three under `--mode mutation-kinds`;
both minimal positives pass all three in both modes.

## The `template_kind` attack, and why Grok did not call it a blocker

Grok reproduced the same behaviour the initiator and Codex did, including the
honest re-root to the one-record closure, and reached a different conclusion:

> The same pass appears with `template_kind = "process-artefact"` (a
> non-reserved string) and a hollow body. That path is **normative**, not a
> bug: SPEC 12 (`spec.md:972-985`) deliberately puts non-reserved / absent
> `template_kind` outside conformance scope, and producers are told to use that
> escape when they do not want pin/kind obligations.
>
> So a non-string `template_kind` is a **SPEC 2.3 type gap** (`template_kind`
> "is a string") that `validateMeta` never checks. Effectively it lands on the
> same escape hatch as a non-reserved string or absence.
>
> It is **not** a false accept of a document that still claims
> `template_kind = "state-mutation"`. Consumers that key on the string never
> see those kinds. The hollow-proof structural property in the design record
> holds when the kind string is correct (control: string TK + hollow + re-root
> still fails required proof pins).

Grok listed the non-string case as follow-up item 5: "Optional: `validateMeta`
reject non-string `template_kind` (SPEC 2.3). Improves hygiene; does not change
the reserved-kind security story, because non-reserved strings remain a
deliberate escape."

Grok found no further typed-accessor accept path inside documents that declare
a correct kind string: nested wrong types fail closed (digest ints and arrays,
scheme int, `performed_at` datetime, empty, whitespace, empty
`[execution_proof]` on a claim).

## Reproducible residual: Python crashes on a table-typed vocabulary value

> Python still does `scheme not in schemes` / `finality not in finalities`
> without a type guard (`validate_state_mutation.py:327`, `:333`). A
> table-typed `scheme` or `finality_basis` raises
> `TypeError: unhashable type: 'dict'` and exits 1. Primaries reject cleanly.
> Fail-closed, but undignified.

Confirmed by the initiator and fixed.

## Priority 2: converging or structurally defect-prone

> Converging on accept-path severity; structurally still fragile on process.

Grok's table: round 2 all three accepted a blank scheme; round 3 Go only
accepted a claim with a full proof array; round 4 no further accept path in the
same class under a correct `template_kind`. "Each round found a real bypass
inside the previous fix, and each was rarer and narrower."

On whether a shared corpus would have caught the earlier rounds:

> **R2 blank/wrong-typed scheme:** yes, if cases assert all three binaries
> against `invalid/` and require reject. Ad hoc `validate.yml` loops only cover
> what someone remembers to list.
> **R3 array-of-tables proof on claim:** yes, if `mutation-claim/invalid/`
> existed. The absence of any mutation-claim conformance tree is why RKC02
> lived only in two ad hoc negatives until R3.
> **R3 diagnostic honesty for `mutation = 1`:** only if cases assert message
> classes or structured defect codes, not bare exit codes.

> What would end the loop is not another review round: a shared corpus that
> every implementation is forced to agree on, plus (ideally) one declarative
> encoding of kind invariants instead of three prose ports.

## Priority 3: merge readiness

Must fix before land: **none found.** Follow-ups: conformance corpus for both
kinds; the Python vocabulary type guard; CI enumerated lists; vocabulary
compile-time versus ontology-loaded drift; optionally the non-string
`template_kind` rule. Acceptable to carry: leap-second policy, the 12.8.2
no-normalization decision, `provider-receipt` retention.

Grok also flagged stale bookkeeping: `design-record.md:3` still says the change
is "NOT reviewed" after three rounds.

## Priority 4: what nobody has asked

1. Promotion claim-to-mutation has never been RUN end to end, only asserted in
   prose.
2. No normative consumer algorithm exists: when to refuse `provider-receipt`,
   how to rank scheme against finality, how tiers bind. The tiers under
   `profiles/agent-assurance/tiers/` do not reference these kinds at all.
3. SPEC 13 capability envelope and abstraction class are descriptor-only and
   have never been checked as a merge gate for instances.
