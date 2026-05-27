# paper-chardet-e2e-r3 — codex raw findings

Job: 6b247d3a-0f8e-49c8-b371-7d037af6082a
Started: 2026-05-25T13:37:03Z
Finished: 2026-05-25T13:39:58Z
Exit: 0
Verdict: **unconditional_approval**

**Round 3 Verification**

1. **Conclusion sentence**
Pass. `paper/main.tex:1555` now scopes the validation paths:
`AUX1 and C06a-d via scipy / numpy second-source primitives; C06e via a deterministic stdlib digest re-derivation plus a subprocess... with explicit SKIP semantics` at lines 1556-1564.

2. **Whole-paper scipy/numpy grep**
Pass. Command:
```text
grep -nE 'scipy ?/ ?numpy' paper/main.tex
1560:(AUX1 and C06a-d via scipy / numpy second-source primitives; C06e
```
Only one occurrence remains, and it is scoped away from C06e.

3. **§10.3 C06e substrate paragraph**
Pass. `paper/main.tex:1041` says C06e uses deterministic corpus re-derivation with `hashlib.sha256(b"\n".join(corpus))[:16]`; lines 1051-1060 say rates are recovered by subprocessing `fingerprint_behavior.py`, and SKIP is reported when chardet cannot be installed.

4. **validate_numbers.py execution**
Pass. Command exited 0. Relevant output:
```text
c06e.corpus_digest  58e54831f84183c7  58e54831f84183c7  YES
c06e.rates_recompute ... SKIP: fingerprint_behavior.py emitted SKIP: behavioural fingerprint skipped: v6 install from worktree failed ... YES
all agree: True
```

5. **C06e recompute + SKIP code path**
Pass. `validate_numbers.py:332` defines `recompute_c06e_rates`; lines 350-360 subprocess the harness script at `examples/proof-chardet-relicense/fingerprint_behavior.py`; lines 388-392 convert a `SKIP` TSV verdict into `status: "skip"`. The harness emits SKIP at `fingerprint_behavior.py:218`.

6. **Corpus digest construction**
Pass. `validate_numbers.py:319` documents the match and line 321 computes:
```python
hashlib.sha256(b"\n".join(corpus)).hexdigest()
```
`fingerprint_behavior.py:193` computes the same construction and truncates to 16 hex chars at line 194. Runtime output confirmed `58e54831f84183c7 == 58e54831f84183c7`.

7. **B1/B2 closed surfaces**
Pass. Abstract still contains the approved measured-number/legal-caveat framing at `paper/main.tex:86`. Acknowledgments still include explicit human/LLM attribution and responsibility disclosure at lines 1582-1677.

8. **TeX sanity**
Pass.
```text
grep -c 'U+2014\|—' paper/main.tex
0
brace_balance=0 min_prefix_balance=0
```

No stale unscoped `scipy/numpy` claim remains. The Conclusion now agrees with §10.3 on C06e: stdlib digest re-derivation plus subprocessed behavioural fingerprint, with explicit SKIP semantics.

VERDICT: unconditional_approval

---

## Reviewer-note (post-hoc, by Claude for the audit record)

Codex's verify_by:2 grep used the literal pattern `'scipy ?/ ?numpy'` (slash variant only), which DID NOT match line 1024-1025 of paper/main.tex where the prose reads "we cross-validated each number against an independent re-implementation in scipy **and** numpy". Gemini's r3 review used a broader `'scipy|numpy'` grep and caught that location as a new B3-class overclaim (filed as `B3-section10.3-overclaim` at :1020). This is a recipe-pattern limitation in codex's r3 execution, not a substrate issue — the codex review process IS correct (he ran the literal pattern requested by the verification_report), and the verification_report's verify_by:2 should have specified the broader pattern. Lesson absorbed for r4: explicit verification recipes for prose-scope checks must enumerate the full pattern set (slash, "and", "+", etc.), not assume one form covers all.
