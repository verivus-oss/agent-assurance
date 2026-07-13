# U10 implementation review verdict: grok (xAI Grok CLI, gateway job 0a898973-8be2-448b-9fc0-f4b110a7531d)

Round 1, completed 2026-07-12T22:05Z (host time), evidence-based: grok built both
primaries, ran the triad, the 25-case conformance corpus, the CI-style discover sweep,
and its own adversarial fixtures (/tmp/crfp-grok-adv, /tmp/crfp-grok-mini,
/tmp/crfp-grok-inv07) inside its dedicated worktree wt-grok.

Orchestrator adjudication: all four required fixes independently reproduced by the
orchestrator in the main checkout / wt-mine. The 79-vs-80 root cause was identified by
the orchestrator as the gitignored local file tools/werner-style-policy.toml, present
only in the author's dirty working tree; the committed tree (what CI sees) yields 79.

## FINAL VERDICT: APPROVAL WITH REQUIRED FIXES

1. Wrong discover count (80 -> 79)
   - Files: docs/planning/closure-record-form-promotion/research/02-verification-record.md (C03 bullet and Full-sweep section); CHANGELOG.md U10 entry (line 15)
   - Repro: python3 validators/validate_closure_root.py --discover . --exclude examples/negative --exclude conformance/cases/implementation-dag/invalid --exclude conformance/cases/api-snapshot/invalid (in a clean checkout; reports 79)
2. Overclaim: "byte-identical error sets" for INV07 (C04 evidence)
   - File: docs/planning/closure-record-form-promotion/research/02-verification-record.md
   - Repro: run rs/go/py profile validators on examples/negative/profile-descriptor-bad-closure-record.toml and diff the presence-enum line: rs ["required", "when-present"] vs go [required when-present] vs py ['required', 'when-present']
   - Fix: state verdict-identical / same INV07 finding set, or normalize the three formatters.
3. Undeclared U09 deviation
   - File: verification record Deviations section; U09 commit 2da8769 also modified .github/workflows/validate.yml, absent from the planned U09 file list in implementation-dag.toml.
   - Repro: git show --name-only 2da8769
4. U05 follow-up commit a2d6b92 without CHANGELOG entry
   - Repro: git show --stat a2d6b92 (touches only validators/validate_closure_root.py)

## Attack-surface checklist (grok)

1. Triad divergence: Verified verdict parity; presence-set message spelling differs across rs/go/py.
2. Pin resolution in every closure-validating mode: Verified (auto + provenance share the pin path; no escape when descriptors load).
3. U08 exclusions vs no-silent-negatives: Verified; exclusions printed; every examples/negative/* in CI negative-agreement; conformance invalids asserted by runner.
4. Extends dedup: Verified; single emission with child profile; INV07 duplicate rejection after union on all three.
5. INV07 parity: Verified reject parity (empty field, trailing dot, presence typo, non-array all rejected by all three); not byte-identical message text.
6. RKV03 boundary: Verified; py-kind rejects lingering digest; primaries accept at closure/provenance layer; boundary recorded in freeze 1.4 and kind descriptor.
7. spec.md 12.8.1 vs code: Verified (shape, sort, sha256-only, presence semantics, framework_profile rejection, no pin-free path).
8. CI coherence: Verified via local simulation of closure + key negative steps.
9. CHANGELOG/process: Finding (items 3 and 4 above); no bare kind =; versions pinned at 0.1.0 / 1; em dash only on a removed line.
10. Verification-record numbers: Finding (79 not 80); 25 conformance cases reproduces.

## Non-reproducible verification-record claims (grok)

- "80 conforming files" (record + CHANGELOG): actual 79 in a clean tree.
- "byte-identical error sets" on the INV07 fixture: same finding set, not byte-identical text.
- Deviations section omits U09's .github/workflows/validate.yml touch.

## Raw evidence highlights (from grok's own run in wt-grok)

- cargo build + go build succeeded; triad PASS on examples/minimal-api-snapshot.toml.
- make dagtoml-conformance: 25 cases, PASSED.
- Discover with CI excludes: 79 files PASS; rs/go --mode provenance on those 79: PASS.
- Negatives: bad-closure and witness-stripped rejected by all three closure impls;
  witness-lingering-digest: py-kind reject (RKV03), primaries closure-layer accept
  (auto rejects only via the deliberate source_bytes=621 provenance error).
- Adversarial: missing/unresolvable framework_profile reject; sha384 pin reject;
  when-present absent + 3-record root accept; posture flip root-stable; legacy
  meta.kind synonym still pin-resolved.
- Extends chain: single-emission accepted, double-emission rejected, re-declared pin
  rejected as INV07 duplicate after union, on all three.
