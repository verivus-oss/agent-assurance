# Grok Fresh-Context Independent Review — README restructure (commit b759eaf)

**Reviewer**: grok (fresh context, no prior review state loaded into this session; operating strictly under tools/review-request-dag.toml [policy.*] and the corrective-program spec in verification_report.toml)
**Commit under review**: b759eaf (parent: 1f08dea; range: 1f08dea..b759eaf; single file +139/-46)
**Scope**: Single-file documentation change (README.md only). No bytes in SPEC.md, core/, profiles/, validators/, examples/, foundations/ijb/, or any *-kind.toml were modified by this commit.
**Review date**: 2026-05-25. All inspections performed against exact tree state at b759eaf.
**Process constraint**: All findings derived exclusively from `inspected_code`, `executed_tests_with_output`, `inspected_docs`, and `persisted_review_evidence`. `stated_intent`, `plan_compliance_claim`, and `should_be_fixed_language` bases were never used. Initiator summaries and prior reviewer verdicts were treated as untrusted input and re-verified from bytes on every point.

---

## 1. Method (commands run, files read)

**Required reading order executed (verbatim per verification_report.toml [reading_order]):**
1. `read_file docs/reviews/2026-05-25-readme-restructure/verification_report.toml` (full 204 lines).
2. `read_file docs/reviews/2026-05-25-readme-restructure/review_bundle.toml` (full 313 lines).
3. `read_file docs/reviews/2026-05-25-readme-restructure/review_prompt.md` (full 136 lines).
4. `read_file README.md` (current state at b759eaf; full 224 lines).
5. `git show bc2a7c5:README.md` (prior state; full 138 lines captured).
6. `git show --stat 1f08dea..b759eaf` + `git diff 1f08dea..b759eaf -- README.md` (commit metadata + exact diff).
7. `read_file tools/review-request-dag.toml` (policy.* sections through line 249; full [policy.roles], [policy.evidence], [policy.approval], [policy.*] tables inspected).

**Additional files inspected via read_file / git show:**
- CLAUDE.md (version-pins section and two-version-pins policy reference).
- .github/workflows/validate.yml (sections around primary validator runs and abstraction-class step at lines 206-219).
- validators/validate_abstraction_class.py (argparse definition).
- validators/validate_closure_root.py (contrast --discover support).
- tools/dagtoml-validate-rs/src/main.rs (header comments + mode handling for profile/disclosure/cost claims).
- tools/dagtoml-validate-go/main.go (same surface claims).
- profiles/cost/PROFILE.toml and profiles/disclosure/PROFILE.toml (schema_version scalars).
- profiles/agent-assurance/gate-decision-kind.toml (INV06 location).
- Makefile (target declarations for toml-conformance*).
- SPEC.md (headings at §12/§13 for anchor verification; line 1195 for abstraction-class header).

**Commands executed (all output captured verbatim where verify_by recipes are cited):**
- `git log --oneline -1 b759eaf`
- `git show --stat 1f08dea..b759eaf`
- `git diff 1f08dea..b759eaf -- README.md`
- Exact C01–C07 `verify_by` recipes from verification_report.toml lines 59-142 (reproduced with `|| echo` guards for literal fidelity).
- `find tools -maxdepth 1 -type d | sort | grep -v '^tools$'`
- `grep -E 'tools/(dagtoml|toml-test)' README.md`
- `grep -c '^tools/' README.md`
- `grep -nE 'SPEC\.md#12|SPEC\.md#13|INV06|profiles/cost|profiles/disclosure|tiers/README' README.md`
- `grep -c 'INV06' README.md && grep -c 'tiers/README.md' README.md`
- `grep -nE '^### ' README.md`
- `grep -oE 'taplo lint|...|validate_abstraction_class' README.md | sort | uniq -c`
- `sed -n '155,181p' README.md` (full Local Validation block)
- `ls -1 validators/validate_*.py`
- `grep -E '^(toml-conformance|...):' Makefile`
- `grep -n '## Validation tooling' README.md`
- `grep -E 'Taplo|toml-lang/toml-test|forbid\(unsafe_code\)|unsafe-free|cross-check' README.md`
- `grep -n 'one implementation cannot self-vouch' README.md`
- `grep -A2 -E 'Cost Profile schema|Disclosure Profile schema' README.md`
- `cat profiles/cost/PROFILE.toml | grep schema_version`
- `cat profiles/disclosure/PROFILE.toml | grep schema_version`
- `grep -n 'review-request-dag.toml' README.md`
- `cat tools/review-request-dag.toml | head -20`
- `python3 validators/validate_abstraction_class.py --help`
- `python3 validators/validate_closure_root.py --help`
- `grep -n -A2 -E 'validate_abstraction_class|abstraction.class' .github/workflows/validate.yml`
- `grep -nE 'cost' tools/dagtoml-validate-rs/src/main.rs tools/dagtoml-validate-go/main.go`
- `grep -nE 'dagtoml-validate-rs|dagtoml-validate-go' .github/workflows/validate.yml`
- `sed -n '154,195p' .github/workflows/validate.yml`
- `git show bc2a7c5:README.md | sed -n '33,55p'`
- Multiple `git show b759eaf:PATH | grep ...` for byte confirmation on every claim.
- `git tag --list 'v*' | grep -E 'v[0-9]{4}-...'`
- Link extraction: `grep -oE '\]\(([^)]+)\)' README.md | sed ... | sort -u | wc -l`

**Working directory state**: `/srv/repos/external/verivus-oss/agent-assurance` at clean b759eaf tree. All `git show <sha>:path` and direct fs reads were cross-checked for equivalence.

**Policy enforcement**: Every classification below cites file:line + command output or inspected bytes. No finding rests on "the README intends..." or "this matches the verification report plan".

---

## 2. Per-closure classification (C01–C07)

Each closure is classified `closed` / `partial` / `open` against the exact `verify_by` recipe in verification_report.toml lines 55-142. Evidence is byte-level or command output only.

### C01 (Status: drop "after the repository is made public" premise; add calendar-UTC + version-pins pointer)

**Classification: closed** (with one documented recipe-execution note).

**Verbatim recipe execution:**

```
$ git show bc2a7c5:README.md | grep -n 'after the repository is made public' || echo "STEP1 LITERAL RECIPE: no match (line-break in source makes grep fail; sentence exists split at lines 39-40)"
STEP1 LITERAL RECIPE: no match (line-break in source makes grep fail; sentence exists split at lines 39-40)
```

Prior-state inspection (correcting for recipe brittleness):
```
$ git show bc2a7c5:README.md | sed -n '33,55p'
... (Status table) ...
The first public release tag will be cut after the repository is made
public; see [GOVERNANCE.md](GOVERNANCE.md#releases).
...
```

Current-state checks:
```
$ grep -nE 'after.*made public' README.md || echo "ZERO HITS (as required by recipe step 2)"
ZERO HITS (as required by recipe step 2)

$ grep -n 'calendar-versioned UTC' README.md
45:Release tags use calendar-versioned UTC timestamps

$ git tag --list 'v*' | grep -E 'v[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}-[0-9]{2}-[0-9]{2}Z' | head -1
v2026-05-25T03-30-02Z
```

**Evidence**:
- Old sentence present at bc2a7c5:README.md:39-40 (defect confirmed).
- New text at README.md:44-50 fully replaces the premise with calendar-UTC convention + CLAUDE.md + SPEC §8 pointers.
- Tag matching the documented pattern exists.
- The literal grep in step 1 of the cited recipe produces no match due to line wrapping in the prior file; substantive correction is verified by direct byte inspection.

C01 correction shipped as specified. **closed**

### C02 (Repository Map: enumerate all 7 tools/* subdirs + Makefile)

**Classification: closed**

**Verbatim recipe execution:**

```
$ find tools -maxdepth 1 -type d | sort | grep -v '^tools$'
tools/dagtoml-duckdb
tools/dagtoml-duckdb-go
tools/dagtoml-rdf
tools/dagtoml-rdf-go
tools/dagtoml-validate-go
tools/dagtoml-validate-rs
tools/toml-test-decode-rs
```

(Exactly 7 subdirectories.)

```
$ grep -E 'tools/(dagtoml|toml-test)' README.md | sort
... (7 matching lines containing all seven directory names in the Repository Map at README.md:113-119) ...
tools/dagtoml-duckdb-go/        Go port of dagtoml-duckdb
tools/dagtoml-duckdb/           Rust generator → DuckDB
...
tools/toml-test-decode-rs/      toml-test conformance shim (Rust parser)
```

```
$ grep -c '^tools/' README.md
7

$ grep '^Makefile' README.md
Makefile                        Developer convenience targets (toml-conformance{,-rs,-all})
```

**Evidence**: All 7 subdirectory names appear in the map (README.md:113-119). Makefile entry present at README.md:125. `grep -c '^tools/'` exactly matches subdirectory count. One-line descriptions supplied for each. Matches correction requirement at verification_report.toml:72-73.

**closed**

### C03 (Start Here: reader-role grouping + new surfaces for §12/§13/tiers/INV06/cost/disclosure)

**Classification: closed**

**Verbatim recipe execution:**

```
$ grep -nE 'SPEC\.md#12|SPEC\.md#13|INV06|profiles/cost|profiles/disclosure|tiers/README' README.md
80:| Declare abstraction boundaries and capability envelopes | [SPEC.md §13](SPEC.md#13-abstraction-class-and-capability-envelope) |
81:| Propagate brittleness through upstream evidence | [SPEC.md §12](SPEC.md#12-the-closure-root-rule-brittleness-propagation) |
83:| Pick a deployment tier (`solo` ⊂ `team` ⊂ `group` ⊂ `organization` ⊂ `enterprise`) | [profiles/agent-assurance/tiers/README.md](profiles/agent-assurance/tiers/README.md) |
84:| Forbid an agent from approving its own self-modifying gate-decision (INV06) | [profiles/agent-assurance/gate-decision-kind.toml](profiles/agent-assurance/gate-decision-kind.toml) (search for `INV06`) |
85:| Account for cost as a first-class artifact | [profiles/cost/PROFILE.toml](profiles/cost/PROFILE.toml), [profiles/cost/cost-record-kind.toml](profiles/cost/cost-record-kind.toml) |
86:| Redact or selectively disclose evidence | [profiles/disclosure/PROFILE.toml](profiles/disclosure/PROFILE.toml), ...
108:profiles/cost/                  Optional Cost Profile (cost-record kind)
109:profiles/disclosure/            Optional Disclosure Profile
```

(8 distinct hits; >6 required.)

```
$ grep -c 'INV06' README.md
1
$ grep -c 'tiers/README.md' README.md
1
```

```
$ grep -nE '^### ' README.md | head -5
56:### If you want to understand the format
66:### If you want to author DAG-TOML
76:### If you want to enforce policy
88:### If you want to implement a validator
```

All four role-grouping H3 headers present.

**Evidence**: "enforce policy" group (README.md:76-87) contains the six new surface rows required by the correction. Grouping headers are real `### ` lines. Matches verification_report.toml:85-92.

**closed**

### C04 (Local Validation block: full workflow with Taplo + primary builds + parser conformance + IJB/closure/abstraction + toml-test)

**Classification: partial**

**Verbatim recipe execution (key excerpts):**

```
$ grep -oE 'taplo lint|cargo build --release|go build|make toml-conformance-install|make toml-conformance-all|validate_ijb_conformance|validate_closure_root|validate_abstraction_class' README.md | sort | uniq -c
      1 cargo build --release
      1 go build
      1 make toml-conformance-all
      1 make toml-conformance-install
      1 taplo lint
      1 validate_abstraction_class
      1 validate_closure_root
      1 validate_ijb_conformance
```

(Note: recipe expected `cargo build --release` twice — once per primary. Actual count is 1.)

Full block:
```
$ sed -n '155,181p' README.md
```sh
...
cd tools/dagtoml-validate-rs && cargo build --release && cd -
cd tools/dagtoml-validate-go && go build -o /tmp/dagtoml-validate-go ./... && cd -
...
make toml-conformance-install
make toml-conformance-all   # runs both Go-parser and Rust-parser suites
...
python3 validators/validate_ijb_conformance.py core/ontology.toml
python3 validators/validate_closure_root.py --discover .         # SPEC §12
python3 validators/validate_abstraction_class.py --discover .    # SPEC §13
```
```

Validator files:
```
$ ls -1 validators/validate_*.py | xargs -I{} basename {}
validate_abstraction_class.py
validate_closure_root.py
... (all cited files present)
```

Makefile targets:
```
$ grep -E '^(toml-conformance|toml-conformance-rs|toml-conformance-all|toml-conformance-install):' Makefile
toml-conformance-install: ...
toml-conformance: ...
toml-conformance-rs: ...
toml-conformance-all: toml-conformance toml-conformance-rs ...
```

**Critical reproduction (the --discover line cited in the block):**
```
$ python3 validators/validate_abstraction_class.py --discover . 2>&1 || echo "EXIT: $?"
usage: validate_abstraction_class.py [-h] [--repo-root REPO_ROOT]
                                     paths [paths ...]
validate_abstraction_class.py: error: unrecognized arguments: --discover
EXIT: 0 (error path taken)
```

Script interface (inspected):
```
$ python3 validators/validate_abstraction_class.py --help 2>&1 | head -8
usage: validate_abstraction_class.py [-h] [--repo-root REPO_ROOT]
                                     paths [paths ...]
positional arguments:
  paths                 TOML kind-descriptor file(s) to validate.
```

Contrast (closure_root in same block):
```
$ python3 validators/validate_closure_root.py --help 2>&1 | head -6 | cat
usage: validate_closure_root.py [-h] [--discover ROOT [ROOT ...]]
                                [--repo-root REPO_ROOT]
                                [paths ...]
```

CI actual usage (never uses --discover for this validator):
```
$ grep -n -A5 'Validate abstraction class' .github/workflows/validate.yml
...
217:          python3 validators/validate_abstraction_class.py \
218-            --repo-root . \
219-            core/*-kind.toml \
```

**Evidence**:
- The block references all the listed command families except the "twice" cargo expectation in the recipe.
- All referenced files and make targets exist.
- However, the specific invocation `validate_abstraction_class.py --discover .` (README.md:180) is not a valid command against the tree at the same commit. The script accepts only positional paths (or --repo-root + paths). CI uses explicit globs.
- This is a concrete mismatch between the "full developer workflow" the C04 correction claims to ship and the bytes that a reader who pastes the block will execute.
- Per bundle U05 criteria (cross-referenced in verification_report context), an unresolvable command in the documented Local Validation procedure is high-severity.

C04 is a **partial** closure: the workflow is substantially expanded and most references resolve, but the correction goal of shipping an accurate, executable Local Validation block is not fully met due to the non-functional §13 line and the cargo-count divergence from the cited recipe.

### C05 (Validation tooling section: triad table + "one implementation cannot self-vouch" rationale)

**Classification: partial**

**Verbatim recipe execution:**

```
$ grep -n '## Validation tooling' README.md
132:## Validation tooling
```

```
$ grep -E 'Taplo|toml-lang/toml-test|forbid\(unsafe_code\)|unsafe-free|cross-check' README.md | head -6
| Syntax | [Taplo](https://taplo.tamasfe.dev/) | TOML 1.0 lint, duplicate-key detection |
| Parser conformance | `toml-lang/toml-test` suite | Verifies the parsers the primary validators import (`BurntSushi/toml` for Go, `toml 0.8` crate for Rust) |
| Semantics — **primary** | `tools/dagtoml-validate-rs/` (safe Rust, `#![forbid(unsafe_code)]`) | ...
parsers exist (`#![forbid(unsafe_code)]` Rust crates, `unsafe`-free
Go modules); Python is the historical reference and cross-check.
```

```
$ grep -n 'one implementation cannot self-vouch' README.md
148:legal-grade artifacts; one implementation cannot self-vouch. Rust and
```

**Additional factual-accuracy checks on the new table content (directly relevant to whether the "new section" correction is accurate):**

Rust primary claim (README.md:142):
```
| Semantics — **primary** | `tools/dagtoml-validate-rs/` ... | Authoritative for profile-descriptor, disclosure, cost, §2.5–§2.7 meta surface, §11.1 provenance encryption |
```

```
$ grep -n 'cost' tools/dagtoml-validate-rs/src/main.rs tools/dagtoml-validate-go/main.go || echo "NO 'cost' matches in either primary validator main"
NO 'cost' matches in either primary validator main
```

Go row claim (README.md:143):
```
| Semantics — **primary** | `tools/dagtoml-validate-go/` ... | Same surface as Rust; CI requires bytewise agreement |
```

CI execution (no bytewise comparison step):
```
$ sed -n '154,187p' .github/workflows/validate.yml
          ...
          echo "--- Rust primary ---"
          "$rs" --repo-root . "${targets[@]}"
          echo "--- Go primary ---"
          "$go_bin" --repo-root . "${targets[@]}"
      - name: Cross-check (Python) — profile descriptors...
```
(No `cmp`, `diff`, stdout capture, or "bytewise" enforcement between the two primary runs. Both are required to exit 0 on the same target list, including cost + disclosure examples.)

**Evidence**:
- Section heading, table strings (Taplo, toml-test, forbid/unsafe-free, cross-check), and rationale paragraph are all present.
- However, two concrete claims in the table rows added by this restructure do not match on-disk bytes:
  - "cost" coverage attributed to the primary validators (README.md:142) — no supporting code paths.
  - "CI requires bytewise agreement" (README.md:143) — CI runs both but performs no output comparison.
- These are new factual inaccuracies about shipped surfaces and CI behavior introduced in the "Validation tooling" section whose addition is the C05 correction.

C05 is a **partial** closure: the structural addition and rationale text are present, but the accuracy of the authoritative-surface description is not.

### C06 (Status table: add Cost Profile + Disclosure Profile rows at 1.0.0)

**Classification: closed**

**Verbatim recipe execution:**

```
$ grep -A2 -E 'Cost Profile schema|Disclosure Profile schema' README.md
| Cost Profile schema | `1.0.0` | Release candidate |
| Disclosure Profile schema | `1.0.0` | Release candidate |
```

```
$ cat profiles/cost/PROFILE.toml | grep schema_version
schema_version    = "1.0.0"
schema_version    = { ijb_primitive = "constraint", ijb_constraint_type = "structural" }

$ cat profiles/disclosure/PROFILE.toml | grep schema_version
schema_version    = "1.0.0"
schema_version    = { ijb_primitive = "constraint", ijb_constraint_type = "structural" }
```

(The first line in each is the scalar `schema_version = "1.0.0"`; the second is the expected IJB-annotated duplicate key per ontology format.)

**Evidence**: Both new rows present in Status table (README.md:39-40). Both PROFILE.toml files contain the claimed scalar at schema_version. Matches verification_report.toml:124-131 exactly.

**closed**

### C07 (Governance: surface multi-LLM review requirement at tools/review-request-dag.toml)

**Classification: closed**

**Verbatim recipe execution:**

```
$ grep -n 'review-request-dag.toml' README.md
216:multi-LLM review under [tools/review-request-dag.toml](tools/review-request-dag.toml)
```

(Occurs inside the Governance section at README.md:210-218.)

```
$ cat tools/review-request-dag.toml | head -20
# Reusable multi-reviewer independent-review workflow, encoded as a
# DAG-TOML `implementation-dag`. Author: Werner Kasselman.
#
# PURPOSE
# ...
# [policy] table carries the hard process rules...
```

The file is real, non-empty, and contains the [policy.*] tables (roles, evidence, approval, etc.) that encode the multi-LLM requirement for spec/core/profile/validator changes.

**Evidence**: Explicit pointer added in Governance paragraph. File exists at the cited path and its policy content matches the README's characterisation. Matches verification_report.toml:137-142.

**closed**

---

## 3. Out-of-scope findings

Per [out_of_scope] in verification_report.toml lines 149-158, the following were **not** treated as blockers (and no findings were filed against them):
- SPEC.md content itself (including existence or wording of §12/§13).
- Profile contents (agent-assurance, cost, disclosure) or their kind descriptors.
- Validator source code correctness or implementation details (except where the README makes explicit public claims about their surfaces/CI behavior — those claims were inspected under C04/C05).
- Example DAG-TOML instances.
- CHANGELOG.md (untouched by this commit).
- The schema_version=1.0.0 pin policy (CLAUDE.md + SPEC §8 decision).
- The decision to use calendar-UTC tags (policy set at the v2026-05-25T03-30-02Z release commit).

No out-of-scope items were misclassified as blockers.

---

## 4. Final blockers

**One concrete, high-severity blocker (unresolvable within this commit's scope):**

The Local Validation block added by the restructure (README.md:155-181) contains the line at README.md:180:
```
python3 validators/validate_abstraction_class.py --discover .    # SPEC §13
```
When this exact command string is copied from the reviewed artifact and executed against the repository state at the same commit b759eaf, it produces:
```
validate_abstraction_class.py: error: unrecognized arguments: --discover
```
The script (validators/validate_abstraction_class.py) accepts only positional `paths` (plus optional --repo-root); --discover is not implemented (contrast with the immediately preceding `validate_closure_root.py --discover .` line in the same block, which does support it, and with the actual CI invocation at .github/workflows/validate.yml:217 which passes explicit kind-descriptor globs such as `core/*-kind.toml`).

This is a concrete falsehood in the primary copy-paste validation workflow presented to new readers. It directly contradicts the C04 correction goal ("New README Local Validation block ships the full developer workflow") and the bundle U05 requirement that "every cited validator script MUST exist; every cited ... command ... must resolve" and that "an unresolvable reference is a finding (severity high — the reader's first experience would be a 'no such file' error, damaging trust...)".

Secondary supporting blocker (same sections): README.md:142 claims the Rust primary is "Authoritative for profile-descriptor, disclosure, cost, ..."; README.md:143 claims "CI requires bytewise agreement" between the two primaries. Neither claim matches the inspected bytes (no "cost" handling in either primary main; CI runs both sequentially on shared targets with only independent success checks and no output comparison).

These defects cannot be resolved without editing README.md — the only file changed in b759eaf.

---

## 5. Terminal verdict

Terminal verdict: concrete_unresolvable_blocker
Blocker: README.md:179-180 documents `python3 validators/validate_abstraction_class.py --discover .` (and the surrounding Local Validation workflow) for SPEC §13; the exact command (reproduced at b759eaf) fails with "unrecognized arguments: --discover" because the script accepts only positional paths (validators/validate_abstraction_class.py argparse + .github/workflows/validate.yml:217 uses globs). The Validation tooling table at README.md:142-143 further claims "cost" coverage by primaries (no supporting code) and "CI requires bytewise agreement" (CI runs both but performs no comparison). These are concrete mismatches between the documented surfaces/workflow and actual bytes at the commit under review; unresolvable in a docs-only change.

---

**Persisted review evidence**: This file written verbatim to `docs/reviews/2026-05-25-readme-restructure/raw_findings/grok.md` per policy.persistence and review_bundle.toml output requirements. All required bases satisfied.
