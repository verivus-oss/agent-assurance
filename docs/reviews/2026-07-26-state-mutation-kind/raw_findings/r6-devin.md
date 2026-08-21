# Round 6, Devin: APPROVED (contains one false claim)

Returned text, reproduced as received. Em dashes normalized to commas per the
repo writing convention. Gateway job `edb9b4a7-2521-45c0-81dc-ddf35ae8209b`,
correlation `adacg-r6-devin`, 5081 bytes, 3m25s.

**Devin executed properly this round** (round 5's lesson held: dispatched with
`permissionMode: "dangerous"`, it cloned `/tmp/r6-devin`, built both primaries
and `dagtoml-rdf` from source, and ran the gates). Its mutation test on named
question 1 independently reproduces the initiator's result.

**But its answer to named question 5 is false, and it is the exact point Grok
made a blocker.** Devin wrote:

> `attribute_value_allowed` remained 144; that is expected because the new
> closed vocabulary values are promoted to engine enums rather than to the
> `attribute_value_allowed` table.

No enum exists for either vocabulary. `reference/database/postgres/schema.sql`
has no `CREATE TYPE` for `execution_proof_scheme` or `finality_basis`, and both
carry NULL in the enum-type column of their `attribute_vocabulary` rows
(`reference/database/postgres/seed.sql:229-230`), exactly like `witness_scheme`
and `attester_observed`, which ARE seeded. Devin asserted an explanation rather
than testing it, and the assertion happened to be the one that made a green gate
look correct. Recorded because it is the round-6 instance of the failure mode
this review series keeps hitting: a plausible reason accepted in place of a
check.

## What Devin executed

1. Built both primaries and `dagtoml-rdf` from source in `/tmp/r6-devin`.
2. `conformance/runner.py` passed 45 cases.
3. **Named question 1, executed.** Reverted `hasKey(doc, "execution_proof")` to
   `tableOf` at `tools/dagtoml-validate-go/main.go:3986`, rebuilt, reran:
   `array-proof.toml` exited 0 (accepted, wrong), `table-proof.toml` exited 1
   (rejected, right). Confirms the whitelisted collision is justified. Restored
   `hasKey` and rebuilt.
4. **Named question 2, executed.** `validate_closure_root.py --discover .` and
   `--discover "$(pwd)"` both passed at 91 files with identical exclusions.
5. **Named question 3, executed.** Both mutation-claim negatives fail
   `validate_provenance.py` (225 declared vs 224 actual), fail
   `validate_state_mutation.py` with RKC02, and pass `validate_closure_root.py`.
   Swept all 32 files under `examples/negative/`: all 18 carrying `[provenance]`
   fail. No other fixture violates the convention.
6. **Named question 4, read.** `profiles/com.verivus.runtime/PROFILE.toml`
   lines 97-105: `mutation-claim` pins only `mutation.authorization_sha256` and
   `mutation.effect_sha256`. Both fixtures carry identical values, so the shared
   `closure_root` is correct; RKC02 is a kind-layer invariant, not a closure pin.
7. **Named question 5, partly executed and partly wrong.**
   `check_attribute_values.py` passed and reported closed 123 == 123 and schema
   triples 1476 == 1476. The `attribute_value_allowed` explanation is false, see
   above.
8. **Unprompted checks.** `ruff check .`, `taplo lint` over 318 TOML files,
   `check_provenance_containment.sh`, `check_pin_resolution_guards.sh`,
   `check_safe_tools.sh`, `check_manifest_drift.sh`, and
   `validate_state_mutation.py` on both positives. All passed.
9. **`_tmp-fake.capture`.** `grep -R` found no references anywhere in the tree.
10. **Named question 6.** Considers the repo-level negative-gate matrix
    correctly deferred: a process improvement, not a blocker.

Devin considered the standing open items out of scope and not PR-blocking.
