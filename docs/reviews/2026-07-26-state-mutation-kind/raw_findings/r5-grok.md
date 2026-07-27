# Round 5, Grok: APPROVED (no blocker)

Independent design review of the conformance corpus on
`profile/state-mutation-kind` at HEAD `150600d`, under review `67dd095` and
`8869fed`. Scope: the corpus, not the validators, except where a case is
evidence something about them is wrong. Built both primaries from this
worktree and executed them.

```text
tools/dagtoml-validate-rs  (cargo build --release from this tree)
tools/dagtoml-validate-go  -> /tmp/dagtoml-validate-go-clean
python3 conformance/runner.py --rs ... --go ... --repo-root .
# result: 44 cases, CONFORMANCE PASSED
```

## Priority 1: mutation-test of the four fixes (acid test)

Each fix was reverted in a scratch copy under `/tmp/corpus-mut-*`, primaries
rebuilt, full corpus re-run.

| Reverted fix | Corpus | Red on | Mode |
|---|---|---|---|
| Empty-string vocabulary skip (rs `v.is_empty()` / go `v != ""`) | RED | `state-mutation/invalid/blank-vocabulary-tokens` | verdict: rs=0, go=0 (py still rejects) |
| RKC02 via `tableOf` instead of `hasKey` (Go only) | RED | `mutation-claim/invalid/array-proof` | verdict: go=0 |
| Silent `return [], []` for non-string `template_kind` (all three) | RED | `state-mutation/invalid/malformed-kind-selector` | verdict: rs=go=py=0 |
| Calendar range checks dropped from `is_rfc3339_utc` (all three) | RED | `state-mutation/invalid/impossible-timestamp` | verdict: rs=go=py=0 |

All four are verdict failures, not mere needle misses. That is the stronger
property: the corpus would still catch these if every sidecar were deleted.

Precision checks matching the initiator's parallel log:

- Empty-string-only mutation left `wrong-typed-proof-fields` green (sibling
  cases cover adjacent halves of one defect class).
- RKC02 `tableOf` mutation left `table-proof` green and turned only
  `array-proof` red (shape-sensitive fixture doing its job).
- Calendar mutation left `unicode-digit-timestamp` green (ASCII-shape vs
  calendar-meaning are separate).

**No fix this series produced escapes the corpus.** That was the main ask.

## Priority 2: needle discrimination

Executed self-match of every `error_contains` needle against all three
implementations after a clean Go rebuild: every needle hits on its own case.

Swap / cross-match (would sidecar A pass against document B's rejection on
all three impls?):

| Pair | Result | Judgment |
|---|---|---|
| `impossible-timestamp` vs `unicode-digit-timestamp` | discriminate (8869fed) | good |
| `blank-vocabulary-tokens` vs `wrong-typed-proof-fields` | discriminate (8869fed) | good |
| `array-proof` vs `table-proof` | both only `RKC02` | same defect class, different TOML shapes; intentional. Verdicts diverge under the real RKC02 regression (see P1). |
| `hollow-proof` (`RKM02` only) vs `required-pin-missing-proof` | hollow needles pass on required-pin | residual looseness |
| `hollow-proof` / `unbound-proof` vs claim RKC02 cases | single-token needles match incidental `RKM02`/`RKM04` mentions inside RKC02 prose | residual looseness |

The residual cases are weaker than the four the initiator fixed in `8869fed`,
but they are not the "literally interchangeable field-name only" failure mode.
`RKM02` and `RKM04` are defect-class identifiers. A hollow reversion that
accepts the document still fails on verdict. Tightening
`hollow-proof.expected.toml` and `unbound-proof.expected.toml` to include a
field path (e.g. `execution_proof.scheme is required` / the wrong
`binds_sha256` value) would be a good follow-up, not a withhold.

`required-pin-missing-proof.expected.toml` asserts `"SPEC §12.8.1"`. That
depends on the section symbol the initiator aligned in `67dd095`. It works
today. A harmless reword to `SPEC 12.8.1` (no `§`) would break CI. Acceptable
for a pin-resolution case that must name the closure layer, but brittle.
Prefer also pinning the phrase `pinned closure record` which all three already
emit.

`inlined-proof.expected.toml` asserts only `"not a permitted key"`. That is a
defect class (closed key set / RKM03), not a field name. Survives rewording of
the RKM03 tag as long as the key-set message remains. Not interchangeable with
other current cases.

## Priority 3: one reason per invalid case

Layer split (Python kind vs closure):

| Case | kind | closure | Notes |
|---|---|---|---|
| blank-vocabulary-tokens | reject | pass | two vocabulary defects (scheme + finality); sidecar pins scheme path + membership phrase |
| hollow-proof | reject | pass | three missing unpinned keys, all RKM02 |
| impossible-timestamp | reject | pass | single defect |
| inlined-proof | reject | pass | single defect |
| malformed-kind-selector | pass (not our kind) | reject | single closure defect; intended |
| required-pin-missing-proof | reject | reject | dual by construction: missing table fires RKM02 and two required pins. Sidecar pins the pin names + §12.8.1, so it is honest about the layer under test |
| unbound-proof | reject | pass | single defect |
| unicode-digit-timestamp | reject | pass | single defect |
| wrong-typed-proof-fields | reject | pass | three wrong-typed fields; sidecar pins scheme type phrase |
| array-proof / table-proof | reject | pass | single RKC02 |

`source_bytes = 416` on the corpus required-pin case (was 417): fixed. Corpus
cases that edit bound fields carry recomputed `binds_sha256` /
`closure_root` so RKM04/closure do not steal the failure.

Valid cases:

- `five-record-ledger-transaction` and `three-record-claim`: full kind +
  closure accept on all three.
- Escape hatches: kind validators report zero instances and exit 0; closure
  accepts the honest one-record source-hash root. They pass because scope
  declines to run, which is the SPEC §12 behaviour under guard, not a silent
  no-op bug.

## Priority 4: what the corpus does not cover

Hard invariants with no dedicated fixture:

| ID | Coverage | Notes |
|---|---|---|
| RKM01 | partial | required-pin covers missing required pins; no wrong-`closure_root` / wrong-digest stream case |
| RKM02 | yes | hollow, blank, wrong-typed, required-pin |
| RKM03 | yes | inlined-proof, timestamp grammars, wrong-typed locator |
| RKM04 | yes | unbound-proof |
| RKM05 | none | IJB resolution; kind introduces no entity prefixes. Untestable as a meaningful mutation-kind fixture without inventing foreign prefixes |
| RKM06 | **none** | scheme/finality coherence. Validators enforce it (probed
  `provider-receipt` + `ledger-final`: all three reject with RKM06). Simply
  missing from the corpus |
| RKC01 | none | three-record closure integrity for claims |
| RKC02 | yes | array-proof + table-proof |
| RKC03 | none | claim-side grammars (operation injection lives only under `examples/negative/`) |
| RKC04 | none | same IJB reduction as RKM05 |

From `raw_findings/` rather than the initiator summary: round-1
operation-injection (newline-forging `operation`) is still only under
`examples/negative/`, not the corpus. Round-2/3/4 blockers that became
code fixes all have corpus cases.

`examples/negative/` vs `conformance/cases/`: heavy overlap, already
drifting. Corpus cases use `source_bytes = 416`; several negatives still say
`417`, and some differ in scheme / `binds_sha256` / `closure_root`. That is a
**hazard**, not a documentation-versus-gate arrangement that is holding.
Defensible intent (docs vs gate) fails when the two copies encode different
documents. Prefer: make `examples/negative/` thin wrappers or delete the
mutation-kind negatives that the corpus now owns, keeping only cases the
corpus deliberately omits (operation-injection, no-proof if still wanted as
prose). Not a corpus correctness blocker; it is a maintenance debt.

## Priority 5: derived skip of `conformance/cases/*/invalid/`

`validators/validate_closure_root.py` (post-`67dd095`) skips any discover
target whose posix path starts with `conformance/cases/` and contains
`/invalid/`. Same path shape as the workflow's file-list builder at
`.github/workflows/validate.yml:363`.

What it can skip that is not an asserted-negative case: any future
`conformance/cases/<anything>/invalid/<file>.toml`, including a mistakenly
placed MUST-ACCEPT fixture. That is the intended structural rule: under
`invalid/` the runner demands reject. Risk is low if contributors follow the
layout.

Claim check: "matches what the Rust and Go discovery paths always did." The
skip is not inside `dagtoml-validate-rs` or `dagtoml-validate-go`. Those
binaries validate the paths they are given. The workflow pre-filters the
list for them. Python's `--discover` now applies the same shape. Behaviour is
aligned for the CI positive sweep; the comment at `validate.yml:382`
("skipped by the validator itself") is slightly overstated for the primaries.

Workflow per-fixture negatives: glob over `examples/negative/state-mutation-*.toml`
and `mutation-claim-*.toml`, with `malformed-kind-selector` excluded from the
kind-layer loop and asserted at closure. A file landing under
`examples/negative/` matching those globs is asserted to fail. That is correct
for that directory's contract. Vice versa: a fixture only under the corpus is
gated by the runner, not by that glob. Fine.

## Verdict

**Unconditional approval.**

The corpus does what round 4 required of it: shared fixtures, three
implementations, defect-class sidecars rather than exit codes alone, and the
acid test that reintroducing each of the four series fixes turns the named
case red. Residual needle tightness work and the RKM06 coverage gap are
follow-ups, not reasons to withhold. No invented blocker.

---

## Initiator note

This file was written into the worktree by the reviewer itself during the run,
not transcribed afterwards, which is why its formatting differs from the other
`raw_findings/` entries. Kept as returned.

Grok approved and graded the loose `"RKM02"` and `"RKM04"` needles a follow-up
rather than a withhold. **Codex graded the same observation a blocker and was
right.** Grok saw the looseness; Codex proved the consequence mechanically by
swapping the sidecar onto `array-proof` and watching it still pass. The
difference between noticing a weakness and demonstrating it decides severity,
and this is the clearest example in the series.

Grok's coverage finding was independently correct and is now fixed: RKM06 was
enforced in all three implementations with no fixture at all. It has one.

Grok's `examples/negative/` drift observation is accepted and recorded as open.
