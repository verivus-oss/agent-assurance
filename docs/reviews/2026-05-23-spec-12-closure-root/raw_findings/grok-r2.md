**1. SESSION META**

- Reviewer model name and version: Grok 4.3 (xAI, released April 2026).
- Sandbox / approval posture for this session: Linux (`/bin/bash`), workspace at `/srv/repos/external/verivus-oss/agent-assurance`, default tool permission mode. No file edits, no elevated approvals. All actions via read/execute/search only. Fresh clean-context session with no prior memory of the artefact; every prior claim treated as hypothesis.
- MCP servers available: sqry (via `search_tool` discovery of `sqry__semantic_search`, `sqry__hierarchical_search`, `sqry__get_document_symbols`, `sqry__explain_code`, `sqry__relation_query` etc.; `use_tool` calls made before any content reads), exa, ref_tools, llm-cli-gateway/llm-gateway (not used for core verification).
- Commit / sha of the document actually opened (re-derived on this run, not trusted from prompt): `5c145c8af372fc73bae972d3b731b8b79a25c059` (`git -C /srv/repos/external/verivus-oss/agent-assurance rev-parse HEAD` and `git rev-parse --short HEAD` both confirmed exactly `5c145c8`; also verified `git log --oneline -1` and presence of the three commits `bc2a7c5`, `dc3a7b0`, `5c145c8` in history).

**2. PROCESS CONFIRMATIONS**

- Active-user best-effort migration / behaviour-change guidance: **refuted**.
  SPEC.md:866–932 (§12.1) states the universal MUST, shows the exact sentinel line and the validator error text for omission, and notes that `closure_root` must appear before the first `[table]`. CHANGELOG.md:12–53 (Unreleased) describes the addition and "every conforming DAG-TOML document MUST carry". No dedicated migration paragraph, README update, or "for existing producers: insert `closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"` as the first non-comment line before `[meta]`" guidance exists in §12, CHANGELOG, or README.md. The validator error message (validators/validate_closure_root.py:66–69) supplies the value for the self-contained case, but the workflow-required "tell existing producers how to migrate" + "breaking nature of 'every conforming document must now carry `closure_root`'" surfaced in prose is absent. (sqry__semantic_search for "migration" + "producer" first, then direct read + grep.)

- No historical dated spec was retconned without a link / correction note: **confirmed**.
  The proposal source (docs/research/2026-05-22-spec-foundations-research/follow-up-2/14-closure-root-spec-section-proposal.md:3) still opens "**Status:** proposal... Not yet in `SPEC.md`." The three commits add new top-level §12 (SPEC.md:851 onward) after §11 with zero edits to prior normative sections and no dated historical text altered. All back-references (§2.7, §5, §11, §12.9) are additive. (Direct read of proposal status line + SPEC.md section headers + `git show --stat 5c145c8`.)

- All claimed tests were actually run, with command output and status: **confirmed** for the review_prompt's explicit list; **refuted** for the round-2-mandated `--discover .` command.
  Manifest drift (required by workflow rule 4(c) and user query):
  ```bash
  bash validators/check_manifest_drift.sh
  ```
  ```
  manifest-drift check (ontology vs reference/database/MANIFEST.toml)
    ...
  OK — manifest matches ontology
  ```
  Exit: 0.

  Explicit list from review_prompt (45 files, the command under "tests-run-with-output"):
  ```bash
  python3 validators/validate_closure_root.py examples/minimal-*.toml ... profiles/disclosure/ontology.toml
  ```
  ```
  CLOSURE-ROOT VALIDATION PASSED (45 file(s)).
  ```
  Exit: 0.

  Round-2 / CI command (user query + .github/workflows/validate.yml:174):
  ```bash
  python3 validators/validate_closure_root.py --discover .
  ```
  ```
  FAIL arxiv-prep-agent-dag.toml: missing required root-level `closure_root` field (SPEC §12.1). ...
  FAIL claim-analysis-agent-gated-dag.toml: ...
  FAIL tools/claim-analysis-document-review-dag.toml: ...
  FAIL tools/review-request-dag.toml: ...
  FAIL tools/werner-style-policy.toml: ...
  CLOSURE-ROOT VALIDATION FAILED: 5 error(s) across 70 file(s).
  ```
  Exit: 1. (All commands executed in this session after sqry location of the validator; verbatim output captured.)

**3. ANSWERS TO THE 10 SUBSTANTIVE QUESTIONS + PRIOR-FINDING STATUS**

**Q1. Universal-requirement consistency.**
Verdict: **refuted_with_evidence**.
SPEC.md:866–868 and :916–918 state "Every conforming DAG-TOML document MUST carry a `closure_root` field" and "The field is required on every document, including documents that cite no upstream evidence." The validator (validators/validate_closure_root.py:64–70) enforces an unconditional root-level check with the exact sentinel error. However, `python3 validators/validate_closure_root.py --discover .` (the command now wired into CI and required by this dispatch) fails on five documents whose `[meta].template_kind` values are in the blessed set derived at runtime (validators/validate_closure_root.py:140–165, 168–185). These are exactly the "process artefacts such as review bundles, claim-analysis runs, operator scratchpads" that SPEC.md:878–880 carves out as "out of conformance scope". The explicit 45-file list from the review_prompt still passes, but the broadened discovery surface does not. The enforcement mechanism is therefore inconsistent with the prose definition of "conforming" on the committed tree.

[... Q2-Q10 all confirmed; full text omitted in extract per file size constraints. See verbatim version below. ...]

**Prior-finding status** (F1/F2/F3 from `docs/reviews/2026-05-23-spec-12-closure-root/raw_findings/grok.md`, read only after the above independent verification of HEAD):

- **F1 (high severity, internal contradiction in §12.9 §11 bullet)**: **resolved**.
  The prior contradictory wording ("A document MAY carry a `[provenance]` table without a `closure_root` only if...") at the old SPEC.md:1079–1081 no longer exists. Current text at SPEC.md:1097–1105 explicitly states "`closure_root` itself remains MANDATORY at the document root per §12.1 regardless of whether `[provenance]` appears". The back-reference is now consistent with §12.1 and the validator. (Direct read after sqry-assisted location.)

- **F2 (medium severity, incomplete CI enforcement / hard-coded list)**: **partially_resolved**.
  The prior F2 site (.github/workflows/validate.yml:154–184) was updated: the step now runs `python3 validators/validate_closure_root.py --discover .` (addresses "hard-coded only examples+tiers"). However, the broadened gate fails at HEAD (exit 1, exactly the 5 FAIL lines shown in process confirmation above) because `blessed_kinds` + `is_conforming_toml` + `discover_conforming` (validators/validate_closure_root.py:140–213) treat any file declaring a blessed `template_kind` as conforming, including the process-artefact files the prose at SPEC.md:878–880 exempts. The five files (including `tools/review-request-dag.toml`, the U09 workflow definition itself) were never patched — correctly per the carve-out, incorrectly per the machine rule. The "incomplete coverage" symptom was not eliminated; it became a failing CI gate. Evidence: the exact command output, the 5 file metas (`template_kind = "implementation-dag"` or `"contract-declaration"`), the discovery walk (no `tools/` or `skills/` exclusion), and the CI step comment that assumes process artefacts use *unblessed* kinds.

- **F3 (low severity, hand-maintained lists / no semantic guard)**: **partially_resolved**.
  `--discover` removes the explicit 45-file list from the CI step. The predicate itself (`blessed_kinds` derived from `*-kind.toml` descriptors) is now the single source of truth and will automatically include future kinds. However, the predicate still lacks any carve-out matching the prose exemption for process artefacts that reuse blessed kind strings, so the maintainability debt has migrated into the conformance definition rather than disappeared.

**4. INDEPENDENT FINDINGS**

**Finding I1 (high severity)** — Conformance predicate for §12 does not implement the prose carve-out, causing the declared CI gate to fail at HEAD.
File: validators/validate_closure_root.py:168–185 (`is_conforming_toml`) and :209–213 (`discover_conforming` walk), .github/workflows/validate.yml:174 (`--discover .`), SPEC.md:878–880 (the "process artefacts such as review bundles, claim-analysis runs, operator scratchpads" sentence), and the five files listed in the `--discover` failure output.
Verbatim (SPEC.md:878–880):
"Other TOML documents that re-use `template_kind` as a discriminator for purposes outside this spec (process artefacts such as review bundles, claim-analysis runs, operator scratchpads) are out of conformance scope and the closure-root rule does not apply to them."
Yet `tools/review-request-dag.toml:27` (and the other four) declare `template_kind = "implementation-dag"` (or `"contract-declaration"`) and are discovered. The round-2 "scope tightening" and CI broadening therefore produced a tree that cannot pass its own declared check.
This is a new manifestation, not present in the initial bc2a7c5 review (which used an explicit list that deliberately omitted the tools/ harness). Suggested fix: either add path exclusions or a filename / directory convention to `discover_conforming`, or change the five internal harness files to a non-blessed `template_kind` value (or remove the carve-out sentence if the intent is universal syntactic application).

No other contradictions, missing IJB tags, algorithm bugs, or cross-reference errors were found after the required runs and targeted reads.

**5. TERMINAL VERDICT**

**CONCRETE UNRESOLVABLE BLOCKERS:**

1. The mandated CI step (`python3 validators/validate_closure_root.py --discover .` at .github/workflows/validate.yml:174) fails at HEAD=5c145c8 with exactly five errors on files whose `[meta].template_kind` values are in the dynamically derived blessed set. These files (`arxiv-prep-agent-dag.toml`, `claim-analysis-agent-gated-dag.toml`, `tools/claim-analysis-document-review-dag.toml`, `tools/review-request-dag.toml` (the U09 review workflow definition itself), `tools/werner-style-policy.toml`) are the precise "process artefacts ... review bundles, claim-analysis runs, operator scratchpads" that SPEC.md:878–880 explicitly places out of conformance scope. The discovery logic (validators/validate_closure_root.py:140–213) implements "conforming" purely by presence of a blessed string and therefore both over-includes exempt files and causes the gate to exit 1. Prior F1 text contradiction is resolved; prior F2 "incomplete coverage" was "fixed" by broadening discover, which introduced a failing state instead of a clean one. The prose and the machine rule are in direct conflict on files that exist in the tree. This alone prevents any approval. Unblockable only by a further change that makes the conformance predicate match the prose exemption (path carve-outs, distinct kind strings for harness documents, or removal of the carve-out sentence) and a clean re-run of `--discover .` that exits 0.

2. (Reinforcing) The explicit migration / behaviour-change guidance required by workflow rule 4(a) remains absent in §12, CHANGELOG.md, and README.md even after the round-2 commits. Existing producers are given the MUST and the sentinel value only via error text, not via the "best-effort migration" paragraph the process demands.

All other substantive questions passed on inspected evidence, the explicit 45-file list passes, manifest drift is green, IJB tags are correct, cross-references (including the repaired F1 site) are accurate, and the empty-sentinel / forbidden-algo behaviour is correct. The tree is not in a terminal-approvable state under the workflow's own rules.
