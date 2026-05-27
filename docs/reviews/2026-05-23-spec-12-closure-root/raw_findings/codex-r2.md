1. SESSION META

- Reviewer model name and version: Codex, based on GPT-5.
- Sandbox / approval posture: `danger-full-access`; network enabled; approval policy `never`; no approvals requested.
- MCP servers available/used: `sqry` MCP was available. I used `mcp__sqry__.get_index_status` and `mcp__sqry__.semantic_search` before literal inspection; the current sqry index returned no validator-symbol hits, so I followed with `rg`, `nl`, `git show`, and executed validators.
- Worktree posture: live worktree is dirty and contains untracked TOML files, so I separately tested a clean `HEAD` archive for commit-sensitive `--discover .` behavior.
- Re-derived HEAD:

```bash
git rev-parse HEAD
```

```text
5c145c8af372fc73bae972d3b731b8b79a25c059
```

2. PROCESS CONFIRMATIONS

**Migration guidance** — refuted.

Evidence that the repo policy requires a migration note:

- `README.md:42-44`:
```text
Backwards-incompatible changes require a schema major-version bump and a
migration note. Additive changes use the minor version path described in
[SPEC.md](SPEC.md#8-versioning-policy).
```

- `SPEC.md:487-488`:
```text
- Removing fields, changing field semantics, or tightening validation is
  a **major** bump and ships with a migration note.
```

Evidence that §12 tightens validation:

- `SPEC.md:866-875`:
```text
Every conforming DAG-TOML document MUST carry a `closure_root` field
whose value is a cryptographic digest over the canonical
concatenation of:

A document is **conforming** for the purposes of this section if and
only if its `[meta].template_kind` is one of:

- a kind declared by `core/*-kind.toml` (see §3 for the closed list);
- a kind declared by a blessed profile's `profiles/<name>/*-kind.toml`;
- one of the meta kinds `kind-descriptor` or `ontology`.
```

`CHANGELOG.md:12-24` explains the new rule, but I found no producer migration note. The relevant changelog text says what changed, not how existing producers should migrate:

```text
Every conforming DAG-TOML document MUST
carry a root-level `closure_root` field of the form
`<sha256|sha384|sha512>:<lowercase-hex>` ...
```

**No retconning** — confirmed.

The cumulative diff adds review records under `docs/reviews/`, but I found no `docs/research/` historical artifact modifications in the reviewed range.

```bash
git diff --stat 638a90e..HEAD -- docs/research docs/reviews tools/review-request-dag.toml
```

```text
 .../raw_findings/codex.md                          | 673 +++++++++++++++++++++
 .../raw_findings/grok.md                           | 191 ++++++
 .../review_bundle.toml                             |  56 ++
 .../review_prompt.md                               | 266 ++++++++
 4 files changed, 1186 insertions(+)
docs/reviews/2026-05-23-spec-12-closure-root/raw_findings/codex.md
docs/reviews/2026-05-23-spec-12-closure-root/raw_findings/grok.md
docs/reviews/2026-05-23-spec-12-closure-root/review_bundle.toml
docs/reviews/2026-05-23-spec-12-closure-root/review_prompt.md
```

Exit code: 0.

**Tests run with output** — confirmed run; closure-root broad discovery is failing.

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
python3 validators/validate_closure_root.py examples/minimal-*.toml examples/minimal-review-readiness/*.toml profiles/agent-assurance/tiers/*.toml core/*-kind.toml core/ontology.toml profiles/agent-assurance/*-kind.toml profiles/agent-assurance/PROFILE.toml profiles/agent-assurance/ontology.toml profiles/disclosure/*-kind.toml profiles/disclosure/PROFILE.toml profiles/disclosure/ontology.toml
```

```text
CLOSURE-ROOT VALIDATION PASSED (45 file(s)).
```

Exit code: 0.

Live dirty worktree run requested by dispatch:

```bash
python3 validators/validate_closure_root.py --discover .
```

```text
FAIL arxiv-prep-agent-dag.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL claim-analysis-agent-gated-dag.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL tools/claim-analysis-document-review-dag.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL tools/review-request-dag.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL tools/werner-style-policy.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

CLOSURE-ROOT VALIDATION FAILED: 5 error(s) across 70 file(s).
```

Exit code: 1. Those five files are untracked in this worktree, so I also ran the same validator against a clean archive of committed `HEAD`:

```bash
tmp=$(mktemp -d); git archive HEAD | tar -x -C "$tmp"; cd "$tmp" && python3 validators/validate_closure_root.py --discover .
```

```text
FAIL examples/proof-hello-world/CONTRACT_DECLARATION.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL examples/proof-hello-world/EVIDENCE_MATRIX.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL examples/proof-hello-world/IMPLEMENTATION_DAG.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL examples/proof-hello-world/REVIEW_READINESS.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL examples/proof-hello-world/TRACEABILITY.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

CLOSURE-ROOT VALIDATION FAILED: 5 error(s) across 65 file(s).
```

Exit code: 1.

3. ANSWERS TO THE 10 SUBSTANTIVE QUESTIONS + PRIOR-FINDING STATUS

### Q1. Universal-requirement consistency

Verdict: refuted_with_evidence.

The spec and validator define a universal blessed-kind requirement:

- `SPEC.md:866-875`:
```text
Every conforming DAG-TOML document MUST carry a `closure_root` field
...
A document is **conforming** for the purposes of this section if and
only if its `[meta].template_kind` is one of:
...
- one of the meta kinds `kind-descriptor` or `ontology`.
```

- `validators/validate_closure_root.py:168-185`:
```text
def is_conforming_toml(path: pathlib.Path, blessed: frozenset[str]) -> bool:
    """A conforming DAG-TOML document declares a blessed
    `[meta].template_kind`.
...
    tk = meta.get("template_kind")
    return isinstance(tk, str) and tk in blessed
```

Clean committed `HEAD` still has five conforming files that fail:

- `examples/proof-hello-world/CONTRACT_DECLARATION.toml` at HEAD `11-13`:
```text
[meta]
schema_version  = "1.0.0"
template_kind   = "contract-declaration"
```

- `examples/proof-hello-world/EVIDENCE_MATRIX.toml` at HEAD `10-12`:
```text
[meta]
schema_version  = "1.0.0"
template_kind   = "evidence-matrix"
```

- `examples/proof-hello-world/IMPLEMENTATION_DAG.toml` at HEAD `11-13`:
```text
[meta]
schema_version  = "1.0.0"
template_kind   = "implementation-dag"
```

- `examples/proof-hello-world/REVIEW_READINESS.toml` at HEAD `7-9`:
```text
[meta]
schema_version  = "1.0.0"
template_kind   = "readiness-gate"
```

- `examples/proof-hello-world/TRACEABILITY.toml` at HEAD `19-21`:
```text
[meta]
schema_version   = "1.0.0"
template_kind    = "traceability"
```

Command summary:

```text
clean_head_conforming_count = 65
clean_head_missing_closure_root_count = 5
examples/proof-hello-world/CONTRACT_DECLARATION.toml
examples/proof-hello-world/EVIDENCE_MATRIX.toml
examples/proof-hello-world/IMPLEMENTATION_DAG.toml
examples/proof-hello-world/REVIEW_READINESS.toml
examples/proof-hello-world/TRACEABILITY.toml
```

Exit code: 0 for the inventory script; exit code 1 for `validate_closure_root.py --discover .` on clean `HEAD`.

### Q2. TOML root-binding correctness

Verdict: confirmed for inspected patched files.

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
for f in ['examples/minimal-implementation-dag.toml','profiles/agent-assurance/tiers/solo.toml','core/implementation-dag-kind.toml']:
    data=tomllib.loads(open(f,'rb').read().decode())
    print(f, sorted(data.keys())[:8], 'closure_root_top_level=', 'closure_root' in data)
PY
```

```text
examples/minimal-implementation-dag.toml ['closure_root', 'computed', 'meta', 'units'] closure_root_top_level= True
profiles/agent-assurance/tiers/solo.toml ['closure_root', 'contracts', 'meta'] closure_root_top_level= True
core/implementation-dag-kind.toml ['closure_root', 'kind', 'meta'] closure_root_top_level= True
```

Exit code: 0.

### Q3. Empty-closure sentinel correctness

Verdict: confirmed.

- `SPEC.md:921-925`:
```text
closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
```

```text
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
```text
FORBIDDEN_ALGOS = ("md5", "sha1")
```

- `validators/validate_closure_root.py:90-95`:
```text
if algo in FORBIDDEN_ALGOS:
    errors.append(
        f"{path}: `closure_root` uses forbidden weak digest "
        f"algorithm `{algo}`. SPEC §12.1 forbids MD5 and SHA-1 — "
        f"use SHA-256 or stronger."
    )
```

Command:

```bash
tmp=$(mktemp); printf 'closure_root = "md5:abc"\n' > "$tmp"; python3 validators/validate_closure_root.py "$tmp"
```

```text
FAIL /tmp/tmp.dihv0Y9UAi: `closure_root` uses forbidden weak digest algorithm `md5`. SPEC §12.1 forbids MD5 and SHA-1 — use SHA-256 or stronger.

CLOSURE-ROOT VALIDATION FAILED: 1 error(s) across 1 file(s).
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
...
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
...
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

- `SPEC.md:1097-1105`:
```text
- §11 (`[provenance]`) — `source_sha256` is one input to
  `closure_root` whenever a `[provenance]` table is present.
  `closure_root` itself remains MANDATORY at the document root per
  §12.1 regardless of whether `[provenance]` appears; a
  provenance-only document still emits `closure_root` ...
  `[provenance]` annotates origin, but never substitutes for
  `closure_root`.
```

The cited targets exist and match the references: §2.7 is posture metadata, §5 is hard invariants/cycles, §11 is provenance, and §12.9 ties them together.

### Q7. Forbidden mechanisms list is closed and complete

Verdict: confirmed.

- `SPEC.md:1047-1059`:
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

The four named mechanisms cover stale re-signing, unsigned placement, out-of-band revocation masking, and stale input reuse. The lead sentence is broad enough to block equivalent papering-over mechanisms under different names.

### Q8. Deferred canonical concatenation (§12.8)

Verdict: confirmed.

- `SPEC.md:1068-1078`:
```text
§12.1 specifies *what* `closure_root` is computed over (the closure of
upstream hashes plus the closure of revocation snapshots, both in
canonical sorted order). It does not pin the byte-level
canonical-concatenation algorithm ...
At `schema_version = "1.0.0"` the rule is specified at the
*property* level (cascade-break on any input change); runtimes that
interoperate MUST pin the algorithm out-of-band ...
```

- `SPEC.md:1080-1082`:
```text
Profiles that pin the algorithm MUST do so in their
`profile-descriptor` document (per §6.1) so consumers can enumerate
it without reading code.
```

This is defensible as a property-level v1 rule. It does mean two uncoordinated runtimes cannot safely recompute the same non-empty root, but the text makes interop conditional on an out-of-band/profile-pinned algorithm rather than silently promising global byte-level interoperability.

### Q9. Disclosure-profile interaction (§12.9 last bullet)

Verdict: confirmed.

- `SPEC.md:1106-1116`:
```text
- Profiles — the disclosure profile (`profiles/disclosure/`)
  introduces a question this section must answer: when a producer
  publishes a redacted form of an artifact, does the redaction flip
  the upstream's `closure_root`? **No.** The unredacted artifact and
  its redacted disclosure are two distinct artifacts with two
  distinct SHA-256 values; the redacted form carries its own
  `closure_root` that cites the unredacted form as upstream. The
  unredacted artifact's `closure_root` is unaffected by the act of
  publishing a redaction.
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

- `profiles/disclosure/disclosure-attestation-kind.toml:64-67`:
```text
- When `disclosure_posture = "partial"`, the entry MUST link to at
  least one `RED:` redaction-manifest entry via `covered_by`.
- When `disclosure_posture = "embargoed"`, the file's
  `[meta].embargo_until` MUST be set per SPEC §2.7.
```

The disclosure kind describes posture and links to redaction/proof artifacts; it does not imply mutating the upstream artifact’s own closure root.

### Q10. Manifest-drift integrity

Verdict: confirmed.

- `reference/database/MANIFEST.toml:32-37`:
```text
[counts]
template_kinds         = 19    # 6 core + 9 agent-assurance + 3 disclosure + 1 meta `kind-descriptor`
entity_kinds           = 26    # 17 core + 6 agent-assurance + 3 disclosure
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

### Prior-finding status

- F1 — partially_resolved. The eight specific prior files are fixed at `HEAD`; examples include `VERIFICATION_REPORT.toml:14-17`, `paper/VERIFICATION_REPORT.toml:26-29`, and `skills/convert-md-to-dag/CONTRACT_DECLARATION.toml:3-6`, each now carrying root-level `closure_root` before `[meta]`. However the class of defect remains: clean committed `HEAD` still fails `validate_closure_root.py --discover .` on five conforming `examples/proof-hello-world/*.toml` files, with `[meta].template_kind` at `CONTRACT_DECLARATION.toml:11-13`, `EVIDENCE_MATRIX.toml:10-12`, `IMPLEMENTATION_DAG.toml:11-13`, `REVIEW_READINESS.toml:7-9`, and `TRACEABILITY.toml:19-21`.
- F2 — resolved. Prior CI used a narrowed discovery root; current `.github/workflows/validate.yml:168-175` says:
```text
# We walk the whole repo (--discover .) so a new tracked
# conforming document under any directory — paper/, skills/,
# tools/, examples/, profiles/, core/, anywhere — is caught
# automatically.
run: |
  set -e
  python3 validators/validate_closure_root.py \
    --discover .
```
This resolves the prior CI coverage gap. It now catches the remaining proof-example failures.
- F3 — not_resolved. Migration guidance is still absent. `README.md:42-44` and `SPEC.md:487-488` require a migration note for backwards-incompatible/tightened validation changes, while `CHANGELOG.md:12-24` and `CHANGELOG.md:53-64` describe the new rule and canonical-example sentinel application without producer migration steps.

4. INDEPENDENT FINDINGS

- F4 — high — committed `HEAD` still contains five conforming DAG-TOML documents without `closure_root`. Clean `HEAD` archive `python3 validators/validate_closure_root.py --discover .` exits 1 and reports the five `examples/proof-hello-world/*.toml` failures. These files use blessed template kinds shown at `CONTRACT_DECLARATION.toml:11-13`, `EVIDENCE_MATRIX.toml:10-12`, `IMPLEMENTATION_DAG.toml:11-13`, `REVIEW_READINESS.toml:7-9`, and `TRACEABILITY.toml:19-21`.
- F5 — medium — migration guidance remains missing despite the repo’s own versioning policy. `SPEC.md:487-488` says tightening validation is a major bump with a migration note; §12’s universal required field at `SPEC.md:866-875` is such a tightening, and no inspected `SPEC.md` / `CHANGELOG.md` / `README.md` text gives existing producers a migration procedure.

5. TERMINAL VERDICT

CONCRETE UNRESOLVABLE BLOCKERS:

1. Clean committed `HEAD` does not satisfy SPEC §12’s universal closure-root rule. `SPEC.md:866-875` requires `closure_root` on every conforming DAG-TOML document, and `validators/validate_closure_root.py:168-185` defines conforming discovery by blessed `[meta].template_kind`. A clean archive of `5c145c8af372fc73bae972d3b731b8b79a25c059` fails `python3 validators/validate_closure_root.py --discover .` with five missing-root errors in `examples/proof-hello-world/CONTRACT_DECLARATION.toml`, `EVIDENCE_MATRIX.toml`, `IMPLEMENTATION_DAG.toml`, `REVIEW_READINESS.toml`, and `TRACEABILITY.toml`.

2. The required migration guidance remains absent. `README.md:42-44` and `SPEC.md:487-488` require a migration note for backwards-incompatible validation tightening, while §12 now makes a root-level field mandatory for every conforming document. The inspected changelog explains the new rule but does not tell existing producers how to migrate existing documents or distinguish empty-closure sentinel use from non-empty closure computation.
