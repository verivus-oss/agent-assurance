# README restructure — Gemini Review (2026-05-25)

Independent review of `README.md` restructure (commit `b759eaf`).

## 1. Method

I verified the changes by:
- Inspecting `README.md` at `b759eaf`.
- Comparing against `bc2a7c5:README.md`.
- Running the `verify_by` recipes for closures C01-C07.
- Executing unit checks U01-U06 from the review bundle.
- Auditing all 42 internal links (40 path-based, 5 SPEC.md anchors, 1 CLAUDE.md anchor).
- Cross-checking version numbers against `core/ontology.toml` and profile descriptors.
- Verifying existence of all cited tools, validators, and examples.

## 2. Per-closure classification

| ID | Status | Evidence |
| --- | --- | --- |
| **C01** | closed | `grep` confirmed "after the repository is made public" is gone. "calendar-versioned UTC" added (line 45). `git tag` shows `v2026-05-25T03-30-02Z`. |
| **C02** | closed | `ls -d tools/*/` returns 7 subdirectories; all 7 appear in Repository Map (lines 113-119). `Makefile` present in map (line 124). |
| **C03** | closed | `SPEC.md#12`, `SPEC.md#13`, `INV06`, `profiles/cost`, `profiles/disclosure`, `tiers/README.md` all found in Start Here (lines 80-86). Headers use `###` (lines 56, 66, 76, 88). |
| **C04** | closed | Local Validation block (lines 142-166) includes all cited commands. Python validators and Makefile targets (`toml-conformance-all`, etc.) verified on disk. |
| **C05** | closed | "Validation tooling" section (lines 127-140) and "triad" rationale paragraph (lines 142-147) present and accurate. |
| **C06** | closed | Status table (lines 35-42) includes Cost and Disclosure profiles. `schema_version = "1.0.0"` verified in `profiles/cost/PROFILE.toml` and `profiles/disclosure/PROFILE.toml`. |
| **C07** | closed | Governance section (lines 182-188) correctly links to `tools/review-request-dag.toml` and describes the multi-LLM review policy. |

## 3. Unit Verification (U01-U06)

- **U01 (Factual Accuracy):** 
  - SPEC §13 exists at `SPEC.md:1195`.
  - Five deployment tiers verified in `profiles/agent-assurance/tiers/`.
  - Cost and Disclosure profile contents verified.
  - `INV06` verified in `profiles/agent-assurance/gate-decision-kind.toml`.
  - Rust/Go validators and parser-conformance shim verified in `tools/`.
- **U02 (Link Integrity):** 
  - All 42 link targets verified. 
  - SPEC.md anchors (`#8`, `#91`, `#10`, `#12`, `#13`) match GFM-generated anchors from headers.
  - `CLAUDE.md#the-two-version-pins` matches `CLAUDE.md:115`.
- **U03 (Taxonomy):** Grouping by reader role is coherent. Placing "Validate source-code symbols" under "author" is appropriate as it serves the author's verification needs.
- **U04 (Versions):** `schema_version = "1.0.0"` and `ontology_version = 1` claims match the on-disk source of truth.
- **U05 (Executable):** Fenced shell block commands are accurate; all paths resolve.
- **U06 (Governance):** `tools/review-request-dag.toml` verified as the authoritative policy file.

## 4. Out-of-scope findings

None.

## 5. Final blockers

None.

Terminal verdict: unconditional_approval
