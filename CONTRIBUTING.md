# Contributing to DAG-TOML

This repository is the public specification for the DAG-TOML format and
the Agent Assurance Profile. Contributions are welcome when they make the
specification clearer, more consistent, easier to validate, or easier to
implement.

## Fast Path

1. Search existing issues and pull requests.
2. Open the most specific issue template for the change you want.
3. Keep the proposal small: describe the problem, the affected files, and
   the smallest compatible fix.
4. Open a pull request that references the issue and runs the validators.

Trivial typo fixes may go straight to a pull request. Any semantic
change should start with an issue.

## Good Issues

Open an issue for:

- Contradictory or ambiguous normative language.
- Missing edge cases in the specification.
- Reference-validator behavior that disagrees with the spec.
- Example files that are invalid, incomplete, or misleading.
- Profile proposals that extend the ontology without changing existing
  semantics.

Security findings belong in [SECURITY.md](SECURITY.md), not public
issues.

## Spec Change Process

A specification pull request must:

- Reference an issue that states the user-visible problem.
- Update affected prose and matching `*-kind.toml` descriptors together.
- Update `core/ontology.toml` or
  `profiles/agent-assurance/ontology.toml` when relation vocabulary or
  attribute values change.
- Add or update at least one example when the file shape changes.
- Update [CHANGELOG.md](CHANGELOG.md) under `[Unreleased]`.
- Pass the reference validators.

Material changes require maintainer review. Breaking changes require a
major schema-version bump and a migration note.

## Review Discipline

These two disciplines apply to every contributor (human or agent) and
to every spec-surface change. They are enforced by convention, not by
new infrastructure — the mechanisms already exist; the rule is to
follow them.

### 1. No initiator self-approval

When a contributor authors a change to `spec.md`, `core/`,
`profiles/`, `validators/`, or any tracked DAG-TOML document, the
contributor MUST NOT also issue the approving terminal verdict.
Approval comes from independent reviewers per the workflow at
[`tools/review-request-dag.toml`](tools/review-request-dag.toml).
`[policy.approval]` in that file enumerates the
`forbidden_approval_bases` (stated intent, plan-compliance claims,
"should be fixed" language) and the `required_approval_bases`
(inspected code, executed tests with output, inspected docs,
persisted review evidence). Persisted review evidence lives under
[`docs/reviews/<session-id>/`](docs/reviews/). The full audit trail
of a worked review session, including a round-1 blocker that
self-approval would have shipped, is at
`docs/reviews/2026-05-24-tooling-sweep-and-closure-root-sentinels/`
and its r2 follow-up. See
[ISS-001](docs/issues/2026-05-23-iss-001-self-approval-discipline.md)
for the issue history.

### 2. Spec-reserved-kind files MUST land with `closure_root` in the same commit

Any commit that adds or modifies a `[meta].template_kind` field
declaring a spec-reserved kind (one of the kinds declared by
`core/*-kind.toml` or by a spec-reserved profile's `*-kind.toml`, or the
meta kinds `kind-descriptor` / `ontology`) MUST also ensure the
file's root-level `closure_root` is present and correct in the same
commit. Per SPEC §12.11, self-contained documents emit the canonical
empty-closure sentinel
`sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

Run the validator locally before `git commit`:

```sh
python3 validators/validate_closure_root.py --discover . --exclude examples/negative
```

Do not commit if it is red. The same validator runs in CI
([`.github/workflows/validate.yml`](.github/workflows/validate.yml)
line ~180); a red CI is the symptom, not the prevention. See
[ISS-004](docs/issues/2026-05-24-iss-004-spec-reserved-kind-files-must-land-with-closure-root.md)
for the issue history and the worked counter-example.

### Agent-specific note on auto-memory

Agent-based contributors (e.g. provider-specific agent CLI, Codex, Gemini, Grok) may
use a per-session, host-specific auto-memory facility to remember
this discipline across sessions. Such facilities are NOT part of
the repo, NOT visible to other contributors or other agent CLIs,
and MUST NOT be cited as load-bearing safeguards. This file
([CONTRIBUTING.md](CONTRIBUTING.md)) is the contributor-visible
mechanism; auto-memory is an implementation-side convenience for
individual agents that complements it.

## Local Checks

Install the only Python dependency:

```sh
python3 -m pip install -r requirements.txt
```

Run the core validators:

```sh
python3 validators/validate_implementation_dag.py examples/minimal-implementation-dag.toml
python3 validators/validate_traceability.py examples/minimal-traceability.toml
python3 validators/validate_review_readiness.py examples/minimal-review-readiness/review_readiness.toml
python3 validators/validate_ijb_conformance.py core/ontology.toml
```

Run descriptor validation after editing any `*-kind.toml` file:

```sh
for f in core/*-kind.toml profiles/agent-assurance/*-kind.toml; do
  python3 validators/validate_kind_descriptor.py "$f" \
    --repo-root . --check-references-exist
done
```

Run the §12 closure-root gate after adding or modifying any spec-reserved
`[meta].template_kind` file (see Review Discipline section 2):

```sh
python3 validators/validate_closure_root.py --discover . --exclude examples/negative
```

Run the structural implementation-dag validator after editing any operational
DAG under `tools/` (ISS-005 — these are spec-reserved `implementation-dag`
files and must stay INV01-INV06 conformant; CI runs the same check across
Python + Rust + Go):

```sh
for f in tools/*-dag.toml; do
  python3 validators/validate_implementation_dag.py "$f"
done
```

CI runs the full matrix in [.github/workflows/validate.yml](.github/workflows/validate.yml).
CI also runs thirteen OSS security and quality scanners on every push and
pull request — in the order of the validate.yml "Coverage map" comment
block: `actionlint`, `zizmor`, `shellcheck`, `typos`, `ruff`, `bandit`,
`osv-scanner`, `gitleaks`, `cargo-audit`, `cargo-deny`, `govulncheck`,
`golangci-lint`, `lychee`. Each fails the build on any finding. CodeQL
advanced-setup covers `actions`, `go`, `python`, and `rust`. See
[SECURITY.md](SECURITY.md) for the full defensive posture and per-tool
role descriptions.

## Style

- Write normative requirements with `MUST`, `SHOULD`, or `MAY`.
- Keep examples minimal and executable by the validators.
- Prefer precise field names over prose-only explanations.
- Use kebab-case for `template_kind` values.
- Keep IDs short and prefixed (`REQ:`, `TEST:`, `ART:`, `OUT:`).
- Use two-space indentation in TOML arrays and tables.

## Licensing

By intentionally submitting a contribution, you agree that your
contribution is licensed under the Apache License, Version 2.0.
