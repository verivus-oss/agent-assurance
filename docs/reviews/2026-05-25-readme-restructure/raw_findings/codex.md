# Codex review: README restructure

Scope reviewed: commit `b759eaf` over parent `1f08dea`, single modified file `README.md`.

## 1. Method

I read, in order:

- `docs/reviews/2026-05-25-readme-restructure/verification_report.toml`
- `docs/reviews/2026-05-25-readme-restructure/review_bundle.toml`
- `docs/reviews/2026-05-25-readme-restructure/review_prompt.md`
- `README.md`
- `git show bc2a7c5:README.md`
- `tools/review-request-dag.toml` policy blocks

I then ran the closure `verify_by` commands and additional byte checks against `SPEC.md`, profile descriptors, validators, examples, the Makefile, and `.github/workflows/validate.yml`. I did not use the initiator summary as evidence.

Key commands run:

```sh
git show bc2a7c5:README.md | grep -n 'after the repository is made public'
grep -nE 'after.*made public' README.md
grep -n 'calendar-versioned UTC' README.md
git tag --list 'v*'
ls -d tools/*/
grep -c '^tools/' README.md
grep -nE 'SPEC\.md#12|SPEC\.md#13|INV06|profiles/cost|profiles/disclosure|tiers/README' README.md
grep -nE 'taplo lint|cargo build --release|go build|make toml-conformance-install|make toml-conformance-all|validate_ijb_conformance|validate_closure_root|validate_abstraction_class' README.md
grep -nE '^(toml-conformance-install|toml-conformance-all|toml-conformance|toml-conformance-rs):' Makefile
grep -nE 'Taplo|toml-lang/toml-test|#!\[forbid\(unsafe_code\)\]|unsafe-free|cross-check' README.md
cat profiles/cost/PROFILE.toml | grep schema_version
cat profiles/disclosure/PROFILE.toml | grep schema_version
cat tools/review-request-dag.toml | head -20
```

I also ran a README link audit with a small Python script. It reported `links_total=43`, `external=3`, `internal=40`, and every internal target was `OK`; the five `SPEC.md#...` anchors were present in headings from `SPEC.md`.

## 2. Per-closure classification

### C01: closed

The exact prior-state recipe command produced no output because the old README wraps the sentence across two lines:

```sh
$ git show bc2a7c5:README.md | grep -n 'after the repository is made public'
```

Output:

```text
```

Exit status: 1.

Supplemental prior-state byte evidence confirms the sentence existed:

```sh
$ git show bc2a7c5:README.md | grep -n -A1 'first public release tag'
39:The first public release tag will be cut after the repository is made
40-public; see [GOVERNANCE.md](GOVERNANCE.md#releases).
```

The new README has no matching "after ... made public" sentence:

```sh
$ grep -nE 'after.*made public' README.md
```

Output:

```text
```

Exit status: 1.

The new README contains the calendar-UTC tag wording:

```sh
$ grep -n 'calendar-versioned UTC' README.md
45:Release tags use calendar-versioned UTC timestamps
```

The repository has a matching release tag:

```sh
$ git tag --list 'v*'
v2026-05-25T03-30-02Z
```

Evidence: `README.md:43-50`.

### C02: closed

The repository has seven `tools/*/` subdirectories:

```sh
$ ls -d tools/*/
tools/dagtoml-duckdb-go/
tools/dagtoml-duckdb/
tools/dagtoml-rdf-go/
tools/dagtoml-rdf/
tools/dagtoml-validate-go/
tools/dagtoml-validate-rs/
tools/toml-test-decode-rs/
```

Each appears in the Repository Map:

```sh
$ grep -nE '^tools/(dagtoml-duckdb-go|dagtoml-duckdb|dagtoml-rdf-go|dagtoml-rdf|dagtoml-validate-go|dagtoml-validate-rs|toml-test-decode-rs)/' README.md
113:tools/dagtoml-validate-rs/      Primary safe-Rust validator
114:tools/dagtoml-validate-go/      Primary safe-Go validator
115:tools/dagtoml-rdf/              Rust generator → RDF/Turtle
116:tools/dagtoml-rdf-go/           Go port of dagtoml-rdf
117:tools/dagtoml-duckdb/           Rust generator → DuckDB
118:tools/dagtoml-duckdb-go/        Go port of dagtoml-duckdb
119:tools/toml-test-decode-rs/      toml-test conformance shim (Rust parser)
```

The top-level Makefile appears:

```sh
$ grep -n '^Makefile' README.md
125:Makefile                        Developer convenience targets (toml-conformance{,-rs,-all})
```

The README has seven `tools/` map entries:

```sh
$ grep -c '^tools/' README.md
7
```

Evidence: `README.md:101-126`.

### C03: closed

The required Start Here pointers are present:

```sh
$ grep -nE 'SPEC\.md#12|SPEC\.md#13|INV06|profiles/cost|profiles/disclosure|tiers/README' README.md
80:| Declare abstraction boundaries and capability envelopes | [SPEC.md §13](SPEC.md#13-abstraction-class-and-capability-envelope) |
81:| Propagate brittleness through upstream evidence | [SPEC.md §12](SPEC.md#12-the-closure-root-rule-brittleness-propagation) |
83:| Pick a deployment tier (`solo` ⊂ `team` ⊂ `group` ⊂ `organization` ⊂ `enterprise`) | [profiles/agent-assurance/tiers/README.md](profiles/agent-assurance/tiers/README.md) |
84:| Forbid an agent from approving its own self-modifying gate-decision (INV06) | [profiles/agent-assurance/gate-decision-kind.toml](profiles/agent-assurance/gate-decision-kind.toml) (search for `INV06`) |
85:| Account for cost as a first-class artifact | [profiles/cost/PROFILE.toml](profiles/cost/PROFILE.toml), [profiles/cost/cost-record-kind.toml](profiles/cost/cost-record-kind.toml) |
86:| Redact or selectively disclose evidence | [profiles/disclosure/PROFILE.toml](profiles/disclosure/PROFILE.toml), [profiles/disclosure/disclosure-attestation-kind.toml](profiles/disclosure/disclosure-attestation-kind.toml), [profiles/disclosure/redaction-manifest-kind.toml](profiles/disclosure/redaction-manifest-kind.toml), [profiles/disclosure/selective-disclosure-proof-kind.toml](profiles/disclosure/selective-disclosure-proof-kind.toml) |
108:profiles/cost/                  Optional Cost Profile (cost-record kind)
109:profiles/disclosure/            Optional Disclosure Profile
```

`INV06` and `tiers/README.md` are present:

```sh
$ grep -n 'INV06' README.md
84:| Forbid an agent from approving its own self-modifying gate-decision (INV06) | [profiles/agent-assurance/gate-decision-kind.toml](profiles/agent-assurance/gate-decision-kind.toml) (search for `INV06`) |
```

```sh
$ grep -n 'tiers/README.md' README.md
83:| Pick a deployment tier (`solo` ⊂ `team` ⊂ `group` ⊂ `organization` ⊂ `enterprise`) | [profiles/agent-assurance/tiers/README.md](profiles/agent-assurance/tiers/README.md) |
```

The four role headers are H3s:

```sh
$ grep -nE '^### If you want to (understand|author|enforce|implement)' README.md
56:### If you want to understand the format
66:### If you want to author DAG-TOML
76:### If you want to enforce policy
88:### If you want to implement a validator
```

Evidence: `README.md:52-97`.

### C04: closed

The Local Validation block references the required validation workflow:

```sh
$ grep -nE 'taplo lint|cargo build --release|go build|make toml-conformance-install|make toml-conformance-all|validate_ijb_conformance|validate_closure_root|validate_abstraction_class' README.md
160:taplo lint
163:cd tools/dagtoml-validate-rs && cargo build --release && cd -
164:cd tools/dagtoml-validate-go && go build -o /tmp/dagtoml-validate-go ./... && cd -
167:make toml-conformance-install
168:make toml-conformance-all   # runs both Go-parser and Rust-parser suites
178:python3 validators/validate_ijb_conformance.py core/ontology.toml
179:python3 validators/validate_closure_root.py --discover .         # SPEC §12
180:python3 validators/validate_abstraction_class.py --discover .    # SPEC §13
```

The cited Python validators exist:

```sh
$ ls validators/validate_ijb_conformance.py validators/validate_closure_root.py validators/validate_abstraction_class.py validators/validate_implementation_dag.py validators/validate_traceability.py validators/validate_review_readiness.py
validators/validate_abstraction_class.py
validators/validate_closure_root.py
validators/validate_ijb_conformance.py
validators/validate_implementation_dag.py
validators/validate_review_readiness.py
validators/validate_traceability.py
```

The cited Makefile targets exist:

```sh
$ grep -nE '^(toml-conformance-install|toml-conformance-all|toml-conformance|toml-conformance-rs):' Makefile
64:toml-conformance-install: ## Install pinned toml-test + BurntSushi decoder under $GOBIN.
68:toml-conformance: ## Run TOML 1.0 spec-conformance suite against the BurntSushi parser used by tools/dagtoml-validate-go.
73:toml-conformance-rs: ## Run TOML 1.0 spec-conformance suite against the `toml` crate used by tools/dagtoml-validate-rs.
85:toml-conformance-all: toml-conformance toml-conformance-rs ## Run both Go-parser and Rust-parser conformance suites.
```

Note: the verifier text says "`cargo build --release` (twice - once per primary)", but the Go primary is correctly built with `go build`; the README has one Rust cargo build and one Go build. Evidence: `README.md:155-181`.

### C05: closed

The section heading exists:

```sh
$ grep -n '^## Validation tooling' README.md
132:## Validation tooling
```

The table and rationale include the required terms:

```sh
$ grep -nE 'Taplo|toml-lang/toml-test|#!\[forbid\(unsafe_code\)\]|unsafe-free|cross-check' README.md
94:| Python reference validators (cross-check, not normative) | [validators/](validators/) |
112:validators/                     Python reference validators (cross-check)
140:| Syntax | [Taplo](https://taplo.tamasfe.dev/) | TOML 1.0 lint, duplicate-key detection |
141:| Parser conformance | `toml-lang/toml-test` suite | Verifies the parsers the primary validators import (`BurntSushi/toml` for Go, `toml 0.8` crate for Rust) |
142:| Semantics — **primary** | `tools/dagtoml-validate-rs/` (safe Rust, `#![forbid(unsafe_code)]`) | Authoritative for profile-descriptor, disclosure, cost, §2.5–§2.7 meta surface, §11.1 provenance encryption |
150:parsers exist (`#![forbid(unsafe_code)]` Rust crates, `unsafe`-free
151:Go modules); Python is the historical reference and cross-check.
159:# Install Taplo per https://taplo.tamasfe.dev/cli/installation/
186:cross-checks, IJB conformance, closure-root, abstraction-class +
```

The self-vouch rationale is present:

```sh
$ grep -n 'one implementation cannot self-vouch' README.md
148:legal-grade artifacts; one implementation cannot self-vouch. Rust and
```

Evidence: `README.md:132-151`. This closure is closed, but `README.md:142-143` contain separate factual blockers listed below.

### C06: closed

The Status table contains the cost and disclosure rows:

```sh
$ grep -nE 'Cost Profile schema|Disclosure Profile schema' README.md
39:| Cost Profile schema | `1.0.0` | Release candidate |
40:| Disclosure Profile schema | `1.0.0` | Release candidate |
```

The profile descriptors contain `schema_version = "1.0.0"`:

```sh
$ cat profiles/cost/PROFILE.toml | grep schema_version
schema_version    = "1.0.0"
schema_version    = { ijb_primitive = "constraint", ijb_constraint_type = "structural" }
```

```sh
$ cat profiles/disclosure/PROFILE.toml | grep schema_version
schema_version    = "1.0.0"
schema_version    = { ijb_primitive = "constraint", ijb_constraint_type = "structural" }
```

Evidence: `README.md:35-41`, `profiles/cost/PROFILE.toml:34`, `profiles/disclosure/PROFILE.toml:17`.

### C07: closed

The README cites `tools/review-request-dag.toml` in Governance:

```sh
$ grep -n 'review-request-dag.toml' README.md
216:multi-LLM review under [tools/review-request-dag.toml](tools/review-request-dag.toml)
```

The cited file exists and has policy content:

```sh
$ cat tools/review-request-dag.toml | head -20
# Reusable multi-reviewer independent-review workflow, encoded as a
# DAG-TOML `implementation-dag`. Author: Werner Kasselman.
#
# PURPOSE
#
# This DAG is the durable, machine-readable form of an instruction
# that was previously a free-text prompt. From now on, when a piece
# of work needs an independent multi-LLM review, instantiate this
# DAG, fill the [policy.instance] block, and execute the units in
# order.
#
# The DAG does NOT mock the review — it sequences the real steps
# (assemble bundle, dispatch reviews to named models, classify each
# DAG unit under review, rebut disagreements with code/doc evidence,
# persist the verbatim review text, iterate until terminal). The
# [policy] table carries the hard process rules that the units must
# obey; comments above each unit map the rule to the unit.
#
# LINEAGE
#
```

Policy blocks are present at `tools/review-request-dag.toml:56`, `:66`, `:77`, `:96`, `:103`, `:109`, `:117`, `:124`, and `:140`. The substantive-surface trigger is also stated in `CONTRIBUTING.md:58-68`.

Evidence: `README.md:210-218`.

## 3. Out-of-scope findings

None filed. I did not treat unchanged SPEC/profile/validator behavior as a closure blocker. However, README claims about that existing behavior are in scope because the README now publishes them.

## 4. Final blockers

- Severity: high. `README.md:142` says the Rust primary validator is "Authoritative for profile-descriptor, disclosure, cost, §2.5-§2.7 meta surface, §11.1 provenance encryption." The current primary validator routing does not implement cost-record-specific validation: Rust routes `profile-descriptor` and the three disclosure kinds only at `tools/dagtoml-validate-rs/src/main.rs:1045-1055`; Go does the same at `tools/dagtoml-validate-go/main.go:822-829`. Cost validation exists in the Python reference validator and CI cross-check (`validators/validate_cost.py`, `.github/workflows/validate.yml:189-204`), not in either primary validator.

Executed evidence:

```sh
$ rg -n 'cost-record|validate_cost|cost' tools/dagtoml-validate-rs/src/main.rs tools/dagtoml-validate-go/main.go validators/validate_cost.py .github/workflows/validate.yml
.github/workflows/validate.yml:159:            profiles/cost/PROFILE.toml
.github/workflows/validate.yml:163:            examples/minimal-cost-record.toml
.github/workflows/validate.yml:189:      - name: Cross-check (Python) — profile descriptors, disclosure profile, cost profile
.github/workflows/validate.yml:196:            profiles/cost/PROFILE.toml
.github/workflows/validate.yml:202:          python3 validators/validate_cost.py \
.github/workflows/validate.yml:204:            examples/minimal-cost-record.toml
.github/workflows/validate.yml:222:            profiles/cost/*-kind.toml
.github/workflows/validate.yml:250:          for f in core/*-kind.toml profiles/agent-assurance/*-kind.toml profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml; do
.github/workflows/validate.yml:280:            profiles/cost/ontology.toml
.github/workflows/validate.yml:281:          for f in core/*-kind.toml profiles/agent-assurance/*-kind.toml profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml; do
.github/workflows/validate.yml:285:          for f in profiles/agent-assurance/PROFILE.toml profiles/disclosure/PROFILE.toml profiles/cost/PROFILE.toml; do
.github/workflows/validate.yml:305:                   examples/minimal-cost-record.toml; do
validators/validate_cost.py:2:"""Validate `cost-record` instance documents (cost profile).
validators/validate_cost.py:5:`profiles/cost/cost-record-kind.toml`:
validators/validate_cost.py:9:  INV02 — `[record].citing_kind` is in the closed `cost_citing_kind`
validators/validate_cost.py:12:          `cost_dimension_category` vocabulary.
validators/validate_cost.py:55:    """Load the cost profile's closed vocabularies from its ontology.
validators/validate_cost.py:62:    ont = repo_root / "profiles" / "cost" / "ontology.toml"
validators/validate_cost.py:64:    want = {"decider_class", "cost_citing_kind", "cost_dimension_category"}
validators/validate_cost.py:74:            f"cost-profile ontology is missing required vocabularies: "
validators/validate_cost.py:99:    if not isinstance(meta, dict) or meta.get("template_kind") != "cost-record":
validators/validate_cost.py:101:            f"{path}: not a cost-record instance "
validators/validate_cost.py:102:            f"(meta.template_kind != 'cost-record')"
validators/validate_cost.py:104:    if meta.get("framework_profile") != "cost":
validators/validate_cost.py:106:            f"{path}: meta.framework_profile must be 'cost', "
validators/validate_cost.py:132:    if isinstance(ck, str) and ck not in vocab["cost_citing_kind"]:
validators/validate_cost.py:135:            f"cost_citing_kind={sorted(vocab['cost_citing_kind'])}"
validators/validate_cost.py:170:            if cat not in vocab["cost_dimension_category"]:
validators/validate_cost.py:174:                    f"cost_dimension_category={sorted(vocab['cost_dimension_category'])}"
validators/validate_cost.py:197:        description="Validate cost-record instance documents (cost profile).",
validators/validate_cost.py:199:    parser.add_argument("paths", nargs="+", help="TOML cost-record file(s) to validate.")
validators/validate_cost.py:204:            "Repository root containing `profiles/cost/ontology.toml` "
```

- Severity: medium. `README.md:143` says the safe-Go primary row has the same surface as Rust and that "CI requires bytewise agreement." The workflow runs the two primary validators sequentially at `.github/workflows/validate.yml:184-187`; it does not capture and compare their output with `cmp`/`diff`. The validators also print different success headers at `tools/dagtoml-validate-rs/src/main.rs:1078-1080` and `tools/dagtoml-validate-go/main.go:853-855`, so literal bytewise stdout agreement is not what CI enforces.

Executed evidence:

```sh
$ rg -n 'cmp|diff|bytewise|byte-wise|agreement|dagtoml-validate-rs|dagtoml-validate-go' .github/workflows/validate.yml validators Makefile tools/dagtoml-validate-rs tools/dagtoml-validate-go
Makefile:19:# validator (tools/dagtoml-validate-go) depends on. Conformance of
Makefile:53:# uses the same `toml` 0.8 crate that tools/dagtoml-validate-rs
Makefile:68:toml-conformance: ## Run TOML 1.0 spec-conformance suite against the BurntSushi parser used by tools/dagtoml-validate-go.
Makefile:73:toml-conformance-rs: ## Run TOML 1.0 spec-conformance suite against the `toml` crate used by tools/dagtoml-validate-rs.
.github/workflows/validate.yml:32:          cache-dependency-path: tools/dagtoml-validate-go/go.sum
.github/workflows/validate.yml:45:          cd tools/dagtoml-validate-rs
.github/workflows/validate.yml:47:          cp target/release/dagtoml-validate-rs "${RUNNER_TEMP}/dagtoml-validate-rs"
.github/workflows/validate.yml:52:          cd tools/dagtoml-validate-go
.github/workflows/validate.yml:53:          go build -o "${RUNNER_TEMP}/dagtoml-validate-go" ./...
.github/workflows/validate.yml:89:        # Go validator (tools/dagtoml-validate-go) depends on, so a
.github/workflows/validate.yml:104:        # crate dagtoml-validate-rs depends on, then runs the
.github/workflows/validate.yml:154:          rs="${RUNNER_TEMP}/dagtoml-validate-rs"
.github/workflows/validate.yml:155:          go_bin="${RUNNER_TEMP}/dagtoml-validate-go"
tools/dagtoml-validate-go/go.mod:1:module github.com/verivus-oss/agent-assurance/tools/dagtoml-validate-go
tools/dagtoml-validate-go/main.go:1:// dagtoml-validate-go is the Go primary validator for the DAG-TOML
tools/dagtoml-validate-go/main.go:14:// (tools/dagtoml-validate-rs/). Both are primary; the Python
tools/dagtoml-validate-go/main.go:843:		// stable order is helpful for diff-based investigation
tools/dagtoml-validate-rs/Cargo.lock:6:name = "dagtoml-validate-rs"
tools/dagtoml-validate-rs/Cargo.toml:2:name = "dagtoml-validate-rs"
tools/dagtoml-validate-rs/Cargo.toml:18:name = "dagtoml-validate-rs"
tools/dagtoml-validate-rs/src/main.rs:60:            "usage: dagtoml-validate-rs --repo-root <path> [--mode auto|profile|disclosure|provenance|meta] <file.toml> ..."
validators/check_manifest_drift.sh:6:# Exits 0 on agreement, 1 on any drift. Prints a small report either way.
validators/validate_implementation_dag.py:146:        # the same cycle reported from a different entry point dedupes, and
validators/check_attribute_values.py:22:count differs from its expected value, the script reports the
validators/check_attribute_values.py:32:Exit 0 on full agreement; 1 on any drift.
validators/validate_ijb_conformance.py:164:    mutating any of them to a different valid IJB value (e.g. swapping
```

Workflow excerpt:

```sh
$ nl -ba .github/workflows/validate.yml | sed -n '143,189p'
   143	      - name: Primary validators (Rust + Go) — full canonical sweep
   144	        # Safe-Rust + Go are the primary validators for the v1.0
   145	        # layering artifacts AND for the SPEC §2.5 / §2.6 / §2.7 /
   146	        # §11.1 meta surface that applies to EVERY DAG-TOML file.
   147	        # CI runs them against every canonical example, every tier
   148	        # file, every profile descriptor, and the new disclosure
   149	        # examples so the meta-rules can't drift unnoticed on old
   150	        # kinds. Python validators below run as cross-checks;
   151	        # divergence between primary and reference is a build break.
   152	        run: |
   153	          set -e
   154	          rs="${RUNNER_TEMP}/dagtoml-validate-rs"
   155	          go_bin="${RUNNER_TEMP}/dagtoml-validate-go"
   156	          targets=(
   157	            profiles/agent-assurance/PROFILE.toml
   158	            profiles/disclosure/PROFILE.toml
   159	            profiles/cost/PROFILE.toml
   160	            examples/minimal-disclosure-attestation.toml
   161	            examples/minimal-redaction-manifest.toml
   162	            examples/minimal-selective-disclosure-proof.toml
   163	            examples/minimal-cost-record.toml
   164	            examples/minimal-implementation-dag.toml
   165	            examples/minimal-traceability.toml
   166	            examples/minimal-spec-contract.toml
   167	            examples/minimal-threat-model.toml
   168	            examples/minimal-smoke-validation.toml
   169	            examples/minimal-rollback-plan.toml
   170	            examples/minimal-adapter-contract.toml
   171	            examples/minimal-adapter-registry-binding.toml
   172	            examples/minimal-assertion-bundle.toml
   173	            examples/minimal-assertion-log-record.toml
   174	            examples/minimal-gate-decision.toml
   175	            examples/minimal-review-readiness/REVIEW_READINESS.toml
   176	            examples/minimal-review-readiness/CONTRACT_DECLARATION.toml
   177	            examples/minimal-review-readiness/EVIDENCE_MATRIX.toml
   178	            profiles/agent-assurance/tiers/solo.toml
   179	            profiles/agent-assurance/tiers/team.toml
   180	            profiles/agent-assurance/tiers/group.toml
   181	            profiles/agent-assurance/tiers/organization.toml
   182	            profiles/agent-assurance/tiers/enterprise.toml
   183	          )
   184	          echo "--- Rust primary ---"
   185	          "$rs" --repo-root . "${targets[@]}"
   186	          echo "--- Go primary ---"
   187	          "$go_bin" --repo-root . "${targets[@]}"
   188	
   189	      - name: Cross-check (Python) — profile descriptors, disclosure profile, cost profile
```

Process confirmations: this is a README-only documentation change, so active-user migration guidance is not directly changed; README still states migration notes are required for backwards-incompatible changes at `README.md:47-50`. I found no README edit that retcons a historical dated spec without link or correction note. Claimed closure checks above were run with command output and status.

Terminal verdict: concrete_unresolvable_blocker
Blocker: `README.md:142-143` contains factual claims that do not match the repository bytes: the primary validators do not implement cost-record-specific validation (`tools/dagtoml-validate-rs/src/main.rs:1045-1055`, `tools/dagtoml-validate-go/main.go:822-829`), and CI does not require bytewise Rust/Go primary-validator output agreement (`.github/workflows/validate.yml:184-187` runs them sequentially without a comparison). These are public README claims about shipped validator coverage and CI enforcement, so the README restructure cannot receive unconditional approval as written.
