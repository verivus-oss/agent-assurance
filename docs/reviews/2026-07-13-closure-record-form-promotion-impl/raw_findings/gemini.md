# U10 implementation review verdict: gemini (Antigravity CLI, gateway job 6d015220-fd14-4d02-92ba-4dd99bf2dce4)

Round 2 dispatch (round 1, job d5707491, died at the agy 5-minute print timeout with no
output; relaunched with printTimeout 40m). Completed 2026-07-12T22:15Z (host time),
exit 0. Evidence-based: ran conformance, the CI-style discover sweep, synthetic triad
variants (sha384, legacy kind, unpinned kinds), synthetic INV07 variants, an extends
diamond, RKV03 boundary runs, and framework_profile rejection tests in its worktree
wt-gemini.

Orchestrator adjudication: both required fixes verified. Fix 2 (79 vs 80) matches grok
and the orchestrator's own reproduction. Fix 1 verified by the orchestrator: every
shipped api-snapshot fixture (conformance/cases/api-snapshot/{valid,invalid}, all
examples/negative/api-snapshot-*.toml) declares framework_profile =
"com.verivus.runtime"; no repo-persisted, CI-asserted fixture covers the frozen parity
matrix row "pinned kind, framework_profile missing/unresolvable -> reject". The
behavior itself is implemented and was verified by all three reviewers and the
orchestrator with ad-hoc fixtures; what is missing is persisted corpus coverage.

## FINAL VERDICT: APPROVAL WITH REQUIRED FIXES

1. Add a negative fixture testing rejection of a missing or unresolvable
   framework_profile on a pinned kind; spec.md 12.8.1 normative text is enforced in
   code but lacks shipped test coverage.
   - File reference: conformance/cases/api-snapshot/invalid/ (new fixture)
   - Repro: grep -ri "unresolvable framework_profile" conformance/cases/ examples/negative/  (no results)
2. Correct the sweep count claim.
   - File reference: docs/planning/closure-record-form-promotion/research/02-verification-record.md line 66
   - Repro: python3 validators/validate_closure_root.py --discover . --exclude examples/negative --exclude conformance/cases/implementation-dag/invalid --exclude conformance/cases/api-snapshot/invalid  (79 files, not 80)

## Attack-surface checklist (gemini)

1. Triad divergence: Verified, no divergence on constructed or existing fixtures.
2. Pin-resolution rule in auto AND provenance modes: Verified in rs and go.
3. U08 sweep exclusions: Verified; all exclusions asserted to fail.
4. Extends dedup: Verified via diamond hierarchy; identical closure_root, single emission.
5. INV07 parity: Verified; all three reject empty field, trailing dot, presence typo, non-array.
6. RKV03 boundary: Verified; py-kind rejects lingering digest, rs/go pass it under --mode provenance.
7. Spec text vs implementation: FINDING; framework_profile rejection enforced but untested by shipped fixtures.
8. CI coherence: Verified via local simulation.
9. CHANGELOG/process: Verified per gemini (note: grok found two process gaps here that gemini did not; grok's are evidence-backed and adopted in consolidation).
10. Verification record numbers: FINDING; 80 does not reproduce, actual 79.

## Non-reproducible verification-record claims (gemini)

- "closure discover 80 files": actual 79 under the U08 exclusions.
