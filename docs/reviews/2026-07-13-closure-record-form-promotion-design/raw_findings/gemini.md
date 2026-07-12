# Design review verdict: gemini (Google Antigravity CLI via llm-gateway)

Jobs: 0be8de94-f42b-452e-a913-018745201510 (round 1, completed 04:52:36Z), f70b15ea-39df-4fef-ae20-66de13005ae5 (round 2, completed 04:56:43Z).
Iterations: 2.

Round 1 verdict: BLOCKER (witness-stripping detection bypass via present=false lingering attestation_sha256).
Round 2 (after the orchestrator confirmed the finding with file evidence and asked for the clearing amendment): the blocker converts to a required fix conditional on a specific U02 amendment.

FINAL VERDICT: APPROVAL WITH REQUIRED FIXES

## Required fixes (gemini's enumeration)

1. Amend the design/U02 freeze to require kind-layer rejection of residual witness digest fields when snapshot.witness.present = false (resolution option (a): closure stays purely field-presence-based; RKV03 gains a MUST NOT for lingering witness digests). Evidence: validate_api_snapshot.py:229-251 enforces witness fields only when present=true; attestation_sha256 is in ALLOWED_WITNESS_KEYS (line 75); api-snapshot-kind.toml RKV03 permits lingering fields. Without this, a present=false downgrade keeps the record set and root identical, bypassing witness-strip detection.
2. Assign a new invariant ID (the proposed "new INV06" collides with the existing INV06 at core/profile-descriptor-kind.toml:214-220); expand U04 to include the Rust and Go primaries (main.rs:3032-3132 hardcodes INV01-INV05 enforcement) and update core/profile-descriptor-kind.toml in the same change per the move-together rule.
3. Correct 01_design.md section 3.5: the four-record root over the shipped digests mathematically equals sha256:013f3d34bab26a1b9d9fd77ff03aae76a3b07ee112c4995dc5ef448b2d1796db (gemini reproduced the sorted stream and sha256sum independently); the "do not reuse" guidance is incorrect since the digests are unchanged.
4. Amend U02 to mandate hard rejection of an unresolvable framework_profile during closure evaluation regardless of namespace. Evidence: main.rs:4114-4140 hard-rejects missing descriptors only for unprefixed names; reverse-DNS names like com.verivus.runtime are downgraded, so a silent "no pins" fall-through would validate a stripped document against the 1-record root (pin bypass).

## Cross-check of the other reviewer's findings

- INV06 collision: VALID (verified in core/profile-descriptor-kind.toml).
- U04 under-scope for triad parity: VALID (verified in main.rs profile validation).
- 013f3d34 recompute: VALID (independently recomputed).
- Reverse-DNS downgrade strengthening the matrix-row finding: VALID, escalated to a pin-bypass vector.

## Round 1 attack-surface summary (1-10)

1 sound (TOML bare keys forbid spaces/newlines; double-pin rejection plus duplicate-pin rejection is collision-free); 2 misstated in the design (closure paths never read framework_profile); 3 sound (four shipped profiles, none pin; profile-less documents bypass the new logic entirely); 4 broken via the present=false lingering-field downgrade (round 1 blocker, now fix 1); 5 sound (INV lands before pins; triad merges before U08; U08 atomicity aligns with move-together); 6 verified (runner.py PY_VALIDATORS never invokes validate_closure_root.py, U09 necessary); 7 exact root cause of the C02 bypass; 8 verified compliant; 9 sound ([redacted: private-repository facts, verified at file level]); 10 properly scoped.

## Unassessable (pre-implementation)

The witness-stripped negative fixture (planned in U08); conformance/cases/api-snapshot fixtures (U09); the U02 sweep and freeze artifact; [internal-repository publish-gate items redacted].

## Evidence basis

Read the bundle files and ground truth in both repos; reproduced the closure-stream computation; verified line-level behavior of the kind validator, the three closure implementations, and the profile checks.
