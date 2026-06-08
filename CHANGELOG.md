# Changelog

All notable changes to the DAG-TOML specification and the Agent
Assurance Profile will be documented here.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- **Static specification site.** Added the Cloudflare Pages static site
  under `site/`, including human-readable pages, Markdown mirrors,
  agent discovery metadata, a deploy workflow, favicon assets, and the
  social share image used by Open Graph and Twitter cards.
- **OSS readiness sweep.** Added public-repository metadata and ownership
  files, ignored local paper/research scratch files, added an OpenSSF
  Scorecard workflow and README badge, pinned CI to GitHub-hosted
  `ubuntu-24.04` runners with Harden-Runner audit telemetry, documented
  the non-normative status of historical review/research directories, and
  corrected public-status and release-policy wording after the `v0.1.0`
  mint.
- **CodeQL advanced-setup workflow.** Added
  [`.github/workflows/codeql.yml`](.github/workflows/codeql.yml) scanning
  `actions`, `go`, `python`, and `rust` with build-mode `none` on every
  push, every pull request, and weekly. GitHub's default-setup REST API
  does not currently accept `rust` as a language value (verified by a
  live `PATCH` probe that returned
  `Invalid property /languages/3: 'rust' is not a possible value`),
  which would have left roughly one third of this repository's source
  unscanned. Advanced-setup restores Rust coverage. All actions are
  SHA-pinned to the same versions used elsewhere in the workflow
  directory.
- **Archived multi-LLM review session (#26).** Added the non-normative
  process records under
  `docs/reviews/2026-05-27-agentskills-profile-pitch/` for an outbound
  pitch that was reviewed, approved, and then withdrawn unpublished;
  retained for traceability per the `docs/reviews/` convention.

### Changed

- **Implementation-dag placeholder parity in primary validators (#27).**
  Wired the unresolved-placeholder check (`<…>` markers in
  `files_create`/`files_modify`) into the Rust and Go implementation-dag
  paths, matching the Python reference, and removed the corresponding
  `conformance/known-divergences.toml` entry. The Go predicate uses an
  implementation-dag-specific marker set (`<`, `>` only) distinct from
  the broader kind-descriptor set; a `date-literal-path.toml` fixture
  pins the split. Conformance 21/21 across rs/go/py.
- **Dependency bumps.** `toml` 0.9→1.1.2+spec-1.1.0 in `tools/dagtoml-rdf`
  (#1); `github.com/BurntSushi/toml` 1.4→1.6 in `tools/dagtoml-validate-go`
  (#5); the GitHub Actions workflow dependency group (4 updates, #20).
- **Primary validator coverage promoted to Rust + Go.** Ported the
  remaining CI-enforced semantic surfaces from Python-only reference
  checks into both primary validators: implementation-dag,
  traceability, review-readiness, kind-descriptor structure, IJB
  conformance, `[provenance]` source binding, cost-record,
  rollback-plan trigger-kind closure, and SPEC §13
  abstraction/capability-envelope checks. CI now runs Rust and Go over
  ontologies, every kind descriptor, every canonical example, every
  tier file, and every profile descriptor, and includes negative
  fixtures proving Rust, Go, and Python all reject malformed files.
- **Root scratch artifacts moved local-only.** Verified the loose paper
  scratch files (`all_links.txt`, `bib_keys.txt`, `cited_keys.txt`,
  `labels.txt`, `find_matches.py`, `find_matches_v2.py`) are untracked
  and unused by CI, Makefile, docs, examples, or tools; moved the local
  copies under `.local/scratch/`. Existing root-only `.gitignore` rules
  keep them from being accidentally committed.
- **Go validation toolchain updated to patched 1.26.4.** The CI Go
  setup pin and the two Go reference modules that declare a patch-level
  toolchain now agree on Go `1.26.4`, matching the OSV-reported fixed
  stdlib version.
- **`SECURITY.md` documents the full defensive posture.** Rewritten to
  describe secret scanning + push protection, Dependabot security
  updates, CodeQL advanced-setup over the four languages, the
  `main-branch-protection` ruleset, the `signing-approvers` team,
  sigstore-signed release tags (with the `gitsign verify` instruction),
  OpenSSF Scorecard publishing, and the thirteen OSS scanning tools in
  [`.github/workflows/validate.yml`](.github/workflows/validate.yml).
  The thirteen-tool section mirrors the `validate.yml` "Coverage map"
  comment block verbatim (same order, same one-line role descriptions),
  and names that comment block as the canonical source so future
  contributors know which file leads if they diverge again.
- **`CONTRIBUTING.md` references the canonical scanner inventory.** One
  paragraph appended under "Local Checks" pointing to `SECURITY.md` for
  the per-tool role descriptions and listing the thirteen-tool sequence
  in the same order as `validate.yml`.

## [v0.1.0] - 2026-05-27

### Added

- **Initial public draft release.** Minted the specification repository as
  a clean public tree with the DAG-TOML draft specification, core kind
  descriptors, spec-reserved profiles, examples, validators, governance
  docs, and CI configuration.

## Pre-Public Development History

The entries below were retained from the private development history as
traceability evidence. They may refer to paper workspaces, review bundles,
or preparation directories that now live outside this specification repo.

### Changed

- **Public stability label changed to Draft Specification.**
  spec.md, README.md, and GOVERNANCE.md now distinguish the document
  maturity label from the on-file `schema_version` compatibility pin.
  Release tags continue to use calendar-versioned UTC timestamps
  (`v<YYYY-MM-DD>T<HH-MM-SS>Z`) rather than draft maturity labels.
- **Draft version pins made coherent.** Live schema/spec pins now use
  `schema_version = "0.1.0"` while `ontology_version = 1` remains a
  monotonic positive integer vocabulary snapshot. Validators now enforce
  `schema_version` as a semver string and `ontology_version`, when
  present, as a positive integer.
- **Terminology rename across the live spec surface to
  `spec-reserved`.** The prior prose marker for spec-published
  profiles, kinds, and the validator-discovered conformance set
  is now written as `spec-reserved` throughout spec.md, the
  ADOPTION and CONTRIBUTING docs, the three
  spec-reserved profile-descriptor headers, the ontology files,
  the kind-descriptor descriptor, and the Python/Go/Rust
  validators. The rename aligns the prose form with the
  machine-readable `namespace = "spec.reserved"` field already
  present in every profile-descriptor, closing the
  prose↔machine-readable gap that the agent-notes no-drift rule
  warns against. Python identifier renames in
  `validators/validate_closure_root.py` use the underscore
  variant `ALWAYS_SPEC_RESERVED_KINDS` /
  `spec_reserved_kinds()` / `spec_reserved` parameters,
  preserving Python identifier syntax. Go and Rust validators
  had no broken identifiers (the prior term appeared only in
  string literals). Historical records (CHANGELOG history
  below, docs/reviews/, docs/issues/, docs/planning/,
  docs/research/) are deliberately left untouched so they
  continue to reflect the terminology in use at the time of
  writing. All validators pass: closure-root discovery,
  profile-descriptor validation, IJB conformance, every kind
  descriptor under `core/` and `profiles/*/`, and the canonical
  example suite.

### Fixed

- **SPEC §12.8 closure roots now bind declared provenance source
  hashes.** The Python reference validator and both primary validators
  now compute the canonical `[provenance].source_sha256` closure stream
  instead of accepting the empty sentinel for provenance-bearing
  documents. The convert-md-to-dag skill package now carries the
  computed closure root for its declared source artifact. README.md and
  tools/README.md also distinguish current Tier-1 validator coverage
  from the remaining legacy Python-only migration backlog.
- **spec.md §2.3 / §2.5 / §6 — cost profile enumeration drift.**
  The cost profile shipped under `profiles/cost/` with
  `namespace = "spec.reserved"` and full CI integration, but
  spec.md's authoritative enumerations still listed only
  `agent-assurance` and `disclosure`. §2.3's
  `template_kind` table now includes a `cost-record` row;
  §2.5's spec-reserved-values bullet list now includes `cost`;
  §6's prose now names all three spec-reserved profile
  directories and says "Each ships a profile-descriptor
  document" rather than "Both ship". The escape hatch at §2.5
  ("the authoritative enumeration is the `profile-descriptor`
  files at `profiles/<name>/PROFILE.toml`") and the validator
  code at `validators/validate_closure_root.py:140` were
  already correct; this change resolves the prose drift only.
  No behaviour change.

### Added

- **spec.md §14 / §15 — explicit security and privacy considerations.**
  The public specification now has dedicated sections stating the
  security boundary of DAG-TOML's declarative evidence model and the
  privacy risks created by inspectable provenance, disclosure,
  redaction, closure, and metadata fields. The change consolidates
  existing posture material from the security, disclosure,
  provenance, confidentiality, and threat-model surfaces into the spec
  itself. No file-shape or validator behaviour changes.
- **OSS security + quality scanning posture (13 tools wired into CI).**
  Free-OSS-tool stack that closes the gaps from running on a free-plan
  private GitHub org (no GHAS: no CodeQL, no secret scanning, no
  branch protection). Every step uses SHA-pinned actions or
  version-pinned binaries (with SHA256 verification for downloads) and
  is configured to fail the build on any finding.
  - **Workflow integrity:** `actionlint` (GHA workflow correctness),
    `zizmor` (GHA workflow security — impostor-commit, excessive
    permissions, credential persistence). The zizmor audit caught
    three real findings on the existing workflow which were also
    fixed in this commit: top-level + job-level `permissions: contents:
    read` blocks, and `persist-credentials: false` on the checkout
    step.
  - **Content correctness:** `shellcheck` (validator shell scripts +
    paper witness scripts), `typos` (source-code spellchecker; critical
    for spec repos where misspelled ontology predicates would be silent
    semantic errors).
  - **Python:** `ruff` (configured for `--select S,F` —
    flake8-bandit security + pyflakes correctness, line-length 120;
    bugbear/style rules deferred to a dedicated cleanup PR), `bandit`
    (already wired; kept for defense-in-depth — different AST passes
    than ruff).
  - **Dependency CVEs:** `osv-scanner` (lock-file CVE check across
    requirements.txt + Cargo.lock + go.sum).
  - **Secrets:** `gitleaks` v8.30.1 binary (SHA256 verified) — secret
    leak detection in working tree + commit history.
  - **Rust:** `cargo-audit` (RustSec advisory DB) + `cargo-deny`
    (license policy allowlist Apache/MIT/BSD/MPL only; deny GPL family;
    crates.io-only source allowlist; multiple-version + wildcard
    bans). Configuration at `deny.toml`.
  - **Go:** `govulncheck` (call-graph-aware vuln check) +
    `golangci-lint` v2.12.2 (gosec + staticcheck + errcheck + govet +
    ineffassign + unused). Configuration at `.golangci.yml`.
  - **Link rot:** `lychee` (URL liveness check across .md/.toml/.tex
    files; documentation links, paper citation URLs in references.bib,
    kind-descriptor `references = [...]` URLs). Configuration at
    `lychee.toml`.
- **Dependabot expanded to four ecosystems** (`github-actions`, `pip`,
  `cargo`, `gomod`) — was previously github-actions only. Weekly bump
  cadence with distinct PR-limit caps and commit-message prefixes per
  ecosystem. Dependabot automated security fixes also enabled via the
  GitHub API.
- **First-run shake-out of the scanning stack (8 fixup commits).**
  The initial CI push of the 13-tool stack surfaced 8 distinct
  findings or false-positive classes across runs `26406653986`
  through `26412405532`. Each fixup is one commit:
  - `e7430a7` — `_typos.toml`: exclude `docs/{reviews,research,
    claim_analysis}/`, `tools/werner-style-policy.toml`,
    `foundations/ijb/examples/0{6,7}-*`, `paper/user-prompts.md`;
    allowlist `COSE` (RFC 9052 acronym), `Synopsys` (vendor name),
    `vai` (Werner shorthand for Verifiable AI in §13 label),
    plus identifier-regex skipping for structured IJB example IDs.
  - `8b3c51f` — osv-scanner: drop `--skip-git` flag removed in v2.
  - `c6c91d9` — `tools/dagtoml-validate-go`: remove unused
    `arrayOfStrings` helper (golangci-lint `unused` linter).
  - `633f23e` — osv-scanner: add `--no-resolve` to skip the flaky
    upstream gRPC service that resolves transitive deps from
    `requirements.txt`. Lockfile-based scanning (Cargo.lock,
    go.sum) covers the rest; networkx pulls in no transitive deps
    that need resolution.
  - `31a37b0` — `tools/dagtoml-rdf-go`: errcheck on
    `os.Stdout.WriteString` (wrap in `if _, err := ...`); gosec
    G306 `0o644` WriteFile permissions annotated with `//nolint:gosec`
    + rationale (regenerated reference RDF schema is intended to be
    world-readable for downstream implementers).
  - `06fb1f2` — `lychee.toml`: remove `include = ["**/*.md", ...]`
    array. The `include` key takes URL-regex patterns, not file
    globs; lychee `v0.23.0` errored with "regex parse error ...
    repetition operator missing expression". File-extension scoping
    is handled by lychee's built-in extractor selection.
  - `182dd31` — `lychee.toml`: extend `exclude_path` with
    `docs/research/` + `docs/claim_analysis/`; extend `exclude`
    URL-regex list with placeholder/example domains
    (`*.yourdomain.com`, `config.kasselman.com.au`) and the
    `file://` scheme. Repo-internal file-existence is checked by
    the path-existence validators under `validators/`, not by
    lychee.
  - `34eb281` — `lychee.toml`: exclude `www.fco-im.nl`. The
    academic-paper host cited from
    `foundations/ijb/fco-im-integration-options.md` times out from
    GitHub Actions runners; the FCO-IM papers themselves are
    stable academic references, not load-bearing dependencies.

  Final state after `34eb281`: CI run `26412405532` green on every
  step of the 13-tool stack plus all 36 pre-existing validators.

### Changed

- **`validators/check_safe_tools.sh`:** swapped literal backticks
  inside a printf format string for single quotes (shellcheck SC2006
  flagged the backticks as legacy command-substitution syntax — they
  were intended as literals); added `# shellcheck disable=SC2001`
  annotation to the documented sed indent idiom.
- **`validators/*.py`:** removed 3 unused variables (dead code from
  prior refactoring, caught by `ruff F841`); removed 1 unused `import
  sys` (caught by `ruff F401`); added `# nosec`/`# noqa` annotations
  with explicit rationale to 2 safe `subprocess.run(list, ...)` call
  sites and 1 intentional `try/except/pass` site.
- **`.github/workflows/validate.yml`:** workflow now declares
  `permissions: contents: read` at both workflow and job level
  (closes the two zizmor `excessive-permissions` findings); the
  `actions/checkout` invocation sets `persist-credentials: false`
  (closes the zizmor `artipacked` finding); job carries an explicit
  `name:` for log-grep clarity.

- **Multi-LLM end-to-end review framework — bytes-verified arc closure
  across three independent review sessions.** The spec, the chardet
  relicense paper, and the hello-world proof paper each went through a
  tier-3 multi-LLM review framework (codex + gemini + grok per session;
  mistral unavailable on host; verification_report.toml as
  corrective-program spec; reviewers iterate against bytes, not
  summaries). Total: 12 reviewer-sessions across the three arcs, 36
  individual verdicts persisted. Final state: all three arcs closed at
  unanimous unconditional_approval with zero remaining bytes-verifiable
  defects.
  - `docs/reviews/2026-05-25-spec-e2e/` (r1, 15 blockers) →
    `docs/reviews/2026-05-25-spec-e2e-r2/` (1 codex blocker: S08.1
    --help string) → `docs/reviews/2026-05-25-spec-e2e-r3/` (unanimous;
    arc terminal).
  - `docs/reviews/2026-05-25-paper-chardet-e2e/` (r1, 10 blockers) →
    `docs/reviews/2026-05-25-paper-chardet-e2e-r2/` (codex B3 Conclusion
    overclaim) → `docs/reviews/2026-05-25-paper-chardet-e2e-r3/`
    (gemini B3 §10.3 intro overclaim — same defect class, third
    location) → `docs/reviews/2026-05-25-paper-chardet-e2e-r4/`
    (unanimous; arc terminal).
  - `docs/reviews/2026-05-25-paper-hello-world-e2e/` (r1, 2 blockers
    C1+C2) → `docs/reviews/2026-05-25-paper-hello-world-e2e-r2/`
    (unanimous including original C1 filer; arc terminal).
- **Validator-help cites every invariant ID it enforces.**
  `validators/validate_gate_decision.py` argparse description now
  enumerates INV01..INV06 with one-line summaries of each — closes
  spec-e2e-r2's S08.1 recipe-literal blocker. `--help | grep -oE
  'INV0[1-6]' | sort -u` returns all six.

### Changed

- **`paper/main.tex` Conclusion and §10.3 introduction now scope
  validation claims accurately.** Three recurring B3-class
  "scipy/numpy implementation" overclaims were caught across r2 and r3
  reviews of the chardet relicense paper. The paper's Conclusion
  (closed at r3) and §10.3 introductory sentence (closed at r4) both
  now distinguish AUX1+C06a-d (validated via scipy/numpy second-source
  primitives) from C06e (validated via stdlib digest re-derivation
  plus a subprocess to the harness's behavioural-fingerprint script,
  with explicit SKIP semantics). The §10.3 intro also states why C06e
  takes a different path: "because there is no scipy or numpy primitive
  that re-derives a chardet behavioural fingerprint."
- **`paper/figures/scripts/validation_report.json` refreshed.**
  Reviewer runs of `validate_numbers.py` regenerated this artifact
  during r3+r4. Previous corpus_digest_full was stale from a pre-r2
  era; now shows the correct `58e54831f84183c755c2458f...` digest
  matching `fingerprint_behavior.py`'s computation. Adds the
  `c06e_rates` SKIP row that documents toolchain-failure explicit
  reasons.
- **`.gitignore`: add `.local/`.** The local Werner Style Spec
  working-copy directory is local-only and MUST NOT ship in the public
  repo. Now explicitly gitignored.

### Audit-trail notes (not normative)

- All three review arcs demonstrate the multi-LLM lattice's
  load-bearing redundancy: each round, different reviewers caught
  different defect classes. At r3 of the chardet arc, codex's
  recipe-literal grep (`scipy ?/ ?numpy`) and grok's
  context-redeems-framing interpretation BOTH approved while
  gemini's broader grep (`scipy|numpy`) caught the surviving §10.3
  intro overclaim. Two reviewers would have missed it; three with
  diverse approaches caught it.
- Lesson for future verification_report.toml authors: when remediating
  a prose-class defect, the next round's grep recipe must enumerate
  the FULL alternation pattern (slash, "and", "+", bare-comma), not
  narrow to the form that triggered the predecessor blocker. r4's
  recipe added explicit A/B/C/D classification (listing-specific /
  scoped-composite / unscoped-global / negative-clause-clarification)
  so reviewers could not approve a class-C hit by interpretation.

## [v2026-05-25T03-30-02Z] — 2026-05-25 03:30:02 UTC

### Added

- **Rust-side TOML parser-conformance harness (closes the
  Go/Rust asymmetry).** New `tools/toml-test-decode-rs/` binary
  (~75 lines, `#![forbid(unsafe_code)]`, two deps: `toml 0.8` +
  `serde_json 1`) reads TOML on stdin and emits the toml-test
  tagged-JSON format on stdout. The shim is built from the same
  `toml` 0.8 crate that `tools/dagtoml-validate-rs` depends on,
  so a green run is direct evidence about the parser the **Rust**
  primary validator actually uses at runtime — the symmetric half
  of the existing BurntSushi/toml conformance check that covers
  the Go primary validator. Wired into the Makefile as
  `toml-conformance-rs` (and a `toml-conformance-all` alias that
  runs both Go and Rust passes) and into
  `.github/workflows/validate.yml` as a new step adjacent to the
  existing Go-side check. Result on the current crate pin:
  **185/185 valid + 371/371 invalid pass with no skiplist needed**
  — the Rust crate is strictly more conformant than BurntSushi
  v1.4 (it correctly rejects all 13 dotted-key / inline-table
  redefinition fixtures that BurntSushi accepts, removing the need
  for the permissiveness-baseline list on this side). The
  toml-lang/toml-test runner pinned at v1.6.0 is reused — no new
  go-install step in CI.
- **Agent Assurance Profile: cross-provider gate-decision invariant
  (INV06) for self-modification.** When a `gate-decision` artifact
  adjudicates a change to the producer agent's own harness or source
  code (`decision.subject_class = "self-modification"`), the
  gate-decision MUST be issued by a model whose `provider_id` AND
  `model_family_id` BOTH differ from the proposing agent's. The
  conjunctive AND is load-bearing: same-provider/different-family and
  different-provider/same-family BOTH fail. Files changed:
  - `profiles/agent-assurance/ontology.toml` — three new attribute
    vocabularies (`subject_class`, `provider_id`, `model_family_id`),
    each IJB-tagged `constraint/structural` per KD rules.
  - `profiles/agent-assurance/gate-decision-kind.toml` — root-shape
    prose adds five optional fields (`subject_class` plus four
    `*_provider_id`/`*_model_family_id`); new hard invariant `INV06`
    encodes the conditional-required-and-inequality predicate; the
    `[kind.relation_to_ontology].attribute_vocabularies` list grows
    to include the three new vocabularies.
  - `profiles/agent-assurance/tiers/solo.toml` — contracts `C02`
    (AI self-sign) and `C05` (single-signer) carve out
    self-modification gate-decisions explicitly, deferring to INV06;
    `verified_by` adds `gate-decision-invariant:INV06@1`.
  - `profiles/agent-assurance/overview.md` — new "Scope and posture"
    section states the profile's multi-provider operating assumption,
    audience-impact note for single-provider deployments, and
    migration guidance for existing profile users.
  - `profiles/agent-assurance/tiers/README.md` — tier-table solo row
    references INV06; new "Cross-tier rule" callout makes explicit
    that INV06 is a profile-level posture, not a per-tier ratchet.
  - `examples/self-modification-gate-decision.toml` — new worked
    example with the full attribution shape (proposing anthropic/claude,
    deciding openai/gpt); existing
    `examples/minimal-gate-decision.toml` left unchanged (pre-INV06
    shape, still valid as a non-self-modification decision).
  - `reference/database/MANIFEST.toml` — `[counts]` bumped
    (attribute_vocabularies 43→46, attribute_values_declared 180→202);
    per-engine `expected_seed_counts` bumped
    (attribute_vocabulary 43→46, attribute_value_allowed 116→138 in
    postgres + duckdb + sqlite); rdf `expected_footer_counts`
    attribute_vocabularies 43→46; `expected_triple_counts.schema`
    1329→1400.
  - `reference/database/postgres/seed.sql`,
    `reference/database/duckdb/seed.sql`,
    `reference/database/sqlite/seed.sql` — each adds 3 new
    `attribute_vocabulary` rows (`subject_class`, `provider_id`,
    `model_family_id`) and 22 new `attribute_value_allowed` rows
    (2 + 10 + 10), using engine-correct array syntax
    (`ARRAY[]` / `[]` / `json_array()` respectively); header
    comments updated.
  - `reference/database/rdf/schema.ttl` — regenerated via
    `tools/dagtoml-rdf/target/release/dagtoml-rdf`; footer count
    moves from 43 to 46 vocabularies (1400 triples total).
  - `tools/dagtoml-duckdb/src/main.rs` and
    `tools/dagtoml-duckdb-go/main.go` — hardcoded `EXPECTED_COUNTS`
    mirror updated (43→46 vocab, 116→138 value rows) so the runtime
    self-check matches the new manifest.
  - `CHANGELOG.md` (this entry).

  Rationale and predecessor review: this change implements the
  proposal blocked in round-1 review at
  `docs/reviews/2026-05-25-cross-provider-self-mod-gate-proposal/`
  (terminal verdict `concrete_unresolvable_blocker` from codex + grok).
  Closures: B1 (chain-verifiable predicate via `subject_class`), B2
  (tight `AND` not "and/or" in INV06), B3 (solo tier C02/C05
  contradiction carved out), R1 (additive-optional fields + conditional
  invariant per `spec.md:482-489` versioning), R2 (migration guidance
  in overview + tiers/README), R3 (no proper-noun "agent-federator" in
  normative prose — the runtime contract is described, the broker name
  isn't). Round-2 multi-LLM review at
  `docs/reviews/2026-05-25-cross-provider-self-mod-gate-proposal-r2/`
  returned 2× `unconditional_approval` (gemini, grok) and 1×
  `concrete_unresolvable_blocker` (codex) on a single residual
  cross-cutting defect: this CHANGELOG entry's "Files changed"
  sub-bullet list initially omitted 8 of the 14 changed files (the
  list above as written closes that gap), plus a bundle metadata
  correction (see `r2/terminal_decision.toml` N2). A round-3 review
  is dispatched to verify the metadata fix without re-litigating
  the structural change.

### Fixed

- **CI: bump Node 20-deprecated actions to current major.**
  `actions/checkout` v4 → v5, `actions/setup-python` v5 → v6,
  `actions/setup-go` v5 → v6. GitHub announced Node 20 deprecation
  on runners with a 2026-06-02 hard cutoff (the older majors above
  bundle Node 20). `dtolnay/rust-toolchain@stable` is a shell-based
  action and unaffected.
- **CI: silence false positives + redact real leaks in the
  banned-markers grep.** Surfaced as a follow-on once the
  manifest-drift gate started running again (previously hidden
  behind the same CI failure). Two changes:
  1. **Workflow**: `.github/workflows/validate.yml`'s "Verify no
     banned markers" step now also excludes `docs/reviews/` from
     the `/srv/repos/internal` scan. Rationale: multi-LLM review
     audit trails legitimately discuss the banned-path policy by
     name as part of their evidence record (e.g., "Confirmed —
     banned internal path prefix absent."). The grep is meant to
     catch ACTUAL leaks in spec/example/code/paper surfaces, not
     narrative discussion of the policy in audit trails. Editing
     historical review files to obfuscate the string would
     falsify the audit record. Comment in the workflow now
     enumerates the full exclusion rationale.
  2. **Redactions**: `paper/Makefile` (1 occurrence in a header
     comment) and `paper/user-prompts.md` (2 occurrences in
     captured user-prompt history) had absolute
     `/srv/repos/internal/...` paths that genuinely should not
     ship in a public repo. The paths are now redacted in-place
     with `[internal path redacted: ...]` markers that preserve
     the substantive meaning (which internal artefact was being
     referenced) without leaking the absolute filesystem
     location. These leaks have existed since at least
     2026-05-21 (last green CI on this repo); they went
     undetected because the manifest-drift step was failing
     upstream and halting CI before "Verify no banned markers"
     ran.
- **CI: build `dagtoml-rdf` before the manifest-drift gate.** The
  count-mirror gate in `validators/check_attribute_values.py`
  (invoked by `validators/check_manifest_drift.sh`) probes
  `tools/dagtoml-rdf/target/release/dagtoml-rdf` to compute the RDF
  triple-count surface, and intentionally hard-fails when the
  binary is absent (the script's own comment: missing-binary is
  "the silent-mirror-rot pattern the gate exists to prevent"). The
  CI workflow built `dagtoml-validate-rs` and `dagtoml-validate-go`
  but never `dagtoml-rdf`, so the gate had been hard-failing on
  every push since the dependency was introduced — three
  consecutive `main` pushes before this fix (issue-ledger persist,
  SPEC §13 Phase 3 persist, toml-conformance-harness persist) all
  failed at this step despite their actual content being clean. New
  step "Build dagtoml-rdf (required by manifest-drift gate)" runs
  before the "Manifest drift" step.

### Added

- **toml-test parser-conformance harness — review approved (unanimous).**
  Round-1 multi-LLM review of commit `afe354c` returned 3/3
  `unconditional_approval` from codex, gemini, and grok. All three
  reviewers reproduced `make toml-conformance` (185/185 valid +
  358/358 invalid + 13 skipped) and independently re-ran the
  *unskipped* suite, confirming the 13-entry skiplist matches the
  actual fail set byte-for-byte. Codex additionally ran
  `go version -m` on the installed `toml-test-decoder` binary and
  observed `mod github.com/BurntSushi/toml v1.4.0` directly,
  providing binary-provenance evidence that the decoder is built
  from the same module `tools/dagtoml-validate-go` imports — the
  load-bearing claim of the change. Terminal decision persisted at
  `docs/reviews/2026-05-25-toml-conformance-harness/terminal_decision.toml`.
- **TOML 1.0 spec-conformance harness wired into CI.** New top-level
  `Makefile` ships two targets: `toml-conformance-install`
  (`go install`s the pinned `toml-lang/toml-test` runner and the
  `BurntSushi/toml` `toml-test-decoder` shim) and `toml-conformance`
  (runs the suite). The decoder is shipped by the same
  `BurntSushi/toml v1.4.0` module that `tools/dagtoml-validate-go`
  depends on, so a green run is evidence about the parser the Go
  validator actually uses at runtime — not just about some unrelated
  TOML library. Result on the pinned version: 185/185 valid and
  358/358 invalid pass, with 13 known-tolerated invalid-test misses
  enumerated in the Makefile's `TOML_CONFORMANCE_SKIPS` skiplist
  (all dotted-key / inline-table redefinition edge cases that
  pre-date the TOML 1.1 spec tightening). The skiplist is a
  baseline of permissiveness, not a permanent allowance: any bump
  of `TOML_TEST_DECODER_VERSION` requires revisiting it. Wired into
  `.github/workflows/validate.yml` as a new step adjacent to the
  Taplo lint, so both syntax-layer checks run together. Follow-up:
  a Rust decoder shim against the `toml` 0.8 crate used by
  `tools/dagtoml-validate-rs` would extend the same evidence path
  to the Rust validator's parser.
- **SPEC §13 retrofit — Phase 3 review approved (unanimous).** Round-1
  multi-LLM review of commit `3749398` (Phase 3 retrofit) returned
  3/3 `unconditional_approval` from codex, gemini, and grok. The
  R1/R2 challenge on `adapter-contract` (plan §7 row 7 + §8) was
  tested against bytes by codex (prompt-designated adversary) and
  grok (independent confirmer); both rejected R2 with file:line
  citations and upheld R1. Terminal decision persisted at
  `docs/reviews/2026-05-25-spec-13-phase-3-procedure-and-special/terminal_decision.toml`.
  With this approval the SPEC §13 retrofit arc (Phases 1 → 2 → 3)
  is fully closed; the `spec.md:1478-1486` follow-up is discharged
  and 19 of 19 blessed kinds now carry the §13 contract.
- **SPEC §13 retrofit — Phase 3 (procedure-bearing + special).
  Retrofit complete: 19 of 19 blessed kinds now declare §13.** Five
  kind descriptors retrofitted (all Family A under Reading R1):
  - `procedure-declaration.v1`:
    `profiles/agent-assurance/rollback-plan-kind.toml`. R1 header is
    explicit: the envelope bounds the descriptor parse only; runtime
    trigger evaluation (metric scraping, threshold comparison,
    paging) and procedure-step execution (flag flips, redeploys) are
    RUNTIME-SPEC and lie outside this envelope.
  - `validation-record.v1`:
    `profiles/agent-assurance/smoke-validation-kind.toml`. Records the
    outcome of a smoke run that already executed; the smoke run's own
    runtime capabilities are not constrained by this envelope.
  - `assertion-set.v1`:
    `profiles/agent-assurance/assertion-bundle-kind.toml`. SPEC-layer
    validation parses each `[[bundle.assertions]].line` against the
    ABNF and checks within-bundle ID uniqueness; hash/digest
    verification is RUNTIME-SPEC per the kind's own INV04.
  - `interface-contract.v1`:
    `profiles/agent-assurance/adapter-contract-kind.toml`. Plan §7
    flagged this kind for R1/R2 reviewer challenge; the §13 header
    comment is extra-explicit that R1 was adopted, that the runtime
    capabilities a deployed adapter is permitted at execution time
    are declared INSIDE the instance file's `[adapter].runtime_*`
    fields (NOT in this kind descriptor's envelope), and that an R2
    envelope would either be unboundedly wide or duplicate the
    instance-level declarations.
  - `cryptographic-proof.v1`:
    `profiles/disclosure/selective-disclosure-proof-kind.toml`. Per
    the kind's own prose at lines 61-62 and the plan §5
    Family-B/C-exceptions analysis (which codex r1 on the plan
    pinned against validator-vocabulary evidence): the SPEC-layer
    parse is shape-only; cryptographic verification is RUNTIME-SPEC.
    Family A — `entropy_source = "none"`, `crypto_keys.denied = true`.
  The abstraction-class validator now reports
  `19 file(s) checked; 19 declared a §13 block` (up from 14 after
  Phase 2). Closure-root validator remains green at 74 files — each
  retrofitted descriptor's declared `closure_root` stays at the
  canonical empty-closure sentinel per SPEC §12.11 because none of
  them cite upstream evidence. With Phase 3 landed, the SPEC §13
  retrofit follow-up called out at `spec.md:1478-1486` is fully
  closed: every blessed kind in the public spec now participates in
  §13's class + envelope contract and its closure-root cascade-break
  property.
- **SPEC §13 retrofit — Phase 2 (declarations).** Nine kind descriptors
  now declare the §13 contract, covering six new class ids:
  - `policy-declaration.v1` (3 kinds, each with its own kind-specific
    description per plan §6): `core/contract-declaration-kind.toml`,
    `core/readiness-gate-kind.toml`,
    `profiles/agent-assurance/spec-contract-kind.toml`.
  - `plan-decomposition.v1`: `core/implementation-dag-kind.toml`. The
    description explicitly states the envelope bounds the descriptor
    parse only (Reading R1 per plan §5); runtime capabilities of the
    units the DAG describes are declared on each unit's producer kind.
  - `extension-declaration.v1`: `core/profile-descriptor-kind.toml`.
  - `relation-ledger.v1`: `core/traceability-kind.toml`.
  - `binding-declaration.v1`:
    `profiles/agent-assurance/adapter-registry-binding-kind.toml`.
  - `threat-declaration.v1`:
    `profiles/agent-assurance/threat-model-kind.toml`. The §13 prose
    explicitly avoids the IJB-forbidden phrase "risk posture", per the
    kind's existing IJB-stance note.
  - `attestation-record.v1`:
    `profiles/disclosure/disclosure-attestation-kind.toml`. The
    description records that signature verification is RUNTIME-SPEC,
    matching the kind's existing prose at lines 69-70.
  Every retrofit uses the Family A envelope (100ms CPU, 1MB memory, all
  9 capability domains denied/zeroed) matching the cost-record /
  Phase 1 reference shape. The abstraction-class validator now reports
  `19 file(s) checked; 14 declared a §13 block` (up from 5). Closure-root
  validator remains green at 74 files — each retrofitted descriptor's
  declared `closure_root` stays at the canonical empty-closure sentinel
  per SPEC §12.11 because none of them cite upstream evidence (the
  descriptor file's SHA-256 changes; its declared closure_root value
  does not). Phase 3 (5 procedure-bearing + special kinds) remains
  follow-up work per plan §8.
- **SPEC §13 retrofit — Phase 1 (observation-record.v1).** Four kind
  descriptors now declare the §13 contract: `core/evidence-matrix-kind.toml`,
  `profiles/agent-assurance/gate-decision-kind.toml`,
  `profiles/agent-assurance/assertion-log-record-kind.toml`, and
  `profiles/disclosure/redaction-manifest-kind.toml`. Each adds
  `[kind.abstraction_class]` with `id = "observation-record.v1"` and a
  kind-specific `description` that names its own structural shape (per
  the per-kind-description rule in
  `docs/planning/2026-05-25-spec-13-retrofit-scoping.md §6`), plus a
  Family A `[kind.capability_envelope]` block (100ms CPU, 1MB memory,
  all 9 capability domains denied/zeroed) matching the cost-record
  reference at `profiles/cost/cost-record-kind.toml:282-327`. The
  abstraction-class validator now reports
  `19 file(s) checked; 5 declared a §13 block` (up from 1). Closure-root
  validator remains green at 74 files — each retrofitted descriptor's
  declared `closure_root` stays at the canonical empty-closure sentinel
  per SPEC §12.11 because none of them cite upstream evidence (the
  descriptor file's SHA-256 changes; its declared closure_root value
  does not). Phases 2 (8 declaration kinds) and 3 (5 procedure-bearing
  and special kinds) remain follow-up work per plan §8.
- **SPEC §13 — Abstraction class + capability envelope.** Folds the
  Stream F V2 + Turn-6 abstraction-class-type-safety proposals
  (`docs/research/2026-05-22-spec-foundations-research/follow-up-2/16-stream-f-synthesis-v2.md`
  + `.../10-abstraction-class-thread.md` + `.../12-canonical-thread.md`)
  into normative spec text. Every `*-kind.toml` descriptor MAY now
  declare two optional blocks: `[kind.abstraction_class]` (a single
  versioned class id of the form `<slug>.v<integer>` + a producer-
  attested description) and `[kind.capability_envelope]` (resource
  bounds + a closed-set of nine per-domain capability grants drawn
  from WASI Preview 2 WIT: filesystem, sockets, http, clocks,
  random, environment, process_spawn, ipc, crypto_keys). Both
  blocks are part of the kind descriptor's canonical bytes and
  flow into its `closure_root` per §12.1, so changing the class or
  widening the envelope cascade-breaks downstream instances. New
  subsections §13.1–§13.10 cover the rule, the two block shapes,
  the cascade-break property, scope-out (wire format, attenuation
  calculus, signing tier, enforcement backend, static-observability
  for WASM are all RUNTIME-SPEC), IJB conformance, the
  closed-vocabulary participation, a worked `data-transform.v1`
  example, four forbidden papering-over mechanisms (re-sign under
  unchanged closure_root on widening; implicit-grant on missing
  domain; ad-hoc capability fields outside the closed set; mixing
  technical+legal signing tiers), and the backwards-compatible
  introduction rule (existing kinds remain conformant; new
  declarations are opt-in).
- **Two new core ontology vocabularies** in `core/ontology.toml`:
  - `capability_envelope.domain` — closed set of 9 WIT-derived
    domain names; sub-table names under
    `[kind.capability_envelope]` are bounded by this vocabulary.
    Adding a new domain is a SPEC amendment that bumps
    `schema_version`. Fail-closed default: an omitted domain
    sub-table is treated as denied (§13.9).
  - `abstraction_class.id_pattern` — closed pattern
    `<slug>.v<integer>` with `<slug>` producer-attested and
    `v<integer>` required + monotonic. The value space is open by
    design (producers declare their own class taxonomy); the
    shape is closed so consumers can reject class-version drift
    via the §12 closure-root cascade.
- **`validators/validate_abstraction_class.py`** — dedicated
  reference validator. Enforces the structural rules of §13.2 +
  §13.3: id pattern, IJB tags, required cpu/memory bounds,
  closed-set domain names (with the single source of truth being
  the core ontology's `capability_envelope.domain` vocabulary),
  per-domain sub-table shape (preopens + read/write/exec for
  filesystem; tcp/udp/ip-resolve allowlists for sockets; etc.).
  Backwards-compatible: descriptors that omit both blocks pass.
  Wired into CI as a separate workflow step.
- **Worked example** in `profiles/cost/cost-record-kind.toml`: the
  cost-record kind now declares
  `abstraction_class.id = "observation-record.v1"` (read-only
  observation artefact, no I/O, no networking) and a minimal
  capability envelope (1MB memory, 100ms CPU, all 9 capability
  domains denied or zeroed). This is the first kind descriptor in
  the spec to declare the §13 primitive; it demonstrates the
  pattern. The other 18 kinds remain unmodified — retrofitting
  them is explicit follow-up work.
- **Reference DB updates**: 2 new attribute vocabularies + 10 new
  attribute values seeded across postgres / sqlite / duckdb.
  `expected_seed_counts.attribute_vocabulary` 41→43,
  `attribute_value_allowed` 106→116. RDF regenerated:
  `expected_triple_counts.schema` 1291→1329. Rust + Go
  `EXPECTED_COUNTS` hardcodes updated. MANIFEST `[counts]`:
  `attribute_vocabularies` 41→43, `attribute_values_declared`
  170→180, `attribute_values_closed` 99→109.
  `bash validators/check_manifest_drift.sh` is green at the new
  totals across all 28 count-mirror surfaces.

- **Cost profile (Stream G — Cost-Witnessed Decision).** New blessed
  profile under `profiles/cost/` with a single kind, `cost-record`,
  declaring the cost of one costed action so that gate-decisions and
  evidence-matrix entries can cite *which* costs witnessed a verdict
  and an auditor can see *what class of deciding entity* paid for it.
  Three closed vocabularies in `profiles/cost/ontology.toml`:
  `cost_dimension_category` (7 values: token_equivalent,
  compute_time_seconds, storage_bytes, bandwidth_bytes,
  human_review_time_seconds, energy_equivalent, evidence_run_count),
  `decider_class` (8 values: deterministic_check, llm_single,
  llm_consensus, human_reviewer, tee_attested_compute, notarisation,
  transparency_log_write, other), `cost_citing_kind` (7 values
  enumerating the kinds whose execution may pay a cost). Quantities
  are non-negative integers (no floats per canonical-form
  determinism); unit labels are producer-attested and free-form (no
  spec-fixed unit normalisation — comparability across producers
  requires an explicit conversion artefact). Minimal example at
  `examples/minimal-cost-record.toml` (smoke-validation paid for by
  three-model LLM consensus). Per the proposal under
  `docs/research/2026-05-22-spec-foundations-research/follow-up-2/13-stream-g-cost-witnessed-decision.md`,
  the cost-record is observation not policy; signatures, currency,
  vendor SKUs, allowances, and transitive aggregation are
  deliberately out of scope. The kind names Cost-Witnessed Decision
  as the third frontier primitive peer to Provable Intent
  (SPEC §12 closure-root) and Structural Governance (SPEC §3/§10
  IJB). New `validators/validate_cost.py` enforces invariants
  INV01–INV06 (closed-vocab membership × 3, integer-only quantities,
  RFC 3339 timestamps, MD5/SHA-1 forbidden). INV07 — IJB-primitive
  resolution of every entity prefix and relation predicate used in
  instance files — is delegated to the shared
  `validators/validate_ijb_conformance.py` as declared in the kind
  descriptor's `[[kind.hard_invariants]] enforced_by` field; the
  cost validator deliberately does not duplicate that cross-cutting
  check. Reference DB seeds
  (postgres / sqlite / duckdb), MANIFEST counts, and regenerated
  RDF schema all updated; `bash validators/check_manifest_drift.sh`
  is green at 20 template kinds / 27 entity kinds / 31 relation
  predicates / 41 attribute vocabularies. CI gates the cost profile
  alongside agent-assurance and disclosure.
- **Second-pass review filings + round-2 fixes for `examples/arxiv-prep-agent-dag.toml`.**
  Captured the three completed second-pass job outputs (Claude / Codex /
  Gemini) into
  `docs/reviews/2026-05-24-arxiv-prep-dag/second-pass/raw_findings/` so the
  audit trail exists. Patched `examples/arxiv-prep-agent-dag.toml` for the four
  blockers Codex enumerated (LL-001 prose-header overclaim narrowed to the
  documented corpus; LL-002 subdir/flatten policy made explicitly
  mode-selectable via `policy.instance.allow_subdirs`; NEW-001 U09
  manifest path moved into `evidence/` subdirectory to match its summary
  prose; NEW-002 U10 submission-bundle summary now states the .bbl
  inclusion rule explicitly, conditioned on U04's mode), plus the two
  STILL-PRESENT leftover overclaims Codex flagged (UC-002 "vanishingly
  unlikely" replaced with a bounded eliminates-documented-classes claim;
  SR-001 "authoritative sources" replaced with "referenced source
  corpus"). Both `validate_implementation_dag.py` and
  `validate_ijb_conformance.py --repo-root .` still PASS on the patched
  file. A third-pass review (including a non-plan-mode Claude re-run) is
  required before unconditional approval.
- **Migration note for pre-§12 producers** at spec.md §12.11. Walks
  the four-step migration mechanically: identify conforming
  documents (`[meta].template_kind` blessed per §12.1), choose the
  closure value (empty-closure sentinel for self-contained docs,
  computed digest per §12.1 otherwise), place the field before the
  first `[table]` header, re-emit + re-sign. This is a
  backwards-incompatible conformance change; per §8.2 it would
  normally bump major `schema_version`, but the rule lands
  during the Draft Specification phase so `schema_version` stays at
  `"0.1.0"`.
- **SPEC §12 — the closure-root rule (brittleness propagation).** Folds
  the proposal under
  `docs/research/2026-05-22-spec-foundations-research/follow-up-2/14-`
  into normative spec text. Every conforming DAG-TOML document MUST
  carry a root-level `closure_root` field of the form
  `<sha256|sha384|sha512>:<lowercase-hex>` computed over the canonical
  concatenation of (1) every upstream artifact hash cited and (2)
  every upstream revocation snapshot known at emission time. The
  field MUST appear before the first `[table]` header so TOML binds
  it to the document root rather than to `[meta]`. Self-contained
  documents emit the canonical empty-closure sentinel
  `sha256:e3b0…b855` (SHA-256("")), with stronger-digest analogues
  tabled in §12.1. New subsections §12.2–§12.10 cover the
  cascade-break property, producer/consumer responsibilities,
  what is deliberately out of scope (envelope format, signing
  primitive, transparency-log target), four forbidden papering-over
  mechanisms (re-signing on stale closure, storing closure in
  unsigned envelope attributes, "soft revocations", caching closure
  inputs across upstream versions), the deferred canonical-
  concatenation algorithm, interactions with §2.7 / §5 / §11 /
  the disclosure profile (redaction does NOT flip the upstream's
  closure), and the live-feed snapshot rule. Back-references added
  in §2.7 (posture fields are NOT closure-root inputs), §5
  (closure-graph acyclicity extends the §5 cycle prohibition), and
  §11 (`source_sha256` is *one input* to `closure_root`, not a
  substitute).
- **`cites_upstream` core relation predicate** in
  `core/ontology.toml`. Cross-kind marker that a `*-kind.toml`
  required field carries an upstream artifact reference that MUST
  flow into the document's closure root. Source and range are
  intentionally `unconstrained_label` — the rule fires uniformly
  across every conforming kind regardless of which concrete
  entity kinds a profile defines. Total core relation count is
  now 31 (was 30).
- **`closure_root.digest_algorithm` core attribute vocabulary** in
  `core/ontology.toml` (extensible: `sha256` | `sha384` | `sha512`).
  Closed-for-now; extension reserved for stronger / post-quantum
  digests. Weaker algorithms (MD5, SHA-1) are forbidden by SPEC
  §12.1 and MUST NOT be added. Total core attribute-vocabulary
  count is now 10 (was 9); union with profile vocabularies is 38
  (was 37).
- **`validators/validate_closure_root.py`** — dedicated reference
  validator for the §12 rule. Enforces presence at the document
  root, `<algo>:<hex>` shape, hex-length-matches-algorithm, and
  explicit rejection of MD5/SHA-1. Wired into CI as a separate
  workflow step gating every canonical example and tier file.
  Computation of the digest itself is profile/runtime work; the
  validator enforces the spec-layer rules only.
- **Empty-closure sentinel applied to every canonical example.** All
  17 minimal examples under `examples/` plus all 5 deployment-tier
  files now declare the canonical empty-closure sentinel as their
  root-level `closure_root` so the brittleness graph is a total
  function — every conforming document participates.
- **Reference database updates for §12.** `cites_upstream` and
  `closure_root.digest_algorithm` (plus its three closed values) are
  seeded in `reference/database/{postgres,sqlite,duckdb}/seed.sql`
  and in `reference/database/graph/schema.cypher`. The RDF
  reference (`reference/database/rdf/schema.ttl`) was regenerated
  via `tools/dagtoml-rdf`. `reference/database/MANIFEST.toml`
  `[counts]` updated to `relation_predicates = 31`,
  `attribute_vocabularies = 38`, `attribute_values = 84`; all
  per-engine `expected_*_counts` updated to match. `bash
  validators/check_manifest_drift.sh` is green.
- **ArXiv submission pre-flight DAG** — `examples/arxiv-prep-agent-dag.toml`.
  A 10-unit `implementation-dag` (core only) that encodes every requirement from
  Trevor Campbell's checklist, the official arXiv "Common Mistakes" FAQ, Ian Huston's
  2011 checklist, and the current `submit_tex.html` + `texlive.html` guidance
  (TeX Live 2025, bib/biber auto-processing, minted v3 cache rules, ifpdf, hyperref
  order, 4-pass typeout, filename hygiene, figure formats, 00README, hidden-file
  stripping, etc.). Uses the exact same `[policy.*]` + `proofs_mapping` + `evidence`
  + gated-compilation pattern as `claim-analysis-agent-gated-dag.toml`. All
  `ART:`, `OUT:`, `Uxx`, and predicate strings pass `validate_ijb_conformance.py`.
  The DAG produces a clean tarball + machine-readable evidence pack that makes
  arXiv rejection for packaging reasons effectively impossible. Full text of the
  three source URLs was retrieved via Exa MCP before authoring.
- **Stream F triangulation + V2 synthesis + `source-analysis` profile
  proposal** under
  `docs/research/2026-05-22-spec-foundations-research/follow-up-2/`.
  Three CLI agents (Codex/Gemini/Grok) gave independent second-opinion
  reports on the Exa Deep Researcher's capability-envelope verdict and
  converged on the same six categorical critiques. Stream F V2
  synthesis (`16-`) supersedes the Exa Deep report as the canonical
  Stream F output: CDDL stays for shape only (attenuation moves to a
  separate executable calculus); draft dCBOR is replaced by RFC 8949
  Core Deterministic Encoding + frozen profile rules (floats
  prohibited); COSE_Sign1 stays for technical integrity but **CB-AdES
  (ETSI TS 119 152-1, March 2026)** is now the recommended legal-grade
  COSE profile carrying `xRefs`/`rRefs`/`sigTst`/`arcTst` headers;
  Linux syscall names are replaced by **WASI Preview 2 WIT interfaces**
  as the canonical capability vocabulary; the seven-field envelope is
  expanded to nine capability domains plus separate resource bounds;
  and the "compression library opens a socket" example is reframed
  as static observability via WASM Component Model imports (consumer's
  CI rejects the artifact at parse time, not runtime). The
  `source-analysis` profile proposal (`15-`) drafts a three-kind
  subset of the spec (`source-record`, `semantic-extraction`,
  `source-citation`) for analyzing articles/research papers, capturing
  their logical/semantic/intent structure as IJB-typed graphs, signing
  the extraction, and emitting a cryptographically-bound citation
  format `[author24/hash8]`. Both proposals await maintainer review.
- **Stream F (capability envelopes), Stream G (Cost-Witnessed Decision),
  and the closure-root spec.md section proposal** under
  `docs/research/2026-05-22-spec-foundations-research/follow-up-2/`.
  Stream F's Exa Deep Researcher report proposes a hybrid CBOR-canonical
  serialization + typed envelope schema (CDDL over CBOR + COSE signing
  with DID-bound keys), with attenuation via monotonic set-reduction
  and enforcement via LSM/seccomp/Capsicum/CHERI per deployment; the
  three CLI-agent companion runs were lost to gateway result-retention
  ageing and are being re-launched as second-opinion triangulation.
  Stream G ("Cost-Witnessed Decision") proposes a new `cost-record`
  template kind (placement deferred to a new minimal `cost` profile),
  with a `decider_class` closed-set discriminator that makes gate
  threat-surface legible to auditors, seven closed-set cost dimensions
  with producer-attested unit labels, integer-only quantities (matching
  Stream D's no-floats consensus), and an optional `[[decision.cited_costs]]`
  cross-reference into gate-decision. The closure-root spec.md section
  proposal drafts a new top-level §12 establishing the
  brittleness-propagating attestation rule (upstream changes MUST flip
  downstream `closure_root`; signed envelopes wrapping downstream
  documents MUST become invalid; non-normative warning that this
  inverts standard PKI behaviour and enumerates four forbidden
  papering-over mechanisms). Not yet folded into spec.md — proposal
  awaits maintainer review.
- **Spec intro framing — Provable Intent + Structural Governance**
  (`spec.md`, `README.md`). Names the two load-bearing deliverables the
  spec exists to solve, anchored to the "writing code is becoming the
  new assembly language" framing and the "bicycle vs. autonomous
  self-generating infrastructure" rebuttal. Replaces the earlier dry
  "describes how agents plan, sequence, and prove work" framing as the
  reader's first encounter with the spec's purpose. Detailed rationale
  in `docs/research/2026-05-22-spec-foundations-research/follow-up-2/11-overkill-rebuttal-and-frontier-problems.md`.
- **Abstraction-class type-safety primitive** added to design directives
  (`docs/research/2026-05-22-spec-foundations-research/06-user-design-directives.md`
  Turn 6 addendum). Kind descriptors must declare both structural shape
  AND capability envelope; class violations must cascade-break
  downstream regardless of signature validity. Three-part and five-part
  thread drafts in `follow-up-2/10-` and `follow-up-2/12-` respectively.
- **Cross-LLM + Exa research dossier on spec foundations**
  (`docs/research/2026-05-22-spec-foundations-research/`). Independent
  external research conducted in parallel by Claude+Exa, Codex+Exa,
  Gemini+Exa, Grok+Exa, and Exa Deep Researcher (`exa-research-pro`),
  across three waves and 13 research streams:
  - **First wave** — six questions (IJB primitives prior art,
    TOML-only spec-design risks, self-describing-schema drift,
    agent-assurance governance, spec-design failure modes, DAG
    traceability).
  - **Follow-up wave** — four streams (kind-descriptor drift mitigation,
    legal-grade one-shot immutable attestation, separation-of-duty
    validation, alternative-format selection / new-format design).
    Convergence across four independent sources was unusually tight;
    recommended build order D → A → C → B.
  - **Third wave (`follow-up-2/`)** — cognitive-automation lineage
    ("what do we do with more processing power"), HW/SW/cognition
    layering as inference cost declines and FPGA emerges, plus
    a Grok-shared conversation about Cloudflare zero-trust TOML
    hosting (recovered via headless-Chrome render of the share URL).
  - Includes the user's design directives, per-stream synthesis,
    full prompt reproducibility (`prompts/`), and operational records
    (`raw/job-manifest.toml`, `raw/failed-attempts.md`). Total Exa Deep
    Researcher spend across waves: $10.21.
- **Pre-1.0 layering primitives** (spec.md §2.5, §2.7, §6.1, §11.1).
  Four hard-to-retrofit additions land together so the public/private
  boundary stops drifting:
  - **`profile-descriptor` kind** (`core/profile-descriptor-kind.toml`).
    Meta-meta layer documenting profiles the way `kind-descriptor`
    documents `template_kind`s. Declares `name`, `namespace`, `owner`,
    `license`, `extends`, `ontology`, `contained_kinds`. Reference
    instances at `profiles/agent-assurance/PROFILE.toml` and
    `profiles/disclosure/PROFILE.toml`.
  - **Profile namespacing partition** (SPEC §2.5). Unprefixed
    kebab-case is reserved for blessed profiles; everything else MUST
    be reverse-DNS. The DNS namespace gives adopters uniqueness
    without a central registry.
  - **`[meta].confidentiality / license / embargo_until`** (SPEC §2.7).
    Closed set for confidentiality, free-form SPDX/`LicenseRef-…` for
    license, RFC 3339 for embargo_until (REQUIRED when
    `confidentiality = "embargoed"`).
  - **`[provenance.encryption]` sub-table** (SPEC §11.1). Records the
    encryption shape so a `[provenance]` block can refer to encrypted
    source bytes without the spec ever touching keys.
- **Disclosure profile** (`profiles/disclosure/`). New blessed profile
  with three kinds — `disclosure-attestation`, `redaction-manifest`,
  `selective-disclosure-proof` — plus its own ontology extension and
  three minimal examples
  (`examples/minimal-disclosure-attestation.toml`,
  `examples/minimal-redaction-manifest.toml`,
  `examples/minimal-selective-disclosure-proof.toml`).
- **Safe-Rust + Go primary validators** under
  `tools/dagtoml-validate-rs/` and `tools/dagtoml-validate-go/`. Both
  cover profile-descriptor invariants (INV01..INV05), the disclosure
  profile, the `[provenance.encryption]` sub-table, and the §2.6 /
  §2.7 meta-field rules. Rust crate is `#![forbid(unsafe_code)]`
  (enforced by `validators/check_safe_tools.sh`); Go module uses the
  BurntSushi/toml parser. CI runs both BEFORE the Python validators;
  divergence is a build break. The pre-existing Python validators
  (`validators/validate_*.py`) are retained as cross-checks.
- **Reference Python validators for the new artifacts.**
  `validators/validate_profile_descriptor.py` and
  `validators/validate_disclosure.py`.
- **Adoption guide** at `docs/adoption.md` — non-normative,
  walks the "public spec, private profile" pattern with a worked
  `com.example.internal` example.
- **Pre-1.0 cleanups** bundled with the layering work:
  - `confidentiality = "public"` and `license = "Apache-2.0"` set on
    every canonical example and tier file so adopters see the new
    fields in practice.
  - SPEC §2.6: `[meta].docs` MUST start with `https://` and MUST NOT
    contain a query string; enforced by the primary validators.
  - `core/ontology.toml` new `[[attribute_vocabularies]]` entries:
    `confidentiality`, `license`, `framework_profile_namespace`, and
    `provenance.encryption.hash_is_over`.
  - `validators/validate_ijb_conformance.py` extended to classify the
    three new meta fields and to dispatch on
    `template_kind = "profile-descriptor"`. The §10.2 mapping note
    now permits `ijb_constraint_type = "policy"` or `"observed"` on
    `[[attribute_vocabularies]]` blocks (declared posture
    vocabularies).
- `reference/database/`: non-normative reference database schemas for
  ingesting DAG-TOML instances. Includes `postgres/schema.sql` (hybrid
  relational + JSONB, with enums for closed attribute vocabularies and
  views for DAG/coverage/gate queries), `postgres/seed.sql` (registry
  rows derived from the ontology files and `*-kind.toml` descriptors,
  covering all 15 template kinds (5 core + 9 profile + the meta
  `kind-descriptor`), all 23 entity kinds (17 core + 6 profile), all
  30 core relation rows (with `contract:`-namespaced variants for
  predicate names the ontology declares more than once), and all 29
  attribute vocabularies (5 core + 24 profile)), and
  `graph/schema.cypher` (property-graph model with constraints,
  indexes, registry seed, and example invariant + traversal queries).
  `reference/database/README.md` documents the design principles, IJB
  grounding, and ingestion model. `reference/database/MANIFEST.toml`
  provides the machine-readable companion: artifact paths, target
  versions, namespaced-predicate convention, and the ontology-derived
  counts the seed inserts (15 / 23 / 30 / 29 / 54) so an ingestion
  tool or drift check can verify load results without re-parsing the
  ontology. Nothing under `reference/database/` is conformance-required;
  the ontology files and validators remain the source of truth.
- `reference/database/sqlite/`: SQLite/libSQL (Turso) reference schema.
  Same registry shape and counts as the Postgres reference, adapted to
  SQLite STRICT tables (no `CREATE TYPE` enums — column-level CHECK
  lists instead; JSON via the json1 built-in; arrays as JSON values;
  cycle detection as a recursive view since SQLite has no stored
  functions). Verified by loading `schema.sql` + `seed.sql` into stock
  SQLite 3.51 in an alpine container — same 15/23/30/29/54 row counts,
  same invariant views fire on the same fixture. libSQL ≥0.24 supports
  every feature used; no schema changes needed for Turso.
- `validators/check_manifest_drift.sh`: pure-bash drift check. Compares
  the four counts in `reference/database/MANIFEST.toml [counts]`
  against the live ontology files (number of `[[entities]]`,
  `[[relations]]`, `[[attribute_vocabularies]]` blocks plus the count
  of `*-kind.toml` descriptors). Also parses the footer of
  `reference/database/rdf/schema.ttl` and verifies the same counts so
  a stale RDF artifact is caught even when the manifest and SQL seeds
  were correctly regenerated. Exits non-zero on either drift. Wired
  into the validate CI workflow as the step after Taplo lint.
- `reference/database/rdf/`: RDF/Turtle reference. `schema.ttl` renders
  the IJB primitives, 15 template kinds, 23 entity kinds, 30 relation
  predicates, and 29 attribute vocabularies as RDF classes and
  properties under three namespaces (`dagtoml:`, `dagprof:`, `ijb:`).
  Closed vocabularies use `owl:oneOf` ranges; open vocabularies are
  marked `dagtoml:extensible true`. `shapes.ttl` is hand-authored
  SHACL covering the graph-shaped invariants the schema alone cannot:
  single producer per artifact, depends_on/blocks symmetry,
  depends_on acyclicity, cardinality 1 on matrix claim/evidence and
  gate artifact_class, plus closed-vocab `sh:in` enforcement. Both
  files verified as well-formed Turtle (1025 + 148 triples). The
  generator is the Rust crate at `tools/dagtoml-rdf` — no Python
  dependency; SHACL is hand-authored because the invariants are
  spec-stable, not ontology-derived.
- `reference/database/duckdb/`: DuckDB reference. Native ENUM types
  (PG-style), native `LIST<VARCHAR>` arrays (no JSON encoding for
  relation domain/range), native UUID/JSON/TIMESTAMPTZ. Schema is a
  port of the Postgres reference, not the SQLite one — DuckDB sits
  closer to PG in expressive power. Cycle detection is a recursive
  `CREATE VIEW` instead of a stored function (DuckDB has no
  PG-style stored functions). Loads on `duckdb >= 1.5` with the same
  15/23/30/29/54 row counts; all four invariant views fire correctly
  on the standard fixture (multi-producer, asymmetric depends_on,
  free-form discrimination). The `.duckdb` artifact is binary and
  intentionally NOT checked in — consumers regenerate via
  `tools/dagtoml-duckdb`.
- `tools/dagtoml-rdf/`: Rust generator (edition 2024) reading
  `core/ontology.toml` + `profiles/agent-assurance/ontology.toml` +
  every `*-kind.toml` and emitting `reference/database/rdf/schema.ttl`.
  Subcommand `dagtoml-rdf verify -o <ttl>` re-parses the artifact
  with `oxttl` to confirm well-formedness. Single binary, no Python
  in any code path. Build: `cargo build --release -p dagtoml-rdf`.
- `tools/dagtoml-rdf-go/` + `tools/dagtoml-duckdb-go/`: Go counterparts
  of the Rust tools. Same logic, same outputs (matching 1188-triple
  Turtle / 19/26/30/37/81 row counts). The Go RDF generator uses
  `github.com/pelletier/go-toml/v2`; the Go DuckDB orchestrator has zero
  third-party deps. Both files explicitly do NOT `import "unsafe"`.
- `validators/check_safe_tools.sh`: CI gate enforcing that every Rust
  crate under `tools/` carries `#![forbid(unsafe_code)]` and no Go file
  under `tools/` imports `unsafe`. Wired into `.github/workflows/
  validate.yml` immediately after the manifest-drift step. Tested with
  injected violations in both languages — fails fast with a precise
  file:line citation.
- `tools/README.md`: documents the safety policy, lists current tools,
  and states that Python is supported as a third option but is no
  longer the default for new tooling.
- Both Rust crates (`tools/dagtoml-rdf` and `tools/dagtoml-duckdb`)
  now carry `#![forbid(unsafe_code)]` at the top of `src/main.rs`.
  Builds are warning-clean with the lint enforced.
- `reference/database/{postgres,sqlite,duckdb}/seed.sql` + MANIFEST
  counts resync: ontology now has 6 core `*-kind.toml` files (added
  `profile-descriptor`), a second `disclosure` profile (3 entities +
  4 vocabs + 3 kind files), and 4 new core vocabularies
  (`confidentiality`, `license`, `framework_profile_namespace`,
  `provenance.encryption.hash_is_over`). New canonical counts:
  19 / 26 / 30 / 37 / 81 (kind / entity / relation / vocab /
  allowed-value rows). All three SQL reference DBs reload cleanly
  with the new counts; the RDF generator was updated to walk all
  profiles dynamically (no profile names hardcoded). The manifest
  drift script now also walks all profiles.
- `tools/dagtoml-duckdb/`: Rust orchestrator that wraps the `duckdb`
  CLI to build a `.duckdb` from the checked-in `duckdb/schema.sql` +
  `seed.sql` and verify the post-load row counts. Zero third-party
  dependencies (no libduckdb-sys; the engine lives in the
  consumer-installed CLI). Defaults the output stem to
  `agent_assurance` because DuckDB derives the catalog name from the
  file stem and a `dagtoml.duckdb` file would collide with the
  `dagtoml` schema name. Build: `cargo build --release -p dagtoml-duckdb`.
- `spec.md §11`: optional root-level `[provenance]` table for DAG-TOML
  files that are generated from a separate source artifact. When
  present it MUST carry `source_path`, `source_sha256`, and
  `source_bytes`; validators recognising the table MUST recompute the
  SHA-256 and byte length of the referenced file and fail on mismatch.
- `validators/validate_provenance.py`: the reference validator for the
  new `[provenance]` table. Walks each TOML it is handed, treats a
  missing `[provenance]` as silent PASS, and on a present table
  enforces the SHA-256 / byte-length binding described in `spec.md §11`.
  Rejects absolute `source_path` values and rejects relative paths
  that resolve outside the repo root (containment check, per SPEC §11).
- `validators/validate_rollback_plan.py`: closure check for the
  `rollback-plan` kind's `trigger_kind` enum. The hard invariant in
  `profiles/agent-assurance/rollback-plan-kind.toml` requires every
  `[[triggers]].trigger_kind` value to come from the profile ontology's
  declared vocabulary; that rule was previously not enforced by
  `validate_ijb_conformance.py` because instance-file rules only
  inspect ID-shaped strings and declared predicate values. The new
  validator closes that gap.
- `skills/convert-md-to-dag/`: authoring skill that produces a governed
  DAG-TOML package (implementation-dag, contract-declaration,
  readiness-gate, traceability, threat-model, rollback-plan) from a
  source Markdown file. Every generated TOML includes a `[provenance]`
  table that binds the package to the originating Markdown via the
  `spec.md §11` SHA-256 contract. New top-level `skills/` directory
  documented in `README.md`.
- `validators/validate_code_symbols.py` (experimental): sqry-backed
  symbol existence check for Rust, Go, TypeScript, and Java
  traceability entries. Not yet a CI gate (sqry install in CI is
  unpinned); see `docs/language-validators.md`.
- `examples/language-validation/`: cross-language traceability fixture
  used by `validate_code_symbols.py`, plus minimal Rust, Go,
  TypeScript, and Java source stubs. Validated structurally by CI
  (path-existence + IJB conformance) and protected from symbol drift
  by a grep-level CI check.
- `docs/language-validators.md`: companion doc describing the
  experimental sqry-backed code-symbol validator and what would have
  to land before it becomes a required CI job.
- Three new `trigger_kind` values in the profile ontology vocabulary:
  `validator_failure`, `missing_evidence`, `manual_override`. These
  cover spec-authoring and audit-flow rollback triggers where the
  trigger is a tooling outcome rather than a runtime metric.
- CI: `.github/workflows/validate.yml` now also IJB-validates every
  TOML under `skills/convert-md-to-dag/` and
  `examples/language-validation/`, enforces the `[provenance]`
  binding (`validate_provenance.py`) on every file with a
  `[provenance]` table, enforces the rollback-plan `trigger_kind`
  closure on both the minimal example and the skill instance, and
  fails if any language fixture loses a declared symbol name.

### Changed

- **SPEC §13 — three independent-review blockers closed (r1 fix
  commit; Codex r1 findings F1/F2/F3 + the deeper §2.4 contradiction
  Claude surfaced during fix-plan synthesis).**
  - **F1 (high) — §13.3 cited a nonexistent normative file.**
    `spec.md:1324-1327` (commit `27c1020`) stated the full grant
    sub-table schema was "declared by the
    `core/kind-descriptor-kind.toml` descriptor's
    `[kind.capability_envelope]` schema". That file does not exist
    and §2.4 (`spec.md:128-134`) explicitly states "tooling MUST
    NOT require a `kind-descriptor-kind.toml` to exist." The §13.3
    sentence is rewritten to name the actual normative surfaces
    jointly: the closed `capability_envelope.domain` vocabulary in
    `core/ontology.toml`, the per-domain shape checks in
    `validators/validate_abstraction_class.py`, and the §13.3 prose
    itself, with an explicit cross-reference to §2.4's
    recursion-stop rule.
  - **F2 (medium) — §13.3 prose / validator syntax mismatch on
    domain denial.** `spec.md:1268-1270` (commit `27c1020`) said
    "Each domain is either denied entirely (`false`) or scoped via
    a sub-table." The validator rejects any top-level domain value
    that is not a sub-table
    (`validators/validate_abstraction_class.py:300-310`), and the
    worked example
    (`profiles/cost/cost-record-kind.toml:300-327`) uses the
    `denied = true` sub-table form on every denied domain. Prose
    is corrected to: "Each domain is a sub-table — denied via
    `denied = true` or scoped via fields that constrain the
    grant." Missing-domain fail-closed semantics are preserved by
    `spec.md:1305-1307` (the §13.3 worked example) and the §13.9
    "Missing-domain = denied" bullet.
  - **F3 (medium) — §13.9 forbade signing-tier composition,
    contradicting §13.5's scope-out.** `spec.md:1470-1472` (commit
    `27c1020`) read: "Mix the technical-tier and legal-tier
    signatures on the same artefact. Either tier carries the
    closure root; both is declared posture, not engineering."
    §13.5 (`spec.md:1363-1366`) explicitly defers signing-tier
    selection to profile/runtime, and §12.5 scopes signing-envelope
    format to profiles/RUNTIME-SPEC. Mixed-tier rules are a
    signing-profile policy, not a capability-envelope
    papering-over mechanism. The bullet is deleted; the remaining
    three §13.9 bullets (re-sign under unchanged closure_root after
    envelope widening; treating missing domain as implicit grant;
    encoding capability declarations outside
    `[kind.capability_envelope]`) are all capability-envelope
    papering-over mechanisms and structurally complete for §13.9's
    actual scope.
  - Persistent review evidence:
    `docs/reviews/2026-05-23-spec-13-abstraction-class/codex-review.md`
    (Codex r1 — original blockers); `.../raw_findings/grok.md`
    (Grok r1 — methodology-split unconditional approval);
    `.../raw_findings/codex-fix-plan-r1.md` (Codex pre-implementation
    fix-plan review — `UNCONDITIONAL APPROVAL of fix plan`).
    Per ISS-001 (initiator-self-approval discipline), the merge gate
    is the r2 reviewer verdicts on this commit, not initiator
    adjudication.
- README stability table: schema, profile, and ontology versions are
  marked `Release candidate` until the first public release tag, per
  `GOVERNANCE.md`. The earlier `Stable` label was inconsistent with
  the still-private repository state.
- `spec.md` header status changed from `stable` to
  `release candidate (pending first public release tag)` to match the
  README stability table and the governance text. The label flips back
  to `stable` when the first public tag is cut.
- `examples/minimal-adapter-contract.toml` and the matching
  kind-descriptor block in
  `profiles/agent-assurance/adapter-contract-kind.toml` use
  `example-vendor:red_team_review@1` instead of the previous
  vendor-specific identifier. The example is illustrative; the
  string format is unchanged.
- `skills/convert-md-to-dag/traceability.toml`: the two
  provenance-related audit tests now invoke
  `validate_provenance.py` directly (digest + byte-length binding)
  instead of grepping for the presence of `source_hash` / a
  `[provenance]` header. Test IDs renamed accordingly
  (`source_hash_present` → `source_hash_binds`,
  `all_toml_files_cite_source` → `all_toml_files_bind_source`).

- Optional `[meta].docs` convention for DAG-TOML files and kind
  descriptors. The field points agents and tools at the canonical human
  specification or descriptor URL, but validators MUST NOT require
  network access to read it.
- Compact field reference at `docs/field-reference.md`, covering root
  metadata, core kinds, Agent Assurance Profile kinds, validator
  coverage, and the "what vs how" boundary between DAG-TOML and
  runtimes.
- IJB conformance CI loop extended to the five new profile-kind
  examples (`minimal-adapter-contract`, `minimal-adapter-registry-binding`,
  `minimal-assertion-bundle`, `minimal-assertion-log-record`,
  `minimal-gate-decision`). The validator's instance-file rules 5–6 only
  inspect strings that appear under an `id =` key or under a key that
  matches a declared ontology predicate (see
  `validators/validate_ijb_conformance.py` `validate_instance.walk`);
  for the new examples that surface is small (one `id` field across the
  five files at the time of this entry), so the practical effect today is
  to lock the structural shape of those files into CI rather than to
  resolve a large set of entity prefixes. The shape gate matters: any
  future content that introduces a `PREFIX:slug`-shaped token under a
  validated key, or a non-conforming `units.<id>` table key, will now
  fail the build. Previously CI only parsed these files as TOML.
- `taplo lint` CI step (pinned to Taplo `0.10.0`) for stricter TOML
  syntax / duplicate-key checks than Python's `tomllib` performs. New
  repo-root `.taplo.toml` declares the include/exclude file set;
  formatter rules are intentionally not enforced from this config.
- `requirements.txt` pinning `networkx>=3.0,<4`. CI installs it via
  `pip install -r requirements.txt`. `validators/validate_implementation_dag.py`
  now uses `networkx.simple_cycles` and `networkx.topological_sort` in
  place of the previous hand-rolled DFS for cycle detection and
  node-weighted longest-path (critical-path LOC) computation. Behaviour
  on the canonical example is preserved; reported cycle paths now use
  the canonical rotation so the same cycle reported from a different
  entry point dedupes deterministically.
- Deployment-tier bundles under `profiles/agent-assurance/tiers/` as
  five self-contained `contract-declaration` instances (`solo.toml`,
  `team.toml`, `group.toml`, `organization.toml`,
  `enterprise.toml`) plus a README documenting the
  solo ⊂ team ⊂ group ⊂ organization ⊂ enterprise ladder. No new
  `template_kind`; each tier file is a valid `contract-declaration`
  per the live kind schema.
- Five new Agent Assurance Profile `template_kind` values for the
  adapter / validation engine layer:
  - `adapter-contract` — declares a pure-function adapter that
    converts raw tool output into canonical IJB assertions, with
    declared runtime policies and conformance fixture references.
    Kind descriptor at
    `profiles/agent-assurance/adapter-contract-kind.toml`; example at
    `examples/minimal-adapter-contract.toml`.
  - `assertion-bundle` — sealed output of one adapter run as an
    ordered list of canonical-grammar assertion lines with
    provenance. Kind descriptor at
    `profiles/agent-assurance/assertion-bundle-kind.toml`; example at
    `examples/minimal-assertion-bundle.toml`.
  - `gate-decision` — mechanical pass/fail outcome of evaluating
    declared constraints against cited bundles. No editorialization
    surface. Verdict is a closed two-value enum; overrides are
    recorded as separate signed observations and do not toggle the
    verdict. Kind descriptor at
    `profiles/agent-assurance/gate-decision-kind.toml`; example at
    `examples/minimal-gate-decision.toml`.
  - `assertion-log-record` — one append-only log record citing an
    assertion bundle. Storage-agnostic; not git-coupled; not
    CI-coupled. Cross-record monotonicity and signature verification
    are explicitly deferred to RUNTIME-SPEC. Kind descriptor at
    `profiles/agent-assurance/assertion-log-record-kind.toml`;
    example at `examples/minimal-assertion-log-record.toml`.
  - `adapter-registry-binding` — declares how an adapter reference
    is resolved by an operator, with pluggable scheme (`file`,
    `https`, `oci`, `ipfs`, extensible) gated by trust anchor and
    policy constraint citations. Kind descriptor at
    `profiles/agent-assurance/adapter-registry-binding-kind.toml`;
    example at `examples/minimal-adapter-registry-binding.toml`.
- Eighteen new `[[attribute_vocabularies]]` entries in
  `profiles/agent-assurance/ontology.toml` declaring closed value
  sets for the new kinds: `runtime_kind`, `runtime_network_policy`,
  `runtime_clock_policy`, `input_hash_method`, `adapter_id_derivation`,
  `gate_decision_verdict`, `evidence_root_algorithm`,
  `record_signature_algorithm`, `record_hash_algorithm`,
  `record_canonical_form`, `registry_scheme`, `adapter_ref_syntax`,
  `signer_class`, `authority_role`, `severity_tier`, `autonomy_tier`,
  `override_decision_method`, `override_rule_operator`.
- Scope discipline: every new kind descriptor carries an explicit
  "validator MUST NOT" invariant naming the cross-document,
  cryptographic, and runtime behaviors that are out of scope for
  SPEC-LAYER validation (deferred to a sibling RUNTIME-SPEC).
- Initial specification publication candidate.
- Kind-descriptor pattern: each `template_kind` ships as a
  `*-kind.toml` file in `core/` or `profiles/agent-assurance/` carrying
  prose, required fields, hard-invariant pointers, and worked-example
  pointers in one machine-readable document.
- Reference validator `validators/validate_kind_descriptor.py` for the
  kind-descriptor template_kind itself.
- `LICENSE` (Apache-2.0).
- `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`.
- `.github/workflows/validate.yml` running reference validators on every
  push and pull request.
- Profile-kind minimal examples: `minimal-spec-contract.toml`,
  `minimal-threat-model.toml`, `minimal-smoke-validation.toml`,
  `minimal-rollback-plan.toml`.
- Non-normative architecture overview at `docs/architecture.md`
  describing how DAG-TOML relates to validators, per-repository
  runtimes, fleet control planes, and consumer tooling, and where the
  boundary between spec and runtime falls. Linked from `README.md`.
- IJB substrate integration. The "It's Just Business" framework ships
  under `foundations/ijb/` as relicensed (Apache-2.0) reference
  material: six-primitive definitions
  (`foundations/ijb/primitives.md`), canonical assertion grammar
  (`foundations/ijb/canonical-assertion-grammar.md`), FCO-IM
  integration notes, and worked examples. Every block in
  `core/ontology.toml` and `profiles/agent-assurance/ontology.toml`
  now carries an `ijb_primitive` annotation (`thing` / `scope` /
  `path` / `observed` / `constraint` / `time`) plus, where IJB
  itself distinguishes, an `ijb_class` (`structural` | `instance`)
  or `ijb_constraint_type` (`structural` | `policy` | `observed`)
  qualifier. Every kind-descriptor block in `core/*-kind.toml` and
  `profiles/agent-assurance/*-kind.toml` (`[kind]`,
  `[[kind.required_fields]]`, `[[kind.required_sections]]`,
  `[[kind.hard_invariants]]`, `[[kind.example]]`,
  `[kind.relation_to_ontology]`) carries the same `ijb_*` annotation
  per the SPEC §10.2 kind-descriptor mapping. The mapping is
  normative in `spec.md §10` with prose support in
  `core/ontology.md §8` and a layering diagram in
  `docs/architecture.md §5`. A new structural validator,
  `validators/validate_ijb_conformance.py`, enforces:
  every ontology block declares the required `ijb_*` fields; every
  kind-descriptor block does the same, with value classes pinned to
  the SPEC §10.2 mapping (`[kind]` is `thing/structural`,
  `[[kind.required_fields|required_sections|hard_invariants]]` and
  `[kind.relation_to_ontology]` are `constraint/structural`, and
  `[[kind.example]]` is `observed`); every value is drawn from the
  closed primitive / class / constraint-type sets; and every entity
  prefix and relation predicate used in a conforming instance file
  resolves through the loaded ontologies to a primitive-typed
  structural declaration. The validator is wired into CI alongside
  the existing four, including a per-kind-descriptor pass. Every
  kind-descriptor also gains a matching `[[kind.hard_invariants]]`
  entry pointing at the new validator. Free-text reality-check
  forbidden-concept matching is documented as a deliberate v0.2.0
  deferral in SPEC §10.4.

### Changed

- Per-kind prose documents (`core/implementation-dag.md`,
  `core/traceability.md`, `core/review-readiness.md`,
  `profiles/agent-assurance/{spec-contract,threat-model,smoke-validation,rollback-plan}.md`)
  collapsed into the matching `*-kind.toml` descriptors. Cross-references
  in `README.md` and `spec.md` updated to point at the new files.

### Notes

- `schema_version = "0.1.0"` and `ontology_version = 1` (core);
  profile `ontology_version = 1`. Pre-publication policy applies:
  versions stay at these values regardless of intervening edits until
  the first public release.

### Removed

- The previously-planned JSON Schema layer under `schemas/` has been
  dropped from the published deliverables. The machine-readable
  contract lives in TOML — in the `*-kind.toml` descriptors and the
  ontology files — and the reference validators consume those
  declarations to enforce both structural and semantic rules. The
  `schemas/` directory is retained for future generated Taplo schemas
  (an editor-tooling-only artifact derived from the kind descriptors,
  not authored by hand). See `spec.md §9` and `schemas/README.md`.
