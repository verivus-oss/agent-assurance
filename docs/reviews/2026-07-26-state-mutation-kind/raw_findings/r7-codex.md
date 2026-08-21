# Round 7, Codex: NOT APPROVED

Gateway job `c55780cf-fa6a-4f5f-8b33-2fe451522230`, 315 KB transcript, 11m03s.
Provider session `019fa547-fb55-7192-9fb7-0d7a5ec82b52`. Em dashes normalized
to commas per the repo writing convention.

Third consecutive round in which Codex named a real blocker.

## Blocker

The new membership gate is still count-based and fails open on ontology
identity and value-set mismatches. `derive_ontology_vocab_values` stores only a
value COUNT, not the declared values. The loop iterates seed names, silently
skips an unknown seed vocabulary at `declared is None: continue`
(`check_attribute_values.py:468-471`), and never detects an ontology vocabulary
absent from the seed.

Two scratch mutations, both green:

```
# One value typo, known vocabulary:
execution_proof_scheme: ledger-transaction -> ledger-transactoin
count-mirror gate: OK        exit=0

# Rename the vocabulary to execution_proof_schmee, retaining four rows
# including the typo:
count-mirror gate: OK        exit=0
```

Codex then loaded the mutated seed into a live postgres container to show the
corruption is real rather than a parsing artefact:

```
INSERT 0 23 / 0 27 / 0 31 / 0 50 / 0 152
execution_proof_schmee=ledger-transactoin,provider-receipt,tee-quote,zk-receipt
```

Its required conditions: reject unknown seed names, missing ontology names,
duplicate ontology names, and compare each non-native vocabulary's exact seeded
value SET against the ontology set.

Codex's summary of the situation: "the actual head data is correct ... the
failure is that CI does not preserve this correctness."

## What Codex verified as correct

- All three engines loaded live, both vocabulary sets exact:
  `execution_proof_scheme=ledger-transaction,provider-receipt,tee-quote,zk-receipt`
  and `finality_basis=ledger-confirmed,ledger-final,none,provider-acknowledged`.
- Header totals confirmed by independently loaded SQL counts (23/27/31/50/152),
  and postgres confirmed the vocabulary layer split 12 / 27 / 4 / 3 / 4.
- The regression proof reproduces: old gate green on `2d5809e`, new gate gives
  the six named failures.
- The sqlite baseline: all eight clauses executed, zero `git log` hits, each
  originating in `eccdcab`, which is an ancestor of the base. Codex calls the
  baseline reasonable for this branch, with the caveat that it should not
  exempt future exact-set checking forever.
- `7f1c853` comment-only. At `2012d6a`: 45 conformance cases, 12 discrimination
  sidecars, manifest drift, provenance containment, pin guards, safe-tools and
  Taplo all pass.

## The graph surface, run for the first time

Codex loaded neo4j, the one surface no one has executed in seven rounds. It
loads successfully, but the documented illustrative registry is
`15 KindDescriptor / 23 EntityKind / 31 RelationPredicate` against manifest
expectations of `23/27/31`. Codex deliberately did NOT raise this as a second
blocker, on the grounds that no graph file changed between `f9a37cf` and head,
so it is a pre-existing non-normative gap rather than something this branch
introduced. That restraint is worth recording: it is the correct handling of a
real defect that is out of scope.

Read rather than executed: the GitHub CI run statuses and the commit-message
rationale. Codex confirms it modified no shared-worktree file and removed its
review containers.
