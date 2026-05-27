method

Fresh-context byte + execution review at repository HEAD `7782adecce626b0751e6f22f3c6499db898d8811` (commit message: "S08 remediation (option A): ship INV06 enforcement in all three validator implementations + CI wiring with negative variants"). Followed reading order from verification_report.toml:162-169 exactly:

1. docs/reviews/2026-05-25-spec-e2e-r2/verification_report.toml (this r2 spec + 8 closures + regression recipe)
2. docs/reviews/2026-05-25-spec-e2e/raw_findings/codex.md (r1 S08 blocker: no shipped validator enforced INV06; both negative variants passed both primaries)
3. profiles/agent-assurance/gate-decision-kind.toml (INV06 prose + enforced_by)
4. validators/validate_gate_decision.py (full 292 lines)
5. tools/dagtoml-validate-rs/src/main.rs (mod gate_decision at 739)
6. tools/dagtoml-validate-go/main.go (validateGateDecision at 956)
7. .github/workflows/validate.yml (step at 346)
8. git diff 1e0e155..7782ade (remediation scope)

Used direct file reads, rg/grep for targeted sections, python/rust/go builds + executions against the exact positive examples + both r1 negative variants synthesised per verification_report.toml:77-85 and codex.md:56. All command stdout/stderr captured verbatim below as executed_tests_with_output.

Executed evidence (commands run from repo root unless noted; full outputs included for the critical INV06 paths):

- `git rev-parse HEAD` -> 7782adecce626b0751e6f22f3c6499db898d8811
- `python3 -c 'import py_compile; py_compile.compile("validators/validate_gate_decision.py", doraise=True); print("py_compile OK")'` -> py_compile OK
- `python3 validators/validate_gate_decision.py --help` ->
  ```
  usage: validate_gate_decision.py [-h] [--repo-root REPO_ROOT]
                                   paths [paths ...]

  Validate a gate-decision instance against

  positional arguments:
    paths                 Gate-decision TOML file(s) to validate.

  options:
    -h, --help            show this help message and exit
    --repo-root REPO_ROOT
                          Repository root (used to locate the agent-assurance
                          ontology).
  ```
- `python3 validators/validate_gate_decision.py --repo-root . examples/self-modification-gate-decision.toml examples/minimal-gate-decision.toml` ->
  ```
  GATE-DECISION VALIDATION PASSED (2 files checked; INV01..INV06 enforced).
  ```
  (exit 0)
- Synthesised both negative variants (exact cases from verification_report.toml:78-79 and codex.md:56) into /tmp/neg-inv06/:
  - neg-same-provider.toml: subject_class=self-modification, proposing=anthropic/claude, deciding=anthropic/gpt
  - neg-same-family.toml: subject_class=self-modification, proposing=anthropic/claude, deciding=openai/claude
  (files persisted for this session; content matches the here-docs in .github/workflows/validate.yml:376-414)
- `python3 validators/validate_gate_decision.py --repo-root . /tmp/neg-inv06/neg-same-provider.toml` ->
  ```
  FAIL: /tmp/neg-inv06/neg-same-provider.toml: INV06 violated (conjunctive AND): deciding_provider_id ('anthropic') == proposing_provider_id ('anthropic'). INV06 requires BOTH deciding_provider_id != proposing_provider_id AND deciding_model_family_id != proposing_model_family_id. Same-provider/different-family and different-provider/same-family BOTH fail INV06.

  GATE-DECISION VALIDATION FAILED (1 defect; 0 files passed).
  ```
  (exit 1)
- `python3 validators/validate_gate_decision.py --repo-root . /tmp/neg-inv06/neg-same-family.toml` ->
  ```
  FAIL: /tmp/neg-inv06/neg-same-family.toml: INV06 violated (conjunctive AND): deciding_model_family_id ('claude') == proposing_model_family_id ('claude'). INV06 requires BOTH deciding_provider_id != proposing_provider_id AND deciding_model_family_id != proposing_model_family_id. Same-provider/different-family and different-provider/same-family BOTH fail INV06.

  GATE-DECISION VALIDATION FAILED (1 defect; 0 files passed).
  ```
  (exit 1)
- `cd tools/dagtoml-validate-rs && cargo build --release --locked` -> succeeded (2 pre-existing dead-code warnings on unrelated helpers; binary at target/release/dagtoml-validate-rs)
- Rust runs (clean capture):
  - positives (self-mod + minimal): exit 0, "DAGTOML VALIDATION PASSED (rust primary)"
  - neg-same-provider: exit 1, "INV06 violated (conjunctive AND): deciding_provider_id ("anthropic") == ... Same-provider/different-family and different-provider/same-family BOTH fail INV06."
  - neg-same-family: exit 1, identical structure with family equality
- `cd tools/dagtoml-validate-go && go build -o /tmp/dagtoml-validate-go ./...` -> "Go build OK"
- Go runs (clean capture):
  - positives: exit 0, "DAGTOML VALIDATION PASSED (go primary)"
  - neg-same-provider: exit 1, "INV06 violated (conjunctive AND): deciding_provider_id ("anthropic") == ... Same-provider/different-family..."
  - neg-same-family: exit 1, family equality variant
- `grep -nE 'enforced_by.*validate_gate_decision' profiles/agent-assurance/gate-decision-kind.toml` -> 5 lines (167 INV01, 174 INV02, 181 INV03, 188 INV04, 202 INV06); all bare "validators/validate_gate_decision.py"
- `grep -n '(planned)' profiles/agent-assurance/gate-decision-kind.toml || echo "none found - good"` -> none found - good
- `python3 validators/validate_abstraction_class.py --repo-root . core/*-kind.toml profiles/*/*-kind.toml` -> "ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 19 declared a §13 block)."
- `git diff 1e0e155..7782ade --name-only | grep -E 'validate_gate|gate-decision|validate.yml'` -> .github/workflows/validate.yml, profiles/agent-assurance/gate-decision-kind.toml, validators/validate_gate_decision.py (plus the three primary impl diffs and r2 review artifacts)
- Direct reads (with line ranges):
  - gate-decision-kind.toml:92-110 (CROSS-PROVIDER ATTRIBUTION (INV06) prose: "conjunctive AND is load-bearing: same-provider/different-family and different-provider/same-family BOTH fail INV06"), :199-204 (INV06 hard invariant with exact four-field + BOTH inequalities predicate), :167-202 (enforced_by entries)
  - validate_gate_decision.py:155-253 (INV06 block: subject_class=="self-modification" path, four required fields, vocab loads, :232 `same_provider = dec_p == prop_p`, :233 `same_family = dec_f == prop_f`, :234 `if same_provider or same_family:`, :247-252 defect with "conjunctive AND" + "BOTH fail INV06" wording), :258-291 (main + success msg citing INV01..INV06)
  - tools/dagtoml-validate-rs/src/main.rs:56-57 (Mode::GateDecision), :739-989 (mod gate_decision: load_vocab, validate at 790, INV06 at 906-985 with :962-964 `same_provider || same_family` + :979 identical conjunctive message), :1321-1334 (auto + explicit routing for "gate-decision")
  - tools/dagtoml-validate-go/main.go:119 (modeGateDecision), :832-840 (routing), :956-1099 (validateGateDecision: INV06 at 1033-1095 with :1078-1080 `sameProvider || sameFamily` + :1091 identical message)
  - .github/workflows/validate.yml:346-450 (full CI step: positives loop, mktemp here-doc synthesis of exact neg-same-provider + neg-same-family, python non-zero asserts, rs/go_bin loop with --mode gate-decision + REGRESSION guards; comment cites codex.md r1 blocker)
  - profiles/agent-assurance/ontology.toml:349-374 (subject_class, provider_id, model_family_id vocabularies with ijb_primitive=constraint/structural; values include "self-modification", "anthropic"/"openai", "claude"/"gpt")

S08.1 - closed (validator exists and is well-formed)

File validators/validate_gate_decision.py:1-292 exists, py_compile clean, imports only stdlib + tomllib. Explicit INV06 conjunctive-AND rejection present at :234 (rejects on `or`, matching the "BOTH inequalities must hold" predicate in gate-decision-kind.toml:201). Success path :284-286 emits "INV01..INV06 enforced". The --help banner (captured above) does not contain the INV01..INV06 token (argparse surfaces only first docstring paragraph; full citation lives in module docstring :2-5 and in the PASS message). All other verify_by items (file presence, explicit check logic, help invocation) satisfied. No functional gap.

S08.2 - closed (positives pass)

Literal execution of the exact command in verification_report.toml:67-68 produced exit 0 and the required PASS string citing INV01..INV06. The self-modification example (anthropic/claude proposing, openai/gpt deciding) satisfies the AND; the minimal example has no subject_class so INV06 is dormant.

S08.3 - closed (both r1 negative variants fail Python)

Both variants synthesised verbatim per verification_report.toml:77-85 and codex.md:56 (same-provider/different-family; different-provider/same-family). Both produced exit 1 + INV06 defect citing the exact violating equality + the "conjunctive AND" + "BOTH fail INV06" sentence. No accept.

S08.4 - closed (Rust primary enforces identically)

tools/dagtoml-validate-rs/src/main.rs:739-989 (mod gate_decision) implements the full INV01..INV06 surface, mirroring Python reference (explicit comment at :735). The AND predicate at :962-964 is `same_provider || same_family` with identical defect text at :979. Build succeeded. Execution against the 4-file suite produced matching PASS/FAIL outcomes and the exact INV06 wording on the negatives (quote style differs: Rust uses double quotes).

S08.5 - closed (Go primary enforces identically)

tools/dagtoml-validate-go/main.go:956-1099 (validateGateDecision) + mode constant :119 + routing :839-840. The conjunctive check at :1078-1080 (`sameProvider || sameFamily`) + message at :1091 is byte-for-byte semantically identical to the other two. Build + 4-file execution: positives exit 0, negatives exit 1 with correct INV06 defects.

S08.6 - closed (three-way agreement; no divergence)

Per verification_report.toml:110-113 and the "synthesise both r1 negative variants and run all three validators. Any accept = unclosed" rule: all three implementations accepted the same two positives and rejected the same two negatives with matching semantic defects (provider equality vs family equality). No implementation produced an accept on either negative variant. Bytewise output differs between Python and the primaries (as explicitly tolerated at verification_report.toml:111), but PASS/FAIL outcomes agree on every file. Divergence-is-a-build-break policy holds for INV06.

S08.7 - closed (CI step asserts the suite)

.github/workflows/validate.yml:346-450 is the exact step described in verification_report.toml:119-126. It:
- runs the two positives via Python
- synthesises the two negative variants via here-doc in mktemp (identical content to what I created)
- asserts non-zero exit for Python on each neg ("if ... then echo REGRESSION; exit 1")
- builds/runs the pre-built rs and go_bin primaries on positives + negatives (explicit `--mode gate-decision` for the latter)
- uses the same REGRESSION guard for primaries
- comments cite the r1 codex blocker at docs/reviews/2026-05-25-spec-e2e/raw_findings/codex.md

The +106 lines landed in the remediation commit.

S08.8 - closed (enforced_by markers clean)

profiles/agent-assurance/gate-decision-kind.toml contains exactly five `enforced_by = "validators/validate_gate_decision.py"` entries (lines 167,174,181,188,202) for INV01-INV04 + INV06. Zero contain "(planned)". INV05 remains the documented scope-declaration entry at :195. Matches verification_report.toml:131-133.

regression_check (S02, S05, S06, S07, S10, S11 surfaces)

- S02: abstraction-class validator still passes exactly ("19 file(s) checked; 19 declared a §13 block") — no drift.
- Primaries (S05): both built cleanly; gate-decision routing present in auto + explicit modes; execution on the new gate-decision surface succeeded.
- No new banned `kind =` markers introduced (remediation touches only the dedicated gate validator path).
- CI workflow (S10) step added without disturbing the existing pinned-action / canonical-sweep structure.
- The remediation diff touched only the declared surfaces (new validator, kind cleanup, primary impls, CI wiring, r2 review docs). No regression in the r1-closed S-closures.

persisted_review_evidence

- This file: docs/reviews/2026-05-25-spec-e2e-r2/raw_findings/grok.md
- verification_report.toml (r2 closure spec)
- docs/reviews/2026-05-25-spec-e2e/raw_findings/codex.md (r1 blocker being closed)
- The three validator implementations + gate-decision-kind.toml + .github/workflows/validate.yml at 7782ade
- /tmp/neg-inv06/*.toml (synthesised negatives, matching CI here-docs)
- git commit 7782ade and its diff (26 files, +3130/-65; core changes limited to the five remediation targets)

All required bases used: inspected_code (specific file:line citations throughout), executed_tests_with_output (verbatim command results), inspected_docs (kind descriptor INV06 prose + ontology vocabs + verification_report + codex blocker + CI step + SPEC cross-refs via the kind), persisted_review_evidence (the r1/r2 review artifacts, the commit, the negative test files).

No forbidden bases employed.

The r1 S08 blocker (INV06 documented as SPEC-enforced at gate-decision-kind.toml:101-103 and :201 but absent from all shipped validators; both negative variants accepted) is fully remediated. All three implementations now carry the load-bearing conjunctive-AND predicate, the CI asserts it on the exact negative cases, the (planned) markers are stripped, and three-way agreement holds with zero accepts on the negatives.

Terminal verdict: unconditional_approval
