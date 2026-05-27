# paper-chardet-e2e-r3 — gemini raw findings

Job: 895952a0-82a8-4db5-be87-885511d57b3e
Started: 2026-05-25T13:35:40Z
Finished: 2026-05-25T13:37:50Z
Exit: 0
Verdict: **concrete_unresolvable_blocker**

The Round 3 review of the `paper-chardet-e2e` arc is complete. My inspection of the bytes in `paper/main.tex` and the execution of the numeric validation script confirms that while the primary `B3-conclusion-overclaim` from Round 2 has been addressed in the Conclusion, a nearly identical overclaim remains in Section 10.3.

### Verification Results

1.  **Conclusion Scoping (Pass):** Lines 1560–1564 correctly distinguish between the validation paths for the different signals. It accurately scopes C06e as being validated via stdlib digest and a subprocess, rather than a global "scipy/numpy" claim.
    *   *Bytes:* `(AUX1 and C06a-d via scipy / numpy second-source primitives; C06e via a deterministic stdlib digest re-derivation plus a subprocess... with explicit SKIP semantics)`
2.  **Section 10.3 Scoping (Fail):** Grep and line-read of Section 10.3 reveal that the introductory sentence of the numeric validation section still makes a global, unscoped claim that "each number" is cross-validated against scipy and numpy. This is false for C06e (validated via subprocess/digest) and AUX1 (validated via stdlib `hashlib`).
    *   *Location:* `paper/main.tex:1020`
    *   *Text:* `we cross-validated each number against an independent re-implementation in scipy and numpy`
3.  **Substrate Intact (Pass):** The detailed description of C06e validation in Section 10.3 (lines 1039–1057) is accurate and matches the `validate_numbers.py` implementation.
4.  **Numeric Validation (Pass):** `python3 paper/figures/scripts/validate_numbers.py` was executed and all 26 checks passed, including the C06e corpus digest and measured match rates.
5.  **Corpus Digest (Pass):** Both `validate_numbers.py` and `paper/main.tex` (L1043) correctly describe the `b"\n".join(corpus)` hash construction, closing the Round 1/2 substrate defect.
6.  **TeX Sanity (Pass):** No Unicode em-dashes (`—` or `U+2014`) were found in the file.
7.  **Acknowledgments/Abstract (Pass):** No regressions found; mentions of Werner's role and the authoring process are preserved.

### Blocker Disposition

```toml
id            = "B3-section10.3-overclaim"
severity      = "concrete"
location      = "paper/main.tex:1020"
defect        = "we cross-validated each number against an independent re-implementation in scipy and numpy"
remediation   = "we cross-validated the AUX1 and C06a--d results against an independent re-implementation in scipy and numpy"
verified_via  = "grep -nE 'scipy|numpy' paper/main.tex"
```

While the Conclusion is now accurate, the overclaim in §10.3 constitutes a stale claim that contradicts the actual validation logic for C06e described later in the same section. Per the r3 directive, this is a blocker.

VERDICT: concrete_unresolvable_blocker
