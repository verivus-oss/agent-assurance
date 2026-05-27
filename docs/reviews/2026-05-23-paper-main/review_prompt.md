# Independent paper review — request

You are an independent reviewer dispatched per the workflow defined
in `tools/review-request-dag.toml`. This is a fresh / clean-context
session: you have no prior memory of this artefact. Treat any prior
claim about it as a hypothesis to verify, not as evidence.

## What you are reviewing

- **Document under review:** `paper/main.tex` in the repository
  rooted at `/srv/repos/external/verivus-oss/agent-assurance`.
  - sha256 of the bytes under review:
    `9664be061e4bc8493de2e5054d3c3d61737bd666e56077b9856c19585dbde306`
  - Repo commit: `638a90e8a0dc68c3e4aa8dfa29b51f6466d435fe`
  - The paper is a manuscript titled "Paraphrase-Resistant Detection
    of AI-Driven Code Rewrites: A Falsifiable Harness Applied to the
    chardet v6 to v7 Relicensing Dispute".

## Inputs you have

- The bundle the paper describes:
  `examples/proof-chardet-relicense/`
  - `CONTRACT_DECLARATION.toml`
  - `IMPLEMENTATION_DAG.toml`
  - `TRACEABILITY.toml`
  - `EVIDENCE_MATRIX.toml`
  - `REVIEW_READINESS.toml`
  - `VERIFICATION_REPORT.toml`
  - `README.md`
  - `extract_signals.py`, `fingerprint_behavior.py`, `detect.sh`
- Numeric validation script: `paper/figures/scripts/validate_numbers.py`
  and `paper/figures/scripts/validation_report.json`.
- JPlag run: `paper/figures/scripts/run_jplag.sh` and
  `paper/figures/scripts/jplag_chardet_results.json`.
- The paper's own verification report:
  `paper/VERIFICATION_REPORT.toml`.
- The references file: `paper/references.bib` (44 entries).

## Inputs you have AS PRIOR ART (NOT as ground truth)

- A self-review of the same document was performed by the paper's
  initiating model on 2026-05-22 and is at
  `docs/claim_analysis/2026-05-22-paper-main/`. It reports 29
  findings (1 high, 12 medium, 16 low). You are NOT being asked to
  approve that self-review. You are being asked to perform an
  independent review. The self-review is included so you do not have
  to redo work, BUT every finding it lists is a HYPOTHESIS for you
  to confirm, refute, or mark unverifiable — never to accept.

## Workflow rules (binding, from `tools/review-request-dag.toml`)

These are non-negotiable. Read them once and apply them throughout.

1. **Verify against code and docs, not the initiator's summary.**
   Open the cited files. Check the cited lines. Run the cited
   commands. Do not accept a claim because the initiator (or the
   self-review) says it is true.
2. **Search order:** `sqry` (AST-based semantic) first; literal /
   text search only for exact confirmation. The repo has a `sqry`
   MCP server with `mcp__sqry__*` tools — use them. For text
   matches, use `grep` / `rg` only to confirm a sqry hit.
3. **Every finding requires file + line + severity.** Verbatim
   quote the document part. No paraphrase. Severity ∈ {high,
   medium, low}.
4. **Classify each prior-art finding** as `confirmed`,
   `refuted_with_evidence` (cite code/doc), or `unverifiable`.
   Add any NEW findings you uncover that the self-review missed.
5. **Process confirmations to report on:**
   (a) active-user best-effort migration / behaviour-change
       guidance is present in the document where appropriate;
   (b) no historical dated spec was retconned without a link /
       correction note;
   (c) all claimed tests were actually run, with command output
       and status. The paper at §sec:results, §sec:numeric-validation,
       §sec:sqry, and §sec:related-tools makes empirical claims —
       check that the cited artefacts (validation_report.json,
       jplag_chardet_results.json, EVIDENCE_MATRIX) actually
       contain the values quoted in the paper.
6. **Forbidden approval bases:** stated intent, plan-compliance
   claims, "should be fixed" language. APPROVAL MUST BE BASED ON
   INSPECTED CODE, EXECUTED TESTS WITH OUTPUT, INSPECTED DOCS, AND
   PERSISTED REVIEW EVIDENCE.
7. **Terminal states:** issue either `UNCONDITIONAL APPROVAL` or
   a list of `CONCRETE UNRESOLVABLE BLOCKERS`. Do not approve
   conditionally. Do not approve subject to fixes.
8. **Persist your full review verbatim.** Your output IS the
   review record. Do not summarise — be specific and quote.

## What I need from you

Produce a single review report with these sections, in order.

### 1. SESSION META

- Reviewer model name and version.
- Sandbox / approval posture for this session.
- MCP servers available.
- Commit / sha of the document you actually opened (re-derive,
  do not trust mine).

### 2. PROCESS CONFIRMATIONS

For each of the three checks in rule 5 above, report:
`confirmed` / `refuted` / `unverifiable` with file+line evidence.

### 3. CLASSIFICATION OF THE 29 PRIOR-ART FINDINGS

For each finding ID in `docs/claim_analysis/2026-05-22-paper-main/claim_analysis.json`
(IDs S1-F01..S1-F04, F2-F01..F2-F06, L3-F01..L3-F03,
U4-F01..U4-F04, S2-F01..S2-F05, C5-F01..C5-F04, Q6-F01..Q6-F03),
report a single line:

```
<finding-id>  <confirmed | refuted_with_evidence | unverifiable>  <file:line evidence>  <one-sentence note>
```

### 4. INDEPENDENT FINDINGS

Findings you uncovered that the self-review missed. Same shape as
the self-review findings (id, severity, file+line, verbatim quote,
problem explanation, suggested fix).

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

If you believe the document's claim is correct and the self-review
finding is wrong, you MUST cite the code or doc evidence that
refutes the finding. Assertion is not enough.

If you cannot tell, mark the finding `unverifiable` and explain
which piece of evidence you would need to resolve it.

Begin.
