# WP1 Validator Ports Review Prompt

Date: 2026-05-29 UTC

Independent read-only code review for WP1 in
`/srv/repos/external/verivus-oss/agent-assurance`.

Rules supplied to reviewers:

- Rust/Go validators are primary, Python is cross-check.
- No unsafe weakening.
- Validator/tooling/docs only; do not change kind semantics.
- CI must catch Rust/Go/Python disagreement and malformed negative fixtures.
- Negative fixtures must prove enforcement, not just parsing.

Intent supplied to reviewers:

- Port kind-descriptor, IJB, provenance source binding,
  implementation-dag, traceability, review-readiness, cost-record,
  rollback-plan, and SPEC §13 abstraction/capability checks to Rust+Go.
- Expand `validate.yml` primary sweep.
- Add `examples/negative`.
- Update docs.

Local gate evidence supplied to reviewers:

- `taplo lint` and TOML parse passed.
- `validators/check_safe_tools.sh` passed.
- `validators/check_manifest_drift.sh` and
  `validators/check_attribute_values.py` passed.
- `make toml-conformance-all` passed.
- Rust/Go 49-file primary sweep passed.
- Python cross-checks passed.
- Negative fixtures were rejected by Rust, Go, and Python.
- `cargo fmt/clippy/test` and `go build/vet/golangci-lint` passed.
