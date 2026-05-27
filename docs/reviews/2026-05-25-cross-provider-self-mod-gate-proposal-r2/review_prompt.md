# Round-2 review — INV06 cross-provider self-mod implementation (2026-05-25)

Fresh-context reviewer. Narrow scope: verify commit `b7e2472`
closes the six dispositions (B1-B3 blockers, R1-R3 required revisions)
that round-1 review filed, without introducing new defects.

## Background — what r1 said (verify, don't trust)

r1 session: `docs/reviews/2026-05-25-cross-provider-self-mod-gate-proposal/`
r1 terminal: `terminal_decision.toml` (synthesized verdict
`concrete_unresolvable_blocker`).

- **codex** (`raw_findings/codex.md`): `concrete_unresolvable_blocker`,
  3 findings (C1-F1 ambiguous "and/or", C1-F2 predicate not chain-derivable,
  C2-F1 solo-tier coherence).
- **gemini** (`raw_findings/gemini.md`): `unconditional_approval` —
  acknowledged same issues at "low severity / posture choice", not
  blocker.
- **grok** (`raw_findings/grok.md`): `concrete_unresolvable_blocker`,
  2 findings (P01-C1 predicate, P01-C2 solo tier).
- **mistral**: unavailable (CLI not installed on host).

Codex + grok blockers bound per strongest-evidence rule (both
independently re-read solo.toml L21-60 and confirmed the C02/C05
contradiction; initiator subsequently re-verified the same bytes
and filed no rebuttal).

## Repository

- Working copy: `/srv/repos/external/verivus-oss/agent-assurance`
- Parent (pre-r2): `8a63abb`
- HEAD (post-r2): `b7e2472`
- Commit range: `8a63abb..b7e2472` (1 commit; 14 files modified +
  1 created)
- r2 bundle: `docs/reviews/2026-05-25-cross-provider-self-mod-gate-proposal-r2/review_bundle.toml`

## Rules (`tools/review-request-dag.toml [policy.*]`)

Verify against bytes; never accept the initiator's summary as evidence.
File:line + severity for every finding. `forbidden_approval_bases`:
`stated_intent`, `plan_compliance_claim`, `should_be_fixed_language`.
Terminal: `unconditional_approval` or `concrete_unresolvable_blocker`.

## What to verify

For each of B1, B2, B3, R1, R2, R3, classify as **closed**, **partial**,
or **open** with file:line evidence drawn from the diff at b7e2472.

### B1 closure — chain-verifiable self-modification predicate

- Read `profiles/agent-assurance/ontology.toml` at HEAD. A new
  `[[attribute_vocabularies]]` block with `attribute = "subject_class"`
  MUST exist, `applies_to = "gate-decision"`, with values including
  `"self-modification"`. IJB tagging MUST be `constraint/structural`
  per KD2.
- Read `profiles/agent-assurance/gate-decision-kind.toml`. The ROOT
  SHAPE prose MUST document a `[decision].subject_class` field. The
  field MUST NOT appear in `[[kind.required_fields]]` (i.e., it is
  additive-optional).
- The predicate "subject of change is the producer agent's own harness
  or source code" MUST now be representable as the artifact value
  `subject_class = "self-modification"`, not as runtime knowledge.
  Confirm by reading the new INV06 hard invariant and the
  `examples/self-modification-gate-decision.toml` worked example.

### B2 closure — tight AND, not "and/or"

- Read INV06 in `profiles/agent-assurance/gate-decision-kind.toml`.
  The rule MUST use 'MUST satisfy BOTH ... AND ...' or equivalent
  conjunctive wording. The exact text "and/or" MUST NOT appear in
  INV06.
- Run: `grep -n 'and/or' profiles/agent-assurance/gate-decision-kind.toml`
  MUST return zero matches (or only in non-INV06 unrelated prose;
  if any match exists, locate it and judge).
- The rule MUST explicitly state that
  same-provider/different-family AND different-provider/same-family
  BOTH fail. Cite the line.

### B3 closure — solo tier carve-out

- Read `profiles/agent-assurance/tiers/solo.toml` at HEAD. Contract
  C02 statement (line ~32) MUST explicitly exclude
  `subject_class = "self-modification"` gate-decisions from the AI
  self-sign permission, deferring to INV06.
- Contract C05 statement (line ~56) MUST do the same for the
  single-signer rule.
- Both C02 and C05 `verified_by` MUST include
  `"gate-decision-invariant:INV06@1"`.
- Confirm the carve-outs do not break the validator (run
  `python3 validators/validate_review_readiness.py profiles/agent-assurance/tiers/solo.toml`
  — MUST pass).

### R1 closure — additive-optional + conditional invariant

- Verify the four attribution fields (`proposing_provider_id`,
  `proposing_model_family_id`, `deciding_provider_id`,
  `deciding_model_family_id`) do NOT appear in
  `[[kind.required_fields]]`. Cite the absence by reading the
  `required_fields` block in full.
- Verify INV06 is the ONLY place these fields are required, and
  only conditional on `subject_class = "self-modification"`.
- Verify the pre-INV06 example (`examples/minimal-gate-decision.toml`)
  is UNCHANGED at HEAD (it has no `subject_class` and no provider
  attribution; INV06 should not trigger; the validator should still
  accept it):
  - `git show b7e2472 -- examples/minimal-gate-decision.toml` MUST
    show no diff (the file is unchanged in this commit).
  - `python3 validators/validate_ijb_conformance.py examples/minimal-gate-decision.toml --repo-root .` MUST pass.
- The `[kind.example]` entry for `minimal-gate-decision.toml` MUST
  state in its `inline_summary` that the pre-INV06 shape remains
  valid because INV06 only triggers on `subject_class = "self-modification"`.

### R2 closure — migration + posture

- Read `profiles/agent-assurance/overview.md` at HEAD. A "Scope and
  posture" section MUST exist with three substantive paragraphs:
  - (i) multi-provider operating assumption + rationale;
  - (ii) audience impact for single-provider / air-gapped / regulated
    deployments, giving them named coherent options;
  - (iii) migration note for existing profile users covering pre-INV06
    instance validity AND the new solo tier contract surface.
- Read `profiles/agent-assurance/tiers/README.md`. The solo row in the
  ladder table MUST reference INV06. A "Cross-tier rule" callout MUST
  make the profile-level (not per-tier) scope of INV06 explicit.

### R3 closure — no proper-noun in normative prose

- Run `grep -rni 'agent-federator\|federator' profiles/ SPEC.md core/`
  — MUST return zero matches. (Matches under `docs/reviews/` are
  acceptable because that is the persisted r1 audit trail, explicitly
  out of normative scope.)
- Verify the normative prose describes the runtime CONTRACT (what
  attribution metadata must be present, what predicates must hold,
  that implementations may vary), NOT a named broker role. Locate
  this prose in `gate-decision-kind.toml` (INV06 + CROSS-PROVIDER
  ATTRIBUTION section) and `overview.md` "Scope and posture".

### Reference DB + count-mirror plumbing

The committed change touches the non-normative `reference/database/`
seeds and the `tools/dagtoml-{duckdb,duckdb-go}` count hardcodes.
Verify the plumbing is internally consistent:

- `python3 validators/check_attribute_values.py` MUST exit 0 and print
  "COUNT-MIRROR OK".
- `bash validators/check_manifest_drift.sh` MUST exit 0 and print "OK".
- `tools/dagtoml-rdf/target/release/dagtoml-rdf verify -o reference/database/rdf/schema.ttl`
  MUST return 1400 triples (matching `expected_triple_counts.schema`).
- Cross-engine row consistency: postgres / duckdb / sqlite each MUST
  insert exactly 3 new vocabulary rows (`subject_class`, `provider_id`,
  `model_family_id`) and 22 new value rows (2 + 10 + 10). Engine-specific
  array syntax: `ARRAY[]`, `[]`, `json_array()` respectively.

### No new defects

- `git show --stat b7e2472` MUST show exactly the 14 files listed in
  the bundle; no SPEC.md change; no core/ change; no validator change.
- `python3 validators/validate_closure_root.py --discover .` MUST exit
  0 over all 75 affected files (one more than pre-commit count of 74
  because `examples/self-modification-gate-decision.toml` is new).
- No contradiction with `SPEC.md §5` hard invariants.
- No JSON Schema dependency introduced.
- No VAP-specific runtime name in any committed file.
- No drift between `*-kind.toml` and example: the new example
  (`examples/self-modification-gate-decision.toml`) MUST be pointed
  to from `gate-decision-kind.toml [[kind.example]]`.

### Cross-cutting

- CHANGELOG.md `[Unreleased] Added` entry MUST list every changed
  file, reference the r1 review as predecessor, and enumerate B1-B3 +
  R1-R3 closures explicitly. The CHANGELOG entry MUST NOT
  over-claim (e.g., promising round-2 approval before it's issued).

## Process checks (per `[policy.process_checks]`)

- Active-user migration / behavior-change guidance — verify R2 closure
  covers this; if R2 is closed, this check is satisfied.
- No historical dated spec retconned without link / correction note —
  verify the commit adds rather than retcons; flag if it modifies
  any pre-2026-05-25 dated artifact without a correction note.
- Claimed tests actually run with command output and status — the
  initiator listed validator runs in `bundle.units.summary`. Pick at
  least three of them, re-run independently, and report exit status.

## Required output (no prefatory chit-chat)

1. `## Summary` — terminal classification for the implementation.
2. `## B1 disposition` — closed / partial / open + file:line evidence.
3. `## B2 disposition` — closed / partial / open + file:line evidence.
4. `## B3 disposition` — closed / partial / open + file:line evidence.
5. `## R1 disposition` — closed / partial / open + file:line evidence.
6. `## R2 disposition` — closed / partial / open + file:line evidence.
7. `## R3 disposition` — closed / partial / open + file:line evidence.
8. `## Reference DB plumbing` — count-mirror + manifest-drift +
   RDF triple count + engine row consistency confirmation.
9. `## No new defects` — confirmation or list of new defects.
10. `## Process checks` — one per `[policy.process_checks]` item.
11. `## Terminal verdict` — `unconditional_approval` or
    `concrete_unresolvable_blocker`. Rationale tied to bytes /
    executed commands.

Persistence: your verbatim response will be saved to
`docs/reviews/2026-05-25-cross-provider-self-mod-gate-proposal-r2/raw_findings/<your_model_name>.md`.

Start with `## Summary`.
