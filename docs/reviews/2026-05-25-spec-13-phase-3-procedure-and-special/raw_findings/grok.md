# SPEC §13 Phase 3 retrofit — grok independent review (2026-05-25)

Fresh-context reviewer (grok). Scope: commit `3749398` (HEAD) vs parent `8a5e715`. PHASE-TERMINAL (14/19 → 19/19).

**Initiator**: claude-opus-4-7 (explicitly excluded; this review is a clean-context independent pass).

All claims verified against repo bytes via direct file reads, `git show <sha>:<path>`, executed validator commands with quoted stdout, and `grep` on exact commit content. sqry MCP available but literal + executed tests used for precision on TOML descriptors and validator logic (policy.evidence search_order prioritises semantic but exact confirmation requires literal here).

## Summary

`unconditional_approval`

All nine units (U01–U09) complete. All executed verify commands from review_bundle.toml [[bundle.units]] produced the exact required outputs. U04 (adapter-contract) received highest scrutiny for R1/R2: byte inspection of pre-retrofit prose (adapter-contract-kind.toml:27-31, 75-77, 161-162 INV04, required_fields:108-123), required sections, and worked example (examples/minimal-adapter-contract.toml:42-49) found zero evidence that the spec author intended R2 (envelope bounding deployed adapter runtime permissions). All evidence places runtime policy declarations at instance `[adapter].runtime_*` level and carves execution/hermeticity/digest work as RUNTIME-SPEC. R1 stands; no blocker. U05 Family A correct per plan §5 + validator vocab bytes. U06 19/19 green with exact validator outputs reproduced. U07 zero forbidden-phrase matches. U08 sentinels at line 5. U09 exactly 6 files. Process checks satisfied via inspected CHANGELOG bytes and reproduced test outputs. No concrete_unresolvable_blocker.

## U01 — rollback-plan

complete

- Inspected: `git show 3749398 -- profiles/agent-assurance/rollback-plan-kind.toml` (exact diff added 68 lines of §13 blocks after pre-existing INV03 at line 153).
- `python3 validators/validate_abstraction_class.py --repo-root . profiles/agent-assurance/rollback-plan-kind.toml` → `ABSTRACTION-CLASS VALIDATION PASSED (1 file(s) checked; 1 declared a §13 block).`
- `grep -n closure_root ...` → line 5 sentinel (confirmed in U08 aggregate).
- File bytes at `profiles/agent-assurance/rollback-plan-kind.toml:173-175`:
  ```
  [kind.abstraction_class]
  id          = "procedure-declaration.v1"
  description = "Procedure-declaration artefact: declares a `[plan]` (summary + owner + ISO-8601 `estimated_ttr`), at least one `[[triggers]]` row (each carrying `id`, closed-vocabulary `trigger_kind`, `metric`, `threshold`, `window`, `action`), and an ordered `[procedure].steps` list a runtime executes to undo the change. Bounds the descriptor parse only; runtime trigger evaluation (metric scraping, threshold comparison, paging) and procedure-step execution (flag flips, redeploys) are RUNTIME-SPEC and lie outside this envelope. No I/O outside the canonical-form text serialisation; no networking; no process spawn."
  ```
- IJB tags present on both `[kind.abstraction_class]` (174-177) and `[kind.capability_envelope]` (179-182): `ijb_primitive = "constraint"`, `ijb_constraint_type = "structural"`.
- Family A envelope (184-218): all 9 domains + bounds explicit, `random.entropy_source = "none"`, `crypto_keys.denied = true`, cpu 100ms/5%, mem 1MB, all others denied/zeroed. Matches cost-record reference shape at `profiles/cost/cost-record-kind.toml:282-327`.
- Pre-retrofit required_sections/hard_invariants (lines 106-153) declare `[[triggers]]`, `[procedure]`, INV01–INV03; description cites exactly those fields + R1 carve-out. Consistent.
- Class id `procedure-declaration.v1` matches `validators/validate_abstraction_class.py:52` regex `^[a-z0-9][a-z0-9._-]*\.v\d+$`; unique in this phase (bundle U01).

## U02 — smoke-validation

complete

- `git show 3749398 -- profiles/agent-assurance/smoke-validation-kind.toml` (diff added 66 lines after pre-existing INV04 at ~147).
- `python3 validators/validate_abstraction_class.py .../smoke-validation-kind.toml` → `ABSTRACTION-CLASS VALIDATION PASSED (1 file(s) checked; 1 declared a §13 block).`
- Description at `profiles/agent-assurance/smoke-validation-kind.toml:169-170` names `[result]` (decision from `smoke.decision` vocab, duration_s, artefact), `[[checks]]` (id SMOKE:, title, status from status vocab applies_to SMOKE, evidence), plus INV03 cross-field derivation rule. Matches pre-retrofit `[[kind.required_fields]]` (95-100 result.decision), `[[kind.required_sections]]` (101-104 checks), `[[kind.hard_invariants]]` INV03 (123-126).
- IJB tags + Family A envelope identical shape to U01 (lines 168-213), all 9 domains explicit/denied/zeroed.
- Pre-existing prose (not reproduced here, inspected via read) + INV04 carve execution of smoke run to RUNTIME-SPEC. Envelope correctly bounds only the recorded descriptor parse.
- Class id `validation-record.v1` valid per regex; unique this phase.

## U03 — assertion-bundle

complete

- `git show 3749398 -- profiles/agent-assurance/assertion-bundle-kind.toml` (65-line addition after INV04 at 145).
- Validate: `ABSTRACTION-CLASS VALIDATION PASSED (1 file(s) checked; 1 declared a §13 block).`
- Description at `profiles/agent-assurance/assertion-bundle-kind.toml:184-186` names sealed `[[bundle.assertions]]` (line per ABNF foundations/ijb/CANONICAL-ASSERTION-GRAMMAR.md:46-83), provenance (adapter_contract_ref, adapter_version_pin, raw_input_hash/bundle_hash 64-hex, created_at RFC3339), cites INV04 for hash/digest verification as RUNTIME-SPEC.
- Inspected INV04 bytes (145-148): "SPEC-layer validation MUST NOT verify `bundle.bundle_hash` against bundle contents; MUST NOT verify the bundle was produced by the cited adapter; MUST NOT dereference `bundle.adapter_contract_ref`. Those checks are RUNTIME-SPEC."
- IJB + Family A envelope (190-229) complete/denied/zeroed.
- Pre-retrofit required_fields (105-107 bundle.bundle_hash etc.) and INV01/INV03 (124-143) align with description. Consistent.
- Class id `assertion-set.v1` valid + unique.

## U04 — adapter-contract (R1/R2 highest scrutiny)

complete — no blocker filed

- Bundle verifies executed:
  - `git show 3749398 -- .../adapter-contract-kind.toml` (92-line addition after relation_to_ontology at 183; includes full R1/R2 header comment).
  - `sed -n '185,220p' .../adapter-contract-kind.toml` (reproduced the R1-adopted / R2-rejected reasoning citing instance `[adapter].runtime_*` fields and unboundedness).
  - `python3 validators/validate_abstraction_class.py .../adapter-contract-kind.toml` → `ABSTRACTION-CLASS VALIDATION PASSED (1 file(s) checked; 1 declared a §13 block).`
  - `grep -n closure_root ...` → line 5 sentinel.
  - `cat examples/minimal-adapter-contract.toml` (full 69 lines inspected; runtime policies declared at instance level: lines 46-49 `runtime_network_policy = "denied"`, `runtime_clock_policy = "injected"`, `runtime_env_allowlist = []` under `[adapter]`).
- **R1/R2 byte-level inspection (per review_prompt §U04 and plan §5:156-161, §7:221, §8:258-266)**: Read full pre-retrofit prose (adapter-contract-kind.toml:20-78), required_fields (87-135), hard_invariants (137-165), relation_to_ontology (173-185), and the worked example.
  - Existing prose (27-31): "The contract carries the adapter's identity, declared invariants, runtime policy declarations, and conformance fixture references. It does NOT carry the adapter binary itself, nor does it specify how the adapter is executed. Execution, hermeticity enforcement, and digest verification are RUNTIME-SPEC concerns and are explicitly out of scope for SPEC-layer validation."
  - Existing prose (75-77): "VALIDATOR MUST NOT execute the adapter, verify hermeticity, run fixtures, verify any digest against an artifact, or resolve fixture references to files. Those are RUNTIME-SPEC concerns."
  - INV04 (161-162): "SPEC-layer validation MUST NOT execute the adapter, verify hermeticity, dereference fixtures, or verify any digest against an artifact. Those checks are RUNTIME-SPEC."
  - Required fields (108-123) mandate presence of `adapter.runtime_kind`, `runtime_network_policy`, `runtime_clock_policy` (and env_allowlist via shape) in *instances*; they are the surface for runtime policy values. No language claims the kind descriptor envelope should bound or enumerate deployed-adapter permissions.
  - Example (42-49) places concrete policy values (`denied`, `injected`) inside the instance `[adapter]` table, not in any envelope.
- No byte-level evidence in *existing* (pre-3749398) prose, required-fields, hard_invariants, or worked example that spec author intended R2 (envelope bounding what a deployed adapter is permitted at runtime). All evidence supports R1 (descriptor parse only) + RUNTIME-SPEC carve-out for execution. The retrofit's own §13 header (added bytes) makes the R1 choice explicit and cites the same instance-level fields as the reason R2 is rejected, but per instructions the challenge bar is evidence in *existing* content — none found.
- Therefore: R1 stands per plan §5 and the inspected bytes. No `concrete_unresolvable_blocker`.
- Class id `interface-contract.v1` valid + unique. IJB tags + Family A envelope (all 9 domains explicit) present (lines 189-236 in post-commit file).

## U05 — selective-disclosure-proof

complete

- `git show 3749398 -- .../selective-disclosure-proof-kind.toml` (76-line addition after relation_to_ontology).
- `sed -n '140,170p' .../selective-disclosure-proof-kind.toml` (header + abstraction block citing plan §5 Family-B/C exceptions + codex r1 validator defects).
- `python3 validators/validate_abstraction_class.py .../selective-disclosure-proof-kind.toml` → `ABSTRACTION-CLASS VALIDATION PASSED (1 file(s) checked; 1 declared a §13 block).`
- `grep -n closure_root` → line 5 sentinel.
- `sed -n '180,225p' validators/validate_abstraction_class.py` (reproduced exact vocab: entropy_source only `os | deterministic_seed | none` at ~182; crypto_keys only `read_keys | use_keys | generate_allowed` at ~214; no `sign/verify` or `system`).
- Pre-existing prose (61-62, inspected): "The SPEC layer enforces shape only. Verifying the proof against the published bytes is RUNTIME-SPEC."
- Description at 167-169 names `[[proofs]]` (SDP: id, subject, bound_source sha256:<64hex> per INV01, proof_scheme per INV02, covers RED: list per INV03 or proof_artifact), cites RUNTIME-SPEC delegation at lines 61-62.
- Family A envelope (173-212): all 9 domains + bounds explicit, `random.entropy_source = "none"`, `crypto_keys.denied = true`. Matches cost-record shape. (A proposed Family C would have failed the validator vocab checks cited in the header.)
- Class id `cryptographic-proof.v1` valid + unique this phase. IJB tags present.
- Per plan §5:141-154 (read in full): Family A is the correct choice; no byte-level justification for wider envelope exists in the kind's own prose.

## U06 — validators green at 19/19

All commands from review_bundle.toml [[bundle.units.U06]] and review_prompt executed with absolute paths; exact outputs:

1. `python3 validators/validate_abstraction_class.py --repo-root /srv/... core/*-kind.toml profiles/agent-assurance/*-kind.toml profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml`
   - Output: `ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 19 declared a §13 block).`
   - (Was 14 after Phase 2; PHASE-TERMINAL confirmed by execution.)

2. `for f in ...; do python3 validators/validate_ijb_conformance.py "$f"; done | grep -c 'IJB CONFORMANCE VALIDATION PASSED'`
   - Output: `19`

3. `for f in ...; do python3 validators/validate_kind_descriptor.py "$f" --repo-root ... --check-references-exist; done | grep -c 'KIND DESCRIPTOR VALIDATION PASSED'`
   - Output: `19`

4. `python3 validators/validate_closure_root.py --discover /srv/...`
   - Output: `CLOSURE-ROOT VALIDATION PASSED (74 file(s)).`

5. `/home/werner/.local/bin/taplo lint /srv/.../core/*-kind.toml /srv/.../profiles/*/*-kind.toml`
   - Exit 0; INFO lines only (19 files collected, no FAIL or error output).

All four plan-§9 gates green at 19/19 on the exact commit bytes.

## U07 — no forbidden-phrase leak

Re-ran exact pre-flight grep from bundle U07 and review_prompt against HEAD:

```
for f in /srv/.../profiles/agent-assurance/rollback-plan-kind.toml .../smoke-validation-kind.toml .../assertion-bundle-kind.toml .../adapter-contract-kind.toml /srv/.../profiles/disclosure/selective-disclosure-proof-kind.toml; do
  echo "--- $f ---"
  grep -niE 'forbidden|MUST NOT appear|only in this note|do not (appear|use)|MUST NOT use' "$f" || echo "(no matches)"
done
```

Exact output:
```
--- /srv/repos/external/verivus-oss/agent-assurance/profiles/agent-assurance/rollback-plan-kind.toml ---
(no matches)
--- /srv/repos/external/verivus-oss/agent-assurance/profiles/agent-assurance/smoke-validation-kind.toml ---
(no matches)
--- /srv/repos/external/verivus-oss/agent-assurance/profiles/agent-assurance/assertion-bundle-kind.toml ---
(no matches)
--- /srv/repos/external/verivus-oss/agent-assurance/profiles/agent-assurance/adapter-contract-kind.toml ---
(no matches)
--- /srv/repos/external/verivus-oss/agent-assurance/profiles/disclosure/selective-disclosure-proof-kind.toml ---
(no matches)
```

Zero matches. Phase 2 r1 "risk posture" leak (fixed in 6b63860) did not recur. No pre-existing forbidden-phrase invariants violated by the new §13 headers.

## U08 — closure_root sentinel preserved

```
grep -n 'closure_root' [5 Phase 3 files]
```

Exact:
```
/srv/.../rollback-plan-kind.toml:5:closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
/srv/.../smoke-validation-kind.toml:5:closure_root = "sha256:e3b0c442..."
/srv/.../assertion-bundle-kind.toml:5:closure_root = "sha256:e3b0c442..."
/srv/.../adapter-contract-kind.toml:5:closure_root = "sha256:e3b0c442..."
/srv/.../selective-disclosure-proof-kind.toml:5:closure_root = "sha256:e3b0c442..."
```

Every match is the empty-closure sentinel (SPEC §12.1). All five at line 5 (pre-existing header length made this uniform). `python3 validators/validate_closure_root.py --discover .` (U06) → `CLOSURE-ROOT VALIDATION PASSED (74 file(s)).` Sentinel VALUE preserved per §12.11; file SHA-256 flip is the intended cascade-break signal for downstream instances.

## U09 — scope discipline

```
git show --stat 3749398
git diff --name-only 8a5e715..3749398
```

Exact (from execution):
- 6 files changed, 399 insertions(+)
- Files:
  - CHANGELOG.md
  - profiles/agent-assurance/adapter-contract-kind.toml
  - profiles/agent-assurance/assertion-bundle-kind.toml
  - profiles/agent-assurance/rollback-plan-kind.toml
  - profiles/agent-assurance/smoke-validation-kind.toml
  - profiles/disclosure/selective-disclosure-proof-kind.toml

MUST NOT list (and does not): SPEC.md, the plan doc, any Phase 1/2 kind descriptors, any validator/*.py, any ontology.toml. Scope exactly as declared in review_bundle.toml and plan §9.

## Process checks

Per `[policy.process_checks]` in `tools/review-request-dag.toml` and review_prompt:

- active-user migration/behavior-change guidance present?  
  Inspected: CHANGELOG.md addition (this commit) + each of 5 §13 header comments (e.g. adapter-contract-kind.toml:198-210, rollback-plan-kind.toml:159-171) explicitly document R1 semantics and that runtime trigger/procedure/adapter-execution/crypto work remains RUNTIME-SPEC. No instance shape change; additive only. Guidance present in persisted bytes. (No active-user runtime change; descriptors only.)

- no historical dated spec retconned without link/correction note?  
  `git diff --name-only 8a5e715..3749398` (U09) confirms SPEC.md untouched. The follow-up marker text at SPEC.md:1478-1486 remains verbatim (read confirmed). Closure recorded in CHANGELOG under [Unreleased] + review lineage (bundle, terminal_decision). No retcon of dated prose.

- claimed tests actually run with command output and status?  
  Yes: every command listed in [[bundle.units]] U06/U07/U08 + per-unit verify arrays was executed in this session with full stdout captured and quoted above (U06 19/19 exact strings, U07 no-matches, U08 sentinels + 74 PASS, per-kind validate_abstraction_class PASS). Taplo exit 0. All reproduced on commit bytes.

## Terminal verdict

unconditional_approval

Rationale tied exclusively to inspected bytes and executed command outputs (no stated_intent, no plan_compliance_claim as sole basis, no should_be_fixed_language):

- 19/19 validator green reproduced exactly (U06).
- Zero forbidden-phrase matches on HEAD (U07).
- All 5 sentinels + 74-file closure validator (U08).
- Exact 6-file scope (U09).
- U01–U03, U05: description cites own required_fields/sections/invariants; IJB tags present; Family A envelopes match cost-record reference at every byte (9 domains, entropy=none, crypto denied, 100ms/1MB).
- U04: highest-scrutiny read of pre-retrofit adapter-contract-kind.toml:20-78 (RUNTIME-SPEC carve-outs at 27-31/75-77), 108-123 (runtime_* required at instance level), 161-162 (INV04), examples/minimal-adapter-contract.toml:42-49 (policies declared in [adapter] table) yields no byte evidence for R2 intent. R1 stands; no blocker.
- U05: pre-retrofit prose:61-62 + validator:182/214 bytes confirm Family A is the only valid choice; cryptographic work RUNTIME-SPEC.
- Process checks satisfied via CHANGELOG + SPEC.md bytes + reproduced test outputs.

All required approval bases met (inspected_code with file:line, executed_tests_with_output, inspected_docs, persisted_review_evidence). No concrete_unresolvable_blocker exists. This commit is cleared for terminal gate.

---

**Persisted**: this verbatim text written to `docs/reviews/2026-05-25-spec-13-phase-3-procedure-and-special/raw_findings/grok.md` before any summary output.
**SHA inspected**: 3749398f5b6f126466832536225ba700c8ae3dc0 vs 8a5e7157001a5f4a173030275514227a8cdddca0
**Date of review execution**: 2026-05-25 (clean context)
