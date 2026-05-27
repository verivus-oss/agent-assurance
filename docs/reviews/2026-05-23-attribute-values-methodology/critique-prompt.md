# Critique — an Opus consultant's proposal for resolving `MANIFEST.toml [counts].attribute_values`

You are dispatched to critique a proposal, not to approve it. Fresh / clean-context session. No prior memory.

## Context

The repo is `/srv/repos/external/verivus-oss/agent-assurance` at HEAD `99e18dba38ec3b4c6234b77bac7a87b0f2e6cdfc`.

A field in `reference/database/MANIFEST.toml [counts].attribute_values` has been the subject of disagreement: two prior reviewers verified it independently and produced different numbers (170 vs 99) using different filters on the same ontology bytes. They could not be reconciled without picking one reading over the other.

A third party — an Opus consultant — was then asked to investigate the evidence broadly and produce a single recommendation. They produced the report at:

  `docs/reviews/2026-05-23-attribute-values-methodology/raw_findings/opus.md`

OPEN AND READ THAT FILE FIRST. Then critique it.

## The proposal in brief (READ THE FULL REPORT, do not rely on this summary)

The Opus consultant recommends **option (E)**: split `[counts].attribute_values` into two unambiguously-named fields, add a producer-side Python validator that derives both from the ontology files and exits non-zero on drift, wire it into the existing `check_manifest_drift.sh`, and add a one-paragraph SPEC.md §10 normative-naming rule.

- `attribute_values_declared = 170` (sum of `len(values)` across every `[[attribute_vocabularies]]` block in core + every profile ontology)
- `attribute_values_closed = 99` (same sum, filtered to `extensible = false`)

The report also flags a much wider problem: **eight** mirror surfaces exist (`[counts]`, three `expected_seed_counts`, `expected_node_counts`, `expected_footer_counts`, two hardcoded `EXPECTED_COUNTS` in tools/), all but the four CI-gated block-counts are stale. A separate follow-up PR (out of scope of this proposal) would extend the drift script to gate every surface and delete the hardcoded mirrors.

## What I need from you

This is a critique, not an approval. The Opus consultant is fallible. Your job is to find what they missed, overclaimed, or got wrong. Be specific.

Produce a report with these sections:

### 1. Verification of the Opus report's evidence

Re-derive each load-bearing claim independently. Report `confirmed` / `refuted_with_evidence` / `unverifiable` for each, with file:line evidence and your own command output where applicable. Specifically:

- The 8-surface mirror table at Opus §2. Re-parse MANIFEST.toml and the two duckdb tools. Are the values they cite as "stale" actually stale? Are there mirror surfaces they missed?
- The historical `81 → 84 → 106 → 170` claim about how `attribute_values` was maintained. Walk `git log -p reference/database/MANIFEST.toml` yourself and confirm or refute.
- The "106 ≈ today's sqlite seed-row count of 109" claim. Re-count sqlite seed rows yourself.
- The "actual seed file row counts 74, 109, 109" line at Opus §2. Re-count for each engine.
- The two arithmetic errors Opus alleges in my structural-analysis §2. Re-derive the per-file value totals yourself.

### 2. Critique of the recommendation

For each of the four sub-edits in the Opus report (§4.1 MANIFEST split, §4.2 validator, §4.3 wire-in, §4.4 SPEC paragraph) — is it correct as written? What does it miss?

Specific things to consider, but go beyond:

- Are the two new field names (`attribute_values_declared`, `attribute_values_closed`) the right names? Would something else be clearer (`*_total` / `*_enforced`? `*_all` / `*_strict`?)? Would a third name be needed for "seed-row-count" given Opus says that's what historical maintenance actually tracked?
- The validator at §4.2 derives only the two ontology-aggregate numbers. Does it leave open the same "stale-seed-mirror" hole on the OTHER mirror surfaces that Opus flagged?
- The proposed SPEC §10 paragraph normatively rules that "mixing the two aggregates in one field is prohibited" — is this the right normative scope, or is it too broad / too narrow?
- The PR-splitting decision (immediate fix in scope, the broader mirror-rot is follow-up). Honest scoping, or kicking a can?
- The Opus report concedes 3 self-concerns. Are they the right 3? Did they miss any?

### 3. What you would do differently

Concrete counter-proposals. If you agree with Opus, say so plainly. If you disagree, propose alternative edits with specific file:line changes. **Do not produce a list of vague concerns; produce a specific alternative or admit the Opus version is correct.**

### 4. Decision matrix

For the spec maintainer reading this: assemble a short table of (option, what-it-buys, what-it-costs, residual-risk). Include Opus's recommendation alongside any of your alternatives.

### 5. Bottom line

A single sentence: "I [agree with / would modify / reject] the Opus recommendation; the maintainer should [exact action]."

Be specific. No prose-only conclusions. The user reads this directly and acts on it.

Begin.
