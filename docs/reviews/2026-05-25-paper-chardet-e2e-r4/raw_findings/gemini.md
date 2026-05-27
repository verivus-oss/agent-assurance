# paper-chardet-e2e-r4 — gemini raw findings

Job: 4e06454c-ced0-4a3b-a3be-54445b0a256d
Started: 2026-05-25T13:49:29Z
Finished: 2026-05-25T13:52:02Z
Exit: 0
Verdict: **unconditional_approval**

All Round 4 verification checks have been completed against commit `4c57fdd` (which incorporates the prose fix in `6d64887`).

### 1. §10.3 Intro Scoping (B3-overclaim closure)
The introductory sentence of §10.3 has been successfully rewritten to explicitly scope the `scipy` and `numpy` validation claim.

**Bytes verified (paper/main.tex:1022-1025):**
```latex
To guard against single-implementation error in any of the headline
numbers in \cref{tab:results}, we cross-validated AUX1 and the
C06a--d results against an independent re-implementation in scipy
and numpy~\cite{virtanen2020scipy,harris2020numpy}; C06e is handled
```
The "each number" overclaim from r3 has been removed and replaced with a specific enumeration of `AUX1 and the C06a--d results`.

### 2. Broad Grep Classification
Executed `grep -nE 'scipy|numpy' paper/main.tex`. All 9 hits are confirmed as acceptable per the r4 directive:

*   **Class A (Listing-specific):** Lines 578, 579, 1033, 1034, 1038 (Specific primitives for Cosine, Jaccard, Degrees).
*   **Class B (Scoped composite):** Lines 1024, 1025, 1564 (Explicitly scoped to AUX1 and C06a-d).
*   **Class D (Negative-clause):** Line 1028 ("no scipy or numpy primitive for [C06e]").
*   **Class C (Unscoped global):** **ZERO HITS.**

### 3. Triple-Agreement Consistency Audit (C06e)
The validation path for C06e (stdlib digest + subprocess + SKIP) is now internally consistent across the three critical locations:
1.  **§10.3 Intro (:1025-1029):** Mentions C06e is handled separately via stdlib digest + subprocess.
2.  **§10.3 C06e Paragraph (:1045-1060):** Details the `hashlib.sha256` construction, `fingerprint_behavior.py` subprocess, and `SKIP` semantics for isolated venvs.
3.  **Conclusion (:1562-1570):** Summarizes the split-validation strategy (AUX1+C06a-d via scipy/numpy; C06e via stdlib/subprocess/SKIP).

### 4. Numeric Validation Script Execution
Ran `python3 paper/figures/scripts/validate_numbers.py`:
*   **Exit Code:** 0 (Success)
*   **Output:** `all agree: True`
*   **C06e Details:** `c06e.corpus_digest` matched (`58e54831f84183c7`) and rates matched (`0.0`).

### 5. TeX Sanity and Regression Sweep
*   **Brace Balance:** 658 open / 658 close (0 balance).
*   **Em-dashes:** No new em-dashes introduced in the prose-fix area.
*   **Orphan Refs:** No broken `\cref`, `\cite`, or `\ref` found in the modified sections.
*   **Collateral Damage:** Confirmed via `git show 6d64887` that the fix was surgically applied to the §10.3 intro and did not revert or damage the r3-approved Conclusion or C06e paragraphs.

**VERDICT: unconditional_approval**
