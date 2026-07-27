# The round-7 membership gate fails open on a reformatted row

Initiator: Claude (Opus 5), Werner Kasselman's session, 2026-07-27, found while
round 7 was in flight against `35f3b93`. Recorded here rather than fixed
immediately, so the four reviewers keep reviewing the commit they were given.

Round 7's named question 1 asks the reviewers whether the new membership check
fails open anywhere. It does, and the initiator found it by attacking its own
fix rather than by explaining why it was sound. This file is the answer to that
question, written before their verdicts arrive so it cannot be a
reconstruction.

## The defect

`derive_seed_vocab_surfaces` decides whether a vocabulary is backed by a native
type by taking the **last comma-separated token of the row's first line**. Every
row in the seeds today happens to be a single line, so this works. Reformat one
row across two lines, which is legal SQL and semantically identical, and the
parser reads the wrong column:

```
    ('execution_proof_scheme', NULL, ARRAY['state-mutation'], 'structural',
     FALSE, NULL, 'profile:com.verivus.runtime', NULL),
```

The last token of line one is `'structural'`, which is not `NULL`, so the
vocabulary is recorded as **backed**. Backed vocabularies are expected to be
absent from `attribute_value_allowed`, so the check then requires exactly the
wrong thing: it demands the values NOT be there.

Confirmed directly:

```
execution_proof_scheme -> backed = True   (correct answer: False)
finality_basis         -> backed = False  (correct answer: False)
```

## It hides the exact defect it was written to catch

In a scratch copy: reformat that one row, delete `execution_proof_scheme`'s four
value rows from the postgres seed, and set the declared counts to the resulting
148 the way a careless author would after deleting rows. The gate goes fully
green (output reproduced with its em dashes normalized to commas, per the repo
writing convention):

```
COUNT-MIRROR OK, every surface agrees with reality.
OK, manifest matches ontology + every count-mirror surface agrees
```

`execution_proof_scheme` has zero seeded values in postgres, which is Grok's
round-6 blocker reintroduced, and the membership section reports
`OK, seed membership matches the ontology`.

The one visible tell is a count that nobody reads: the summary line says
`50 vocabularies, 33 non-backed` where the correct figure is 34. The gate prints
the number that would give it away and does not check it.

## Why the earlier regression proof did not catch this

The proof run against `2d5809e` reformatted nothing. It deleted rows from
correctly-formatted seeds, so every vocabulary parsed correctly and the check
fired as designed. A test that only perturbs the data cannot find a defect in
the parser. The membership check was verified against the defect it was written
for and not against variations of the file it reads.

## Severity, honestly

Today the branch is correct: every row in all three seeds is on one line, so the
gate is accurate at `35f3b93` and both round-6 blockers really are fixed. This
is a robustness defect in a new gate, not a live data defect. But the whole
argument for `2012d6a` is that counts agreeing is not sufficient and the gate
must compare by name, and a by-name check that a whitespace change can silently
disable does not carry that argument.

## The fix, for after round 7 closes

Parse the `attribute_vocabulary` block by SQL row rather than by line: join
lines until parenthesis balance returns to zero, then split the row's columns
respecting quotes and `ARRAY[...]` / `[...]` brackets. Then either of these
should also hold, because a single misparse should not be able to pass quietly:

- assert that the number of non-backed vocabularies matches an independently
  derived figure, so `33` versus `34` is itself a failure;
- treat a vocabulary whose backing column cannot be parsed unambiguously as an
  error rather than as either answer.

The second is the one that matters. The current code has no representation for
"I could not tell", and picks `backed = True`, which is the permissive answer.
A gate that guesses should guess in the direction that fails.
