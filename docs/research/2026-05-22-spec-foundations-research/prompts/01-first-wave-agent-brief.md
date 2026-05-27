# First-wave agent brief — sent verbatim to Codex / Gemini / Grok

Each of Codex (`gpt-5.5`), Gemini (`gemini-3.1-pro-preview`), and Grok
(`grok-build`) received this same brief independently via the
`llm-cli-gateway` MCP server with the `exa` MCP enabled. None saw the
others' output. Minor wording differences existed across the three jobs
(Grok and Gemini's were slightly trimmed for token economy); the Codex
version is the longest and is reproduced first below, then the diffs.

Job IDs:

- Codex (3rd successful attempt after CLI-flag fixes): `1d0bcb23-8199-4015-850c-0dae2c9d163b`
- Gemini: `a484d116-043c-4dd4-9d5e-9e139b8829d9`
- Grok (2nd successful attempt after model-flag fix): `471c8ac0-9d02-404c-beea-a9f95c2e6410`

## Codex version (full)

```
You are doing INDEPENDENT external research using the `exa` MCP server (web_search_exa, web_search_advanced_exa, get_code_context_exa, deep_researcher_start/check). Use Exa extensively (10+ searches across different angles). Do NOT read any local repo.

CONTEXT (read once, don't quote back):
A public TOML-based specification called "DAG-TOML" describes how AI software-engineering agents plan, sequence, and prove work. It has three layers:
  1. Core DAG-TOML (implementation-dag, traceability, review-readiness templates)
  2. Agent Assurance Profile (spec-contract, threat-model, smoke-validation, rollback-plan, adapter-contract, assertion-bundle, assertion-log-record, gate-decision)
  3. IJB foundation — a meta-ontology with SIX PRIMITIVES: thing | scope | path | observed | constraint | time, plus class markers (structural vs instance). Every entity/relation/attribute carries `ijb_primitive` and `ijb_class`. Kind-descriptor (*-kind.toml) files follow KD1–KD3 rules.
No JSON Schema layer — TOML + Python validators enforce shape. Hard invariants like "blocks is inverse of depends_on", "each ART has exactly one producer", "critical_path is longest weighted path" are enforced in code.

RESEARCH QUESTIONS (use Exa hard on each):
1. IJB primitives prior art — precedents for a SIX-primitive ontology. Compare against BFO, DOLCE, SUMO, UFO, Bunge-Wand-Weber, FCO-IM, ORM/NIAM, situation/event calculus, ArchiMate, ARIS, REA, W3C PROV. What collapses or category errors does it risk?
2. TOML-based spec design — guidance and pitfalls when authoring a spec in TOML. What do Cargo, pyproject, Taplo teach? When does TOML break down? Schema evolution without JSON Schema?
3. Kind-descriptor / self-describing-schema patterns — JSON-LD contexts, SHACL, OpenAPI components, ProtoBuf descriptors, CUE, Dhall. What goes wrong with self-description? How to keep prose and machine-form aligned?
4. Agent assurance / AI agent governance specs — W3C PROV, in-toto, SLSA, SBOM, OpenSSF Scorecard, NIST AI RMF, ISO/IEC 42001, EU AI Act. Failure modes: over-attestation, evidence fatigue, gate gaming.
5. Spec-design failure modes — Hyrum's law, schema bloat, ontology drift, OWL/RDF over-expressivity, "rough consensus and running code", "two implementations" rule.
6. DAG-shaped traceability — cycle prevention, critical path in SE vs PERT/CPM, anti-patterns.

OUTPUT: 6 sections (~150–300 words each) with 3–6 cited URLs per section; "TOP RISKS" (5–8 bullets); "RECOMMENDATIONS" (5–8 bullets). Be skeptical and independent. ~2500–4000 words total.
```

## Gateway parameters used

- Codex: `model=latest`, `mcpServers=["exa"]`, `sandboxMode=read-only`,
  `idleTimeoutMs=1800000`
- Gemini: `model=latest`, `mcpServers=["exa"]`, `approvalMode=yolo`,
  `idleTimeoutMs=1800000`
- Grok: `model=latest`, `mcpServers=["exa"]`, `alwaysApprove=true`,
  `idleTimeoutMs=1800000`

## Failed attempts (preserved for diagnosis)

- Codex attempt 1 failed with `error: unexpected argument '--ask-for-approval'` — gateway emitted a flag the local Codex CLI doesn't accept. Removed `askForApproval`.
- Codex attempt 2 failed with `error: unexpected argument '--search'` — removed `search=true` parameter; Codex still has Exa via its own MCP config.
- Grok attempt 1 failed with `400 Bad Request: Model grok-build does not support parameter reasoningEffort.` — removed `effort: "high"`.

## Diffs in Gemini / Grok prompts vs Codex

Gemini's prompt was identical except missing the "(use 10+ searches across different angles)" emphasis. Grok's prompt was structurally identical but each section was compressed to 1–2 lines.
