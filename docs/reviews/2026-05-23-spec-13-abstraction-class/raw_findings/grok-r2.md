# Independent Review — SPEC §13 r2 fix commit (Codex r1 blockers F1/F2/F3 close)
**Commit under review:** 7328dfd3937a1d37c7b274ce527c330e5b54d346 ("SPEC §13: close codex r1 blockers F1/F2/F3 + §2.4 contradiction")
**Parent for fix isolation:** 0848d34c09973e137e2ca855e85bbd682eb67b9f (immediate; the r1-reviewed commit 27c1020 is the SPEC §13 introduction whose defects are being closed)
**Reviewer:** Grok 4.3 (xAI) — clean-context session, independent reviewer #2 for r2 round
**Date:** 2026-05-23 (fresh session, zero prior memory of artefact or prior reviews during analysis)
**Workspace:** /srv/repos/external/verivus-oss/agent-assurance
**MCP usage:** sqry MCP first for all structural discovery on validators/validate_abstraction_class.py, core/ontology.toml symbols, DOMAIN_CHECKERS, per-domain checkers, _load_domains, validate_capability_envelope, etc. (index rebuilt with 48 files / 7736 symbols via sqry__rebuild_index; repeated semantic_search / pattern_search / get_workspace_symbols / list_files calls). Literal run_command (git, python, grep, sed, cat), read_file, and direct python -c only for exact line confirmation, command output capture, and existence checks after sqry orientation.
**Prior reviews read (before any verdict formation):** 
  - `docs/reviews/2026-05-23-spec-13-abstraction-class/codex-review.md` (Codex r1 — CONCRETE UNRESOLVABLE BLOCKERS F1/F2/F3 with verbatim quotes and file:line)
  - `docs/reviews/2026-05-23-spec-13-abstraction-class/raw_findings/grok.md` (prior Grok r1 — UNCONDITIONAL APPROVAL; positive-check methodology that missed all three)
  - `docs/reviews/2026-05-23-spec-13-abstraction-class/raw_findings/codex-fix-plan-r1.md` (Codex fix-plan review — UNCONDITIONAL APPROVAL of the proposed remediations, explicitly not an implementation approval)
**Re-derived HEAD:** 7328dfd3937a1d37c7b274ce527c330e5b54d346 (verified via `git log --oneline -5`, `git show 7328dfd --stat`, `git rev-parse HEAD`)
**Sandbox / approval posture:** danger-full-access on the workspace; all test artefacts confined to /tmp (never committed); tracked files never mutated; `git checkout --` used where needed for cleanliness. Network disabled for this run. No persistent state changes.
**Process hygiene:** Every command, negative test, validator invocation, and file existence check reproduced verbatim below with exit codes + last lines. No reliance on commit message intent, "should be fixed" language, or plan-compliance. Only source-grounded evidence.

---

## DIFF SCOPE CHECK

**Initiator claim (in query):** `git diff 27c1020..7328dfd` reports only `SPEC.md` and `CHANGELOG.md` changed (2 files, +65/-10 net).

**Verified reality (rule 1 — against code, not summary):**
```bash
git diff 27c1020..7328dfd --stat | tail -3
```
Actual output: 43 files changed, 3142 insertions(+), 10 deletions(-). The range includes the unrelated intermediate commit 0848d34 ("Close LL-001 in arxiv-prep-agent-dag.toml...") which added the entire arxiv-prep review tree under `docs/reviews/2026-05-24-arxiv-prep-dag/`, `arxiv-prep-agent-dag.toml`, `tools/claim-analysis-...`, etc.

**Isolating the actual r2 SPEC §13 fix commit (the only commit that claims to close F1/F2/F3):**
```bash
git diff --name-only 7328dfd^..7328dfd
```
Only two files:
- CHANGELOG.md
- SPEC.md

This matches the "2 files" description when the correct parent (immediate parent of the fix commit) is used. The initiator's range description was imprecise; the substantive changes under review for the blocker close live exclusively in 7328dfd^..7328dfd.

**Exact prose diff for the three fixes (7328dfd^..7328dfd -- SPEC.md):**
- F2 site (1268-1270): `(`false`)` → `denied = true` sub-table language.
- F1 site (1324-1330): full replacement of `core/kind-descriptor-kind.toml` claim with the three real normative surfaces + explicit §2.4 cross-reference.
- F3 site (1470-1472): deletion of the "Mix the technical-tier and legal-tier signatures..." bullet; surrounding three bullets untouched.

No other files in the r2 fix commit. All subsequent checks use the post-fix text at 7328dfd.

---

## ANSWERS TO Q1–Q7

### Q1 — F1 is mechanically closed

**Verdict:** Yes, mechanically closed with correct replacement prose.

**Evidence (all verified at 7328dfd):**

(a) `core/ontology.toml` is named as the source of the closed `capability_envelope.domain` vocabulary:
```bash
sed -n '1324,1330p' SPEC.md
```
```
The full table of grant sub-tables is normative and is declared
jointly by (a) the closed `capability_envelope.domain` vocabulary
in `core/ontology.toml`, (b) the per-domain shape checks enforced
by `validators/validate_abstraction_class.py`, and (c) this
section's prose. Per §2.4, tooling MUST NOT require a
`kind-descriptor-kind.toml` to exist; the validator + ontology +
SPEC §13 are the recursion-stop surfaces.
```
File exists and was cross-checked via sqry + python parse (9 values, `extensible = false`, IJB `constraint`/`structural`).

(b) `validators/validate_abstraction_class.py` is explicitly named as the enforcer of per-domain shape checks. The function `validate_capability_envelope` (sqry symbol at current index) + the DOMAIN_CHECKERS dispatch (lines 226-236) + the top-level sub-table guard (lines 306-310) are the live implementation.

(c) §2.4's "MUST NOT require `kind-descriptor-kind.toml`" rule is directly referenced ("Per §2.4...").

(d) `git diff 27c1020..7328dfd | grep kind-descriptor-kind.toml` returns only deletion markers from the r2 hunk + the historical quotes inside the new CHANGELOG entry (the §2.4 prohibition sentence itself). The normative claim that the file declared the schema is gone; only the prohibition quote remains.

**File:line citations for the old defect (now closed):**
- Old (27c1020): SPEC.md:1324-1327 quoted in Codex r1 review (codex-review.md:300-305).
- New (7328dfd): SPEC.md:1324-1330 — correct surfaces only.

No residual reference claiming `core/kind-descriptor-kind.toml` exists as a normative descriptor.

### Q2 — F2 is mechanically closed

**Verdict:** Yes.

**Evidence:**

Old prose (27c1020, quoted in codex-review.md:313-318):
> "Each domain is either denied entirely (`false`) or scoped via a sub-table."

New prose (7328dfd, SPEC.md:1268-1271):
> "Each domain is a sub-table — denied via `denied = true` or scoped via fields that constrain the grant."

Validator confirmation (read_file + sqry symbol `validate_capability_envelope`):
```python
# validators/validate_abstraction_class.py:306-310
if not isinstance(val, dict):
    errors.append(
        f"{loc}.{key}: top-level value must be a sub-table, "
        f"got {type(val).__name__}"
    )
```
Exact match to the new prose. The DOMAIN_CHECKERS short-circuit on `table.get("denied") is True` (every one of the 9 checkers: _check_domain_filesystem:142, _check_domain_sockets:152, etc.).

Missing-domain fail-closed semantic is preserved elsewhere (not removed):
- SPEC.md:1305-1307 (the §13.3 TOML example comment)
- SPEC.md:1321 (omitted domains comment)
- SPEC.md:1469 (§13.9 "Missing-domain = denied; the failure mode is fail-closed.")
- validator docstring and ontology notes (core/ontology.toml:648)

**Test confirmation (literal execution):**
A TOML file with `filesystem = false` (bool, not sub-table) under `[kind.capability_envelope]` produces:
```
FAIL ...: [kind.capability_envelope].filesystem: top-level value must be a sub-table, got bool
```
(Exit 1, as required.)

The worked example uses only sub-tables (see Q7).

### Q3 — F3 is mechanically closed

**Verdict:** Yes.

**Evidence:**

Old bullet (27c1020, quoted in codex-review.md:326-331 and codex-fix-plan-r1.md:50-53):
> - Mix the technical-tier and legal-tier signatures on the same artefact. Either tier carries the closure root; both is declared posture, not engineering.

New §13.9 (7328dfd, SPEC.md:1462-1472):
```markdown
Implementers MUST NOT:

- Re-sign an instance document under an unchanged `closure_root` after widening...
- Treat a missing capability domain table as an implicit grant...
- Encode capability declarations outside `[kind.capability_envelope]` in ad-hoc...
```
The mixed-tier bullet is absent. The three surrounding bullets are intact and are all capability-envelope papering-over mechanisms.

**No relocation (per Q3 instruction):**
```bash
git grep -n "Mix the technical-tier\|mixed.*signing.*tier\|technical-tier and legal-tier" -- '*.md' '*.toml' 2>/dev/null
```
Only match: CHANGELOG.md:553 — the historical quote inside the r2 "Changed" entry documenting the removal. No normative text anywhere in the repo now contains the rule.

§13.5 still defers signing tier (SPEC.md:1366-1369): "is profile/runtime choice."

### Q4 — No collateral regressions

**Commands run verbatim + exit codes + last lines:**

1. Abstraction-class validator sweep (all 19 descriptors):
```bash
python3 validators/validate_abstraction_class.py --repo-root . core/*-kind.toml profiles/agent-assurance/*-kind.toml profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml
```
EXIT: 0  
Last line: `ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 1 declared a §13 block).`

2. Manifest drift / count-mirror:
```bash
bash validators/check_manifest_drift.sh
```
EXIT: 0  
Last lines:
```
COUNT-MIRROR OK — every surface agrees with reality.

OK — manifest matches ontology + every count-mirror surface agrees
```

3. IJB conformance on core/ontology.toml (includes the two new §13 vocabularies):
```bash
python3 validators/validate_ijb_conformance.py core/ontology.toml
```
EXIT: 0  
Last lines:
```
IJB CONFORMANCE VALIDATION PASSED
- file: /srv/repos/external/verivus-oss/agent-assurance/core/ontology.toml
- template_kind: ontology
```

All three required commands exit 0 with clean final lines. No drift, no new violations introduced by the prose edits.

### Q5 — CHANGELOG.md hygiene

**Verdict:** Compliant.

**Evidence (CHANGELOG.md:519-576, [Unreleased] / Changed section):**

The entry titled "SPEC §13 — three independent-review blockers closed (r1 fix commit; Codex r1 findings F1/F2/F3 + the deeper §2.4 contradiction Claude surfaced during fix-plan synthesis)." contains:

- Verbatim quotes of the exact r1-commit (27c1020) defective sentences for each of F1, F2, F3 (with line numbers from that commit).
- Precise pointers to the three persistent review records:
  - `docs/reviews/2026-05-23-spec-13-abstraction-class/codex-review.md`
  - `.../raw_findings/grok.md`
  - `.../raw_findings/codex-fix-plan-r1.md`
- Description of what was actually edited in the implementation (prose rewrite for F1, syntax alignment for F2, bullet deletion for F3).
- Explicit note on the merge gate being the r2 reviewer verdicts (per ISS-001 discipline).

The entry is under `### Changed` in `[Unreleased]`, dated to the r2 fix commit. No drift between the changelog description and the actual diff.

### Q6 — Independent adversarial re-scan (Codex methodology applied to post-fix §13 at 7328dfd)

**Methodology:** sqry-first symbol discovery on validator + ontology, followed by literal `git ls-files` / `ls -f` / python tomllib parses / full-grep contradiction scans / negative TOML tests / §13.5 cross-checks against every other paragraph in §13. Every claim below is source-grounded.

**(a) Every file path mentioned in §13 — existence verified**

Explicitly named paths in current §13 prose (extracted via sed + grep on lines 1195-1490):
- `core/ontology.toml` — EXISTS + tracked + IJB-tagged + contains the 9-value closed vocabulary with `extensible = false`.
- `validators/validate_abstraction_class.py` — EXISTS + tracked + contains `validate_capability_envelope`, `DOMAIN_CHECKERS` (9 entries), `_load_domains` (single source of truth from ontology), all 9 `_check_domain_*` functions.
- `profiles/cost/cost-record-kind.toml` — EXISTS + tracked + is the only one of the 19 descriptors declaring the two §13 blocks; 9 domain sub-tables present.
- `docs/research/2026-05-22-spec-foundations-research/follow-up-2/16-stream-F-synthesis-v2.md` — EXISTS (research note referenced for wire-format / WASM scope-outs).
- `docs/issues/2026-05-23-ISS-002-graph-cypher-seed-incomplete.md` — EXISTS (follow-up tracking link in §13.10).
- `kind-descriptor-kind.toml` — correctly appears *only* inside the §2.4 prohibition sentence ("tooling MUST NOT require a `kind-descriptor-kind.toml` to exist"). The file itself does not exist (as required by §2.4 and confirmed by `find core -maxdepth 1 -name '*-kind.toml'` listing exactly the 6 core + 13 profile descriptors).

All paths that the prose claims are normative surfaces exist and were independently located via sqry + filesystem checks.

**(b) Every MUST / MUST NOT claim in §13 — no contradictions with rest of SPEC.md**

MUST/MUST NOT occurrences inside §13 (post-fix text):
- "Adopters who want the brittleness-propagation property of §13.4 MUST declare both." — Conditional on wanting the property; consistent with the backwards-compat rule in §13.10. No conflict.
- "Per §2.4, tooling MUST NOT require a `kind-descriptor-kind.toml` to exist" — Direct, accurate quotation of §2.4:128-134. Verified identical wording and intent.
- Runtime consequences in the §13.3 example ("The runtime MUST NOT open sockets...") — These are *derived* from the concrete envelope in the example descriptor; they are not new universal mandates on all runtimes. They illustrate what a consumer of *that* descriptor knows. No conflict with §12 or elsewhere.
- "Implementers MUST NOT:" + the three bullets in §13.9 — All three are capability-envelope papering-over mechanisms. The first explicitly cross-references "the same papering-over hazard §12.7 enumerates." §12.7 (SPEC.md:977-978 and 1059-1071) forbids stale re-sign under unchanged closure_root; §13.9 applies the identical rule to the envelope-widening case. They are additive and non-contradictory (the §13 version is narrower and maps back). No other §13 text contradicts them.

Full-repo grep for overlapping "re-sign" / "closure_root" language confirms deliberate consistency, not conflict. No other MUST NOT in §13 touches signing-tier composition (the F3 item is gone).

**(c) Every concrete syntax example in §13 prose — validator behaviour matches the claims**

1. The §13.3 TOML example (SPEC.md:1289-1322) shows:
   - `cpu_bounds` + `memory_bounds` as required tables.
   - `filesystem`, `sockets`, `http` as sub-tables (one with fields, two with `denied = true`).
   - Comment: "A domain whose table is entirely missing is treated as `denied = true` (fail closed)."

   Validator run on equivalent shapes (including the full cost-record example) passes. A file containing a bare `filesystem = false` (bool) at the capability_envelope table level produces exactly:
   ```
   FAIL ...: [kind.capability_envelope].filesystem: top-level value must be a sub-table, got bool
   ```
   (Exit 1, operator-visible, matches the prose rule.)

2. Unknown domain name test (via the validator's closed-set check at lines 312-317) produces:
   ```
   ...: not a capability domain. Closed set: [...]. Adding a new domain requires a SPEC amendment (§13.3).
   ```
   Matches the prose.

3. The worked example (Q7 below) with all 9 domains as sub-tables (some `denied = true`, some scoped) passes cleanly.

All syntax claims in the prose are accepted/rejected by the validator exactly as stated.

**(d) Every scope-out / deferral in §13.5 — no normative leakage elsewhere in §13**

§13.5 (SPEC.md:1355-1380) explicitly scopes out:
- Wire format / CBOR CDDL (separate Stream F V2 document)
- Attenuation calculus (pinned to Stream D executable spec)
- Signing tier ("is profile/runtime choice")
- Enforcement backend (runtime choice)
- WASM static observability (RUNTIME-SPEC)
- `runtime-observation-attestation` kind (future)

Post-fix scan of the entire §13 text (1195-1490) for any residual normative language on these surfaces:
- Signing tier: only the explicit deferral sentence remains. All other "sign" mentions are about closure-root cascade brittleness ("the signature does not survive a class change", re-sign requiring inspection of the widened envelope) — these are about *when* a signature becomes invalid, not which tier or mixing rule. The removed F3 bullet is the only prior item that would have conflicted; it is gone.
- No other paragraph in §13.3–§13.10 imposes a MUST/MUST NOT on wire format, attenuation algorithm, enforcement mechanism, or WASM observability.
- The §13.9 forbidden list is strictly limited to the three papering-over mechanisms that are in-scope for the kind-descriptor layer.

The deferrals are honest; §13 contains no hidden normative rules on the scoped-out surfaces.

**Q6 overall:** No new defects, no contradictions, no scope leakage, no missing-file claims. The r2 text is tighter and more precisely aligned with the validator + ontology than the r1 text was.

### Q7 — Worked example still passes

**profiles/cost/cost-record-kind.toml** (the canonical §13 worked example) was inspected at 7328dfd:

- Declares both `[kind.abstraction_class]` (id = "observation-record.v1") and `[kind.capability_envelope]`.
- `spec_version`, `cpu_bounds` (with `max_cpu_ms`), `memory_bounds` (with `max_bytes`) present.
- Exactly 9 domain sub-tables under `capability_envelope`: filesystem, sockets, http, clocks, random, environment, process_spawn, ipc, crypto_keys.
  - 7 use `denied = true` (whole-domain denial inside a sub-table).
  - 2 (clocks, random) use scoped fields instead of the denied flag.
- All IJB tags correct (`constraint` / `structural`).
- `ijb_primitive` / `ijb_constraint_type` present on both blocks.

**Validator run:**
```bash
python3 validators/validate_abstraction_class.py --repo-root . profiles/cost/cost-record-kind.toml
```
EXIT: 0  
`ABSTRACTION-CLASS VALIDATION PASSED (1 file(s) checked; 1 declared a §13 block).`

The 9-domain + resource-bounds shape matches the new §13.3 prose ("Each domain is a sub-table — denied via `denied = true` or scoped...") and the ontology closed set. No drift.

---

## TERMINAL VERDICT

**UNCONDITIONAL APPROVAL — r2 fix commit 7328dfd mechanically closes F1/F2/F3 with source-aligned prose, validator behaviour, preserved fail-closed semantics, no regressions on the 19-descriptor + IJB + manifest gates, correct CHANGELOG hygiene, and a clean adversarial re-scan of the post-fix §13 text (no contradictions, no scope leakage, all named files exist, all syntax examples match validator outcomes).**

The implementation matches the Codex-approved fix plan in every observable detail; the prior Grok r1 methodology gap is closed by this round's cross-reference discipline. No concrete unresolvable blockers remain.

**Review record persisted at:** `docs/reviews/2026-05-23-spec-13-abstraction-class/raw_findings/grok-r2.md`

---

**End of review.**