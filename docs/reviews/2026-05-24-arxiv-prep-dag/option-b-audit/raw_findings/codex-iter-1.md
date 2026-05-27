# Codex Option-B Audit — Iteration 1

**Job ID:** 546e71db-bdf0-470b-80bd-8188d9ae7abb
**CLI:** codex
**Correlation ID:** option-b-audit-codex-001
**Session ID:** 4e0895f8-dab3-4b22-bcbf-2cb2266dc30d
**Started:** 2026-05-23T00:30:52.024Z
**Finished:** 2026-05-23T00:35:42.842Z
**Runtime:** 4 min 50 s
**Exit:** 0
**Stdout bytes:** 6972
**Stderr bytes:** 87887
**Token usage (final trace line):** 106,991
**Runtime params:** `sandboxMode=danger-full-access`, `mcpServers=["sqry","exa","ref_tools"]`, `idleTimeoutMs=1800000`

**SHAs at audit time** (verified by Codex in-trace):
- proposed-mappings.toml: `d46253364305de05ce8934b0664c3d8956ce6193c1ed0b799dfb16fc515a6c6e`
- arxiv-prep-agent-dag.toml: `8f2b19f77a0c1e32e725d9ab9484965e5a601026696d7c3a37b6981668c6b383`
- arxiv-checklists-reference.txt: `0e95cb3efc47c8d24dc7de309281f1c0e4adf7539af6ab1f3ca26204705d7851`
- HEAD: `99e18dba38ec3b4c6234b77bac7a87b0f2e6cdfc`

## Verbatim Output

```
Target audited: `docs/reviews/2026-05-24-arxiv-prep-dag/fourth-pass/option-b/proposed-mappings.toml`
Mapping sha256: d46253364305de05ce8934b0664c3d8956ce6193c1ed0b799dfb16fc515a6c6e
DAG sha256: 8f2b19f77a0c1e32e725d9ab9484965e5a601026696d7c3a37b6981668c6b383
Corpus sha256: 0e95cb3efc47c8d24dc7de309281f1c0e4adf7539af6ab1f3ca26204705d7851
HEAD commit: 99e18dba38ec3b4c6234b77bac7a87b0f2e6cdfc
Validator observations: `validate_implementation_dag.py arxiv-prep-agent-dag.toml` PASS; `validate_ijb_conformance.py --repo-root . arxiv-prep-agent-dag.toml` PASS; `tomllib` parse of proposed mappings PASS.

Check 1: PASS. All three requested SHA-256 values and HEAD match.

Check 2: PASS. `total_items = 41`, actual items = 41; `gap_count = 10`, actual `is_gap=true` entries = 10. Every item has the observed v1 fields: `id`, `source`, `also_appears_in`, `pitfall_quote`, `proposed_units`, `proposed_evidence`, `unit_evidence_quote`, `confidence`, `is_gap`, `gap_reason`, `notes`. TOML is well-formed.

Check 3: FAIL. The 41 explicit corpus phrases are present in the mapping and I found no fabricated `pitfall_quote`. However, the Ian item `remove unused sections/comments/extraneous/rev control` is over-conflated: it combines distinct rules with different DAG coverage into one gap. U03 covers some revision-control/extraneous-file cleanup, while comments and unused sections are uncovered. That loses distinct coverage state.

Check 4: random sample seed `20260523`; sampled quote integrity:
`texlive_2025.hyperref-before-hyperxmp`: pitfall PASS, unit N/A gap.
`arxiv-mistakes.readme-for-ignore`: pitfall PASS, unit PASS.
`ianhuston.remove-unused-sections-and-comments`: pitfall PASS, unit N/A gap.
`arxiv-mistakes.bbbk-error`: pitfall PASS, unit N/A gap.
`arxiv-mistakes.mixed-figures`: pitfall PASS, unit PASS.
`submit_tex.bbl-compat-3-3-tl2025`: pitfall PASS, unit PASS.
`submit_tex.tl2025-default`: pitfall PASS, unit PASS.
`arxiv-mistakes.concatenated-files`: pitfall PASS, unit N/A gap.
`submit_tex.figure-formats-per-processor`: pitfall PASS, unit PASS.
`ianhuston.check-bib-text-style`: pitfall PASS, unit PASS.
Additional unsampled defect found: several `unit_evidence_quote` values containing TeX backslashes are not raw-verbatim in the DAG file because the DAG TOML source uses escaped backslashes.

Check 5: gap verdicts:
`arxiv-mistakes.bbbk-error`: ACCURATE; no U01-U10 summary or `[policy.evidence]` names Bbbk. Trivial U07 recipe addition.
`arxiv-mistakes.breqn-hyperref-fix`: ACCURATE; no named breqn+hyperref fix. Trivial U07 recipe addition.
`arxiv-mistakes.concatenated-files`: ACCURATE; no multiple-document structural scan.
`arxiv-mistakes.missing-style-files`: ACCURATE; U08 catches compile failure but no positive custom `.sty/.cls` presence/TL inventory check.
`arxiv-mistakes.old-styles`: ACCURATE; no deprecated-style blocklist.
`arxiv-mistakes.unusual-fonts`: ACCURATE; no font inventory or Type1/Type3/system-font check.
`arxiv-mistakes.user-intervention-inp`: INACCURATE as a gap. The mapping itself admits U08 would surface it, and the DAG has a compile gate using `-interaction=nonstopmode`.
`ianhuston.remove-unused-sections-and-comments`: ACCURATE only for comments/unused sections; inaccurate as a single combined gap because rev-control cleanup is partially covered by U03.
`ianhuston.update-journal-refs`: ACCURATE; U04 adds arXiv IDs but does not update now-published journal refs.
`texlive_2025.hyperref-before-hyperxmp`: ACCURATE; U07 has only generic "other TL2025 fixes," not this load-order rule. Trivial U07 recipe addition.

Check 6: 21 of 25 high-confidence items are substantively justified. Four should be downgraded: `arxiv-mistakes.absolute-filenames`, `arxiv-mistakes.include-subdirs-write-perms`, `arxiv-mistakes.mixed-figures`, `trevorcampbell.compile-in-tmp-and-verify`. Medium sample reassessment: `ianhuston.check-bib-text-style` remains medium; `arxiv-mistakes.last-minute-changes` remains medium; `arxiv-mistakes.non-tex-files` should be low unless U10 is added because U03/U09 mostly audit/record rather than enforce the final clean-source-only bundle.

Check 7: PASS. For all 31 non-gap items, every `proposed_evidence` artifact is produced by at least one listed `proposed_units` entry, and the same unit/artifact pair exists in `[policy.proofs_mapping]`.

Check 8: Not as written. If all 10 gaps are closed by DAG amendments, LL-001 would likely clear after the checklist table is expanded. If any corpus-enumerated gap is merely declared out-of-scope, the current claims still fail: `arxiv-prep-agent-dag.toml:79` says "attaching an explicit unit or gate to each preflight failure mode enumerated in the referenced checklists," and `arxiv-prep-agent-dag.toml:82` says checklist items "were each addressed by an explicit unit or gate." Those claims must either be narrowed to acknowledge explicit in-corpus exceptions, or every in-corpus gap must get a unit/gate.

Defects found:
1. `docs/reviews/2026-05-24-arxiv-prep-dag/arxiv-checklists-reference.txt:10`: "remove unused sections/comments/extraneous/rev control" is treated as one mapping item at `proposed-mappings.toml:338`, losing distinct coverage state. U03 separately covers part of it: `arxiv-prep-agent-dag.toml:223`: "any $Id$ or CVS revision strings inside .tex."
2. `proposed-mappings.toml:278-279`: `is_gap = true` and "U08 runs with -interaction=nonstopmode locally which would surface it as a fault" conflict with the DAG gate at `arxiv-prep-agent-dag.toml:299`: "Run chosen_processor on main.tex four (or more) times with -interaction=nonstopmode."
3. `proposed-mappings.toml:120`: `'''Switch any \ifx\pdfoutput to \usepackage{ifpdf} + \ifpdf.'''` is not raw-verbatim in the DAG; the raw DAG line is escaped at `arxiv-prep-agent-dag.toml:282`: "Switch any \\ifx\\pdfoutput to \\usepackage{ifpdf} + \\ifpdf." Affected IDs include absolute/space/include path checks, ifpdf, protect-cite, equation punctuation, read-equations, no-today, and typeout.
4. `proposed-mappings.toml:130` claims `\include subdirs write perms`, but `proposed-mappings.toml:133` only quotes "subdir policy violations"; the write-permission pitfall is not named.
5. `proposed-mappings.toml:494` claims `compile in tmp and verify`, but `proposed-mappings.toml:497` only quotes "Run chosen_processor on main.tex four (or more) times"; tmp/staging isolation is not named in that evidence quote.
6. `arxiv-prep-agent-dag.toml:79` and `arxiv-prep-agent-dag.toml:82` still require every in-corpus checklist item to be addressed by a unit/gate; an out-of-scope block for in-corpus gaps would not clear LL-001 unless these claims are narrowed.

Defects fixed in-session by Codex: none; audit only, no file edits made.

GATE DECISION: STILL BLOCKED (blockers: over-conflated Ian checklist item; false-positive `user-intervention .inp` gap; non-verbatim evidence quotes; unresolved prose conflict if in-corpus gaps are declared out-of-scope)
```

## Interpretation

All 6 defects are evidence-grounded (file:line + verbatim quote for each). Claude (orchestrator) does not disagree with any of them on inspection — verified independently:

| # | Defect | Resolution path |
|---|---|---|
| 1 | `ianhuston.remove-unused-sections-and-comments` over-conflated | Split into `remove-rev-control-strings` (non-gap → U03) and `remove-comments-and-unused-sections` (gap, comments + `\section` blocks not covered) |
| 2 | `arxiv-mistakes.user-intervention-inp` is a false gap | Reclassify as non-gap → U08, evidence ART:compile-and-pdf-evidence, with quote about `-interaction=nonstopmode` |
| 3 | 10 `unit_evidence_quote` values use unescaped backslashes (Opus de-escaped them) | Re-quote each affected item using the raw escaped form (`\\ifx\\pdfoutput`, etc.) so `rg -F` against the DAG succeeds |
| 4 | `arxiv-mistakes.include-subdirs-write-perms` quote does not name "write permissions" | Either find a quote that names them, or flip to is_gap |
| 5 | `trevorcampbell.compile-in-tmp-and-verify` quote does not name "tmp/staging isolation" | Re-quote with U01's "Copy paper_source_dir to staging_dir" line which DOES address compile-in-staging, OR flip to is_gap |
| 6 | DAG prose at lines 79/82 still claims universal in-corpus coverage; an out-of-scope block doesn't clear LL-001 unless prose is narrowed | Narrow prose to scope the claim to `[policy.checklist_coverage]` itself (the table becomes the binding declaration of scope) |

**Plus Check 6 secondary findings** (not in the numbered defect list but flagged as needed):
- 4 "high"-confidence items should be downgraded: `arxiv-mistakes.absolute-filenames`, `arxiv-mistakes.include-subdirs-write-perms` (same as Defect 4), `arxiv-mistakes.mixed-figures`, `trevorcampbell.compile-in-tmp-and-verify` (same as Defect 5).
- 1 "medium" should be "low": `arxiv-mistakes.non-tex-files` (U03/U09 audit/record but don't enforce final clean-source-only bundle until U10 is added).

## Iteration 2 plan

Iter-2 will apply mechanical fixes for Defects 1, 2, 3 and Check 6 downgrades, address Defects 4 and 5 by direct re-inspection of the corpus + DAG, and patch the DAG prose at lines 79/82 to scope the universal-coverage claim to `[policy.checklist_coverage]` itself (Defect 6 resolution).

Iter-2 will NOT add new U07 recipes for the genuine gaps in this round (bbbk-error, breqn-hyperref-fix, hyperref-before-hyperxmp, etc.) — those are real DAG amendments that should land separately under user direction.
