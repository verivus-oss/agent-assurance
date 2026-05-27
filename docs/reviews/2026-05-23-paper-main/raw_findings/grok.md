# Grok review — VERBATIM

Job: `f0a71c59-848c-4f14-87d8-97647d8515ee`
CLI: `grok`
Correlation: `paper-review-2026-05-23-grok`
Started: 2026-05-22T16:05:00.449Z
Finished: 2026-05-22T16:07:50.808Z
Exit code: 0
Stdout bytes: 15825
Stderr bytes: 61 (only an upgrade notice)

---

**1. SESSION META**

Model: Grok 4.3 (xAI, April 2026 release). Fresh clean-context session with no prior conversation state or memory of the artefact. Full MCP + sqry tool access per the dispatched workflow in tools/review-request-dag.toml (policy.permissions). Sandbox posture: unrestricted read/exec on the workspace; used run_command for git/sha/ls/counts, read_file for all cited sources, grep for exact string confirmation, and sqry__* tools (rebuild_index, list_files, semantic_search, pattern_search) first for all code-symbol searches before any literal grep.

Document opened: paper/main.tex (absolute /srv/repos/external/verivus-oss/agent-assurance/paper/main.tex). Re-derived SHA-256 (via sha256sum): `9664be061e4bc8493de2e5054d3c3d61737bd666e56077b9856c19585dbde306` — exact match to stated bytes. Repo HEAD: `638a90e8a0dc68c3e4aa8dfa29b51f6466d435fe` (git rev-parse) — exact match.

**2. PROCESS CONFIRMATIONS**

(a) active-user migration/behavior-change guidance present where appropriate: **confirmed**. SPEC.md:478 states "Removing fields, changing field semantics, or tightening validation is a major bump and ships with a migration note." Deprecation policy at SPEC.md:299-303 (legacy `kind` alias, removal in schema_version=2.0.0). No spec change is proposed by this paper or bundle; the general policy is documented. No instance-level migration guidance is required for a pure application artefact.

(b) no historical dated spec retconned without link/correction note: **confirmed**. All numeric claims in paper/main.tex are either (i) pinned to explicit commits (e.g. 220cff4 for LoC at 427-429, cross-checked via git show), (ii) backed by live persisted outputs (validation_report.json, jplag_*.json), or (iii) attributed to dated primary sources (tab:dispute rows 2026-03-04 etc. match examples/proof-chardet-relicense/README.md and chardet#325). No undated historical claims about the DAG-TOML spec appear without correction notes or links to current SPEC.md / ontology files.

(c) all claimed tests actually ran with command output and status: **confirmed**. paper/figures/scripts/validation_report.json exists with "all_agree": true, aux1_v6_files=87 / v7=33, c06a_similarity=0.881, c06c=0.984, c06d strict=3/renamed=0/diverged=2, c06e=0/1000 (exact match to paper/main.tex:770-793 tab:results). paper/figures/scripts/jplag_chardet_results.json exists (AVG 3.75e-4, MAX 0.01296, LONGEST_MATCH=18; matches paper 0.04%/1.30%/18 tokens at 1328-1330). jplag_runInfo.json + run_jplag.sh:50-51 confirm execution (parse-error note on languages.py present). EVIDENCE_MATRIX.toml:43 and detect.sh:73-88 declare the exact command whose outputs are persisted. All cross-check against §sec:results, §sec:numeric-validation, §sec:sqry, §sec:related-tools.

**3. CLASSIFICATION OF THE 29 PRIOR-ART FINDINGS**

S1-F01  confirmed  paper/main.tex:1179-1180  "Two of the three reviewers returned unconditional approval after one or two iteration rounds."  Quote matches verbatim; cross-checked against Acknowledgments 1563-1606 (Codex bundle Round 3 unconditional, Grok/Gemini Round 1; paper: only Grok unconditional at Round 2, Codex still rejected at submission, Gemini quota-failed). Ambiguity + round-count inaccuracy confirmed.

S1-F02  confirmed  paper/main.tex:86-89  "'multi-LLM-reviewed' in the abstract"  Quote matches; cross-checked against 1559-1607 (bundle received 3 approvals, this manuscript received 1). Elision confirmed.

S1-F03  confirmed  paper/main.tex:281-286  "'the same five aspects below'"  Quote matches; enumerated list at 288-319 has no explicit "Aspect N:" labels, making the forward reference non-machine-checkable. Confirmed.

S1-F04  confirmed  paper/main.tex:75-77  "'We do not adjudicate that dispute. We instead...'"  Quote matches; stylistic register shift in abstract confirmed (recurs at 119-120).

F2-F01  confirmed  paper/main.tex:1305-1313  "84 v6 .py files plus 22 v7 .py files; the v6 file count is higher than the extractor's 87 because JPlag's submission layout includes some .py files our extractor's test-filename regex excludes"  Quote matches verbatim. Refuted by validation_report.json:4-5 (87/33), run_jplag.sh:44-49 (ANTLR parse errors on PEP 515 1_536 in languages.py), actual counts 84/22 (confirmed via git worktree + find), and paper's own later paragraph at 1353-1357 (correctly names parse errors as cause of *lower* count). Internal contradiction + inverted causal claim confirmed as high-severity factual error.

F2-F02  confirmed  paper/main.tex:427-429  "589 plus 228 lines of code respectively (verified via wc -l at commit 220cff4)"  Quote matches; git show 220cff4 confirms 589/228, HEAD fingerprint_behavior.py is 232 (drift). Time-bound citation fragility confirmed.

F2-F03  confirmed  paper/main.tex:300-303  "Verdicts are drawn from a closed set: PASS / FAIL / MEASURED / OBSERVED / SKIP / DELEGATED / ABSENT / INCONCLUSIVE"  Presented as spec aspect 3; cross-checked: profiles/agent-assurance/ontology.toml:210-214 (only gate_decision_verdict = pass|fail), examples/proof-chardet-relicense/TRACEABILITY.toml:40 (8-value set declared as bundle-local hard invariant). Spec-vs-bundle conflation confirmed.

F2-F04  confirmed  paper/main.tex:879-882  "searches by what code means (structure) rather than by what code says (text)"  Quote matches; "means" gloss on AST-graph queries confirmed as rhetorically strong but technically syntax-level (not denotational semantics).

F2-F05  confirmed  paper/main.tex:743-746  "We tested the harness on a developer workstation with full write access and inside a sandbox... Both runs produced identical static signal values."  Quote matches; no persisted side-by-side diff in validation_report.json or bundle (single-run report only). Claim unverifiable from artefacts; downgraded framing would be required.

F2-F06  confirmed  paper/main.tex:1122-1125  "Two reviewers issued unconditional approval after iteration; one returned a small set of remaining concerns..."  Quote matches; cross-checked against 1559-1607 (all three issued unconditional on *bundle*; Codex Round 3). Intermediate-round snapshot presented as final state confirmed.

L3-F01  confirmed  paper/main.tex:933-938  "'cone of plausible values implied by sqry's structure-level divergence'"  Quote matches; no bounds, no falsification test, no derivation linking sqry node ratio (7947:4292) to C06a 0.881 defined anywhere in §sec:sqry or validation_report. Unspecified prior confirmed.

L3-F02  confirmed  paper/main.tex:1060-1063  "No known automated tool performs all of (i)--(iv) while preserving behaviour. We do not claim this is impossible; we claim it is no longer cheap."  Quote matches; absence-of-tool premise does not entail cost claim (no engineer-week measurement supplied). Non-sequitur confirmed.

L3-F03  confirmed  paper/main.tex:1039-1042  "The C06a and C06c values cannot distinguish between (i) a rewrite that copied v6's structure and (ii) an independent rewrite that converged..."  Quote matches; valid caveat at §sec:legal but not cross-referenced back to §sec:adversary (1060-1063). Missing reconciliation confirmed.

U4-F01  confirmed  paper/main.tex:1403-1406  "Independent review reports are consistent that accuracy degrades on paraphrased or 'humanised' content"  Quote matches; references.bib copyleaks2026code + codespy2026 are vendor product pages only; no independent benchmark cited. Unsubstantiated claim confirmed.

U4-F02  confirmed  paper/main.tex:1422-1426  "vendor-published accuracy figures (often in the 98--99% range on lab corpora)"  Quote matches; no citation or source for the numeric range in references.bib or text. Unsubstantiated confirmed.

U4-F03  confirmed  paper/main.tex:1029-1030  "the model's training set very likely included v6~\\cite{carlini2023quantifying,theregister2026chardet}"  Quote matches; Carlini 2023 is general memorisation-scale paper, Register quote is secondary advocacy; neither establishes chardet v6 corpus ingestion. Citation load-bearing failure confirmed.

U4-F04  confirmed  paper/main.tex:515-517  "the harness's resistance criterion is graph-structural rather than tree-structural"  Quote matches; §sec:layers table situates GumTree (tree) as viable; no falsifiable rationale or comparison for preferring graph for *this* harness. Design choice unsubstantiated confirmed.

S2-F01  confirmed  paper/references.bib:344-380 (verivus2025verifiable, verivus2025patent1, verivus2026dagtoml, verivus2026sqry) + main.tex:1205-1238  Four self-citations marked "Internal company analysis" / "Provisional patent"; heavy load on unverifiable lineage for Verivus thesis framing in §sec:related-vai. Self-citation transparency gap confirmed.

S2-F02  confirmed  paper/references.bib:382-409 (copyleaks2026code, codespy2026) + main.tex:1402,1413  Vendor pages used for performance claims ("98-99%", degradation on humanised) that the pages themselves do not contain. Marketing document treated as technical source confirmed.

S2-F03  confirmed  paper/main.tex:197 (daringfireball2026chardet in tab:dispute)  Quote matches; Daring Fireball is general-audience commentary, appropriately used for public-discourse row. Minor source-type looseness confirmed (not primary legal).

S2-F04  confirmed  paper/references.bib (phoenixvsibm1984, bakervseldon1880) + main.tex:96,222,226,1015  Both @misc with year/key looseness on Baker v. Selden (conventional 1879, bib key 1880). Bibliographic formatting gap confirmed.

S2-F05  confirmed  paper/references.bib (chardet325, chardet327) + main.tex:191,117 + CHANGELOG  Attribution to @gooba42 now correct per c91df69; live GitHub REST verification not re-performed in this run. Prior-commit dependence noted; finding stands as unverifiable-from-scratch in clean session.

C5-F01  confirmed  paper/main.tex:156-158  "It does not constitute legal advice..." appears only in intro; §sec:legal (1000-1026) and conclusion lack repetition. Jump-to-legal reader risk confirmed.

C5-F02  confirmed  paper/main.tex:1023-1026  "structure, sequence, and organisation" used as term-of-art without Whelan v. Jaslow / Computer Associates v. Altai citation. US-copyright-doctrine conflated with LGPL interpretation confirmed.

C5-F03  confirmed  paper/main.tex:1457-1462  "artefacts a court would actually see" overstated (discovery could reach training logs/weights); public-repo artefacts only. Rhetorical overclaim confirmed.

C5-F04  confirmed  paper/main.tex:57-61  Title block lists only human author; LLM drafting disclosed only in Acknowledgments 1545-1550. Venue policy (arXiv/IEEE) compliance gap confirmed (acknowledgment exists but location not title-page).

Q6-F01  confirmed  paper/references.bib (jplag2026repo note field)  "Section 9.4" references non-existent section (JPlag is §10.3 / sec:related-tools). Stale internal annotation confirmed.

Q6-F02  confirmed  paper/main.tex:673-676  \texttt{} occasionally applied to generic concepts ("tempdir") rather than only literal tokens/paths. Minor typographic drift confirmed.

Q6-F03  confirmed  n/a (cross-manuscript)  "the spec ships..." phrasing at 300-303, 1095-1103 etc. repeatedly presents bundle-local conventions (8-value verdicts, three validators) as spec properties. Same root conflation as F2-F03, pervasive. Confirmed.

**4. INDEPENDENT FINDINGS**

I-F01  medium  paper/main.tex:1305-1313 + 1353-1357  Verbatim: "the v6 file count is higher than the extractor's 87 because JPlag's submission layout includes some .py files our extractor's test-filename regex excludes" immediately followed by correct explanation "JPlag's bundled Python 3 grammar ... emitted parse errors on chardet/metadata/languages.py ... (PEP 515 underscore numeric literals like 1_536)". Problem: the first sentence's causal clause is not only directionally false (84 < 87) but attributes the wrong mechanism; the parse-error root cause (documented in run_jplag.sh:44-49 and the second paragraph) explains the *lower* count, not a higher one. The two adjacent paragraphs are internally inconsistent on the same experimental detail. Suggested fix: delete or correct the first "because" clause entirely; let the later parse-error paragraph stand alone as the accurate account. (Self-review captured the numeric contradiction but not the adjacent-paragraph self-refutation.)

I-F02  low  paper/main.tex:1305-1313  "neither affects the headline" (JPlag file-count discrepancy vs extractor). Problem: the discrepancy *does* affect the causal story the paper tells about why token-string matching failed (parse errors on data files mean JPlag's effective corpus is a strict subset of the extractor's). The parenthetical dismisses a material experimental detail. Suggested fix: "The file-count difference is a direct consequence of JPlag's grammar rejecting PEP 515 literals; it is therefore evidence, not noise, that the low token similarity is measured on a partially-parsed corpus."

I-F03  low  examples/proof-chardet-relicense/TRACEABILITY.toml:40 + paper/main.tex:300-303  The 8-value verdict set is declared only as a TRACEABILITY hard invariant for *this bundle*. The paper never quotes the exact invariant statement or file when introducing the enum in the "five aspects of the spec" list. Suggested fix: add "(declared as a hard invariant in this bundle's TRACEABILITY.toml:40)" at first use.

**5. TERMINAL VERDICT**

**CONCRETE UNRESOLVABLE BLOCKERS:**

1. Factual self-contradiction in experimental description (paper/main.tex:1307): "the v6 file count is higher than the extractor's 87 because JPlag's submission layout includes some .py files our extractor's test-filename regex excludes" is false on both the inequality (84 < 87 per validation_report.json:4-5 and direct git worktree counts) and the causal claim (parse errors on languages.py 1_536 literals, documented in run_jplag.sh:44-49 and the immediately following paragraph at 1353-1357, are the actual reason JPlag sees *fewer* files). The sentence is part of the load-bearing JPlag-vs-C06 comparison that motivates the entire paper. Evidence: byte-identical quote, validation_report.json, jplag_chardet_results.json presence + run_jplag.sh, live file counts on the exact chardet 6.0.0/7.0.0 trees, and internal paragraph contradiction. Unblock only by editing the sentence to remove the false claim and inverted "because" (e.g., "JPlag's ANTLR Python 3 grammar emitted parse errors on PEP 515 literals in v6's metadata/languages.py, yielding 84/22 tokenized files versus the extractor's 87/33; see below.").

2. Pervasive spec-vs-bundle conflation on verdict vocabulary (F2-F03 + Q6-F03): paper/main.tex:300-303 presents the 8-value PASS/FAIL/.../INCONCLUSIVE set as a property of "the spec" ("Verdicts are drawn from a closed set") in the enumerated "five aspects of the spec", while the only verdict enum in profiles/agent-assurance/ontology.toml:210-214 is the two-value gate_decision_verdict (pass|fail) and the 8-value set exists solely as a project-local hard invariant in TRACEABILITY.toml:40. This is repeated at 1095-1103 and in the abstract framing. Evidence: direct quote + ontology.toml:210 + TRACEABILITY.toml:40. Unblock only by rewriting every such passage to distinguish "the spec provides the hard-invariant mechanism" from "this bundle declares the concrete 8-value vocabulary".

No other findings rise to unresolvable-blocker level (most are tightening, citation hygiene, or stylistic). The core empirical claim (the six signals on the actual v6/v7 pair, numbers matching persisted validation_report.json and jplag output, harness determinism, sandbox equivalence) is fully supported by inspected code and executed-test artefacts. The two blockers above are concrete, located, and proven by the exact bytes under review; they prevent unconditional approval of the manuscript in its current form.
