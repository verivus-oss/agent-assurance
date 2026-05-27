## Summary

U08 is **complete**. Commit `073d5c5` closes my r1 blockers U07-F1, U07-F2, and U07-F3 on inspected repo bytes. Terminal classification: `unconditional_approval`.

## U08 — 073d5c5

No findings. `git show --stat --format='%H%n%P%n%s' 073d5c5` shows parent `c88f7ea` and only one changed file: `docs/planning/2026-05-25-spec-13-retrofit-scoping.md` with `124 insertions(+), 54 deletions(-)`.

## U07-F1 disposition

**Closed.** Plan row 18 now classifies `selective-disclosure-proof` as envelope family `A`, not `C`: [docs/planning/2026-05-25-spec-13-retrofit-scoping.md](/srv/repos/external/verivus-oss/agent-assurance/docs/planning/2026-05-25-spec-13-retrofit-scoping.md:232).

The old invalid `entropy_source = "system"`, `sign = false`, and `verify = true` text survives only in the §5 historical explanation of what r1 rejected: [docs/planning/2026-05-25-spec-13-retrofit-scoping.md](/srv/repos/external/verivus-oss/agent-assurance/docs/planning/2026-05-25-spec-13-retrofit-scoping.md:141). A section-limited grep over §6/§7/§8 returned no matches for those live-proposal fields.

Validator vocabularies confirm the original blocker basis: random accepts only `os`, `deterministic_seed`, `none` at [validators/validate_abstraction_class.py](/srv/repos/external/verivus-oss/agent-assurance/validators/validate_abstraction_class.py:182), and crypto key fields are `read_keys`, `use_keys`, `generate_allowed` at [validators/validate_abstraction_class.py](/srv/repos/external/verivus-oss/agent-assurance/validators/validate_abstraction_class.py:214). The SDP descriptor still delegates proof verification to RUNTIME-SPEC: [profiles/disclosure/selective-disclosure-proof-kind.toml](/srv/repos/external/verivus-oss/agent-assurance/profiles/disclosure/selective-disclosure-proof-kind.toml:61).

## U07-F2 disposition

**Closed.** §6 now says the class id is a producer-attested label/role, not a byte-level structural-shape contract: [docs/planning/2026-05-25-spec-13-retrofit-scoping.md](/srv/repos/external/verivus-oss/agent-assurance/docs/planning/2026-05-25-spec-13-retrofit-scoping.md:167).

The `observation-record.v1` row no longer says "closed-vocab dimensions + integer quantities"; it now describes a coarse artefact role and explicitly says each kind declares its own structural shape: [docs/planning/2026-05-25-spec-13-retrofit-scoping.md](/srv/repos/external/verivus-oss/agent-assurance/docs/planning/2026-05-25-spec-13-retrofit-scoping.md:184).

The new per-kind description rule is present at [docs/planning/2026-05-25-spec-13-retrofit-scoping.md](/srv/repos/external/verivus-oss/agent-assurance/docs/planning/2026-05-25-spec-13-retrofit-scoping.md:201), and it cites the existing cost-record description as the canonical shape. The cited cost-record bytes are present at [profiles/cost/cost-record-kind.toml](/srv/repos/external/verivus-oss/agent-assurance/profiles/cost/cost-record-kind.toml:282).

## U07-F3 disposition

**Closed.** `grep -n 'MUST flip' docs/planning/2026-05-25-spec-13-retrofit-scoping.md` returned zero matches, exit status `1`.

§9 now gives a single coherent closure-root rule: the empty sentinel persists for self-contained descriptors, while the descriptor file SHA-256 changes: [docs/planning/2026-05-25-spec-13-retrofit-scoping.md](/srv/repos/external/verivus-oss/agent-assurance/docs/planning/2026-05-25-spec-13-retrofit-scoping.md:299) and [docs/planning/2026-05-25-spec-13-retrofit-scoping.md](/srv/repos/external/verivus-oss/agent-assurance/docs/planning/2026-05-25-spec-13-retrofit-scoping.md:315). This matches SPEC §12.1 / §12.11 sentinel language at [SPEC.md](/srv/repos/external/verivus-oss/agent-assurance/SPEC.md:928) and [SPEC.md](/srv/repos/external/verivus-oss/agent-assurance/SPEC.md:1155).

The §13.4-vs-§12.1 tension is acknowledged as out of scope and filed as an ISS-005 candidate at [docs/planning/2026-05-25-spec-13-retrofit-scoping.md](/srv/repos/external/verivus-oss/agent-assurance/docs/planning/2026-05-25-spec-13-retrofit-scoping.md:349).

## No new defects

Confirmed. `git diff --name-only c88f7ea..073d5c5` returns only `docs/planning/2026-05-25-spec-13-retrofit-scoping.md`; no `SPEC.md`, kind descriptors, or validators were changed.

`git merge-base --is-ancestor c88f7ea 073d5c5` exited `0`.

`python3 validators/validate_closure_root.py --discover .` exited `0` with:

```text
CLOSURE-ROOT VALIDATION PASSED (74 file(s)).
```

§12 open questions were updated correctly: the SDP envelope question is gone, and Q2 now asks about producer-attested role-level taxonomy rather than byte-identical structure: [docs/planning/2026-05-25-spec-13-retrofit-scoping.md](/srv/repos/external/verivus-oss/agent-assurance/docs/planning/2026-05-25-spec-13-retrofit-scoping.md:363). §13 revision history accurately describes the r1-to-r2 fixes without over-claiming: [docs/planning/2026-05-25-spec-13-retrofit-scoping.md](/srv/repos/external/verivus-oss/agent-assurance/docs/planning/2026-05-25-spec-13-retrofit-scoping.md:378).

## Process checks

confirm_active_user_migration_or_behavior_change_guidance: confirmed. The reviewed commit is docs-only; the plan keeps the retrofit additive and describes revert behavior at [docs/planning/2026-05-25-spec-13-retrofit-scoping.md](/srv/repos/external/verivus-oss/agent-assurance/docs/planning/2026-05-25-spec-13-retrofit-scoping.md:324).

confirm_no_historical_dated_spec_retconned_without_link_or_correction_note: confirmed. `git show --name-status --oneline 073d5c5` shows only the planning doc modified, and the plan records the dated revision history at [docs/planning/2026-05-25-spec-13-retrofit-scoping.md](/srv/repos/external/verivus-oss/agent-assurance/docs/planning/2026-05-25-spec-13-retrofit-scoping.md:380).

confirm_claimed_tests_were_actually_run_with_command_output_and_status: confirmed. I ran the closure-root validator above. I also ran `python3 validators/validate_abstraction_class.py --repo-root . core/*-kind.toml profiles/agent-assurance/*-kind.toml profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml`, which exited `0` with `ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 1 declared a §13 block).`

## Terminal verdict

`unconditional_approval`

Rationale: approval is based on inspected docs/code, executed command output, and persisted r1/r2 review evidence. The SDP envelope is now Family A and validator-compatible, the taxonomy no longer asserts shared byte-level structure, and §9 now has one closure-root rule consistent with SPEC §12.
