---
name: convert-md-to-dag
description: Convert an existing Markdown process, skill, or workflow guide into a governed DAG-TOML package using the DAG-TOML specification and Agent Assurance Profile.
---

# Convert Markdown To DAG-TOML

Use this skill when a user provides a `.md` file and asks for a governed,
spec-compliant DAG-TOML package.

## Canonical Outputs

Generate TOML instance files using the current DAG-TOML shapes:

- `implementation_dag.toml` with `template_kind = "implementation-dag"`
- `contract_declaration.toml` with `template_kind = "contract-declaration"`
- `review_readiness.toml` with `template_kind = "readiness-gate"`
- `traceability.toml` with `template_kind = "traceability"`
- `threat_model.toml` with `template_kind = "threat-model"` when relevant
- `rollback_plan.toml` with `template_kind = "rollback-plan"`

Do not emit the older `[dag]` / `[[tasks]]` draft shape. Do not make
`threat_model.md`, `rollback_plan.md`, or `traceability.md` the canonical
artifacts; Markdown companions are optional summaries only.

## Required Provenance

Every generated TOML file MUST include a `[provenance]` table that
captures the originating Markdown file:

```toml
[provenance]
source_path        = "relative/or/absolute/source.md"
source_sha256      = "sha256:<hex-digest>"
source_bytes       = 12345
captured_at        = "YYYY-MM-DDTHH:MM:SSZ"
extraction_method  = "manual-analysis"
source_description = "Short description of the source Markdown."
```

The `traceability.toml` file MUST additionally cite the same path and
hash in `[meta].source_spec` and `[meta].source_hash`. If a hash cannot
be computed, stop and report the blocker instead of emitting unverifiable
provenance.

## Process

1. Read the entire Markdown source.
2. Compute and record the source Markdown SHA-256 hash and byte count.
3. Extract purpose, success criteria, constraints, edge cases, and
   implicit assumptions.
4. Design small implementation units with explicit `depends_on`,
   inverse `blocks`, artifact flow, and computed critical path.
5. Convert vague claims into refutable contracts and readiness gates.
6. Add Agent Assurance Profile artifacts when the conversion affects
   safety, security, operational correctness, or review governance.
7. Record traceability to the original Markdown path and hash in every
   TOML artifact's `[provenance]` table.
8. Run local validators.
9. If a multi-model gateway such as `llm-cli-gateway` is available,
   request at least three model reviews before finalizing. If
   unavailable, record the tool absence as a review blocker instead of
   pretending the gate passed.

## Multi-LLM Review Gate

When a multi-model gateway such as `llm-cli-gateway` is available, submit
the whole generated package for review:

- **Inputs:** every generated TOML file in the package.
- **Criteria:** the gates and blocking conditions declared in
  `review_readiness.toml`.
- **Reviewers:** at least three distinct models, preferring models from
  different vendors so that one vendor's blind spot cannot clear the gate
  on its own.

Do not hardcode model identifiers in this skill; they go stale. Resolve
the available models from the gateway at review time, and record the
exact identifiers that produced each review alongside the findings.

Each reviewer MUST check claims against the generated files themselves,
never against a summary of them. The final package must either cite
review evidence naming at least three distinct models, or keep the
multi-LLM gate blocked with a concrete reason.
