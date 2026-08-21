# Round 5, Codex: NOT APPROVED

Final verdict message, reproduced as received. Em dashes normalized to commas
per the repo writing convention. Gateway job
`dee4efdb-3623-45e4-a3da-8a512de0c3f8`, 517 KB transcript.

**Codex was the only reviewer to name this a blocker, and it was right.**

## Finding

The corpus has one blocker: `hollow-proof.expected.toml` does not discriminate.
It asserts only `"RKM02"` at
`conformance/cases/state-mutation/invalid/hollow-proof.expected.toml:7`, but the
RKC02 claim-with-proof diagnostic also contains `RKM02` incidentally at
`validators/validate_state_mutation.py:287`. I swapped
`array-proof.expected.toml` and `hollow-proof.expected.toml` in a scratch tree:
`array-proof` still passed with the hollow sidecar, while `hollow-proof` failed
with the RKC02 sidecar. That means the hollow sidecar can bless a different
defect class.

## Acid tests

Clean baseline: built Rust and Go from this worktree, then
`conformance/runner.py` passed all 44 cases.

- Fix 1, blank and wrong-typed vocabulary tokens: red on
  `blank-vocabulary-tokens.toml` and `wrong-typed-proof-fields.toml`, verdict
  mismatches for Rust and Go.
- Fix 2, Go RKC02 by shape: red on `mutation-claim/invalid/array-proof.toml`,
  Go verdict mismatch.
- Fix 3, malformed kind selector: red on `malformed-kind-selector.toml`,
  verdict mismatches for Rust, Go, and Python. The absent and non-reserved
  valid escape hatches stayed green.
- Fix 4, calendar validity: red on `impossible-timestamp.toml`, verdict
  mismatches for all three.

The acid test coverage is real. The remaining blocker is the
non-discriminating sidecar.

BLOCKER: NON_DISCRIMINATING_HOLLOW_PROOF_NEEDLE at
`conformance/cases/state-mutation/invalid/hollow-proof.expected.toml:7`.

---

## Initiator note

Accepted, reproduced, and generalized. The swap Codex describes is exactly
reproducible: the RKC02 message reads "so that RKM02, RKM04 and RKM06 apply to
it", so it contains all three invariant names as prose.

Running the full cross-product rather than the single pair Codex tried found
the problem was **worse than reported**: four sidecars failed to discriminate,
not one. `unbound-proof`'s bare `"RKM04"` matched four other cases, because
both timestamp cases also cite RKM04 while explaining that the field is bound.

Fixed, plus two structural consequences:

1. `error_not_contains` was added to the runner. `hollow-proof` could not be
   separated from `required-pin-missing-proof` by any presence-only needle,
   because the latter's output is a strict SUPERSET of the former's. It now
   asserts the closure layer stayed silent, which is the actual claim of the
   case.
2. `conformance/discrimination.py` now runs the whole cross-product in CI, so
   this class cannot recur silently. Negative-controlled by restoring the bare
   `"RKM02"` needle and confirming it reports all three collisions.

Codex ran into two tool-level obstacles worth recording: its sandbox refused
`rm -rf` when setting up scratch trees, and one `apply_patch` failed to match.
It worked around both. Neither affected the finding.
