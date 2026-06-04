# WP1 Validator Ports Verification Report

Date: 2026-05-29 UTC

This report is the corrective-program specification for the follow-up
independent review round. Reviewers must verify claims against the
code, workflow, docs, examples, and persisted review evidence. Do not
accept this report or any agent summary as approval evidence by itself.

## Review Target

Branch: `fix/2026-05-29-five-weaknesses`

Commit under review:

```text
4f48edd5167e527e482f496925411ccd99501d8e
feat: port validator coverage to primary tools
```

Parent context:

```text
1230558 chore: move root scratch files local-only
715bb2d ci(codeql): move write permissions to job level
```

Diff command reviewers should run:

```sh
git show --stat --patch 4f48edd5167e527e482f496925411ccd99501d8e
```

Changed files in `4f48edd5167e527e482f496925411ccd99501d8e`:

```text
.github/workflows/validate.yml
AGENTS.md
CHANGELOG.md
README.md
docs/language-validators.md
docs/reviews/2026-05-29-wp1-validator-ports/gateway-dispatch.md
docs/reviews/2026-05-29-wp1-validator-ports/gemini-review.md
docs/reviews/2026-05-29-wp1-validator-ports/grok-review.md
docs/reviews/2026-05-29-wp1-validator-ports/review_prompt.md
docs/reviews/2026-05-29-wp1-validator-ports/terminal_decision.toml
examples/negative/abstraction-class-unknown-domain.toml
examples/negative/cost-record-bad-dimension.toml
examples/negative/implementation-dag-bad-critical-path.toml
examples/negative/kind-descriptor-name-mismatch.toml
examples/negative/ontology-wrong-ijb-primitive.toml
examples/negative/provenance-wrong-source-sha.toml
examples/negative/review-readiness-missing-gate-target.toml
examples/negative/rollback-plan-bad-trigger-kind.toml
examples/negative/traceability-missing-requirement-target.toml
tools/dagtoml-validate-go/main.go
tools/dagtoml-validate-rs/Cargo.toml
tools/dagtoml-validate-rs/src/main.rs
```

## Required Review Questions

Reviewers must answer these questions from inspected code and command
evidence:

1. Do Rust and Go primary validators actually implement the newly ported
   surfaces instead of merely parsing them?
2. Does `.github/workflows/validate.yml` run Rust and Go on the relevant
   canonical examples, tiers, profile descriptors, ontologies, and kind
   descriptors?
3. Do the new negative fixtures prove enforcement for each ported
   surface?
4. Do Python validators remain as cross-checks rather than being removed
   or downgraded?
5. Was the safe-tooling posture preserved (`#![forbid(unsafe_code)]` in
   Rust tools and no Go `unsafe` imports)?
6. Did the change avoid spec/kind semantic drift, limiting itself to
   validators, workflow, examples/negative, and docs?
7. Is the persisted review evidence complete enough to satisfy the
   repository's self-approval discipline?

## Verification Commands Already Run

These commands were run locally after the WP1 changes. Reviewers should
rerun or selectively verify them rather than accepting this list as
proof.

```sh
taplo lint
python3 -c 'import pathlib, tomllib; files=[p for p in pathlib.Path(".").rglob("*.toml") if not any(x.startswith(".") for x in p.parts)]; [tomllib.loads(p.read_text()) for p in files]; print(f"parsed OK: {len(files)} files")'
bash validators/check_safe_tools.sh
bash validators/check_manifest_drift.sh
python3 validators/check_attribute_values.py
make toml-conformance-all
```

Observed output excerpts:

```text
parsed OK: 185 files

OK — all tools/ are safe (forbid(unsafe_code) Rust + unsafe-free Go)

COUNT-MIRROR OK — every surface agrees with reality.

toml-test ... Go:
  valid tests: 185 passed,  0 failed
invalid tests: 358 passed,  0 failed

toml-test ... Rust:
  valid tests: 185 passed,  0 failed
invalid tests: 371 passed,  0 failed
```

Primary validator sweep:

```sh
targets=(
  profiles/agent-assurance/PROFILE.toml
  profiles/disclosure/PROFILE.toml
  profiles/cost/PROFILE.toml
  core/ontology.toml
  profiles/agent-assurance/ontology.toml
  profiles/disclosure/ontology.toml
  profiles/cost/ontology.toml
  core/*-kind.toml
  profiles/agent-assurance/*-kind.toml
  profiles/disclosure/*-kind.toml
  profiles/cost/*-kind.toml
  examples/minimal-disclosure-attestation.toml
  examples/minimal-redaction-manifest.toml
  examples/minimal-selective-disclosure-proof.toml
  examples/minimal-cost-record.toml
  examples/minimal-implementation-dag.toml
  examples/minimal-traceability.toml
  examples/minimal-spec-contract.toml
  examples/minimal-threat-model.toml
  examples/minimal-smoke-validation.toml
  examples/minimal-rollback-plan.toml
  examples/minimal-adapter-contract.toml
  examples/minimal-adapter-registry-binding.toml
  examples/minimal-assertion-bundle.toml
  examples/minimal-assertion-log-record.toml
  examples/minimal-gate-decision.toml
  examples/minimal-review-readiness/review_readiness.toml
  examples/minimal-review-readiness/contract_declaration.toml
  examples/minimal-review-readiness/evidence_matrix.toml
  profiles/agent-assurance/tiers/solo.toml
  profiles/agent-assurance/tiers/team.toml
  profiles/agent-assurance/tiers/group.toml
  profiles/agent-assurance/tiers/organization.toml
  profiles/agent-assurance/tiers/enterprise.toml
)
tools/dagtoml-validate-rs/target/debug/dagtoml-validate-rs --repo-root . "${targets[@]}"
tools/dagtoml-validate-go/dagtoml-validate-go --repo-root . "${targets[@]}"
```

Observed output:

```text
DAGTOML VALIDATION PASSED (rust primary)
- files validated: 49
- profiles in resolution set: 3

DAGTOML VALIDATION PASSED (go primary)
- files validated: 49
- profiles in resolution set: 3
```

Python cross-check excerpts:

```text
PROFILE DESCRIPTOR VALIDATION PASSED
DISCLOSURE VALIDATION PASSED
COST-RECORD VALIDATION PASSED (1 file(s)).
ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 19 declared a §13 block).
IMPLEMENTATION DAG VALIDATION PASSED
TRACEABILITY VALIDATION PASSED
REVIEW READINESS VALIDATION PASSED
ROLLBACK PLAN VALIDATION PASSED
GATE-DECISION VALIDATION PASSED (2 files checked; INV01..INV06 enforced).
CLOSURE-ROOT VALIDATION PASSED (70 file(s)).
```

Negative fixture agreement was run for Rust, Go, and Python over:

```text
examples/negative/kind-descriptor-name-mismatch.toml
examples/negative/ontology-wrong-ijb-primitive.toml
examples/negative/provenance-wrong-source-sha.toml
examples/negative/implementation-dag-bad-critical-path.toml
examples/negative/traceability-missing-requirement-target.toml
examples/negative/review-readiness-missing-gate-target.toml
examples/negative/cost-record-bad-dimension.toml
examples/negative/rollback-plan-bad-trigger-kind.toml
examples/negative/abstraction-class-unknown-domain.toml
```

Observed result for every fixture:

```text
ok: <implementation/surface> rejected
```

Toolchain checks:

```sh
for dir in tools/dagtoml-validate-go tools/dagtoml-duckdb-go tools/dagtoml-rdf-go; do
  (cd "$dir" && go build ./... && go vet ./... && /home/werner/go/bin/golangci-lint run ./...)
done

for dir in tools/dagtoml-validate-rs tools/toml-test-decode-rs tools/dagtoml-duckdb tools/dagtoml-rdf; do
  (cd "$dir" && cargo fmt --check && cargo clippy -- -D warnings && cargo test)
done
```

Observed output excerpts:

```text
0 issues.
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
```

Other workflow-equivalent checks:

```text
no banned markers found
no internal source-tree paths found
all language fixtures contain declared symbols
all canonical examples present
```

## Existing Review Evidence

Reviewers must inspect these files and decide whether they are
sufficient. They are not allowed to accept the terminal decision without
checking the code/tests/docs themselves.

```text
docs/reviews/2026-05-29-wp1-validator-ports/review_prompt.md
docs/reviews/2026-05-29-wp1-validator-ports/gemini-review.md
docs/reviews/2026-05-29-wp1-validator-ports/grok-review.md
docs/reviews/2026-05-29-wp1-validator-ports/gateway-dispatch.md
docs/reviews/2026-05-29-wp1-validator-ports/terminal_decision.toml
```

## Known Environment State

`git status --short --untracked-files=all` after commit shows only
unrelated untracked files, including `.wrangler/cache/pages.json`,
draft `docs/posts/*`, and an older untracked
`docs/reviews/2026-05-27-agentskills-profile-pitch/` bundle. These are
outside the WP1 commit under review.
