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
9. If `llm` / `llm-cli-gateway` is available, request at least three
   model reviews before finalizing. If unavailable, record the tool
   absence as a review blocker instead of pretending the gate passed.

## Multi-LLM Review Command

Use this command shape when the local gateway exists:

```sh
llm review \
  --files "implementation_dag.toml,contract_declaration.toml,review_readiness.toml,traceability.toml,threat_model.toml,rollback_plan.toml" \
  --models "claude-3.5-sonnet,gpt-4o,grok-3" \
  --criteria "review_readiness.toml"
```

The final package must either cite review evidence from at least three
different models or keep the multi-LLM gate blocked with a concrete
reason.
