# Codex Review: paper/main.tex at HEAD 1e0e155

Reviewer: Codex, fresh-context end-to-end review
Target: `paper/main.tex`
Session: `docs/reviews/2026-05-25-paper-chardet-e2e/`
Date: 2026-05-25

I verified claims against the bytes in the workspace, not against the initiator summary or prior reviewer summaries. I used sqry first for repository index coverage; sqry has an index, but it covers source-code files, not the LaTeX manuscript, so the manuscript checks below are byte-level literal checks plus executable harness commands.

## Findings

1. **High / P08 failure: unresolved LaTeX reference.** `paper/main.tex:366` contains `\S \ref{sec:six-signals}`, but the actual signal-section label is `\label{sec:signals}` at `paper/main.tex:467`. My reference checker found exactly one missing reference: `('sec:six-signals', 366)`. This would render as `??` in the PDF and violates P08's requirement that every `\ref{LABEL}` / `\cref{LABEL}` has a matching `\label{LABEL}`.

2. **Medium / P03 failure: two figures are not referenced from prose by label.** The required PDFs exist and can be regenerated, but `paper/main.tex:879` defines `\label{fig:dag}` and `paper/main.tex:889` defines `\label{fig:topology}` with no matching `\ref{fig:dag}`, `\cref{fig:dag}`, `\ref{fig:topology}`, or `\cref{fig:topology}` anywhere in `paper/main.tex`. Only `fig:cfhist` is referenced from prose at `paper/main.tex:837` and labelled at `paper/main.tex:905`. This violates P03's explicit "Each is referenced from paper/main.tex via `\ref{...}` / `\cref{...}`" condition.

3. **High / P02 failure: C06e independent-validation claims are broader than the validation script supports.** The manuscript says every headline number is independently cross-validated by `validate_numbers.py` at `paper/main.tex:1012`-`paper/main.tex:1025` and repeats that "every one" of the six reproducible numbers has been cross-validated at `paper/main.tex:1534`-`paper/main.tex:1537`. For C06e, however, `paper/figures/scripts/validate_numbers.py:304`-`paper/figures/scripts/validate_numbers.py:308` states it does not invoke chardet and only checks PRNG construction; `paper/figures/scripts/validate_numbers.py:349`-`paper/figures/scripts/validate_numbers.py:352` hard-codes the C06e rates/digest in `HARNESS_HEADLINE`; and the comparison table at `paper/figures/scripts/validate_numbers.py:401`-`paper/figures/scripts/validate_numbers.py:440` never adds C06e exact rate, bucket rate, input count, or digest. The generated `validation_report.json` has `all_agree: True`, but its independent C06e digest is `8fbc70630c023315` while the harness headline digest is `58e54831f84183c7`, and C06e is absent from the 21 agreement rows. The harness digest itself is reproducible from `fingerprint_behavior.py`'s corpus construction, but that is not what `validate_numbers.py` currently compares.

## Required Inputs Inspected

- `docs/reviews/2026-05-25-paper-chardet-e2e/verification_report.toml`: full read; P01-P10 closure requirements extracted.
- `tools/review-request-dag.toml`: policy read; confirmed forbidden approval bases, required evidence bases, persistence rule, and terminal verdict requirement.
- `paper/main.tex`: full read, lines 1-1695, plus targeted checks for citations, labels, references, figures, numeric claims, methodology, limitations, and review-process prose.
- `paper/references.bib`: full read, lines 1-515.
- `paper/figures/scripts/validate_numbers.py`: full read, lines 1-473.
- `paper/figures/scripts/validation_report.json`: full read.
- `paper/figures/scripts/jplag_chardet_results.json`, `jplag_options.json`, `jplag_runInfo.json`: parsed with `python3 -m json.tool`.
- `paper/figures/scripts/gen_figures.sh` and `gen_figures.py`: inspected for reproducibility chain.
- `paper/Makefile`: full read.
- Supporting artefacts inspected where the closures required cross-checks: `examples/proof-chardet-relicense/detect.sh`, `extract_signals.py`, `fingerprint_behavior.py`, `CONTRACT_DECLARATION.toml`, `EVIDENCE_MATRIX.toml`, `REVIEW_READINESS.toml`, `VERIFICATION_REPORT.toml`; `SPEC.md`; `core/*kind.toml`; `profiles/*/*kind.toml`; `profiles/agent-assurance/gate-decision-kind.toml`; `profiles/agent-assurance/tiers/*`; `.github/workflows/validate.yml`.

## Executed Checks and Outputs

- `git rev-parse HEAD` -> `1e0e155e32829a3830187815e566893421b931e2`.
- `wc -l paper/main.tex` -> `1695 paper/main.tex`.
- Citation resolution script:
  - `cite_uses 88`
  - `unique_cites 38`
  - `bib_entries 38`
  - `missing []`
  - `unused []`
- JPlag JSON parse:
  - `AVG = 0.00037514616732317244` -> 0.04%
  - `MAX = 0.012958367797077475` -> 1.30%
  - `LONGEST_MATCH = 18.0`
  - `MAXIMUM_LENGTH = 247026.0`
  - `jplag_runInfo.json` reports version 6.3.0 and `totalComparisons = 1`.
- `make -C paper validate` exited 0 and printed all 21 comparison rows as `YES`, then `all agree: True`; it rewrote `paper/figures/scripts/validation_report.json` byte-identically (`git diff -- paper/figures/scripts/validation_report.json` empty).
- Direct C06e validation-report inspection:
  - `all_agree True`
  - `c06e_validation_digest 8fbc70630c023315`
  - `harness_digest 58e54831f84183c7`
  - comparison rows list AUX1, C06a, C06b, C06c, C06d only; no C06e row.
- Direct harness-digest check from `fingerprint_behavior.py`:
  - computed `58e54831f84183c7`.
- `bash examples/proof-chardet-relicense/detect.sh` exited 0 on this host, but C06e emitted `SKIP`:
  - AUX1 `0 matches across 87 v6 / 33 v7 files` PASS
  - C06a `similarity=0.881 v6_nodes=342 v7_nodes=358 v6_edges=488 v7_edges=659` MEASURED
  - C06b `jaccard=0.333 shared=2 v6_only=1 v7_only=3` MEASURED
  - C06c `cosine=0.984 v6_total=652 v7_total=848` MEASURED
  - C06d `shared=5 strict=3 renamed_args=0 diverged=2` MEASURED
  - C06e `behavioural fingerprint skipped: v6 install from worktree failed: ERROR: Failed to build ... when installing build dependencies` SKIP
  - SUMMARY: `MEASURED: 4`, `PASS: 1`, `SKIP: 1`.
- LaTeX structural checker:
  - `brace_delta 0`
  - `begin_minus_end {}`
  - `end_minus_begin {}`
  - `labels 50`
  - `refs 36`
  - `missing_refs [('sec:six-signals', 366)]`
- Style floor:
  - `grep -c $'\u2014' paper/main.tex` -> `0` (grep exit 1 because no matches)
  - banned-vocabulary grep -> `0` (grep exit 1 because no matches)
  - sentence-length sanity computation -> `sentences 325`, `mean 26.412`, `cv 0.714`, above the 0.4 floor.
- Figure existence and reproduction:
  - existing PDFs: `fig1_implementation_dag.pdf` 20498 bytes, `fig2_topology_features.pdf` 15428 bytes, `fig3_control_flow_hist.pdf` 17813 bytes.
  - regenerated figures to `/tmp/.../out` with `gen_figures.py`; output sizes matched the committed PDFs: 20498, 15428, 17813 bytes.
- Toolchain availability:
  - `which pdflatex` and `which bibtex` both failed; TeX build was not executable on this host. P08 was therefore verified by byte-level structural checks.
- P06 spec cross-check:
  - found 19 `*-kind.toml` files.
  - all 19 contain both `[kind.abstraction_class]` and `[kind.capability_envelope]`.
  - `profiles/agent-assurance/gate-decision-kind.toml:200`-`201` defines INV06 with both provider and model-family inequality and explicit conjunctive AND language.
  - profiles present: `agent-assurance`, `cost`, `disclosure`.
  - tier files present: `solo`, `team`, `group`, `organization`, `enterprise`.

## Closure Classification

- P01: complete. Every `\cite...{KEY}` in `paper/main.tex` resolves to a real `@TYPE{KEY,` entry in `paper/references.bib`; no unused or missing keys found by the extraction script.
- P02: incomplete. Most numeric claims trace cleanly to `validation_report.json`, `validate_numbers.py`, or JPlag JSON, but the manuscript overstates C06e independent validation by attributing exact/bucket-rate cross-validation to `validate_numbers.py` when that script does not invoke chardet and does not compare C06e rows.
- P03: incomplete. Figure PDFs exist and regenerate, but `fig:dag` and `fig:topology` are never referenced by `\ref`/`\cref` in prose.
- P04: complete with caveat. Section "The Six Signals" contains subsections for AUX1, C06a, C06b, C06c, C06d, and C06e; the results table reports numeric outcomes for each. The concrete runnable command is centralized in methodology/reproducibility rather than repeated in each subsection, but the measurement source for each signal is identifiable.
- P05: complete. Worktree materialisation, test-file exclusion, determinism, behavioural isolation, and sandbox compatibility each name mechanisms that exist in the harness bytes. The live C06e run degraded to SKIP on this host, which is a documented path.
- P06: complete. The one-page DAG-TOML section matches the current Rust + Go + Python validator triad, toml-test CI coverage, SPEC §12/§13 state, three profiles, five-tier ladder, and INV06 AND predicate.
- P07: complete. U+2014 count is 0, banned-vocabulary grep count is 0, and computed sentence-length CV is 0.714.
- P08: incomplete. Brace and environment balance pass, but `\ref{sec:six-signals}` has no matching label.
- P09: complete. The "Multi-LLM Review Process" section describes dispatch, iteration, persisted review evidence, and terminal decisions in the same pattern encoded in `tools/review-request-dag.toml`; the current review directory already has persisted raw findings and this file adds the required Codex raw finding.
- P10: complete with caveat. The manuscript includes explicit non-claims, construct/internal/external limitations, and preserves the narrow "one repository / one pair / one runner class" framing. The C06e validation wording above still needs correction because it affects the evidence claim, not because the limitations section overclaims the legal conclusion.

## Process Confirmations

- Inspected code: yes; see scripts and harness files listed above.
- Inspected docs: yes; see manuscript, bibliography, Makefile, verification report, review policy, SPEC/profile files listed above.
- Executed tests with output: yes; `make -C paper validate`, figure regeneration to `/tmp`, citation/reference/style scripts, JPlag JSON parsing, and `detect.sh` were run with outputs recorded above.
- Persisted review evidence: yes; this full review is persisted at `docs/reviews/2026-05-25-paper-chardet-e2e/raw_findings/codex.md`.

Terminal verdict: concrete_unresolvable_blocker
Blocker: `paper/main.tex:366` has an unresolved `\ref{sec:six-signals}` even though the actual section label is `paper/main.tex:467` `\label{sec:signals}`; `paper/main.tex:879` and `paper/main.tex:889` define `fig:dag` and `fig:topology` but neither is referenced from prose by `\ref`/`\cref`; and `paper/main.tex:1012`-`paper/main.tex:1025` plus `paper/main.tex:1534`-`paper/main.tex:1537` claim all six headline numbers are independently cross-validated by `paper/figures/scripts/validate_numbers.py`, while `paper/figures/scripts/validate_numbers.py:304`-`paper/figures/scripts/validate_numbers.py:308` says C06e does not invoke chardet and `paper/figures/scripts/validate_numbers.py:401`-`paper/figures/scripts/validate_numbers.py:440` never compares any C06e row.
