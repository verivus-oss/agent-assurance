# Independent Review: TOML Conformance Harness (2026-05-25)

**Commit under review:** `afe354c`
**Parent commit:** `8cc1110`

I have independently verified the `toml-test` conformance harness change according to the review constraints and the policy defined in `tools/review-request-dag.toml`.

## Execution of Tests
I executed the following commands to verify the conformance tests locally:
```bash
make toml-conformance-install
make toml-conformance
```

**Output:**
```
GOBIN=/home/werner/go/bin go install github.com/toml-lang/toml-test/cmd/toml-test@v1.6.0
GOBIN=/home/werner/go/bin go install github.com/BurntSushi/toml/cmd/toml-test-decoder@v1.4.0
/home/werner/go/bin/toml-test -skip invalid/array/extend-defined-aot -skip invalid/inline-table/duplicate-key-3 -skip invalid/inline-table/overwrite-02 -skip invalid/inline-table/overwrite-08 -skip invalid/spec/inline-table-2-0 -skip invalid/spec/table-9-1 -skip invalid/table/append-to-array-with-dotted-keys -skip invalid/table/append-with-dotted-keys-1 -skip invalid/table/append-with-dotted-keys-2 -skip invalid/table/duplicate-key-dotted-table -skip invalid/table/duplicate-key-dotted-table2 -skip invalid/table/redefine-2 -skip invalid/table/redefine-3 /home/werner/go/bin/toml-test-decoder
toml-test v0001-01-01 [/home/werner/go/bin/toml-test-decoder]: using embedded tests, 13 skipped
  valid tests: 185 passed,  0 failed
invalid tests: 358 passed,  0 failed
```

## Unit Classification

**U01 (version-pinning-binds-conformance-to-validator-parser):**
*   **Result:** Pass (inspected_code)
*   **Evidence:** `Makefile:20` declares `TOML_TEST_DECODER_VERSION := v1.4.0`. `tools/dagtoml-validate-go/go.mod:5` requires `github.com/BurntSushi/toml v1.4.0`. The version strings match exactly. Severity: none (passed).

**U02 (skiplist-baseline-is-honest):**
*   **Result:** Pass (executed_tests_with_output, inspected_code)
*   **Evidence:** The 13 invalid-test skips listed in `Makefile:38-51` match the set of 13 failures present when executing `toml-test` without skips. The 13 skipped entries properly mask all failures such that the `make toml-conformance` step succeeds with "0 failed, 13 skipped". `Makefile:30-36` correctly states the rationale, declaring these as "currently-known-tolerated-permissiveness" and requiring revisitation on a bump. Severity: none (passed).

**U03 (ci-step-is-mandatory-not-soft):**
*   **Result:** Pass (inspected_code)
*   **Evidence:** `.github/workflows/validate.yml:79-82` configures the run with `set -e` followed by the two `make` commands. It does not use `continue-on-error`, meaning the shell exit code propagates and breaks the CI step properly if conformance fails. Severity: none (passed).

**U04 (no-spec-or-validator-byte-changed):**
*   **Result:** Pass (inspected_code)
*   **Evidence:** Diffing `8cc1110..afe354c` via `git diff --name-only` yields exactly `.github/workflows/validate.yml`, `CHANGELOG.md`, and `Makefile`. No other files (including SPEC, validator, or instance bytes) were modified. Severity: none (passed).

**U05 (changelog-and-followup-honest):**
*   **Result:** Pass (inspected_docs)
*   **Evidence:** `CHANGELOG.md:12-32` states clearly under `## [Unreleased]` that the module tested is the same as the one used by `tools/dagtoml-validate-go`, and accurately states: "Follow-up: a Rust decoder shim against the `toml` 0.8 crate used by `tools/dagtoml-validate-rs` would extend the same evidence path to the Rust validator's parser." Severity: none (passed).

Terminal verdict: unconditional_approval