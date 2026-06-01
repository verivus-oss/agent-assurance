---
id: ISS-005
title: Operational `tools/*-dag.toml` DAGs are outside CI structural validation; `claim-analysis-agent-gated-dag.toml` violates INV01
status: open
severity: medium
opened: 2026-06-01
opened_in_commit: 91e050a
classification: §5 hard-invariant conformance / CI coverage gap
---

## Symptom

`tools/claim-analysis-agent-gated-dag.toml` fails the reference
implementation-dag validator on the INV01 inverse invariant:

```
$ python3 validators/validate_implementation_dag.py -- tools/claim-analysis-agent-gated-dag.toml
IMPLEMENTATION DAG VALIDATION FAILED
- inverse mismatch: U08.depends_on contains `U04` but U04.blocks is missing `U08`
```

`[units.U08].depends_on = ["U04","U05","U06","U07"]`, but
`[units.U04].blocks = ["U05"]`. INV01 (`spec.md#5-hard-invariants`,
restated in `core/implementation-dag-kind.toml`) requires `blocks` to be
the *exact* inverse of direct `depends_on`. Independent recomputation of
the inverse confirms `U04` is the only mismatched node; every other unit
in the file is consistent, and the two sibling DAGs
(`tools/claim-analysis-document-review-dag.toml`,
`tools/review-request-dag.toml`) both pass.

The dependency is real and required: `U08` consumes
`ART:source-reliability-findings`, which is produced **only** by `U04`
(INV03 holds). The edge is transitively redundant for *ordering*
(`U04 → U05 → U08` already exists), but DAG-TOML couples `consumes` to
`depends_on`, so the direct edge must stay and the inverse must reflect
it. The fix therefore belongs in `U04.blocks`, not in `U08.depends_on`.

This defect went unnoticed because **CI never runs the structural
implementation-dag validator over `tools/`**. In
`.github/workflows/validate.yml`, `validate_implementation_dag.py` (and
the Rust/Go `--mode implementation-dag` equivalents) are invoked only
against:

- `examples/minimal-implementation-dag.toml` (the canonical-examples step),
- `examples/negative/implementation-dag-bad-critical-path.toml` (expected-reject), and
- `skills/convert-md-to-dag/implementation_dag.toml` (skill-package step).

The three operational DAGs under `tools/` — the ones consumed as durable,
executable instructions (e.g. `tools/review-request-dag.toml` is the
named review gate referenced by downstream consumers) — are outside the
structural-validation net. (Note: the `closure_root` gate *does* cover
them via `validate_closure_root.py --discover .`; the gap is specifically
the INV01–INV05 structural surface, not §12.)

## Why it matters

INV01–INV05 are the load-bearing graph invariants that let independent
tools consume a DAG without re-deriving its shape. A `tools/` DAG that
silently breaks INV01 ships green and is handed to executors and
reviewers as if conformant. The defect here is benign in effect (a
missing reverse edge, not a wrong dependency), but the coverage gap that
hid it is not: any of INV01–INV05 could be violated in a `tools/` DAG
today and CI would stay green.

## Safeguard (what would prevent recurrence)

Consistent with the stance recorded in
[ISS-004](2026-05-24-iss-004-spec-reserved-kind-files-must-land-with-closure-root.md)
(discipline is the prevention; CI is the backstop):

### Safeguard A — convention (the prevention)

Any commit that adds or modifies an `implementation-dag` under `tools/`
MUST run `validators/validate_implementation_dag.py` against the changed
file(s) locally before `git commit`, and must not commit on red. Add this
to `CONTRIBUTING.md` "Local Checks" next to the existing
`validate_closure_root.py --discover .` line, citing this issue.

### Safeguard B — CI coverage (the backstop)

Extend `.github/workflows/validate.yml` to validate every operational DAG
under `tools/`, mirroring the canonical-examples step. Minimal shape:

```yaml
      - name: Validate operational tools/ DAGs (strict)
        run: |
          set -e
          for f in tools/*-dag.toml; do
            [ -e "$f" ] || continue
            echo "--- $f ---"
            python3 validators/validate_implementation_dag.py "$f"
          done
```

For parity with the example/skill steps, the Rust/Go validators should
gain the same `tools/*-dag.toml` coverage under `--mode implementation-dag`.
Apply Safeguard A's one-line fix to `U04.blocks` **before** wiring
Safeguard B, otherwise the new step turns CI red on landing.

## Resolution steps (the actionable fix)

1. **One-line INV01 fix** in `tools/claim-analysis-agent-gated-dag.toml`,
   `[units.U04]`:
   ```toml
   blocks         = ["U05","U08"]   # was ["U05"]
   ```
   `[computed]` is unaffected (the U04→U08 edge is transitively redundant
   for ordering, so entry_points / leaf_nodes / critical_path / loc_totals
   / max_parallel are unchanged). Re-run the validator to confirm PASS.
2. **CONTRIBUTING.md** — add the Safeguard A discipline under "Local
   Checks", citing this issue.
3. **CI** — add the Safeguard B step (and Rust/Go parity) so the coverage
   gap is closed for all current and future `tools/` DAGs.

## Acceptance criteria

- `python3 validators/validate_implementation_dag.py tools/claim-analysis-agent-gated-dag.toml`
  passes (and the Rust/Go validators agree).
- `.github/workflows/validate.yml` validates every `tools/*-dag.toml`
  with the structural implementation-dag validator (Python + Rust + Go),
  so a future INV01–INV05 violation in a `tools/` DAG is caught on push.
- `CONTRIBUTING.md` "Local Checks" names the `tools/` DAG validation
  discipline and links to this issue.
