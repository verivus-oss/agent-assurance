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
order and one-line role descriptions below follow the "Coverage map"
comment block in `validate.yml`:

- `actionlint` — GHA workflow correctness (broken expressions,
  deprecated APIs, shell-injection in `run:`)
- `zizmor` — GHA workflow security (impostor-commit, unpinned uses,
  excessive permissions)
- `shellcheck` — shell-script correctness for `validators/*.sh` and
  example witness scripts
- `dagtoml-spell` - structured source and filename token checks against a
  pinned literal correction table, with typed data roles, source digests
  and explicit omissions. Replaces the spelling action present at
  `a3420ad83ab0758e389fca86dbdfb837e86df5bc`.
- `ruff` — Python deep linter (security `S` rules, correctness,
  dead-code); defense-in-depth above bandit
- `bandit` — Python static security analysis of `validators/`
- `osv-scanner` — CVEs in `requirements.txt` + `Cargo.lock` + `go.sum`
  (complements Dependabot: catches transitive and advisory-DB-only
  entries Dependabot misses)
- The native credential gate checks stored blobs throughout reachable Git
  history, including the HEAD tree, merge parents and deletion-only commits.
  Cold controls exercise declared provider candidates, rejected inputs and
  source identity failures. The exact four historical public-literal events
  remain the sole event exceptions; all other events fail. See
  `validators/CREDENTIALS.md` for the candidate contract and scan boundaries.
- `cargo-audit` - RustSec advisory DB check for every derived tools crate
- `cargo-deny` - Rust license, source, dependency ban and advisory policy
  over the same derived tooling manifest population
- `govulncheck` — Go call-graph-aware vuln check for `tools/*-go`
- `golangci-lint` — Go meta-linter (gosec + staticcheck + errcheck +
  govet + ineffassign + unused)
- `lychee` — link rot across `spec.md`, README, `references.bib`

Workflow actions are SHA-pinned. Python verification packages use version
and hash pins; Rust builds use checked-in Cargo.lock files.

The shared JSON codec replaces the wrapper from
`16d7d85f31a3071d56f4f8c34d99d1800ad5ce73` with explicit syntax validation
before native value decoding. Its cold controls reject standard JSON and
regex imports; [the codec contract](validators/JSON.md) names its boundaries.
Other reference-store cold imports remain inside the audit scope.

The source-inspection consumers use compile-only native syntax trees and
owned traversal, literal and regeneration helpers. The supplier and license
are recorded in `vendor-provenance/python-ast.toml`; the bounded interface
and retirement decisions are in `validators/SYNTAX-TREE.md`. Malformed source
diagnostics identify original bytes without retaining native parser source
coordinates. Unknown regeneration nodes fail before source emission. Cold
component controls cover the helper and current mutation selector, with
independent swallowed-import guard controls. Native compiler internals and
other entry points remain outside that component observation.

The authored record sites from `1691549990e81ac801fbbc611d1f7e31a36b5719`
use explicit carriers with [record component controls](validators/RECORDS.md).
This retires their dataclass dependency without widening the cold audit scope.

Current filesystem consumers from `4df544e0727fd881531b3b2fad716c36468bd996`
use [owned native path primitives](validators/PATHS.md), with explicit
containment and cold SQLite outcome controls. Authored random identifiers
use OS entropy with version/variant controls. External drivers and the wider
verification dependencies still require their own consumer audits.

Cold instruments from `c8590f56eb33205c7b540f2d959cc39b30dd718d` retain
attempted forbidden imports and require that population to remain empty.
Catching the audit exception cannot turn an attempt into a successful
boundary result. The guard-integrity instrument derives every tracked cold
runner and its literal forbidden-root population, checks successful controls,
then requires swallowed attempts to fail the final property in both modes.
It does not establish absence inside native dependencies.

The estate no-regex rule also covers dependencies, build and test tools,
and security scanners. The active scanner engines still require a consumer
audit and replacement; a successful scan is not evidence of compliance
with that rule. The link checker receives URLs selected by exact path and
host comparisons.

## Disclosure

We coordinate disclosure: the reporter, the maintainers, and (if the
finding affects published profiles) the profile owners agree on a
disclosure date. Default embargo is 30 days from acknowledgement; we
extend if a fix needs more time.

We credit reporters in `CHANGELOG.md` for the release that fixes the
finding, unless the reporter requests otherwise.
