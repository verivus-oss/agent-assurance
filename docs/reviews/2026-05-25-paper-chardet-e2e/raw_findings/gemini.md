# Gemini Review: paper/main.tex (chardet relicensing manuscript)

**Date:** 2026-05-25  
**HEAD:** 1e0e155  
**Target:** `paper/main.tex`  

## Executive Summary
The manuscript provides a comprehensive structural analysis of the `chardet` v6 vs v7 relicensing dispute, supported by a reproducible detection harness and independent validation. However, the manuscript fails on two counts of the `verification_report.toml` (P03 and P02) related to figure references and the integrity of the independent validation claim.

## Findings by Closure

### P01: Every \cite{KEY} resolves to a real bib entry
**Status: PASS**
- **Inspected Docs:** `paper/main.tex`, `paper/references.bib`.
- **Executed Tests:** Extracted every `\cite` key from `main.tex` and compared against the keys in `references.bib` using `comm`.
- **Output:** All 32 unique cited keys are present in the bibliography.

### P02: Every claim with a specific number has a verifiable source
**Status: FAIL**
- **Inspected Code:** `paper/figures/scripts/validate_numbers.py`.
- **Inspected Docs:** `paper/main.tex`.
- **Executed Tests:** Ran `make validate` in the `paper/` directory.
- **Evidence:**
  - The manuscript claims (lines 1620-1621): *"every one of which [the six signal numbers] has been independently cross-validated against a scipy / numpy implementation in paper/figures/scripts/validate_numbers.py"*.
  - Inspection of `validate_numbers.py` (lines 351-381) reveals that `C06e` (Exact match rate, Bucket match rate, and Corpus digest) is **omitted** from the `comparison` list that determines the `all_agree` status.
  - Furthermore, the independent `recompute_c06e_corpus_digest` function in `validate_numbers.py` (lines 280-295) computes a digest of `8fbc70630c023315` (by hashing the concatenated payloads), which diverges from the harness's reported digest of `58e54831f84183c7` (which hashes the `\n`-joined payloads). 
  - While the headline match rates (0/1000) are likely correct, the claim of independent cross-validation for "every one" of the six signals is technically false in the context of the provided validation script.

### P03: Every figure exists, is referenced from the text, and reproducible
**Status: FAIL**
- **Inspected Docs:** `paper/main.tex`.
- **Executed Tests:** `grep -n "fig:dag" paper/main.tex` and `grep -n "fig:topology" paper/main.tex`.
- **Evidence:**
  - Figure 1 (`\label{fig:dag}`) and Figure 2 (`\label{fig:topology}`) are defined on lines 879 and 889 respectively.
  - Neither label is referenced anywhere in the manuscript prose via `\ref` or `\cref`. This violates the requirement: *"Each is referenced from paper/main.tex via \ref{...} / \cref{...}"*.

### P04: Six signals C06a-e + AUX1 each have an enumeration section AND a measurement source
**Status: PASS**
- **Inspected Docs:** `paper/main.tex`.
- **Evidence:**
  - Section 4 ("The Six Signals") contains subsections 4.1 through 4.6 for each signal.
  - Section 8.1 ("Headline numbers") reports the results in Table 4.

### P05: Methodology section is reproducible from the bytes
**Status: PASS**
- **Inspected Code:** `examples/proof-chardet-relicense/detect.sh`.
- **Inspected Docs:** `paper/main.tex` Section 5.
- **Evidence:** The commands described in Section 5 (e.g., `git worktree add --detach`) match the implementation in the harness script.

### P06: DAG-TOML spec section (§2.4)
**Status: PASS**
- **Inspected Code:** `tools/dagtoml-validate-rs/`, `tools/dagtoml-validate-go/`, `validators/`, `profiles/agent-assurance/gate-decision-kind.toml`.
- **Evidence:** 
  - The "triad" of validators (Rust, Go, Python) exists.
  - `profiles/agent-assurance/gate-decision-kind.toml` contains the INV06 cross-provider self-modification check as described.
  - SPEC §12 (`closure_root`) and §13 (`abstraction_class`) are present in the kind descriptors.

### P07: Werner Style Spec sanity floor
**Status: PASS**
- **Executed Tests:**
  - `grep -c $'\u2014' paper/main.tex` -> 0 matches.
  - `grep -ciE '\b(leverage|...)\b' paper/main.tex` -> 0 matches.
- **Evidence:** The source is free of U+2014 and banned vocabulary.

### P08: LaTeX structural integrity
**Status: PASS**
- **Executed Tests:**
  - `python3 -c 'import pathlib; t = pathlib.Path("paper/main.tex").read_text(); print(t.count("{") - t.count("}"))'` -> 0.
- **Evidence:** Brace balance is maintained.

### P09: Multi-LLM review process section
**Status: PASS**
- **Inspected Docs:** `paper/main.tex` Section 11.
- **Evidence:** The section honestly describes the dispatch/iteration pattern and acknowledges the Gemini quota failure.

### P10: Threats to Validity and Limitations
**Status: PASS**
- **Inspected Docs:** `paper/main.tex` Sections 10 and 12.
- **Evidence:** The paper explicitly acknowledges that the signals are proxies and does not claim to measure training-data provenance.

## Persisted Review Evidence
- `cited_keys.txt` vs `bib_keys.txt` (P01 verify)
- `validation_report.json` (P02 verify)
- `grep` outputs (P03 and P07 verify)

## Terminal Verdict
Terminal verdict: concrete_unresolvable_blocker
Blocker: The manuscript violates P03 as Figure 1 (fig:dag) and Figure 2 (fig:topology) are defined but never referenced in the prose. Additionally, it violates P02 as the claim in Section 14 (lines 1620-1621) that "every one" of the six signals has been "independently cross-validated" by validate_numbers.py is false; the script omits C06e from its comparison logic and fails to reproduce the harness's C06e corpus digest (8fbc70630c023315 vs 58e54831f84183c7).
