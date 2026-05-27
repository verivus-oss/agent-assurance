# SPEC §13 Phase 1 retrofit — independent review (2026-05-25)

Fresh-context reviewer. Narrow scope: verify commit `140bd9e` lands
the four Phase 1 retrofits from the approved plan, without
introducing defects.

## Repository

- Working copy: `/srv/repos/external/verivus-oss/agent-assurance`
- Parent commit: `c63c57a` (kickoff-prompt land)
- HEAD: `140bd9e` (the commit under review)
- Commit range: `c63c57a..140bd9e` (1 commit; 5 files modified)
- Bundle: `docs/reviews/2026-05-25-spec-13-phase-1-observation-record/review_bundle.toml`

## Lineage

- Plan: `docs/planning/2026-05-25-spec-13-retrofit-scoping.md`
- Plan approved (unanimous, no blockers):
  `docs/reviews/2026-05-25-spec-13-retrofit-scoping-plan-r2/terminal_decision.toml`
- Reference shape (the only kind that declared §13 before this commit):
  `profiles/cost/cost-record-kind.toml:282-327`

## Rules (`tools/review-request-dag.toml [policy.*]`)

Verify against bytes; never accept summary. File:line + severity.
`forbidden_approval_bases`: stated_intent, plan_compliance_claim,
should_be_fixed_language. Terminal: `unconditional_approval` or
`concrete_unresolvable_blocker`.

## What to verify

### U01 — evidence-matrix retrofit

- File: `core/evidence-matrix-kind.toml`.
- The new `[kind.abstraction_class]` block MUST:
  - declare `id = "observation-record.v1"`.
  - declare a non-empty `description` that names the kind's own
    `[[claims]]` / `[[evidence]]` / `[[matrix]]` shape (NOT the
    cost-record `dimensions` text).
  - carry `ijb_primitive = "constraint"` + `ijb_constraint_type = "structural"`.
- The new `[kind.capability_envelope]` block MUST be Family A: all
  9 capability domains explicitly present and denied/zeroed (per
  SPEC §13.9 missing = denied, but the cost-record reference at
  `profiles/cost/cost-record-kind.toml:288-327` makes them explicit).
- The descriptor's root-level `closure_root` MUST still be the empty
  sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
  (per SPEC §12.11 + plan §9 — descriptors that cite no upstream
  evidence stay at the sentinel).

### U02 — gate-decision retrofit

- File: `profiles/agent-assurance/gate-decision-kind.toml`.
- Same shape checks as U01, with the description naming gate-decision's
  own structural shape (verdict / evidence_root / cited_bundles /
  failed_constraint_refs / override_refs / decided_at), NOT the
  cost-record dimensions text and NOT a verbatim copy of evidence-matrix's
  description.

### U03 — assertion-log-record retrofit

- File: `profiles/agent-assurance/assertion-log-record-kind.toml`.
- Same shape checks. Description names index / prev_hash / bundle_hash /
  signer_id / signature / signature_algorithm / hash_algorithm /
  canonical_form / timestamp per the kind's own required fields.
- The accompanying header comment SHOULD note that signature
  verification, prev_hash chain checks, and timestamp corroboration
  are RUNTIME-SPEC and lie outside this envelope (consistent with
  the kind's existing INV04).

### U04 — redaction-manifest retrofit

- File: `profiles/disclosure/redaction-manifest-kind.toml`.
- Same shape checks. Description names `[[redactions]]` entries with
  subject / locator / closed-vocabulary redaction_method /
  redaction_reason (+ conditional notes for reason='other').
- The accompanying header comment SHOULD note that cryptographic
  verification (that the published bytes match the source modulo
  the listed redactions) is delegated to the matching
  selective-disclosure-proof and is RUNTIME-SPEC.

### U05 — validators all green

Re-run each command and report the exact one-line summary:

```sh
python3 validators/validate_abstraction_class.py --repo-root . \
  core/*-kind.toml profiles/agent-assurance/*-kind.toml \
  profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml
# MUST report: 19 file(s) checked; 5 declared a §13 block.

for f in core/*-kind.toml profiles/agent-assurance/*-kind.toml \
         profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml; do
  python3 validators/validate_ijb_conformance.py "$f"
done
# Every line MUST be IJB CONFORMANCE VALIDATION PASSED.

for f in core/*-kind.toml profiles/agent-assurance/*-kind.toml \
         profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml; do
  python3 validators/validate_kind_descriptor.py "$f" \
    --repo-root . --check-references-exist
done
# Every line MUST be KIND DESCRIPTOR VALIDATION PASSED.

python3 validators/validate_closure_root.py --discover .
# MUST report: CLOSURE-ROOT VALIDATION PASSED (74 file(s)).

taplo lint core/*-kind.toml profiles/*/*-kind.toml
# No FAIL lines.
```

### U06 — per-kind-description rule

Plan §6 (lines 201-209) says when kinds share a class id, each MUST
declare a kind-specific description. The reference is cost-record's
description at `profiles/cost/cost-record-kind.toml:284`.

Run:

```sh
grep -nE '^description ' core/evidence-matrix-kind.toml \
  profiles/agent-assurance/gate-decision-kind.toml \
  profiles/agent-assurance/assertion-log-record-kind.toml \
  profiles/disclosure/redaction-manifest-kind.toml \
  profiles/cost/cost-record-kind.toml
```

Confirm all five description strings are textually distinct. Confirm
none of the four new descriptions copy the cost-record dimensions
text verbatim. Confirm each description ties back to the kind's own
`[[kind.required_fields]]` / `[[kind.required_sections]]` (read the
descriptor file's earlier required-fields/sections rows for context).

### U07 — closure_root sentinel preserved

```sh
grep -n 'closure_root' \
  core/evidence-matrix-kind.toml \
  profiles/agent-assurance/gate-decision-kind.toml \
  profiles/agent-assurance/assertion-log-record-kind.toml \
  profiles/disclosure/redaction-manifest-kind.toml
```

Every match MUST be the empty-closure sentinel
`sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
at line 5 of each file. Per plan §9, the file's SHA-256 flips
(because the bytes change) but its declared `closure_root` value does
not (because none of these descriptors cite upstream evidence).

### U08 — scope discipline

```sh
git show --stat 140bd9e
git diff --name-only c63c57a..140bd9e
```

MUST show exactly 5 files modified:
- `CHANGELOG.md`
- `core/evidence-matrix-kind.toml`
- `profiles/agent-assurance/assertion-log-record-kind.toml`
- `profiles/agent-assurance/gate-decision-kind.toml`
- `profiles/disclosure/redaction-manifest-kind.toml`

MUST NOT include:
- `SPEC.md`
- `docs/planning/2026-05-25-spec-13-retrofit-scoping.md`
- any of the other 13 kind descriptors
- any validator under `validators/`
- any ontology under `core/ontology.toml` or
  `profiles/*/ontology.toml`

Per plan §11 and the kickoff prompt's OUT OF SCOPE list, Phase 1 is
deliberately narrow.

### Cross-cutting checks

- The class id `observation-record.v1` MUST match the closed pattern
  `<slug>.v<integer>` (`validators/validate_abstraction_class.py:52`,
  ID_PATTERN). Confirm by re-running the abstraction-class validator
  (already covered by U05) and by inspecting the regex.
- Each `[kind.capability_envelope]` MUST declare exactly the 9
  capability-domain sub-tables from the closed
  `capability_envelope.domain` vocabulary in `core/ontology.toml`
  (`validators/validate_abstraction_class.py:_load_domains`,
  used at line 312-318). Confirm by reading the validator's domain
  loader and the four new envelope blocks.
- Each `random` sub-table MUST use one of the three accepted entropy
  sources `os | deterministic_seed | none` (validator at
  `validators/validate_abstraction_class.py:182-191`). Confirm
  `entropy_source = "none"` in all four.
- Each `crypto_keys` sub-table MUST be denied (`denied = true`); the
  validator at `:214-223` accepts only `read_keys | use_keys |
  generate_allowed` if not denied. Confirm denial in all four.

## Required output (no prefatory chit-chat)

1. `## Summary` — terminal classification for the whole commit.
2. `## U01 — evidence-matrix` — complete / incomplete / unverifiable +
   file:line evidence.
3. `## U02 — gate-decision` — same.
4. `## U03 — assertion-log-record` — same.
5. `## U04 — redaction-manifest` — same.
6. `## U05 — validators all green` — exit codes + summary lines.
7. `## U06 — per-kind-description rule` — confirm distinctness of all
   5 descriptions and per-kind shape coverage.
8. `## U07 — closure_root sentinel preserved` — confirm sentinel
   present at line 5 of all four files; confirm validator exit 0.
9. `## U08 — scope discipline` — confirm exactly 5 files modified;
   confirm none of the forbidden files touched.
10. `## Process checks` — one per `[policy.process_checks]` item:
    - active-user migration/behavior-change guidance present?
    - no historical dated spec retconned without link/correction note?
    - claimed tests actually run with command output and status?
11. `## Terminal verdict` — `unconditional_approval` or
    `concrete_unresolvable_blocker`. Rationale tied to bytes /
    executed commands.

Persistence: your verbatim response will be saved to
`docs/reviews/2026-05-25-spec-13-phase-1-observation-record/raw_findings/<your_model_name>.md`.

Start with `## Summary`.
