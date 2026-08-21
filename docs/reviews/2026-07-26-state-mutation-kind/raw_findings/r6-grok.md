# Round 6, Grok: NOT APPROVED

Returned text, reproduced as received. Em dashes normalized to commas per the
repo writing convention. Gateway job `faf1d6e4-85cc-43e1-ab3e-59ab56a1760b`,
correlation `adacg-r6-grok`, 8745 bytes, 4m51s.

**Grok's blocker is correct.** The initiator reproduced it independently and
confirmed it, including refuting Devin's contradicting explanation. See
`initiator-seed-gap-r6.md` for that work.

## Blocker as stated

Incomplete seed emission for the two new closed vocabularies:
`execution_proof_scheme` and `finality_basis` have rows in
`attribute_vocabulary` but their eight allowed values are missing from
`attribute_value_allowed` across all three engine seeds. The count-mirror
surfaces agree with each other at 144 because the gate compares seed to
manifest, not seed to ontology.

- Files: `reference/database/postgres/seed.sql` ~398-403, sqlite ~327-332,
  duckdb ~311-316; `reference/database/MANIFEST.toml` lines 283, 314, 324;
  `tools/dagtoml-duckdb/src/main.rs` EXPECTED_COUNTS;
  `tools/dagtoml-duckdb-go/main.go` expectedCounts.
- Class: the same class as defect 1 (incomplete count-mirror propagation), but
  on the value-row surface rather than the vocabulary-row surface. The prior
  `com.verivus.runtime` closed non-enum vocabularies (`witness_scheme`,
  `attester_observed`) seed their values; the two new ones do not.
- Why the gate is green: `validators/check_attribute_values.py` checks
  `expected_seed_counts.attribute_value_allowed` against actual seed INSERT row
  counts (both 144). It does not require every non-enum closed ontology
  vocabulary to appear in that table. Ontology `attribute_values_closed` (123)
  is a different surface.

Grok's required fix: append eight `attribute_value_allowed` rows to all three
seeds mirroring the witness block, bump `attribute_value_allowed` 144 to 152 on
the three MANIFEST `expected_seed_counts` and the Rust and Go hardcodes, then
re-run `validators/check_manifest_drift.sh`.

## Named questions, Grok's answers

1. **Discrimination allowlist: claim is TRUE (executed).** Baseline: both
   `array-proof` and `table-proof` reject with identical RKC02 text. Reverting
   only the RKC02 check from `hasKey` to `tableOf` and rebuilding Go:
   `array-proof` passes (exit 0, false green), `table-proof` still fails.
   The exemption is earned by verdict discrimination, not message
   discrimination. Grok restored `main.go` afterwards.
2. **Path-form skip `c197de4`: fix is real (executed).** `is_conformance_invalid`
   matches resolved path components, not a relative string prefix. Relative,
   absolute and `../invalid` forms all match; 91 files either way.
3. **Provenance negatives: class fixed (executed).** Both negatives: capture
   224, declared 225, `validate_provenance.py` FAIL, `validate_closure_root.py`
   PASS, kind layer FAIL with RKC02. 3d: every `examples/negative/*` that has a
   real `[provenance]` table fails the gate. Other "deliberately wrong" comments
   match real capture sizes (416 to 417, 620 to 621, 224 to 225).
4. **Identical `closure_root`: correct (executed plus read).** Both negatives
   pin the same three digests over the same capture. `execution_proof.*` is not
   pinned for `mutation-claim` because a stream cannot pin absence.
5. **123 and 1476 confirmed independently; 144 is the hole.**
   `check_attribute_values.py` compares `expected_seed_counts` to actual seed
   SQL row counts, not to ontology closed totals, which is why 144 can stay
   green while incomplete. RDF correctly embeds the new `owl:oneOf` values; the
   SQL seeds do not list them. That asymmetry is the blocker.
6. **Class of defect 4: correctly deferred (read plus reasoned).**

## Gates Grok ran at `2d5809e`

Built from the tree only. `conformance/runner.py` PASSED 45 cases;
`conformance/discrimination.py` PASSED 12 sidecars; `check_manifest_drift.sh`
PASSED (and, Grok notes, does not see the seed/ontology value gap);
`check_provenance_containment.sh` PASSED; `check_pin_resolution_guards.sh`
PASSED; `check_safe_tools.sh` PASSED; `ruff check .` PASSED; closure discover
relative and absolute PASSED at 91 files.

Not run by Grok: `golangci-lint` (not installed on the host it used) and any
network check of the CI run IDs.

## Grok's calibration note, reproduced

"Round 5: I approved while Codex found a real non-discrimination hole. This
round I treated 'gate green' as insufficient and recomputed seed contents
against the ontology and the prior `com.verivus.runtime` pattern. The
discrimination fix and provenance fix hold; the post-round-5 reference
propagation does not fully complete the surface it names."
