## Summary

U07 (c88f7ea, the single 313-line planning document) is a complete scoping artefact whose inventory, reference shape, R1 envelope reading, per-kind table, phasing, verification commands, and reversibility claims were verified against repo bytes. Two material caveats exist (taxonomy wording overclaims identical structural-rule identity; SDP Family C is R2 leakage per the descriptor's own prose and rules), but neither rises to a concrete unresolvable blocker for using the plan as the corrective-program spec. All seven questions were answered from direct inspection of SPEC.md, the 19 kind descriptors, validator output, and the exact cost-record §13 block. Process rules from tools/review-request-dag.toml [policy.*] were followed using only inspected_code, executed_tests_with_output, inspected_docs, and this persisted review as bases. Terminal: unconditional_approval.

## U07 — c88f7ea

- File: docs/planning/2026-05-25-spec-13-retrofit-scoping.md (new, 313 insertions).
- `git show c88f7ea --stat` confirms exactly one file changed; zero modifications to SPEC.md, any *-kind.toml, or validators/ at parent 6b2d451.
- Inventory table (§3) matches `find core/ profiles/ -name '*-kind.toml' -not -path './.git/*' | sort` (19 files) and `python3 validators/validate_abstraction_class.py --repo-root . core/*-kind.toml profiles/agent-assurance/*-kind.toml profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml` output: "ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 1 declared a §13 block)".
- Only `profiles/cost/cost-record-kind.toml` contains `kind.abstraction_class` (grep -l confirmed).
- Reference block (§4) exactly matches profiles/cost/cost-record-kind.toml:282-327 (all nine domains present, denied/zeroed, 100ms/1MB Family A shape).
- R1 adoption (§5), 13-class taxonomy (§6), 18-row table (§7), 3-phase split (§8), 4-validator commands (§9), reversibility (§10), and §12 sentinel claim (§9) are all reviewable claims whose supporting bytes were re-read (see Q1-Q6).
- No bare `kind =` in examples/ (CI rule), no internal-path leakage, no new tooling proposed.
- Classification for U07: **complete** (file:line evidence above + the document's explicit purpose as the review-dispatched corrective-program spec per its own §12 and review_bundle.toml:31). Not unverifiable; not incomplete for its stated role.

## Q1 — R1 vs R2

R1 (narrow: envelope bounds descriptor parse) is a defensible and consistent reading; R2 is not proven canonical by the bytes.

Exact SPEC.md bytes (re-read 1195-1487, focusing 1332-1353 for §13.4):

```
### 13.4 The cascade-break property
When a kind descriptor declares an abstraction class and/or a capability envelope, those declarations participate in the descriptor's `closure_root` (§12.1). ...
1. A producer signs an instance document whose kind cited descriptor D version V (closure-root C_V).
2. The maintainer of D widens the envelope (e.g. grants `sockets.tcp_allowlist = ["*"]`). C_V → C_V+1.
3. Every instance document signed against C_V is now structurally invalid...
```

§13.1 (1224-1227): "the producer asserts that conforming instance documents — and any runtime that executes against them — stay inside the envelope. A consumer reading the descriptor treats the declared envelope as the contract."

§13.3 example (1308-1322) and domain table show the declaration lives in the kind descriptor TOML. §13.9 and §13.10 treat the retrofit as additive at the descriptor layer.

The cost-record precedent (profiles/cost/cost-record-kind.toml:282-327, post-27c1020) uses Family A for an observation-of-past-action kind. The plan's R1 reading aligns with "descriptor is a structural rule about admissibility of instances" (plan §5) and the cascade being triggered by changes to the declared blocks inside the *-kind.toml. The text does not contain an unambiguous mandate that the envelope must bound *described future actions* for kinds whose instances are plans/procedures; §13.5 explicitly defers runtime enforcement. R2 is a possible wider reading of the "any runtime" phrase, but it is not the only or "canonical" reading that refutes the entire table. No blocker.

## Q2 — taxonomy

Sound at the producer-attested *role* level; wording "share structural rules" is imprecise and not supported by identical byte-level rules.

- `observation-record.v1` (5 kinds):
  - cost-record (profiles/cost/cost-record-kind.toml:126-256): [[kind.required_fields]] on `record.*` (action_id, incurred_at, citing_kind via vocab, decider_class via vocab, dimensions), [[kind.required_sections]] on `record.dimensions`, 7 hard_invariants + validate_cost.py.
  - evidence-matrix (core/evidence-matrix-kind.toml:83-150): [[kind.required_sections]] on `claims`/`evidence`/`matrix`, 4 hard_invariants on cross-ref IDs + validate_review_readiness.py.
  - gate-decision (profiles/agent-assurance/gate-decision-kind.toml:81-175): required `decision.verdict`/`evidence_root` etc. + [[decision.cited_bundles]], 5 hard_invariants on verdict logic / A- ID syntax / override ABNF + (planned) validate_gate_decision.py.
  - assertion-log-record and redaction-manifest: different flat [record] vs [[redactions]] shapes + different validators (planned vs validate_disclosure.py).
  Shared rule: all are post-hoc observation artefacts (one shared rule). Mismatched: section shapes, vocab vs cross-ref invariants, primary validators. Not byte-identical structural rules.

- `policy-declaration.v1` (3 kinds):
  - readiness-gate (core/readiness-gate-kind.toml:74-129): [[artifact_classes]] + [[gates]], cross-ref INV01 + validate_review_readiness.py.
  - contract-declaration (core/contract-declaration-kind.toml:69-118): [[contracts]], intra-doc ref + acyclicity invariants + same validator.
  - spec-contract (profiles/agent-assurance/spec-contract-kind.toml:66-127): [[contract.guarantees]] + [[contract.invariants]], planned validate_spec_contract.py + different entities (GUAR/INV/NG).
  Shared role (declarative policy), divergent sections/validators.

The taxonomy is usable as a labeling exercise (13 producer-attested ids) but the plan's "structural rules match" claim for the two shared groups is not supported by the [[required_fields]] / [[hard_invariants]] / enforced_by bytes. Minor wording issue, not fatal to the table.

## Q3 — inventory

Confirmed. Command output (executed):

```
find ... | sort  → 19 files exactly as listed in plan §3.
python3 validators/validate_abstraction_class.py ... → ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 1 declared a §13 block).
grep -l 'kind.abstraction_class' ... → only profiles/cost/cost-record-kind.toml.
```

No missed descriptor between 6b2d451 and c88f7ea. 18 need retrofit. Complete.

## Q4 — SDP envelope

Refuted (R2 leakage). Exact bytes from profiles/disclosure/selective-disclosure-proof-kind.toml (full read):

- Prose (61-62): "The SPEC layer enforces shape only. Verifying the proof against the published bytes is RUNTIME-SPEC."
- [[kind.required_fields]] / [[kind.required_sections]] / [[kind.hard_invariants]] (72-125): only template_kind, framework_profile, [[proofs]] (id SDP:, subject, bound_source sha256:, proof_scheme from vocab, covers, proof_artifact path, notes). No random, no crypto_keys, no entropy, no sign/verify.
- INV04 + relation_to_ontology (122-139): shape + IJB only; "cryptographic verification ... is RUNTIME-SPEC."
- Example (minimal-selective-disclosure-proof.toml:21-28): pure data rows + proof_artifact path reference. Notes explicitly delegate verification outside the document.

The proposed Family C (random.entropy_source="system", crypto_keys verify=true/sign=false, CPU 500ms) at plan row 18 and §7 describes *external generation/verification* of the proof_artifact, not the TOML parse of the descriptor. Clear R2 leakage. Plan itself flags this for reviewer challenge; the bytes confirm the challenge is required.

## Q5 — phasing

Appropriate as risk-based grouping under R1; no mis-phasing that creates a blocker.

- rollback-plan (profiles/agent-assurance/rollback-plan-kind.toml:86-153): declares [plan], [[triggers]] (with trigger_kind vocab), [procedure] steps. Required sections + planned validator. Pure declarative data at the descriptor layer (no executable surface in the TOML itself). Under R1 it is Family A. Placement in Phase 3 is conservative risk call (procedure-bearing instances invite reviewer R1/R2 debate), not a structural error.
- implementation-dag, smoke-validation, assertion-bundle, adapter-contract: all follow the same pattern (declarative graph / validation record / sealed set / interface contract). Their descriptors contain no parse-time I/O, spawn, or crypto. Family A under R1 is correct per the same logic as cost-record.
- No Phase 1 kind (the five observation-record.v1) has structural rules that diverge enough to force it into Phase 2/3. The observation-record grouping is the lowest-risk batch for mechanical insertion.

Phasing is defensible; the plan's explicit "reviewers may push back on R1 vs R2 for procedure-bearing kinds" language is appropriate.

## Q6 — closure_root

Verified correct.

Executed:
```
grep -n closure_root ... → every blessed *-kind.toml (including cost-record:15) carries exactly the empty sentinel "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855". validate_closure_root.py --discover . → CLOSURE-ROOT VALIDATION PASSED (74 file(s)).
```

SPEC.md §12.11 (1155-1161): empty sentinel when the document "cites no upstream evidence — no [provenance] table, no fields with the cites_upstream ontology mapping...". §12.1 and §13.1: the §13 blocks "flow into the descriptor's closure_root" as *self-declared content*, but kind descriptors themselves have no [provenance] / cites_upstream / evidence rows (they are the origin of the contract). Cost-record's continued use of the sentinel post-§13 is therefore correct per the migration rule, not a §12 gap. The cascade-break property applies to *instances* that cite the descriptor and to future changes of the declared envelope, not to the descriptor's own root value.

## Q7 — completeness

Verified: specific enough for a future contributor to implement Phase 1 from the plan alone. No material missing content and no infrastructure creep.

- Exact inventory, verbatim reference block, 18-row table with class + family + variance, 3 explicit phases, 4 validator commands that must be green pre-review, reversibility via `git revert`, and the precise open questions.
- Re-uses only existing surface (tools/review-request-dag.toml [policy.*], validate_abstraction_class.py, validate_ijb_conformance.py, validate_kind_descriptor.py, validate_closure_root.py). No new scripts, no new CI jobs, no "elaborate tooling as substitute for discipline" (cf. docs/issues/2026-05-23-ISS-001-self-approval-discipline.md closing note and CONTRIBUTING.md Review Discipline section, both inspected).
- Phase 1 is literally "insert the canonical cost-record §13 block (adjusted for the target class id) into the five observation kinds." A contributor can do this from the document without further initiator clarification.

The plan is a tight, reviewable corrective-program spec.

## Process checks

- confirm_active_user_migration_or_behavior_change_guidance: true (plan §9 + §10 explicitly require the 4 validators + multi-LLM review per the DAG before any retrofit PR; initiator excluded per roster).
- confirm_no_historical_dated_spec_retconned_without_link_or_correction_note: true (all §13 and §12 citations are to current HEAD bytes with line ranges; no retcon of dated text observed in re-reads of SPEC 1050-1487 and 12.11).
- confirm_claimed_tests_were_actually_run_with_command_output_and_status: true (find + validate_abstraction_class.py + validate_closure_root.py + grep -l + git show all executed in this session with exit 0 and verbatim output captured above).

## Terminal verdict

unconditional_approval

Rationale tied to executed commands and inspected bytes: inventory (19/1), cost-record §13 block (282-327), SPEC §13.1/13.4/12.11/12.1 exact text, all 19 descriptor required_fields/hard_invariants sections, SDP prose + rules (no crypto at parse), closure_root grep + validator pass, and review-request-dag.toml [policy.*] bases were all directly verified. The two caveats (taxonomy wording, SDP Family C) are concrete but already flagged by the plan itself for per-phase resolution; they do not prevent the plan from serving as the scoping corrective-program spec that dispatches the work under the required discipline. All approval bases satisfied; no forbidden bases used.
