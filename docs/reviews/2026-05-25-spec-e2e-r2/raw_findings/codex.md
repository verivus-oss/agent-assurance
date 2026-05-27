method

Fresh-context r2 byte review at repository HEAD `7782ade` for the S08 INV06-enforcement remediation. I read the required artifacts in order:

1. `docs/reviews/2026-05-25-spec-e2e-r2/verification_report.toml`
2. `docs/reviews/2026-05-25-spec-e2e/raw_findings/codex.md`
3. `validators/validate_gate_decision.py`
4. `tools/dagtoml-validate-rs/src/main.rs`
5. `tools/dagtoml-validate-go/main.go`
6. `profiles/agent-assurance/gate-decision-kind.toml`
7. `.github/workflows/validate.yml`
8. `git diff 1e0e155..7782ade`
9. `tools/review-request-dag.toml` `[policy.*]`

finding

S08.1 is not fully closed: `python3 validators/validate_gate_decision.py --help` does not print a usage/help line citing `INV01..INV06`, contrary to the verification report's byte-level closure recipe at `docs/reviews/2026-05-25-spec-e2e-r2/verification_report.toml:58`. The validator's docstring contains `INV01..INV06` at `validators/validate_gate_decision.py:2-4`, but the CLI passes only `__doc__.splitlines()[0]` to argparse at `validators/validate_gate_decision.py:259`, so the observed help output is:

```text
usage: validate_gate_decision.py [-h] [--repo-root REPO_ROOT]
                                 paths [paths ...]

Validate a gate-decision instance against

positional arguments:
  paths                 Gate-decision TOML file(s) to validate.
```

That is an exact closure failure for S08.1. It is not an INV06 predicate failure: the enforcement itself is present and works across Python, Rust, and Go.

closure notes

S08.1: partial. `validators/validate_gate_decision.py` exists and compiles. The source contains the required rejection predicate as `same_provider or same_family` at `validators/validate_gate_decision.py:232-253`. The `--help` output does not cite `INV01..INV06`, as shown above.

S08.2: closed. Running the two positive examples individually produced:

```text
GATE-DECISION VALIDATION PASSED (1 file checked; INV01..INV06 enforced).
GATE-DECISION VALIDATION PASSED (1 file checked; INV01..INV06 enforced).
```

S08.3: closed. I constructed the two r1 negative variants in `/tmp/inv06-r2-codex/neg-same-provider.toml` and `/tmp/inv06-r2-codex/neg-same-family.toml`. Python rejected both with exit status 1 and messages naming `INV06`, the exact equality, and the required wording that same-provider/different-family and different-provider/same-family both fail INV06.

S08.4: closed. `cargo build --release --locked` in `tools/dagtoml-validate-rs` succeeded with only two dead-code warnings. Rust declares `Mode::GateDecision` at `tools/dagtoml-validate-rs/src/main.rs:48-57`, parses `--mode gate-decision` at `tools/dagtoml-validate-rs/src/main.rs:80-89`, routes auto-mode `template_kind = "gate-decision"` at `tools/dagtoml-validate-rs/src/main.rs:1310-1323`, and explicit gate-decision mode at `tools/dagtoml-validate-rs/src/main.rs:1332-1334`. The INV06 rejection logic uses `same_provider || same_family` at `tools/dagtoml-validate-rs/src/main.rs:955-979`.

S08.5: closed. `go build -o /tmp/dagtoml-validate-go ./...` in `tools/dagtoml-validate-go` succeeded. Go declares `modeGateDecision` at `tools/dagtoml-validate-go/main.go:113-119`, parses `gate-decision` at `tools/dagtoml-validate-go/main.go:122-137`, routes auto-mode `template_kind = "gate-decision"` at `tools/dagtoml-validate-go/main.go:826-833`, and explicit mode at `tools/dagtoml-validate-go/main.go:839-840`. The INV06 rejection logic uses `sameProvider || sameFamily` at `tools/dagtoml-validate-go/main.go:1076-1092`.

S08.6: closed. Required three-way agreement check:

```text
PYTHON_POSITIVE
GATE-DECISION VALIDATION PASSED (2 files checked; INV01..INV06 enforced).

PYTHON_NEGATIVE
EXPECTED_FAIL python /tmp/inv06-r2-codex/neg-same-provider.toml status=1
EXPECTED_FAIL python /tmp/inv06-r2-codex/neg-same-family.toml status=1

RUST_POSITIVE_AUTO
DAGTOML VALIDATION PASSED (rust primary)
- files validated: 2
- profiles in resolution set: 3

RUST_NEGATIVE_GATE_MODE
EXPECTED_FAIL rust /tmp/inv06-r2-codex/neg-same-provider.toml status=1
EXPECTED_FAIL rust /tmp/inv06-r2-codex/neg-same-family.toml status=1

GO_POSITIVE_AUTO
DAGTOML VALIDATION PASSED (go primary)
- files validated: 2
- profiles in resolution set: 3

GO_NEGATIVE_GATE_MODE
EXPECTED_FAIL go /tmp/inv06-r2-codex/neg-same-provider.toml status=1
EXPECTED_FAIL go /tmp/inv06-r2-codex/neg-same-family.toml status=1
```

No validator accepted either negative variant.

S08.7: mostly closed from bytes and local execution; external CI status was not confirmable in this sandbox. The workflow step exists at `.github/workflows/validate.yml:346-448`. It runs the Python positive examples at `.github/workflows/validate.yml:363-368`, synthesizes both negative variants at `.github/workflows/validate.yml:373-414`, asserts Python negative failure at `.github/workflows/validate.yml:416-424`, and asserts Rust/Go positive plus negative behavior at `.github/workflows/validate.yml:432-448`. `gh run list --branch main --limit 1` failed locally with `error connecting to api.github.com`, so I did not independently confirm the remote CI run status.

S08.8: closed. `grep -nE 'enforced_by.*validate_gate_decision' profiles/agent-assurance/gate-decision-kind.toml` returns exactly five entries at lines 167, 174, 181, 188, and 202. `rg -n '\(planned\)|planned' profiles/agent-assurance/gate-decision-kind.toml` returned no matches.

regression check

S02 regression passed:

```text
ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 19 declared a §13 block).
```

S05 regression passed for the workflow's 26-file canonical primary sweep:

```text
RUST_CANONICAL
DAGTOML VALIDATION PASSED (rust primary)
- files validated: 26
- profiles in resolution set: 3
GO_CANONICAL
DAGTOML VALIDATION PASSED (go primary)
- files validated: 26
- profiles in resolution set: 3
```

S06 regression passed with installed conformance binaries:

```text
valid tests: 185 passed,  0 failed
invalid tests: 358 passed,  0 failed
valid tests: 185 passed,  0 failed
invalid tests: 371 passed,  0 failed
```

S10 local workflow-byte regression is covered by the inspected `.github/workflows/validate.yml` gate-decision step and the canonical primary sweep above. Remote GitHub status could not be checked because the environment could not connect to `api.github.com`.

Terminal verdict: concrete_unresolvable_blocker
Blocker: `docs/reviews/2026-05-25-spec-e2e-r2/verification_report.toml:58` requires `python3 validators/validate_gate_decision.py --help` to print a usage/help line citing `INV01..INV06`, but `validators/validate_gate_decision.py:259` passes only `__doc__.splitlines()[0]` to argparse; the observed help output stops at `Validate a gate-decision instance against` and does not cite `INV01..INV06`, so S08.1 is not closed even though the INV06 enforcement matrix itself now passes.
