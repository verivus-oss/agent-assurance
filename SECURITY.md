# Security policy

## Reporting a vulnerability

Email **security@verivus.com** with:

- A short description of the issue and the file(s) or rule(s) affected.
- A minimal reproduction if applicable (a TOML snippet that demonstrates
  the problem, plus the validator invocation that triggers or fails to
  trigger).
- Whether you believe the issue is exploitable in the spec text, the
  kind-descriptor TOMLs, the ontology files, or the reference
  validators.

We aim to acknowledge reports within five business days.

## Scope

This is a specification repository. The threat surface is narrower than
a runtime project, but the following classes of finding are in scope:

- **Specification ambiguities** that allow two conforming implementations
  to disagree about whether a document is valid.
- **Path-traversal or injection patterns** in published examples that
  could mislead automated tooling.
- **Reference validator bugs** (under `validators/`) that accept
  malformed input or reject conforming input, especially where the
  consequence is a false-positive review-readiness pass.
- **Kind-descriptor or ontology bugs** (under `core/` and
  `profiles/agent-assurance/`) where the declared structural contract
  diverges from the prose specification or the reference validators.

Out of scope:

- Vulnerabilities in third-party runtimes that consume DAG-TOML files
  (report to the runtime project).
- Aesthetic preferences about the spec.

## Defensive posture

This repository runs the following defensive controls:

- **Secret scanning + push protection** at the GitHub level.
- **Dependabot security updates** with a weekly cadence.
- **CodeQL advanced-setup** scans `actions`, `go`, `python`, and `rust`
  on every push, every pull request, and on a weekly schedule. See
  [`.github/workflows/codeql.yml`](.github/workflows/codeql.yml).
- **Branch protection ruleset** `main-branch-protection` enforces
  `non_fast_forward`, no `deletion`, and a pull-request rule that requires
  one approving review, `require_code_owner_review`,
  `required_review_thread_resolution`, `dismiss_stale_reviews_on_push`, and
  `allowed_merge_methods = ["merge"]`. Squash and rebase merging are also
  disabled at the repository level, so a merge commit is the only way a
  change reaches `main`.

  `required_linear_history` was removed on 2026-08-30, from this ruleset and
  from the branch protection that duplicated it. It forbids merge commits,
  and a merge commit is what keeps a cited commit resolvable: squash and
  rebase both discard the commits they land, so any evidence citing them
  dies at merge. Force-push and deletion protection are separate rules,
  `non_fast_forward` and `deletion`, and neither was touched. See the merge
  policy in [CONTRIBUTING.md](CONTRIBUTING.md) for the full reasoning.
- **`signing-approvers` team** holds `maintain` permission on this
  repository and reviews changes touching signing material.
- **Sigstore-signed release tags.** Annotated tags are signed with
  `gitsign`; the `v0.1.0` tag is the reference shape. GitHub's native
  tag-verification view shows "Unverified" because the sigstore root is
  not in GitHub's trust set; verify via `gitsign verify <tag>` against
  the public Rekor log.
- **OpenSSF Scorecard** publishes weekly; see the README badge for the
  current score.

### Thirteen OSS scanning tools in CI

`.github/workflows/validate.yml` runs the following scanners on every
push and pull request; each step fails the build on any finding. The
order and one-line role descriptions below are the verbatim "Coverage
map" comment block in `validate.yml` (lines 694-719):

- `actionlint` — GHA workflow correctness (broken expressions,
  deprecated APIs, shell-injection in `run:`)
- `zizmor` — GHA workflow security (impostor-commit, unpinned uses,
  excessive permissions)
- `shellcheck` — shell-script correctness for `validators/*.sh` and
  example witness scripts
- `typos` — source-code spellchecker; critical for spec repos (a
  misspelled ontology predicate is a silent semantic error)
- `ruff` — Python deep linter (security `S` rules, correctness,
  dead-code); defense-in-depth above bandit
- `bandit` — Python static security analysis of `validators/`
- `osv-scanner` — CVEs in `requirements.txt` + `Cargo.lock` + `go.sum`
  (complements Dependabot: catches transitive and advisory-DB-only
  entries Dependabot misses)
- `gitleaks` — secret leak detection in commits + working tree
  (replaces GHAS secret scanning)
- `cargo-audit` — RustSec advisory DB check for every `tools/*-rs`
- `cargo-deny` — Rust license policy + dep ban + advisories (catches
  license drift that audit doesn't)
- `govulncheck` — Go call-graph-aware vuln check for `tools/*-go`
- `golangci-lint` — Go meta-linter (gosec + staticcheck + errcheck +
  govet + ineffassign + unused)
- `lychee` — link rot across `spec.md`, README, `references.bib`

Every workflow action is SHA-pinned. Pip and cargo installs are
version-pinned; hash-pinning is on the roadmap and tracked in the
`chore/pip-hash-pinning` branch.

## Disclosure

We coordinate disclosure: the reporter, the maintainers, and (if the
finding affects published profiles) the profile owners agree on a
disclosure date. Default embargo is 30 days from acknowledgement; we
extend if a fix needs more time.

We credit reporters in `CHANGELOG.md` for the release that fixes the
finding, unless the reporter requests otherwise.
