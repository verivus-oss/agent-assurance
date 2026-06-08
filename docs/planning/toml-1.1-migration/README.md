# TOML 1.0 → 1.1 migration — DAG-TOML scoping pack

A complete, self-validating DAG-TOML governance pack scoping the
deliberate migration of the validator/conformance stack from TOML 1.0 to
TOML 1.1.

**Status: migration complete — verified, with one documented divergence.**
All eight units (U01–U08) are done. The parity spike (U01) and go/no-go
decision (U02) recorded **GO** (operator sign-off confirmed 2026-06-08),
and the migration was executed and verified end-to-end: the Rust (`toml`
1.1.2+spec-1.1.0), Go (`BurntSushi/toml` v1.6.0), and Python (`tomli`
2.4.1) primaries are uniformly TOML 1.1 in lockstep; the conformance
harness runs the 1.1 corpus (`-toml 1.1.0`); and `spec.md` §9.2 carries the
per-feature 1.1 dispositions. U08 recorded the verified state in
[`conformance/known-divergences-toml-1.1.toml`](../../../conformance/known-divergences-toml-1.1.toml):
rs/go/py **agree** on the operative dagtoml semantic corpus (empty
baseline) and the toml-test *valid* corpus, with one **pre-existing,
documented** exception — on 13 toml-test *invalid* fixtures the Go
(BurntSushi v1.6.0) parser is more permissive than Rust/Python (a
BurntSushi limitation, identical at TOML 1.0, *not* introduced by this
migration; named rather than silently skipped). The migration landed as
stacked per-unit PRs in dependency order.

## Why this pack exists

`toml 1.1.2+spec-1.1.0` (a TOML **1.1** parser) entered the Rust tooling
via a dependabot bump, and `BurntSushi/toml` v1.6.0 (1.1 default) entered
the Go validator's `go.mod` the same way. The repo's foundational
invariant is that the Rust, Go, and Python primaries agree on every
fixture — but the Rust *validator* (`toml` 0.8) and Python `tomllib` are
still TOML **1.0**, while the Go validator already parses **1.1** at
runtime. The repo is therefore already latently split, and adopting 1.1
piecemeal in one parser at a time would manufacture the exact divergence
the conformance suite exists to catch. This pack scopes the migration so
that parity across all three is proven *before* the harness flips and
*before* the remaining parsers move.

## Contents

| File | Kind | Role |
|---|---|---|
| [`01_spec.md`](01_spec.md) | spec (markdown) | Normative requirements R1–R5; the parity constraint |
| [`03_implementation_plan.md`](03_implementation_plan.md) | plan (markdown) | Decomposition rationale; risks |
| [`implementation-dag.toml`](implementation-dag.toml) | `implementation-dag` | 8-unit work DAG; parity gate (U02) upstream of every parser bump |
| [`contract-declaration.toml`](contract-declaration.toml) | `contract-declaration` | Contracts C01–C04; C01 = cross-implementation parity |
| [`readiness-gate.toml`](readiness-gate.toml) | `readiness-gate` | Gates G01 (planning pack) + G02 (parity go/no-go); status `migration-complete-go-toml-test-divergences-documented` |
| [`evidence-matrix.toml`](evidence-matrix.toml) | `evidence-matrix` | Claims ↔ pack documents; prospective claims marked |
| [`rollback-plan.toml`](rollback-plan.toml) | `rollback-plan` | Revert procedure + tooling-outcome triggers |
| [`research/01-parser-availability-survey.md`](research/01-parser-availability-survey.md) | — | U01 deliverable — parser survey (complete) |
| [`research/02-parity-decision.md`](research/02-parity-decision.md) | — | U02 deliverable — go/no-go decision: **GO** (complete) |

The two `research/` documents are the migration's first deliverables;
they are now authored, recording the **GO** decision. The operator STOP/GO
sign-off was confirmed 2026-06-08, so the parser-bump units (U03+) are
cleared to proceed under the decision's guardrails.

## Validating this pack

Every `.toml` here carries the empty-closure sentinel (self-contained)
and validates against the full stack:

```sh
RS=tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs
GO=/tmp/go-val   # go build -o /tmp/go-val ./tools/dagtoml-validate-go

$RS --repo-root . docs/planning/toml-1.1-migration/*.toml
$GO --repo-root . docs/planning/toml-1.1-migration/*.toml
python3 validators/validate_closure_root.py --discover .
python3 validators/validate_implementation_dag.py docs/planning/toml-1.1-migration/implementation-dag.toml --repo-root .
python3 validators/validate_review_readiness.py docs/planning/toml-1.1-migration/contract-declaration.toml --repo-root .
python3 validators/validate_review_readiness.py docs/planning/toml-1.1-migration/readiness-gate.toml --repo-root .
python3 validators/validate_review_readiness.py docs/planning/toml-1.1-migration/evidence-matrix.toml --repo-root .
python3 validators/validate_rollback_plan.py docs/planning/toml-1.1-migration/rollback-plan.toml --repo-root .
```

## The gate

Nothing in `implementation-dag.toml` units U03–U08 may begin until
[`readiness-gate.toml`](readiness-gate.toml) gate **G02** passes — i.e.
until the parser-availability spike (U01) and the go/no-go decision (U02)
confirm a 1.1-capable parser exists for **all three** primaries. If any
does not, the migration halts with the blocker recorded and the repo
stays uniformly TOML 1.0.

**Outcome:** G02 passed and the migration is now **complete**. U01/U02
recorded **GO** (a released, default-1.1, no-`unsafe` parser for all three
primaries), the operator sign-off was confirmed 2026-06-08, and U03–U08
then executed: all three primaries are uniformly TOML 1.1 in lockstep, the
harness runs the 1.1 corpus, `spec.md` §9.2 holds the feature dispositions,
and U08 recorded the verified state — rs/go/py agree on the operative
dagtoml corpus (empty baseline) and the toml-test valid corpus, with 13
pre-existing, documented Go (BurntSushi) permissiveness divergences on the
toml-test invalid corpus (see
[`conformance/known-divergences-toml-1.1.toml`](../../../conformance/known-divergences-toml-1.1.toml)).
The NO-GO branch above did not fire.
