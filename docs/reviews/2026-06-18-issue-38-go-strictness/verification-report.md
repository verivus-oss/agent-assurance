# Verification report — close C01 Go/BurntSushi toml-test strictness gap (issue #38)

**Date:** 2026-06-18
**Branch:** `fix/issue-38-go-strictness` (base `main` @ `f2fe440`)
**Reviewers must verify against the code + the toml-test oracle, not this prose.**

## 1. Problem
`github.com/BurntSushi/toml` v1.6.0 (the Go primary parser) ACCEPTS 13 invalid
`toml-test` 1.1 fixtures — all dotted-key / inline-table redefinition — that the
Rust (`toml` 1.1) and Python (`tomli`) primaries REJECT. Contract **C01** wants
parity ("block, not skip"). The 13 were tolerated via `Makefile`
`TOML_CONFORMANCE_SKIPS` and recorded in
`conformance/known-divergences-toml-1.1.toml` `[[toml_test_go_permissiveness]]`.

## 2. Design — `pelletier/go-toml/v2` as a strict gate in front of BurntSushi
Empirically, `pelletier/go-toml/v2` **v2.4.0** rejects all 13 invalid fixtures and
accepts the full 189-case TOML 1.1 valid corpus (pure Go, imports `unsafe` 0
times). It is added as a strict **pre-parse gate**, not a replacement for
BurntSushi's structural decode, in the two places that share the Go parser stance:

- **Primary validator** `tools/dagtoml-validate-go/main.go` (`loadDoc`):
  `pelletier.Unmarshal` runs first; on error the document is REJECTED
  (`TOML parse failed (strict): …`) and never reaches BurntSushi. BurntSushi still
  performs the structural decode the rest of the validator relies on (typed
  array/datetime shapes via `asArray`/`int64Of`).
- **toml-test decoder shim** `tools/toml-test-decode-go/` (new module, mirrors
  `tools/toml-test-decode-rs/`): pelletier strict gate (exit 1 on parse error,
  which toml-test reads as "rejected"), then BurntSushi tagged-JSON emit so the
  valid-corpus output is byte-identical to the stock BurntSushi decoder.

**Version note (judgment call):** pelletier **v2.3.1** lacks TOML 1.1 support and
rejects 3 valid fixtures (`datetime/no-seconds`, `inline-table/newline`,
`string/hex-escape`); **v2.4.0** added 1.1 and passes all 189. v2.4.0 is used.

## 3. The change
- `tools/dagtoml-validate-go/{main.go,go.mod,go.sum}` — pelletier gate + dep.
- `tools/toml-test-decode-go/{main.go,go.mod,go.sum}` — new shim (binary gitignored).
- `Makefile` — `toml-conformance` builds+uses the new shim; `TOML_CONFORMANCE_SKIPS`
  emptied; install target no longer fetches the stock BurntSushi decoder.
- `conformance/known-divergences-toml-1.1.toml` — 13-entry list removed; prose
  records the gap is closed (zero skips).
- `.github/workflows/validate.yml` — the new module wired into the `govulncheck`
  loop and a new `golangci-lint` step (it was otherwise CI-unscanned).
- `.gitignore` — ignore the new shim binary.

## 4. Verification (all run; commands reproducible in the worktree)
- **toml-test oracle, ZERO skips, new Go shim:**
  `~/go/bin/toml-test -toml 1.1.0 <shim>` → `valid tests: 189 passed, 0 failed` /
  `invalid tests: 362 passed, 0 failed`. All 13 now rejected; zero skips.
- **`make toml-conformance`** passes with the emptied skip list (clean rebuild).
- **`make toml-conformance-rs`** still 189/362, zero skips.
- **`python3 conformance/runner.py`** — 21 cases, rs=go=py AGREE, CONFORMANCE PASSED.
- **`bash validators/check_safe_tools.sh`** exit 0 (recognises the new module as
  unsafe-free).
- **govulncheck v1.3.0** on `dagtoml-validate-go` and `toml-test-decode-go`:
  "Your code is affected by 0 vulnerabilities."
- **golangci-lint v2 (repo `.golangci.yml`)** on both modules: `0 issues`.
- **`go vet ./...` + `gofmt -l`** clean in both modules.
- **Primary validator:** rejects `a.b = 1` + `[a.b]`
  (`TOML parse failed (strict): toml: key b should be a table, not a value`); still
  accepts every canonical doc (full CI sweep + all 200 tracked valid `.toml`).

## 5. Out of scope
This change does not alter BurntSushi's structural decode or any validator
semantics beyond rejecting the 13 malformed patterns earlier; valid documents are
unaffected.
