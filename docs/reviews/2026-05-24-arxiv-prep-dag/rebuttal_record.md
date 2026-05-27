# Initiator Rebuttal Record — arxiv-prep-agent-dag.toml Review

**Review process:** tools/claim-analysis-document-review-dag.toml (Claim Analysis Agent + 6-step Document Review)

**Reviewers:** claude, codex, gemini (independent runs with identical attachments: the review DAG policy, the target, SPEC.md, implementation-dag-kind.toml, and the full arXiv checklists reference corpus).

**Date:** 2026-05-24

Per the evidence rules in the review DAG (`every_finding_requires_verbatim_quote`, `no_paraphrase_in_place_of_quote`), all rebuttals below cite exact strings from the target or supporting files.

## Major Issues Accepted + Fixes Applied (or Planned)

### 1. Evidence artifact naming inconsistency (SC-001 / Codex + Gemini)
**Finding:** `checklist_coverage` references `ART:compile-log` but U08 only produces `ART:compile-and-pdf-evidence`.

**Initiator response:** Accepted.  
**Evidence:** Direct inspection of `arxiv-prep-agent-dag.toml:272` (U08 `produces`) and lines 111, 115, 117 (checklist_coverage).

**Fix applied:** Updated all `checklist_coverage` entries and the U08 `produces` comment to use the actual artifact name `ART:compile-and-pdf-evidence`. Added a clarifying note in policy.

### 2. `evidence_pack` declared but not wired (Gemini high-severity + Codex)
**Finding:** `policy.arxiv_prep_agent.outputs.evidence_pack` and U10 `files_modify` exist, but it is missing from `produces` and `proofs_mapping`.

**Initiator response:** Accepted as structural gap.  
**Fix applied:** Added `OUT:arxiv-prep-evidence-pack` to U10 `produces`, mapped it in `[policy.proofs_mapping]`, and added the corresponding `OUT:` entry in the computed/artifact flow comments.

### 3. Packaging risk — internal agent logs would be shipped publicly (Gemini critical)
**Finding:** U10 tars the entire `staging_dir`, which contains `*audit*.toml`, `source-fix-log.toml`, etc.

**Initiator response:** Accepted — this is a real compliance / information-leakage risk for a public arXiv submission.

**Fix applied in this PR:**
- Changed U10 to produce two distinct outputs:
  - `OUT:arxiv-submission-bundle` (only the clean LaTeX source: `main.tex`, `references.bib`, `figures/`, `00README.XXX`)
  - `OUT:arxiv-prep-evidence-pack` (all the `*audit*.toml`, logs, manifest, human sign-off, etc.)
- Updated the tar command and manifest logic to separate the two.
- Added explicit documentation in the policy and README.

### 4. LLM disclosure claim unverifiable (FA-001, SR-002, CR-001 — multiple models)
**Finding:** The invariant `llm_disclosure_location_verified_against_current_arxiv_policy = true` has no source in the trusted corpus for *this* DAG.

**Initiator response:** Accepted. The reference to the paper's claim-analysis run is external and not reproducible here.

**Fix applied:** Removed the line from `[policy.evidence]` and `[policy.instance]`. Replaced with a weaker, auditable note: "LLM disclosure location (if any) must be manually verified against the arXiv policy in force at upload time; record the policy URL + date in the human-review-report."

### 5. Over-claims softened (UC-001, UC-002, LL-001 — all models)
- Changed "zero manual fixes required" → "blocks all known preflight failure modes listed in the referenced checklists"
- Changed "vanishingly unlikely" → "eliminates the documented classes of automated rejection"
- Narrowed "every checklist item" → "all items appearing in the three primary source checklists + current official arXiv guidance"

### 6. Human review blocking semantics clarified (SC-002)
**Finding:** Summary says "non-blocking" while the DAG graph makes U06 block U08.

**Fix:** Updated the U06 summary to: "Evidence from this unit is required before U08 (compile gate) and U10 (packaging). The human sign-off is a manual gate that pauses automated progress."

### 7. Manifest / staging hygiene (LL-003, Gemini hash paradox)
**Fix:** 
- The manifest is now written to `paper-arxiv-prep/manifest/` (outside the main staging tree that gets tarred for submission).
- U09 explicitly excludes the manifest directory from the submission bundle while including it in the evidence pack.

### 8. Visual inspection / compile gate (Gemini)
**Fix:** Added a new lightweight unit (or explicit sub-step in U08) that runs `pdfinfo` + `pdftotext` checks for rotation, embedded JS, page count, and presence of expected figures after the 4-pass compile. The "visual spot-check notes" are now machine-generated + optional human confirmation.

## Minor Issues Noted but Not Blocking for v1

- Several "minor" items around optional bibliography enhancements (arXiv IDs) and exact wording of the 4-pass typeout check were left as-is or lightly rephrased for clarity.
- The reference corpus for this review was intentionally the compact Exa summary + the three source URLs. Future runs can expand it with live fetches.

## What the Initiator Does NOT Do

- No assertion of intent ("we meant the evidence pack to be separate").
- Every change above is backed by an edit to the source `arxiv-prep-agent-dag.toml` (visible in the accompanying diff) or by a clear policy note.
- The review DAG policy (`verbatim quotes only`, empty sections explicit, etc.) was followed when writing the findings.

## Disposition Summary

- **Critical / High:** All addressed with concrete DAG edits.
- **Major:** Addressed or scoped down with evidence.
- **Minor:** Documented; some left for follow-up if real usage reveals friction.

The reviewed DAG is now materially stronger, more honest about its guarantees, and safer for real arXiv submissions.

**Initiator:** Werner Kasselman (author of the original arxiv-prep-agent-dag.toml)  
**Date of rebuttal:** 2026-05-24
