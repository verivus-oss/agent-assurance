# Round 7 review request: the two round-6 blocker fixes

- **Branch:** `profile/state-mutation-kind`
- **Head under review:** `35f3b93`
- **Previously reviewed head:** `2d5809e` (round 6)
- **PR base:** `origin/main` = `f9a37cf`. 20 commits.

Round 6 ended **NOT APPROVED**: Codex and Grok each named a distinct, real
blocker; Devin and Mistral approved, and both were wrong on the specific point
Grok blocked on. Three commits since:

```
2012d6a fix: seed the two new closed vocabularies, and gate membership not just counts
7f1c853 fix: the seed headers describe the seeds again
35f3b93 review: round-6 record, two blockers and the evidence behind them
```

## What each blocker was, and what was done

**Blocker 1 (Grok).** `execution_proof_scheme` and `finality_basis` had rows in
`attribute_vocabulary` and none of their eight values in
`attribute_value_allowed`, in all three engine seeds. Every declared count
agreed at 144, so no gate saw it.

Fixed in `2012d6a`: eight rows per seed, and `144 -> 152` on the five surfaces
the gate names. The gate was re-run **between** adding the rows and bumping the
counts, so the five surfaces were enumerated by the gate rather than assumed.

**The class fix is the part to attack.** `validators/check_attribute_values.py`
now compares the seeds to the ontology **by name**, per engine: a vocabulary
with no native backing and a non-empty value list must appear in
`attribute_value_allowed` with exactly its declared number of values; one with
a backing must not appear at all.

**Blocker 2 (Codex).** All three seed headers described counts that had been
wrong since `301a322`, while claiming to be "verified against ontology files"
and "CI-gated". Fixed in `7f1c853`, which is a comment-only diff. The rot was
wider than the two numbers Codex named, so every count-bearing comment in all
three seeds was rederived; see the commit message for the full list.

## Verification the initiator ran, at `35f3b93`

| Gate | Result |
|---|---|
| `check_manifest_drift.sh` (with the new membership check) | PASSED |
| `conformance/runner.py` | PASSED, 45 cases |
| `conformance/discrimination.py` | PASSED, 12 sidecars over 12 cases |
| `check_provenance_containment.sh` | PASSED |
| `check_pin_resolution_guards.sh` | PASSED |
| `check_safe_tools.sh` | PASSED |
| `ruff check .` (0.15.15) | PASSED |
| `golangci-lint run ./...` (2.12.2) x 4 modules | PASSED |
| `taplo lint` | PASSED |
| `cargo build --release --locked` (dagtoml-duckdb) | PASSED |
| `go build ./...` (dagtoml-duckdb-go) | PASSED |

**Regression proof for the class fix.** Exported the untouched tree at
`2d5809e`, swapped in only the new `check_attribute_values.py`, and ran the
gate. Where the old gate passed, the new one fails with exactly six membership
failures:

```
1. postgres: execution_proof_scheme (4 values declared, 0 seeded) is absent from attribute_value_allowed
2. postgres: finality_basis (4 values declared, 0 seeded) is absent from attribute_value_allowed
3-6. the same pair in sqlite and duckdb
```

## Named questions

1. **Is the membership rule the right rule?** It encodes what
   `postgres/seed.sql:232` says about itself: `attribute_value_allowed` carries
   values for vocabularies with no native backing. The backing is read from the
   last column of each `attribute_vocabulary` row. Attack the parse: a row whose
   last column is not what the code thinks it is, an engine whose column order
   differs, a vocabulary present in a seed but absent from every ontology, a
   name appearing in two ontologies. Does the check fail open anywhere?
2. **Is the sqlite baseline honest, or is it an exemption that hides a defect?**
   `SQLITE_MEMBERSHIP_BASELINE` lists eight vocabularies (`severity_tier`,
   `runtime_kind`, `adapter_ref_syntax`, `adapter_id_derivation`,
   `gate_decision_verdict`, `override_rule_operator`, `runtime_clock_policy`,
   `runtime_network_policy`). The claim justifying it: each carries NULL in
   sqlite's `backing_check_constraint`, has no value rows, and is named by no
   CHECK in `sqlite/schema.sql`, so nothing in that mirror enforces it; postgres
   backs all eight with enum types; and all of this predates this branch.
   **Verify every clause of that claim.** If any of the eight is in fact
   enforced somewhere, the baseline is hiding a real gap rather than recording
   one. If any of them was introduced by this branch, the baseline is
   laundering this branch's own defect, and that is a blocker.

   The initiator ran the "predates this branch" clause rather than asserting
   it, which is the round-6 lesson applied: `git log f9a37cf..HEAD -S<name> --
   reference/database/sqlite/seed.sql` returns **0 commits for all eight**, and
   `severity_tier` and `runtime_kind` both trace to `eccdcab` (2026-05-27,
   "Mint agent-assurance spec"), two months before this branch. Falsify that if
   you can; do not simply repeat it.
3. **Is the baseline the right mechanism at all?** It fails the branch open for
   eight names in exchange for gating the other 42. The alternative was to
   restrict the membership check to postgres and duckdb. Argue for the better
   one. If you think the eight should simply be fixed here, say so and say why
   it is in scope for a branch about mutation kinds.
4. **Are the rederived header numbers right?** `7f1c853` changed roughly two
   dozen numbers across three files. Recompute each independently rather than
   checking that they agree with each other. Particular attention to the
   per-layer breakdowns, which are the numbers most likely to be wrong in a way
   no gate can see, since nothing parses these comments: this is the same
   surface that was silently false for months.
5. **Does the split hold?** `7f1c853` is claimed to be comment-only. Verify
   (`git show 7f1c853 | grep -E '^[+-]' | grep -v '^[+-]\s*--'` should be empty
   apart from the file headers). And confirm `2012d6a` alone leaves the tree
   green, so the two commits are independently correct rather than only
   correct together.
6. **The eight seeded values themselves.** Do they match the ontology exactly,
   in content and in count, for both vocabularies, in all three engines? A
   typo'd value is precisely the sort of thing a count gate cannot see, which is
   the failure this whole exchange has been about.
7. **Anything the initiator and four reviewers have now missed six times.** The
   standing pattern across this branch: every real defect since round 5 was
   found by running a gate that already existed, not by reading the diff. Two
   remain unexercised locally by anyone: the graph (`neo4j`) and the three
   engine `[verification]` blocks, which require containers. Nobody has ever run
   them. If you can, run one.

## Standing open items, unchanged from round 6

Not in scope for approval, but say so if you think one blocks a PR: the corpus
covers only the two mutation kinds; nothing forces a new kind to arrive with
conformance cases; promotion `mutation-claim -> state-mutation` has never been
executed end to end; there is no normative consumer algorithm and no binding to
`profiles/agent-assurance/tiers/`; vocabulary source differs between the
reference and the primaries with no CI lock; enumerated lists in CI remain a
structural hazard; and nothing asserts that a negative fixture fails every gate
it is nominally subject to.

Also unchanged and disclosed: mixed authorship, and the branch is not
bisectable-green (`cff386b` through `4a48069` fail CI).

## How to review

Read the files yourself. Verify every claim above against the code and executed
commands. **Do not accept this document as evidence for anything.** Build both
primaries from the tree; do not use any prebuilt binary you find on disk.

```sh
git clone <repo> r7 && cd r7 && git checkout 35f3b93
(cd tools/dagtoml-validate-rs && cargo build --release --locked)
(cd tools/dagtoml-validate-go && go build -o /tmp/dagtoml-validate-go ./...)
cargo build --release --locked --manifest-path tools/dagtoml-rdf/Cargo.toml
bash validators/check_manifest_drift.sh
git show 2012d6a; git show 7f1c853
```

Approve **only** on the basis of what you inspected. Do not approve on intent,
on plan-compliance, or on "should be fixed". Round 6 saw two approvals resting
on an assertion nobody executed; if you find yourself explaining why something
is fine, run it instead. Either give **unconditional approval**, or name **one
concrete blocker** with a file path, a line range, and a reproduction.
