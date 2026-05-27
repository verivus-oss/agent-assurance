## Summary

**unconditional_approval**

All eight units (U01–U08) verified complete against repo bytes and executed command output. All required approval bases satisfied via inspected files (absolute paths), re-executed validators with quoted stdout, sqry semantic searches on validator logic + ontology, git diffs, and explicit process confirmations. No defects found. No forbidden bases used. Terminal state per `tools/review-request-dag.toml:94`.

## U01 — evidence-matrix

**complete**

- File inspected: `/srv/repos/external/verivus-oss/agent-assurance/core/evidence-matrix-kind.toml` (210 lines post-commit).
- `closure_root` at line 5: `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (sentinel).
- `[kind.abstraction_class]` (lines 166-172): `id = "observation-record.v1"`, non-empty `description` naming own `[[claims]]`, `[[evidence]]`, `[[matrix]]` tables + cross-refs + scope/exclusions (ties to `[[kind.required_sections]]` at lines 90-106 pre-existing), `ijb_primitive = "constraint"`, `ijb_constraint_type = "structural"`.
- `[kind.capability_envelope]` + 9 domains + `crypto_keys` (lines 174-210): Family A, all explicit, `cpu_bounds` 100ms/5%, `memory_bounds` 1048576, all denied or zeroed (`entropy_source = "none"`, clocks false/0), `crypto_keys` denied. Matches cost-record reference shape at `profiles/cost/cost-record-kind.toml:288-327` except kind-specific comment.
- Header comment (lines 155-163) explains observation-of-coverage role and RUNTIME-SPEC boundary.
- Per-kind validator: `python3 validators/validate_abstraction_class.py --repo-root . core/evidence-matrix-kind.toml` → "ABSTRACTION-CLASS VALIDATION PASSED (1 file(s) checked; 1 declared a §13 block)."
- sqry semantic search + read confirmed ID_PATTERN and domain loader enforce closed set from `core/ontology.toml`.

## U02 — gate-decision

**complete**

- File inspected: `/srv/repos/external/verivus-oss/agent-assurance/profiles/agent-assurance/gate-decision-kind.toml` (234 lines).
- `closure_root` at line 5: sentinel (confirmed via grep).
- `[kind.abstraction_class]` (lines 190-196): `id = "observation-record.v1"`, description names own shape (`[decision].verdict`, `evidence_root`, `[[decision.cited_bundles]]` / failed_constraint_refs / override_refs, `decided_at` RFC3339) per `[[kind.required_fields]]` (lines 81-117 pre-existing), IJB tags correct.
- `[kind.capability_envelope]` (lines 198-234): Family A, all 9 + crypto_keys, identical bounds/denials.
- INV05 (lines 170-175) explicitly scopes signature/chain/timestamp/crypto verification as RUNTIME-SPEC.
- Header comment (lines 178-188) notes RUNTIME-SPEC delegation.
- Per-kind validator: "ABSTRACTION-CLASS VALIDATION PASSED".
- Description textually distinct from cost-record (no "dimensions + integer quantities" copy).

## U03 — assertion-log-record

**complete**

- File inspected: `/srv/repos/external/verivus-oss/agent-assurance/profiles/agent-assurance/assertion-log-record-kind.toml` (254 lines).
- `closure_root` at line 5: sentinel.
- `[kind.abstraction_class]` (lines 210-216): `id = "observation-record.v1"`, description names own fields (`[record].index`, `prev_hash`, `bundle_hash`, `signer_id`, `signature`, closed-vocab algorithms/canonical_form, `timestamp`) per `[[kind.required_fields]]` (lines 81-147), IJB tags.
- `[kind.capability_envelope]` (lines 218-254): Family A, all 9 + crypto_keys.
- INV04 (lines 160-165) explicitly states "SPEC-layer validation MUST NOT verify ... signature, prev_hash chain ... timestamp corroboration. Those checks are RUNTIME-SPEC."
- Header comment (lines 168-178) matches prompt requirement: "signature verification, prev_hash chain checks, and timestamp corroboration are RUNTIME-SPEC and lie outside this envelope".
- Per-kind validator pass. Description distinct (names log-record specific fields).

## U04 — redaction-manifest

**complete**

- File inspected: `/srv/repos/external/verivus-oss/agent-assurance/profiles/disclosure/redaction-manifest-kind.toml` (199 lines).
- `closure_root` at line 5: sentinel.
- `[kind.abstraction_class]` (lines 155-161): `id = "observation-record.v1"`, description names `[[redactions]]` entries (subject, locator, closed-vocab `redaction_method`, `redaction_reason` + mandatory notes when 'other') per INV01-INV03 (lines 89-114 pre-existing), IJB tags.
- `[kind.capability_envelope]` (lines 163-199): Family A, all 9 + crypto_keys.
- Header comment (lines 140-152) notes: "Cryptographic verification that the published bytes match the source modulo the listed redactions is delegated to the matching selective-disclosure-proof and is RUNTIME-SPEC".
- Per-kind validator pass. Description distinct (names redactions table + conditional notes rule).

## U05 — validators all green

**complete** (all commands executed; exact outputs quoted)

1. `python3 validators/validate_abstraction_class.py --repo-root . core/*-kind.toml profiles/agent-assurance/*-kind.toml profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml`
   - Output: `ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 5 declared a §13 block).`
   - Exit: 0. (5 includes the four new + cost-record reference.)

2. `for f in core/*-kind.toml profiles/agent-assurance/*-kind.toml profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml; do python3 validators/validate_ijb_conformance.py "$f"; done`
   - All 19 lines: `IJB CONFORMANCE VALIDATION PASSED` (including the four retrofitted and cost-record). Exit: 0 for loop.

3. `for f in ...; do python3 validators/validate_kind_descriptor.py "$f" --repo-root . --check-references-exist; done`
   - All 19: `KIND DESCRIPTOR VALIDATION PASSED` (with per-file invariant counts; the four show 4/5/4/4 invariants). Exit: 0.

4. `python3 validators/validate_closure_root.py --discover .`
   - Output: `CLOSURE-ROOT VALIDATION PASSED (74 file(s)).`
   - Exit: 0.

5. `taplo lint core/*-kind.toml profiles/*/*-kind.toml`
   - Exit: 0. Only INFO lines (19 files collected, 0 excluded); no FAIL, no error output.

Per-kind abstraction runs on the four also all PASSED.

## U06 — per-kind-description rule

**complete**

- `grep -n 'observation-record.v1' ...` (executed): appears exactly in the five expected files (evidence-matrix:166, gate-decision:190, assertion-log:210, redaction:155, cost-record:283). No others.
- `grep -nE '^description ' ...` (executed, full output in thinking trace): the five §13-level descriptions (evidence-matrix:167, gate:191, assertion:211, redaction:156, cost:284) are textually distinct.
  - cost: "Read-only observation artefact: declares hashed citations to prior actions + closed-vocabulary categorical dimensions + integer quantities. ..."
  - evidence-matrix: names "three connected `[[claims]]`, `[[evidence]]`, and `[[matrix]]` tables ..."
  - gate-decision: names "mechanical outcome ... `[decision].verdict`, ... `evidence_root`, ... cited_bundles / failed_constraint_refs / override_refs ... `decided_at`"
  - assertion-log: names "one append-only log record ... `[record].index`, `prev_hash`, `bundle_hash`, ... signature_algorithm ... canonical_form, ... `timestamp`"
  - redaction: names "`[[redactions]]` entries naming ... (`subject`, `locator`), ... `redaction_method`, ... `redaction_reason`, plus ... `notes` ... when `redaction_reason = \"other\"`"
- None of the four copy the cost "dimensions + integer quantities" text.
- Each ties to its own `[[kind.required_fields]]` / `[[kind.required_sections]]` (cross-checked against file contents at the listed line ranges).

## U07 — closure_root sentinel preserved

**complete**

- `grep -n 'closure_root' ...` (executed): all four files report the exact sentinel at line 5 only.
  - evidence-matrix-kind.toml:5
  - gate-decision-kind.toml:5
  - assertion-log-record-kind.toml:5
  - redaction-manifest-kind.toml:5
- `python3 validators/validate_closure_root.py --discover .` (re-executed): `CLOSURE-ROOT VALIDATION PASSED (74 file(s)).` (includes the four; their declared value did not flip despite byte changes).
- Matches plan §9 + SPEC §12.11 expectation (descriptors cite no upstream evidence).

## U08 — scope discipline

**complete**

- `git show --stat 140bd9e` (executed): exactly 5 files changed, +261 insertions:
  - CHANGELOG.md
  - core/evidence-matrix-kind.toml
  - profiles/agent-assurance/assertion-log-record-kind.toml
  - profiles/agent-assurance/gate-decision-kind.toml
  - profiles/disclosure/redaction-manifest-kind.toml
- `git diff --name-only c63c57a..140bd9e` (executed): exactly those 5; no others.
- Confirmed absent (forbidden per plan §11 + prompt):
  - SPEC.md (0 mentions in diff)
  - docs/planning/2026-05-25-spec-13-retrofit-scoping.md
  - any other *-kind.toml (13 untouched)
  - validators/ (none)
  - core/ontology.toml or profiles/*/ontology.toml (none)
- Matches Phase 1 narrow scope (plan §8 lines 239-249).

## Process checks

- **active-user migration/behavior-change guidance present?** Inspected: CHANGELOG.md [Unreleased] "SPEC §13 retrofit — Phase 1" bullet + sibling "SPEC §13 — Abstraction class + capability envelope" bullet. The general §13 entry states "Backwards-compatible: descriptors that omit both blocks pass." and "existing kinds remain conformant; new declarations are opt-in." Phase 1 bullet documents the exact delta + verification commands. No instance shape changes; additive under [kind]. Guidance present at feature level for the commit's scope. (Confirmed via `sed` + `grep` on CHANGELOG.md lines 1-120+.)
- **no historical dated spec retconned without link/correction note?** Confirmed via `git diff --name-only c63c57a..140bd9e`: SPEC.md not present. No edits to dated prose. The §13.4 vs §12.1 tension remains out-of-scope (plan §11, noted as ISS-005 candidate in prior revision history at planning doc:356). No retcon.
- **claimed tests actually run with command output and status?** Yes: all U05 commands, per-kind validators, git show/diff, grep for descriptions/closure/ids, ontology domain load, and taplo executed in this session. Exact stdout + exit 0 quoted above for each. sqry semantic searches used for validator internals (ID_PATTERN, _load_domains, DOMAIN_CHECKERS, entropy/crypto rules) per policy.evidence search_order.

## Cross-cutting checks (supporting U01–U04)

- ID pattern: `validators/validate_abstraction_class.py:52` (via sqry + read_file): `ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*\\.v\\d+$")`. "observation-record.v1" matches (lowercase slug with `-`, `.v1`). Validator enforced on all 19 + 5 with blocks.
- 9 domains: loaded from `core/ontology.toml` `attribute_vocabularies` "capability_envelope.domain" (via python one-liner + sqry on _load_domains): exactly `['clocks', 'crypto_keys', 'environment', 'filesystem', 'http', 'ipc', 'process_spawn', 'random', 'sockets']`. All four envelopes declare every one explicitly (read_file tails + sed extracts).
- random: all four use `entropy_source = "none"` (in-range per validator:182-191 `_check_domain_random`).
- crypto_keys: all four `denied = true` (per `_check_domain_crypto_keys`:214-223; only read_keys/use_keys/generate_allowed allowed if not denied).
- IJB tags on new blocks: `ijb_primitive = "constraint"`, `ijb_constraint_type = "structural"` on both `[kind.abstraction_class]` and `[kind.capability_envelope]` (and sub-tables omit, matching cost-record:282-327 reference). validate_ijb_conformance.py passed on all four.

## Terminal verdict

**unconditional_approval**

Rationale (tied exclusively to bytes + executed commands, no intent/plan-claim/should-fix language):

- U01–U08 all complete with direct file:line + stdout evidence (e.g., core/evidence-matrix-kind.toml:166-172 for id+description, 174-210 for envelope; 19/5 abstraction report; 74-file closure PASS; exact 5-file diff; 5 distinct descriptions at the 5 listed line numbers).
- All validators re-executed here exit 0 with required summary lines.
- sqry confirmed validator enforcement logic (ID_PATTERN, 9 domains from ontology, entropy/crypto checkers).
- Process checks satisfied via inspected CHANGELOG.md + git + command outputs.
- Zero concrete defects at any file:line. The four descriptors + CHANGELOG match the canonical Family A + per-kind-description shape from the cost-record reference (profiles/cost/cost-record-kind.toml:282-327) and satisfy every U01–U08 predicate in the review_prompt.

No blockers. Commit is ready.

(Verbatim review persisted to: docs/reviews/2026-05-25-spec-13-phase-1-observation-record/raw_findings/grok.md)
