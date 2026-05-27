# SPEC §13 Phase 3 retrofit — independent review (2026-05-25)

Fresh-context reviewer. Narrow scope: verify commit `3749398` lands
the final 5 §13 retrofits from the approved plan, without
introducing defects. This is the PHASE-TERMINAL commit (14/19 →
19/19).

## Repository

- Working copy: `/srv/repos/external/verivus-oss/agent-assurance`
- Parent commit: `8a5e715` (Phase 2 r2 review persisted)
- HEAD: `3749398` (the commit under review)
- Commit range: `8a5e715..3749398` (1 commit; 6 files modified)
- Bundle: `docs/reviews/2026-05-25-spec-13-phase-3-procedure-and-special/review_bundle.toml`

## Lineage

- Plan: `docs/planning/2026-05-25-spec-13-retrofit-scoping.md`
- Plan approved (unanimous):
  `docs/reviews/2026-05-25-spec-13-retrofit-scoping-plan-r2/terminal_decision.toml`
- Phase 1 approved:
  `docs/reviews/2026-05-25-spec-13-phase-1-observation-record/terminal_decision.toml`
- Phase 2 r2 approved:
  `docs/reviews/2026-05-25-spec-13-phase-2-declarations-r2/terminal_decision.toml`
- Reference shapes:
  - `profiles/cost/cost-record-kind.toml:282-327` (Phase 0)
  - Phase 1 + Phase 2 retrofits at `140bd9e` + `092bccc` + `6b63860`

## Rules (`tools/review-request-dag.toml [policy.*]`)

Verify against bytes; never accept the bundle summary. File:line +
severity. `forbidden_approval_bases`: stated_intent,
plan_compliance_claim, should_be_fixed_language. Terminal:
`unconditional_approval` or `concrete_unresolvable_blocker`.

## What to verify

For each of U01..U05 (the five retrofitted kinds), check:

1. `[kind.abstraction_class]` declares the expected `id` (see the
   bundle's `class_id` field for each unit). All five are unique in
   this phase (procedure-declaration.v1, validation-record.v1,
   assertion-set.v1, interface-contract.v1, cryptographic-proof.v1)
   so the per-kind-description rule is trivially satisfied.
2. `description` is non-empty and names the kind's OWN structural
   shape (read the descriptor's earlier `[[kind.required_fields]]` /
   `[[kind.required_sections]]` / `[[kind.hard_invariants]]` rows for
   context — the description should cite the same fields).
3. IJB tags `ijb_primitive = "constraint"` +
   `ijb_constraint_type = "structural"` are present.
4. `[kind.capability_envelope]` is Family A: all 9 capability domains
   explicitly present and denied/zeroed.
5. The descriptor's root-level `closure_root` is still the empty
   sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

### U04 — adapter-contract (R1/R2 ambiguity, highest scrutiny)

Plan §7 row 7 + §8 Phase 3 explicitly flagged this kind for R1/R2
reviewer challenge. The §13 header comment in `adapter-contract-kind.toml`
is extra-explicit about adopting R1 (envelope bounds descriptor parse)
and rejecting R2 (which would either be unbounded or duplicate the
instance-level `[adapter].runtime_*` fields).

The reviewer's job here: if you can cite **byte-level evidence in the
kind's existing prose, required-fields, or worked example
(`examples/minimal-adapter-contract.toml`)** that the spec author
intended R2 — i.e., that the kind descriptor's envelope SHOULD bound
what a deployed adapter is permitted at runtime — file a blocker
with file:line. Otherwise R1 stands per plan §5 and the §13 header's
own reasoning.

Read:
- `profiles/agent-assurance/adapter-contract-kind.toml` (full)
- `examples/minimal-adapter-contract.toml`
- `docs/planning/2026-05-25-spec-13-retrofit-scoping.md` §5 (lines
  109-164), §7 row 7 (line 221), §8 Phase 3 (lines 258-266)

Specifically check whether the kind's instance-level `[adapter]`
table fields (`runtime_kind`, `runtime_network_policy`,
`runtime_clock_policy`, `runtime_env_allowlist`) being the existing
runtime-policy surface AT INSTANCE LEVEL supports R1 (instance-level
is where runtime policy lives) or R2 (descriptor-level envelope
should mirror / constrain them).

### U05 — selective-disclosure-proof (Family A correctness)

Per plan §5 Family-B/C-exceptions paragraph (lines 141-154) the
SPEC-layer parse is shape-only; cryptographic verification is
RUNTIME-SPEC. Codex r1 on the plan caught two earlier-draft defects
in a proposed Family C envelope:

- `entropy_source = "system"` is not in
  `validators/validate_abstraction_class.py:182` accepted set
  (`os | deterministic_seed | none`).
- `crypto_keys.sign / verify` is not in
  `validators/validate_abstraction_class.py:214-223` accepted set
  (`read_keys | use_keys | generate_allowed`).

The kind's own prose at lines 61-62 (pre-commit) delegates verification
to RUNTIME-SPEC. Verify the §13 retrofit adopts Family A (all 9 domains
denied/zeroed, `entropy_source = "none"`, `crypto_keys.denied = true`).
If a reviewer believes a wider envelope is justified, the bar is
byte-level evidence in the kind's existing prose plus a field-name set
that the validator accepts.

### U06 — aggregate validators green at 19/19 (PHASE-TERMINAL)

Re-run each command and report the exact one-line summary:

```sh
python3 validators/validate_abstraction_class.py --repo-root . \
  core/*-kind.toml profiles/agent-assurance/*-kind.toml \
  profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml
# MUST report: 19 file(s) checked; 19 declared a §13 block.

for f in core/*-kind.toml profiles/agent-assurance/*-kind.toml \
         profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml; do
  python3 validators/validate_ijb_conformance.py "$f"
done | grep -c 'IJB CONFORMANCE VALIDATION PASSED'
# MUST be 19.

for f in core/*-kind.toml profiles/agent-assurance/*-kind.toml \
         profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml; do
  python3 validators/validate_kind_descriptor.py "$f" \
    --repo-root . --check-references-exist
done | grep -c 'KIND DESCRIPTOR VALIDATION PASSED'
# MUST be 19.

python3 validators/validate_closure_root.py --discover .
# MUST report: CLOSURE-ROOT VALIDATION PASSED (74 file(s)).

taplo lint core/*-kind.toml profiles/*/*-kind.toml
# No FAIL lines.
```

### U07 — no forbidden-phrase leak (Phase 2 r1 lesson applied)

Phase 2 r1 caught a "risk posture" leak in the threat-model §13
header comment. For Phase 3 the initiator pre-flighted all 5 files
for similar invariants. Re-run the pre-flight grep against HEAD:

```sh
for f in profiles/agent-assurance/rollback-plan-kind.toml \
         profiles/agent-assurance/smoke-validation-kind.toml \
         profiles/agent-assurance/assertion-bundle-kind.toml \
         profiles/agent-assurance/adapter-contract-kind.toml \
         profiles/disclosure/selective-disclosure-proof-kind.toml; do
  echo "--- $f ---"
  grep -niE 'forbidden|MUST NOT appear|only in this note|do not (appear|use)|MUST NOT use' "$f" \
    || echo "(no matches)"
done
```

Expected: zero matches in every file. Any match indicates either a
pre-existing forbidden-phrase rule the §13 header MUST honor, or a
new leak introduced by the retrofit. File a blocker if either.

### U08 — closure_root sentinel preserved

```sh
grep -n 'closure_root' \
  profiles/agent-assurance/rollback-plan-kind.toml \
  profiles/agent-assurance/smoke-validation-kind.toml \
  profiles/agent-assurance/assertion-bundle-kind.toml \
  profiles/agent-assurance/adapter-contract-kind.toml \
  profiles/disclosure/selective-disclosure-proof-kind.toml
```

Every match MUST be the empty-closure sentinel. The Phase 2 line-5
quibble is moot here — all five Phase 3 files happen to have their
sentinel at line 5 (no multi-line header comments above the
sentinel). The substantive rule (SPEC §12.11) is sentinel VALUE,
not line number.

### U09 — scope discipline

```sh
git show --stat 3749398
git diff --name-only 8a5e715..3749398
```

MUST show exactly 6 files modified — the 5 retrofitted kind
descriptors + `CHANGELOG.md`. MUST NOT include:

- `SPEC.md`
- `docs/planning/2026-05-25-spec-13-retrofit-scoping.md`
- any Phase 1 or Phase 2 kind descriptor
- any validator under `validators/`
- any `ontology.toml` under `core/` or `profiles/`

### Cross-cutting checks

- Class id `<slug>.v<integer>` pattern: every new id matches the
  regex at `validators/validate_abstraction_class.py:52`. The five
  new ids are `procedure-declaration.v1`, `validation-record.v1`,
  `assertion-set.v1`, `interface-contract.v1`,
  `cryptographic-proof.v1`.
- Each `[kind.capability_envelope]` declares all 9 capability-domain
  sub-tables from the closed `capability_envelope.domain` vocabulary
  (`validators/validate_abstraction_class.py:_load_domains`).
- Each `random` sub-table uses `entropy_source = "none"` (validator
  at `:182-191`).
- Each `crypto_keys` sub-table is `denied = true` (validator at
  `:214-223`).
- IJB tags on both `[kind.abstraction_class]` and
  `[kind.capability_envelope]` carry `ijb_primitive = "constraint"` +
  `ijb_constraint_type = "structural"`.

## Required output (no prefatory chit-chat)

1. `## Summary` — terminal classification for the whole commit.
2. `## U01 — rollback-plan` through `## U05 — selective-disclosure-proof`
   (one section each): complete / incomplete / unverifiable + file:line
   evidence.
3. `## U06 — validators green at 19/19` — exit codes + summary lines.
4. `## U07 — no forbidden-phrase leak` — grep output for all 5 files.
5. `## U08 — closure_root sentinel preserved` — grep + validator output.
6. `## U09 — scope discipline` — confirm exactly 6 files modified.
7. `## Process checks` — one per `[policy.process_checks]` item:
   - active-user migration/behavior-change guidance present?
   - no historical dated spec retconned without link/correction note?
   - claimed tests actually run with command output and status?
8. `## Terminal verdict` — `unconditional_approval` or
   `concrete_unresolvable_blocker`. Rationale tied to bytes /
   executed commands.

Persistence: your verbatim response will be saved to
`docs/reviews/2026-05-25-spec-13-phase-3-procedure-and-special/raw_findings/<your_model_name>.md`.

Start with `## Summary`.
