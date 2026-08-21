# Round 7, Devin: NOT APPROVED

Gateway job `7820d299-3d10-45b1-94d5-95bde3f0b9ee`, 8503 bytes, 9m00s. Em
dashes normalized to commas per the repo writing convention.

**Devin found the blocker independently this round**, which is the correction
asked of it after rounds 5 and 6, where it confirmed what others had already
flagged and then asserted a false explanation rather than running it.

## Blocker

The membership gate fails open both ways: for a vocabulary in a seed but in no
ontology, and for an ontology vocabulary absent from the seed. Demonstrated by
renaming `requirement_kind` to `bogus_kind` at `postgres/seed.sql:169` only:

```
attribute_value_allowed membership.postgres:
  50 vocabularies, 34 non-backed, 33 with value rows
  OK, seed membership matches the ontology
COUNT-MIRROR OK, every surface agrees with reality.
```

An ontology vocabulary disappeared from `attribute_vocabulary`, a non-ontology
vocabulary appeared, the value rows still reference the old name, and the gate
passes. Devin also notes the loop cannot detect duplicate vocabulary names
across ontologies; it found none only because none exist today. It read all
three `schema.sql` files to confirm the last column is currently the backing
column in every engine, so the position-dependent parse works for the
checked-in seeds but would misparse an engine whose column order differed.

## What Devin verified as correct

- The sqlite baseline: every clause executed, including the postgres enum for
  each of the eight (naming the four cases where the type name differs from the
  vocabulary name) and zero `git log f9a37cf..HEAD -S` hits.
- Header numbers, recomputed from ontology and descriptor files rather than
  compared against each other.
- `7f1c853` comment-only; `2012d6a` alone green on the count-mirror gate.
- The eight seeded values, set-compared per engine, `diff=none` in all six.
- Explicitly flags one judgment claim it did NOT execute: that the baseline
  beats the postgres-only alternative.

## The surface nobody had run in seven rounds

Devin executed the `[verification.sqlite]` block from `MANIFEST.toml` in a
podman container, loading schema and seed into a real sqlite database:

```
podman exec sqlite-test-r7d sh -c 'sqlite3 /tmp/d.db < /tmp/schema.sql && sqlite3 /tmp/d.db < /tmp/seed.sql && echo OK'
OK
dagtoml_kind_descriptor         23
dagtoml_entity_kind_descriptor  27
dagtoml_relation_descriptor     31
dagtoml_attribute_vocabulary    50
dagtoml_attribute_value_allowed 152
```

That is the first execution of any `[verification]` block in this review
series. The seeds are not merely parseable, they load and produce the declared
counts. Devin did not run the neo4j block (needs the `apoc` plugin).
