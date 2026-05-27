# 1. SESSION META

- **Reviewer model name and version:** Grok 4.3 (xAI, released April 2026).
- **Sandbox / approval posture:** Linux sandbox at `/srv/repos/external/verivus-oss/agent-assurance`; full read/write/execute on workspace and `/tmp`; fresh clean-context session with zero prior memory of the artefact; treated every claim (including initiator commit message) as hypothesis requiring direct file + command verification per binding workflow rules from `tools/review-request-dag.toml`.
- **MCP servers available:** sqry (primary), exa, llm-cli-gateway / llm-gateway, ref_tools.
- **Commit / sha re-derived (do not trust prompt):** `fccc1dcf8ebc796eaeee395d73126256fd94d869`.

# 2. PROCESS CONFIRMATIONS

- **(a) Active-user best-effort migration / behaviour-change guidance:** `confirmed`. `profiles/cost/PROFILE.toml:1-61` contains 60+ lines of adopter-facing prose; `CHANGELOG.md:12-44` explicitly states "opt in via `framework_profile = "cost"`" and scope.
- **(b) No historical dated spec was retconned without a link / correction note:** `confirmed`. The 12 changed files are only new `profiles/cost/*`, new `examples/minimal-cost-record.toml`, new `validators/validate_cost.py`, plus reference DB updates. No SPEC.md, no pre-2026-05 dated research files, no core ontology/kind edits outside the additive cost surface.
- **(c) All claimed tests were actually run, with command output and status:** `confirmed`. Exact commands executed; key exits: `bash validators/check_manifest_drift.sh` → 0 (OK), `python3 validators/validate_cost.py --repo-root . examples/minimal-cost-record.toml` → 0 (PASSED), `python3 validators/validate_profile_descriptor.py --repo-root . profiles/cost/PROFILE.toml` → 0 (PASSED), `python3 validators/validate_kind_descriptor.py ... --check-references-exist` → 0 (PASSED, 7 invariants), `python3 validators/validate_ijb_conformance.py profiles/cost/ontology.toml` → 0 (PASSED), `python3 validators/validate_closure_root.py --discover .` → 1 (5 unrelated pre-existing FAILs on arxiv/tools files) but targeted `examples/minimal-cost-record.toml` → 0 (PASSED).

# 3. ANSWERS TO THE 10 SUBSTANTIVE QUESTIONS

**Q1. Closed-vocabulary completeness.** `confirmed`. `profiles/cost/ontology.toml:57-72` `cost_dimension_category` (7 values) tags at 71-72; `74-90` `decider_class` (8 values) tags at 89-90; `92-107` `cost_citing_kind` (7 values) tags at 106-107. All three `extensible = false`.

**Q2. Validator enforces every declared invariant.** `confirmed` (7/7). Seven negative TOMLs constructed; all rejected with the expected error messages. See verbatim outputs in raw findings.

**Q3. Float quantities rejected.** `confirmed`. `quantity = 1.5` → exit 1; `FAIL ... must be a non-negative integer (no floats per canonical-form determinism); got float 1.5`.

**Q4. MD5/SHA-1 hash_algorithm rejected.** `confirmed`. `hash_algorithm = "md5"` → exit 1; `FAIL ... 'md5' is forbidden by SPEC §12.1 (no MD5 or SHA-1); use SHA-256 or stronger.`.

**Q5. Closure-root requirement is enforced on the cost example.** `confirmed`. `--discover .` discovers the example and validates it; targeted run exits 0, PASSED (1 file).

**Q6. Manifest counts match ontology reality.** `refuted_with_evidence` (partial). `check_manifest_drift.sh` exits 0 (OK) but it only checks block counts. Independent parse: core 22 + agent-assurance 51 + disclosure 4 + cost 22 = 99 closed values, not 106 as MANIFEST claims at line 37. The drift script ignores `attribute_values`; the commit's "+22 from cost vocabularies" math was correct but applied to a wrong base.

**Q7. Profile-descriptor correctness.** `confirmed`. Validation PASSED; `contained_kinds = ["cost-record"]`, `extends = []`, `namespace = "spec.reserved"`, correct IJB tags on `[profile]`.

**Q8. No-billing-dialect constraints honoured.** `confirmed`. `cost-record-kind.toml:96-102` lists out-of-scope items; required fields contain zero `rate`/`currency`/`total`/`formula`; validator only checks non-empty producer string for `unit_label`, no normalisation.

**Q9. No transitive aggregation surface.** `confirmed`. `cost-record-kind.toml:107-110` explicit: "The cost-record is NOT transitive..."; grep for `cited_costs|aggregates|sum_of|cost_root|cost_total` returns zero matches in the kind file.

**Q10. Decider-class gaming surface.** `unverifiable` (structural) / `confirmed` (acknowledgement). No structural protection exists; `profiles/cost/ontology.toml:88` acknowledges silent mislabelling as a separation-of-duty violation.

# 4. INDEPENDENT FINDINGS

**IF-001 (medium):** `reference/database/MANIFEST.toml:37` `attribute_values = 106` does not match independent closed-vocabulary value sum (99). `check_manifest_drift.sh` never inspects this field, so the incorrect claim was not caught by CI. Non-normative but part of the commit's "reference-DB seeds + CI wiring" claim.

**IF-002 (low):** `python3 validators/validate_closure_root.py --discover .` emits 5 FAILs (arxiv-prep-agent-dag.toml + 4 tools/*.toml). Pre-existing, unrelated to Stream G.

**IF-003 (low):** `sqry` index required explicit `sqry__rebuild_index --force` before symbol queries on the new validator returned matches. Environment observation only.

# 5. TERMINAL VERDICT

**CONCRETE UNRESOLVABLE BLOCKERS:**

1. MANIFEST.toml [counts] attribute_values claims 106 (and the cost commit message asserts "+22 from cost vocabularies") but the four ontology files contain only 99 closed (extensible=false) attribute values in total (core 22 + agent-assurance 51 + disclosure 4 + cost 22). This is a factual error in a file the commit explicitly updated as part of "reference-DB seeds + CI wiring". File: `reference/database/MANIFEST.toml:37`; evidence: direct `tomllib` parse + `check_manifest_drift.sh` (green only because it ignores the field) + commit --stat. Unblocks only by correcting the number + comment to 99 and re-verifying any downstream seed generation.

(The core blessed profile artefacts — 3 closed vocabs with correct IJB tags, 7 invariants all enforced by negative tests + 4 required validators, minimal example, PROFILE, CI wiring, and seeds — are otherwise clean and interlock correctly.)
