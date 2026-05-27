# spec-e2e-r3 — codex raw findings

Job: b7ab156d-2297-4dc7-b499-e59147d5d6f5
Started: 2026-05-25T13:36:55Z
Finished: 2026-05-25T13:40:49Z
Exit: 0
Verdict: **unconditional_approval**

## Round 3 Verification: 4fbc906

Review basis: checked out HEAD is `4fbc90639b4bafd7f7a90b52ae723efd1e9a9d27`. I inspected the bytes and ran the validators locally.

1. **Paper conclusion cross-check: pass**
   `paper/main.tex:1556-1564` now says the six numbers are cross-validated by `validate_numbers.py`, with `AUX1 and C06a-d via scipy / numpy` and `C06e via a deterministic stdlib digest re-derivation plus a subprocess...`. No global scipy/numpy overclaim remains.

2. **Python `--help` cites INV01..INV06: pass**
   Source fix is at `validators/validate_gate_decision.py:259-272`, where argparse description enumerates `INV01` through `INV06`.
   Command output:
   ```text
   grep IDs: INV01 INV02 INV03 INV04 INV05 INV06
   ```
   Help output begins:
   ```text
   Validate a gate-decision instance against the hard invariants INV01..INV06
   ...
   INV01 ... INV02 ... INV03 ... INV04 ... INV05 ... INV06 ...
   ```

3. **Python positive example: pass**
   Command:
   ```text
   python3 validators/validate_gate_decision.py --repo-root . examples/self-modification-gate-decision.toml
   ```
   Output:
   ```text
   GATE-DECISION VALIDATION PASSED (1 file checked; INV01..INV06 enforced).
   exit=0
   ```

4. **Python r1 negatives: pass**
   Negative shapes are defined in `docs/reviews/2026-05-25-spec-e2e-r2/verification_report.toml:77-83`.
   Both local variants exited `1` and emitted `INV06 violated (conjunctive AND)`. Same-provider output cited `deciding_provider_id ('anthropic') == proposing_provider_id ('anthropic')`; same-family output cited `deciding_model_family_id ('claude') == proposing_model_family_id ('claude')`.

5. **Rust validator: pass**
   The literal shorthand command in r3 omits `--repo-root`; the Rust CLI requires it at `tools/dagtoml-validate-rs/src/main.rs:60-63` and `106-108`. With the required flag, the surface passes:
   ```text
   DAGTOML VALIDATION PASSED (rust primary)
   exit=0
   ```
   Both negatives exited `1` with `INV06 violated (conjunctive AND)` and the same-provider / same-family equality detail. The AND rejection is implemented at `tools/dagtoml-validate-rs/src/main.rs:955-983`.

6. **Go validator: pass**
   Same invocation note: Go requires `--repo-root` at `tools/dagtoml-validate-go/main.go:784-790`. With the required flag:
   ```text
   DAGTOML VALIDATION PASSED (go primary)
   exit=0
   ```
   Both negatives exited `1` with `INV06 violated (conjunctive AND)`. The AND rejection is implemented at `tools/dagtoml-validate-go/main.go:1076-1092`.

7. **CI gate-decision step: pass**
   Step exists at `.github/workflows/validate.yml:346`. It runs Python positives at `363-368`, synthesizes both negatives at `376-414`, checks Python negative rejection at `416-423`, then runs Rust and Go positives/negatives at `432-449`. That is 12 validator invocations: Python 4 plus Rust/Go 8.

8. **Kind descriptor invariants / planned markers: pass**
   `profiles/agent-assurance/gate-decision-kind.toml:164-202` declares `INV01` through `INV06`. `INV01-INV04` and `INV06` reference `validators/validate_gate_decision.py` at lines `167`, `174`, `181`, `188`, and `202`; `INV05` is explicitly `scope declaration; no validator action` at line `195`, matching the r2 exception in `docs/reviews/2026-05-25-spec-e2e-r2/verification_report.toml:132`.
   `rg -n '\(planned\)|planned' profiles/agent-assurance/gate-decision-kind.toml` produced no matches.

9. **Regression sweep S03/S05/S06: pass**
   S03 closure-root brittleness remains in `SPEC.md:953-1008` and the forbidden stale-root mechanisms remain in `SPEC.md:1051-1071`.
   S06 abstraction-class header/rule remains at `SPEC.md:1195-1241`.
   S05 capability-envelope domain mapping table remains at `SPEC.md:1277-1288`, with fail-closed semantics at `SPEC.md:1305-1321` and worked example at `SPEC.md:1418-1448`.

No concrete blocker found. S08.1 is closed, and the r2-closed INV06 enforcement surfaces survived.

VERDICT: unconditional_approval
