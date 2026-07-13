# Design review verdict: codex (OpenAI Codex CLI via llm-gateway)

Jobs: e678321e-0cf6-4ce7-82f0-50c14de9e5b1 (round 1, 21 min deep review, completed 05:09:12Z), e58ebde1-5f83-4c80-b6be-17f818262645 (final-message reprint), 7a3059b7-6ce7-48b6-9bb6-3c0438a23912 (round 2 convergence, completed 05:16:45Z). Codex session 019f54a7-6692-73f0-95c4-e1f5c7f01fa6.
Iterations: 2.

Round 1 verdict: BLOCKER (witness-state binding bypass).
Round 2: blocker converts with a concrete U02 amendment; one finding (TOML whitespace evasion) partially retracted after rebuttal.

FINAL VERDICT: APPROVAL WITH REQUIRED FIXES
Enumerated: (1) witness-state rule and conformance scope; (2) canonical declaration grammar and target policy; (3) spec, descriptor, and triad reconciliation; (4) fixture and CI cutover corrections; (5) internal DAG and carve-out gate corrections.

## Round 1 findings (all verified by the orchestrator unless noted)

1. BLOCKER (now fix 1): closure emission is field-presence-based while RKV03 permits lingering witness fields at present=false (api-snapshot-kind.toml:169, validate_api_snapshot.py:227). Flipping present to false while retaining attestation_sha256 preserves all four records and the root. Round-2 amendment accepted: RKV03 rewritten so present=false requires witness digest/identity fields absent, enforced at the kind layer, plus a lingering-digest negative fixture. Scoping caveat codex added: Rust and Go do not implement RKV03 today, so that fixture is a Python kind-layer rejection unless RKV03 is ported; the table-removal stale-root fixture remains the all-three closure test.
2. Label grammar under-specified; additionally the design does not exclude pinning closure_root itself (self-referential hash). Round 2: the TOML dotted-key whitespace argument was overstated (field is a decoded string scalar); agreed fix is a byte-frozen regex such as ^[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*$ over the decoded string, segment-wise lookup, same normalized value as emitted label, plus exclusions: closure_root, meta.*, posture fields, provenance.source_sha256.
3. INV06 collides with existing INV06 (core/profile-descriptor-kind.toml:214); no DAG unit updates the machine-readable profile-descriptor contract; U04 changes Python only despite native rs/go profile validators; extends behavior and duplicate profile-name handling undefined.
4. Normative scope not reconciled: spec.md section 12.1 (around line 976) still limits profile-layer inputs to cites_upstream, evidence, and revocation; U03 omits the 12.1 amendment; pin grammar sha256-only conflicts with kind fields permitting sha256/sha384/sha512 (api-snapshot-kind.toml:133).
5. Matrix row "framework_profile unresolvable -> reject (existing behavior)" is false: all three closure constructors read only provenance (validate_closure_root.py:61, main.rs:3973, main.go:2427); native framework checks are separate auto/meta-mode behavior (main.rs:4182, main.go:3032). Recast as new frozen policy including aliases, reverse-DNS names, and modes.
6. U08/U09 cannot pass CI as listed: CI closure-validates every blessed TOML including examples/negative (validate.yml, closure discover step; no negative-directory exclusion in validate_closure_root.py discovery). The four blessed api-snapshot negatives (bad-subpart-digest, inlined-secret, raw-header, witness-incomplete) need re-rooting but are absent from U08 files_modify; the old bad-closure fixture is unblessed (template_kind api-snapshot-bad-closure) so it receives no pin. Define the expected-failure fixture convention and include all affected paths in the DAG.
7. Public-process compliance: the public bundle cites the "ADACG mapping document" and "ADACG reviewer" (01_design.md:17, README.md:19-20) though ADACG appears nowhere else in the public repo (internal-only referent); CHANGELOG work is listed only in U03/U08 while the plan calls for stacked per-unit PRs and the repo rule is every-PR.
8. [REDACTED: finding concerns the private downstream repository's sequencing bundle; persisted unredacted in that repository's planning records. Public-relevant remediation: unit ids in that bundle violated the public ontology id pattern (core/ontology.toml:133, extensible = false) and were rejected by both primaries while the Python DAG validator passed them (it performs no IJB entity-pattern check); remediated by renaming to the U-prefixed pattern.]
9. [REDACTED: finding concerns the private downstream repository's sequencing bundle; persisted unredacted in that repository's planning records. Public-relevant remediation: its evidence-rollup leaf encoding and validator-ref pinning gaps were remediated in that bundle.]
10. ADVISORY: critical-path prose (U03) vs computed (U04) mismatch; the new README omits the validation recipe present in the cited house bundle.

## Attack-surface summary

1 not sound until the grammar is byte-frozen; 2 false as written; 3 holds for shipped profiles, no-profile byte identity UNASSESSABLE; 4 blocked by the present=false gap (now amended); 5 correct weighted path but fixture inventory breaks CI mid-stack; 6 confirmed, runner.py never invokes Python closure (runner.py:37, 115); 7 kind/closure semantic gap; 8 no bare kind, versions pinned, review dispatch declared but not evidenced, ADACG and CHANGELOG defects; 9 [redacted: private-repository facts, verified correct]; 10 under-scoped declaration policy vs non-goals.

## Unassessable

U02 freeze decision, compat sweep, operator sign-off, U01/U10 review evidence; all new closure/profile-loader implementations and C01-C06 evidence; byte-identical no-profile behavior and actual witness-strip detection across the triad; [internal-repository sequencing items redacted].

## Evidence basis

21-minute tool-driven review with file reads across both repos, TOML grammar cross-check against the vendored BurntSushi v1.1.0 spec, and live execution of both primary validators against the private downstream bundle's DAG document. Round-2 answers included reproduced command output.
