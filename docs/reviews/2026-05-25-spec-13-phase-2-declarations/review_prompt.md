# SPEC §13 Phase 2 retrofit — independent review (2026-05-25)

Fresh-context reviewer. Narrow scope: verify commit `092bccc` lands
the nine Phase 2 retrofits from the approved plan, without
introducing defects.

## Repository

- Working copy: `/srv/repos/external/verivus-oss/agent-assurance`
- Parent commit: `ec37e7d` (Phase 1 review persisted)
- HEAD: `092bccc` (the commit under review)
- Commit range: `ec37e7d..092bccc` (1 commit; 10 files modified)
- Bundle: `docs/reviews/2026-05-25-spec-13-phase-2-declarations/review_bundle.toml`

## Lineage

- Plan: `docs/planning/2026-05-25-spec-13-retrofit-scoping.md`
- Plan approved (unanimous):
  `docs/reviews/2026-05-25-spec-13-retrofit-scoping-plan-r2/terminal_decision.toml`
- Phase 1 implementation approved (unanimous):
  `docs/reviews/2026-05-25-spec-13-phase-1-observation-record/terminal_decision.toml`
- Reference shapes:
  - `profiles/cost/cost-record-kind.toml:282-327` (Phase 0)
  - Four Phase 1 retrofits at `140bd9e` (load-bearing per-kind-description
    examples)

## Rules (`tools/review-request-dag.toml [policy.*]`)

Verify against bytes; never accept the bundle summary. File:line +
severity. `forbidden_approval_bases`: stated_intent,
plan_compliance_claim, should_be_fixed_language. Terminal:
`unconditional_approval` or `concrete_unresolvable_blocker`.

## What to verify

For each unit U01..U09 (the nine retrofitted kinds), check:

1. `[kind.abstraction_class]` declares the expected `id` (see the
   bundle's `class_id` field for each unit).
2. `description` is non-empty and names the kind's OWN structural
   shape (read the descriptor's earlier `[[kind.required_fields]]` /
   `[[kind.required_sections]]` / `[[kind.hard_invariants]]` rows for
   context — the description should cite the same fields).
3. IJB tags `ijb_primitive = "constraint"` +
   `ijb_constraint_type = "structural"` are present.
4. `[kind.capability_envelope]` is Family A: all 9 capability domains
   explicitly present and denied/zeroed (per the cost-record reference).
5. The descriptor's root-level `closure_root` is still the empty
   sentinel
   `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
   at line 5.

### U01..U03 — three policy-declaration.v1 kinds

The three descriptions MUST be textually distinct (per plan §6,
lines 201-209). Run:

```sh
grep -nE '^description ' core/contract-declaration-kind.toml \
  core/readiness-gate-kind.toml \
  profiles/agent-assurance/spec-contract-kind.toml \
  | grep -A0 'Declarative policy artefact'
```

Three lines, three different strings, each citing the kind's own
required-fields/sections (contracts vs artifact_classes+gates vs
guarantees+non_goals+invariants).

### U04 — implementation-dag (R1 envelope nuance)

The plan flagged R1 vs R2 as the principal interpretive question for
this kind (plan §5, §8 Phase 3 note). The retrofit MUST adopt R1:
the envelope bounds the descriptor PARSE only, not the runtime of the
units the DAG describes. Verify:

- The `[kind.abstraction_class].description` says so explicitly.
- The header comment above the §13 block says so explicitly.
- The envelope is Family A (denied/zeroed) — NOT a wide envelope that
  would have to cover whatever any described unit might demand.

### U08 — threat-model (no "risk posture" leak)

The kind's existing IJB-stance note (lines 64-77 pre-commit) forbids
the phrase "risk posture" as a field name, value, kind label, or
conforming-instance concept. The §13 description MUST NOT introduce
it. Run:

```sh
grep -n 'risk posture' profiles/agent-assurance/threat-model-kind.toml
```

The only allowed match is inside the existing IJB-stance note; the new
abstraction-class description (look at the `description = "..."` line
under `[kind.abstraction_class]`) MUST be clean.

### U10 — validators all green

Re-run each command and report the exact one-line summary:

```sh
python3 validators/validate_abstraction_class.py --repo-root . \
  core/*-kind.toml profiles/agent-assurance/*-kind.toml \
  profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml
# MUST report: 19 file(s) checked; 14 declared a §13 block.

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

### U11 — per-kind-description rule

Confirm the three `policy-declaration.v1` descriptions are textually
distinct AND that each names the kind's own structural shape. The
other six Phase 2 class ids (`plan-decomposition.v1`,
`extension-declaration.v1`, `relation-ledger.v1`,
`binding-declaration.v1`, `threat-declaration.v1`,
`attestation-record.v1`) are each used by exactly one kind in this PR;
the rule is trivially satisfied. Also cross-check against the
five Phase 0+1 `observation-record.v1` descriptions — they should not
collide with any Phase 2 description because the class ids differ.

### U12 — closure_root sentinel preserved

```sh
grep -n 'closure_root' \
  core/contract-declaration-kind.toml \
  core/readiness-gate-kind.toml \
  core/implementation-dag-kind.toml \
  core/profile-descriptor-kind.toml \
  core/traceability-kind.toml \
  profiles/agent-assurance/spec-contract-kind.toml \
  profiles/agent-assurance/adapter-registry-binding-kind.toml \
  profiles/agent-assurance/threat-model-kind.toml \
  profiles/disclosure/disclosure-attestation-kind.toml
```

Every match MUST be the empty-closure sentinel at line 5 of each file.
Per plan §9, the file's SHA-256 flips (because the bytes change) but
the declared `closure_root` value does not (these descriptors cite no
upstream evidence).

### U13 — scope discipline

```sh
git show --stat 092bccc
git diff --name-only ec37e7d..092bccc
```

MUST show exactly 10 files modified — the 9 retrofitted kind
descriptors + `CHANGELOG.md`. MUST NOT include:

- `SPEC.md`
- `docs/planning/2026-05-25-spec-13-retrofit-scoping.md`
- the 5 Phase 3 kinds (`rollback-plan-kind.toml`,
  `smoke-validation-kind.toml`, `assertion-bundle-kind.toml`,
  `adapter-contract-kind.toml`, `selective-disclosure-proof-kind.toml`)
- the 4 Phase 1 kinds or `cost-record-kind.toml`
- any validator under `validators/`
- any `ontology.toml` under `core/` or `profiles/`

### Cross-cutting checks

- Class id `<slug>.v<integer>` pattern: every new id matches the regex
  at `validators/validate_abstraction_class.py:52`. The seven new ids
  are `policy-declaration.v1` (×3), `plan-decomposition.v1`,
  `extension-declaration.v1`, `relation-ledger.v1`,
  `binding-declaration.v1`, `threat-declaration.v1`,
  `attestation-record.v1`.
- Each `[kind.capability_envelope]` declares all 9 capability-domain
  sub-tables from the closed `capability_envelope.domain` vocabulary
  (loaded at `validators/validate_abstraction_class.py:_load_domains`).
- Each `random` sub-table uses `entropy_source = "none"` (validator at
  `:182-191`).
- Each `crypto_keys` sub-table is `denied = true` (validator at
  `:214-223`).
- IJB tags on both `[kind.abstraction_class]` and
  `[kind.capability_envelope]` carry `ijb_primitive = "constraint"` +
  `ijb_constraint_type = "structural"`.

### Plan-header off-by-one (informational, not a defect to file)

Plan §8 Phase 2 header literally reads "(8 kinds)" but the enumeration
below lists 9 kinds. The plan-§3 inventory of 18 missing-§13 kinds
plus the Phase 4+9+5 = 18 split confirms 9 is the correct count for
this phase. The kickoff prompt for Phase 1 said "Do NOT modify the
plan", and that rule still applies here. Reviewers MAY note this as
follow-up but it is NOT a defect in this commit.

## Required output (no prefatory chit-chat)

1. `## Summary` — terminal classification for the whole commit.
2. `## U01 — contract-declaration` through `## U09 — disclosure-attestation`
   (one section each): complete / incomplete / unverifiable + file:line
   evidence.
3. `## U10 — validators all green` — exit codes + summary lines.
4. `## U11 — per-kind-description rule` — confirm distinctness for the
   three policy-declaration.v1 descriptions; spot-check the others.
5. `## U12 — closure_root sentinel preserved` — confirm sentinel
   present at line 5 of all 9 files; confirm validator exit 0.
6. `## U13 — scope discipline` — confirm exactly 10 files modified;
   confirm none of the forbidden files touched.
7. `## Process checks` — one per `[policy.process_checks]` item:
   - active-user migration/behavior-change guidance present?
   - no historical dated spec retconned without link/correction note?
   - claimed tests actually run with command output and status?
8. `## Terminal verdict` — `unconditional_approval` or
   `concrete_unresolvable_blocker`. Rationale tied to bytes /
   executed commands.

Persistence: your verbatim response will be saved to
`docs/reviews/2026-05-25-spec-13-phase-2-declarations/raw_findings/<your_model_name>.md`.

Start with `## Summary`.
