# Independent review — ISS-001 closing + ISS-004 filing (2026-05-24)

You are an independent reviewer running with a fresh, clean context.
You have NO prior memory of the 2026-05-24 sessions. Your scope is
narrow: verify whether commit `ca50b2c` correctly closes ISS-001
and correctly files ISS-004, given the in-session user feedback that
constrains the framing.

## Repository

- Working copy: `/srv/repos/external/verivus-oss/agent-assurance`
- Parent commit: `884f290`
- HEAD: `ca50b2c`
- Commit range: `884f290..ca50b2c` (1 commit)
- The review bundle: `docs/reviews/2026-05-24-iss-001-closure-and-iss-004-filing/review_bundle.toml`
- Workflow rules: `tools/review-request-dag.toml [policy.*]`

## Background context (do NOT trust these claims — verify them)

The bundle's `[bundle.predecessors]` lists two earlier review
sessions today. The chain:

1. **Session 1 (r1)** — `docs/reviews/2026-05-24-tooling-sweep-and-closure-root-sentinels/`
   - 4 commits reviewed: `47b6acd`, `320a901`, `d027178`,
     (initially up to `d027178`; later `32936b1` repaired the
     codex r1 blocker).
   - Codex r1 issued `concrete_unresolvable_blocker` on
     `paper-arxiv-prep/compile-and-pdf-evidence.toml` (invalid
     TOML at line 27).

2. **Session 2 (r2)** — `docs/reviews/2026-05-24-tooling-sweep-and-closure-root-sentinels-r2/`
   - Reviewed the fix commit `32936b1`.
   - Unanimous `unconditional_approval` (3/3).

3. **Session 3 (this)** — reviews the issue-ledger changes that
   close ISS-001 and file ISS-004.

The user explicitly corrected the initiator twice during the
session, captured verbatim in `[bundle.user_feedback_in_session]`.
Verify those quotes against your own reading of the conversation
context if you have access to it; otherwise treat them as
context-only and focus on whether ISS-001's closing text and
ISS-004's framing are consistent with the user's principle that
elaborate CI tooling is not a substitute for following the
existing rule.

## Rules you MUST obey (`tools/review-request-dag.toml [policy.*]`)

- `[policy.evidence]` — verify against bytes; never accept summary
  as evidence. Findings need file:line + severity.
- `[policy.approval]` — `forbidden_approval_bases`: `stated_intent`,
  `plan_compliance_claim`, `should_be_fixed_language`. Required:
  `inspected_code`, `executed_tests_with_output`, `inspected_docs`,
  `persisted_review_evidence`. Terminal: `unconditional_approval`
  or `concrete_unresolvable_blocker`.
- `[policy.unit_classification]` — classify U05 with file:line
  evidence.

## What to verify — the five questions

Read the review bundle's `[bundle.questions]` section. It contains
the substantive questions: Q1 (ISS-001 factual accuracy), Q2
(closing warranted vs premature), Q3 (ISS-004 correctly framed),
Q4 (self-approval recursion — was this review needed?), Q5 (retcon
check). Answer each.

In addition:

1. **Verify the absence of files claimed absent.** ISS-001's
   closing note says "Safeguards A and B as originally proposed
   are NOT built". Verify by attempting to read:
   - `validators/check_review_session_terminal.py`
   - `validators/check_commit_message.py`
   Both MUST be absent at HEAD. If either exists, the closing note
   is factually wrong.

2. **Verify the rule it cites IS live.** ISS-004 says
   `validate_closure_root.py` runs in CI at line ~180 of
   `validate.yml`. Verify by reading
   `.github/workflows/validate.yml` and confirming the validator
   is invoked.

3. **Verify the SHA cited.** ISS-001 closes itself by `closed_by:
   884f290`. Run `git show 884f290 --stat` and verify that the
   commit contains the r1 + r2 review session artifacts as the
   closing note describes.

## Required output (no prefatory chit-chat)

1. `## Summary` — one paragraph, terminal classification for U05.
2. `## U05 — ca50b2c` — findings with file:line + severity.
3. `## Q1 — ISS-001 factual accuracy` — verified / refuted, with
   evidence.
4. `## Q2 — closing warranted` — verified / refuted, with
   evidence and reasoning about whether the closing note's
   argument (that the original acceptance criteria were the
   wrong framing) is sound.
5. `## Q3 — ISS-004 correctly framed` — verified / refuted.
6. `## Q4 — self-approval recursion` — pick position (a), (b), or
   partially each, with evidence from the cited files.
7. `## Q5 — retcon check` — pass / fail.
8. `## Process checks` — one line per
   `[policy.process_checks]` item.
9. `## Terminal verdict` — `unconditional_approval` or
   `concrete_unresolvable_blocker`. Rationale tied to evidence.

## Persistence

Your full verbatim response will be saved to
`docs/reviews/2026-05-24-iss-001-closure-and-iss-004-filing/raw_findings/<your_model_name>.md`

Start with the `## Summary` heading.
