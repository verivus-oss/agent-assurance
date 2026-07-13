# Planning bundle: profile-pinned closure record forms (SPEC 12.8 promotion)

Created: 2026-07-12. Status: U01 in progress (design pack + cross-LLM design
review); everything past U02 is blocked on the grammar-freeze gate.

## What this is

The planning pack for promoting **profile-pinned closure record forms** into
the operative SPEC 12.8 closure stream, so a profile descriptor can declare
additional labeled closure inputs and the validator triad folds them into
`closure_root`. First user: the `com.verivus.runtime` `api-snapshot` kind,
whose component digests (`snapshot.request.descriptor_sha256`,
`snapshot.response.body_sha256`) and witness digest
(`snapshot.witness.attestation_sha256`, when present) become independent
closure records.

The property this delivers: **witness stripping becomes detectable at the
closure root** (an anchored root changes when the witness table is removed),
closing the gap the kind descriptor's CLOSURE LAYERING prose discloses and the
profile's external review
(`docs/reviews/2026-06-17-com-verivus-runtime-api-snapshot/`) independently
raised.

## Validating the pack

```sh
python3 validators/validate_implementation_dag.py docs/planning/closure-record-form-promotion/implementation-dag.toml
python3 validators/validate_review_readiness.py docs/planning/closure-record-form-promotion/contract-declaration.toml
python3 validators/validate_review_readiness.py docs/planning/closure-record-form-promotion/readiness-gate.toml
python3 validators/validate_review_readiness.py docs/planning/closure-record-form-promotion/evidence-matrix.toml
python3 validators/validate_rollback_plan.py docs/planning/closure-record-form-promotion/rollback-plan.toml
python3 validators/validate_closure_root.py --discover .
taplo lint docs/planning/closure-record-form-promotion/*.toml
```

## The pack

| File | Role |
|---|---|
| [`01_design.md`](01_design.md) | The design: grammar, profile-descriptor schema, triad changes, fixtures, compatibility |
| [`03_implementation_plan.md`](03_implementation_plan.md) | Decomposition rationale for the DAG |
| [`implementation-dag.toml`](implementation-dag.toml) | 10 units, grammar-freeze hard gate at U02 |
| [`contract-declaration.toml`](contract-declaration.toml) | C01-C06: parity, stripping detection, compat, enumerability, posture exclusion, gate precedence |
| [`readiness-gate.toml`](readiness-gate.toml) | G01 planning pack, G02 grammar freeze |
| [`evidence-matrix.toml`](evidence-matrix.toml) | Claims -> evidence, prospective entries marked |
| [`rollback-plan.toml`](rollback-plan.toml) | Stack-revert procedure and triggers |

## Process obligations

- No initiator self-approval: the design review (U01) and the implementation
  review (U10) are dispatched via `tools/review-request-dag.toml` to
  independent reviewers, evidence under `docs/reviews/`.
- The grammar freeze (U02) requires operator STOP/GO before any spec,
  validator, profile, or fixture change lands.
- Downstream/runtime sequencing and any public carve-out are planned in the
  consuming repository's own bundle, gated on this DAG's terminal output;
  this public bundle intentionally names no internal repositories.
