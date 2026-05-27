# paper-chardet-e2e-r4 — codex raw findings

Job: 117102a6-b2d7-44ec-b7b7-7f808ba848fd
Started: 2026-05-25T13:49:19Z
Finished: 2026-05-25T13:52:26Z
Exit: 0
Verdict: **unconditional_approval**

**Review Result**

Verified bytes at `HEAD = 4c57fddd17aa906632aaf71d6f8d274f38f3a1bb`. Note: the r4 report's `head_commit` field reads `6d64887`, not `4c57fdd`; I treated the working-tree HEAD bytes as authoritative per the prompt.

**Checks**

1. `paper/main.tex:1019-1045` passes. The intro scopes SciPy/NumPy validation to `AUX1` and `C06a--d`, avoids "each/every/all number" global framing, and says C06e is handled separately via stdlib digest re-derivation plus subprocess.

2. `grep -nE 'scipy|numpy' paper/main.tex` classifications:

| Line | Hit | Class |
|---:|---|---|
| 578 | C06b Jaccard via scipy set primitive | A |
| 579 | C06c cosine via `scipy.spatial.distance.cosine` | A |
| 1024-1025 | AUX1 and C06a--d via scipy/numpy | B |
| 1028 | no scipy or numpy primitive for C06e fingerprint | D |
| 1033 | C06c cosine via scipy primitive | A |
| 1034 | Jaccard via scipy primitive | A |
| 1038 | mean/max degrees via numpy | A |
| 1564 | Conclusion scoped composite: AUX1 and C06a-d via scipy / numpy; C06e separately | B |

Zero Class-C hits.

3. Triple agreement passes. The intro, C06e paragraph, and Conclusion all keep C06e out of SciPy/NumPy validation and describe the separate stdlib digest plus subprocess path; the C06e paragraph and Conclusion include explicit SKIP semantics.

4. `python3 paper/figures/scripts/validate_numbers.py` exited 0. Output included `c06e.corpus_digest` matching `58e54831f84183c7`, `c06e.rates_recompute` as `SKIP`, and `all agree: True`.

5. TeX sanity passes: em-dash grep found 0 hits, brace balance is `0`, parsed refs/cites show `missing_refs 0` and `missing_cites 0`.

6. Regression sweep passes. Compared against `4fbc906`: C06e paragraph hash matched, Conclusion validation sentence hash matched, and `git diff --unified=0 4fbc906..HEAD -- paper/main.tex` shows only the §10.3 intro/proximate transition edit.

No concrete blocker found.

VERDICT: unconditional_approval

---

## Reviewer-note (post-hoc, by Claude for the audit record)

Codex correctly noted that the r4 verification_report's head_commit was written as `6d64887` but the working-tree HEAD was `4c57fdd` — that's because I wrote the r4 verification_report BEFORE the trivial head_commit pointer fixup commit, and codex treated working-tree HEAD as authoritative. This is the correct behavior. The r4 verification_report file at `4c57fdd` actually contains `head_commit = "6d64887"` (still pointing to the §10.3 prose commit), and `4c57fdd` is only the head_commit pointer fixup — so substantively codex was reviewing the right bytes regardless. No defect; documenting for the audit trail.
