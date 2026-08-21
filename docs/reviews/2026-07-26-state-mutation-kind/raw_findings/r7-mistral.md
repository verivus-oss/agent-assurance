# Round 7, Mistral: APPROVED (wrong for the third round running)

Gateway job `d8b5a9e3-fbc7-4c08-a428-ffb0fc0bdfc3`, 6694 bytes, 3m46s. Em
dashes normalized to commas per the repo writing convention.

Mistral executed real commands again, which is the improvement asked of it
after round 2. But its two load-bearing conclusions are both false, and both
were falsified by reviewers who mutated the tree instead of reading it.

## Where it was wrong

**"No fail-open found."** Three other reviewers each found one independently,
and the initiator reproduced two of them. Mistral came within one step of it:
it noticed that "vocabularies present in seed but absent from ontology are
silently skipped (line 470-471)" and then dismissed the finding because
"enumeration shows zero such cases". That is the exact hole Grok, Codex and
Devin each drove a mutation through. A structural gap is not closed by the
observation that nothing currently occupies it.

**"All header numbers in postgres/seed.sql, sqlite/seed.sql, and
duckdb/seed.sql are correct."** Two are not: `duckdb/seed.sql:70` says
`relation_descriptor (30)` against 31 rows, and `postgres/seed.sql:168` labels a
5-row subsection `Core (9)`. Both confirmed by the initiator.

## Where it was right

The sqlite baseline verification is sound and independently executed, clause by
clause, matching Grok, Codex, Devin and the initiator. The eight seeded values
were set-compared per engine. The split checks and the `2012d6a`-alone check
were run. It was explicit about the one thing it could not execute (the
container-backed `[verification]` blocks and neo4j), which is the right way to
report a gap.

## The pattern, recorded because it is now three rounds old

Round 5: approved, missed the non-discriminating sidecar Codex caught. Round 6:
approved, asserted the "different surfaces" explanation Grok disproved by
running it, and miscounted the negative fixtures 16 against 18. Round 7:
approved, asserted "no fail-open" against three independent counterexamples.

Each time the method is the same: read the code, construct an explanation for
why it is sound, report the explanation as a finding. The three reviewers who
found real defects all did the same different thing, which was to change
something and re-run the gate.
