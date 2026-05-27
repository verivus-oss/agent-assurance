# Independent paper review — round 2 (R2)

You are an independent reviewer dispatched per the workflow defined
in `tools/review-request-dag.toml`. This is a fresh / clean-context
session: you have no prior memory of this artefact. Per
`[policy.completion]`, prior-session reviewer evidence does NOT
carry over — you must independently verify the current bytes.

## What you are reviewing

- **Document under review:** `paper/main.tex` in
  `/srv/repos/external/verivus-oss/agent-assurance`.
  - sha256 of the CURRENT bytes:
    `6ba15597a36096462cadd55aade3b7bac13c8e7abd86a26b3b53374001437025`
  - PRIOR sha (R1, before fixes):
    `9664be061e4bc8493de2e5054d3c3d61737bd666e56077b9856c19585dbde306`
  - Repo commit: `638a90e8a0dc68c3e4aa8dfa29b51f6466d435fe` (the
    paper change is uncommitted; `git status` shows
    `M paper/main.tex`).
  - Title: "Paraphrase-Resistant Detection of AI-Driven Code
    Rewrites: A Falsifiable Harness Applied to the chardet v6 to
    v7 Relicensing Dispute".

## Inputs

- The bundle the paper describes:
  `examples/proof-chardet-relicense/`.
- Numeric validation: `paper/figures/scripts/validate_numbers.py`
  and `paper/figures/scripts/validation_report.json`.
- JPlag: `paper/figures/scripts/run_jplag.sh` and
  `paper/figures/scripts/jplag_chardet_results.json`.
- Paper's own verification report: `paper/VERIFICATION_REPORT.toml`.
- References: `paper/references.bib`.

## Prior-session corrective program (R1)

The R1 session at `docs/reviews/2026-05-23-paper-main/` issued
verdict `fail` with four concrete unresolvable blockers:

1. **B1 — JPlag file-count direction contradiction**
   (location: paper/main.tex around line 1305 before fix).
2. **B2 — Spec-vs-bundle conflation on verdict vocabulary**
   (locations: §sec:spec item 3 and §sec:verifier opening).
3. **B3 — C06e numeric-validation overclaim** (location:
   §sec:numeric-validation C06e paragraph).
4. **B4 — Unpersisted sandbox-vs-workstation claim** (location:
   §sec:sandbox).

The R1 record is at:
- `docs/reviews/2026-05-23-paper-main/gate_decision.toml`
- `docs/reviews/2026-05-23-paper-main/terminal_decision.toml`
- `docs/reviews/2026-05-23-paper-main/raw_findings/{codex,gemini,grok}.md`

The initiator claims to have applied fixes between sha
`9664be06...` and the current sha `6ba15597...`. The bundle file
`docs/reviews/2026-05-23-paper-main-r2/review_bundle.toml`
records the claimed fix locations.

## Workflow rules (binding)

1. Verify against the CURRENT bytes (sha `6ba15597...`). Do not
   trust the initiator's claim that the fix is applied — re-read
   the file at the cited line range and judge for yourself.
2. Search: prefer `sqry` (AST-based, via `mcp__sqry__*`) where
   applicable; use grep/rg and direct reads for prose. Run the
   harness scripts if you want to verify empirical claims.
3. Every finding requires verbatim quote + file:line + severity
   ∈ {high, medium, low}. No paraphrase.
4. Approval bases are restricted to inspected code, executed
   tests with output, inspected docs, and persisted review
   evidence. Forbidden bases: stated intent, plan-compliance
   claims, "should be fixed" language.
5. Terminal states: `UNCONDITIONAL APPROVAL` or `CONCRETE
   UNRESOLVABLE BLOCKERS`. No conditional approvals.

## What I need from you

Produce a single review report in this exact structure.

### 1. SESSION META

Model name + version. Sandbox / approval posture. MCP servers
available. Re-derived sha256 of `paper/main.tex` (do not trust
mine). Commands actually run and their exit codes.

### 2. BLOCKER VERIFICATION (the four R1 blockers)

For each of B1, B2, B3, B4: classify as one of:

- `fixed` — the new bytes resolve the R1 blocker. Cite the
  current file:line range and quote the new text.
- `not_fixed` — the issue is still present. Cite file:line and
  the unchanged or insufficiently-changed text.
- `partially_fixed` — some part of the R1 blocker is addressed
  but another part remains. State what is fixed, what is not,
  with file:line for both.
- `new_issue_introduced` — the edit creates a NEW problem.
  Describe the new problem with file:line and verbatim quote.

For B2 (spec-vs-bundle), verify BOTH cited locations: §sec:spec
item 3 AND §sec:verifier opening.

### 3. NEW INDEPENDENT FINDINGS

Anything you uncover in the new bytes that wasn't flagged in R1.
Same shape: id, severity, file:line, verbatim quote, problem
explanation, suggested fix.

This includes issues the EDITS may have introduced — e.g., LaTeX
syntax issues, broken cross-references, internal inconsistencies
between the new prose and other parts of the paper that the
edits didn't touch.

### 4. STILL-OPEN R1 NON-BLOCKER FINDINGS (sample check)

The R1 self-review had 29 findings; 4 were elevated to blockers
(B1-B4). The other 25 were not, and the initiator did NOT claim
to fix them in this round. Sample-check at least 5 of those 25
to confirm they remain present (or have been incidentally
addressed). The relevant IDs from
`docs/claim_analysis/2026-05-22-paper-main/claim_analysis.json`:
S1-F01..S1-F04, F2-F02, F2-F04, F2-F06, L3-F01..L3-F03,
U4-F01..U4-F04, S2-F01..S2-F05, C5-F01..C5-F04, Q6-F01..Q6-F03.

Report only the ones you sampled, with file:line evidence.

### 5. TERMINAL VERDICT

Either:

- `UNCONDITIONAL APPROVAL — <one-line justification anchored to
  inspected evidence of the four blockers all being resolved>`
- `CONCRETE UNRESOLVABLE BLOCKERS:` followed by a numbered list.
  Each entry must state: what is wrong, where (file:line), what
  evidence proves it is wrong, and what would unblock it.

Begin with section 1. No preamble. Be specific and quote.

## Disagreement protocol

If you believe the initiator's claimed fix is correct and a prior
R1 reviewer's blocker finding was wrong, cite the code or doc
evidence that refutes the R1 finding. Assertion is not enough.
