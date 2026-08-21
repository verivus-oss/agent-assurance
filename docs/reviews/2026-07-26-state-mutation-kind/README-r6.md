# Round 6: NOT APPROVED, two confirmed blockers

Dispatched 2026-07-27 against `2d5809e`, the pre-PR gate. Four reviewers, all
four returned a verdict, all four executed.

| Reviewer | Verdict | Basis |
|---|---|---|
| Codex | **NOT APPROVED** | stale count headers in all three reference SQL seeds |
| Grok | **NOT APPROVED** | eight missing `attribute_value_allowed` rows in all three seeds |
| Devin | APPROVED | executed properly, but its answer to Q5 is false |
| Mistral | APPROVED | executed, but repeats the same false Q5 assertion and miscounts Q3 |

Both blockers were reproduced independently by the initiator before being
accepted. Both live in `301a322`. Both are the same defect class as the
manifest-drift defect `301a322` was written to fix, one surface deeper. Neither
is caught by any gate, which is why CI is green at this SHA.

## Blocker 1 (Grok): the seed value rows

`execution_proof_scheme` and `finality_basis` have rows in
`attribute_vocabulary` but none of their eight values in
`attribute_value_allowed`, in postgres, sqlite and duckdb alike.

The seed states its own rule at `postgres/seed.sql:232`: the table holds values
for **non-enum-backed** vocabularies, because enum-backed ones are enforced by
the enum type. Across all 50 vocabularies, 16 are enum-backed and none of them
is seeded, 34 are not enum-backed and all but three are seeded. The three are
`license` (extensible with zero declared values, legitimately absent) and the
two this branch added.

Devin and Mistral both asserted the absence was expected because the values were
"promoted to engine enums". No `CREATE TYPE` exists for either, and both carry
NULL in the enum column at `postgres/seed.sql:229-230`, exactly like
`witness_scheme` and `attester_observed`, which are seeded.

Full working in `initiator-seed-gap-r6.md`, including a wrong cut that nearly
refuted the blocker.

## Blocker 2 (Codex): the seed headers

`postgres/seed.sql:10-11` says "Counts (verified against ontology files; matches
MANIFEST.toml)" then "21 template kinds"; the data and manifest say 23. Line 26
says 48 attribute vocabularies against an actual 50. `sqlite/seed.sql:9` makes
the stronger claim "CI-gated by validators/check_attribute_values.py; drift
fails". Nothing parses those headers.

The residue is wider than the two headline numbers: `postgres:31`
(`kind_descriptor (20 rows)`), `postgres:161` (`attribute_vocabulary (46 rows)`),
`sqlite:20`, `sqlite:118`, `duckdb:107`, and `sqlite:14`
(`144 attribute_value_allowed rows`), which blocker 1 will change again.

## What the round confirmed rather than broke

Reproduced independently by the initiator, and by three or more reviewers each:

- The `ALLOWED_COLLISIONS` exemption in `conformance/discrimination.py:37` is
  **earned**. Mutating only the RKC02 site from `hasKey` to `tableOf` reddens
  `array-proof` and leaves `table-proof` green, which is the stated claim. Five
  independent reproductions this round.
- `c197de4` is a general fix: `is_conformance_invalid` matches resolved path
  components, and relative, absolute and `../` forms all behave identically.
- `16d1729` fixed the class as well as the instance: all 18 `examples/negative/`
  fixtures carrying a `[provenance]` table are rejected by
  `validate_provenance.py`, and no other fixture carries a false
  "deliberately wrong" comment.
- The shared `closure_root` on the two mutation-claim negatives is correct.
  Both pin identical values for all three pinned records, and `PROFILE.toml:93-96`
  explains that RKC02 must be kind-layer because a closure stream can pin
  presence but never absence.
- `attribute_values_closed = 123` and RDF `schema = 1476` are both correct.
  The committed `schema.ttl` is byte-identical to a fresh regeneration.
- `golangci-lint` 2.12.2 reports 0 issues across all four Go modules. Codex
  installed it itself after finding it absent, and is the only reviewer that ran
  it.

## Method notes for round 7

- Devin and Mistral both approved while asserting, untested, the exact
  proposition Grok disproved by testing. An approval that rests on an
  explanation nobody ran is worth less than a blocker that rests on a command
  somebody ran. Round 7 should name that assertion explicitly and require it be
  executed.
- Mistral's job reported zero stdout and no provider activity for nine minutes
  before completing in one burst. Do not read a silent Mistral job as dead.
- Gemini was not dispatched this round; it has failed to return a verdict in
  rounds 3, 4 and 5, twice at exactly 5m08s regardless of `idleTimeoutMs`.
