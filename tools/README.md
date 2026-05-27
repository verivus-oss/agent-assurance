# tools/

Native tooling that produces and verifies the artifacts under
`reference/database/`. Anything spec-critical lives here.

## Language hierarchy (CI-enforced)

This repo has an explicit ordering of acceptable implementation
languages for spec-critical tooling. The order is **not** a matter of
taste — CI runs the higher tiers first and treats divergence as a
build break.

### Tier 1 — default: safe Rust **or** Go

New tooling MUST be written in one of these two languages. Both are
required to be **memory-safe by construction at the level of the code
we write**:

- **Rust** crates MUST declare `#![forbid(unsafe_code)]` at the top of
  `src/main.rs` or `src/lib.rs`. The compiler refuses to build any
  `unsafe { ... }` block inside the crate. Dependencies may use `unsafe`
  internally; that is out of scope for this rule. MSRV is pinned in
  each `Cargo.toml` (`rust-version = "1.85"`); CI tracks current
  stable, which MUST be >= MSRV.
- **Go** modules MUST NOT contain any `.go` file that imports
  `"unsafe"`. The `go.mod` declares `go 1.26` (latest stable at the
  time this policy was written); CI's `actions/setup-go@v5` is set to
  `go-version: "stable"` so the runner tracks Go's release cadence
  automatically.

Both are enforced by `validators/check_safe_tools.sh`, which runs in
`.github/workflows/validate.yml` right after the manifest-drift step.

The choice between Rust and Go is judgment-call:

| Concern                                    | Prefer Rust              | Prefer Go             |
|--------------------------------------------|--------------------------|-----------------------|
| Parser-heavy logic, RDF/Turtle, SHACL      | yes                      |                       |
| Subprocess orchestration / CLI wrapping    |                          | yes                   |
| Single-binary distribution                 | yes (with LTO+strip)     | yes                   |
| Quick rewrite by a non-Rust reviewer       |                          | yes                   |
| Compile time matters more than runtime     |                          | yes                   |

When unsure, ship both. The two reference tools (`dagtoml-rdf` and
`dagtoml-duckdb`) have Go counterparts at `*-go/`; CI exercises both
and fails on functional divergence.

### Tier 2 — supported: Java, TypeScript, Python

Tooling in these languages is **accepted** but never **required**. They
exist for three legitimate reasons:

1. **Bridging existing ecosystems** (e.g., a TypeScript validator for
   editor extensions that already run TypeScript; a Java client for
   teams whose CI is Maven/Gradle-bound).
2. **Cross-check / fallback**: a second implementation in a different
   language is the cheapest insurance against a primary-language bug.
   The Python validators under `validators/` are first-class
   cross-checks for the primary Rust/Go validators — CI runs both, and
   a difference between primary and secondary fails the build.
3. **Prototype / one-shot scripts**: things you'd otherwise write as a
   notebook. These do not belong in `tools/`; they belong in
   `validators/` (Python only) or in a contributor's own working tree.

For new CI-enforced spec invariants, the corresponding Tier-1 tool
MUST exist before the invariant is treated as fully supported. Tier-2
may add coverage but never replace Tier-1 coverage for new work.

Legacy Python validators that predate this policy are allowed to keep
running in CI only when the gap is documented in README.md's
validation-tooling table as a Tier-1 migration backlog. Those surfaces
remain enforceable, but they are not described as primary until the
safe Rust and Go validators implement the same invariant and CI runs
both implementations against the same positive/negative evidence.

### Tier 0 — forbidden defaults

- **Bash / shell** for any logic beyond ~100 lines or any computation
  more involved than `grep`/`awk`/`find`/`wc` orchestration. The
  drift script (`validators/check_manifest_drift.sh`) and the
  safe-tools script (`validators/check_safe_tools.sh`) sit at exactly
  this threshold and intentionally do nothing more.
- **Python with a runtime dependency** for new spec-critical tools.
  Python is acceptable for Tier-2 cross-checks using only the stdlib
  (`tomllib`, `pathlib`, etc.) and the small allowed set in
  `requirements.txt`.
- **C, C++, anything FFI-heavy**, unless an existence proof shows that
  Rust or Go cannot reach the required performance. Has not happened
  yet and the bar is high.

## Safety policy (CI-enforced)

`validators/check_safe_tools.sh` runs in CI and fails the build on
any violation in tools/.

## Standard slopscan

Every review of executable code or dependency manifests should include
a slopscan: a focused pass for AI-generated-code failure modes, not a
general style critique. Treat the following as the standing checklist
for Go, Python, Rust, and dependency manifests.

### Dependency hallucination and slopsquatting

AI coding assistants can suggest plausible package names that do not
exist. Attackers can then register those names, or close variants, and
turn the suggestion into a supply-chain compromise. For every changed
manifest or lockfile, check:

- package exists in the real registry for its ecosystem;
- package is not brand new without a documented reason;
- name is not a typo, homoglyph, case variant, scope/org squat,
  ecosystem-confused form, or version-suffix form of a known package;
- package has an expected source repository, maintainer history, and
  adoption profile for its role;
- lockfile or checksum file is present where the ecosystem supports
  one (`Cargo.lock`, `go.sum`, pinned/hash-locked Python inputs);
- no unexplained local path, fork, `replace`, alternate index, or
  unauthenticated mirror weakens registry verification.

Prefer standard-library or already-approved dependencies over new
packages for small tasks. New dependencies need a short justification
in the change under review.

### Python slopscan

Run `python3 -m compileall -q validators` for validator changes. When
Python code grows beyond small stdlib validators, add `ruff` and
`bandit` coverage before relying on it in CI.

Flag and either remove or justify:

- `eval`, `exec`, `compile`, or attempts to make them "safe" by
  overriding `__builtins__`;
- `pickle`, `marshal`, `shelve`, or model-artifact deserialization on
  untrusted input;
- `subprocess` with `shell=True`, `os.system`, or string-built shell
  commands;
- broad `except Exception: pass` without a comment proving the failure
  is optional and already reported elsewhere;
- `tempfile.mktemp`, unsafe archive extraction, unsafe XML parsing,
  `random` for secrets, unverified TLS, or logging of secrets/PII.

### Go slopscan

Run `go vet ./...` in every changed Go module. For service or
concurrent code, also run the race detector in the relevant test
command. Reviewers should flag:

- ignored errors, ignored `Close`/`CancelFunc` results where cleanup is
  required, or `context.WithCancel` without a matching cancel path;
- goroutine loop-variable capture, `copylocks`, `unsafe` imports,
  `InsecureSkipVerify`, or HTTP clients without timeouts in networked
  code;
- `exec.Command("sh", "-c", ...)` or string-built command lines;
- unexplained `panic`, `log.Fatal`, or process exit inside library
  code;
- stale `go.mod`/`go.sum`, unexplained `replace`, or unreviewed new
  transitive dependencies.

### Rust slopscan

Run `cargo fmt --check`, `cargo clippy --locked -- -D warnings`, and
`cargo audit` in every changed Rust crate. Reviewers should flag:

- executable code using `unsafe`, or unsafe public API without a
  precise safety contract;
- production `unwrap`, `expect`, `panic!`, `todo!`, `unimplemented!`,
  or `dbg!` outside tests or one-shot binaries where failure is
  intentionally fatal;
- broad `#[allow(...)]` or lint-level weakening without a local reason;
- shell-mediated command execution, permissive file modes, unchecked
  path handling, or unchecked deserialization;
- missing `Cargo.lock` for binaries or unexplained new dependencies.

### Rust

Every Rust crate under `tools/` MUST declare:

```rust
#![forbid(unsafe_code)]
```

near the top of its `src/main.rs` or `src/lib.rs`. This is a
compiler-level lint — the build itself fails if any code inside the
crate reaches for `unsafe { ... }` or `unsafe fn`. The check script
also greps `src/**.rs` for stray `unsafe` blocks as a belt-and-braces
catch.

Dependencies (serde, oxttl, BurntSushi/toml, pelletier/go-toml/v2,
etc.) may use `unsafe` internally; auditing them is out of scope for
this policy. Use `cargo-geiger` or `govulncheck` if you want deeper
coverage of the dependency tree.

### Go

No `.go` file under `tools/` may `import "unsafe"`. The check script
greps for any of:

- `import "unsafe"`
- `import _ "unsafe"`
- `"unsafe"` inside an `import (...)` group

Dependencies' internal use of `unsafe` is out of scope.

## Toolchain versions

| Language    | CI version          | Pinned in              | Rationale                                                |
|-------------|---------------------|------------------------|----------------------------------------------------------|
| Rust        | `stable` (current)  | `Cargo.toml` rust-version = 1.85 (MSRV floor) | Tracks the language; MSRV documents the floor that consumers can rely on. |
| Go          | `stable` (current)  | `go.mod` `go 1.26`     | Same — track the language, document the floor each module assumes. |
| Python      | 3.11                | `.github/workflows/validate.yml` | Cross-check only; not the primary path. |
| Bash        | system (4.x+)       | n/a                    | Used only for the smallest invariant scripts.            |

Bumping a primary toolchain (Rust or Go) is allowed and expected as
upstream releases land. The change is: bump `go.mod` / `Cargo.toml`
in the same PR, run all the checks locally, note in CHANGELOG that
the floor moved.

## Current tools

| Tool                        | Lang  | Purpose                                                                 |
| --------------------------- | ----- | ----------------------------------------------------------------------- |
| `dagtoml-rdf/`              | Rust  | Generate `reference/database/rdf/schema.ttl` from the ontology.         |
| `dagtoml-rdf-go/`           | Go    | Same as `dagtoml-rdf`, in Go. Functional output verified equivalent.    |
| `dagtoml-duckdb/`           | Rust  | Build `agent_assurance.duckdb` from `duckdb/{schema,seed}.sql`.         |
| `dagtoml-duckdb-go/`        | Go    | Same as `dagtoml-duckdb`, in Go.                                        |
| `dagtoml-validate-rs/`      | Rust  | Primary validator for profile descriptors + disclosure profile + SPEC §2.2/2.5-2.7, §11.1, §12.8 source-hash closure roots, and selected profile invariants. |
| `dagtoml-validate-go/`      | Go    | Same as `dagtoml-validate-rs`, in Go.                                   |

The Rust and Go counterparts produce equivalent functional outputs; CI
exercises both. If they diverge (modulo header comments and
implementation-detail formatting), the build fails.

## Adding a new tool

1. Pick Rust or Go (Tier 1). Adding a Java/TS/Python equivalent is
   optional and only acceptable as a cross-check.
2. Add the safety marker (`#![forbid(unsafe_code)]` in Rust, or
   keep `"unsafe"` out of every `.go` file). The CI check refuses to
   let you skip it.
3. Place the tool at `tools/<name>/` (Rust) or `tools/<name>-go/` (Go).
   Mirror the naming if you ship both.
4. Add a row to the **Current tools** table above.
5. Pin toolchain versions in `Cargo.toml` (`rust-version`) or `go.mod`
   (`go x.y`) at a value that is `<=` what CI currently tracks.
6. Wire the tool's runtime invocation into
   `.github/workflows/validate.yml` if it produces a CI-checked
   artifact. If it produces a checked-in artifact (like the .ttl),
   add a drift check that catches stale output.
