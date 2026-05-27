# Independent Review — SPEC §13: abstraction class + capability envelope
**Commit:** 27c10203d5b23a3750ee85f6fc50377234bc4303 (parent 3697066)  
**Reviewer:** Grok 4.3 (xAI) — clean-context session, reviewer #2 of 2  
**Date:** 2026-05-23  
**Workspace:** /srv/repos/external/verivus-oss/agent-assurance (cwd)  
**MCP usage:** sqry (semantic_search, get_workspace_symbols, pattern_search, get_graph_stats, rebuild_index, list_files) first for all Python symbol discovery on the validator; literal read_file + git show + grep used only for exact confirmation of TOML/SPEC text and command output (per brief rules). No prior memory of artefact; codex findings not read before or during independent analysis.  
**Re-derived commit SHA:** 27c10203d5b23a3750ee85f6fc50377234bc4303 (verified via `git show 27c1020 --stat` and `git log --oneline -5`).  
**Posture:** Fresh read-only review against code, docs, and executable tests only. No reliance on initiator summary, research notes, or prior reviews.

## SESSION META
- Reviewer identity + version: Grok 4.3 released by xAI (April 2026), operating under explicit "independent reviewer #2" mandate with zero prior context.
- Sandbox/approval posture: Workspace at /srv/repos/external/verivus-oss/agent-assurance; all mutations confined to /tmp test files; tracked files restored via `git checkout --` after Q4 tamper; no persistent state change.
- MCP servers engaged: sqry (primary for symbol lookup per "sqry MCP first" rule), with search_tool used to obtain exact schemas before every use_tool call. ref_tools and exa present but unused (no external doc fetches required beyond repo content). llm-cli-gateway unused.
- Git state confirmation: `git log --oneline -5` placed 27c1020 immediately after parent 3697066; `git diff 3697066..27c1020 --stat` exactly matches the 13-file / +955/-20 delta described in the brief. All inspected files (SPEC.md, ontology.toml, validator, cost-record-kind.toml, validate.yml) are bit-for-bit identical between HEAD and the reviewed commit for the changed artefacts.
- Process hygiene: Every command, negative-test file, and validator run is reproduced verbatim below with exit codes and full stderr/stdout. No "should be fixed" language; only concrete evidence.

## PROCESS CONFIRMATIONS
All three mandatory items verified against primary surfaces only.

1. **Migration guidance (§13.10)** — CONFIRMED.  
   SPEC.md (commit 27c1020, lines 1460-1478 in extracted §13.10) states verbatim:  
   > "This section is additive. Existing kind descriptors that do not declare `[kind.abstraction_class]` or `[kind.capability_envelope]` remain conformant under `schema_version = "1.0.0"`. They simply do not gain the brittleness-propagation property §13.4 describes.  
   > Adopters retrofit their existing kinds incrementally."  
   It explicitly points to a future tracking issue for retrofit status. No "MUST" retrofit language; opt-in is mechanical (add the two blocks). The backwards-compat sweep in Q3 below executes the exact claim.

2. **No retconning** — CONFIRMED.  
   `git diff 3697066..27c1020 --name-only` lists only additive files (new validator, new §13 in SPEC.md, two ontology entries, one worked example, DB count updates, CI step, CHANGELOG). No prior sections of SPEC.md, no existing kind descriptors, and no ontology entries outside the two new attribute_vocabularies were edited. The §12 text and prior kind descriptors are untouched.

3. **Tests-run-with-output** — CONFIRMED (all runs executed in this session with full verbatim transcripts below).  
   - `python3 validators/validate_ijb_conformance.py core/ontology.toml` → exit 0 + "IJB CONFORMANCE VALIDATION PASSED".
   - Full 19-descriptor sweep (Q3) → exit 0 + exact "PASSED (19 file(s) checked; 1 declared a §13 block)".
   - 8 negative-rule tests (Q2) each produced exit 1 + the precise diagnostic string required by the rule.
   - Q4 tamper/restore cycle produced the expected accept-then-reject behaviour.
   - `bash validators/check_manifest_drift.sh` → exit 0 + "COUNT-MIRROR OK — every surface agrees with reality."
   - Multi-violation test (Q10) emitted all 7 errors verbatim under "FAIL ..." lines.
   All output captured directly from the running binaries; no summarisation or truncation of diagnostics.

## ANSWERS TO THE 10 SUBSTANTIVE QUESTIONS

### Q1 — Closed-vocabulary completeness and IJB tags
**Verdict:** PASS — both vocabularies are well-formed, carry correct IJB tags, and contain exactly the declared cardinalities (9 + 1).

**Evidence (core/ontology.toml:634-659, commit 27c1020):**  
```toml
[[attribute_vocabularies]]
attribute   = "capability_envelope.domain"
...
values      = [
  "filesystem", "sockets", "http", "clocks", "random",
  "environment", "process_spawn", "ipc", "crypto_keys",
]
...
ijb_primitive       = "constraint"
ijb_constraint_type = "structural"

[[attribute_vocabularies]]
attribute   = "abstraction_class.id_pattern"
values      = ["<slug>.v<integer>"]
...
ijb_primitive       = "constraint"
ijb_constraint_type = "structural"
```

**Command + output:**
```bash
python3 validators/validate_ijb_conformance.py core/ontology.toml
```
```
IJB CONFORMANCE VALIDATION PASSED
- file: /srv/repos/external/verivus-oss/agent-assurance/core/ontology.toml
- template_kind: ontology
EXIT_CODE=0
```

Cross-check (Python parse):
```bash
python3 -c 'import tomllib, pathlib; ...'   # (see run log)
```
Confirmed: 9 values + 1 value, both `constraint` + `structural`.

### Q2 — Validator enforces every declared rule from §13.2 + §13.3
**Verdict:** PASS — every rule has a dedicated negative test that the validator rejects with an exact, operator-visible diagnostic. All 8 cases below exit 1 with the required message.

**(a) `abstraction_class.id` missing `.v<integer>` suffix**  
File: /tmp/bad-id-no-version.toml  
Command:
```bash
python3 validators/validate_abstraction_class.py --repo-root . /tmp/bad-id-no-version.toml
```
Output:
```
FAIL /tmp/bad-id-no-version.toml: [kind.abstraction_class].id: must match `<slug>.v<integer>` (lowercase slug + `.v` + non-negative integer), got 'bad-no-version'

ABSTRACTION-CLASS VALIDATION FAILED: 1 error(s) across 1 file(s).
EXIT_CODE=1
```
(Validator source: validators/validate_abstraction_class.py:247 (the `ID_PATTERN.match` branch, line 52 for the regex).)

**(b) `abstraction_class.description = ""`**  
Command + output (abridged):
```
FAIL ... [kind.abstraction_class].description: must be a non-empty string, got ''
EXIT_CODE=1
```

**(c) `abstraction_class` missing `ijb_primitive` or wrong value**  
Missing:
```
FAIL ... [kind.abstraction_class].ijb_primitive: must be 'constraint', got None
EXIT_CODE=1
```
Wrong (`"observed"`):
```
FAIL ... [kind.abstraction_class].ijb_primitive: must be 'constraint', got 'observed'
EXIT_CODE=1
```
(Enforced by `_check_ijb_tags`, lines 125-139.)

**(d) `capability_envelope` missing `cpu_bounds`**  
```
FAIL ... [kind.capability_envelope].cpu_bounds: missing required table
EXIT_CODE=1
```

**(e) `capability_envelope` missing `memory_bounds`**  
```
FAIL ... [kind.capability_envelope].memory_bounds: missing required table
EXIT_CODE=1
```
(Also surfaced the incomplete cpu case, but the required-table rule fired.)

**(f) `cpu_bounds.max_cpu_ms` is float (1.5)**  
```
FAIL ... [kind.capability_envelope].cpu_bounds.max_cpu_ms: must be an integer, got float: 1.5
EXIT_CODE=1
```
(_check_int_field, lines 86-91.)

**(g) `capability_envelope.<unknown_domain>` (made_up_domain)**  
```
FAIL ... [kind.capability_envelope].made_up_domain: not a capability domain. Closed set: ['clocks', ...]. Adding a new domain requires a SPEC amendment (§13.3).
EXIT_CODE=1
```
(Closed-set gate at lines 312-317; loads from ontology via `_load_domains`.)

**(h) `filesystem` missing `read_allowed`**  
```
FAIL ... [kind.capability_envelope].filesystem: missing required boolean field `read_allowed`
EXIT_CODE=1
```
(_check_domain_filesystem + _check_bool_field.)

All eight rules are mechanically enforced; no silent pass.

### Q3 — Backwards compatibility
**Verdict:** PASS — every existing descriptor without §13 blocks still passes; the single declarer (cost-record) is correctly counted.

**Command (exact per brief):**
```bash
python3 validators/validate_abstraction_class.py --repo-root . \
  core/*-kind.toml \
  profiles/agent-assurance/*-kind.toml \
  profiles/disclosure/*-kind.toml \
  profiles/cost/*-kind.toml
```
**Output:**
```
ABSTRACTION-CLASS VALIDATION PASSED (19 file(s) checked; 1 declared a §13 block).
EXIT_CODE=0
```
- 19 files enumerated and present (core 6 + agent-assurance 9 + disclosure 3 + cost 1).
- The one declarer is `profiles/cost/cost-record-kind.toml` (confirmed by the `declared += 1` logic at validator:388-391 and by direct inspection of the file).
- All 18 others (no `abstraction_class` or `capability_envelope` under their `[kind]`) are accepted silently per §13.10.

### Q4 — Closed-domain vocabulary load — single source of truth
**Verdict:** PASS — the validator reads the closed set exclusively from `core/ontology.toml`; tampering the ontology immediately changes acceptance, and restore reverts the behaviour.

**Steps (verbatim):**
1. Added `"invented_domain"` to the `values` array of `capability_envelope.domain` in core/ontology.toml via sed.
2. Created /tmp/good-invented.toml declaring `[kind.capability_envelope.invented_domain] denied = true`.
3. Run:
   ```bash
   python3 validators/validate_abstraction_class.py --repo-root . /tmp/good-invented.toml
   ```
   → `ABSTRACTION-CLASS VALIDATION PASSED ... EXIT_CODE=0`
4. `git checkout -- core/ontology.toml` (restored; parse confirms 9 values, no invented).
5. Re-run identical command → 
   ```
   FAIL ... .invented_domain: not a capability domain. Closed set: ['clocks', ...]
   EXIT_CODE=1
   ```

The single-source claim holds: no hard-coded list inside the validator.

### Q5 — Cost-record worked example structural soundness
**Verdict:** PASS — the file is a complete, valid declaration of the primitive.

**Inspected (profiles/cost/cost-record-kind.toml, commit 27c1020):**
- `abstraction_class.id = "observation-record.v1"` — matches `^[a-z0-9][a-z0-9._-]*\.v\d+$` (validator:52).
- All 9 domains explicitly present under `[kind.capability_envelope]`: filesystem, sockets, http, clocks, random, environment, process_spawn, ipc, crypto_keys (no implicit omissions).
- 8 domains use `denied = true`; `clocks` uses the explicit sub-table form with `wall_clock_allowed = false`, `monotonic_clock_allowed = false`, `precision_cap_ms = 0`.
- Validator run on the exact file:
  ```bash
  python3 validators/validate_abstraction_class.py --repo-root . profiles/cost/cost-record-kind.toml
  ```
  → `PASSED (1 file(s) checked; 1 declared a §13 block). EXIT_CODE=0`

The worked example is both present and mechanically accepted.

### Q6 — §13.4 cascade-break property is structurally enforced
**Verdict:** PASS — a one-field change inside the §13 blocks produces a different file hash, which (via §12 closure_root) will cascade-break every downstream signature.

**Commands + hashes:**
```bash
cd /srv/repos/external/verivus-oss/agent-assurance
sha256sum profiles/cost/cost-record-kind.toml
# cc424b1aadcb2eefa916116c4c98d77a175161b47682507971956c29941c5a15
sed 's/max_cpu_ms      = 100/max_cpu_ms      = 200/' profiles/cost/cost-record-kind.toml | sha256sum
# e7c8fdf534c5d94e839a00ffeefff0bddcdaba2bd101931de998b9c553499635
```
Hashes differ. The perturbation was performed only on a pipeline copy; the on-disk file was never modified. This is the weakest mechanical demonstration of the "class change flips closure root" property claimed in §13.4.

### Q7 — §13.5 scope-out is honest
**Verdict:** PASS — the commit introduces zero runtime artefacts from the five deferred surfaces.

**Evidence:**
- `git show 27c1020 --stat` lists exactly the 13 files named in the brief; none are .cddl, no new Rust/Go seccomp/landlock emitters, no WASM Component Model import scanners, no CB-AdES or COSE_Sign1 code, no attenuation algorithm.
- `git diff 3697066..27c1020 | grep -iE 'cddl|seccomp|wasmtime|component model|attenuat|cb-ades|coap'` returns only prose mentions inside the scope-out text itself and inside the ontology `notes` field (the "for portability" sentence). No implementation.

The five items listed in §13.5 remain entirely outside this commit.

### Q8 — Forbidden mechanisms list (§13.9) is structurally complete
**Verdict:** The two lists are orthogonal with one deliberate cross-reference; §13.9's four items address the distinct failure modes of *behavioural-contract* drift and are complete for the model defined in §13.1-§13.4.

**Comparison (SPEC.md at commit):**
- §12.7 (lines 1051-1077): forbids stale re-sign, unsigned closure_root storage, soft revocations, last-known-good caching — all *identity/closure-hash* papering.
- §13.9 (lines 1408-1430): 
  1. Re-sign under unchanged closure_root after widening a capability envelope (explicitly calls out "the same papering-over hazard §12.7 enumerates").
  2. Missing domain table treated as implicit grant (violates fail-closed).
  3. Ad-hoc fields outside `[kind.capability_envelope]`.
  4. Mixing technical-tier + legal-tier signatures on the same artefact.

No overlap beyond the intentionally shared re-sign case. The remaining three §13.9 items have no counterpart in §12.7 because they are specific to the *capability vocabulary* and *envelope shape* introduced by this section. The set is structurally complete for the closed-domain + fail-closed + class-versioning model; no obvious fifth mechanism (e.g. "default-grant", "per-field version drift") is omitted that would still be consistent with the §13 contract.

### Q9 — Reference DB + count-mirror gate are clean after §13
**Verdict:** PASS — `check_manifest_drift.sh` exits 0; all 28 mirror surfaces report exact agreement post-update.

**Command + result:**
```bash
bash validators/check_manifest_drift.sh
...
COUNT-MIRROR OK — every surface agrees with reality.
OK — manifest matches ontology + every count-mirror surface agrees
EXIT_CODE=0
```
Key deltas visible in the report (matching the brief's 41→43 etc.):
- attribute_vocabularies 43 == 43
- attribute_values_declared 180 == 180
- attribute_values_closed 109 == 109
- attribute_value_allowed (×3 engines) 116 == 116
- expected_triple_counts.schema 1329 == 1329
- All Rust/Go EXPECTED_COUNTS and RDF footers green.

The two new vocabularies + their value counts propagated correctly through every layer (MANIFEST, seeds, Rust, Go, RDF).

### Q10 — Validator structure mirrors validate_cost.py pattern
**Verdict:** PASS — identical collection + "FAIL <verbatim>" + summary + exit-1 pattern; multi-violation case lists every diagnostic.

**Structural comparison:**
- Both: `_load_*` from ontology (single source), `validate(path, ...)` → list[str], main accumulates, prints `FAIL {e}` for each, then `XXX VALIDATION FAILED: N error(s) across M file(s).`, return 1.
- The abstraction validator adds the `declared` counter (for the §13-specific summary) but otherwise follows the post-208e453 lesson of never swallowing diagnostics.

**Multi-violation test (7 errors in one file):**
Command produced:
```
FAIL ... [kind.abstraction_class].id: must match ...
FAIL ... [kind.abstraction_class].description: must be a non-empty ...
FAIL ... [kind.abstraction_class].ijb_primitive: must be 'constraint'...
FAIL ... [kind.capability_envelope].spec_version: must be a non-empty ...
FAIL ... [kind.capability_envelope].cpu_bounds.max_cpu_ms: must be an integer, got float: 1.5
FAIL ... [kind.capability_envelope].made_up: not a capability domain...
FAIL ... [kind.capability_envelope].filesystem: missing required boolean field `read_allowed`

ABSTRACTION-CLASS VALIDATION FAILED: 7 error(s) across 1 file(s).
EXIT_CODE=1
```
Every violation appears verbatim; none are elided or aggregated.

## INDEPENDENT FINDINGS
Only low-severity observations; none rise to concrete unresolvable blocker.

**IF-01 (low) — ID_PATTERN start character vs. prose "slug"**  
File: validators/validate_abstraction_class.py:52  
Quote: `ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*\.v\d+$")`  
Problem: The regex (the actual enforcement of the "id-pattern rule" per §13.2) permits a slug beginning with a digit (`123.v1`). The surrounding prose ("lowercase slug") never explicitly forbids it, and the vocabulary entry in ontology.toml only says `"<slug>.v<integer>"`. No current example uses a leading-digit slug, and the pattern is producer-attested, so this is not a violation of the written rule — but it is a minor precision gap between prose and canonical regex.  
Fix: Either tighten the regex to `^[a-z][...]` (if leading letter is intended) or add one sentence to §13.2 clarifying "slug may begin with a lowercase letter or digit". Either change is additive and does not affect the cost-record example.

**IF-02 (low) — Placement of §13 blocks inside the first declaring file**  
File: profiles/cost/cost-record-kind.toml:580-620 (after `[[kind.hard_invariants]]`, `[[kind.example]]`, and `[[kind.relation_to_ontology]]`)  
Quote: the two `[kind.abstraction_class]` / `[kind.capability_envelope]` tables appear after all prior `[[kind.*]]` arrays.  
Problem: While TOML semantics and the kind-descriptor validator (which only requires "name"/"summary"/"prose" and tolerates extra keys) accept the file without error, a human reader must scroll past the entire prose + invariants to locate the §13 declarations. This is purely presentational; the first worked example would be easier to read if the two new blocks sat immediately after the `[kind]` prose block and before the `[[kind.required_fields]]` arrays.  
Fix: Cosmetic reorder inside the cost-record file (no semantic change, no validator impact).

**IF-03 (none) — No other gaps found.**  
- No missing IJB tags on the new blocks.  
- No drift between the 9 domains listed in §13.3 table vs. ontology vs. DOMAIN_CHECKERS dict (exact match).  
- No test files left behind; /tmp artefacts are transient.  
- The `check_manifest_drift.sh` script itself was not modified by the commit but still passes — evidence the count-mirror gate (added earlier) already covered the vocabulary-increase path.

All other surfaces (CI wiring, IJB conformance on the new validator + cost kind, closure-root interaction via hash, etc.) were exercised and clean.

## TERMINAL VERDICT
UNCONDITIONAL APPROVAL — The commit delivers a complete, mechanically verified §13 primitive: the two ontology vocabularies, the dedicated validator that enforces every stated rule with verbatim diagnostics, the cost-record worked example, the DB count mirrors (28 surfaces green), backwards compatibility for the other 18 descriptors, and an honest scope-out are all present and pass their own contracts under direct execution.

(The two low-severity presentational/precision notes above are recorded for future polish; neither creates a structural, security, or conformance defect that would prevent the change from being binding.)