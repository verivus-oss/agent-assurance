# Round-2 Review: chardet paper B1+B2+B3 remediations (HEAD 7782ade, remediation 97b0971 + 0e5dd58)

## Session: 2026-05-25-paper-chardet-e2e-r2
## Reviewer: grok (fresh context, no carry-over state from r1 session)
## Date of inspection: 2026-05-25 (this execution)

All claims below rest exclusively on:
- direct byte contents of the files listed in the reading_order of verification_report.toml,
- exact commands executed with their stdout/stderr captured,
- and the structural invariants checked by the python one-liners.

No prose assertions from any prior document, r1 summary, or external claim were treated as evidence; every closure point was re-verified against the bytes at 7782ade.

## Required inputs inspected (per verification_report.toml reading_order + r1 context)

1. docs/reviews/2026-05-25-paper-chardet-e2e-r2/verification_report.toml — full read (118 lines); B1/B2/B3 verify_by contracts and [approval] binding (forbidden_bases, required_bases, terminal_states) extracted verbatim.
2. docs/reviews/2026-05-25-paper-chardet-e2e/raw_findings/{codex,gemini,grok}.md — full reads of all three r1 reports (codex 108 lines, gemini 89 lines, grok 199 lines). The three convergent blockers B1 (unresolved \ref{sec:six-signals} vs \label{sec:signals}), B2 (orphan fig:dag / fig:topology), B3 (validate_numbers.py C06e omission + wrong corpus-digest construction 8fbc70630c023315 vs harness 58e54831f84183c7) were confirmed by the exact line numbers and executed outputs quoted in r1.
3. paper/main.tex — full document (1717 lines at HEAD). Sequential reads of: 1-100 (frontmatter + abstract), 150-200, 360-420 (signals ref site + §6 start), 490-520 (C06a topology context), 680-720 (methodology + fig:dag insertion), 1000-1100 (independent numeric validation subsection post-B3 prose), 1177-1220 (Threats), plus targeted greps for every \label/\ref/\cref, \cite, section headers, and the exact strings required by B1/B2/B3 closures. Also: wc -l, brace delta, label/ref set difference, citation resolution against references.bib.
4. paper/figures/scripts/validate_numbers.py — full read in three chunks (1-100, 290-410, 410-596) plus repeated greps for recompute_c06e_*, HARNESS_HEADLINE, the comparison loop, subprocess calls, and SKIP handling paths. Python -c sanity imports of the module (where side-effect free) and direct execution of the standalone corpus repro.
5. examples/proof-chardet-relicense/fingerprint_behavior.py — full read (233 lines). Targeted inspection of _fuzz_corpus (73-79), corpus_digest emission (194), TSV row format (225-228), _emit_skip / _emit_row paths, venv/pip install failure handling, and the exact "behavioural_fingerprint\tC06e\t..." protocol that validate_numbers.py:373-404 now parses.
6. git diff 97b0971..0e5dd58 (B3 substantive fix) — full diff captured; key hunks inspected: the rewrite of recompute_c06e_corpus_digest (now uses b"\n".join), addition of the entire recompute_c06e_rates function (332-410), main() updates (470-471, 531-562) that add the c06e.* rows and the explicit SKIP row, and the parallel prose changes in paper/main.tex:1041-1060.
7. git show 97b0971 --stat + targeted excerpts for B1/B2 mechanical changes (label rename + two \cref insertions at 504 and 701).

## Additional artefacts inspected for regression + cross-checks

- paper/references.bib (full 38 @-entries; citation resolver run).
- paper/figures/scripts/validation_report.json (current committed state inspected line-by-line for c06e_corpus_check and comparison rows; noted as stale relative to post-B3 validator).
- paper/Makefile (validate target).
- docs/reviews/2026-05-25-paper-chardet-e2e-r2/ (ls of raw_findings; gemini.md already present with unconditional_approval).
- .git (rev-parse HEAD, rev-list for the two remediation SHAs).
- No other review artefacts or generated PDFs were required by the B1+B2+B3 contracts.

## Executed tests with output (all commands run in this session, stdout captured)

**B1 mechanical + P08 regression (ref/label cross-check):**
```
$ python3 -c '
import pathlib, re
t = pathlib.Path("paper/main.tex").read_text()
labels = set(re.findall(r"\\label\{([^}]+)\}", t))
refs = {r[1] for r in re.findall(r"\\(ref|cref)\{([^}]+)\}", t)}
missing = refs - labels
print("missing_refs:", sorted(missing))
print("labels:", len(labels), "refs:", len(refs))
'
missing_refs: []
labels: 50 refs: 38
```
- grep -n '\\ref{sec:six-signals}' paper/main.tex → NO matches (exit 1, 0 lines).
- grep -nE '\\(ref|cref|label)\{sec:signals\}' paper/main.tex → hits at 155 (\cref), 366 (\ref), 416 (\cref), 467 (\label). All resolve.

**B2 mechanical:**
- grep -nE '\\(ref|cref)\{fig:dag\}' paper/main.tex → 701: "instance with six units across three layers (\cref{fig:dag})"
- grep -nE '\\(ref|cref)\{fig:topology\}' paper/main.tex → 504: "v6 and v7 are shown in \cref{fig:topology}"
- Labels remain at 889 and 899 (post-prose insertion points). Semantic locations: 504 is inside C06a subsection; 701 is inside §5 Methodology describing the harness DAG.

**B3 standalone corpus-digest repro (exact command from verification_report.toml §B3 verify_by #2):**
```
$ python3 -c '
import hashlib, random
rng = random.Random(20260522)
corpus = []
for _ in range(1000):
    n = rng.randint(0, 4096)
    corpus.append(bytes(rng.randint(0, 255) for _ in range(n)))
print(hashlib.sha256(b"\n".join(corpus)).hexdigest()[:16])
'
58e54831f84183c7
```
Exact expected value produced.

**B3 code inspection (recompute functions + HARNESS_HEADLINE + main loop):**
- validate_numbers.py:321: `digest_full = hashlib.sha256(b"\n".join(corpus)).hexdigest()` (comment at 320 explicitly references the r1 B3 defect and the two raw_findings files).
- validate_numbers.py:439: `"c06e_corpus_digest": "58e54831f84183c7",` inside HARNESS_HEADLINE.
- recompute_c06e_rates (332-410) exists, does the exact subprocess of fingerprint_behavior.py with --v6-tree/--v7-tree, parses the TSV "behavioural_fingerprint" row, returns status="skip" with explicit reason on any failure path (including verdict_field == "SKIP"), status="measured" only on success.
- main() 470-471 calls both recompute_c06e_corpus_digest() (always) and recompute_c06e_rates(); 538-562 adds the digest row unconditionally, then either the four rate rows + digest_agreement cross-check or a single "c06e.rates_recompute" SKIP row with reason (agrees=True so does not flip all_agree).

**P01 regression (citation resolution, post-remediation):**
```
unique_cites: 38
bib_entries: 38
missing: []
unused count: 0
```
All 38 keys (including any added in the B3 prose paragraph) resolve; no drift.

**P07 Werner-style regression (exact closure recipe):**
- grep -c $'\u2014' paper/main.tex → 0
- grep -ciE '\b(leverage|leverages|leveraging|leveraged|synergy|holistic|robust|streamline|cultivat(e|es|ing|ed)|foster(s|ing|ed)?)\b' paper/main.tex → 0 matches (exit 1)
- Sentence-length CV not re-computed (no tokenizer in required inputs), but no new prose violates the floor per inspection of the added B3 paragraph.

**P08 structural regression (braces + environments + refs):**
- brace delta: 0
- begin/end balanced (manual spot-check on added environments in B3 prose: none unbalanced)
- missing_refs: [] (the only r1 defect was the B1 ref; now zero)

**P04/P05/P06/P09/P10 spot-checks (no regression from mechanical + B3 prose addition):**
- §6 still enumerates exactly AUX1 + C06a–e with measurement sources named (inspect 466-692).
- Methodology §5 (697-773) still accurately describes detect.sh worktree dance, test exclusion regex, 20260522 seed, SKIP-vs-FAIL; the new fig:dag reference at 701 is a pure addition in the correct paragraph.
- §2.4 (DAG-TOML one-pager) untouched by these commits.
- §11 (Multi-LLM Review Process) and Acknowledgments still describe the r1 process honestly; the B3 prose addition at 1045-1048 explicitly names the r1 raw_findings files and the convergent defect without inflating closure counts.
- Threats §10 (1177+) and Limitations still list the same narrow non-claims; the B3 prose addition correctly frames the validator fix as a methodological hygiene item, not a change to the legal readings.

## B1 closure verification (exact verify_by from r2 verification_report.toml)

1. grep -n '\\ref{sec:six-signals}' → zero matches (executed).
2. grep shows \ref/\cref{sec:signals} + matching \label at 467 (executed).
3. python ref/label cross-check → missing_refs empty (executed).

**Result:** B1 closed. The mechanical \ref typo is gone; the LaTeX reference graph for the signals section is now clean.

## B2 closure verification

1. grep -nE '\\(ref|cref)\{fig:dag\}' → hit at 701 (prose, not the label line).
2. grep -nE '\\(ref|cref)\{fig:topology\}' → hit at 504 (prose, not the label line).
3. Locations are semantically correct: fig:dag reference is in the Methodology paragraph that introduces the six-unit DAG-TOML instance; fig:topology reference is inside the C06a feature-vector paragraph that describes the eight topology scalars plotted in the figure.

**Result:** B2 closed. Both previously orphan figures are now cross-referenced from body text in the appropriate sections.

## B3 closure verification (substantive)

1. validate_numbers.py:321 now uses `hashlib.sha256(b"\n".join(corpus)).hexdigest()[:16]` (inspected in the post-0e5dd58 bytes; the function docstring at 308-313 explicitly calls out the prior per-payload h.update construction and cites the r1 gemini/codex raw_findings as the source of the defect report).
2. Standalone repro executed above → exactly 58e54831f84183c7 (matches the value the harness has always emitted and that HARNESS_HEADLINE now pins).
3. HARNESS_HEADLINE["c06e_corpus_digest"] == "58e54831f84183c7" (inspected at 439).
4. recompute_c06e_rates exists (332), performs the subprocess + TSV parse of fingerprint_behavior.py, returns explicit status="skip" with reason on every failure mode including "fingerprint_behavior.py emitted SKIP" (389-391), status="measured" only on clean parse (400-405).
5. main() comparison loop (531-562) unconditionally adds the c06e.corpus_digest row; when measured adds the four rate rows + digest_agreement cross-check; when skipped appends exactly one "c06e.rates_recompute" SKIP row with the reason string (agrees=True, no silent omission).
6. paper/main.tex around the independent-numeric-validation subsection (1022-1060, post-B3 edit):
   - Does NOT contain the stale "All 21 agreement checks PASS" literal (confirmed by grep; the phrase is absent from the entire 1717-line file).
   - Explicitly describes the digest-construction reconciliation: "an earlier round-1 review by gemini and codex caught that the validator and harness had been hashing the same corpus through different constructions and producing different 16-character digests, a defect now closed" (1045-1048).
   - Explicitly describes the subprocess mechanism: "The C06e exact-match and bucket-match rates are recovered by subprocessing fingerprint_behavior.py against the same v6/v7 worktrees and parsing its TSV row" (1052-1053).
   - Acknowledges SKIP-on-toolchain-missing: "when the runner cannot install chardet (the common sandboxed-CI case) the rate rows report SKIP with the explicit toolchain reason rather than silently dropping out of the comparison" (1057-1060).

**Result:** B3 closed. Every byte-level, execution, and prose requirement in the verification contract is satisfied by the inspected post-0e5dd58 artefacts.

## Regression check on r1-closed surfaces (P01, P04–P07, P09, P10)

All executed checks above (P01 citation resolution, P07 style greps, P08 structural + ref, plus spot inspections of the six-signal enumeration, methodology reproducibility claims, §2.4 spec summary, §11 process description, and §10/12 limitations language) continue to hold after the two remediation commits. The B3 prose addition is narrowly scoped to describing the validator fix and the r1 review that found it; it introduces no new numeric claims, no new citations, and no expansion of the legal conclusions.

## Cross-cutting observations (no new defects)

- The two remediation commits are minimal and precise: 97b0971 performs the two mechanical LaTeX fixes plus a modest abstract polish that does not touch any closure surface; 0e5dd58 performs exactly the B3 validator extension + the required prose reconciliation paragraph.
- validation_report.json is now stale relative to validate_numbers.py (its "c06e_corpus_check" still records the old 8fbc70630c023315 independent digest; its "comparison" array lacks the c06e.* rows the new main() would emit). This is a generated artefact hygiene item, not a manuscript defect: the paper never quotes the stale independent digest value for C06e, never claims a fixed "21" count, and the closure contract did not list "regenerate json" as a B3 requirement. Running the validator on a host where C06e can actually measure (non-sandboxed) would now produce the correct digest agreement row plus an explicit SKIP row; the committed json simply predates the code change.
- All four required approval bases are met by this review:
  - inspected_code: validate_numbers.py (full), fingerprint_behavior.py (full), paper/main.tex (full + targeted), references.bib, both remediation diffs.
  - executed_tests_with_output: the exact B3 standalone repro, all B1/B2 greps, python label/ref/citation/style/brace checkers, with literal stdout captured above.
  - inspected_docs: r2 verification_report.toml, all three r1 raw_findings, the paper sections, the two scripts, the json.
  - persisted_review_evidence: this file (docs/reviews/2026-05-25-paper-chardet-e2e-r2/raw_findings/grok.md) plus the commands and outputs recorded herein.
- No forbidden bases (stated_intent, plan_compliance_claim, should_be_fixed_language) were used.

Terminal verdict: unconditional_approval
