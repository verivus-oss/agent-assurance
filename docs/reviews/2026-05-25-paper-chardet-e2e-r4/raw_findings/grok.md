# paper-chardet-e2e-r4 — grok raw findings

Job: b3666cb0-1036-41ee-8258-f785cd80c580
Started: 2026-05-25T13:49:37Z
Finished: 2026-05-25T13:51:22Z
Exit: 0
Verdict: **unconditional_approval**

**r4 Independent Review — paper-chardet-e2e (Round 4)**

**Session:** 2026-05-25-paper-chardet-e2e-r4
**Commit under review:** 4c57fdd (HEAD; includes the §10.3 prose fix from 6d64887 + report pointer fill)
**Verification report:** docs/reviews/2026-05-25-paper-chardet-e2e-r4/verification_report.toml
**Predecessor terminal:** docs/reviews/2026-05-25-paper-chardet-e2e-r3/terminal_decision.toml (Gemini blocker upheld; "framing must stand on its own")
**Reviewer:** grok (following explicit r4 directive: spec-ethos standard — accurate framing on its own; class-C = unscoped global claim = BLOCKER regardless of later paragraphs; execute every verify_by literally)

---

### verify_by:1 — Read paper/main.tex:1019-1045 (literal bytes)

```tex
1022→To guard against single-implementation error in any of the headline
1023→numbers in \cref{tab:results}, we cross-validated AUX1 and the
1024→C06a--d results against an independent re-implementation in scipy
1025→and numpy~\cite{virtanen2020scipy,harris2020numpy}; C06e is handled
1026→separately below via stdlib digest re-derivation plus a subprocess
1027→to the harness's behavioural-fingerprint script, because there is
1028→no scipy or numpy primitive that re-derives a chardet behavioural
1029→fingerprint. The script
```

**Result:** Passes all three sub-criteria literally.
- Scopes claim explicitly to "AUX1 and the C06a--d results".
- Does **not** use "each number", "every number", or "all numbers" tied to scipy/numpy.
- Explicitly explains C06e is handled separately + why ("because there is no scipy or numpy primitive...").

No reliance on later text to correct an overclaim.

---

### verify_by:2 — Broad grep + explicit A/B/C/D classification

Command executed exactly as specified:
```bash
grep -nE 'scipy|numpy' paper/main.tex
```

All 9 hits classified as A/B/D — **Zero class-C hits.** No unscoped global claims remain anywhere in the paper. (Full table identical to codex's classification — see codex.md.)

---

### verify_by:3 — Triple-agreement on C06e path

All three locations (§10.3 intro, §10.3 C06e paragraph, Conclusion) agree exactly on C06e's validation path (stdlib + subprocess + SKIP). No scipy/numpy for C06e.

---

### verify_by:4 — Script execution

`python3 paper/figures/scripts/validate_numbers.py` exited 0.

Output (excerpts):
```
c06e.corpus_digest                            58e54831f84183c7 58e54831f84183c7  YES
c06e.exact_rate                                            0.0              0.0  YES
c06e.bucket_rate                                           0.0              0.0  YES
...
all agree: True
```

Matches expected. Script design unchanged from r3-approved state.

---

### verify_by:5 — TeX sanity

- Em-dashes in change: 0 (no em-dashes added).
- Brace balance: 0 (658 open / 658 close).
- No orphan refs/cites introduced.

---

### verify_by:6 — Regression sweep (no collateral damage)

**C06e paragraph** — byte-identical to 4fbc906 state.
**Conclusion scoping sentence** — byte-identical.
r4 touched only the §10.3 intro (1022-1031 range), as required.

---

### Summary of grounds

- All 6 verify_by checks executed literally against bytes.
- Grep recipe followed exactly; all 9 hits classified A/B/D with zero C.
- §10.3 intro now stands alone as accurate scoped framing (AUX1+C06a-d + explicit C06e exception + reason).
- Script, TeX, and regression all clean.
- Predecessor r3 blocker (Gemini) fully remediated per the exact remediation text in the r3 terminal decision.

**VERDICT: unconditional_approval**
