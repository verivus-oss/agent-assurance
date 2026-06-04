# Round 1 review — Grok (job e8c6f0a7, 2026-06-04T16:32Z)

VERDICT: REVISE — findings (verbatim from reviewer output, full text in gateway flight recorder, correlationId a4a6ed1b-6c6c-44fe-9914-362958b9e39e):

1. DESIGN.md §1 overstates "#21–#25 carry no docs/reviews/ bundle": PR #21 merge includes docs/reviews/2026-05-29-wp1-validator-ports/ (git show, name-only). #22/#24/#25 confirmed bundle-free. #23 absent from branch history.
2. tracked_files false-positives the design bundle itself: pattern 3 matches VERIFICATION_REPORT.md:56 quoted PASS line; exemptions cover only policy file + conformance/cases/policy/**. Artifact needed: exempt docs/reviews/** or restrict pattern to commit/PR streams.
3. REG:NO-INITIATOR-SELF-APPROVAL underspecified: match_mode="structural" with no algorithm in DESIGN.md §5 for gate_decision_artifacts or --initiator inequality; no structural handling anywhere in validator sources.
4. Undeclared overlap with existing .github/workflows/no-ai-attribution.yml (origin/main): design never states whether it is retired, subsumed, or dual-run; risk of divergent patterns and duplicate gates.
5. §8 not a "small runner extension": conformance/runner.py:33-35 registers only implementation-dag; cases are single-toml-fixture shaped (runner.py:96-118); runner treats exit 2 as infrastructure failure (runner.py:125-128) while §5/§8 require exit 2 as an EXPECTED fail-closed outcome — contradictory without runner redesign. Artifact needed: policy fixture schema + expected-exit sidecar.
6. Coverage gaps: applies_to omits pr_title; reverts quoting old stamped bodies match (tested, undocumented); human @users.noreply.github.com latent FP risk on pattern 2.
7. N−1 sound in steady state; stage-0 is the real hole: a single bootstrap PR can land permissive policy/exempt_paths/ignoring code judged only by legacy gates. Mitigation artifact: two-PR bootstrap (law first, enforcement second) + stage-0 scope cap; not present in design.
8. REG: prefix confirmed declared (core/ontology.toml:76-79, "Legal, policy, or regulatory obligation") — semantically a deliberate stretch, acceptable for v1 if documented.
9. Behaviour table reproduced independently across py/rs/go engines; caveat = finding 2.
10. Git-history scan of origin/main with the three patterns: 0 matching lines; policy would not break existing main history, but WOULD break the design session's own verification report under tracked_files.

Verified: C1 (3/3 validators pass, re-run), C2 (rs+go pass), C4 (RE2 lookbehind/backref rejection confirmed by compile errors), C6 (CONTRIBUTING.md:49-67 wording; review-request-dag.toml:77-94 [policy.approval]).
