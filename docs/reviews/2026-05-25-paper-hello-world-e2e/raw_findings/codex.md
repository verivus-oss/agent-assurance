# Codex review: paper-hello-world/main.tex

Reviewer: codex
Date: 2026-05-25
HEAD under review: 1e0e155
Target: paper-hello-world/main.tex

## Inspected material

- docs/reviews/2026-05-25-paper-hello-world-e2e/verification_report.toml
- tools/review-request-dag.toml policy tables
- paper-hello-world/main.tex
- paper-hello-world/references.bib
- examples/proof-hello-world/CONTRACT_DECLARATION.toml
- examples/proof-hello-world/IMPLEMENTATION_DAG.toml
- examples/proof-hello-world/TRACEABILITY.toml
- examples/proof-hello-world/REVIEW_READINESS.toml
- examples/proof-hello-world/EVIDENCE_MATRIX.toml
- examples/proof-hello-world/run_all.sh
- examples/proof-hello-world/detect_semantic_rewrite.sh
- examples/proof-hello-world/detect_awk_rewrite.sh
- SPEC.md, Makefile, .github/workflows/validate.yml, profiles/agent-assurance/, profiles/cost/, profiles/disclosure/

## Findings

### High: the paper claims the newline-byte bug was corrected, but the shipped witnesses still use command substitution and accept missing trailing LF

paper-hello-world/main.tex:275-281 says the original shell comparison stripped trailing newlines, then says the witness scripts were corrected to compare output files with `cmp` against an explicit `Hello, world!\n` byte stream and to check stderr by file size. The current bytes do not match that statement. examples/proof-hello-world/run_all.sh:28-39 reads stdout with `actual_stdout="$(cat "${out}")"` and compares it to `"Hello, world!"`, not to the 14-byte stream. examples/proof-hello-world/detect_semantic_rewrite.sh:53-55 and examples/proof-hello-world/detect_awk_rewrite.sh:62-76 repeat the same pattern for their runtime C01 checks. I verified the behavior with a minimal reproduction: `printf 'Hello, world!'` captured through the same command-substitution comparison prints `no-newline stdout would satisfy current run_all comparison`. This contradicts CONTRACT_DECLARATION.toml:26-28, which requires exact `Hello, world!\n` bytes, and EVIDENCE_MATRIX.toml:40-45, which says PASS witnesses show stdout equals `Hello, world!\n`.

### High: the Table 2 traceability command, as printed in the verification recipe, does not exit 0

The verification report requires running `python3 validators/validate_traceability.py examples/proof-hello-world/TRACEABILITY.toml --check-paths-exist` (docs/reviews/2026-05-25-paper-hello-world-e2e/verification_report.toml:53-55), and Table 2 reports the traceability command with `--check-paths-exist` exits 0 and has path checks enabled (paper-hello-world/main.tex:244-245). Running that exact command from repo root returned exit 1:

```text
TRACEABILITY VALIDATION FAILED
- --check-paths-exist requires --repo-root
...
```

The corrected command, `python3 validators/validate_traceability.py examples/proof-hello-world/TRACEABILITY.toml --repo-root . --check-paths-exist`, returned exit 0 with:

```text
TRACEABILITY VALIDATION PASSED
- entities: 30
- repo_root: /srv/repos/external/verivus-oss/agent-assurance
- path existence checks: enabled
```

So the underlying traceability artifact is healthy, but the paper/review recipe's executable claim is false as written.

### Medium: Table 3 is not one-to-one with Table 2 command evidence

H04 requires every Table 2 command to be referenced as evidence for at least one Table 3 claim (verification_report.toml:73-80). Table 3 names `run_all.sh`, `detect_semantic_rewrite.sh`, `detect_awk_rewrite.sh`, `validators/validate_code_symbols.py`, the five proof TOMLs, and generic "validators" (paper-hello-world/main.tex:314-333). It does not explicitly reference the primary Rust validator command, the primary Go validator command, closure-root validation, IJB conformance with/without `--repo-root`, or `make toml-conformance-all` from Table 2 (paper-hello-world/main.tex:236-264). The Table 2 evidence was executable and mostly passed, but the audit table is not one-to-one with it.

## Closure checks

H01 citations: pass. I extracted all `\cite...{}` keys from main.tex and all bibliography keys from references.bib. The cited keys and bib keys are the same 15-key set: acmBadging2020, arxivSubmitTex2026, arxivTexLive2026, cheers2021robustness, falleri2014gumtree, feldt2010validity, hoffman1988trace, jiang2007deckard, poplArtifact2023, prechelt2002jplag, ralph2020empirical, roy2009clone, runeson2009case, schleimer2003winnowing, sigsoftStandards. Missing keys: none. Unused keys: none.

H02 observed execution: fail for the exact traceability command and for the newline-byte witness claim; otherwise the listed commands I ran matched the reported outcomes.

Executed outputs:

```text
$ bash examples/proof-hello-world/run_all.sh
summary: 5 pass, 1 skip, 0 fail
```

```text
$ bash examples/proof-hello-world/detect_semantic_rewrite.sh
summary: 8 pass, 0 skip, 0 fail
```

```text
$ bash examples/proof-hello-world/detect_awk_rewrite.sh
summary: 6 pass, 0 skip, 0 fail
```

```text
$ tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs --repo-root . examples/proof-hello-world/IMPLEMENTATION_DAG.toml
DAGTOML VALIDATION PASSED (rust primary)
- files validated: 1
- profiles in resolution set: 3
```

```text
$ /tmp/dagtoml-validate-go --repo-root . examples/proof-hello-world/IMPLEMENTATION_DAG.toml
DAGTOML VALIDATION PASSED (go primary)
- files validated: 1
- profiles in resolution set: 3
```

```text
$ python3 validators/validate_implementation_dag.py examples/proof-hello-world/IMPLEMENTATION_DAG.toml
IMPLEMENTATION DAG VALIDATION PASSED
- units: 9
- layers: {0: 8, 1: 1}
- critical_path_loc: 138
```

```text
$ python3 validators/validate_traceability.py examples/proof-hello-world/TRACEABILITY.toml --check-paths-exist
TRACEABILITY VALIDATION FAILED
- --check-paths-exist requires --repo-root
```

```text
$ python3 validators/validate_traceability.py examples/proof-hello-world/TRACEABILITY.toml --repo-root . --check-paths-exist
TRACEABILITY VALIDATION PASSED
- entities: 30
- path existence checks: enabled
```

```text
$ python3 validators/validate_review_readiness.py examples/proof-hello-world/REVIEW_READINESS.toml
REVIEW READINESS VALIDATION PASSED
- kind: readiness-gate
- ids: 2
- entries: 2
```

```text
$ python3 validators/validate_closure_root.py --discover examples/proof-hello-world/
CLOSURE-ROOT VALIDATION PASSED (5 file(s)).
```

```text
$ python3 validators/validate_ijb_conformance.py examples/proof-hello-world/IMPLEMENTATION_DAG.toml
IJB CONFORMANCE VALIDATION FAILED
- instance files require --repo-root so the core and profile ontologies can be loaded for resolution
```

```text
$ python3 validators/validate_ijb_conformance.py examples/proof-hello-world/IMPLEMENTATION_DAG.toml --repo-root .
IJB CONFORMANCE VALIDATION PASSED
- template_kind: implementation-dag
```

```text
$ python3 validators/validate_code_symbols.py examples/proof-hello-world/TRACEABILITY.toml --repo-root .
CODE SYMBOL VALIDATION PASSED
- languages: go, java, rust, typescript
- checked symbols: 8
- matched symbols: 8
- skipped entries: 4
```

```text
$ make toml-conformance-all
valid tests: 185 passed, 0 failed
invalid tests: 358 passed, 0 failed
valid tests: 185 passed, 0 failed
invalid tests: 371 passed, 0 failed
```

I also ran the Rust and Go primary validators against all five proof TOMLs; each invocation exited 0 and printed `DAGTOML VALIDATION PASSED`. I ran IJB conformance against all five proof TOMLs with `--repo-root .`; all passed. I ran IJB conformance against all five proof TOMLs without `--repo-root`; all failed with the documented instance-file requirement.

H03 implementation DAG values: pass. The validator returned 9 units, layers `{0: 8, 1: 1}`, and critical_path_loc 138. The file itself declares entry_points `U01, U02, U03, U04, U05, U07, U08, U09`, leaf_nodes `U06, U07, U09`, critical_path `U05, U06`, and critical_path_loc 138 at examples/proof-hello-world/IMPLEMENTATION_DAG.toml:158-162. Note: the suggested `--verbose` flag in verification_report.toml:68 is not accepted by the validator, but the report says "or read the file directly", and the non-verbose validator plus file bytes were sufficient.

H04 claim audit: fail. Every row in Table 3 has an evidence source, status, and boundary. C01, C05, and C06 are directly covered. C02-C04 are only indirectly covered through the C01 byte-exact claim and an E03 exclusion in EVIDENCE_MATRIX.toml:61-63. More importantly, Table 3 is not one-to-one with Table 2 command evidence: several Table 2 commands are absent from Table 3 as specific evidence.

H05 spec backdrop: pass for the requested byte checks. tools/dagtoml-validate-rs/ and tools/dagtoml-validate-go/ exist. Makefile has `toml-conformance`, `toml-conformance-rs`, and `toml-conformance-all` at Makefile:68-85. SPEC §12 starts at SPEC.md:851 and SPEC §13 starts at SPEC.md:1195. profiles/agent-assurance/, profiles/cost/, and profiles/disclosure/ exist. The tier ladder is documented at profiles/agent-assurance/tiers/README.md:15 and the five tier files exist. INV06 is declared at profiles/agent-assurance/gate-decision-kind.toml:200-201.

H06 Werner-style sanity floor: pass. `grep -c $'\u2014' paper-hello-world/main.tex` returned 0. `grep -cE -- '---' paper-hello-world/main.tex` returned 0. The banned-vocabulary grep returned 0. My sentence-length CV calculation returned 0.934, above the 0.4 floor.

H07 LaTeX structural integrity: pass. Brace balance 0, minimum balance 0. Every `\begin`/`\end` pair matched. Labels were `tab:claims`, `tab:commands`, and `tab:contracts`; refs were the same set; missing refs none.

H08 acknowledgments: pass. paper-hello-world/main.tex:460-474 names tools/dagtoml-validate-rs/, tools/dagtoml-validate-go/, validators/, tools/toml-test-decode-rs/, toml-lang/toml-test, and the codex/gemini/grok review panel. The named paths exist. Makefile:17 pins TOML_TEST_VERSION v1.6.0 and Makefile:64-66 installs toml-lang/toml-test plus BurntSushi's decoder. docs/reviews contains multiple raw_findings/codex.md, raw_findings/gemini.md, and raw_findings/grok.md sessions under the review DAG; this paper session already has gemini.md and grok.md present.

H09 conclusion: pass. paper-hello-world/main.tex:441-458 opens with the required concession-before-pivot and closes with "inside one repository, on one runner, on one day." It explicitly disclaims semantic equivalence, paraphrase resistance at scale, and production assurance workflows at main.tex:454-456.

H10 limitations and non-claims: pass. paper-hello-world/main.tex:419-437 lists general semantic equivalence, arbitrary obfuscation resistance, broad AWK AST similarity, copyright/licensing/authorship conclusions, production readiness, and performance/scalability/precision/recall/benchmark results. The exact-claim paragraph at main.tex:433-437 is bounded to a small proof pack, explicit unsupported-language boundary, and same-toolchain reproducibility.

## Process confirmations

I did not base this review on the initiator's stated intent or on plan-compliance claims. I inspected the manuscript, bibliography, proof TOMLs, shell witnesses, validator docs/workflow bytes, and executed the commands above. This file is the persisted review evidence required by tools/review-request-dag.toml.

Terminal verdict: concrete_unresolvable_blocker
Blocker: paper-hello-world/main.tex:275-281 says the witnesses were corrected to compare output files with `cmp` against the explicit `Hello, world!\n` byte stream, but examples/proof-hello-world/run_all.sh:28-39, examples/proof-hello-world/detect_semantic_rewrite.sh:53-55, and examples/proof-hello-world/detect_awk_rewrite.sh:62-76 still read stdout through command substitution and compare to `Hello, world!`, so a no-newline output satisfies the current check; additionally, paper-hello-world/main.tex:244-245 reports the traceability command with `--check-paths-exist` as exit 0 even though the exact command required by docs/reviews/2026-05-25-paper-hello-world-e2e/verification_report.toml:53-55 exits 1 unless `--repo-root .` is supplied.
