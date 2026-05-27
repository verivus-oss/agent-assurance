# Codex R2 review — VERBATIM

Job: `e7954be5-c462-47aa-aa42-c5e874ee30e8`
CLI: `codex`
Correlation: `paper-review-2026-05-23-r2-codex`
Started: 2026-05-22T17:02:41.732Z
Finished: 2026-05-22T17:07:41.698Z
Exit code: 0
Stdout bytes: 7317
Stderr bytes: 241997

---

### 1. SESSION META

Model: Codex / GPT-5 class model; exact runtime minor version not exposed.

Sandbox/approval posture: `workspace-write`; network restricted; approval policy `never`; writable roots include repo, `/tmp`, and `/home/werner/.codex/memories`.

MCP servers available: sqry/ref/exa/GitHub are exposed in tool metadata; no direct `mcp__sqry__*` namespace was loaded in the active tool list, and I used `rg`/direct reads because this review is prose/LaTeX.

Re-derived sha: `6ba15597a36096462cadd55aade3b7bac13c8e7abd86a26b3b53374001437025  paper/main.tex`.

Commands actually run:
- `sha256sum paper/main.tex; git rev-parse HEAD; git status --short paper/main.tex` exit 0.
- `sed -n ... tools/review-request-dag.toml`, R2 bundle, R1 gate/terminal files exit 0.
- `nl -ba paper/main.tex | sed -n ...` for B1-B4 ranges exit 0.
- `nl -ba profiles/agent-assurance/ontology.toml ...`, `nl -ba examples/.../TRACEABILITY.toml ...`, `nl -ba paper/figures/scripts/validate_numbers.py ...` exit 0.
- `rg -n ... validation_report.json jplag...` exit 0.
- `ls -l paper/figures/scripts/sandbox_vs_workstation.txt; test -e ...` exit 1, proving absent.
- `python3 paper/figures/scripts/validate_numbers.py` exit 0; output ended `all agree: True`.
- `python3 -m json.tool paper/figures/scripts/jplag_chardet_results.json` exit 0.
- `make clean && make` in `paper/` exit 2 because `pdflatex` is absent: `make: pdflatex: No such file or directory`.
- R1 sampling `rg`, `wc -l`, current-line inspections exit 0.
- Local JPlag rerun using `/tmp/jplag_chardet/jplag.jar` exit 0; report showed `chardet_v6 84 indexed files`, `chardet_v7 22 indexed files`, and parse-error files still had token counts.

### 2. BLOCKER VERIFICATION

B1 — `partially_fixed`.
Current text fixes the arithmetic direction but introduces/retains a false causal account.

`paper/main.tex:1337-1343` quote: "JPlag tokenised 84 v6 \texttt{.py} files plus 22 v7 \texttt{.py} files, fewer than the extractor's 87 and 33 respectively: JPlag's bundled ANTLR Python 3 grammar emits parse errors on \texttt{chardet/metadata/languages.py} ... and the files JPlag cannot parse are excluded from its token corpus."

Counter-evidence: `paper/figures/scripts/run_jplag.sh:34-39` says JPlag submits only "the chardet/ implementation tree from v6 and the src/chardet/ implementation tree from v7"; my rerun reported exactly 84 and 22 indexed files, and `metadata/languages.py` still had `tokenCount=590`. The lower file count is therefore not proven to be caused by parse-error exclusion.

B2 — `fixed`.

Spec item 3: `paper/main.tex:300-312` quote: "The spec provides the hard-invariants mechanism for declaring closed verdict vocabularies; each bundle declares its own. The core ontology defines only one verdict attribute, \texttt{gate\_decision\_verdict} ... as a closed two-value enum \texttt{pass | fail} ... This bundle's \texttt{TRACEABILITY.toml:40} declares the eight-value evidence-row vocabulary..."

Verifier opening: `paper/main.tex:1121-1124` quote: "The core spec ships three validators that confirm an \texttt{implementation-dag}, \texttt{traceability}, and \texttt{readiness-gate} document conform to their declared schemas."

Supporting inspected evidence: `profiles/agent-assurance/ontology.toml:210-214` defines `values = ["pass", "fail"]`; `examples/proof-chardet-relicense/TRACEABILITY.toml:40` declares the eight-value bundle vocabulary.

B3 — `fixed`.

`paper/main.tex:1009-1027` quote: "For C06e the validation script deterministically re-derives an independent corpus... notes explicitly that it does not invoke \texttt{chardet}... The headline \texttt{corpus\_digest} and the 0/1000 exact-match rate are therefore taken from the persisted harness output, not independently re-derived by \texttt{validate\_numbers.py}".

Verified against `paper/figures/scripts/validate_numbers.py:304-307` and `validation_report.json` keys showing `8fbc70630c023315` vs `58e54831f84183c7`.

B4 — `fixed`.

`paper/main.tex:753-763` quote: "Because all static signals are deterministic functions of the input bytes ... sandboxed and unsandboxed runs are expected to produce identical static signal values. We have observed this ... The side-by-side comparison is not persisted in the bundle; committing \texttt{paper/figures/scripts/sandbox\_vs\_workstation.txt} ... would make the equivalence machine-checkable."

The previous overclaim is downgraded, and the missing file is acknowledged.

### 3. NEW INDEPENDENT FINDINGS

N1, severity high, `paper/main.tex:1339-1343`.

Verbatim quote: "JPlag's bundled ANTLR Python 3 grammar emits parse errors on \texttt{chardet/metadata/languages.py} ... and the files JPlag cannot parse are excluded from its token corpus."

Problem: the current replacement causal clause is not supported by the executed evidence. `run_jplag.sh:34-39` shows the 84/22 counts are the submitted package-tree counts. The local JPlag rerun indexed 84/22 files and still included parse-error files, including `chardet_v6/metadata/languages.py: tokenCount=590`. Parse errors exist, but the paper's "excluded from its token corpus" explanation is false as written.

Suggested fix: rewrite the count sentence to say 84/22 are the submitted `chardet/` and `src/chardet/` package-tree file counts, while the extractor's 87/33 count covers its broader implementation-file enumeration. Keep parse errors as a separate caveat only if the paper states that JPlag still completed and token-counted affected files, or persist evidence proving actual exclusion.

### 4. STILL-OPEN R1 NON-BLOCKER FINDINGS (sample check)

S1-F02, severity low, remains present. `paper/main.tex:88-89` quote: "a self-contained, multi-LLM-reviewed artefact that any reviewer, lawyer, or court can re-run and inspect."

S1-F01, severity medium, remains present. `paper/main.tex:1210-1211` quote: "Two of the three reviewers returned unconditional approval after one or two iteration rounds."

F2-F02, severity low, remains present as time-bound/current-count drift. `paper/main.tex:437-439` quote: "589 plus 228 lines of code respectively (verified via \texttt{wc -l} at commit \texttt{220cff4})." Current `wc -l` output is `589` and `232`.

L3-F01, severity medium, remains present. `paper/main.tex:951-955` quote: "The C06a similarity of 0.881 sits inside the cone of plausible values implied by sqry's structure-level divergence..."

U4-F02, severity medium, remains present. `paper/main.tex:1461-1462` quote: "vendor-published accuracy figures (often in the 98--99\% range on lab corpora)".

Q6-F01, severity low, remains present. `paper/references.bib:626-627` quote: "reported in Section 9.4."

### 5. TERMINAL VERDICT

CONCRETE UNRESOLVABLE BLOCKERS:

1. B1 is still not resolved. `paper/main.tex:1339-1343` attributes the 84/22-vs-87/33 discrepancy to ANTLR parse errors and excluded files. The inspected script at `paper/figures/scripts/run_jplag.sh:34-39` instead shows JPlag was fed only the package trees, and the live JPlag report indexed 84/22 files while still assigning token counts to parse-error files such as `metadata/languages.py`. Unblock by rewriting the sentence to separate submission-scope file counts from parser-error caveats, or persist evidence proving parser exclusion.
