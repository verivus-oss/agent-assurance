# End-to-end review of paper-hello-world/main.tex (HEAD 1e0e155)

Fresh-context review performed 2026-05-25. I read exactly the four required artifacts listed in verification_report.toml: the verification_report.toml itself (10 closures H01-H10), paper-hello-world/main.tex (479 lines), paper-hello-world/references.bib (15 entries), and the full examples/proof-hello-world/ tree (5 normative TOMLs + 3 executable witnesses + 8 source files under src/).

I then performed additional grounded inspections and executions required by the binding rules (inspected_code, executed_tests_with_output, inspected_docs). All observations below are tied to specific file:line locations or captured command output.

## H01 — Every \cite{KEY} resolves to a real bib entry

I extracted every citation key from paper-hello-world/main.tex:

```
acmBadging2020
arxivSubmitTex2026
arxivTexLive2026
cheers2021robustness
falleri2014gumtree
feldt2010validity
hoffman1988trace
jiang2007deckard
poplArtifact2023
prechelt2002jplag
ralph2020empirical
roy2009clone
runeson2009case
schleimer2003winnowing
sigsoftStandards
```

I extracted every `@...{KEY,` entry from paper-hello-world/references.bib. The two sets are identical (15 keys). No missing or extra keys. H01 holds.

## H02 — Every command in Table 2 actually runs and produces the claimed output

I executed every command listed in the verify_by block and in Table 2 (paper-hello-world/main.tex:228-264), capturing full output and exit status. Repository root: /srv/repos/external/verivus-oss/agent-assurance. Toolchains present: rustc 1.90, go 1.26.3, cc (gcc 15.2), java (runtime only, no javac), node v24.15 (no tsc), awk 5.3.2, python3, sqry 16.0.6, rg.

**Executed:**

```
$ bash examples/proof-hello-world/run_all.sh
proof-hello-world: enforcing CONTRACT_DECLARATION.toml C01 on each language

  PASS  rust       stdout=$'Hello, world!\n' exit=0 stderr=empty
  PASS  go         stdout=$'Hello, world!\n' exit=0 stderr=empty
  PASS  c          stdout=$'Hello, world!\n' exit=0 stderr=empty
  SKIP  java       javac/java not on PATH
  PASS  typescript stdout=$'Hello, world!\n' exit=0 stderr=empty
  PASS  awk        stdout=$'Hello, world!\n' exit=0 stderr=empty

summary: 5 pass, 1 skip, 0 fail
```
(exit 0, matches the 5/1/0 row in Table 2 at main.tex:229-231)

```
$ bash examples/proof-hello-world/detect_awk_rewrite.sh
proof-hello-world: AWK rewrite detection witness

  PASS  plain greeting literal is absent from AWK rewrite source
  PASS  CONTRACT_DECLARATION.toml declares C06 and its witness
  PASS  canonical AWK implementation satisfies CONTRACT C01
  PASS  AWK rewrite still satisfies CONTRACT C01
  PASS  canonical and rewritten AWK share the declared intent profile
  PASS  AWK static source profile matches C06

summary: 6 pass, 0 skip, 0 fail
```
(exit 0, matches the 6/0/0 row at main.tex:234-235)

```
$ bash examples/proof-hello-world/detect_semantic_rewrite.sh
proof-hello-world: semantic AST rewrite witness

  PASS  plain greeting literal is absent from source text
  PASS  convoluted implementation still satisfies CONTRACT C01
  FAIL  sqry did not resolve AST function symbol: concealedBytes
  FAIL  sqry did not resolve AST function symbol: renderLine
  FAIL  sqry did not resolve AST function symbol: emit
  FAIL  sqry did not resolve AST function symbol: main
  FAIL  sqry did not resolve caller edge: main -> renderLine
  FAIL  sqry did not resolve import edge: fmt

summary: 2 pass, 0 skip, 6 fail
```
(exit 1; Table 2 at main.tex:232-233 claims "8 pass, 0 skip, 0 fail. Go rewrite witness passed.")

The remaining validator and make commands were executed with full output captured (see H03/H06/H07 for the subset that directly verifies paper claims; all structural validators, closure-root, IJB with and without --repo-root, code-symbols, and `make toml-conformance-all` were run). The Go-side toml-conformance run produced exactly "13 skipped", "185 valid, 0 failed", "358 invalid, 0 failed". The Rust-side produced "185 valid", "371 invalid", "zero skips". These match the parenthetical counts in the final row of Table 2 (main.tex:260-264).

## H03 — Implementation DAG validator's computed values match the paper

I executed:

```
$ python3 validators/validate_implementation_dag.py examples/proof-hello-world/IMPLEMENTATION_DAG.toml
IMPLEMENTATION DAG VALIDATION PASSED
- file: .../examples/proof-hello-world/IMPLEMENTATION_DAG.toml
- units: 9
- layers: {0: 8, 1: 1}
- critical_path_loc: 138
```
(exit 0)

The [computed] section of examples/proof-hello-world/IMPLEMENTATION_DAG.toml:158-167 declares:
- entry_points = ["U01", "U02", "U03", "U04", "U05", "U07", "U08", "U09"]
- leaf_nodes = ["U06", "U07", "U09"]
- critical_path = ["U05", "U06"]
- critical_path_loc = 138

These match the bullet list at paper-hello-world/main.tex:208-213 and the H03 verify_by criteria exactly. H03 holds.

## H04 — Claim audit table (Table 3) is one-to-one with §3 contracts and Table 2 evidence

I inspected the longtable at paper-hello-world/main.tex:309-344 (Table 3 / tab:claims). Every row names an evidence source (file path or citation), a status ("Directly observed", "Directly observed plus narrow inference", "Cited"), and a counterexample boundary ("Does not imply production readiness", "A runner without those toolchains would produce more SKIPs", "Does not prove arbitrary obfuscation resistance", etc.).

Cross-check against Table 1 contracts (main.tex:152-181):
- C01 is covered by claim row 2 ("The available canonical implementations satisfy C01... run_all.sh corrected byte comparison").
- C05 is covered by claim row 3 (go_convoluted + detect_semantic_rewrite.sh).
- C06 is covered by claim row 4 (LANGUAGE-VALIDATORS.md + validate_code_symbols.py + detect_awk_rewrite.sh).
- C02–C04 are narrowings that inherit from C01 via depends_on in CONTRACT_DECLARATION.toml:51,66,77; the audit table's C01 row plus the Limitations section together address them.

Cross-check against Table 2 commands: run_all.sh, both detect_*.sh, the three Python validators, validate_code_symbols.py, and the toml-conformance make target are all referenced as evidence in at least one claim row or in the H02 execution record. H04 holds on the narrow mapping the paper actually performs.

## H05 — §1 spec-backdrop paragraph accurately describes HEAD 1e0e155

The paragraph at paper-hello-world/main.tex:95-118 names:
- tools/dagtoml-validate-rs/ and tools/dagtoml-validate-go/ (both directories and their binaries exist on disk; I executed both binaries against IMPLEMENTATION_DAG.toml and received "DAGTOML VALIDATION PASSED").
- the toml-test conformance harness (Makefile: toml-conformance, toml-conformance-rs, toml-conformance-all targets exist; I ran make toml-conformance-all successfully).
- SPEC §12 (closure-root) and SPEC §13 (abstraction class + capability envelope) — both sections exist (SPEC.md:851 and SPEC.md:1195).
- three profiles (agent-assurance, cost, disclosure) — directories profiles/agent-assurance/, profiles/cost/, profiles/disclosure/ all exist with PROFILE.toml and ontology files.
- the deployment-tier ladder (profiles/agent-assurance/tiers/ contains solo/team/group/organization/enterprise.toml plus README.md).
- INV06 — declared as a hard invariant in profiles/agent-assurance/gate-decision-kind.toml:200-201 with the exact cross-provider AND predicate text.

All named artifacts exist at HEAD. H05 holds.

## H06 — Werner Style Spec sanity floor

I executed three checks on the manuscript source:
- U+2014 count in paper-hello-world/main.tex: 0
- literal "---" (LaTeX em-dash) count: 0
- banned C78 vocabulary (leverage|synergy|holistic|robust|streamline|cultivate|foster and inflections): 0 matches (case-insensitive regex over whole file)

Sentence-length CV (rough split on . ! ? after stripping simple LaTeX commands): 0.839 (135 sentences, mean 19.8 words, sd 16.6). This is >= 0.4. All four sub-conditions of H06 hold.

## H07 — LaTeX structural integrity

I parsed paper-hello-world/main.tex:
- { count = 219, } count = 219, balance = 0
- 12 \begin and 12 \end; per-environment counts match exactly (itemize x4, tabularx x2, table x2, abstract, lstlisting, longtable, document)
- \ref / \cref targets: tab:claims, tab:commands, tab:contracts — all three have exact matching \label entries in the same file; zero unresolved references, zero unused labels.

H07 holds.

## H08 — Acknowledgments section names real tools + real reviewers

The section added at paper-hello-world/main.tex:460-474 (post 1e0e155 edit) names:
- tools/dagtoml-validate-rs/, tools/dagtoml-validate-go/, validators/, tools/toml-test-decode-rs/ — all four paths exist on disk (I listed and executed binaries under the first two).
- toml-lang/toml-test maintainers — the conformance corpus is the real upstream project; I ran the harness against it via make.
- multi-LLM review panel (codex, gemini, grok) under tools/review-request-dag.toml — the docs/reviews/ tree contains prior sessions that used exactly those three providers.

H08 holds on literal presence and path existence.

## H09 — Conclusion (Werner-rewritten in 1e0e155) does not over-claim

The Conclusion at paper-hello-world/main.tex:441-458 is a single ~110-word sentence. It opens with the explicit concession "I will not pretend this proof carries more than it does, because the whole point of declaring a narrow contract is that it stays narrow". It closes with the bounded qualifier "inside one repository, on one runner, on one day". It enumerates the exact artefacts inspected (six implementations, nine DAG units, five normative TOMLs, three witness scripts, twelve validator commands) and the exact observed outcomes (5+1, 8, 6, structural validators all passed, IJB --repo-root requirement observed). It does not use the words "semantic equivalence", "paraphrase resistance at scale", "production assurance", "benchmark", or "general". H09 holds.

## H10 — Limitations and Non-Claims section enumerates real exclusions

The section at paper-hello-world/main.tex:419-437 lists exactly the six exclusions required by the H10 verify_by:
- general semantic equivalence between arbitrary programs
- arbitrary obfuscation resistance
- broad AWK AST similarity or parser-backed AWK analysis
- copyright, licensing, or authorship conclusions
- production readiness for real assurance workflows
- performance, scalability, precision, recall, or benchmark results

The following paragraph ("The exact claim is narrower...") restates the positive claim in the same bounded language used in the abstract and conclusion. H10 holds.

## Additional observations grounded in inspected_code + executed_tests_with_output

1. examples/proof-hello-world/run_all.sh:29 and :37 still perform `actual_stdout="$(cat "${out}")"` followed by string comparison against the literal "Hello, world!" (no trailing LF). The outer expected variable contains the \n, but it is only used for the PASS log line, never for the actual byte check. There is no `cmp` against a 14-byte reference file anywhere in the script. This is the exact pre-correction logic described (and claimed fixed) in the paragraph at paper-hello-world/main.tex:275-281.

2. When I executed detect_semantic_rewrite.sh, sqry 16.0.6 emitted ANSI color codes into the capture file (visible via cat -A as ^[[33m, ^[[1m etc.). The subsequent grep -Eq word-boundary patterns (lines 72, 82, 91) therefore failed to match the four function symbols and two edges even though sqry's own output clearly listed "function concealedBytes", "function renderLine", "function emit", "function main", the caller edge, and the import edge. The script performs no color stripping and passes no --color=never / NO_COLOR=1. Result: 6 FAILs instead of the 8 PASSes asserted for this exact command in Table 2.

3. I inspected the six canonical sources and two rewrite fixtures under examples/proof-hello-world/src/ (rust/hello.rs:3-5, go/hello.go:7-9, c/hello.c, java/Hello.java, typescript/hello.ts, awk/hello.awk:3-5, go_convoluted/hello.go:5-28, awk_convoluted/hello.awk:2-13). The convoluted Go and AWK sources contain no contiguous "Hello, world!" literal, yet both still produce the required bytes at runtime (confirmed by the PASS lines in the two witness executions above). The AWK rewrite contains exactly the BEGIN + render + split + for + sprintf("%c" profile markers asserted by CONTRACT_DECLARATION.toml:95 and checked by detect_awk_rewrite.sh:113-151.

4. I read docs/LANGUAGE-VALIDATORS.md:16-23 (the supported language list contains only Rust/Go/TypeScript/Java; AWK is absent) and validators/validate_code_symbols.py:1-58 (the --languages default and the skip logic). This confirms the "unsupported language" premise used for C06 in the claim audit table row 4.

5. All five proof TOMLs carry the exact empty-closure sentinel required by SPEC §12.1 (closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"). validate_closure_root.py --discover on the directory reports "CLOSURE-ROOT VALIDATION PASSED (5 file(s))".

6. I executed the IJB validator both without and with --repo-root on all five TOMLs. Without the flag every instance file produces the exact error text "instance files require --repo-root" and exits 1. With the flag all five exit 0 and report "IJB CONFORMANCE VALIDATION PASSED". This matches the two-row demonstration in Table 2 at main.tex:252-256.

## Persisted review evidence

This file (docs/reviews/2026-05-25-paper-hello-world-e2e/raw_findings/grok.md) is the persisted review evidence. It was written after the inspections and executions above; every factual claim in it is traceable to a read_file result, a run_command output block, or a grep result on a specific path.

Terminal verdict: concrete_unresolvable_blocker
Blocker: The manuscript asserts at paper-hello-world/main.tex:275-281 that the witness scripts "were therefore corrected to compare output files with cmp against an explicit Hello, world!\n byte stream" and that "The outcomes in Table 2 are from the corrected witnesses", but direct inspection of the artefact at examples/proof-hello-world/run_all.sh:25-52 (check_contract function) shows it still uses command substitution `actual_stdout="$(cat "${out}")"` plus a no-newline string literal comparison with zero uses of cmp; the trailing LF byte required by CONTRACT_DECLARATION.toml:28 and by the C01 statement in main.tex:160 is therefore never actually verified by the load-bearing executable witness whose results are reported in Table 2.