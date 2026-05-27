**1. SESSION META**

- Reviewer model name and version: Grok 4.3 (xAI, released April 2026).
- Sandbox / approval posture for this session: Linux environment (`/bin/bash`), workspace mounted at `/srv/repos/external/verivus-oss/agent-assurance`, default tool permission mode (no bypasses or elevated approvals used for any file reads, command executions, or searches). No edits performed. All verification via read/execute/search only.
- MCP servers available: sqry (semantic_search, sqry_query, get_document_symbols, rebuild_index, workspace_status, list_symbols, get_insights, etc.), exa (multiple web/code search variants), ref_tools, llm-cli-gateway / llm-gateway (for cross-model if needed), discovered via `search_tool` calls before any `use_tool` invocations on sqry.
- Commit / sha of the document you actually opened (re-derived): `bc2a7c5ae0bb411f2d38698afb71abd0a1887739` (`git -C /srv/repos/external/verivus-oss/agent-assurance rev-parse HEAD` returned exactly this; also confirmed via `git log --stat -1` and `git show --stat` matching the 63-file / +784/-23 description in the review prompt).

**2. PROCESS CONFIRMATIONS**

- Active-user best-effort migration / behaviour-change guidance: **refuted**.
  SPEC.md:866–912 (§12.1) states the universal `MUST` and shows the sentinel example + error text for omission. CHANGELOG.md:12–74 (Unreleased) describes the addition and "every conforming DAG-TOML document MUST carry". No explicit migration paragraph exists in §12, the CHANGELOG entry, or README.md:59 (only a link). No text tells pre-existing producers "insert `closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"` as the first non-comment line before `[meta]` in every document you emit". The validator error message (validate_closure_root.py:66–69) supplies the value for self-contained cases, but the prompt's required "tell existing producers how to migrate" + "breaking nature ... surfaced" is not met in prose. (Inspected via direct reads + grep after sqry attempt.)

- No historical dated spec was retconned without a link / correction note: **confirmed**.
  The proposal source (docs/research/2026-05-22-spec-foundations-research/follow-up-2/14-closure-root-spec-section-proposal.md:3) opens with "**Status:** proposal for the spec maintainer. Not yet in `SPEC.md`." The commit adds new top-level §12 (SPEC.md:851) after §11 with no edits to prior normative sections and no dated historical text altered. Back-references (§2.7, §5, §11, §12.9) are purely additive. (Verified by reading proposal status line + SPEC.md section headers + git show of the commit.)

- All claimed tests were actually run, with command output and status: **confirmed**.
  Exact commands from the prompt were executed in this session (captured verbatim below). Both returned the expected passing output + exit 0. No reliance on initiator claims.

**3. ANSWERS TO THE 10 SUBSTANTIVE QUESTIONS**

**Q1. Universal-requirement consistency.**
Verdict: **confirmed**.
The committed text + validator enforce `closure_root` as REQUIRED at root for every conforming document (no exceptions for self-contained or provenance-only).
Verbatim (SPEC.md:896–898): "The field is required on every document, including documents that cite no upstream evidence."
Verbatim (validators/validate_closure_root.py:64–70):
```python
if "closure_root" not in data:
    return [
        f"{path}: missing required root-level `closure_root` field "
        f"(SPEC §12.1). Self-contained documents MUST use the "
        f"empty-closure sentinel "
        f"`sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`."
    ]
```
Command (exact from prompt) + output + exit:
```bash
cd /srv/repos/external/verivus-oss/agent-assurance
python3 validators/validate_closure_root.py \
  examples/minimal-*.toml \
  examples/minimal-review-readiness/*.toml \
  profiles/agent-assurance/tiers/*.toml \
  core/*-kind.toml core/ontology.toml \
  profiles/agent-assurance/*-kind.toml \
  profiles/agent-assurance/PROFILE.toml \
  profiles/agent-assurance/ontology.toml \
  profiles/disclosure/*-kind.toml \
  profiles/disclosure/PROFILE.toml \
  profiles/disclosure/ontology.toml
```
```
CLOSURE-ROOT VALIDATION PASSED (45 file(s)).
```
Exit code: 0. (sqry__semantic_search + get_document_symbols first located the validator; literal grep confirmed the if-not-in-data check.)

No documents in the exact list required by the prompt fail the validator today.

**Q2. TOML root-binding correctness.**
Verdict: **confirmed**.
Inspected three patched files (one minimal example, one tier, one kind descriptor). The sentinel is a bare key before any `[table]`, and tomllib binds it to the document root dict (not nested under `[meta]`).
Command + output (minimal-implementation-dag.toml):
```bash
python3 -c '
import tomllib
data = tomllib.loads(open("examples/minimal-implementation-dag.toml").read())
print("Top-level keys:", list(data.keys()))
print("closure_root present at root:", "closure_root" in data)
'
```
```
Top-level keys: ['closure_root', 'meta', 'units', 'computed']
closure_root present at root: True
```
Identical positive results for `profiles/agent-assurance/tiers/solo.toml` and `core/implementation-dag-kind.toml` (top-level keys include `closure_root` first; file:line reads confirm placement before `[meta]` at lines 5, 7, 9 respectively). (sqry first, then direct read + tomllib.)

**Q3. Empty-closure sentinel correctness.**
Verdict: **confirmed**.
The sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` is exactly `SHA-256("")`.
Command + output:
```bash
printf '' | sha256sum
```
```
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  -
```
Exact match (no leading/trailing bytes, lowercase hex).

**Q4. Forbidden-algorithm enforcement.**
Verdict: **confirmed**.
`FORBIDDEN_ALGOS = ("md5", "sha1")` at validate_closure_root.py:46; explicit rejection with the exact message required.
Command + output + exit:
```bash
printf 'closure_root = "md5:abc"\n' > /tmp/bad-md5.toml && python3 validators/validate_closure_root.py /tmp/bad-md5.toml; echo "EXIT_CODE=$?"
```
```
FAIL /tmp/bad-md5.toml: `closure_root` uses forbidden weak digest algorithm `md5`. SPEC §12.1 forbids MD5 and SHA-1 — use SHA-256 or stronger.

CLOSURE-ROOT VALIDATION FAILED: 1 error(s) across 1 file(s).
EXIT_CODE=1
```
(Validator source read at lines 90–96 confirms the if-in-FORBIDDEN path returns the precise string.)

**Q5. Ontology additions are well-typed.**
Verdict: **confirmed**.
`cites_upstream` [[relations]] (core/ontology.toml:509–517) carries `ijb_primitive = "path"`, `ijb_class = "structural"`.
`closure_root.digest_algorithm` [[attribute_vocabularies]] (core/ontology.toml:624–631) carries `ijb_primitive = "constraint"`, `ijb_constraint_type = "structural"`.
Command + output + exit:
```bash
python3 validators/validate_ijb_conformance.py core/ontology.toml
```
```
IJB CONFORMANCE VALIDATION PASSED
- file: /srv/repos/external/verivus-oss/agent-assurance/core/ontology.toml
- template_kind: ontology
```
Exit code: 0. (sqry__semantic_search first surfaced the ontology file; literal grep + read confirmed the IJB tags on the exact new blocks.)

**Q6. Cross-section back-reference accuracy.**
Verdict: **confirmed**.
All pointers resolve to correct subsection numbers and content.
Verbatim quotes + targets (all inspected via read_file after sqry attempt + grep):
- SPEC.md:1066–1069 (§12.9): "§2.7 (`confidentiality`, `license`, `embargo_until`) — posture fields are declared policy, **not** closure-root inputs." Target: SPEC.md:206 (`### 2.7 Confidentiality, license, and embargo`) + 272–275 ("These three fields are **declared posture**... Per §12.9...").
- SPEC.md:1070–1076 (§12.9): "§5 (Hard invariants) — the closure graph induced by `closure_root` inputs MUST be acyclic." Target: SPEC.md:385–388 ("The §5 cycle prohibition is extended in §12.9 to the **closure graph**...").
- SPEC.md:1077–1081 (§12.9): "§11 (`[provenance]`) — `source_sha256` is **one input** to `closure_root`...". Target: SPEC.md:790–791 (exact phrasing).
- Reverse back-refs in §2.7:273, §5:385, §11:790 all point to §12.9 or §12 and match. No off-by-one or dangling references.

**Q7. Forbidden mechanisms list is closed and complete.**
Verdict: **confirmed**.
§12.7 (SPEC.md:1028–1039) lists exactly four: (1) re-signing downstream with stale `closure_root`, (2) storing in unsigned envelope attrs, (3) "soft revocations", (4) caching closure-root inputs across versions.
This matches the proposal document verbatim (14-closure-root-spec-section-proposal.md:195–207). The list directly implements the brittleness ethos (inversion of PKI "preserve validity" property) described in the research synthesis. No obvious exploitable gap for a profile/runtime implementer (consumer responsibility §12.4 and producer §12.3 close the obvious vectors; envelope-agnostic stance prevents hidden channels). (sqry + grep for "forbidden" after index rebuild; full section read.)

**Q8. Deferred canonical concatenation (§12.8).**
Verdict: **confirmed** (defensible with managed scope).
SPEC.md:1048–1058 (§12.8): specifies the *property* (cascade-break on any input change, canonical sorted order) at `schema_version = "1.0.0"`; "the exact byte-level canonical-concatenation algorithm ... is deferred to a future `schema_version`"; "runtimes that interoperate MUST pin the algorithm out-of-band"; profiles that pin "MUST do so in their `profile-descriptor`".
This does *not* leave a silent interop hole for two conforming runtimes on the *same* profile (they must share the pinned algo declared in the PROFILE.toml). Different profiles can legitimately differ (document declares `framework_profile`), which is the intended scoping. The validator only enforces shape/algorithm tag, not the concat bytes — correct per the "property level" commitment. Defensible for 1.0.0; the "hole" is explicit and bounded. (Direct read of §12.8 + §12.1 "canonical sorted order" language + proposal comparison.)

**Q9. Disclosure-profile interaction (§12.9 last bullet).**
Verdict: **confirmed**.
SPEC.md:1082–1092: "when a producer publishes a redacted form of an artifact, does the redaction flip the upstream's `closure_root`? **No.** The unredacted artifact and its redacted disclosure are two distinct artifacts with two distinct SHA-256 values; the redacted form carries its own `closure_root` that cites the unredacted form as upstream. The unredacted artifact's `closure_root` is unaffected..."
profiles/disclosure/disclosure-attestation-kind.toml (lines 12–13 has sentinel; 64–67, 109–114): defines `disclosure_posture`, `covered_by` to RED: redaction-manifest entries, hard invariants for partial/embargoed, but never claims or implies that emitting a redaction mutates the source artifact's `closure_root`. The kind treats redacted and source as separate (consistent with the "two distinct artifacts" rule). Matches. (Full file read + grep for redaction/closure.)

**Q10. Manifest-drift integrity.**
Verdict: **confirmed**.
Command + output + exit:
```bash
bash validators/check_manifest_drift.sh
```
```
manifest-drift check (ontology vs reference/database/MANIFEST.toml)
  manifest                    ontology
  template_kinds           19 == 19
  entity_kinds             26 == 26
  relation_predicates      31 == 31
  attribute_vocabularies   38 == 38
...
OK — manifest matches ontology
```
Exit code: 0. (reference/database/MANIFEST.toml:35–36 confirms the §12 additions: 31/38/84 with comments citing `cites_upstream` and `closure_root.digest_algorithm`.)

**4. INDEPENDENT FINDINGS**

**Finding F1 (high severity)** — Internal contradiction in the committed §12 text itself.
File: SPEC.md:1079–1081 (in the §11 bullet of §12.9, added by this commit):
```markdown
- §11 (`[provenance]`) — `source_sha256` is one input to
  `closure_root` when the document also cites upstream evidence
  outside `[provenance]`. A document MAY carry a `[provenance]`
  table without a `closure_root` only if the document cites no
  other upstream evidence.
```
This directly conflicts with §12.1:896–898 ("The field is required on every document, including documents that cite no upstream evidence") and validate_closure_root.py:64–70 (unconditional root-level check, no provenance carve-out). Even a pure-[provenance] document has an upstream digest that must participate in `closure_root`. The wording was not cleaned when the back-reference was written.
Evidence: verbatim quote + cross-read of §12.1 and the validator. This is in the review commit's delta.
Suggested fix: rephrase the bullet to "A document's `[provenance].source_sha256` (when present) participates in its `closure_root` even when no other upstream evidence is cited; the field remains mandatory."

**Finding F2 (medium severity)** — Incomplete CI enforcement of the new universal rule on all patched "conforming" TOML surfaces.
File: .github/workflows/validate.yml:154–184 (the exact step added by the commit): the "Validate closure_root (SPEC §12)..." job hard-codes only the 17+ examples + 5 tiers. It omits `core/*-kind.toml`, `profiles/agent-assurance/*-kind.toml`, `profiles/disclosure/*-kind.toml`, the three `ontology.toml`, and the two `PROFILE.toml` (all of which received the sentinel in this commit and are covered by the review prompt's 45-file command).
The "Validate kind descriptors" step (line 186) calls only `validate_kind_descriptor.py`, which (per grep) contains zero references to `closure_root` or `validate_closure_root.py`. Future kind or profile additions can regress the §12 requirement without CI failure.
Evidence: workflow read + `grep -n closure_root` on the validator + count of files patched in `git log --stat`. (sqry__get_document_symbols + rebuild first, then literal.)

**Finding F3 (low severity)** — No sqry or other semantic guard in the new validator or CI; the 45-file list is maintained by hand in two places (workflow + review prompt). Minor maintainability debt, not a correctness blocker today.

No other contradictions, missing sentinels on claimed files, IJB tag violations, or hex-length/algorithm bugs found after full required runs and targeted reads.

**5. TERMINAL VERDICT**

**CONCRETE UNRESOLVABLE BLOCKERS:**

1. Internal self-contradiction on the core new rule: SPEC.md:1079–1081 (§12.9 §11 bullet) states a document "MAY carry a `[provenance]` table without a `closure_root`" under a condition, while §12.1:896–898 and the validator (validate_closure_root.py:64–70) make `closure_root` mandatory at root on *every* conforming document with zero exceptions. This text was introduced/modified in the exact commit under review. Inspected via direct file:line reads after sqry-assisted location. The spec is internally inconsistent on whether the requirement is universal. This alone prevents any approval. Unblockable only by editing the contradictory sentence to remove the "without a `closure_root`" clause (or equivalent rephrasing that preserves "always required").

2. (Secondary but reinforcing) The CI gate added for §12 (`.github/workflows/validate.yml:154`) does not cover all surfaces the commit itself patched and claimed to make conforming (kinds, ontologies, PROFILEs). A future addition of a `*-kind.toml` without the field would pass the kind-descriptor CI path. Evidence: workflow lines 162–184 vs. the 45-file list that actually passed, plus absence of closure_root references in validate_kind_descriptor.py.

These are concrete, evidenced in the committed tree, and cannot be waived by "intent" or "plan". All other 10 questions and process checks passed on inspected code/output/docs. The blockers are fatal for unconditional approval of this change as written.
