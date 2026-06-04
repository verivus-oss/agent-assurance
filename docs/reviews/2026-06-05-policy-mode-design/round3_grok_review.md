# Round 3 review — Grok (job 0e9ee444, 2026-06-04T16:53Z)

VERDICT: REVISE — 2 findings:
1. §7 shim block (DESIGN:218-224) omits --law-root /tmp/law on policy-mode invocations; gemini r1 law-file bypass (contract 2 verified_by names tools/review-request-dag.toml) re-enters via the executable spec the implementation would copy. Add --law-root to every invocation.
2. 'IDENTICAL vendor alternation' claim false: assistant only in pattern 1 (policy:43 vs :54); 'Generated with Assistant' does not reject; same false claim at policy:51 comment, VERIFICATION_REPORT:6, DESIGN:298. Align or correct.
Residual noted: DESIGN contract-1 prose still says 'ANY model or tool' (stale vs §10.5). Fresh-attack observation (not demanded): 'Co-authored-by: Grok Kasselman' rejects — vendor-name-as-human-name FP class not in matrix.
All six round-2 findings verified FIXED (disposition table with evidence); round-2b gemini items present except shim wiring; implementation may start after finding 1.
