# Final review — count-mirror cleanup + issue ledger (commits 9996826 + 5b1eca1)

You are an independent reviewer dispatched per the workflow at
`tools/review-request-dag.toml`. Fresh / clean-context session. No
prior memory of this artefact.

## Context

A multi-session investigation resolved a methodology disagreement
about `MANIFEST.toml [counts].attribute_values` (170 vs 99). The
resolution split the field into two named subfields, added a new
producer-side validator that gates every count-mirror surface in
the repository, and synced every stale mirror to current reality.

Full prior evidence — read first, in order:

1. `docs/reviews/2026-05-23-attribute-values-methodology/raw_findings/opus.md`
   — Opus consultant's broadened investigation.
2. `docs/reviews/2026-05-23-attribute-values-methodology/raw_findings/grok-critique.md`
   and `.../codex-critique.md` — independent critiques of Opus's
   proposal (both modified Opus's recommendation in the same way:
   drop the SPEC paragraph, widen scope).
3. `docs/reviews/2026-05-23-count-mirror-cleanup/review_bundle.toml`
   — the bundle this session operates against.

## What you are reviewing

- **Repo:** `/srv/repos/external/verivus-oss/agent-assurance`.
- **HEAD:** `5b1eca1f99e38e46c832b9e4f58095019e763127`.
- **Target commit:** `9996826` ("Full count-mirror cleanup")
- **Issue-ledger commit:** `5b1eca1` (the three issues filed for
  the residual concerns Opus's broadened investigation surfaced).
- **Parent (pre-cleanup):** `fccc1dc`.

Inspect with:

```bash
git -C /srv/repos/external/verivus-oss/agent-assurance show 9996826 --stat
git -C /srv/repos/external/verivus-oss/agent-assurance show 5b1eca1 --stat
git -C /srv/repos/external/verivus-oss/agent-assurance diff fccc1dc..5b1eca1
```

## What the commit chain delivers

1. **MANIFEST.toml [counts] split**: `attribute_values = 170` →
   `attribute_values_declared = 170` + `attribute_values_closed = 99`,
   with comments naming the two validators that enforce the closed
   number (`tools/dagtoml-validate-rs/src/main.rs:519-544` and
   `validators/validate_disclosure.py:82-105`).
2. **New validator** `validators/check_attribute_values.py`:
   recomputes every count surface from real sources, compares
   against MANIFEST + the hardcoded mirrors in dagtoml-duckdb/{,/-go},
   exits 1 on drift. ~340 lines, stdlib only.
3. **All stale mirrors synced** to current truth:
   - `expected_seed_counts` × 3 (postgres / sqlite / duckdb): all five
     fields updated.
   - `expected_node_counts` (graph): 16/24/31 → 20/27/31.
   - `expected_triple_counts` (rdf): schema=1100 → 1291.
   - Rust + Go EXPECTED_COUNTS hardcodes: 19/26/30/37/81 → 20/27/31/41/106.
4. **Schema constraints fixed**: `spec_layer` enum/CHECK was missing
   `'profile:cost'` across postgres/sqlite/duckdb. Added.
5. **Seed.sql + cypher header comments** synced.
6. **Issue ledger** at `docs/issues/`:
   - ISS-001 (high): initiator self-approval discipline gap.
   - ISS-002 (medium): graph cypher UNWIND data still incomplete (count-gate
     passes against MANIFEST but the actual data lags — explicit
     follow-up).
   - ISS-003 (low): dagtoml-duckdb hardcoded mirrors are now gated
     but should be eliminated via runtime MANIFEST reads.

## Workflow rules (binding)

1. Verify against code and docs, not the initiator's summary.
2. sqry MCP first; literal grep/text only for exact confirmation.
3. Every finding requires file + line + severity (high/medium/low).
4. Forbidden approval bases: stated intent, plan-compliance,
   "should be fixed". Approval MUST be based on inspected code,
   executed tests with output, inspected docs, and persisted
   review evidence.
5. Terminal states: UNCONDITIONAL APPROVAL or CONCRETE UNRESOLVABLE
   BLOCKERS. No conditional approvals.

## Substantive questions you MUST answer

1. **Does the gate actually fail on drift?** Construct a one-line
   perturbation to `reference/database/MANIFEST.toml`
   (e.g. change `attribute_values_declared = 170` to `171`) and
   run `bash validators/check_manifest_drift.sh`. Show the exact
   command, exit code, and verbatim output. Restore the file
   afterward and verify the gate is green.
2. **Independent count derivation.** Walk the four ontology files
   yourself and compute:
   - attribute_values_declared (sum of all `len(values)`)
   - attribute_values_closed (sum where `extensible = false`)
   Compare to MANIFEST. Show your script and output.
3. **Seed-row truth.** Count actual `INSERT` row counts in each
   of `reference/database/{postgres,sqlite,duckdb}/seed.sql` for
   all five tables (`kind_descriptor`, `entity_kind_descriptor`,
   `relation_descriptor`, `attribute_vocabulary`,
   `attribute_value_allowed`). Confirm they match MANIFEST's
   `expected_seed_counts` blocks.
4. **Hardcoded mirror consistency.** Read
   `tools/dagtoml-duckdb/src/main.rs:21-27` and
   `tools/dagtoml-duckdb-go/main.go:36-45`. Confirm both arrays
   contain exactly the same numbers as MANIFEST's
   `[verification.duckdb].expected_seed_counts`.
5. **Schema constraint coverage.** Verify the four CHECK constraints
   in `reference/database/sqlite/schema.sql` and the `CREATE TYPE
   spec_layer` declarations in
   `reference/database/{postgres,duckdb}/schema.sql` now include
   `'profile:cost'`. Confirm a fresh load + seed of the sqlite
   schema would succeed (or report why it still fails).
6. **RDF triple count.** Run
   `tools/dagtoml-rdf/target/release/dagtoml-rdf verify -o reference/database/rdf/schema.ttl`
   and confirm the parsed triple count matches MANIFEST's
   `expected_triple_counts.schema` (which the commit updated to
   1291).
7. **Cypher UNWIND data drift acknowledgement.** Open
   `reference/database/graph/schema.cypher` and count actual
   `MERGE (k:KindDescriptor ...)` rows, `MERGE (k:EntityKind ...)`
   rows, and `MERGE (p:RelationPredicate ...)` rows. Compare to
   MANIFEST's `expected_node_counts` (which claims 20/27/31). Is
   the comment block at `schema.cypher:88` and `:109` accurate
   in flagging that the actual UNWIND data is incomplete (15/23/31)?
8. **ISS-001 (self-approval) is filed.** Read
   `docs/issues/2026-05-23-ISS-001-self-approval-discipline.md`.
   Does the issue's analysis of past self-approval instances match
   the git log (e.g., does grok round-1 actually issue blockers
   against `bc2a7c5`, codex round-1 against `dc3a7b0`, both
   round-2 against `5c145c8`)? Walk `git log --oneline -- SPEC.md`
   and the `docs/reviews/2026-05-23-spec-12-closure-root/` raw
   findings; do they corroborate the issue's claims?
9. **The validator handles the legacy field correctly.** Construct
   a MANIFEST variant with both `attribute_values = 170` (legacy)
   AND `attribute_values_declared = 170`. Run the validator. Does
   it surface the legacy-field warning per the code at
   `validators/check_attribute_values.py` ~line 220?
10. **No regression of prior gates.** Run the full validator suite:
    ```
    bash validators/check_manifest_drift.sh
    python3 validators/validate_closure_root.py --discover .
    python3 validators/validate_cost.py --repo-root . examples/minimal-cost-record.toml
    python3 validators/validate_ijb_conformance.py core/ontology.toml
    python3 validators/validate_ijb_conformance.py profiles/cost/ontology.toml
    ```
    Capture exit codes. The `validate_closure_root.py --discover .` is
    expected to report 5 failures against pre-existing untracked
    files (`arxiv-prep-agent-dag.toml`, `claim-analysis-agent-gated-dag.toml`,
    `tools/*.toml` × 3) that are out of scope for this commit per
    prior decisions. Confirm those 5 are the same 5 listed in the
    `[counts].attribute_values_closed` comment.

## Output structure

1. **SESSION META** — reviewer model + version, sandbox/approval
   posture, MCP servers, re-derived HEAD sha.
2. **PROCESS CONFIRMATIONS** — for migration guidance (does the
   MANIFEST comment block at lines 30-58 explain the new field
   naming convention to producers?), no retconning, tests run
   with output. Each: confirmed / refuted / unverifiable with
   file:line evidence.
3. **ANSWERS TO THE 10 SUBSTANTIVE QUESTIONS** — one subsection
   per question. For each: verdict (confirmed /
   refuted_with_evidence / unverifiable), file:line evidence with
   verbatim quotes, commands you ran with exit codes and verbatim
   fenced output.
4. **INDEPENDENT FINDINGS** — anything the 10 questions missed.
   Same shape: id, severity, file:line, verbatim quote, problem
   explanation, suggested fix.
5. **TERMINAL VERDICT** — one of:
   - `UNCONDITIONAL APPROVAL — <one-line justification anchored to
     specific inspected evidence>`
   - `CONCRETE UNRESOLVABLE BLOCKERS:` followed by a numbered list.

Be specific. No prose-only conclusions. The user reads this
directly and acts on it.

Begin.
