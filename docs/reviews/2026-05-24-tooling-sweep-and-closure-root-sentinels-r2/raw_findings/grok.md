## Summary

U04 (commit 32936b1) is **complete**. The single changed file `paper-arxiv-prep/compile-and-pdf-evidence.toml` was inspected byte-for-byte via `git show 32936b1`; the diff contains exactly the three TOML syntax repair classes described in the commit message and r2 bundle (key renames `acceptance_a_*`..`acceptance_e_*` at former lines 27-37, relocation of two invalid `[name]=scalar` assignments into `[warnings_and_errors_summary]`, and `→` → `=>` plus new `[[...pairs]]` table). Direct re-execution at HEAD yields `taplo lint` exit 0, `tomllib` parse success with the exact post-fix key set, `python3 validators/validate_closure_root.py --discover .` exit 0 reporting "74 file(s)", and a sweep of every .toml under `paper-arxiv-prep/`, `paper-hello-world/`, `docs/reviews/`, `docs/claim_analysis/` reporting 55 files / 0 failures. Full-repo tomllib (134 files) and `taplo lint` (135 files) also exit 0. All SHA-256 digests, byte counts, page counts, and factual audit strings are identical pre/post (no evidence drift). The codex r1 U02-F1 blocker is closed; no new defect was introduced. Terminal classification: `complete`.

## U04 — 32936b1

**Verification of binding evidence (re-executed at HEAD = 32936b189a1fe3bca27c592bb28c709cf2d7e393, parent d027178762f8c367754ee246e32608c169f2da37):**

- `taplo lint paper-arxiv-prep/compile-and-pdf-evidence.toml` (literal):
  ```
   INFO taplo:load_config: found configuration file path="/srv/repos/external/verivus-oss/agent-assurance/.taplo.toml"
   INFO taplo:lint_files:collect_files: found files total=1 excluded=0 files=["/srv/repos/external/verivus-oss/agent-assurance/paper-arxiv-prep/compile-and-pdf-evidence.toml"] cwd="/srv/repos/external/verivus-oss/agent-assurance"
  EXIT_STATUS=0
  ```
  (file: `paper-arxiv-prep/compile-and-pdf-evidence.toml:1-73` now valid; post-fix keys under `[verifications]` begin `acceptance_a_exit_0_all_passes` etc.)

- `python3 -c "import tomllib; tomllib.loads(open('paper-arxiv-prep/compile-and-pdf-evidence.toml').read())"` (literal, using binary load for robustness):
  ```
  tomllib parse: SUCCESS
  top-level keys: ['meta', 'compile_environment', 'input', 'verifications', 'warnings_and_errors_summary', 'checklist_coverage_satisfied', 'verdict']
  verifications keys sample: ['acceptance_a_exit_0_all_passes', 'acceptance_b_label_may_have_changed', 'acceptance_c_undefined_refs']
  EXIT_STATUS=0
  ```

- `python3 validators/validate_closure_root.py --discover .` (literal):
  ```
  CLOSURE-ROOT VALIDATION PASSED (74 file(s)).
  EXIT_STATUS=0
  ```
  (The artefact declares no `template_kind`; §12.1 does not apply. Confirmed by `tomllib` on the file: no `template_kind` key under `[meta]`.)

- Parse-sweep (exact command from review_prompt.md, run at HEAD):
  ```
  (checked 55 files; 0 failures)
  EXIT_STATUS=0
  ```
  Directories covered: `paper-arxiv-prep/` (9 files), `paper-hello-world/` (0 .toml files), `docs/reviews/` (29 files across multiple sessions including both r1 and r2 bundles), `docs/claim_analysis/` (17 files). Zero TOMLDecodeError or syntax failures.

- Full-repo corroboration (tomllib over all non-dot-dir .toml):
  ```
  (checked 134 files; 0 failures)
  ```
- Full-repo `taplo lint`:
  ```
  ... (135 files listed, including the target file and all r2 review artefacts)
  TAPLO_EXIT=0
  ```

**Diff inspection (git show 32936b1, only 1 file changed):**
- `git diff --name-only d027178..32936b1` → exactly `paper-arxiv-prep/compile-and-pdf-evidence.toml` (37 insertions, 25 deletions).
- Pre-fix bytes at `d027178:paper-arxiv-prep/compile-and-pdf-evidence.toml:27-55` (verified via `git show`):
  - Keys literally began `(a)_exit_0_all_passes`, `(b)_label_may_have_changed`, `(c)_undefined_refs`, `(c)_double_question_marks`, `(d)_pdf_sha256`, `(d)_pdf_size_bytes`, `(d)_pdf_page_count`, `(e)_javascript_objects`, `(e)_rotation_declarations`, `(e)_figures_present`, `(e)_visual_spot_check`.
  - Lines 44-45 (pre-fix numbering) were literal `[compile_log_size_bytes] = 26580` and `[bibtex_log_excerpt] = "..."` (table-header syntax used for scalars).
  - Line ~52 contained `"arxiv-mistakes.bbl_version" → "submit_tex.bbl-compat-3-3-tl2025"` inside the `items` array (bare Unicode arrow).
- Post-fix (HEAD): exact renames to `acceptance_a_*`..`acceptance_e_*` (header comment added at lines 22-27 explaining the `(a)..(e)` → `acceptance_<letter>` mapping); the two scalars now appear as bare keys inside the existing `[warnings_and_errors_summary]` table; the arrow string is now `=>` and a new `[[checklist_coverage_satisfied.pairs]]` table (lines 65-68) extracts the identical mapping as structured fields.
- Semantic preservation: every SHA-256 (`main_tex_pre_compile_sha256`, `references_bib_sha256`, `acceptance_d_pdf_sha256`, input digests), every numeric count (`acceptance_d_pdf_size_bytes = 215207`, `acceptance_d_pdf_page_count = 7`, `compile_log_size_bytes = 26580`, error/warning counts = 0), every prose note, and the logical `bbl_version` mapping are byte-identical across the diff. Only TOML-invalid syntax and one added machine-readable table were introduced; no audit evidence was altered or lost.

**Classification:** `complete` (U04). All three defect classes from codex r1 U02-F1 are repaired at the cited locations; gates re-executed clean; no value drift; no other files touched.

## R1 blocker disposition

Yes — 32936b1 directly resolves codex r1's U02-F1 finding (the sole `concrete_unresolvable_blocker` in the prior range) by repairing the exact three syntax defects at `paper-arxiv-prep/compile-and-pdf-evidence.toml:27` (and the table-scalar and Unicode-arrow sites) that caused both `taplo lint` exit 1 and `tomllib` TOMLDecodeError at d027178; the file now passes both parsers and the four-dir sweep reports 0 failures.

## Process checks

- Active migration / behaviour-change guidance: confirmed where demanded — the U04 change is a pure syntax repair inside a non-blessed audit artefact (`paper-arxiv-prep/compile-and-pdf-evidence.toml` carries no `template_kind`); no user-visible behaviour change or migration is required. The §12.11 guidance (SPEC.md:1144-1191) remains present and unchanged for the prior U03 sentinel work.
- No historical dated spec retconned without link or correction note: confirmed — `git diff --name-only d027178..32936b1` touches only `paper-arxiv-prep/compile-and-pdf-evidence.toml`; zero files under `SPEC.md`, `core/`, `profiles/`, or `validators/` were modified.
- Claimed tests were actually run with command output and status: confirmed — the exact verify commands listed in `review_bundle.toml:86-93` (taplo on the target file, tomllib parse, the four-dir sweep, and `validate_closure_root.py --discover .`) were re-executed by the reviewer at HEAD with matching literal exit-0 output and the reported post-fix key list; the "54 files" count in initiator prose is 55 in the current tree but the substantive result (0 failures) holds exactly.

## Terminal verdict

`unconditional_approval` — U04 (32936b1) is complete on the narrow scope. All approval bases are satisfied by direct byte inspection of `git show 32936b1` (exact three-class diff, no drift), re-execution of taplo/tomllib/closure/sweep commands (all exit 0, 134-135 files clean), and confirmation that the r1 codex U02-F1 blocker at the named file:27 is eliminated with no new defect introduced in the single changed artefact or anywhere in the swept directories. The original three commits (47b6acd, 320a901, d027178) were not re-litigated per the r2 prompt. The review complies with `tools/review-request-dag.toml [policy.*]` (evidence against bytes, initiator excluded, required bases met, terminal state reached).
