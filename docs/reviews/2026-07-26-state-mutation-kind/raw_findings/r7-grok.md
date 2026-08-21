# Round 7, Grok: NOT APPROVED

Gateway job `65be37bb-a5fd-4c38-b19d-c947076456dd`, 12912 bytes, 7m22s. Em
dashes normalized to commas per the repo writing convention.

**Blocker upheld.** The initiator reproduced both exploits before accepting it.

## Blocker: the membership gate still fails open for the original defect class

Two live mutations on the HEAD gate both exit 0 with
`OK, seed membership matches the ontology` on all three engines.

1. **Ontology-side name never required.** Membership iterates seed
   `attribute_vocabulary` names and does `if declared is None: continue` for
   seed-only names, so it never requires each closed non-backed ONTOLOGY
   vocabulary to appear under its real name. Renaming `execution_proof_scheme`
   to `execution_proof_schem` in all three seeds (vocabulary row and value rows)
   leaves counts at 50/152 and membership green, while the ontology still
   declares four values for the real name and the seed has zero rows under it.
2. **Backing is a self-assertion.** A non-NULL last column is treated as native
   enforcement with no check that `schema.sql` defines that type or CHECK.
   Setting the backing to `fake_enum`, dropping the four value rows, and
   lowering the expected counts 152 to 148 is green. `CREATE TYPE fake_enum`
   does not exist. Grok's words: "that is the round-6 'promoted to enums'
   claim, now encoded in a column the gate trusts without verification."
3. **Cardinality, not value identity.** `zk-receipt` to `zk-receipt-TYPO` stays
   green.

Grok's required conditions for approval: membership must be ontology-driven
(every closed non-backed ontology vocabulary required under its real name), and
a non-NULL backing column must be checked against a real schema enum or CHECK,
or value rows required when the backing cannot be verified. Value-set equality
is named as the next hardening step.

## Residual stale headers, falsifying a claim in `7f1c853`

`7f1c853` says every count-bearing comment was rederived. Two were not, both
confirmed by the initiator:

- `reference/database/duckdb/seed.sql:70`: `relation_descriptor (30)` while the
  INSERT has 31 rows and the next comment says 31 correctly.
- `reference/database/postgres/seed.sql:168`: `Core (9)` labels a subsection
  containing 5 rows. The core layer total is 12, split across three sub-groups.

## What Grok verified as correct

- The sqlite baseline is honest. All eight clauses executed: NULL backing, zero
  value rows, no CHECK in `sqlite/schema.sql`, postgres enum present for each
  (some under different type names: `gate_verdict`, `override_rule_op`,
  `clock_policy`, `network_policy`), zero commits in `f9a37cf..HEAD`, all eight
  originating at `eccdcab`. Grok notes the baseline is "soft": it is not
  re-validated each run, so a baselined name that later gains a partial seed
  would not fail.
- The instance fix and the regression proof are real: six failures on the
  untouched `2d5809e` tree with only the new validator swapped in.
- The eight seeded values match the ontology exactly in all three engines.
- `7f1c853` is comment-only; `2012d6a` alone is green.
- Header totals recompute correctly (23 / 27 / 31 / 50 / 152).

## Surfaces Grok exercised that nobody had

Ran the duckdb tools live: `dagtoml-duckdb` and `dagtoml-duckdb-go` both report
`counts match expected (23 / 27 / 31 / 50 / 152)`, and live SQL confirms
`attribute_value_allowed n=152`, `execution_proof_scheme=4`, `finality_basis=4`,
backing NULL for both.

On the graph: read only, no container. Notes `schema.cypher` is incomplete by
its own admission (15 KindDescriptors against 23, 23 EntityKinds against 27) and
carries a stale `expected_node_counts (now 21/27/31 at HEAD)` comment.

Grok also names `SQLITE_MEMBERSHIP_BASELINE` as the same structural hazard it
flagged in round 4 for enumerated CI lists, and prefers deriving baseline
candidates over hardcoding them.
