# Independent spec-change review — cost profile (Stream G Cost-Witnessed Decision)

You are an independent reviewer dispatched per the workflow defined
in `tools/review-request-dag.toml`. This is a fresh / clean-context
session: you have no prior memory of this artefact. Treat any prior
claim about it as a hypothesis to verify, not as evidence.

## What you are reviewing

- **Repo:** `/srv/repos/external/verivus-oss/agent-assurance` (DAG-TOML
  public spec; main branch).
- **Commit under review:** `fccc1dcf8ebc796eaeee395d73126256fd94d869`
  (titled "profiles/cost/: Stream G cost-record kind
  (Cost-Witnessed Decision)").
- **Parent commit:** `953b8870b9cc0bbafa6f6c8ee9d3b8e80f7a8fb1`.
- **What changed:** 12 files, +986 / -44. Adds a new blessed profile
  under `profiles/cost/` with one kind (`cost-record`), three closed
  vocabularies, a dedicated validator, a minimal example, and the
  reference-DB seeds + CI wiring to match.

Inspect the commit and its working tree with:

```bash
git -C /srv/repos/external/verivus-oss/agent-assurance show fccc1dc --stat
git -C /srv/repos/external/verivus-oss/agent-assurance diff 953b887..fccc1dc
git -C /srv/repos/external/verivus-oss/agent-assurance log --oneline -3
```

## Inputs you have

Authoritative changed surfaces (open these directly, do not rely on
the initiator's paraphrase):

1. **`profiles/cost/PROFILE.toml`** — profile descriptor.
   `framework_profile_namespace = "spec.reserved"`, contains one
   kind: `cost-record`.
2. **`profiles/cost/ontology.toml`** — ontology extension declaring:
   - one entity kind `COST` (cost_record)
   - three closed `[[attribute_vocabularies]]` blocks:
     - `cost_dimension_category` (7 values)
     - `decider_class` (8 values)
     - `cost_citing_kind` (7 values)
3. **`profiles/cost/cost-record-kind.toml`** — kind descriptor with
   seven hard invariants (closed-vocab × 3, integer-only quantities,
   RFC 3339 timestamps, MD5/SHA-1 forbidden, IJB conformance).
4. **`validators/validate_cost.py`** — reference Python validator
   enforcing the seven invariants.
5. **`examples/minimal-cost-record.toml`** — one cost-record for a
   smoke-validation run decided by three-model LLM consensus
   (`decider_class = "llm_consensus"`).
6. **CI workflow** — `.github/workflows/validate.yml` now also runs
   the cost validator and includes the cost profile in the kind-
   descriptor / IJB conformance loops and the Rust+Go primary
   validator targets.
7. **Reference DB** — `reference/database/{postgres,sqlite,duckdb}/seed.sql`
   and `reference/database/rdf/schema.ttl` (regenerated) carry the
   cost profile registry rows.
8. **`reference/database/MANIFEST.toml` `[counts]`** — updated to
   `template_kinds = 20`, `entity_kinds = 27`,
   `attribute_vocabularies = 41`, `attribute_values = 106`.

## Inputs you have AS PRIOR ART (NOT as ground truth)

- The proposal at
  `docs/research/2026-05-22-spec-foundations-research/follow-up-2/13-stream-G-cost-witnessed-decision.md`.
  Every claim it makes (closed dimension set sufficient,
  producer-attested unit labels, cost-records-are-not-transitive,
  decider-class structural, observation-not-policy,
  citation-not-embedding) is a HYPOTHESIS for you to confirm
  against the committed text, not to accept.

## Workflow rules (binding, from `tools/review-request-dag.toml`)

These are non-negotiable. Read them once and apply them throughout.

1. **Verify against code and docs, not the initiator's summary.**
   Open the cited files. Check the cited lines. Run the cited
   commands.
2. **Search order:** `sqry` (AST-based semantic) first; literal /
   text search only for exact confirmation. The repo has a `sqry`
   MCP server with `mcp__sqry__*` tools.
3. **Every finding requires file + line + severity** (high/medium/low).
4. **Process confirmations to report on:**
   (a) Active-user best-effort migration / behaviour-change
       guidance — does the cost profile tell *adopters* how to use
       it? Is the CHANGELOG entry clear about scope and how to opt
       in via `framework_profile = "cost"`?
   (b) No historical dated spec was retconned without a link /
       correction note. (The cost profile is purely additive at
       the SPEC layer — verify nothing else changed.)
   (c) All claimed tests were actually run, with command output
       and status. RUN THESE:
       ```
       cd /srv/repos/external/verivus-oss/agent-assurance
       bash validators/check_manifest_drift.sh
       python3 validators/validate_closure_root.py --discover .
       python3 validators/validate_cost.py --repo-root . examples/minimal-cost-record.toml
       python3 validators/validate_ijb_conformance.py profiles/cost/ontology.toml
       python3 validators/validate_ijb_conformance.py profiles/cost/cost-record-kind.toml
       python3 validators/validate_kind_descriptor.py profiles/cost/cost-record-kind.toml --repo-root . --check-references-exist
       python3 validators/validate_profile_descriptor.py --repo-root . profiles/cost/PROFILE.toml
       ```
       Capture exit codes and summary lines.
5. **Forbidden approval bases:** stated intent, plan-compliance
   claims, "should be fixed" language.
6. **Terminal states:** `UNCONDITIONAL APPROVAL` or
   `CONCRETE UNRESOLVABLE BLOCKERS`. No conditional approvals.
7. **Persist your full review verbatim.** Your output IS the review
   record.

## Substantive questions you MUST answer

Each one has a yes/no/unverifiable answer backed by file+line
evidence.

1. **Closed-vocabulary completeness.** Are the three closed
   vocabularies (`cost_dimension_category`, `decider_class`,
   `cost_citing_kind`) declared once each, with the exact value sets
   from the proposal (7 + 8 + 7), correctly tagged with
   `ijb_primitive = "constraint"` and
   `ijb_constraint_type = "structural"`?
2. **Validator enforces every declared invariant.** The kind
   descriptor declares 7 hard invariants (INV01–INV07). Does
   `validators/validate_cost.py` actually check every one of them?
   Construct a negative-test TOML file for each invariant
   individually and verify the validator rejects each. Report
   each command + exit code + verbatim error message.
3. **Float quantities rejected.** Construct a cost-record with
   `quantity = 1.5` (float) and confirm the validator rejects it
   with a "no floats per canonical-form determinism" message.
   This is INV04. Show the exact command and rejection output.
4. **MD5/SHA-1 hash_algorithm rejected.** Construct a cost-record
   with `hash_algorithm = "md5"` and confirm the validator rejects
   it. This is INV06 cross-referencing SPEC §12.1. Show exit
   code and verbatim message.
5. **Closure-root requirement is enforced on the cost example.**
   The cost profile is a new blessed kind set; `cost-record` should
   come under SPEC §12.1's universal closure-root requirement
   automatically. Verify that
   `python3 validators/validate_closure_root.py --discover .`
   discovers the cost example and that it passes. Report the
   output.
6. **Manifest counts match ontology reality.** The MANIFEST claims
   `template_kinds = 20`, `entity_kinds = 27`,
   `attribute_vocabularies = 41`, `attribute_values = 106`.
   Independently count from the ontology files
   (`core/ontology.toml` + `profiles/agent-assurance/ontology.toml`
   + `profiles/disclosure/ontology.toml` + `profiles/cost/ontology.toml`).
   Do the counts match? Run
   `bash validators/check_manifest_drift.sh` and report.
7. **Profile-descriptor correctness.** `profiles/cost/PROFILE.toml`
   declares `contained_kinds = ["cost-record"]`, `extends = []`,
   `namespace = "spec.reserved"`. Does it pass
   `validators/validate_profile_descriptor.py`? Are the IJB tags
   on `[profile]` correct?
8. **No-billing-dialect constraints honoured.** The proposal forbids
   currency, vendor SKUs, per-unit rates, formulas, computed fields,
   normalised units across producers. Inspect the kind descriptor
   and validator — does the committed shape stay clean of these?
   Particular things to check: no `rate` / `currency` / `total`
   fields; no float quantities allowed; unit labels are
   producer-attested strings with no normalisation rule. Quote
   verbatim from `cost-record-kind.toml` and `validate_cost.py`.
9. **No transitive aggregation surface.** The proposal says cost
   records are not transitive — a gate-decision cites the
   cost-records *paid to reach this decision*, not the cost-records
   of every upstream evidence-matrix entry. Does the cost-record
   kind avoid any field that would imply transitivity (no
   `cited_costs`, `aggregates`, `sum_of`, `cost_root`,
   `cost_total` fields)? Quote `record` field list.
10. **Decider-class gaming surface.** The proposal flags a threat:
    a producer mislabelling an LLM call as `deterministic_check`.
    Is there any structural protection in the spec or validator?
    (Spoiler: no — the SPEC layer can't prevent mislabelling,
    only Stream B attestation + auditor review can.) Is this
    acknowledged anywhere in the kind descriptor or CHANGELOG?

## What I need from you

Produce a single review report with these sections, in order.

### 1. SESSION META

- Reviewer model name and version.
- Sandbox / approval posture for this session.
- MCP servers available.
- Commit / sha of the document you actually opened (re-derive,
  do not trust mine):
  ```
  git -C /srv/repos/external/verivus-oss/agent-assurance rev-parse HEAD
  ```

### 2. PROCESS CONFIRMATIONS

For each of the three checks above (migration guidance, no
retconning, tests-run-with-output), report:
`confirmed` / `refuted` / `unverifiable` with file+line evidence.

### 3. ANSWERS TO THE 10 SUBSTANTIVE QUESTIONS

One subsection per question. For each:

- The question (one-liner).
- Your verdict (`confirmed` / `refuted_with_evidence` /
  `unverifiable`).
- The file+line evidence (verbatim quotes, no paraphrase).
- For executed commands: the exact command, its exit code, and the
  output (verbatim, fenced).

### 4. INDEPENDENT FINDINGS

Findings you uncovered that the substantive questions didn't
cover. Same shape: id (you assign), severity (high/medium/low),
file+line, verbatim quote, problem explanation, suggested fix.

### 5. TERMINAL VERDICT

One of:

- `UNCONDITIONAL APPROVAL — <one-line justification, anchored to a
  specific piece of inspected evidence>`
- `CONCRETE UNRESOLVABLE BLOCKERS:` followed by a numbered list,
  each blocker stating: what is wrong, where (file:line), what
  evidence proves it is wrong, and what would unblock it.

Do not output anything outside this five-section structure. Do not
preface with "Here is my review:" — start with section 1.

## Disagreement protocol

If you believe the commit is correct and the proposal document
(`13-stream-G-cost-witnessed-decision.md`) differs (e.g. the
proposal sketches a `cost_root_algorithm` field which the commit
deliberately omits), you MUST quote both versions and explain why
the divergence is intentional or accidental.

If you cannot tell, mark the finding `unverifiable` and explain
which piece of evidence you would need to resolve it.

Begin.
