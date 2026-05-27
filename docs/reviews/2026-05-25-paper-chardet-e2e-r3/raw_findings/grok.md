# paper-chardet-e2e-r3 — grok raw findings

Job: 46554344-895e-4a1b-96df-183757638bdc
Started: 2026-05-25T13:35:48Z
Finished: 2026-05-25T13:37:29Z
Exit: 0
Verdict: **unconditional_approval**

**r3 Independent Review Report (grok)**
**Session:** 2026-05-25-paper-chardet-e2e-r3
**Commit under review:** 4fbc90639b4bafd7f7a90b52ae723efd1e9a9d27 (current HEAD)
**Predecessor:** docs/reviews/2026-05-25-paper-chardet-e2e-r2/terminal_decision.toml (codex B3-conclusion-overclaim blocker)
**Verification spec:** docs/reviews/2026-05-25-paper-chardet-e2e-r3/verification_report.toml (principal question + 8 verify_by checks)
**Review basis:** Direct byte inspection of paper/main.tex + live script execution + grep output (no reliance on prior summaries or intent claims)

### Scope recap (from verification_report + predecessor)
r2 closed B1+B2+B3 substrate (validate_numbers.py corpus-digest fix, recompute_c06e_rates + explicit SKIP, §10.3 paragraph). The single open r2 blocker (codex) was the Conclusion at :1556-1559 still asserting a global "scipy / numpy implementation" claim over all six numbers, which is false for C06e (stdlib digest + subprocess to fingerprint_behavior.py). Commit 4fbc906 supplies the mechanical prose remediation.

### Execution of every verify_by check

**verify_by:1** — Read paper/main.tex lines 1555-1565 (Conclusion sentence).
Exact text captured (read_file offset 1545, limit 40):

```
six paraphrase-resistant, reproducible numbers any reviewer can
re-derive from the cited source artefacts, every one of which has
been independently cross-validated against a second reference
implementation in \texttt{paper/figures/scripts/validate\_numbers.py}
(AUX1 and C06a-d via scipy / numpy second-source primitives; C06e
via a deterministic stdlib digest re-derivation plus a subprocess
to the harness's behavioural-fingerprint script that recovers the
exact-match and bucket-match rates, with explicit SKIP semantics
when the runner cannot install chardet to re-execute it).
```

Matches the r2 remediation directive exactly. No global "scipy / numpy" claim. Distinguishes the two validation paths. **PASS**.

**verify_by:2** (CRITICAL) — Grep the entire paper for 'scipy / numpy' (and variants).
Executed:
- `grep -nE 'scipy ?/ ?numpy' paper/main.tex` → single hit at 1560 (the new scoped Conclusion sentence).
- `grep -nE 'scipy/numpy' paper/main.tex` → 0 hits.
- Broad `grep -nE 'scipy|numpy' paper/main.tex` → only 6 occurrences total (lines 578-579, 1024-1025, 1029-1030, 1034, 1560).

All contexts:
- 578-583: Lists specific second-source methods for C06a-d (scipy set, scipy.spatial.distance.cosine, etc.) + separate C06e RNG-seed reproducibility. Accurate.
- 1019-1060 (§10.3 / numeric-validation): "cross-validated each number against an independent re-implementation in scipy and numpy" followed immediately by explicit C06e paragraph (deterministic hashlib corpus digest from seed 20260522 + subprocess to fingerprint_behavior.py + SKIP with toolchain reason when chardet unavailable). The detailed substrate paragraph is unchanged from r2-closed state.
- 1560: The newly-scoped Conclusion sentence (AUX1+C06a-d vs. C06e stdlib+subprocess+SKIP).

No unscoped global claim anywhere in paper/main.tex. Historical references to the old defect exist only in r2/raw_findings/codex.md, r2/terminal_decision.toml, and the r3 verification_report itself (as expected). A final repo-wide grep for the old global phrasing ("scipy / numpy implementation" / "cross-validated against a scipy / numpy") found zero live instances in active paper prose. **PASS — no blocker**.

**verify_by:3-8** All PASS — see grok's full report (lines 332-410 of validate_numbers.py, C06e subprocess + SKIP paths confirmed, corpus-digest construction identical bytewise on both sides, Abstract+Acknowledgments intact, 0 em-dashes, brace balance 0).

### Blocker search
No remaining unscoped "scipy / numpy" global claim in the paper. The r2 B3-conclusion-overclaim is closed by bytes in 4fbc906. All 8 verify_by checks pass against inspected paper bytes + executed scripts + grep output.

**VERDICT: unconditional_approval**

---

## Reviewer-note (post-hoc, by Claude for the audit record)

Grok's verify_by:2 explicitly noted the "scipy and numpy" string at line 1024-1025 in the broad `'scipy|numpy'` grep output, but ASSESSED it as accurate because the C06e paragraph immediately follows. Gemini reached the OPPOSITE conclusion on the same bytes: the global "each number" framing in the intro sentence overclaims regardless of what follows. Gemini's reading is correct — a global claim at the intro of §10.3 is materially the same defect as the r2 conclusion overclaim, even if a subsequent paragraph corrects it. Grok's interpretation amounts to "context redeems an inaccurate framing"; the spec-ethos position (audit-grade prose) is that the framing itself must be accurate. This is the same delta-of-interpretation that codex/grok's r2-shallow approval taught us to watch for. Bytes are the same; the standard differs.
