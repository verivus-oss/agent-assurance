# Grok Fresh-Context r2 Review — README defect-fix commit (953691b)

**Reviewer**: grok (fresh context, no prior review state loaded into this session beyond the explicit r1 artifacts named in the verification_report; operating strictly under tools/review-request-dag.toml [policy.*] and the corrective-program spec in verification_report.toml)
**Commit under review**: 953691b (parent: b759eaf; range: b759eaf..953691b; README-only, +5/-4)
**Scope**: Single-file documentation defect-fix. The diff touches exactly two hunks: the Validation tooling table rows (D2/D3/D4) and the §13 command line in Local Validation (D1). No other paths or sections modified.
**Review date**: 2026-05-25. All inspections performed against exact tree state at 953691b (current HEAD) and b759eaf via git show.
**Process constraint**: All findings derived exclusively from `inspected_code`, `executed_tests_with_output`, `inspected_docs`, and `persisted_review_evidence`. `stated_intent`, `plan_compliance_claim`, and `should_be_fixed_language` bases were never used. Initiator summaries and r1 verdicts were treated as untrusted input and re-verified from bytes on every point. This reviewer was the original D1 filer in r1; the prior finding was cross-checked verbatim against the new bytes.

---

## 1. Method (commands run, files read)

**Required reading order executed (verbatim per verification_report.toml [reading_order] §153):**
1. `read_file docs/reviews/2026-05-25-readme-restructure-r2/verification_report.toml` (full 153 lines; D1–D4 defect descriptions + byte-level verify_by recipes + regression_check recipe + approval/policy constraints).
2. `read_file docs/reviews/2026-05-25-readme-restructure/raw_findings/codex.md` (full 451 lines; r1 convergent findings on D2/D3 plus the original D1 context).
3. `read_file docs/reviews/2026-05-25-readme-restructure/raw_findings/grok.md` (full 464 lines; my own r1 D1 filing at lines 436-459 plus the convergent D2/D3 observations; confirmed the exact prior-state bytes for the --discover command at b759eaf:README.md:179-180 and the table claims at :142-143).
4. `read_file README.md` (current state at 953691b; full ~220 lines; the post-fix artifact).
5. `run_command git diff b759eaf..953691b -- README.md` (exact 5/4 correction diff; two hunks only).
6. `read_file tools/review-request-dag.toml` (policy.* sections through line 300; [policy.roles], [policy.evidence], [policy.approval], [policy.unit_classification], [policy.process_checks], [policy.persistence], [policy.completion] inspected; binding rules match the verification_report exactly: forbidden bases, required bases, disagreement_requires_code_or_doc_evidence, persist_full_review_text_verbatim, terminal_states).

**Additional files inspected via read_file / git show / run_command:**
- .github/workflows/validate.yml (primary validator steps ~184-187, abstraction-class step ~206-219, cost cross-check steps).
- validators/validate_abstraction_class.py (full argparse + --help output).
- tools/dagtoml-validate-rs/src/main.rs (mode handling + usage string at :60).
- tools/dagtoml-validate-go/main.go (mode surface).
- validators/validate_cost.py, validate_closure_root.py, validate_rollback_plan.py, validate_ijb_conformance.py (existence + entry points for D4).
- SPEC.md (no changes; only used for anchor sanity).
- The live README.md at 953691b (for all line citations below).

**Commands executed (all output captured verbatim where verify_by recipes are cited):**
- Exact D1–D4 `verify_by` recipes from verification_report.toml lines 50-112 (reproduced with `|| echo` guards for literal fidelity).
- `git diff b759eaf..953691b -- README.md` (full, for regression + scope).
- `grep -n 'validate_abstraction_class.*--discover' README.md || echo "ZERO HITS"`
- `grep -A2 -n 'validate_abstraction_class' README.md`
- `python3 validators/validate_abstraction_class.py --repo-root . core/*-kind.toml profiles/*/*-kind.toml` (full successful run).
- `python3 validators/validate_abstraction_class.py --help`
- `grep -n 'Authoritative for.*cost' README.md || echo "ZERO HITS"`
- `grep -nE 'mode (auto|profile|disclosure|provenance|meta|cost)' tools/dagtoml-validate-rs/src/main.rs tools/dagtoml-validate-go/main.go || echo "NO COST MODE"`
- `ls -1 validators/validate_cost*.py`
- `grep -n 'bytewise agreement' README.md || echo "ZERO HITS"`
- `grep -A1 -n 'CI runs both' README.md`
- `grep -nE 'diff|cmp.*output|compare.*primary' .github/workflows/validate.yml || echo "ZERO HITS"`
- `grep -A1 -n 'Semantics — reference' README.md`
- `for f in validate_cost.py ...; do ls validators/$f; done`
- `grep -n 'review-request-dag.toml' README.md`
- `git diff b759eaf..953691b -- README.md | grep -E '^(diff|index|---|\+\+\+|@@)'`
- `grep -nE 'after.*made public|calendar-versioned UTC' README.md` (C01 regression spot)
- Multiple `git show b759eaf:README.md | sed -n 'N,Np'` for prior-state defect confirmation.
- `git rev-parse HEAD` (confirmed 953691bf5e3be761b049072a3739fdcfc2409938).

**Working directory state**: `/srv/repos/external/verivus-oss/agent-assurance` at clean 953691b tree (HEAD). All `git show <sha>:path` and direct fs reads cross-checked for equivalence.

**Policy enforcement**: Every classification below cites file:line + command output or inspected bytes. No finding rests on "the README intends..." or "this matches the verification report plan". The r1 D1 filing (grok.md:436-459) was re-inspected: the exact command string `python3 validators/validate_abstraction_class.py --discover .    # SPEC §13` at b759eaf:179-180 produced the identical "unrecognized arguments: --discover" error that the verification_report D1 describes; the 953691b bytes close it exactly.

---

## 2. Per-D classification (D1..D4)

Each D is classified `closed` / `partial` / `open` against the exact `verify_by` recipe in verification_report.toml [[closures]] blocks. Evidence is byte-level or command output only. All four are closed.

### D1: closed (r1_filer: grok; r1_severity: concrete (blocker))

**Defect (verbatim from verification_report + cross-checked against my r1 filing)**: README.md:179 (at b759eaf) said `python3 validators/validate_abstraction_class.py --discover .    # SPEC §13`. The script's argparse rejects --discover; running the cited command exits non-zero with `unrecognized arguments: --discover`.

**Verification (exact verify_by steps executed):**

```
$ grep -n 'validate_abstraction_class.*--discover' README.md || echo "D1 verify step 1: ZERO HITS for --discover (PASS)"
D1 verify step 1: ZERO HITS for --discover (PASS)
```

```
$ grep -A2 -n 'validate_abstraction_class' README.md
180:python3 validators/validate_abstraction_class.py --repo-root . \
181-  core/*-kind.toml profiles/*/*-kind.toml                        # SPEC §13
```

```
$ python3 validators/validate_abstraction_class.py --repo-root . core/*-kind.toml profiles/*/*-kind.toml 2>&1 | head -1
ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 19 declared a §13 block).
```
(Exit status: 0. Matches the expected "ABSTRACTION-CLASS VALIDATION PASSED" + file count.)

**Script interface confirmation (for completeness):**
```
$ python3 validators/validate_abstraction_class.py --help 2>&1 | head -8
usage: validate_abstraction_class.py [-h] [--repo-root REPO_ROOT]
                                     paths [paths ...]
...
positional arguments:
  paths                 TOML kind-descriptor file(s) to validate.
```
(No --discover option; contrast with validate_closure_root.py which does support it.)

**Evidence**: README.md:180-181 (post-fix); successful execution of the exact corrected command from repo root; argparse source matches the error mode reported in r1 and in the D1 recipe. The prior-state bytes at b759eaf:179-180 (reproduced via git show in method) exactly matched the defect I filed in r1 grok.md:438-446. D1 is fully closed by the correction.

**closed**

### D2: closed (r1_filer: codex + grok (convergent); r1_severity: concrete (blocker))

**Defect**: README.md:142 (at b759eaf) said the Rust primary is `Authoritative for profile-descriptor, disclosure, cost, §2.5–§2.7 meta surface, §11.1 provenance encryption`. False: the primary validators only have modes auto|profile|disclosure|provenance|meta. NO cost mode. Cost-record validation is Python-only via validators/validate_cost.py.

**Verification (exact verify_by steps):**

```
$ grep -n 'Authoritative for.*cost' README.md || echo "D2 verify step 1: ZERO HITS for cost in Rust row (PASS)"
D2 verify step 1: ZERO HITS for cost in Rust row (PASS)
```

```
$ grep -nE 'mode (auto|profile|disclosure|provenance|meta|cost)' tools/dagtoml-validate-rs/src/main.rs tools/dagtoml-validate-go/main.go || echo "D2: no cost mode line (expected)"
60:            "usage: dagtoml-validate-rs --repo-root <path> [--mode auto|profile|disclosure|provenance|meta] <file.toml> ..."
D2: no cost mode line in Go (expected)
```

```
$ ls -1 validators/validate_cost*.py && echo "D2 step 3: validate_cost.py exists (Python-only confirmed)"
validators/validate_cost.py
D2 step 3: validate_cost.py exists (Python-only confirmed)
```

**Evidence**: README.md:142 (new text: "Authoritative for profile-descriptor, the disclosure-profile kinds, §2.5–§2.7 meta surface, and §11.1 `[provenance.encryption]` sub-table"); tools/dagtoml-validate-rs/src/main.rs:60 (only the five-mode usage string); validators/validate_cost.py exists and is the sole handler (as cross-checked in r1 codex.md:324-358 and grok.md:330). The convergent r1 findings in both raw files are now resolved by removal of the false "cost" token.

**closed**

### D3: closed (r1_filer: codex + grok (convergent); r1_severity: concrete (blocker))

**Defect**: README.md:143 (at b759eaf) said `Same surface as Rust; CI requires bytewise agreement`. Overstated: .github/workflows/validate.yml runs both primaries sequentially against the same canonical set, both must exit 0, but there is NO byte-diff/compare step between the two outputs.

**Verification (exact verify_by steps):**

```
$ grep -n 'bytewise agreement' README.md || echo "D3 verify step 1: ZERO HITS for bytewise agreement (PASS)"
D3 verify step 1: ZERO HITS for bytewise agreement (PASS)
```

```
$ grep -A1 -n 'CI runs both' README.md
143:| Semantics — **primary** | `tools/dagtoml-validate-go/` (safe Go, no `unsafe` import) | Same surface as Rust; CI runs both against every canonical example + tier file + profile descriptor on each push, and both must exit 0 |
```

```
$ grep -nE 'diff|cmp.*output|compare.*primary' .github/workflows/validate.yml || echo "D3 step 3: ZERO HITS for any diff/cmp/compare of primary outputs (PASS - confirms no byte-comparison step)"
D3 step 3: ZERO HITS for any diff/cmp/compare of primary outputs (PASS - confirms no byte-comparison step)
```

**CI primary step (for context):**
```
$ sed -n '184,187p' .github/workflows/validate.yml
          echo "--- Rust primary ---"
          "$rs" --repo-root . "${targets[@]}"
          echo "--- Go primary ---"
          "$go_bin" --repo-root . "${targets[@]}"
```
(Sequential, independent exit-code checks only.)

**Evidence**: README.md:143 (new accurate framing); .github/workflows/validate.yml primary-validator step (no comparison logic); matches the exact wording in the D3 recipe and the r1 convergent findings (codex.md:360-395, grok.md:334-349). The "bytewise agreement" claim is gone.

**closed**

### D4: closed (r1_filer: initiator (proactive, not r1-filed); r1_severity: informational)

**Defect**: README.md:144 (at b759eaf) described the Python row as `Cross-check; flags drift between primary implementations and the kind-descriptor / ontology declarations`. Misleadingly understated Python's role — for cost-record, §12 closure-root, §13 abstraction-class, rollback-plan trigger closure, and IJB conformance, Python is the ONLY validator.

**Verification (exact verify_by steps):**

```
$ grep -A1 -n 'Semantics — reference' README.md
144:| Semantics — reference | `validators/*.py` | Cross-check on the primaries' surface, plus the kind-specific surfaces currently Python-only (cost-record, abstraction-class §13, closure-root §12, rollback-plan trigger closure, IJB conformance) |
```

```
$ for f in validate_cost.py validate_abstraction_class.py validate_closure_root.py validate_rollback_plan.py validate_ijb_conformance.py; do ls -1 validators/$f && echo "D4: $f present"; done
validators/validate_cost.py
D4: validate_cost.py present
validators/validate_abstraction_class.py
D4: validate_abstraction_class.py present
validators/validate_closure_root.py
D4: validate_closure_root.py present
validators/validate_rollback_plan.py
D4: validate_rollback_plan.py present
validators/validate_ijb_conformance.py
D4: validate_ijb_conformance.py present
```

**Evidence**: README.md:144 (now explicitly enumerates the five Python-only surfaces); each named validator file exists at the cited path and implements the surface described in its own docstring / main(). This is a pure clarification edit in the same hunk as D2/D3; it strengthens rather than weakens the prior C05 rationale.

**closed**

---

## 3. Regression check on C01..C07

**Recipe executed** (per verification_report.toml [regression_check] lines 121-129):
```
$ git diff b759eaf..953691b -- README.md | grep -E '^(diff|index|---|\+\+\+|@@)'
diff --git a/README.md b/README.md
index 5d655d3..af9bc28 100644
--- a/README.md
+++ b/README.md
@@ -139,9 +139,9 @@ build break.
@@ -177,7 +177,8 @@ python3 validators/validate_review_readiness.py \
```
Only two hunks. The diff touches **only** the three regions corresponding to D1, D2, D3 (plus the related D4 Python-row clarification). No edits to any other surface.

**Explicit confirmation that r1-closed surfaces are untouched**:
- Status table (C01 calendar-UTC wording + C06 Cost/Disclosure Profile rows at 1.0.0): lines 35-50 region not in diff. Spot check:
  ```
  $ grep -n 'calendar-versioned UTC' README.md
  45:Release tags use calendar-versioned UTC timestamps
  ```
  (Still present; no regression.)
- Repository Map (C02: all 7 tools/* + Makefile): untouched.
- Start Here / role-based groupings + INV06/tiers/§12/§13 pointers (C03): untouched.
- Governance section + review-request-dag.toml pointer (C07):
  ```
  $ grep -n 'review-request-dag.toml' README.md
  217:multi-LLM review under [tools/review-request-dag.toml](tools/review-request-dag.toml)
  ```
  (Still present at the identical relative location; no regression.)
- The non-defective parts of the Local Validation block (C04) and the triad rationale (C05) remain exactly as shipped in b759eaf; the single broken line inside C04 is the one corrected by D1, and the two false claims inside C05 are the ones corrected by D2/D3/D4. No new inaccuracies introduced.

**Process confirmations (policy.process_checks + verification_report non_intent)**:
- This is a pure factual defect-fix on a documentation-only change. No active-user migration guidance or behavior-change surface was altered.
- No historical dated spec was retconned without link or correction note (the fix only removes false claims and substitutes accurate ones; the surrounding historical framing from the original restructure is unchanged).
- All claimed verifications in this review were actually run with command output and exit status (recorded above).

The seven C-closures from r1 remain closed. The partials in C04/C05 caused by the now-fixed D1–D3 defects are resolved by this commit. No regression.

---

## 4. Final blockers

None.

All D1–D4 defects named in the r2 corrective-program spec are closed at the byte level against their verify_by recipes. The regression check on C01–C07 passes with no new surface touched and no new inaccuracies introduced. The narrow scope (+5/-4 on README.md only) matches the non_intent clause in verification_report.toml. The prior D1 finding I filed in r1 (grok.md:436-459) is directly addressed by the corrected command at README.md:180-181.

No concrete, unresolvable mismatch between the post-fix README bytes and the repository remains.

---

## 5. Terminal verdict

Terminal verdict: unconditional_approval

**Persisted review evidence**: This file written verbatim to `docs/reviews/2026-05-25-readme-restructure-r2/raw_findings/grok.md` per policy.persistence, verification_report.toml output requirements, and the r2 program spec. All required bases (inspected_code, executed_tests_with_output, inspected_docs, persisted_review_evidence) satisfied. No forbidden bases used.
