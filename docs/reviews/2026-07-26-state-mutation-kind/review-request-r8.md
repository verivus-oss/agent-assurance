# Round 8 review request: the hardened membership gate

- **Branch:** `profile/state-mutation-kind`
- **Head under review:** `80aabd5`
- **Previously reviewed head:** `35f3b93` (round 7)
- **PR base:** `origin/main` = `f9a37cf`. 24 commits.
- **CI:** `validate` and `no-ai-attribution` both `success` at `80aabd5`. CI
  FAILED at `39e3bab` on the `typos` step; see below.

Round 7 ended **NOT APPROVED**, three of four. Codex, Grok and Devin each
independently defeated the membership check added in `2012d6a`. Three commits
since:

```
11bc358 fix: the membership gate is ontology-driven, verifies backings, compares sets
e1922c8 fix: the three count comments 7f1c853 missed
39e3bab review: round-7 record, one convergent blocker from three reviewers
80aabd5 fix: verify backings against real SQL, not commented-out SQL; typos gate
```

## Two defects found AFTER round 7's fixes, before you saw them

Both are in `80aabd5`, and both are disclosed here rather than left for you to
discover, because pretending the first version was sound is exactly the failure
mode this series keeps punishing.

**The schema parse read commented-out SQL.** `11bc358` claimed a backing is
verified rather than believed. It was not. Appending
`-- CREATE TYPE fake_enum AS ENUM (...);` to `postgres/schema.sql` and claiming
`fake_enum` let all four real value rows be deleted with the gate green. Block
comments too. That is Grok's round-7 blocker one level up: verification reduced
to assertion with one extra step. `_strip_sql_comments` now removes line and
block comments, quote-aware, before the parse. A side effect worth knowing:
sqlite's native-construct count fell from 9 to 8, because one of the nine was
itself inside a comment, so the gate had been counting a construct that does
not exist.

**CI failed at `39e3bab` on `typos`**, over the variable name `unparseable`
(the tool wants `unparsable`). The local suite was green because nothing
invokes `typos` outside CI and the initiator had never run it. That is the
fourth time on this branch that an existing, never-run-locally gate caught
something only after a push, and the third distinct such gate after manifest
drift, provenance negatives and golangci-lint. It is now installed at the
pinned version and runs before every push.

## What you defeated, and what was done about it

| Your exploit | Now |
|---|---|
| rename a vocabulary in all three seeds (Grok, Codex) | fails from both directions: the ontology name has no row, and the renamed row is declared by no ontology |
| rename a core vocabulary in one seed (Devin) | same matched pair for `requirement_kind` / `bogus_kind` |
| claim `fake_enum` as a backing, delete the values (Grok) | fails: no `CREATE TYPE` or CHECK in that engine's schema defines it |
| typo one value, count unchanged (Grok, Codex) | fails: value set differs, naming both directions |
| duplicate vocabulary name across ontologies (Devin) | reported instead of collapsing last-one-wins |
| reformat a row across two lines (initiator) | rows are parsed by SQL row, not by line |

The four conditions as you specified them:

1. **Ontology-driven.** The loop iterates ontologies. Every declared vocabulary
   must have an `attribute_vocabulary` row under its real name. Seed rows and
   value rows naming an undeclared vocabulary are reported too.
2. **Backings verified, not believed.** `derive_schema_native_constructs`
   parses `CREATE TYPE <name> AS ENUM (...)` for postgres and duckdb, and
   `<col> TEXT CHECK (<col> ... IN (...))` for sqlite. A claimed backing no
   schema defines fails. A backing that does not admit every ontology value
   fails. A vocabulary carrying value rows despite a verified backing fails.
3. **Exact value sets**, named in both directions, plus a separate duplicate-row
   check so N rows for N-1 values cannot pass.
4. **Duplicate ontology names** reported rather than silently collapsed.

Two hardenings nobody asked for: rows are joined until bracket balance returns
to zero and split on top-level commas only; and a row that does not parse into
8 columns raises rather than guessing, because the old code defaulted to
`backed = True`, the permissive answer.

Grok's soft-baseline caveat is addressed: a `SQLITE_MEMBERSHIP_BASELINE` entry
is skipped only while it has **zero** value rows, so one that acquires a partial
seed is checked normally and the baseline cannot quietly widen.

`e1922c8` fixes the two stale comments Grok named plus a third the initiator
found by auditing every two-to-four-digit number in every seed comment against
derived truth (`postgres/seed.sql:117`, "17 of the 30", actually 31).

## Verification the initiator ran, at `39e3bab`

Each round-7 exploit was re-run against the new gate and is caught with a
specific message; the original round-6 defect still produces exactly six
failures against an untouched `2d5809e` with only this validator swapped in.
Local suite green: manifest drift, conformance (45 cases), discrimination (12
sidecars), provenance containment, pin guards, safe-tools, ruff 0.15.15, taplo.

A design question checked before committing to the strongest form: every backed
vocabulary's claimed construct exists **and** its value set covers the
ontology's, in all three engines, today. That is why the covering check is a
hard failure rather than an advisory.

## Named questions

1. **Defeat it again.** You defeated the previous version three ways in one
   round. The same standard applies: construct a state where a closed ontology
   vocabulary ends up unenforced in some engine while this gate stays green.
   Attack the schema parse in particular, which is new and is now load-bearing:
   a `CREATE TYPE` inside a comment or a string, a CHECK whose column name
   differs from the constraint's target, an enum defined in a file the parser
   does not read, an engine that enforces a closed set some third way.
2. **Is the covering rule right?** A backing must admit every ontology value
   (`declared <= native[backing]`). It is deliberately not equality, because
   `likelihood` and `impact` share `risk_level`, and `smoke.decision` and
   `status` share `smoke_decision`. Is subset the correct relation, or does it
   permit a real defect? Name one if so.
3. **Fail-closed parsing.** `derive_seed_vocab_surfaces` raises on a row that
   does not yield 8 columns. Is raising right, or does it make the gate brittle
   against a legitimate future seed shape? Note the alternative considered and
   rejected: defaulting to unbacked, which would demand value rows for anything
   unparseable.
4. **Is the baseline still honest?** Same eight names, now re-checked on every
   run rather than blanket-skipped. Verify the tightening actually works: give a
   baselined name a partial seed and confirm it fails.
5. **Did `e1922c8` finish the job this time?** `7f1c853` claimed completeness
   and was wrong twice. This one claims an exhaustive audit. Falsify it.
6. **The standing items, unchanged.** The corpus covers only the two mutation
   kinds; nothing forces a new kind to arrive with cases; promotion has never
   been executed end to end; no normative consumer algorithm nor tier binding;
   vocabulary source differs between the reference and the primaries with no CI
   lock; enumerated lists in CI remain a structural hazard, now including
   `SQLITE_MEMBERSHIP_BASELINE`; nothing asserts a negative fixture fails every
   gate it is subject to. Codex additionally found the neo4j mirror stale
   against the manifest (15/23/31 against 23/27/31) and correctly scoped it out,
   since no graph file changed on this branch. Say if you think any of these now
   blocks a PR.

Disclosed and unchanged: mixed authorship, and the branch is not
bisectable-green (`cff386b` through `4a48069` fail CI).

## How to review

Read the files yourself. Verify every claim above by executing it. Build both
primaries from the tree; do not use any prebuilt binary you find on disk.

```sh
git clone <repo> r8 && cd r8 && git checkout 39e3bab
(cd tools/dagtoml-validate-rs && cargo build --release --locked)
(cd tools/dagtoml-validate-go && go build -o /tmp/dagtoml-validate-go ./...)
cargo build --release --locked --manifest-path tools/dagtoml-rdf/Cargo.toml
bash validators/check_manifest_drift.sh
git show 11bc358; git show e1922c8
```

Approve **only** on the basis of what you inspected. The signal across rounds
5, 6 and 7 is unambiguous: every reviewer who changed something and re-ran the
gate found a real defect, and every reviewer who read the code and explained
why it was sound did not. If you find yourself writing an explanation, run a
command instead. Either give **unconditional approval**, or name **one concrete
blocker** with a file path, a line range, and a reproduction.
