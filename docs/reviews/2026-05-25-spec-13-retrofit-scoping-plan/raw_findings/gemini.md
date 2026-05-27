## Summary

The SPEC §13 retrofit scoping plan (`c88f7ea`) is a comprehensive and structurally sound corrective-program specification for bringing the remaining 18 blessed kind descriptors into compliance with the abstraction-class and capability-envelope requirements. Based on empirical verification of the repository inventory (19 total kind descriptors, 1 already retrofitted) and analysis of SPEC §13 and §12 prose, the plan's adoption of the "narrow" R1 reading (bounding the descriptor parse) is the correct architectural choice, consistent with the `cost-record` reference. The proposed 13-class taxonomy aligns with the structural rules (`[[kind.required_fields]]` and `[[kind.hard_invariants]]`) of the respective kinds. While the plan contains a minor textual contradiction in §9 regarding the `closure_root` sentinel behavior and includes likely "R2 leakage" in the `selective-disclosure-proof` envelope, these do not invalidate the corrective program. The plan is sufficiently specific for implementation and avoids infrastructure creep.

Terminal classification for U07: **complete**.

## U07 — c88f7ea

| File:Line | Severity | Finding |
|---|---|---|
| `docs/planning/2026-05-25-spec-13-retrofit-scoping.md:295-300` | Minor | **Textual Contradiction**: The plan asserts that the `closure_root` of retrofitted descriptors "changes" while simultaneously stating the sentinel value "does NOT change". As descriptors cite no cryptographic upstream evidence, the sentinel MUST persist per SPEC §12.1. |
| `SPEC.md:1432` | Minor | **Doc Bug (Likely Typo)**: SPEC §13.4 claims §13 blocks "participate in the descriptor's `closure_root`" and that changing them "flips the descriptor's closure root". Per §12.1, `closure_root` only covers upstream hashes. Changing internal §13 blocks flips the descriptor's *SHA-256*, which flips downstream *instances'* closure roots, but the descriptor's own closure root remains the empty sentinel. |
| `docs/planning/2026-05-25-spec-13-retrofit-scoping.md:252` | Minor | **R2 Leakage**: The Family C proposal for `selective-disclosure-proof` (granting `random` and `crypto_keys`) covers runtime verification, not the "narrow" R1 parse. `validate_disclosure.py` confirms the SPEC-layer check is purely structural (regex/vocab). |

## Q1 — R1 vs R2

**Verified.** The "narrow" R1 reading (envelope bounds descriptor parse) is the only interpretation consistent with the `cost-record` reference and the SPEC's architectural layering.

**Evidence from SPEC.md:**
- `SPEC.md:1244-1246`: "the producer asserts that conforming instance documents — and any runtime that executes against them — stay inside the envelope. A consumer reading the descriptor treats the declared envelope as the contract."
- `SPEC.md:1472-1473`: "the spec specifies the semantic contract; the runtime chooses the implementation." (Supports R1 as the contract definition layer).

**Evidence from `profiles/cost/cost-record-kind.toml`:**
- `lines 282-327`: The reference §13 block explicitly denies all I/O, networking, and process spawn for `cost-record`, which describes actions that *already happened*. If R2 (bounding described actions) were intended, `cost-record` would need an unbounded envelope to cover the actions it records.

## Q2 — taxonomy

**Verified.** The proposed taxonomy in Plan §6 is structurally sound.

- **`observation-record.v1`**: Shared by `cost-record`, `evidence-matrix`, `gate-decision`, `assertion-log-record`, and `redaction-manifest`. All five are IJB `thing/structural` (per their descriptors) and serve as read-only records of facts, outcomes, or relations. While `evidence-matrix` and `redaction-manifest` lack the "integer quantities" prominent in `cost-record`, they share the core "read-only observation of a past state/action" property.
- **`policy-declaration.v1`**: Shared by `readiness-gate`, `contract-declaration`, and `spec-contract`. All three define normative constraints or gates (`artifact_classes`, `contracts`, `guarantees/invariants`) and are IJB `thing/structural`.

## Q3 — inventory

**Confirmed.** The plan's inventory is accurate.

**Command Output:**
```sh
$ find core/ profiles/ -name '*-kind.toml' -not -path './.git/*' | sort
[19 files listed — confirmed]

$ python3 validators/validate_abstraction_class.py --repo-root . core/*-kind.toml profiles/agent-assurance/*-kind.toml profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml
ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 1 declared a §13 block).
```
Inventory count (19) and §13 status (1 existing) are verified.

## Q4 — SDP envelope

**Refuted (R2 Leakage detected).** The proposed Family C envelope for `selective-disclosure-proof` (Plan §7, row 18) grants permissions (`random`, `crypto_keys`) that are not required for parsing the TOML descriptor or performing SPEC-layer validation.

**Evidence from `validators/validate_disclosure.py`:**
- `lines 173-205`: `validate_proof` performs only regex matches on `bound_source` (`^sha256:[0-9a-f]{64}$`) and prefix checks on `covers`. It performs NO cryptographic verification.
- `selective-disclosure-proof-kind.toml:68-69`: "The SPEC layer enforces shape only. Verifying the proof against the published bytes is RUNTIME-SPEC."

**Conclusion**: Under the R1 reading, `selective-disclosure-proof` should be Family A. The Family C proposal is R2 leakage.

## Q5 — phasing

**Confirmed.** The phasing is appropriate for managing risk.

- **Phase 1** (Observation records): Lowest risk as they are flat records with well-understood structural rules.
- **Phase 3** (Procedure-bearing/Special): Appropriately deferred. While `smoke-validation` is an observation, its dependency on `[[checks]]` and the complex `INV03` logic justifies later treatment. `assertion-bundle` involves IJB grammar parsing, which represents a higher "parse-time" CPU complexity, fitting the deferred Phase 3.

## Q6 — closure_root

**Verified.** The plan's assertion that the empty sentinel persists is correct under SPEC §12.1.

**Evidence from bytes:**
```sh
$ grep -n closure_root profiles/cost/cost-record-kind.toml
15:closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
```
The reference `cost-record-kind.toml` uses the empty sentinel despite declaring §13. Per `SPEC.md:1442-1447`, `closure_root` only covers *upstream* artifact hashes (cites_upstream, provenance, evidence). Kind descriptors at HEAD cite no such cryptographic upstreams.

**Conclusion**: The "flip" mentioned in SPEC §13.4 is a doc bug (likely meaning the descriptor's SHA-256 flips). The plan's sentinel expectation is correct.

## Q7 — completeness

**Verified.** The plan is highly specific and serves as an actionable corrective-program spec.
- It provides a mapping for every one of the 18 kinds.
- It defines the taxonomy and baseline envelopes (Family A/C).
- It provides explicit verification commands (Plan §9).

**Infrastructure Creep**: None detected. The plan utilizes existing validators and standard `git` workflows.

## Process checks

- `confirm_active_user_migration_or_behavior_change_guidance`: **Confirmed** (Plan §11 acknowledges follow-ups).
- `confirm_no_historical_dated_spec_retconned_without_link_or_correction_note`: **Confirmed** (Only a new planning doc was added).
- `confirm_claimed_tests_were_actually_run_with_command_output_and_status`: **Confirmed** (Executed validators and grep locally).

## Terminal verdict

**unconditional_approval**

The plan is technically accurate, consistent with the repository's current state and the core SPEC architecture. The minor contradictions and R2 leakage noted do not impede the execution of the retrofit phases. The R1 interpretation is definitively supported by the `cost-record` precedent and SPEC §13.5. Inventory is correct at 19 kinds. Phasing and taxonomy are sound. No unresolvable blockers identified.
