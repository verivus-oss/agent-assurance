# Design review verdict: grok (xAI Grok CLI via llm-gateway)

Job: 5b4dd59b-8982-4af8-9a97-12e6d006efcd, completed 2026-07-12T04:52:40Z.
Iterations: 1 (single pass; all findings independently verified by the orchestrating agent, no contested items).

FINAL VERDICT: APPROVAL WITH REQUIRED FIXES

## Required fixes (grok's enumeration, verbatim in substance)

1. Renumber the closure-records invariant from INV06 to INV07 (or next free id); update kind descriptor and all pack references. Evidence: core/profile-descriptor-kind.toml:215-219 already defines INV06 (IJB ontology-resolution invariant, enforced_by validate_ijb_conformance.py) vs 01_design.md:81, implementation-dag.toml:90.
2. Expand U04 beyond validators/validate_profile_descriptor.py: add the hard invariant to core/profile-descriptor-kind.toml and port the pin checks to rs/go (main.rs:3032-3126 and main.go:2691-2769 already enforce INV01-INV05 natively), or explicitly freeze Python-only and accept the C04 divergence.
3. Rewrite the failure-mode matrix row "framework_profile unresolvable -> reject (existing behavior, unchanged)" (01_design.md:156) as a NEW U02-frozen closure rule. Python closure never reads framework_profile; rs/go check it on separate paths; reverse-DNS names (including com.verivus.runtime) are NOT rejected when the descriptor is missing (main.rs:4129-4133, main.go:2525-2531). Silent "no pins" fall-through on a missing descriptor is a pin bypass.
4. Byte-freeze the bare-key path grammar (segment charset, no leading/trailing/double dots, table-walk rules, no array indices unless specified) and specify closure_records inheritance across extends.
5. Specify when-present vs snapshot.witness.present=false with a residual attestation_sha256 (kind layer allows the lingering key: validate_api_snapshot.py ALLOWED_WITNESS_KEYS line 75, checks only when present=true at lines 234-251). Options: field-presence emission with a new kind rule rejecting residual witness digests; or presence gated on witness.present; or accept the dual semantics explicitly.
6. Correct the 013f3d34 guidance in 01_design.md section 3.5: independent recompute of the four labeled records over the shipped examples/minimal-api-snapshot.toml digests yields exactly sha256:013f3d34bab26a1b9d9fd77ff03aae76a3b07ee112c4995dc5ef448b2d1796db, the very value at examples/negative/api-snapshot-bad-closure.toml:26. The positive example SHOULD become that value; the negative should move to a source-only root.
7. Freeze the pin digest alphabet: design pins sha256-only records while kind digest fields accept sha256|sha384|sha512 (validate_api_snapshot.py:67-68).

## Advisories

- U05/U06/U07 "merge together" is process-only, not DAG-enforced (no mutual edges); same pattern as toml-1.1, acceptable if stated.
- computed.critical_path omits U03 while 03_implementation_plan.md:30 prose includes it; both are valid longest paths (by LOC the U04 path is the max, 800 LOC checks out); reconcile for operators.
- U09 files_create is empty despite promising new conformance/cases/api-snapshot/ trees; bookkeeping only.
- Positive: no bare kind field; no internal-name leak in the public pack; version pins correct; U01/U10 independent review dispatch present; CHANGELOG in U03/U08.

## Attack-surface summary (1-10)

1 conditionally sound (needs byte-frozen path grammar); 2 misstated (see fix 3); 3 holds (only 4 shipped profiles, none pin today); 4 works for field removal, gap for the present=false half-strip; 5 no mid-stack CI break under the stated depends_on graph; 6 confirmed, runner.py never invokes validate_closure_root.py; 7 gap (fix 5); 8 mostly pass, INV id fail; 9 internal gating sound, [redacted: private-repository facts, all verified at file level]; 10 aligned with non-goals.

## Unassessable (pre-implementation)

U02 freeze decision and compat sweep; docs/reviews/ evidence; live triad behavior; conformance cases; INV07 fixtures; witness-stripped fixture bytes; [internal-repository sequencing and publish-gate items redacted].

## Evidence basis

Read the 12 bundle files plus spec.md, all three closure implementations, profile artifacts, conformance/runner.py, CI workflow, and the private downstream repository sources; independently recomputed the four-record closure root.
