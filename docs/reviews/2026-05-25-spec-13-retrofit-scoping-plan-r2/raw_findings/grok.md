## Summary

U08 is **complete**. Commit `073d5c5` closes all three codex r1 blockers (U07-F1, U07-F2, U07-F3) with direct byte-level changes in the single modified file. Verified via executed commands (git ancestry, `validate_closure_root.py --discover .`, `validate_abstraction_class.py`, `grep -n 'MUST flip'`, Family C grep), full plan read, validator source at the exact lines codex cited (`validate_abstraction_class.py:182,214`), and cross-checks against the cited kind descriptors. No new defects. Terminal classification: `unconditional_approval`.

## U08 — 073d5c5

Single commit, single file modified. All three blockers addressed in `docs/planning/2026-05-25-spec-13-retrofit-scoping.md`:
- U07-F1: SDP row 18 now Family A; invalid envelope fields removed from live proposals.
- U07-F2: §6 taxonomy reframed as role label; per-kind description rule added; observation-record.v1 generalized.
- U07-F3: §9 contradiction removed; single coherent sentinel statement + ISS-005 filing.

Cross-cutting: §11 gains ISS-005 item; §12 Q4 dropped and Q2 reworded; §13 revision history added. All changes verified against bytes and executed validators.

## U07-F1 disposition

**closed**

- Plan row 18 at 232: `selective-disclosure-proof` | `cryptographic-proof.v1` | **A** | "SPEC-layer parse is shape-only per `selective-disclosure-proof-kind.toml:61`; all cryptographic work is RUNTIME-SPEC..."
- §5 historical paragraph (141-154) contains the only surviving "Family C" / `entropy_source = "system"` / `sign`/`verify` references: explicitly framed as "Earlier draft proposed... but round-1 review caught two defects" with direct citations to `selective-disclosure-proof-kind.toml:61` and `validate_abstraction_class.py:182` / `:214`.
- Executed: `grep -nE 'Family C|entropy_source.*system|crypto_keys.*verify|crypto_keys.*sign' ...` returned exactly two matches (142,148), both inside the explanatory paragraph.
- Validator source read at 182 (`_check_domain_random`: only `os | deterministic_seed | none`) and 214 (`_check_domain_crypto_keys`: only `read_keys | use_keys | generate_allowed`).
- SDP descriptor read at 61-62: "The SPEC layer enforces shape only. Verifying the proof against the published bytes is RUNTIME-SPEC." Matches codex r1 citation exactly.

## U07-F2 disposition

**closed**

- §6 preamble (167-177): "A class id is a producer-attested **label** for the artefact's role; it is shared across kinds that share that role at a coarse level. The class id is NOT a byte-level structural-shape contract — each kind's own `[[kind.required_fields]]`... remain the structural rule, and each kind's `[kind.abstraction_class].description` field MUST reflect that kind's specific shape."
- Table column renamed (182): "Role at the artefact level (NOT a byte-level shape)".
- observation-record.v1 row (184): now generalized ("Read-only observation of a past state, action, or outcome; each kind declares its own structural shape.").
- New rule (201-209): "Per-kind `description` field rule: when a kind declares `[kind.abstraction_class].id = "<shared-id>"`, the `description` field MUST be kind-specific... Cost-record's existing description at `profiles/cost/cost-record-kind.toml:282-286` is the shape..."
- Cost-record description read at 282-286 (exact match to plan citation).
- Cross-checks executed/inspected: `evidence-matrix-kind.toml:90-106` (claims/evidence/matrix), `gate-decision-kind.toml:95-112` (verdict/evidence_root), `assertion-log-record-kind.toml:95-114` (record.index/prev_hash), `redaction-manifest-kind.toml:83-87` (`[[redactions]]`). All differ structurally from cost-record. `validate_abstraction_class.py` still passes (19 files).

## U07-F3 disposition

**closed**

- Executed: `grep -n 'MUST flip' docs/planning/2026-05-25-spec-13-retrofit-scoping.md` → exit 1, zero matches.
- §9 (299-322) now single coherent block: "the canonical empty-closure sentinel ... **persists** across the retrofit. Per `SPEC.md §12.1` and `§12.11`... The cost-record example at HEAD ... confirms this... What *does* change post-retrofit is the descriptor file's SHA-256... (`SPEC.md §13.4` arguably reads as the descriptor's own closure_root flipping; ... filed as a separate issue candidate — see Section 11.)"
- §11 (349-356) explicitly files the §13.4-vs-§12.1 tension as **ISS-005 candidate**.
- Executed: `python3 validators/validate_closure_root.py --discover .` → "CLOSURE-ROOT VALIDATION PASSED (74 file(s))." (also passes on cost-record at 15, which carries the sentinel post-§13 block).
- §12 Q4 (SDP envelope) dropped; Q2 reworded (363-369) to match the reframed "producer-attested role" claim and explicitly notes the round-1 correction.

## No new defects

- `git show --stat 073d5c5` and `git show 073d5c5 --name-only`: only `docs/planning/2026-05-25-spec-13-retrofit-scoping.md` (+124/-54). No SPEC.md, no *-kind.toml, no validators touched.
- `python3 validators/validate_closure_root.py --discover .` exits 0 (executed above).
- Ancestry: `git merge-base --is-ancestor c88f7ea 073d5c5` → true; `c88f7ea` remains parent of the fix commit (no rewrite).
- `git log --oneline c88f7ea -1` confirms prior commit added the initial plan only.
- Abstraction-class validator re-run post-fix: "ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 1 declared a §13 block)."
- §13 revision history (382-383) accurately records the three targeted fixes without over-claim or retcon of prior state.

## Process checks

- `confirm_active_user_migration_or_behavior_change_guidance`: confirmed via full plan read. This is a forward-looking scoping document for additive §13 retrofits (SPEC.md:1478-1486 cited in plan §1). No runtime behavior change or migration guidance required; plan explicitly states the retrofit is additive and reversible per phase (324-330).
- `confirm_no_historical_dated_spec_retconned_without_link_or_correction_note`: confirmed. `git show --stat 073d5c5` and `--name-only` show zero edits to SPEC.md or any dated normative file. The single changed file is the new planning artefact itself; §13 revision history links the round-1 review session explicitly.
- `confirm_claimed_tests_were_actually_run_with_command_output_and_status`: confirmed. Executed and captured output for: `validate_closure_root.py --discover .` (pass, 74 files), `validate_abstraction_class.py` (pass, 19 files), `grep -n 'MUST flip'` (zero matches), Family C grep (exactly two historical matches), `sed -n '214,225p'` on validator (exact crypto_keys vocabulary), ancestry checks, and full file reads of plan + cited descriptors + validator source at codex's lines.

## Terminal verdict

**unconditional_approval**

Rationale (tied exclusively to inspected bytes, executed command output, and file:line reads): All three blockers are closed. U07-F1: SDP is Family A at plan:232; validator-invalid fields (`entropy_source = "system"`, `sign`/`verify`) exist only inside the explicit historical-explanation paragraph at 141-154 citing `validate_abstraction_class.py:182,214` and descriptor:61. U07-F2: taxonomy reframed at 167-177 and 201-209 as role label only; observation-record.v1 generalized; per-kind description rule added and cost-record:282-286 cited; structural divergence of the five kinds confirmed by direct reads. U07-F3: zero "MUST flip" matches; §9:299-322 is single coherent sentinel-persists text with ISS-005 filing at 349-356. No new defects per git show, executed validators (both pass with captured output), and ancestry confirmation. All policy.process_checks items satisfied by direct inspection/execution. The durable planning artefact is now free of the three concrete defects that produced the r1 `concrete_unresolvable_blocker`.
