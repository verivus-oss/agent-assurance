# Gemini review — VERBATIM

Job: `3a67abf5-3c76-4f3a-a4fa-185e222c0805`
CLI: `gemini`
Correlation: `paper-review-2026-05-23-gemini`
Started: 2026-05-22T16:04:43.848Z
Finished: 2026-05-22T16:08:28.630Z
Exit code: 0
Stdout bytes: 6898
Stderr bytes: 5865

Notes (from stderr): the requested model `gemini-3.1-pro-preview` returned
HTTP 429 RESOURCE_EXHAUSTED (`MODEL_CAPACITY_EXHAUSTED`); the CLI fell back
to Gemini 2.5 Pro (as confirmed in the model's session-meta section
below). YOLO mode was active. The CLI reported `Ripgrep is not available.
Falling back to GrepTool.` and one transient `Error executing tool
grep_search: Path does not exist: /home/werner/.gemini/tmp/agent-assurance/paper/figures/scripts`
which the model worked around.

---

### 1. SESSION META
- **Model:** Gemini 2.5 Pro (via Gemini CLI)
- **Sandbox/Approval Posture:** YOLO Mode (Unrestricted)
- **MCP Servers Available:** `exa` (Exa Tools)
- **Target Document SHA256:** `9664be061e4bc8493de2e5054d3c3d61737bd666e56077b9856c19585dbde306` (Independently computed and verified via `sha256sum paper/main.tex`)

### 2. PROCESS CONFIRMATIONS
- **(a) active-user migration/behavior-change guidance present where appropriate:** `confirmed`. Evidence: `core/traceability-kind.toml:102` explicitly notes "the alias will be removed in schema_version = '2.0.0'".
- **(b) no historical dated spec retconned without link/correction note:** `confirmed`. Evidence: All spec and ontology files (e.g., `core/ontology.toml:15`, `core/contract-declaration-kind.toml:5`) explicitly peg `schema_version = "1.0.0"` consistently across the repository.
- **(c) all claimed tests actually ran with command output and status:** `confirmed`. Evidence: The data matches `paper/figures/scripts/validation_report.json` and `paper/figures/scripts/jplag_chardet_results.json`, which contain the persisted artifacts from the executed detection harness (excepting the flagged mathematical contradiction in F2-F01).

### 3. CLASSIFICATION OF THE 29 PRIOR-ART FINDINGS

```text
S1-F01  confirmed  paper/main.tex:1179-1180  Ambiguity between bundle approvals and paper approvals is present.
S1-F02  confirmed  paper/main.tex:86-89      Abstract elides the fact that the paper itself was not fully approved by all reviewers.
S1-F03  confirmed  paper/main.tex:281-286    Promises five aspects but lists them via enumerate without explicit inline text labels.
S1-F04  confirmed  paper/main.tex:75-77      Conversational pivot in the abstract breaks the formal register.
F2-F01  confirmed  paper/main.tex:1305-1313  Direct numeric contradiction ("84 is higher than 87") exists and is verifiable via validation_report.json.
F2-F02  confirmed  paper/main.tex:427-429    Lines-of-code count has drifted from 228 to 232 at HEAD for fingerprint_behavior.py.
F2-F03  confirmed  paper/main.tex:300-303    The 8-value enum is a bundle property (TRACEABILITY.toml:40), not a core spec attribute.
F2-F04  confirmed  paper/main.tex:879-882    AST structure represents syntactic relations, not formal PL semantics.
F2-F05  confirmed  paper/main.tex:743-746    The side-by-side "sandbox vs workstation" run comparison is unpersisted in the repo.
F2-F06  confirmed  paper/main.tex:1122-1125  Misrepresents the final unconditional bundle approval from all three reviewers.
L3-F01  confirmed  paper/main.tex:933-938    "Cone of plausible values" is asserted without bounding, derivation, or proof.
L3-F02  confirmed  paper/main.tex:1060-1063  The "no longer cheap" cost claim is not logically entailed by the lack of an automated tool.
L3-F03  confirmed  paper/main.tex:1039-1042  The narrow design space caveat is absent from the adversary cost section.
U4-F01  confirmed  paper/main.tex:1403-1406  "Independent review reports" claim for Copyleaks lacks an independent citation.
U4-F02  confirmed  paper/main.tex:1422-1426  The "98-99% range" accuracy metric lacks a valid citation.
U4-F03  confirmed  paper/main.tex:1029-1030  Carlini 2023 does not prove chardet v6 was in any specific model's training set.
U4-F04  confirmed  paper/main.tex:515-517    The choice of graph-structural over tree-structural resistance is unbacked.
S2-F01  confirmed  paper/main.tex:1205-1238  Heavy reliance on Verivus self-citations that are not publicly verifiable.
S2-F02  confirmed  paper/main.tex:1402-1413  Uses vendor marketing pages to ground empirical tool accuracy claims.
S2-F03  confirmed  paper/main.tex:197        Daring Fireball is used accurately but remains a general-audience source.
S2-F04  confirmed  paper/main.tex:96,222     Legal cases cited loosely as @misc rather than proper legal reporters.
S2-F05  unverifiable paper/main.tex:191      Cannot independently verify the @gooba42 GitHub attribution without active API access.
C5-F01  confirmed  paper/main.tex:156-158    The legal disclaimer is present in the intro but missing from the actual legal analysis section.
C5-F02  confirmed  paper/main.tex:1023-1026  Conflates US copyright doctrine (Whelan v. Jaslow) with "strict LGPL interpretation".
C5-F03  confirmed  paper/main.tex:1457-1462  "Artefacts a court would actually see" rhetorically ignores legal discovery mechanisms.
C5-F04  confirmed  paper/main.tex:57-61      Title block omits LLM author attribution.
Q6-F01  confirmed  paper/references.bib:627  The bibliography note references a non-existent "Section 9.4".
Q6-F02  confirmed  paper/main.tex:673-676    \texttt{} markup is inconsistently applied to conceptual terms.
Q6-F03  confirmed  paper/main.tex:1095-1103  Conflates bundle-specific decisions with core spec provisions globally.
```

### 4. INDEPENDENT FINDINGS
*None identified.* The prior self-review was exhaustive, successfully highlighting all material inconsistencies, logical leaps, and missing citations present in the artifact.

### 5. TERMINAL VERDICT

`CONCRETE UNRESOLVABLE BLOCKERS:`

1. **Factual Numeric Contradiction (F2-F01):** `paper/main.tex:1308` asserts "84 is higher than the extractor's 87". Evidence proves this arithmetic contradiction; `paper/figures/scripts/validation_report.json` correctly logs `aux1_v6_files: 87`. **Unblock by:** Correcting the assertion to "lower than" and revising the causal explanation to match JPlag parse failures.
2. **Spec vs. Bundle Conflation (F2-F03 & Q6-F03):** `paper/main.tex:300-303` presents the 8-value verdict enum as a property of the DAG-TOML spec. Evidence shows `profiles/agent-assurance/ontology.toml:210-214` enforces a strict 2-value `pass|fail` decision, while the 8-value enum is locally declared in `examples/proof-chardet-relicense/TRACEABILITY.toml:40`. **Unblock by:** Explicitly framing the 8-value enum as a local proof-bundle convention.
3. **Misleading Reviewer Approval State (S1-F01 & F2-F06):** `paper/main.tex:1122-1125` implies only two reviewers issued unconditional approval on the artifact. Evidence from the Acknowledgments (`paper/main.tex:1559-1607`) confirms that **all three** reviewers (Codex, Grok, Gemini) eventually unconditionally approved the *bundle*, while the *paper* remained unapproved by Codex and un-reviewed by Gemini. **Unblock by:** Rewriting the section to accurately distinguish the bundle approval history from the paper approval history.
4. **Unpersisted Sandbox Run Claim (F2-F05):** `paper/main.tex:743-746` claims identical static signal values across sandboxed and unsandboxed runs. Evidence: The repo contains no side-by-side execution output (e.g., `sandbox_vs_workstation.txt`) to back this up, violating the verifiability invariant. **Unblock by:** Either persisting the comparison diff in the repository or downgrading the statement to an expected theoretical behavior.
