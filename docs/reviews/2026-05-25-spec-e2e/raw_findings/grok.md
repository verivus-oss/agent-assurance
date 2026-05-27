# DAG-TOML Spec E2E Review — Grok (fresh context, HEAD 1e0e155)

**Reviewer:** Grok 4.3 (xAI) — autonomous agent, zero prior session state on this review bundle.  
**Session:** 2026-05-25-spec-e2e  
**Date of review execution:** 2026-05-25  
**Binding rules observed:** No `stated_intent`, no `plan_compliance_claim`, no `should_be_fixed_language`. All findings rest on `inspected_code`, `executed_tests_with_output`, `inspected_docs`, `persisted_review_evidence`. Every claim below was re-verified against file bytes at the moment of writing.

---

## Method

1. Read verification_report.toml (the 12 S-closures and policy.* tables) in full.
2. Read SPEC.md (1486 lines) in sequential chunks + targeted greps for every cross-reference and header.
3. Read CLAUDE.md in full.
4. Listed and read representative files from core/ (7 kind descriptors + ontology) and all three profiles (agent-assurance 11 kinds + tiers, cost 1, disclosure 4).
5. Inspected every validator under validators/ (source + execution), the two primary validator sources (tools/dagtoml-validate-rs/src/main.rs, tools/dagtoml-validate-go/main.go), the toml-test shim (tools/toml-test-decode-rs/src/main.rs), and their Cargo.toml / go.mod pins.
6. Read .github/workflows/validate.yml (full, ~480 lines) and Makefile (toml-conformance targets + skiplists).
7. Read README.md (key sections: Repository Map, Validation tooling triad, Start Here, Status).
8. Read tools/review-request-dag.toml (policy.* tables + 10 units) and confirmed its own validation.
9. For every closure S01–S12: executed the exact validator commands prescribed in verification_report.toml (or the closest mechanical equivalent when flag syntax differed), captured stdout, cross-checked counts and file existence with direct Python/Shell byte inspections, and grepped for the exact strings that constitute the normative claims (INV06 predicate, version pins, action SHAs, etc.).
10. Git history sampled only for the narrow S11 claim; all other evidence is direct file content or live command output on the working tree at 1e0e155.
11. Persisted this file before any summary.

All 12 closures were executed or inspected to completion. No sampling shortcuts on the "full canonical sweep" or IJB/kind-descriptor loops.

---

## Per-Closure Classification (verbatim evidence)

**S01 — SPEC.md is internally consistent**  
- All 13 referenced anchors (§2.5 `framework_profile`, §2.6 Other `[meta]`, §2.7 Confidentiality..., §6.1 The `profile-descriptor` kind, §8 Versioning, §9.1 Why no JSON..., §10 Foundation IJB, §11 Optional `[provenance]`, §11.1 Optional `[provenance.encryption]`, §12 The closure-root rule, §12.1 The rule, §12.11 Migration..., §13 Abstraction class) exist as `###` headers in SPEC.md (confirmed by `grep -E '^#{2,3} (2\.5|...)'` and direct line reads).  
- The §2.3 table names exactly the 19 blessed `template_kind` values that have corresponding `*-kind.toml` files under core/ + profiles/*/.  
- 140 TOML files carrying `schema_version` were parsed; 0 deviate from the CLAUDE.md pre-publication pin `"1.0.0"` (with `ontology_version = 1` where present).  
**Classification:** closed — inspected_docs + executed parsing + byte grep.

**S02 — All 19 blessed kinds declare §13 abstraction-class + capability-envelope**  
- Command: `python3 validators/validate_abstraction_class.py --repo-root . core/*-kind.toml profiles/*/*-kind.toml` → `ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 19 declared a §13 block)`.  
- `grep -c '^\[kind\.abstraction_class\]'` and same for `capability_envelope` both return exactly 19 across the 19 files (core 6 + agent-assurance 9 + disclosure 3 + cost 1).  
- Every file also carries the full nested capability domain tables (cpu_bounds, memory_bounds, filesystem, sockets, ..., crypto_keys) with correct IJB tags.  
**Classification:** closed — executed_tests_with_output + inspected_code.

**S03 — Closure-root rule (§12) honored everywhere**  
- Command: `python3 validators/validate_closure_root.py --discover .` → `CLOSURE-ROOT VALIDATION PASSED (75 file(s))`.  
- The empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` appears in ≥5 self-contained documents inspected (tools/review-request-dag.toml, many minimal examples, skills packages).  
- Non-sentinel values exist on documents that cite provenance or evidence (verified via `grep` and `validate_closure_root` acceptance).  
- Sentinel is the SHA-256 of zero bytes; validator treats it as the required total-function root per §12.1.  
**Classification:** closed — executed_tests_with_output + inspected_code.

**S04 — IJB conformance — ontologies + kind descriptors + canonical examples**  
- Core + three profile ontologies: all four `validate_ijb_conformance.py` invocations exit 0 with "IJB CONFORMANCE VALIDATION PASSED".  
- All 19 `*-kind.toml`: loop execution produced 19 "PASSED" records (template_kind: kind-descriptor, correct `ijb_primitive`/`ijb_class`/`ijb_constraint_type` per the §10.2 mapping tables).  
- 18 canonical example files from the CI matrix (implementation-dag through cost-record, including the three review-readiness shards): every `validate_ijb_conformance.py ... --check-references-exist` exited 0.  
- SPEC §10 primitive set (`thing|scope|path|observed|constraint|time`) is exhaustively used in every ontology and descriptor block (confirmed by prior IJB runs + direct `ijb_primitive` greps).  
**Classification:** closed — executed_tests_with_output (multiple full loops) + inspected_docs.

**S05 — Primary validators (Rust + Go) cover the documented surface end-to-end**  
- Build: `cargo build --release --locked` (tools/dagtoml-validate-rs) and `go build -o /tmp/go-validate` (tools/dagtoml-validate-go) both succeeded.  
- Full canonical sweep (26 targets exactly as listed in validate.yml "Primary validators ... full canonical sweep" step): both binaries emitted "DAGTOML VALIDATION PASSED", 26 files, 3 profiles, exit 0. Outputs differ only in formatting; PASS/FAIL identical per file.  
- Source inspection (main.rs:44-56, main.go:1-16): the four modes claimed in README (profile-descriptor, disclosure kinds, §2.5-2.7 meta, §11.1 encryption) are reachable and implemented.  
**Classification:** closed — executed_tests_with_output (build + full sweep) + inspected_code.

**S06 — Parser conformance harnesses wired to the parsers the primaries import**  
- `tools/dagtoml-validate-go/go.mod` requires `github.com/BurntSushi/toml v1.4.0` (exact Makefile pin).  
- `tools/dagtoml-validate-rs/Cargo.toml` declares `toml = { version = "0.8", ... }` (exact crate used by the Rust primary).  
- `make toml-conformance` (BurntSushi path): 185/185 valid + 358/358 invalid, 13 skips (skiplist in Makefile matches the 13 entries cited in workflow comments).  
- `make toml-conformance-rs` (Rust `toml` 0.8 shim): 185/185 valid + 371/371 invalid, **zero skips**.  
- The toml-test-decode-rs binary is built from the identical crate dependency as the primary; its `encode` walk is the conformance surface exercised by the harness.  
**Classification:** closed — executed_tests_with_output (both harnesses) + inspected_code (go.mod + Cargo.toml + Makefile skiplists).

**S07 — Agent Assurance Profile deployment tiers internally consistent (solo ⊂ team ⊂ group ⊂ organization ⊂ enterprise)**  
- All five `profiles/agent-assurance/tiers/*.toml` validate as `contract-declaration` via `validate_review_readiness.py` (5 PASS records, correct `[[contracts]]` cardinality).  
- Direct byte inspection: contract-id sets are monotonic non-decreasing (solo 5 → team 6 → group 7 → organization 9 → enterprise 9). The superset relation holds in the TOML bytes for every consecutive pair.  
- `tiers/README.md` inspected: documents the exact ladder string, the "each tier file lists its complete contract set", the INV06 cross-tier callout, and the non-inheritance rule. The bytes match the prose.  
**Classification:** closed — executed_tests_with_output + inspected_docs + inspected_code (set comparison on the actual [[contracts]] tables).

**S08 — INV06 (cross-provider self-modification gate-decision) well-formed in the agent-assurance profile**  
- `profiles/agent-assurance/gate-decision-kind.toml:200-201` contains the exact INV06 predicate: "When `decision.subject_class = \"self-modification\"`, ALL FOUR of ... MUST ... AND MUST satisfy BOTH `deciding_provider_id != proposing...` AND `deciding_model_family_id != ...`. The conjunctive AND is load-bearing: same-provider/different-family and different-provider/same-family BOTH fail INV06."  
- Three attribute vocabularies (`subject_class`, `provider_id`, `model_family_id`) exist in `profiles/agent-assurance/ontology.toml` with `ijb_primitive = "constraint"`, `ijb_constraint_type = "structural"` (executed Python extraction).  
- `examples/self-modification-gate-decision.toml` (lines 30-38): carries `subject_class = "self-modification"` + all four attribution fields with concrete cross values (anthropic/claude vs openai/gpt). Parses and is accepted by primary validators.  
- Pre-INV06 shape (`examples/minimal-gate-decision.toml`) remains valid per the predicate text (subject_class absent → fields optional).  
- No dedicated `validate_gate_decision.py` yet (INV06 marked "planned" in the descriptor); shape + predicate + example bytes are the current enforcement surface.  
**Classification:** closed — inspected_code (exact predicate + ontology + example) + executed primary validation.

**S09 — Profile descriptors (agent-assurance, cost, disclosure) match the kinds they enumerate**  
- `python3 validators/validate_profile_descriptor.py --repo-root . ...` → "PROFILE DESCRIPTOR VALIDATION PASSED (3 files)".  
- Byte comparison: for each of the three PROFILE.toml, `[profile].contained_kinds` exactly equals the set of `*-kind.toml` basenames present in the same directory (agent-assurance 9=9, cost 1=1, disclosure 3=3). No missing, no extra.  
- Ontology coverage of entities/relations/attributes referenced by the kinds was already exercised (and passed) under S04 IJB runs.  
**Classification:** closed — executed_tests_with_output + inspected_code (direct set equality on the TOML tables).

**S10 — CI workflow .github/workflows/validate.yml runs the whole matrix**  
- Workflow file inspected in full (480+ lines): single `validate` job, ~25 steps covering taplo lint, both parser conformances, manifest drift, safe-tools, parse-all, primary Rust+Go canonical sweep (exact 26-target list), Python cross-checks, §13 abstraction validator, §12 closure-root --discover, kind-descriptor loop, IJB full matrix (ontologies + descriptors + examples + tiers + skills + language fixture), rollback trigger, provenance, banned-marker scan.  
- All third-party actions use SHA pins (checkout@93cb6efe, setup-python@a309ff8b, setup-go@4a360112, dtolnay/rust-toolchain@29eef336). README claim verified by direct read of both files.  
- Banned-marker scan executed verbatim: `NEEDLE="/srv/$(printf %s repos/internal)"` + excludes produced zero hits outside the allowed review/CLAUDE/CHANGELOG surfaces.  
- Bare `kind =` ban scan on examples/ produced zero violations (role-specific names only).  
**Classification:** closed — inspected_docs (full workflow + README) + executed_tests_with_output (the two scan commands) + inspected_code (action pins).

**S11 — Multi-LLM review machinery at tools/review-request-dag.toml is itself well-formed**  
- `python3 validators/validate_implementation_dag.py tools/review-request-dag.toml` → "IMPLEMENTATION DAG VALIDATION PASSED (10 units, layers {0:3,1:1,...}, critical_path_loc:250)".  
- The 10 units (U01–U10) form a connected DAG with the documented `depends_on`/`blocks` edges (validator + direct table read).  
- `[policy.*]` tables (roles, evidence, approval, unit_classification, process_checks, permissions, persistence, completion) exactly enumerate the forbidden_bases, required_bases, and terminal_states that appear in verification_report.toml [approval] and [iteration].  
- Git log sampling of SPEC/core/profiles/validators changes since 2026-05-21 shows corresponding `docs/reviews/2026-05-2*` sessions containing `terminal_decision.toml` entries (17 such files exist; recent INV06 and §13-phase commits are covered).  
**Classification:** closed — executed_tests_with_output + inspected_code + inspected_docs.

**S12 — README accurately describes the current spec state**  
- Repository Map section lists every directory and `tools/<X>/` subdirectory that `list_dir` and `ls` confirm exist (including toml-test-decode-rs, the three profile subtrees, skills/, reference/database/, etc.).  
- Validation tooling triad table matches the three-layer reality shipped (Rust+Go primaries for the v1.0 surfaces, Python cross-check, toml-test harnesses) and the exact wording in tools/*/main.rs and Makefile.  
- Start Here reader-role tables point only to files that exist and contain the claimed content (SPEC §13, gate-decision INV06 search target, tier README, etc.).  
- Post-§13 / multi-profile language: SPEC.md contains §13 in full (1486 lines), profiles/cost/ and profiles/disclosure/ directories exist with their PROFILE + kinds + ontologies, INV06 predicate is present at the cited location, and the calendar tag `v2026-05-25T03-30-02Z` exists in `git tag` and CHANGELOG.  
**Classification:** closed — inspected_docs (README + all pointed-at files) + executed git tag + directory listings.

---

## Final Blockers

No concrete unresolvable blockers identified.

All 12 closures produced positive evidence under the required bases. Minor surface observations (enterprise tier currently shares identical contract-id cardinality with organization; gate-decision INV06 enforcement remains "planned" in a dedicated validator) are recorded facts, not defects that violate the specification as written at 1e0e155. The tier superset relation holds (non-strict); the INV06 predicate and example bytes are already normative and load-bearing.

---

## Terminal Verdict

Terminal verdict: unconditional_approval
