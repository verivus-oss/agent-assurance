# Codex r2 Review: chardet paper B1/B2/B3 remediations

Reviewer: Codex, fresh-context r2
Target HEAD: `7782ade`
Remediation commits inspected: `97b0971` and `0e5dd58`
Date: 2026-05-25

I verified against the bytes in the workspace and the executed command outputs below, not against the remediation intent.

## Required Inputs Inspected

- `docs/reviews/2026-05-25-paper-chardet-e2e-r2/verification_report.toml`
- r1 blocker files: `docs/reviews/2026-05-25-paper-chardet-e2e/raw_findings/codex.md`, `gemini.md`, and `grok.md`
- `paper/main.tex` in full
- `paper/figures/scripts/validate_numbers.py`
- `examples/proof-chardet-relicense/fingerprint_behavior.py`
- `git diff b759eaf..97b0971 -- paper/main.tex`
- `git diff 97b0971..0e5dd58`

## Closure Checks

### B1: closed

- `grep -n '\\ref{sec:six-signals}' paper/main.tex || true` produced no matches.
- `grep -n '\\ref{sec:signals}\\|\\cref{sec:signals}\\|\\label{sec:signals}' paper/main.tex` produced live refs at lines 155, 366, and 416 plus the matching `\label{sec:signals}` at line 467.
- A Python label/ref checker over `paper/main.tex` reported `labels 50`, `refs 38`, `missing_refs []`.

### B2: closed

- `grep -nE '\\(ref|cref)\{fig:dag\}' paper/main.tex` produced `701:instance with six units across three layers (\cref{fig:dag}): three`, which is prose in the Methodology section.
- `grep -nE '\\(ref|cref)\{fig:topology\}' paper/main.tex` produced `504:v6 and v7 are shown in \cref{fig:topology}; v7 is larger on every`, which is prose in the C06a section.
- The figure labels remain at `paper/main.tex:889` (`fig:dag`) and `paper/main.tex:899` (`fig:topology`).

### B3: incomplete

The code-side C06e fixes are present:

- `paper/figures/scripts/validate_numbers.py:301`-`329` defines `recompute_c06e_corpus_digest` with `hashlib.sha256(b"\n".join(corpus)).hexdigest()` and returns the first 16 hex characters, matching `examples/proof-chardet-relicense/fingerprint_behavior.py:193`-`194`.
- `HARNESS_HEADLINE["c06e_corpus_digest"]` is `58e54831f84183c7` at `paper/figures/scripts/validate_numbers.py:439`.
- `paper/figures/scripts/validate_numbers.py:334`-`406` defines `recompute_c06e_rates`, subprocesses `fingerprint_behavior.py`, parses the TSV row, and returns `status: "skip"` with an explicit reason on SKIP.
- `paper/figures/scripts/validate_numbers.py:538`-`561` always adds `c06e.corpus_digest`, adds C06e rate rows when measured, and appends an explicit `c06e.rates_recompute` SKIP row when the subprocess cannot measure rates.
- The standalone required digest repro printed exactly `58e54831f84183c7`.
- `python3 paper/figures/scripts/validate_numbers.py --output /tmp/codex-r2-validation-report.json` exited 0. Its C06e rows were:
  - `c06e.corpus_digest`: harness `58e54831f84183c7`, independent `58e54831f84183c7`, `YES`
  - `c06e.rates_recompute`: `SKIP: fingerprint_behavior.py emitted SKIP: behavioural fingerprint skipped: v6 install from worktree failed: ERROR: Failed to build 'file:///tmp/validate-numbers-qe1z12o6/v6' when installing build dependencies`, `YES`
  - `all agree: True`

The manuscript still contains a stale overclaim in the conclusion. `paper/main.tex:1556`-`1559` says the six reproducible numbers are “every one of which has been independently cross-validated against a scipy / numpy implementation in `paper/figures/scripts/validate_numbers.py`.” That is not true for C06e at HEAD. The bytes show C06e corpus validation is a deterministic stdlib `random`/`hashlib` digest re-derivation, and C06e exact/bucket rates are recovered by subprocessing the harness script `fingerprint_behavior.py`, not by a scipy/numpy second implementation. This is the same class of validation-scope overclaim that B3 was meant to close; the more detailed §10.3 paragraph is corrected, but the conclusion reintroduces the false global claim.

## Regression Checks

- Citation resolution over `paper/main.tex` and `paper/references.bib`: `cite_uses 88`, `unique_cites 38`, `bib_entries 39`, `missing []`.
- LaTeX structural check: `brace_delta 0`, `begin_minus_end {}`, `end_minus_begin {}`, `missing_refs []`.
- Style floor: `u2014_count 0`, banned-vocabulary count `0`, sentence-length sanity `sentences 380`, `mean 27.85`, `cv 0.775`.
- `rg -n "All 21 agreement checks PASS|All 21" paper/main.tex || true` produced no matches.

## Process Confirmations

- Inspected code: yes.
- Inspected docs: yes.
- Executed tests with output: yes; see grep/ref checks, standalone digest repro, `validate_numbers.py`, citation/reference/style/structure checks above.
- Persisted review evidence: yes; this file is the persisted r2 Codex raw finding.

Terminal verdict: concrete_unresolvable_blocker
Blocker: `paper/main.tex:1556`-`paper/main.tex:1559` still claims all six reproducible numbers are independently cross-validated against a scipy / numpy implementation in `paper/figures/scripts/validate_numbers.py`, but the HEAD bytes show C06e is not: `paper/figures/scripts/validate_numbers.py:301`-`329` re-derives the digest with stdlib `random`/`hashlib`, and `paper/figures/scripts/validate_numbers.py:334`-`406` recovers C06e exact/bucket rates by subprocessing `examples/proof-chardet-relicense/fingerprint_behavior.py`; this surviving conclusion sentence is therefore a concrete B3 validation-scope overclaim.
