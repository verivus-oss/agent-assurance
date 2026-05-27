# Phase 1 kickoff prompt — SPEC §13 retrofit (`observation-record.v1`)

Paste the **"PROMPT TO PASTE"** section below into a fresh Claude
Code (or other coding agent) session running in this repo. The
prompt is self-contained; it points the new session at the
approved scoping plan, the workflow rules, and the canonical
reference shape.

---

## PROMPT TO PASTE

```
You are starting Phase 1 of the SPEC §13 retrofit on this repo
(agent-assurance / DAG-TOML public spec). Working directory:
/srv/repos/external/verivus-oss/agent-assurance.

THE PLAN

The retrofit was scoped and reviewed across two rounds; the
approved plan is at:

  docs/planning/2026-05-25-spec-13-retrofit-scoping.md

Read it in full before starting. Pay particular attention to:

  - §4: the reference shape (cost-record's existing §13 block at
    profiles/cost/cost-record-kind.toml:282-327)
  - §6: the taxonomy. Phase 1 kinds all declare class id
    "observation-record.v1" (a producer-attested role label, NOT
    a byte-level structural-shape contract). The per-kind
    [kind.abstraction_class].description field MUST be
    kind-specific, not the class-level role text.
  - §7 row entries for the four Phase 1 kinds.
  - §8 Phase 1: one PR, the four retrofits below.
  - §9: the four validator commands that MUST be green before you
    dispatch review.

The plan was approved by unanimous multi-LLM review (codex,
gemini, grok) at:

  docs/reviews/2026-05-25-spec-13-retrofit-scoping-plan-r2/terminal_decision.toml

YOUR SCOPE — PHASE 1

Retrofit FOUR kind descriptors to add [kind.abstraction_class]
and [kind.capability_envelope] blocks. cost-record is already
done; do not modify it.

  1. core/evidence-matrix-kind.toml
  2. profiles/agent-assurance/gate-decision-kind.toml
  3. profiles/agent-assurance/assertion-log-record-kind.toml
  4. profiles/disclosure/redaction-manifest-kind.toml

For each, insert TWO blocks following cost-record's shape exactly
(Family A — all 9 domains denied/zeroed, 100ms CPU, 1MB memory),
with one kind-specific change: the [kind.abstraction_class].id is
the same across all four ("observation-record.v1"), but the
[kind.abstraction_class].description MUST be specific to the
kind (tie it back to that kind's own [[kind.required_fields]] /
[[kind.required_sections]]).

Reference description from cost-record (the right shape, not the
text to copy):
  "Read-only observation artefact: declares hashed citations to
   prior actions + closed-vocabulary categorical dimensions +
   integer quantities. No I/O outside the canonical-form text
   serialisation; no networking; no process spawn."

For each retrofit kind, write a parallel kind-specific sentence
naming that kind's own structural shape. For example,
evidence-matrix would name its claims / evidence / matrix
sections, not cost-record's dimensions.

PLACEMENT

Insert the §13 blocks at the end of the [kind] structure,
typically after the [relation_to_ontology] block (mirror
cost-record's placement at profiles/cost/cost-record-kind.toml:
lines 282-327). Do NOT change the file's root-level closure_root
field — kind descriptors stay at the empty-closure sentinel per
SPEC §12.11 (plan §9 explains why; codex / gemini / grok all
confirmed this empirically in r2).

VERIFY BEFORE COMMITTING

Per the plan §9 and CONTRIBUTING.md "Review Discipline" section
2 + "Local Checks":

  python3 validators/validate_abstraction_class.py --repo-root . \
    core/*-kind.toml profiles/agent-assurance/*-kind.toml \
    profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml

  # Expected: "ABSTRACTION-CLASS VALIDATION PASSED (19 file(s)
  # checked; 5 declared a §13 block)." — was 1 before this PR.

  for f in core/*-kind.toml profiles/agent-assurance/*-kind.toml \
           profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml; do
    python3 validators/validate_ijb_conformance.py "$f"
  done

  for f in core/*-kind.toml profiles/agent-assurance/*-kind.toml \
           profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml; do
    python3 validators/validate_kind_descriptor.py "$f" \
      --repo-root . --check-references-exist
  done

  python3 validators/validate_closure_root.py --discover .
  # Expected: "CLOSURE-ROOT VALIDATION PASSED (74 file(s))."

  taplo lint core/*-kind.toml profiles/*/*-kind.toml

All MUST be green. Do NOT commit if any are red.

DISCIPLINE — NON-NEGOTIABLE

Read CONTRIBUTING.md "Review Discipline" before you commit. The
two rules that apply here:

  1. NO INITIATOR SELF-APPROVAL. After you commit the Phase 1
     retrofit, you MUST dispatch an independent multi-LLM review
     per tools/review-request-dag.toml [policy.*] before treating
     the work as done. The workflow is at:

       tools/review-request-dag.toml

     The pattern is (see prior sessions for examples):
       docs/reviews/2026-05-24-tooling-sweep-and-closure-root-sentinels/
       docs/reviews/2026-05-25-spec-13-retrofit-scoping-plan/
       docs/reviews/2026-05-25-spec-13-retrofit-scoping-plan-r2/

     Create a new review session folder
       docs/reviews/<date>-spec-13-phase-1-observation-record/
     with review_bundle.toml + review_prompt.md, then dispatch
     codex / gemini / grok in parallel via the llm-gateway MCP
     server (codex_request_async, gemini_request_async,
     grok_request_async) with createNewSession=true and full
     access permissions (dangerouslyBypassApprovalsAndSandbox,
     yolo / bypassPermissions). Persist the raw findings +
     terminal_decision.toml.

  2. BLESSED-KIND FILES MUST LAND WITH CLOSURE_ROOT IN THE SAME
     COMMIT. All four retrofitted kinds already have
     `closure_root` (the empty sentinel) at HEAD — DO NOT REMOVE
     it. Run validate_closure_root.py --discover . before commit;
     CI's gate is red on the slightest hiccup.

If a reviewer files a concrete_unresolvable_blocker with
file:line evidence, fix in place and dispatch a round 2 in
docs/reviews/<date>-spec-13-phase-1-observation-record-r2/.
Iterate until unanimous unconditional_approval. Do NOT approve
based on stated_intent, plan_compliance_claim, or
should_be_fixed_language.

If you disagree with a reviewer finding, your response MUST cite
code or doc evidence (file + line), not assertion.

OUT OF SCOPE

  - Do NOT modify spec.md.
  - Do NOT modify the plan
    (docs/planning/2026-05-25-spec-13-retrofit-scoping.md).
  - Do NOT touch the other 13 kinds (Phase 2 + Phase 3).
  - Do NOT propose new CI gates, pre-commit hooks, or other
    tooling. The validators already exist; the rule is to run
    them locally before commit. See ISS-001 closing note at
    docs/issues/2026-05-23-iss-001-self-approval-discipline.md
    for why elaborate CI tooling is explicitly rejected as a
    substitute for discipline.
  - Do NOT address ISS-005 (the SPEC §13.4 vs §12.1 tension);
    plan §11 explicitly flags this as out-of-scope.

WORKED EXAMPLES OF THE REVIEW DISCIPLINE IN ACTION

Read at least one prior session before dispatching your own:

  docs/reviews/2026-05-25-spec-13-retrofit-scoping-plan/
    — codex caught three real defects in the plan that
      self-approval would have shipped (one of them mechanically
      fatal: validator-incompatible field names).

  docs/reviews/2026-05-25-spec-13-retrofit-scoping-plan-r2/
    — unanimous unconditional_approval after fix-in-place.

The strongest-evidence verdict binds: a reviewer that re-runs a
validator and cites the failing output outranks a reviewer that
classifies the same issue as "minor" or "should be fixed". Be
the reviewer that runs the validator yourself.

START

Acknowledge you have read this prompt, then read the plan, then
the cost-record reference, then begin. Ask only blocking
questions; otherwise proceed.
```

---

## Notes for the human pasting this prompt

- The new session will not have access to this conversation's
  context. The prompt is self-contained; the new agent learns
  the discipline by reading the plan, `CONTRIBUTING.md`, and the
  prior review-session artifacts.
- The new session's per-project auto-memory at
  `~/.claude/projects/.../memory/` (if provider-specific agent CLI) may already
  carry `feedback_no_self_approval.md` and the matching
  `MEMORY.md` index from this session — that's fine; the prompt
  doesn't depend on it.
- If the new agent is not provider-specific agent CLI (e.g. Codex CLI run
  directly), the auto-memory won't be present; the prompt's
  reference to `CONTRIBUTING.md "Review Discipline"` is the
  load-bearing pointer.
- The expected outcome of Phase 1 is one PR with:
  - Four modified `*-kind.toml` files (the four named above).
  - Each gains `[kind.abstraction_class]` + `[kind.capability_envelope]`
    blocks with kind-specific `description` fields.
  - `validate_abstraction_class.py` reports `5 declared a §13 block`
    (was 1).
  - A new `docs/reviews/<date>-spec-13-phase-1-observation-record/`
    folder with the persisted multi-LLM review and unanimous
    `unconditional_approval`.
