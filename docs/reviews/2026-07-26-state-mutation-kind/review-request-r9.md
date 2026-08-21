# Round 9 review request: a backing must be wired, and must match exactly

- **Branch:** `profile/state-mutation-kind`, code under review **`b2693e1`**
- **Previously reviewed:** `80aabd5` (round 8)
- **PR base:** `origin/main` = `f9a37cf`
- **Corrective-program spec:** `verification-report-r9.txt`, committed beside
  this file. It is real command output, not prose. Grade the branch against it,
  and re-run anything in it you do not trust.

Round 8 ended **NOT APPROVED**, three of four. Codex, Grok and Devin each
defeated `80aabd5`, from four directions. Every one was reproduced by the
initiator before being accepted, and every one is now caught.

## What you defeated, and what changed

| Your attack | Who | Now caught with |
|---|---|---|
| a real `CREATE TYPE fake_enum` that **no column uses** | Grok | "defined but referenced by no column, so it enforces nothing" |
| `SELECT $$CREATE TYPE fake_enum ...$$;`, a string, not DDL | Codex, Devin, Grok | "which no CREATE TYPE or CHECK ... defines" |
| sqlite `CHECK (likelihood IS NULL OR impact IN (...))` | Devin | same, the CHECK no longer counts for `likelihood` |
| widen `risk_level` with `'catastrophic'` | Grok, Devin | "the engine ... admits ['catastrophic'] that no ontology declares" |

Codex settled the dollar-quote case beyond argument by loading the mutated
schema into a real PostgreSQL 16 container: `fake_enum|0|false`. The type does
not exist.

Devin's case was this file's own regex: the backreference in
`(\w+)\s+TEXT\s+CHECK\s*\(\s*\1` matches `likelihood TEXT CHECK (likelihood`,
then `[^)]*?IN\s*\((.*?)\)` grabs an `IN` list belonging to another column.

Four changes in `b2693e1`:

1. `_strip_dollar_quoted` blanks `$$...$$` and `$tag$...$tag$` before parsing.
2. An enum type counts only if its identifier appears outside its own
   `CREATE TYPE` statement, meaning some column is declared with it.
3. A sqlite CHECK counts only when its `IN` constrains the column the CHECK
   belongs to, matched with balanced parens instead of a regex that wanders.
4. The relation is now **equality**, not subset. Checked first: equality
   already holds for all 40 backed vocabularies across the three engines, so it
   costs nothing today and closes the super-enum.

## What the use-site check found immediately, and it is bigger than expected

The eight vocabularies previously baselined as sqlite-only gaps are unenforced
in **postgres and duckdb as well**. Their enum types are defined and referenced
by no column. `severity_tier` appears exactly once in `postgres/schema.sql`, on
its own `CREATE TYPE` line; contrast `priority_level`, used by a real column at
line 228. `git log f9a37cf..HEAD -S<name>` returns 0 commits for all eight in
both `seed.sql` and `schema.sql`.

`SQLITE_MEMBERSHIP_BASELINE` is renamed `UNENFORCED_VOCABULARY_BASELINE` and
applies to every engine. Still a baseline, not a green light: every entry prints
on every run naming the unused type, and it applies only while the vocabulary is
fully unenforced and unseeded.

## Named questions

1. **Defeat it again.** Five rounds running, the reviewer who mutated and re-ran
   found a real defect. Attack the use-site test specifically: it is a textual
   "identifier appears outside its own definition" test, not a parse of column
   definitions. Can you satisfy it without wiring anything? A mention in a
   `COMMENT ON`, a string, a different DDL statement, an identifier that is a
   substring of another. Also attack `_strip_dollar_quoted` (nested tags,
   unterminated tags) and `_balanced` (parens inside string literals).
2. **Is equality right now?** It closed the super-enum. Does it break anything
   legitimate, for instance a shared enum that intentionally spans two
   vocabularies with different declared sets? None exists today; say if one
   should be allowed to.
3. **Is the widened baseline honest?** Verify all eight are genuinely unenforced
   in all three mirrors and genuinely pre-existing. If any one of them IS wired
   somewhere, the baseline is hiding a live gap. If any was introduced by this
   branch, it is laundering, and that is a blocker.
4. **Grok's outstanding falsification.** `postgres/seed.sql:13` still says
   `31 relation rows (26 core + 5 contract-namespaced variants)` while only 3
   `contract:` predicates exist. The initiator confirmed this and has NOT fixed
   it, because the right fix is unclear: is the intended split 28+3, or are two
   more predicates meant to be contract-namespaced? Decide, or say it is out of
   scope. Grok also found `postgres/schema.sql` comments were never audited at
   all (15 against 23, 23 against 27, 30 against 31); those are schema comments,
   outside the seed-comment claim, and are likewise unfixed.
5. **Standing items**, unchanged: the corpus covers only the two mutation kinds;
   nothing forces a new kind to arrive with cases; promotion has never run end
   to end; no normative consumer algorithm nor tier binding; vocabulary source
   differs between reference and primaries with no CI lock; enumerated lists in
   CI remain a hazard, including the baseline set; nothing asserts a negative
   fixture fails every gate; the neo4j mirror is stale at 15/23/31 against
   23/27/31. Say if any now blocks a PR.

Disclosed: mixed authorship, and the branch is not bisectable-green.

## How to review

Read the files yourself and verify every claim by executing it. Do not accept
this document or the verification report as evidence for anything: the report
exists so you can re-run what it claims, not so you can trust it. Build both
primaries from the tree; use no prebuilt binary you find on disk.

```sh
git clone <repo> r9 && cd r9 && git checkout b2693e1
(cd tools/dagtoml-validate-rs && cargo build --release --locked)
(cd tools/dagtoml-validate-go && go build -o /tmp/dagtoml-validate-go ./...)
cargo build --release --locked --manifest-path tools/dagtoml-rdf/Cargo.toml
bash validators/check_manifest_drift.sh
git show b2693e1
```

Approve **only** on the basis of what you inspected: code you read, commands you
ran, output you saw. Not on intent, not on plan-compliance, not on "should be
fixed", and not on the initiator having disclosed something. Either give
**unconditional approval**, or name **one concrete blocker** with a file path, a
line range, and a reproduction.
