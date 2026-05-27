# Gemini r2 Independent Review — README defect-fix (commit 953691b)

**Reviewer**: gemini (operating under tools/review-request-dag.toml [policy.*] and the r2 verification program in docs/reviews/2026-05-25-readme-restructure-r2/verification_report.toml)
**Commit under review**: 953691b (parent: b759eaf; fix for r1 blockers)
**Scope**: README.md only (+5/-4).
**Review date**: 2026-05-25.

---

## 1. Method

I performed the following steps to verify the corrective program:

1.  **Context Assembly:** Read the r2 verification report (`verification_report.toml`), r1 findings (`codex.md`, `grok.md`), and the binding policy (`tools/review-request-dag.toml`).
2.  **State Inspection:** Read the README.md at 953691b and b759eaf to analyze the diff.
3.  **Command Verification:** Executed the revised §13 validation command cited in README.md.
4.  **Byte-Level Verification:** Inspected primary validator source code (`tools/dagtoml-validate-{rs,go}`) to confirm the absence of cost-record handling.
5.  **CI Workflow Verification:** Inspected `.github/workflows/validate.yml` to confirm the absence of byte-comparison steps between primary validators.
6.  **Regression Check:** Analyzed the diff hunk headers to ensure no changes to r1-closed sections (Status, Repository Map, Start Here, Governance).

---

## 2. Per-D classification

### D1: closed (r1_filer: grok)
**Defect:** `validate_abstraction_class.py` rejected `--discover .`.
**Verification:**
- README.md:182-183 now uses:
  `python3 validators/validate_abstraction_class.py --repo-root . core/*-kind.toml profiles/*/*-kind.toml`
- Executed the new command from repo root:
  `python3 validators/validate_abstraction_class.py --repo-root . core/*-kind.toml profiles/*/*-kind.toml`
  **Output:** `ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 19 declared a §13 block).`
**Evidence:** README.md:182-183; successful command execution.

### D2: closed (r1_filer: codex + grok)
**Defect:** README claimed primary validators were authoritative for `cost`.
**Verification:**
- README.md:144 now reads: `Authoritative for profile-descriptor, the disclosure-profile kinds, §2.5–§2.7 meta surface, and §11.1 [provenance.encryption] sub-table`. The word `, cost` has been removed.
- `grep -nE 'mode \(auto|profile|disclosure|provenance|meta\)' tools/dagtoml-validate-rs/src/main.rs tools/dagtoml-validate-go/main.go` confirms only these five modes exist; no `cost` handler.
- `ls validators/validate_cost.py` confirms the reference validator exists.
**Evidence:** README.md:144; `tools/dagtoml-validate-rs/src/main.rs:60`.

### D3: closed (r1_filer: codex + grok)
**Defect:** README claimed CI requires "bytewise agreement" between primaries.
**Verification:**
- README.md:145 now reads: `Same surface as Rust; CI runs both against every canonical example + tier file + profile descriptor on each push, and both must exit 0`.
- `grep -nE 'diff|cmp.*output|compare.*primary' .github/workflows/validate.yml` returns zero hits in primary validator steps.
- `.github/workflows/validate.yml:184-187` confirms sequential execution with independent exit code checks.
**Evidence:** README.md:145; `.github/workflows/validate.yml:184-187`.

### D4: closed (r1_filer: initiator)
**Defect:** Python row understated its role as the ONLY validator for several surfaces.
**Verification:**
- README.md:146 now explicitly lists: `cost-record, abstraction-class §13, closure-root §12, rollback-plan trigger closure, IJB conformance`.
- Confirmed existence of:
  - `validators/validate_cost.py`
  - `validators/validate_abstraction_class.py`
  - `validators/validate_closure_root.py`
  - `validators/validate_rollback_plan.py`
  - `validators/validate_ijb_conformance.py`
**Evidence:** README.md:146; `ls validators/` output.

---

## 3. Regression check on C01–C07

I verified that the seven closures from r1 remain intact. The diff `b759eaf..953691b` is strictly limited to two hunks:
1.  **Validation Tooling table** (lines 142-146): Covers D2, D3, D4.
2.  **Local Validation block** (lines 180-183): Covers D1.

No edits were made to the following sections which carry C01-C07:
- **Status table** (C01, C06).
- **Repository Map** (C02).
- **Start Here / Role-based grouping** (C03).
- **Governance** (C07).
- **Rationale text** (C05).

**Evidence:** `git diff b759eaf..953691b -- README.md` hunk headers and manual inspection.

---

## 4. Final blockers

None. All identified defects are closed and no regressions or new blockers were found.

---

## 5. Terminal verdict

Terminal verdict: unconditional_approval
