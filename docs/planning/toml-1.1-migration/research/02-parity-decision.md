# U02 — Parity go/no-go decision (TOML 1.1 adoption)

Status: **complete**
Unit: [`implementation-dag.toml`](../implementation-dag.toml) `units.U02`
Produces: `ART:parity-decision`
Consumes: `ART:parser-availability-survey` ([`01-parser-availability-survey.md`](01-parser-availability-survey.md))
Governs: readiness gate G02 ([`../readiness-gate.toml`](../readiness-gate.toml)); contracts C04, C01
Created: 2026-06-08

## Decision

> ## **GO.**

A TOML **1.1**-capable parser that parses 1.1 **by default** and
preserves the safe-tools (no-`unsafe`) policy exists for **all three**
primaries and for the conformance harness. The migration is cleared to
proceed past the gate into the parser-bump units (U03/U04/U05). This
decision satisfies readiness gate **G02** and contract **C04**.

## The named 1.1 parser for each primary (C04 / G02 `must_name`)

| Primary | 1.1 parser to adopt | Version | 1.1 default? | Safe-tools | Pin |
|---|---|---|---|---|---|
| **Rust** (`dagtoml-validate-rs`, `toml-test-decode-rs`) | `toml` crate | `1.1.2+spec-1.1.0` (≥0.9.10 line) | yes | pure Rust, no-`unsafe`; already vendored in `dagtoml-rdf` | Cargo req + `Cargo.lock` |
| **Go** (`dagtoml-validate-go`) | `github.com/BurntSushi/toml` | **v1.6.0** | yes (unconditional; env-var gate removed) | **pure Go, no `unsafe`/cgo — verified in module cache** | `go.mod`/`go.sum` (already pinned) |
| **Python** (reference validators) | `tomli` | **2.4.0+** | yes | pure-Python `py3-none-any` wheel; PEP 680 upstream of stdlib `tomllib` | hash-pinned `requirements/toml.txt` |
| **Harness** (`toml-test`) | `toml-lang/toml-test` | 2.0.0+ (`-toml 1.1.0`) | 1.1 default in 2.x | — | `go install @version` in Makefile |

## Evidence (C04 `must_name`: recorded verdict + its evidence)

1. **TOML 1.1.0 is a finalized released spec** (toml-lang/toml `1.1.0`
   GitHub release tag dated 2025-12-24; spec page <https://toml.io/en/v1.1.0>
   dated 12/18/2025) — the precondition that makes "all three in lockstep"
   achievable at all. Source: toml-lang/toml releases.
2. **Go is already 1.1 at runtime.** `dagtoml-validate-go/go.mod`
   requires BurntSushi/toml **v1.6.0**, whose release notes say *"TOML
   1.1 is now enabled by default."* The v1.6.0 source in
   `$GOMODCACHE` contains **no `unsafe`, no cgo, and no
   `BURNTSUSHI_TOML_110` toggle** — 1.1 is the only behaviour. (Landed
   via PR #5.)
3. **Rust 1.1 is already vendored and proven.** `dagtoml-rdf` pins
   `toml = "1.1"` (PR #1); the `1.1.2+spec-1.1.0` line lists 1.1 parsing
   as a default feature since 0.9.10.
4. **Python 1.1 has the best-possible trust posture.** `tomli` 2.4.0+ is
   1.1-by-default, pure Python, zero-dependency, and is the *parent
   project of the stdlib `tomllib`* being replaced (PEP 680, same
   author). The replacement reduces, not increases, supply-chain
   surprise.

## Why this is GO and not NO-GO

The gate's block conditions (G02) are *"any primary lacks a viable TOML
1.1 parser"* / *"the survey or decision is missing"* / *"records NO-GO or
is unresolved."* None hold:

- No primary lacks a parser — each has a released, default-1.1, safe
  option, and two are already in-tree.
- The survey ([U01](01-parser-availability-survey.md)) exists and this
  decision cites it.
- The verdict is recorded GO with per-primary named parsers and
  versions.

Crucially, **doing nothing is not parity-neutral.** The repo is *already*
in a latent split-version state (Go validator → 1.1; Rust/Python
validators → 1.0; conformance evidence → 1.0). NO-GO would not return the
repo to a clean uniform 1.0 — it would *leave the existing divergence
latent and unverified*. (A genuine "stay at 1.0" outcome would itself
require deliberate **down**grades of the already-merged BurntSushi v1.6.0
and `dagtoml-rdf` `toml = "1.1"` pins — i.e. the rollback procedure — and
is out of scope for this decision, which was scoped as go/no-go on
*adopting* 1.1.) GO is therefore both the lower-risk and the
parity-restoring choice.

## Conditions / guardrails carried into U03–U08

GO is granted **with** the following binding conditions (these are not
new scope — they restate R1–R5 as the bar each downstream unit is held
to, so that "GO" cannot be read as "ship without proof"):

1. **Lockstep or nothing (R1/C01).** U06 may not flip the harness to
   `-toml 1.1.0` until U03, U04, and U05 have all landed. No partial
   cutover; the DAG already encodes U06 consuming all three artifacts.
2. **Safe-tools preserved (R5).** U05's `tomli` pin MUST resolve to the
   pure-Python `py3-none-any` wheel (not a mypyc binary wheel) to keep
   the reference auditable; U03/U04 keep the no-`unsafe` posture (already
   true of both parsers).
3. **No feature by default (R4/C03).** U07 must give every newly-valid
   1.1 feature an explicit permit/forbid disposition in `spec.md` before
   U08 closes.
4. **Empty divergence baseline (R1).** U08 closes only with rs/go/py
   agreeing on the full toml-test 1.1 corpus **and** the dagtoml corpus,
   with `conformance/known-divergences-toml-1.1.toml` empty. Any case
   that cannot be made to agree is a **block**, not a skiplist entry.
5. **Backward compatibility holds (R3/C02).** 1.1 is a strict superset
   of 1.0; the survey found no breaking change affecting any repo
   document. If U07 surfaces one, the `TRIG:existing-doc-invalidated`
   rollback trigger fires.

## Operator sign-off

This is the migration's separation-of-duty STOP/GO gate. Per the
implementation prompt, the decision is **surfaced to the maintainer for
go-ahead before any parser bump (U03+) begins.** Recorded recommendation:
**GO**, on the evidence above. No parser-bump unit starts until the
maintainer confirms.

- Recommended by: implementation session (author role; not an approval).
- Maintainer go-ahead: **confirmed 2026-06-08** — STOP/GO cleared to proceed
  into the parser-bump units (U03–U08), subject to the guardrails above
  (lockstep cutover, safe-tools, explicit per-feature spec disposition,
  empty divergence baseline). The maintainer's confirmation authorizes the
  work; it is not a CODEOWNERS review approval of any resulting PR.
