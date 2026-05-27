1. SESSION META

- Reviewer model name and version: Codex, based on GPT-5.
- Sandbox / approval posture: `danger-full-access`; network enabled; approval policy `never`; no approvals requested.
- MCP servers available/used: sqry MCP via `mcp__sqry__` tools. I used `mcp__sqry__.get_index_status` and `mcp__sqry__.semantic_search` before literal `rg`/file inspection.
- Re-derived HEAD:

```bash
git rev-parse HEAD
```

```text
dc3a7b0c35d0d4beb6c3b8143b74af2e272a5af8
```

2. PROCESS CONFIRMATIONS

**Migration guidance present?** refuted.

Evidence that the change is behavior-changing:

- `README.md:42-44`:
```text
Backwards-incompatible changes require a schema major-version bump and a
migration note. Additive changes use the minor version path described in
[SPEC.md](SPEC.md#8-versioning-policy).
```

- `SPEC.md:486-488`:
```text
- Removing fields, changing field semantics, or tightening validation is
  a **major** bump and ships with a migration note.
```

- `SPEC.md:896-908`:
```text
The field is required on every document, including documents that
cite no upstream evidence. A self-contained document — one whose
closure inputs (§12.1.1 + §12.1.2) are both the empty set — MUST emit
the **canonical empty-closure sentinel**:
...
Validators MUST recognise this value as the canonical empty-closure sentinel,
treat it as equivalent in structural meaning to "no upstream
evidence", and reject any document that omits `closure_root`
entirely.
```

The `CHANGELOG.md` entry explains the new rule, but I found no migration note telling existing producers how to update already-valid DAG-TOML documents. Literal confirmation:

```bash
rg -n "migration|migrate|breaking|backwards|incompatible|closure_root" SPEC.md CHANGELOG.md README.md
```

```text
README.md:42:Backwards-incompatible changes require a schema major-version bump and a
README.md:43:migration note. Additive changes use the minor version path described in
SPEC.md:488:  a **major** bump and ships with a migration note.
SPEC.md:866:Every conforming DAG-TOML document MUST carry a `closure_root` field
CHANGELOG.md:16:  carry a root-level `closure_root` field of the form
```

**No retconning?** confirmed.

The reviewed range changes `SPEC.md`, `CHANGELOG.md`, `README.md`, validators, workflow, ontology/reference artifacts, and conforming TOML surfaces. It does not modify `docs/research/` historical research artifacts.

```bash
git diff --stat 638a90e..HEAD -- docs/research docs/reviews tools/review-request-dag.toml
```

```text

```

Exit code: 0.

**Claimed tests actually run with output?** confirmed, with an important caveat: the requested canonical-surface validator passes, but a broader tracked-conforming-document check fails. Required commands:

```bash
bash validators/check_manifest_drift.sh
```

```text
manifest-drift check (ontology vs reference/database/MANIFEST.toml)
  manifest                    ontology
  template_kinds           19 == 19
  entity_kinds             26 == 26
  relation_predicates      31 == 31
  attribute_vocabularies   38 == 38

rdf-drift check (schema.ttl footer vs ontology)
  schema.ttl                  ontology
  template_kinds           19 == 19
  entity_kinds             26 == 26
  relation_predicates      31 == 31
  attribute_vocabularies   38 == 38

OK — manifest matches ontology
```

Exit code: 0.

```bash
python3 validators/validate_closure_root.py --discover core profiles examples
```

```text
CLOSURE-ROOT VALIDATION PASSED (57 file(s)).
```

Exit code: 0.

3. ANSWERS TO THE 10 SUBSTANTIVE QUESTIONS

### Q1. Universal-requirement consistency

Verdict: refuted_with_evidence.

The spec and validator state the universal requirement:

- `SPEC.md:866-879`:
```text
Every conforming DAG-TOML document MUST carry a `closure_root` field
whose value is a cryptographic digest over the canonical
concatenation of:
...
The digest algorithm MUST be SHA-256 or stronger. Weaker algorithms
(MD5, SHA-1) are forbidden.
```

- `validators/validate_closure_root.py:64-70`:
```python
if "closure_root" not in data:
    return [
        f"{path}: missing required root-level `closure_root` field "
        f"(SPEC §12.1). Self-contained documents MUST use the "
        f"empty-closure sentinel "
        f"`sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`."
    ]
```

The requested canonical discovery passes:

```bash
python3 validators/validate_closure_root.py --discover core profiles examples
```

```text
CLOSURE-ROOT VALIDATION PASSED (57 file(s)).
```

Exit code: 0.

But tracked conforming DAG-TOML documents outside `core profiles examples` still fail. I filtered tracked TOML files by the validator’s own convention, `[meta].template_kind`:

```bash
python3 - <<'PY'
import pathlib, subprocess, tomllib
tracked = subprocess.check_output(['git','ls-files','*.toml'], text=True).splitlines()
conforming=[]
missing=[]
for s in tracked:
    p=pathlib.Path(s)
    try:
        data=tomllib.loads(p.read_text())
    except Exception:
        continue
    if isinstance(data.get('meta'), dict) and isinstance(data['meta'].get('template_kind'), str):
        conforming.append(s)
        if 'closure_root' not in data:
            missing.append(s)
print('tracked_conforming_count =', len(conforming))
print('tracked_conforming_missing_closure_root_count =', len(missing))
for s in missing:
    print(s)
PY
```

```text
tracked_conforming_count = 65
tracked_conforming_missing_closure_root_count = 8
VERIFICATION_REPORT.toml
paper/VERIFICATION_REPORT.toml
skills/convert-md-to-dag/CONTRACT_DECLARATION.toml
skills/convert-md-to-dag/IMPLEMENTATION_DAG.toml
skills/convert-md-to-dag/REVIEW_READINESS.toml
skills/convert-md-to-dag/ROLLBACK_PLAN.toml
skills/convert-md-to-dag/THREAT_MODEL.toml
skills/convert-md-to-dag/TRACEABILITY.toml
```

Exit code: 0.

Focused validator run on those tracked conforming files:

```bash
python3 validators/validate_closure_root.py --discover VERIFICATION_REPORT.toml paper skills/convert-md-to-dag
```

```text
FAIL VERIFICATION_REPORT.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL paper/VERIFICATION_REPORT.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL skills/convert-md-to-dag/CONTRACT_DECLARATION.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL skills/convert-md-to-dag/IMPLEMENTATION_DAG.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL skills/convert-md-to-dag/REVIEW_READINESS.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL skills/convert-md-to-dag/ROLLBACK_PLAN.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL skills/convert-md-to-dag/THREAT_MODEL.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL skills/convert-md-to-dag/TRACEABILITY.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

CLOSURE-ROOT VALIDATION FAILED: 8 error(s) across 8 file(s).
```

Exit code: 1.

File-line evidence that these are conforming DAG-TOML documents:

```text
VERIFICATION_REPORT.toml:14:[meta]
VERIFICATION_REPORT.toml:16:template_kind     = "contract-declaration"
paper/VERIFICATION_REPORT.toml:26:[meta]
paper/VERIFICATION_REPORT.toml:28:template_kind     = "contract-declaration"
skills/convert-md-to-dag/CONTRACT_DECLARATION.toml:3:[meta]
skills/convert-md-to-dag/CONTRACT_DECLARATION.toml:5:template_kind  = "contract-declaration"
skills/convert-md-to-dag/IMPLEMENTATION_DAG.toml:3:[meta]
skills/convert-md-to-dag/IMPLEMENTATION_DAG.toml:5:template_kind  = "implementation-dag"
skills/convert-md-to-dag/REVIEW_READINESS.toml:3:[meta]
skills/convert-md-to-dag/REVIEW_READINESS.toml:5:template_kind  = "readiness-gate"
skills/convert-md-to-dag/ROLLBACK_PLAN.toml:3:[meta]
skills/convert-md-to-dag/ROLLBACK_PLAN.toml:5:template_kind     = "rollback-plan"
skills/convert-md-to-dag/THREAT_MODEL.toml:3:[meta]
skills/convert-md-to-dag/THREAT_MODEL.toml:5:template_kind     = "threat-model"
skills/convert-md-to-dag/TRACEABILITY.toml:3:[meta]
skills/convert-md-to-dag/TRACEABILITY.toml:5:template_kind    = "traceability"
```

### Q2. TOML root-binding correctness

Verdict: confirmed.

Three patched files put `closure_root` before `[meta]`:

- `examples/minimal-implementation-dag.toml:4-7`:
```text
# Empty-closure sentinel — SHA-256("") — required by SPEC §12.1.
closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

[meta]
```

- `profiles/agent-assurance/tiers/solo.toml:6-9`:
```text
# Empty-closure sentinel — SHA-256("") — required by SPEC §12.1.
closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

[meta]
```

- `core/implementation-dag-kind.toml:8-11`:
```text
# Empty-closure sentinel — SHA-256("") — required by SPEC §12.1.
closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

[meta]
```

Command:

```bash
python3 - <<'PY'
import tomllib
for f in [
    'examples/minimal-implementation-dag.toml',
    'profiles/agent-assurance/tiers/solo.toml',
    'core/implementation-dag-kind.toml',
]:
    data = tomllib.loads(open(f, 'rb').read().decode())
    print(f)
    print('keys =', list(data.keys()))
    print('closure_root_top_level =', 'closure_root' in data)
    print('meta_has_closure_root =', isinstance(data.get('meta'), dict) and 'closure_root' in data['meta'])
PY
```

```text
examples/minimal-implementation-dag.toml
keys = ['closure_root', 'meta', 'units', 'computed']
closure_root_top_level = True
meta_has_closure_root = False
profiles/agent-assurance/tiers/solo.toml
keys = ['closure_root', 'meta', 'contracts']
closure_root_top_level = True
meta_has_closure_root = False
core/implementation-dag-kind.toml
keys = ['closure_root', 'meta', 'kind']
closure_root_top_level = True
meta_has_closure_root = False
```

Exit code: 0.

### Q3. Empty-closure sentinel correctness

Verdict: confirmed.

- `SPEC.md:901-905`:
```text
closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
...
This is the SHA-256 digest of zero bytes (`SHA-256("")`).
```

Command:

```bash
printf '' | sha256sum
```

```text
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  -
```

Exit code: 0.

### Q4. Forbidden-algorithm enforcement

Verdict: confirmed.

- `validators/validate_closure_root.py:46`:
```python
FORBIDDEN_ALGOS = ("md5", "sha1")
```

- `validators/validate_closure_root.py:90-95`:
```python
if algo in FORBIDDEN_ALGOS:
    errors.append(
        f"{path}: `closure_root` uses forbidden weak digest "
        f"algorithm `{algo}`. SPEC §12.1 forbids MD5 and SHA-1 — "
        f"use SHA-256 or stronger."
    )
```

Command:

```bash
tmp=$(mktemp); printf 'closure_root = "md5:abc"\n' > "$tmp"; python3 validators/validate_closure_root.py "$tmp"; code=$?; printf 'EXIT_CODE=%s\n' "$code"; rm -f "$tmp"; exit "$code"
```

```text
FAIL /tmp/tmp.L2VuYFsATV: `closure_root` uses forbidden weak digest algorithm `md5`. SPEC §12.1 forbids MD5 and SHA-1 — use SHA-256 or stronger.

CLOSURE-ROOT VALIDATION FAILED: 1 error(s) across 1 file(s).
EXIT_CODE=1
```

Exit code: 1.

### Q5. Ontology additions are well-typed

Verdict: confirmed.

- `core/ontology.toml:509-517`:
```text
[[relations]]
predicate    = "cites_upstream"
source       = ["unconstrained_label"]
targets      = ["unconstrained_label"]
cardinality  = "0..*"
inverse      = ""
notes        = "Cross-kind marker that a field in a `*-kind.toml` descriptor carries an upstream artifact reference (SHA-256 digest, document URI, signed-envelope pointer) that MUST flow into the document's root-level `closure_root` digest per SPEC §12.1. Kind descriptors apply this label via `[[kind.required_fields]].ontology_mapping = \"cites_upstream\"` (or the analogous mapping inside `[[kind.required_sections]]`). The relation is intentionally typed against `unconstrained_label` on both sides — concrete artifact entity kinds are profile-defined, but the closure-root rule fires uniformly across every conforming kind."
ijb_primitive = "path"
ijb_class     = "structural"
```

- `core/ontology.toml:624-631`:
```text
[[attribute_vocabularies]]
attribute   = "closure_root.digest_algorithm"
applies_to  = "document_root"
values      = ["sha256", "sha384", "sha512"]
extensible  = true
notes       = "Closed-for-now set of digest algorithms permitted as the prefix on a root-level `closure_root` field (SPEC §12.1). Extension is reserved for stronger / post-quantum digests as they become widely deployed; weaker algorithms (MD5, SHA-1) are forbidden by the spec text and MUST NOT be added. The closure-root rule is independent of the digest choice — only the algorithm tag in the field's value is bounded here."
ijb_primitive       = "constraint"
ijb_constraint_type = "structural"
```

Command:

```bash
python3 validators/validate_ijb_conformance.py core/ontology.toml
```

```text
IJB CONFORMANCE VALIDATION PASSED
- file: /srv/repos/external/verivus-oss/agent-assurance/core/ontology.toml
- template_kind: ontology
```

Exit code: 0.

### Q6. Cross-section back-reference accuracy

Verdict: confirmed.

F1 from Grok is fixed in the follow-up. Current §12.9 no longer says a provenance-only document may omit `closure_root`.

- `SPEC.md:272-275`:
```text
These three fields are **declared posture**, not upstream evidence.
Per §12.9, posture fields are deliberately NOT inputs to the
closure-root digest — they MAY change without flipping a downstream
`closure_root`.
```

- `SPEC.md:385-388`:
```text
The §5 cycle prohibition is extended in §12.9 to the **closure
graph** induced by `closure_root` inputs: a document MUST NOT,
directly or transitively, cite an upstream artifact whose own
closure depends on this document.
```

- `SPEC.md:788-791`:
```text
When the document also carries upstream evidence outside
`[provenance]` (kind-specific citation fields, evidence-matrix
entries), `source_sha256` is **one input** to the §12 closure-root
digest. It is not a substitute for `closure_root`.
```

- `SPEC.md:1066-1085`:
```text
- §2.7 (`confidentiality`, `license`, `embargo_until`) — posture
  fields are declared policy, **not** closure-root inputs. They
  change without breaking downstream hashes. This is intentional:
  posture is a policy declaration, not upstream evidence.
- §5 (Hard invariants) — the closure graph induced by
  `closure_root` inputs MUST be acyclic. A document MUST NOT,
  directly or transitively, cite an upstream artifact whose own
  closure depends on this document. Validators that walk closure
  inputs MUST detect and reject closure cycles; this extends the
  §5 cycle prohibition from intra-DAG `depends_on` to inter-document
  evidence citation.
- §11 (`[provenance]`) — `source_sha256` is one input to
  `closure_root` whenever a `[provenance]` table is present.
  `closure_root` itself remains MANDATORY at the document root per
  §12.1 regardless of whether `[provenance]` appears; a
  provenance-only document still emits `closure_root` (the canonical
  empty-closure sentinel if `[provenance].source_sha256` is its
  only upstream input and that input is itself the empty digest).
  `[provenance]` annotates origin, but never substitutes for
  `closure_root`.
```

The subsection targets are correct: §2.7 covers confidentiality/license/embargo posture, §5 covers hard invariants/cycles, §11 covers provenance, and §12.9 cross-links them accurately.

### Q7. Forbidden mechanisms list is closed and complete

Verdict: confirmed.

- `SPEC.md:1027-1039`:
```text
Implementers MUST NOT introduce mechanisms that paper over
closure-root changes. The following are forbidden:

- Re-signing a downstream document with a stale `closure_root` to
  preserve envelope validity through an upstream change.
- Storing `closure_root` in unsigned envelope attributes
  (`unsignedAttrs`, `unprotectedHeader`, or equivalent) where it is
  not covered by the signature.
- Defining "soft revocations" that update an upstream revocation list
  without flipping downstream closure-root values.
- Caching closure-root inputs across upstream versions (a
  "last-known-good" closure that survives an upstream change is the
  failure mode this section exists to prevent).
```

- `SPEC.md:1041-1044`:
```text
The brittleness is the feature. A downstream document whose signature
silently survives an upstream change is indistinguishable, to the
consumer, from a downstream document whose upstream was never
compromised.
```

The four listed mechanisms cover the obvious ways to preserve downstream validity despite upstream change: stale re-signing, unsigned placement, out-of-band revocation update, and stale input reuse. The broader sentence “MUST NOT introduce mechanisms that paper over closure-root changes” also prevents an implementer from treating the four bullets as the only forbidden spellings.

### Q8. Deferred canonical concatenation (§12.8)

Verdict: confirmed.

- `SPEC.md:1048-1058`:
```text
§12.1 specifies *what* `closure_root` is computed over (the closure of
upstream hashes plus the closure of revocation snapshots, both in
canonical sorted order). It does not pin the byte-level
canonical-concatenation algorithm (length-prefixing vs.
delimiter-separated, sort key collation, handling of duplicate
inputs). At `schema_version = "1.0.0"` the rule is specified at the
*property* level (cascade-break on any input change); runtimes that
interoperate MUST pin the algorithm out-of-band, and a future
`schema_version` bump MAY promote a specific algorithm
```

- `SPEC.md:1060-1062`:
```text
Profiles that pin the algorithm MUST do so in their
`profile-descriptor` document (per §6.1) so consumers can enumerate
it without reading code.
```

This is defensible only because §12.8 explicitly states the interop boundary: runtime pairs that interoperate must pin the byte algorithm out-of-band, and profiles that pin must declare it in the profile descriptor. It does leave non-interoperating or unpinned runtimes unable to recompute a common non-empty `closure_root`, but that gap is explicit rather than silent in the spec text.

### Q9. Disclosure-profile interaction (§12.9 last bullet)

Verdict: confirmed.

- `SPEC.md:1086-1096`:
```text
- Profiles — the disclosure profile (`profiles/disclosure/`)
  introduces a question this section must answer: when a producer
  publishes a redacted form of an artifact, does the redaction flip
  the upstream's `closure_root`? **No.** The unredacted artifact and
  its redacted disclosure are two distinct artifacts with two
  distinct SHA-256 values; the redacted form carries its own
  `closure_root` that cites the unredacted form as upstream. The
  unredacted artifact's `closure_root` is unaffected by the act of
  publishing a redaction. The closure-root rule fires on *changes
  to upstream evidence*, not on the production of a derived
  artifact.
```

- `profiles/disclosure/disclosure-attestation-kind.toml:30-35`:
```text
A disclosure attestation is the entry-point document for the
disclosure profile. It enumerates, per subject (a file path, a
field path, an assertion-bundle ID, …), the posture the publisher
took on that subject — `full`, `partial`, `withheld`, or
`embargoed` — and points the reviewer at the redaction-manifest and
selective-disclosure-proof artifacts (if any) that back the posture.
```

- `profiles/disclosure/selective-disclosure-proof-kind.toml:22-29`:
```text
A selective disclosure proof is the cryptographic commitment that
ties a redaction manifest to its source artifact. The SPEC layer
names the proof scheme and records the bound source hash; the wire
shape of the proof (Merkle path bytes, BBS+ signature, etc.) is
RUNTIME-SPEC. A recipient combining the proof, the redaction
manifest, and the published bytes can confirm that the published
bytes match the source modulo the listed redactions, without ever
seeing the redacted bytes themselves.
```

- `profiles/disclosure/selective-disclosure-proof-kind.toml:53-59`:
```text
- Each entry MUST carry `id` (matching the `SDP:` prefix), `subject`,
  `bound_source` (a `sha256:<hex>` digest of the source artifact the
  proof commits to), `proof_scheme` (drawn from the (extensible)
  `proof_scheme` vocabulary), and at least one of `covers` (list of
  `RED:` ids covered by the proof) or `proof_artifact` (a
  repo-relative path to the binary proof blob).
```

The profile semantics match §12.9: redaction artifacts and proofs are distinct artifacts bound to a source hash; they do not mutate the source artifact’s `closure_root`.

### Q10. Manifest-drift integrity

Verdict: confirmed.

- `reference/database/MANIFEST.toml:35-37`:
```text
relation_predicates    = 31    # one per [[relations]] block in core/ontology.toml (includes SPEC §12 `cites_upstream`)
attribute_vocabularies = 38    # 10 core + 24 agent-assurance + 4 disclosure (10th core = closure_root.digest_algorithm, SPEC §12.1)
attribute_values       = 84    # union across all closed-and-extensible-vocabulary allowed values
```

Command:

```bash
bash validators/check_manifest_drift.sh
```

```text
manifest-drift check (ontology vs reference/database/MANIFEST.toml)
  manifest                    ontology
  template_kinds           19 == 19
  entity_kinds             26 == 26
  relation_predicates      31 == 31
  attribute_vocabularies   38 == 38

rdf-drift check (schema.ttl footer vs ontology)
  schema.ttl                  ontology
  template_kinds           19 == 19
  entity_kinds             26 == 26
  relation_predicates      31 == 31
  attribute_vocabularies   38 == 38

OK — manifest matches ontology
```

Exit code: 0.

4. INDEPENDENT FINDINGS

**F1 — high — tracked conforming DAG-TOML documents remain invalid under the new universal rule.**

File-line evidence:

```text
VERIFICATION_REPORT.toml:14:[meta]
VERIFICATION_REPORT.toml:16:template_kind     = "contract-declaration"
paper/VERIFICATION_REPORT.toml:26:[meta]
paper/VERIFICATION_REPORT.toml:28:template_kind     = "contract-declaration"
skills/convert-md-to-dag/CONTRACT_DECLARATION.toml:3:[meta]
skills/convert-md-to-dag/CONTRACT_DECLARATION.toml:5:template_kind  = "contract-declaration"
skills/convert-md-to-dag/IMPLEMENTATION_DAG.toml:3:[meta]
skills/convert-md-to-dag/IMPLEMENTATION_DAG.toml:5:template_kind  = "implementation-dag"
skills/convert-md-to-dag/REVIEW_READINESS.toml:3:[meta]
skills/convert-md-to-dag/REVIEW_READINESS.toml:5:template_kind  = "readiness-gate"
skills/convert-md-to-dag/ROLLBACK_PLAN.toml:3:[meta]
skills/convert-md-to-dag/ROLLBACK_PLAN.toml:5:template_kind     = "rollback-plan"
skills/convert-md-to-dag/THREAT_MODEL.toml:3:[meta]
skills/convert-md-to-dag/THREAT_MODEL.toml:5:template_kind     = "threat-model"
skills/convert-md-to-dag/TRACEABILITY.toml:3:[meta]
skills/convert-md-to-dag/TRACEABILITY.toml:5:template_kind    = "traceability"
```

Problem: These are tracked conforming DAG-TOML documents by the validator’s own discovery convention, but they lack root-level `closure_root`. The focused validator run fails with 8 errors. This contradicts `SPEC.md:866` (“Every conforming DAG-TOML document MUST carry a `closure_root` field”) and `validators/validate_closure_root.py:117-131`, which defines conforming discovery as `[meta].template_kind`.

Suggested fix: add the root-level sentinel before `[meta]` in all tracked conforming DAG-TOML files, or narrow the normative rule to “canonical examples/profile/core surfaces” if that is the intended scope. The latter would require changing §12.1.

**F2 — high — CI discovery still does not gate every tracked conforming DAG-TOML document.**

- `.github/workflows/validate.yml:154-168`:
```text
- name: Validate closure_root (SPEC §12) on every conforming DAG-TOML document
...
run: |
  set -e
  python3 validators/validate_closure_root.py \
    --discover core profiles examples
```

Problem: The step name says “every conforming DAG-TOML document,” but the command only discovers under `core`, `profiles`, and `examples`. The failing tracked conforming documents in `VERIFICATION_REPORT.toml`, `paper/`, and `skills/convert-md-to-dag/` are outside that scope and therefore not gated. This means Grok’s original hardcoded-list gap is improved for the named canonical surfaces, but a universal-rule CI gap remains.

Suggested fix: either run `--discover` over all tracked repository paths while excluding non-DAG TOML by `[meta].template_kind`, or explicitly include all tracked conforming DAG-TOML roots.

**F3 — medium — migration guidance is absent despite a validator-tightening rule.**

- `README.md:42-44`:
```text
Backwards-incompatible changes require a schema major-version bump and a
migration note. Additive changes use the minor version path described in
[SPEC.md](SPEC.md#8-versioning-policy).
```

- `SPEC.md:486-488`:
```text
- Removing fields, changing field semantics, or tightening validation is
  a **major** bump and ships with a migration note.
```

Problem: §12 tightens validation by making a new root field mandatory, but the inspected `SPEC.md`, `CHANGELOG.md`, and `README.md` do not include a migration note for existing producers or existing tracked DAG-TOML documents. The absence is visible in the remaining invalid tracked files.

Suggested fix: add a migration note in `CHANGELOG.md` or `SPEC.md` stating that existing conforming documents must add `closure_root` before the first `[table]`, and use the empty-closure sentinel only when they truly have no closure inputs.

5. TERMINAL VERDICT

CONCRETE UNRESOLVABLE BLOCKERS:

1. The universal §12 rule is not actually satisfied by the repository at HEAD. `SPEC.md:866` says “Every conforming DAG-TOML document MUST carry a `closure_root` field,” and `validators/validate_closure_root.py:117-131` treats any TOML with `[meta].template_kind` as conforming for discovery. Eight tracked conforming DAG-TOML documents lack `closure_root` and fail `python3 validators/validate_closure_root.py --discover VERIFICATION_REPORT.toml paper skills/convert-md-to-dag` with exit code 1. Unblock by adding root-level `closure_root` before `[meta]` in those tracked conforming files, or by changing the normative scope of §12.1.

2. The CI step claims to validate “every conforming DAG-TOML document” but only runs `--discover core profiles examples` at `.github/workflows/validate.yml:154-168`. That command misses the eight tracked conforming invalid files shown above. Unblock by broadening CI discovery to all tracked conforming DAG-TOML documents, or by making the workflow label and spec scope match a narrower canonical-only rule.
