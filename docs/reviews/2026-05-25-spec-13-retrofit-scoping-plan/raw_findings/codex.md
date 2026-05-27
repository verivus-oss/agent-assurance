## Summary

U07 is **incomplete**. I verified the plan against SPEC §12/§13, the cited kind descriptors, sqry-indexed repo structure, and the validator commands. The inventory claim is correct, but the plan has material blockers: the SDP Family C envelope is unsupported by the descriptor and uses fields the current validator would reject; the shared taxonomy claim is overstated against actual descriptor rules; and §9 gives contradictory closure-root guidance. Terminal classification: `concrete_unresolvable_blocker`.

## U07 — c88f7ea

Finding 1 — **Blocker**: `selective-disclosure-proof` Family C is not supported by the descriptor and is not validator-compatible. The plan proposes `entropy_source = "system"` plus `sign = false, verify = true` at [docs/planning/2026-05-25-spec-13-retrofit-scoping.md](/srv/repos/external/verivus-oss/agent-assurance/docs/planning/2026-05-25-spec-13-retrofit-scoping.md:201), but the descriptor delegates proof verification to RUNTIME-SPEC at [profiles/disclosure/selective-disclosure-proof-kind.toml](/srv/repos/external/verivus-oss/agent-assurance/profiles/disclosure/selective-disclosure-proof-kind.toml:61), and the validator only accepts random sources `os`, `deterministic_seed`, `none` at [validators/validate_abstraction_class.py](/srv/repos/external/verivus-oss/agent-assurance/validators/validate_abstraction_class.py:182), while crypto keys are `read_keys`, `use_keys`, `generate_allowed` at [validators/validate_abstraction_class.py](/srv/repos/external/verivus-oss/agent-assurance/validators/validate_abstraction_class.py:214).

Finding 2 — **Major**: Phase 1's shared `observation-record.v1` is not structurally sound as written. The plan's class description says "closed-vocab dimensions + integer quantities" at [docs/planning/2026-05-25-spec-13-retrofit-scoping.md](/srv/repos/external/verivus-oss/agent-assurance/docs/planning/2026-05-25-spec-13-retrofit-scoping.md:163), which matches cost-record dimensions at [profiles/cost/cost-record-kind.toml](/srv/repos/external/verivus-oss/agent-assurance/profiles/cost/cost-record-kind.toml:196), but not evidence-matrix claims/evidence/matrix, gate-decision verdict roots, assertion-log signatures, or redaction-manifest redactions.

Finding 3 — **Major**: §9 gives contradictory closure-root instructions. It says each retrofitted descriptor's `closure_root MUST flip` at [docs/planning/2026-05-25-spec-13-retrofit-scoping.md](/srv/repos/external/verivus-oss/agent-assurance/docs/planning/2026-05-25-spec-13-retrofit-scoping.md:257), then says the empty sentinel does not change at [docs/planning/2026-05-25-spec-13-retrofit-scoping.md](/srv/repos/external/verivus-oss/agent-assurance/docs/planning/2026-05-25-spec-13-retrofit-scoping.md:262). SPEC §12 supports the sentinel for self-contained descriptors.

## Q1 — R1 vs R2

Refuted as stated. SPEC §13.4 itself is about cascade break, not parse semantics: descriptor declarations participate in `closure_root`, and widening the envelope changes `C_V → C_V+1` at [SPEC.md](/srv/repos/external/verivus-oss/agent-assurance/SPEC.md:1332). The parse-only R1 reading is not confirmed by exact SPEC bytes. §13.1 says the envelope declares grants "permitted to instances of this kind" at [SPEC.md](/srv/repos/external/verivus-oss/agent-assurance/SPEC.md:1220), and asserts "conforming instance documents — and any runtime that executes against them" stay inside it at [SPEC.md](/srv/repos/external/verivus-oss/agent-assurance/SPEC.md:1224). §13.8 also says "runtime executing an instance" may use capabilities at [SPEC.md](/srv/repos/external/verivus-oss/agent-assurance/SPEC.md:1451). I do not find canonical R2-as-"all described future actions" either; the text is ambiguous for procedure-bearing documents.

## Q2 — taxonomy

`observation-record.v1`: not sound as written. Cost-record requires categorical dimensions and non-negative integer quantities at [profiles/cost/cost-record-kind.toml](/srv/repos/external/verivus-oss/agent-assurance/profiles/cost/cost-record-kind.toml:196). Evidence-matrix instead requires `claims`, `evidence`, and `matrix` with cross-reference invariants at [core/evidence-matrix-kind.toml](/srv/repos/external/verivus-oss/agent-assurance/core/evidence-matrix-kind.toml:90). Gate-decision requires verdict/evidence-root fields at [profiles/agent-assurance/gate-decision-kind.toml](/srv/repos/external/verivus-oss/agent-assurance/profiles/agent-assurance/gate-decision-kind.toml:95). Assertion-log-record requires signature/hash fields at [profiles/agent-assurance/assertion-log-record-kind.toml](/srv/repos/external/verivus-oss/agent-assurance/profiles/agent-assurance/assertion-log-record-kind.toml:95). Redaction-manifest requires redactions at [profiles/disclosure/redaction-manifest-kind.toml](/srv/repos/external/verivus-oss/agent-assurance/profiles/disclosure/redaction-manifest-kind.toml:83).

`policy-declaration.v1`: broad concept is defensible, but "shared structural rules" is overstated. Readiness-gate requires `artifact_classes` and `gates` at [core/readiness-gate-kind.toml](/srv/repos/external/verivus-oss/agent-assurance/core/readiness-gate-kind.toml:81); contract-declaration requires `contracts` at [core/contract-declaration-kind.toml](/srv/repos/external/verivus-oss/agent-assurance/core/contract-declaration-kind.toml:76); spec-contract requires `contract.guarantees` and `contract.invariants` at [profiles/agent-assurance/spec-contract-kind.toml](/srv/repos/external/verivus-oss/agent-assurance/profiles/agent-assurance/spec-contract-kind.toml:80).

## Q3 — inventory

Confirmed. `find core/ profiles/ -name '*-kind.toml' -not -path './.git/*' | sort` returned 19 descriptors, matching the plan. `python3 validators/validate_abstraction_class.py --repo-root . core/*-kind.toml profiles/agent-assurance/*-kind.toml profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml` returned:

```text
ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 1 declared a §13 block).
```

`grep -l 'kind.abstraction_class' core/*-kind.toml profiles/*/*-kind.toml` returned only `profiles/cost/cost-record-kind.toml`.

## Q4 — SDP envelope

Refuted. The SDP descriptor requires proof metadata only: `id`, `subject`, `bound_source`, `proof_scheme`, and one of `covers` / `proof_artifact` at [profiles/disclosure/selective-disclosure-proof-kind.toml](/srv/repos/external/verivus-oss/agent-assurance/profiles/disclosure/selective-disclosure-proof-kind.toml:86). It explicitly says "The SPEC layer enforces shape only. Verifying the proof against the published bytes is RUNTIME-SPEC" at [profiles/disclosure/selective-disclosure-proof-kind.toml](/srv/repos/external/verivus-oss/agent-assurance/profiles/disclosure/selective-disclosure-proof-kind.toml:61). The proposed random/crypto grants are R2 leakage, not descriptor parse requirements.

## Q5 — phasing

Partly refuted. `rollback-plan` being Phase 3 is appropriate because it is procedure-bearing: it requires triggers and a procedure at [profiles/agent-assurance/rollback-plan-kind.toml](/srv/repos/external/verivus-oss/agent-assurance/profiles/agent-assurance/rollback-plan-kind.toml:106). Under narrow parsing it can still be Family A, but not Phase 1. `implementation-dag` Family A is plausible only under R1; it describes executable units at [core/implementation-dag-kind.toml](/srv/repos/external/verivus-oss/agent-assurance/core/implementation-dag-kind.toml:49). Phase 1 should not be "mechanical insertion of the canonical block" while using the current `observation-record.v1` description, because the Phase 1 descriptors diverge structurally as cited in Q2.

## Q6 — closure_root

The plan's sentinel assertion is correct under SPEC §12, but §9 is internally inconsistent. `grep -n closure_root profiles/cost/cost-record-kind.toml` shows the sentinel at line 15. `grep -n closure_root core/*-kind.toml profiles/*/*-kind.toml` shows all descriptors use the same sentinel. `python3 validators/validate_closure_root.py --discover .` returned:

```text
CLOSURE-ROOT VALIDATION PASSED (74 file(s)).
```

SPEC §12.1 says a self-contained document with empty closure inputs must emit the empty sentinel at [SPEC.md](/srv/repos/external/verivus-oss/agent-assurance/SPEC.md:928). SPEC §12.11 says documents with no upstream evidence use the same sentinel at [SPEC.md](/srv/repos/external/verivus-oss/agent-assurance/SPEC.md:1153). So this is intended §12 behavior, not a §12 conformance gap. The remaining issue is the plan's "MUST flip" wording and SPEC §13's conflicting claim that class/envelope changes flip descriptor closure root at [SPEC.md](/srv/repos/external/verivus-oss/agent-assurance/SPEC.md:1235).

## Q7 — completeness

Refuted. The plan is close enough for inventory and validator workflow, but not enough to implement Phase 1 safely because the shared class description does not fit the Phase 1 descriptors and the SDP envelope is invalid. It does not slip in rejected CI tooling: it uses the existing review DAG at [docs/planning/2026-05-25-spec-13-retrofit-scoping.md](/srv/repos/external/verivus-oss/agent-assurance/docs/planning/2026-05-25-spec-13-retrofit-scoping.md:205), local validators at [docs/planning/2026-05-25-spec-13-retrofit-scoping.md](/srv/repos/external/verivus-oss/agent-assurance/docs/planning/2026-05-25-spec-13-retrofit-scoping.md:230), and explicitly avoids CI cascade testing at [docs/planning/2026-05-25-spec-13-retrofit-scoping.md](/srv/repos/external/verivus-oss/agent-assurance/docs/planning/2026-05-25-spec-13-retrofit-scoping.md:283). That aligns with CONTRIBUTING's discipline-over-infrastructure rule at [CONTRIBUTING.md](/srv/repos/external/verivus-oss/agent-assurance/CONTRIBUTING.md:51) and ISS-001's closing note at [docs/issues/2026-05-23-ISS-001-self-approval-discipline.md](/srv/repos/external/verivus-oss/agent-assurance/docs/issues/2026-05-23-ISS-001-self-approval-discipline.md:215).

## Process checks

confirm_active_user_migration_or_behavior_change_guidance: checked; plan is docs-only and cites additive §13 introduction, but closure-root guidance needs correction.

confirm_no_historical_dated_spec_retconned_without_link_or_correction_note: confirmed; `git show --name-status c88f7ea` shows one added planning doc and no SPEC/profile/validator edits.

confirm_claimed_tests_were_actually_run_with_command_output_and_status: confirmed; abstraction-class, IJB conformance, kind descriptor, and closure-root validators all exited 0 with pass output.

## Terminal verdict

concrete_unresolvable_blocker

Rationale: U07 cannot be approved on inspected bytes because the SDP Family C row is unsupported and validator-incompatible, the Phase 1 shared taxonomy does not match descriptor structure, and §9's closure-root instructions conflict with SPEC §12 and current validator behavior.
