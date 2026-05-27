# Independent review — SPEC §13 retrofit scoping plan (2026-05-25)

You are an independent reviewer running with a fresh, clean context.
You have NO prior memory of this session or the plan under review.
Your scope: verify the scoping plan at commit `c88f7ea` against
SPEC §13 prose, the existing kind descriptors, and the validators.
You have full filesystem access and MCP tool access (sqry, exa,
ref_tools). Use them.

## Repository

- Working copy: `/srv/repos/external/verivus-oss/agent-assurance`
- Parent commit (pre-plan): `6b2d451`
- HEAD (with plan): `c88f7ea`
- Commit range: `6b2d451..c88f7ea` (1 commit, single new file)
- Plan under review: `docs/planning/2026-05-25-spec-13-retrofit-scoping.md`
- Review bundle: `docs/reviews/2026-05-25-spec-13-retrofit-scoping-plan/review_bundle.toml`

## The discipline (`tools/review-request-dag.toml [policy.*]`)

You MUST verify every assertion in the plan against the actual
bytes in the repo. Do NOT accept the initiator's summary as
evidence. Specifically:

- `[policy.evidence]` — verify against code and docs. Findings
  need file:line + severity. Use sqry semantic search first for
  code-like structures, `read_file` / `grep` for prose. The plan
  cites specific line ranges in SPEC.md and in kind descriptors;
  re-read those bytes yourself.
- `[policy.approval]` — `forbidden_approval_bases` =
  `stated_intent`, `plan_compliance_claim`,
  `should_be_fixed_language`. Required bases = `inspected_code`,
  `executed_tests_with_output`, `inspected_docs`,
  `persisted_review_evidence`. The only terminal states are
  `unconditional_approval` and `concrete_unresolvable_blocker`.
- `[policy.unit_classification]` — classify U07 (the plan
  commit) with file:line evidence.

If the initiator disagrees with your finding in a future round,
the response MUST cite code or doc evidence at file:line, not
assertion.

## What to verify — the seven questions

Read the review bundle's `[bundle.questions]` section in full. It
contains the substantive questions. Below are short pointers; the
bundle has the canonical wording.

### Q1 — R1 vs R2 envelope semantics

Plan §5 picks R1 (envelope bounds descriptor PARSE) over R2
(envelope bounds described actions). Read **SPEC.md §13.4
(approximately lines 1308-1326)** in full. Quote the exact bytes
that confirm or refute R1. If R2 is the canonical reading, every
row in the plan's §7 table is wrong; that would be a
`concrete_unresolvable_blocker`.

Also read cost-record's existing §13 block at
**profiles/cost/cost-record-kind.toml:282-327** for the precedent
the plan cites.

### Q2 — Taxonomy soundness

Plan §6 proposes 13 class ids; 5 of them shared. For each shared
assignment, inspect the kind descriptors' actual structural rules
(`[[kind.required_fields]]`, `[[kind.required_sections]]`,
`[[kind.hard_invariants]]`) and decide whether the rules match
closely enough to share a class id.

Specifically:

- `observation-record.v1` shared by cost-record + evidence-matrix
  + gate-decision + assertion-log-record + redaction-manifest.
  Compare structural rules. Find at least one shared rule and at
  least one mismatched rule, if any.
- `policy-declaration.v1` shared by readiness-gate +
  contract-declaration + spec-contract. Same exercise.

### Q3 — Inventory completeness

Run:
```sh
find core/ profiles/ -name '*-kind.toml' -not -path './.git/*' | sort
python3 validators/validate_abstraction_class.py --repo-root . \
  core/*-kind.toml profiles/agent-assurance/*-kind.toml \
  profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml
```

Confirm: 19 descriptors, 1 declares §13. Report any missing
descriptor.

### Q4 — Selective-disclosure-proof envelope

Plan row 18 (`selective-disclosure-proof`) is the only Family C
proposal. Plan §5 acknowledges this may be R2 leakage. Read
**profiles/disclosure/selective-disclosure-proof-kind.toml**
in full. Does the descriptor's own parse require `random` and
`crypto_keys` capabilities, or is the proposed envelope actually
about the proof's verification *outside* the descriptor?

### Q5 — Phasing appropriateness

Plan §8 puts `rollback-plan`, `implementation-dag`,
`smoke-validation`, `assertion-bundle`, `adapter-contract`,
`selective-disclosure-proof` in Phase 2 or 3. Are any of these
mis-phased? In particular:

- Should `rollback-plan` be Phase 1 (it's described as
  procedure-bearing but the descriptor itself is pure data)?
- Should any Phase 1 kind move to Phase 2/3 because its
  structural rules diverge from the others sharing the class?

### Q6 — Closure-root expectation

Plan §9 asserts the cost-record's `closure_root` is the empty
sentinel at HEAD even after declaring §13. Verify:
```sh
grep -n closure_root profiles/cost/cost-record-kind.toml
grep -n closure_root core/*-kind.toml profiles/*/*-kind.toml
```

Is this correct, or is it a §12 conformance gap (the descriptor
declares §13 which is content, so its closure_root should reflect
that content)? Read **SPEC.md §12.1 and §12.11** to settle which.

### Q7 — Plan completeness vs over-engineering

Read the plan in full. Is it specific enough that a future
contributor could implement Phase 1 from it alone? Or is anything
materially missing? Conversely: does the plan slip in new CI
tooling or infrastructure that the user has previously rejected
as "elaborate CI tooling as substitute for discipline" (see
`docs/issues/2026-05-23-ISS-001-self-approval-discipline.md`
closing note and `CONTRIBUTING.md` "Review Discipline" section)?

## Required output (no prefatory chit-chat)

Provide your full verbatim response under these top-level sections:

1. `## Summary` — one paragraph, terminal classification for U07.
2. `## U07 — c88f7ea` — findings, file:line, severity.
3. `## Q1 — R1 vs R2` — verified / refuted, with SPEC bytes.
4. `## Q2 — taxonomy` — soundness per shared assignment.
5. `## Q3 — inventory` — confirmed / refuted, with command output.
6. `## Q4 — SDP envelope` — verified / refuted, with descriptor
   bytes.
7. `## Q5 — phasing` — confirmed / refuted per kind challenged.
8. `## Q6 — closure_root` — verified / refuted.
9. `## Q7 — completeness` — verified / refuted, citing any
   missing specificity or any inadvertent infrastructure creep.
10. `## Process checks` — one line per
    `[policy.process_checks]` item.
11. `## Terminal verdict` — exactly one of
    `unconditional_approval` or `concrete_unresolvable_blocker`.
    Rationale tied to executed commands and inspected bytes.

## Persistence

Your full verbatim response will be saved to
`docs/reviews/2026-05-25-spec-13-retrofit-scoping-plan/raw_findings/<your_model_name>.md`
by the initiator session. Start with `## Summary`.
