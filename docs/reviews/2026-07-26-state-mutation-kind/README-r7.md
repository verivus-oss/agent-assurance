# Round 7: NOT APPROVED, three of four, one convergent blocker

Dispatched 2026-07-27 against `35f3b93`, with CI green at that SHA. Four
reviewers, all four executed.

| Reviewer | Verdict | Basis |
|---|---|---|
| Codex | **NOT APPROVED** | membership gate fails open on ontology identity and value sets |
| Grok | **NOT APPROVED** | same, plus backing is an unverified self-assertion |
| Devin | **NOT APPROVED** | same, found independently by renaming a core vocabulary |
| Mistral | APPROVED | asserted "no fail-open found"; falsified three times over |

Three reviewers converged on one blocker from three different directions, and
the initiator reproduced two of the exploits directly. This is the first round
of the series where the majority found the same real defect independently.

## The blocker

`2012d6a` added a membership check whose stated purpose was that counts
agreeing is necessary and not sufficient. The check itself is still
insufficient, in four ways:

1. **It is seed-driven, not ontology-driven.** It iterates seed vocabulary
   names and skips any name absent from the ontology
   (`check_attribute_values.py:468-471`). Nothing requires a closed non-backed
   ONTOLOGY vocabulary to appear in the seed at all. Rename it in the seeds and
   the gate is green while the real name has zero enforcement anywhere.
   Found by Grok (`execution_proof_scheme`), Devin (`requirement_kind`) and
   Codex (`execution_proof_schmee`), independently.
2. **The backing column is trusted without verification.** A non-NULL value is
   read as "a native type enforces this", with no check that the named type or
   CHECK exists. Setting it to `fake_enum`, deleting the value rows and
   lowering the counts is green. This is precisely the round-6
   "promoted to engine enums" excuse, the one Devin and Mistral asserted and
   Grok disproved, now expressible as data the gate accepts.
3. **It compares cardinality, not value identity.** `zk-receipt` to
   `zk-receipt-TYPO` is green (Grok). Codex loaded a typo'd value into a live
   postgres and got 152 rows and a corrupted vocabulary.
4. **It cannot detect duplicate vocabulary names across ontologies** (Devin).
   None exist today; the hole is structural.

The initiator separately found a fifth, milder one before any verdict arrived
and recorded it in `initiator-failopen-r7.md`: a vocabulary row reformatted
across two lines makes the position-dependent parse read `'structural'` as the
backing column. Grok and Devin both checked the parse against the current seeds
and correctly reported no present disagreement, which is consistent: that one
requires a reformat, theirs do not.

## What the round confirmed as correct

The branch DATA is right. This is worth stating plainly because the blocker is
about the gate, not the seeds:

- All three engines were loaded live, by three different reviewers, in
  containers and via the duckdb tools. Every engine yields 23 / 27 / 31 / 50 /
  152, and both vocabulary value sets match the ontology exactly.
- Devin executed the `[verification.sqlite]` block from `MANIFEST.toml`, and
  Codex loaded postgres, duckdb AND neo4j. These are the surfaces flagged as
  never-exercised in the round-7 request. They have now been exercised.
- The sqlite baseline is honest. Four independent verifications of all eight
  clauses, including the "predates this branch" clause, which every reviewer
  ran rather than repeated.
- Both round-6 blockers really are fixed. The regression proof reproduces for
  Grok and Codex: old gate green on `2d5809e`, new gate gives the six named
  failures.
- `7f1c853` is comment-only and `2012d6a` alone leaves the tree green, so the
  commit split holds.

## Two residual defects, smaller than the blocker

- `7f1c853` claims every count-bearing comment was rederived. Two were missed:
  `duckdb/seed.sql:70` says `relation_descriptor (30)` against 31 rows, and
  `postgres/seed.sql:168` labels a 5-row subsection `Core (9)`. Found by Grok,
  confirmed by the initiator.
- The graph mirror is stale against the manifest: neo4j loads, but its
  registry is 15 / 23 / 31 against expectations of 23 / 27 / 31. Codex found
  this and deliberately declined to make it a second blocker because no graph
  file changed on this branch. That restraint is the correct handling of a real
  but out-of-scope defect, and it is now a named standing item rather than an
  unknown.

## What approval requires

Agreed almost word for word by Codex and Grok, and implied by Devin:

- membership must be **ontology-driven**: every closed, non-backed ontology
  vocabulary must be required under its real name;
- unknown seed names, missing ontology names and duplicate ontology names must
  all be rejected rather than skipped;
- a non-NULL backing column must be **verified** against a real `CREATE TYPE`
  or CHECK in that engine's schema, and treated as unverified (therefore
  requiring value rows) when it cannot be;
- comparison must be on the exact value **set**, not the count.

## Method note

The three reviewers who found the defect all did the same thing: they changed
something and re-ran the gate. The one who did not, read the code and
constructed an explanation for why it was sound. That is the third consecutive
round in which that distinction predicted who was right, and it now holds
across six reviewers and three rounds. It is the single most reliable signal in
this series.
