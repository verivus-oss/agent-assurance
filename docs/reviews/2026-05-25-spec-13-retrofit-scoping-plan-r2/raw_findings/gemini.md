## Summary

U08 is **complete** and successfully addresses all three blockers identified in Round 1. Commit `073d5c5` modifies `docs/planning/2026-05-25-spec-13-retrofit-scoping.md` to reclassify the selective-disclosure-proof (SDP) as Family A, reframes the abstraction-class taxonomy as a role-level label rather than a structural contract, and resolves the internal contradiction regarding `closure_root` persistence. The plan now aligns with the repository's validator vocabularies and SPEC §12 requirements. Terminal classification: `unconditional_approval`.

## U08 — 073d5c5

I verified the changes in commit `073d5c5` against the repository's code, validators, and existing descriptors. The commit is a surgical update to the planning document that incorporates the Round-1 feedback while preserving historical context for audit purposes.

- **Selective-disclosure-proof (SDP)**: Reclassified from Family C to Family A at line 232.
- **Taxonomy Reframe**: The preamble in §6 (lines 151-159) now explicitly states that class IDs are producer-attested role labels.
- **Closure Root**: The "MUST flip" contradiction was removed; §9 (lines 249-272) now coherently explains why the empty-closure sentinel persists for self-contained descriptors.

## U07-F1 disposition

**Status: Closed.**

- **SDP Family A**: Plan row 18 (line 232) correctly classifies `selective-disclosure-proof` as Envelope family `A`.
- **Invalid Vocabularies Removed**: I searched the document for `entropy_source = "system"`, `sign`, and `verify`. These appear only at lines 142-149 within a historical-explanation paragraph (§5) documenting why the Family C proposal was rejected after r1 review. They are no longer proposed as live fields.
- **Validator Verification**: I inspected `validators/validate_abstraction_class.py:180-225`. Line 185 confirms `entropy_source` must be one of `os | deterministic_seed | none`. Lines 217-221 confirm `crypto_keys` supports `read_keys`, `use_keys`, and `generate_allowed`. The r1 finding that the original plan was validator-incompatible is correct, and the r2 fix correctly moves the kind to Family A to avoid these fields.

## U07-F2 disposition

**Status: Closed.**

- **Taxonomy Reframe**: §6 preamble (lines 151-159) now states: "A class id is a producer-attested **label** for the artefact's role... it is NOT a byte-level structural-shape contract."
- **Observation-record.v1 Generalisation**: The table at line 161 now describes the role as "Read-only observation of a past state, action, or outcome; each kind declares its own structural shape." The specific "closed-vocab... integer quantities" language (which only fit `cost-record`) has been removed from the shared description.
- **New Per-Kind Rule**: A new "Per-kind description field rule" appears at lines 185-191, mandating that each kind's `description` field MUST reflect its own structural shape.
- **Canonical Shape Citation**: `profiles/cost/cost-record-kind.toml:282-286` is correctly cited at line 191 as the reference shape for Phase 1+2 retrofits.

## U07-F3 disposition

**Status: Closed.**

- **"MUST flip" Removal**: `grep -n 'MUST flip'` on the modified plan returned zero matches.
- **Coherent Statement**: §9 (lines 249-272) provides a single, clear explanation: the sentinel persists per SPEC §12.1/§12.11 for self-contained descriptors (like those at HEAD).
- **SHA-256 vs Closure Root**: The plan now correctly distinguishes between the descriptor file's SHA-256 (which changes) and its declared `closure_root` (which remains at the sentinel).
- **SPEC Tension Acknowledged**: The contradiction between SPEC §13.4 and §12.1 is documented as an out-of-scope follow-up (ISS-005 candidate) in §11 (lines 280-282).

## No new defects

- **File Scope**: `git show --stat 073d5c5` confirms only `docs/planning/2026-05-25-spec-13-retrofit-scoping.md` was modified. No other files were touched.
- **Validator Health**: `python3 validators/validate_closure_root.py --discover .` exited 0, confirming the repository remains in a valid state.
- **Ancestry**: `c88f7ea` is a direct ancestor of `073d5c5`.
- **Revision History**: §13 (lines 294-298) accurately records the Round 2 fixes.
- **Open Questions**: Q4 (SDP envelope) was dropped. Q2 (taxonomy) was reworded at line 285 to match the role-level definition.

## Process checks

- `confirm_active_user_migration_or_behavior_change_guidance`: **Confirmed.** The plan itself serves as the migration guidance for the §13 retrofit.
- `confirm_no_historical_dated_spec_retconned_without_link_or_correction_note`: **Confirmed.** No historical spec files were modified in this commit.
- `confirm_claimed_tests_were_actually_run_with_command_output_and_status`: **Confirmed.** I executed the closure-root validator and verified the abstraction-class validator's source code to confirm vocabulary constraints.

## Terminal verdict

**unconditional_approval**

Rationale: Commit `073d5c5` is a high-quality resolution of the r1 blockers. It demonstrates rigorous adherence to the repository's existing validators and SPEC §12 logic. By reframing the abstraction-class taxonomy as an artefact-level role, it preserves the utility of shared class IDs while respecting the structural diversity of the underlying kind descriptors. The plan is now ready for implementation.
