# Independent Review: TOML Conformance Harness (2026-05-25) — Grok

**Reviewer:** grok (fresh-context, independent session)  
**Commit under review:** `afe354c` (parent: `8cc1110`; range: `8cc1110..afe354c`)  
**Review bundle:** `docs/reviews/2026-05-25-toml-conformance-harness/review_bundle.toml`  
**Policy followed:** `tools/review-request-dag.toml` [policy.*] (forbidden bases: stated_intent, plan_compliance_claim, should_be_fixed_language; required bases: inspected_code, executed_tests_with_output, inspected_docs, persisted_review_evidence; terminal states: unconditional_approval | concrete_unresolvable_blocker)

I performed this review with no prior context on the change beyond the canonical bundle and prompt on disk. All verification is against bytes (git objects, filesystem reads, live command execution).

## Commands Executed

Reproduced exactly as required:

```bash
make toml-conformance-install && make toml-conformance
```

**Verbatim output:**

```
GOBIN=/home/werner/go/bin go install github.com/toml-lang/toml-test/cmd/toml-test@v1.6.0
GOBIN=/home/werner/go/bin go install github.com/BurntSushi/toml/cmd/toml-test-decoder@v1.4.0
/home/werner/go/bin/toml-test -skip invalid/array/extend-defined-aot -skip invalid/inline-table/duplicate-key-3 -skip invalid/inline-table/overwrite-02 -skip invalid/inline-table/overwrite-08 -skip invalid/spec/inline-table-2-0 -skip invalid/spec/table-9-1 -skip invalid/table/append-to-array-with-dotted-keys -skip invalid/table/append-with-dotted-keys-1 -skip invalid/table/append-with-dotted-keys-2 -skip invalid/table/duplicate-key-dotted-table -skip invalid/table/duplicate-key-dotted-table2 -skip invalid/table/redefine-2 -skip invalid/table/redefine-3 /home/werner/go/bin/toml-test-decoder
toml-test v0001-01-01 [/home/werner/go/bin/toml-test-decoder]: using embedded tests, 13 skipped
  valid tests: 185 passed,  0 failed
invalid tests: 358 passed,  0 failed
```

Exit status of the combined make invocation: 0 (clean pass under the documented skiplist).

To verify U02 skiplist honesty, I also executed the raw suite (no skips) and captured exit code:

```bash
/home/werner/go/bin/toml-test /home/werner/go/bin/toml-test-decoder
```

**Verbatim tail of raw output + exit code:**

```
... (13 FAIL blocks for the exact names listed below) ...

toml-test v0001-01-01 [/home/werner/go/bin/toml-test-decoder]: using embedded tests
  valid tests: 185 passed,  0 failed
invalid tests: 358 passed, 13 failed
```

```
EXIT_CODE=1
```

(The `toml-test` binary exits 1 on any unskipped failure, so `set -e` in CI will correctly fail the step.)

Additional inspection commands (for cross-checks):
- `git rev-parse HEAD` → afe354c27327d845a6ea88beb876d3ab953527be
- `git diff 8cc1110..afe354c --name-only`
- `git show afe354c:Makefile`
- `git show 8cc1110:tools/dagtoml-validate-go/go.mod`
- `git diff 8cc1110..afe354c -- .github/workflows/validate.yml`
- `git diff 8cc1110..afe354c -- CHANGELOG.md`
- Multiple `read_file` + `grep` for exact line-level confirmation on Makefile, .github/workflows/validate.yml, CHANGELOG.md, tools/dagtoml-validate-go/go.mod, and cross-repo search for "toml-conformance" (only appears in the three changed files + this review session's docs).

## Unit Classification (U01–U05)

All classifications below are derived strictly from inspected bytes + executed test output (no reliance on bundle summaries or stated intent).

**U01 (version-pinning-binds-conformance-to-validator-parser): complete**

- **Classification:** complete
- **Evidence (inspected_code, executed_tests_with_output):**  
  `Makefile:22` declares `TOML_TEST_DECODER_VERSION := v1.4.0`.  
  `tools/dagtoml-validate-go/go.mod:5` (unchanged by this commit) requires `github.com/BurntSushi/toml v1.4.0`.  
  The major.minor.patch strings match exactly. The Makefile comment block at `Makefile:18-21` explicitly records the binding rationale in the shipped bytes. The `make toml-conformance-install` run I executed used precisely this pinned decoder and produced a clean result consistent with the claim.  
- **Severity:** none (no finding)

**U02 (skiplist-baseline-is-honest): complete**

- **Classification:** complete
- **Evidence (executed_tests_with_output, inspected_code):**  
  `Makefile:36-49` contains exactly these 13 entries (the TOML_CONFORMANCE_SKIPS list):  
  invalid/array/extend-defined-aot, invalid/inline-table/duplicate-key-3, invalid/inline-table/overwrite-02, invalid/inline-table/overwrite-08, invalid/spec/inline-table-2-0, invalid/spec/table-9-1, invalid/table/append-to-array-with-dotted-keys, invalid/table/append-with-dotted-keys-1, invalid/table/append-with-dotted-keys-2, invalid/table/duplicate-key-dotted-table, invalid/table/duplicate-key-dotted-table2, invalid/table/redefine-2, invalid/table/redefine-3.  
  The raw execution (no -skip flags) produced failures for *precisely* these 13 names and no others; `make toml-conformance` (with skips) produced "0 failed, 13 skipped" and exit 0.  
  The rationale comment immediately above the list (`Makefile:24-35`) states in bytes: these are "edge cases around dotted-key / inline-table redefinition and TOML 1.1-spec-tightening fixtures", "a baseline of *currently-known-tolerated-permissiveness*, NOT a green light", and "each entry should be revisited when bumping TOML_TEST_DECODER_VERSION". This matches the required honesty contract exactly.  
- **Severity:** none (no finding)

**U03 (ci-step-is-mandatory-not-soft): complete**

- **Classification:** complete
- **Evidence (inspected_code):**  
  `.github/workflows/validate.yml:79-82` (the added step "TOML 1.0 spec conformance...") contains:  
  ```
          run: |
            set -e
            make toml-conformance-install
            make toml-conformance
  ```  
  The job definition (`.github/workflows/validate.yml:10-12`) has no job-level `continue-on-error`. No `continue-on-error: true` appears on this step. The preceding Taplo step and subsequent steps use the same `set -e` pattern; exit codes propagate. The `make toml-conformance` target itself fails (non-zero) when unskipped failures exist, as confirmed by my direct execution (EXIT_CODE=1 on raw run).  
- **Severity:** none (no finding)

**U04 (no-spec-or-validator-byte-changed): complete**

- **Classification:** complete
- **Evidence (inspected_code):**  
  Executed `git diff 8cc1110..afe354c --name-only` (verbatim):  
  ```
  .github/workflows/validate.yml
  CHANGELOG.md
  Makefile
  ```  
  Exactly the three files declared in `review_bundle.toml:55-59`. No paths under `SPEC.md`, `core/`, `profiles/`, `validators/`, `examples/`, `foundations/`, or any `*-kind.toml` / ontology file appear. I additionally grepped the entire working tree for "toml-conformance" (post-checkout at afe354c); only the three changed files plus review-session documentation contain the string.  
- **Severity:** none (no finding)

**U05 (changelog-and-followup-honest): complete**

- **Classification:** complete
- **Evidence (inspected_docs):**  
  `CHANGELOG.md:12-31` (the top entry under `## [Unreleased]` / `### Added`) states in full:  
  - Lives under `[Unreleased]`.  
  - Explicitly names the load-bearing claim: "The decoder is shipped by the same `BurntSushi/toml v1.4.0` module that `tools/dagtoml-validate-go` depends on, so a green run is evidence about the parser the Go validator actually uses at runtime — not just about some unrelated TOML library."  
  - States the Rust gap honestly as follow-up, not done: "Follow-up: a Rust decoder shim against the `toml` 0.8 crate used by `tools/dagtoml-validate-rs` would extend the same evidence path to the Rust validator's parser."  
  The entry also correctly reports the observed counts (185/185 valid, 358/358 invalid + 13 skips) and the skiplist discipline. No overclaim.  
- **Severity:** none (no finding)

## Cross-Cutting Process Confirmations

- All claimed tests were actually executed in this session with captured stdout + explicit exit codes (see "Commands Executed" above).  
- No historical dated SPEC material was modified by this commit (U04 confirms zero bytes outside the three tooling files).  
- Review evidence is persisted verbatim at the path specified by the bundle (this file).  
- sqry semantic search was attempted via MCP discovery for symbol-level confirmation of Makefile targets and workflow steps; fell back to `grep` (system ripgrep) + `git show` + `read_file` + direct execution for exact-string and line-number fidelity on this tiny, non-code change. All required bases (inspected_code, executed_tests_with_output, inspected_docs, persisted_review_evidence) are satisfied for every unit.

## Summary of Findings

Zero findings at any severity. All five units are complete against the bytes and live execution. The harness correctly pins the decoder to the exact module version used by the Go validator, the skiplist is an accurate and honestly documented baseline, the CI step is hard-failing, scope is exactly as described, and the changelog entry is precise.

Terminal verdict: unconditional_approval
