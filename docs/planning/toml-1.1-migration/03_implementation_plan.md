# Implementation plan — TOML 1.0 → 1.1 migration

Status: **U01/U02 complete — parity decision GO (2026-06-08), operator
sign-off confirmed; cleared for U03+**
Created: 2026-06-08
Referenced by: [`implementation-dag.toml`](implementation-dag.toml) `[meta].decomposition`

This document is the decomposition rationale behind
[`implementation-dag.toml`](implementation-dag.toml). The DAG is the
machine-checkable artifact; this is the human-readable "why."

## Shape of the DAG

```
            U01 parser-availability-spike            (layer 0, tier 1)
             │
            U02 parity go/no-go decision             (layer 1, tier 1)   ← HARD GATE
             ├──────────────┬──────────────┐
            U03 rust-1.1    U04 go-1.1    U05 python-1.1   (layer 2, tier 2)
             └──────────────┴──────────────┘
            U06 conformance-harness-1.1              (layer 3, tier 2)
             │
            U07 spec-document-1.1-audit              (layer 4, tier 3)
             │
            U08 cross-impl-1.1-conformance-verify    (layer 5, tier 3)
```

Critical path: U01 → U02 → U04 → U06 → U07 → U08 (510 LOC), with U04
(the Go parser move) the heaviest of the three parallel parser units and
therefore on the path.

## Why this decomposition

- **The decision gate (U02) is a real barrier, not ceremony.** Every
  parser bump (U03/U04/U05) depends on U02. This encodes R2: nothing
  changes until parity feasibility is proven. If U02 is NO-GO, units
  U03–U08 never start. This is the separation-of-duty discipline applied
  to a dependency migration — the "intent" (adopt 1.1) cannot silently
  become "action" (bump a parser) without the proof step in between.

- **The three parser units run in parallel (layer 2) but converge
  (U06).** Rust, Go, and Python are independent changes, but the
  conformance harness can only flip to 1.1 once *all three* land — hence
  U06 consumes all three artifacts. There is no partial cutover.

- **The spec audit (U07) precedes final verification (U08), not the
  harness flip.** Subtle but important: U06 makes the parsers *capable*
  of 1.1; U07 decides which 1.1 features the *spec* actually permits
  (R4). A feature can be parser-valid yet spec-forbidden. U08 then
  verifies the whole stack agrees on the resulting surface.

## Per-unit notes

- **U01** — pure research; produces the availability survey. The crux is
  Go and Python: Rust 1.1 is already proven in `dagtoml-rdf`.
- **U02** — the go/no-go. Output is a decision record. If any primary
  has no viable 1.1 parser, this records NO-GO and the migration stops.
- **U03** — mirror the `toml 1.1.x+spec-1.1.0` line already in
  `dagtoml-rdf`; the validator uses the parse-only API, so call sites may
  shift.
- **U04** — the highest-risk unit: move Go to a 1.1-capable parser while
  preserving the no-`unsafe` safe-tools policy. If BurntSushi has no 1.1
  release, this unit is where the migration most likely fails.
- **U05** — replace stdlib `tomllib` with a hash-pinned 1.1 parser; the
  Python reference must stay authoritative for the corpus.
- **U06** — flip `toml-test` to `-toml 1.1.0`, fold in the
  `toml-test-decode-rs` work (formerly PR #4), rename/retitle the CI step.
- **U07** — audit `spec.md` + every canonical doc for newly-valid 1.1
  features; record the permit/forbid disposition.
- **U08** — final cross-implementation verification with an empty
  known-divergences baseline.

## Risks

| Risk | Unit | Mitigation |
|---|---|---|
| Go has no TOML 1.1 parser meeting the safe-tools policy | U04 | U02 NO-GO; migration halts cleanly |
| Python 1.1 parser is unmaintained / poor supply-chain posture | U05 | weigh in U02; consider keeping Python advisory-only (a spec decision) |
| A 1.0→1.1 breaking change invalidates an existing repo doc | U07 | R3 + rollback trigger `TRIG:existing-doc-invalidated` |
| Partial cutover leaves parsers split | U06 | DAG forbids it — U06 consumes all three parser artifacts |

See [`rollback-plan.toml`](rollback-plan.toml) for the revert procedure
if any of these fire after a cutover begins.
