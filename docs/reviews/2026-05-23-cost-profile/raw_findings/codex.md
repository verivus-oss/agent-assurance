## 1. SESSION META

- Reviewer model: GPT-5 Codex.
- Sandbox / approval posture: `danger-full-access`, network enabled, approval policy `never`.
- MCP servers available/used: `mcp__sqry__` was available. Initial index was stale; I ran `sqry index --force .`, then `mcp__sqry__.semantic_search` found `validators/validate_cost.py`.
- Re-derived HEAD:
```text
$ git rev-parse HEAD
fccc1dcf8ebc796eaeee395d73126256fd94d869
```

## 2. PROCESS CONFIRMATIONS

### Migration guidance

Verdict: `refuted`.

Evidence that the profile itself tells adopters how to opt in:

- `profiles/cost/PROFILE.toml:3: # The cost profile sits next to agent-assurance and disclosure as a`
- `profiles/cost/PROFILE.toml:4: # peer, not inside agent-assurance: a repo may adopt cost on its own,`
- `profiles/cost/PROFILE.toml:54: extends           = []`
- `profiles/cost/PROFILE.toml:56: contained_kinds   = [`
- `profiles/cost/cost-record-kind.toml:44:     template_kind     = "cost-record"`
- `profiles/cost/cost-record-kind.toml:45:     framework_profile = "cost"`

Evidence that the CHANGELOG describes scope but does not state the opt-in field `framework_profile = "cost"`:

- `CHANGELOG.md:12: - **Cost profile (Stream G — Cost-Witnessed Decision).** New blessed`
- `CHANGELOG.md:13:   profile under `profiles/cost/` with a single kind, `cost-record`,`
- `CHANGELOG.md:43:   predicates / 41 attribute vocabularies. CI gates the cost profile`
- `CHANGELOG.md:44:   alongside agent-assurance and disclosure.`

### No retconning

Verdict: `confirmed`.

Changed-file evidence from the reviewed commit:

```text
$ git diff --name-only 953b887..fccc1dc
.github/workflows/validate.yml
CHANGELOG.md
examples/minimal-cost-record.toml
profiles/cost/PROFILE.toml
profiles/cost/cost-record-kind.toml
profiles/cost/ontology.toml
reference/database/MANIFEST.toml
reference/database/duckdb/seed.sql
reference/database/postgres/seed.sql
reference/database/rdf/schema.ttl
reference/database/sqlite/seed.sql
validators/validate_cost.py
```

No historical dated SPEC/proposal file is modified in that diff. The proposal is referenced, not rewritten:

- `profiles/cost/cost-record-kind.toml:121:   "docs/research/2026-05-22-spec-foundations-research/follow-up-2/13-stream-G-cost-witnessed-decision.md",`

### Tests Run With Output

Verdict: `refuted` for the dirty repo path required by the prompt; `confirmed` for the clean detached worktree at the reviewed commit.

Required command in current repo path failed because unrelated untracked TOMLs in the working tree are discovered:

```text
$ python3 validators/validate_closure_root.py --discover .
FAIL arxiv-prep-agent-dag.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL claim-analysis-agent-gated-dag.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL tools/claim-analysis-document-review-dag.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL tools/review-request-dag.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL tools/werner-style-policy.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

CLOSURE-ROOT VALIDATION FAILED: 5 error(s) across 74 file(s).
```

Exit code: `1`.

Same command on clean detached worktree at `fccc1dcf8ebc796eaeee395d73126256fd94d869`:

```text
$ python3 validators/validate_closure_root.py --discover .
CLOSURE-ROOT VALIDATION PASSED (69 file(s)).
EXIT:0
```

Other required commands in the repo path:

```text
$ bash validators/check_manifest_drift.sh
manifest-drift check (ontology vs reference/database/MANIFEST.toml)
  manifest                    ontology
  template_kinds           20 == 20
  entity_kinds             27 == 27
  relation_predicates      31 == 31
  attribute_vocabularies   41 == 41

rdf-drift check (schema.ttl footer vs ontology)
  schema.ttl                  ontology
  template_kinds           20 == 20
  entity_kinds             27 == 27
  relation_predicates      31 == 31
  attribute_vocabularies   41 == 41

OK — manifest matches ontology
```

Exit code: `0`.

```text
$ python3 validators/validate_cost.py --repo-root . examples/minimal-cost-record.toml
COST-RECORD VALIDATION PASSED (1 file(s)).
```

Exit code: `0`.

```text
$ python3 validators/validate_ijb_conformance.py profiles/cost/ontology.toml
IJB CONFORMANCE VALIDATION PASSED
- file: /srv/repos/external/verivus-oss/agent-assurance/profiles/cost/ontology.toml
- template_kind: ontology
- framework_profile: cost
```

Exit code: `0`.

```text
$ python3 validators/validate_ijb_conformance.py profiles/cost/cost-record-kind.toml
IJB CONFORMANCE VALIDATION PASSED
- file: /srv/repos/external/verivus-oss/agent-assurance/profiles/cost/cost-record-kind.toml
- template_kind: kind-descriptor
```

Exit code: `0`.

```text
$ python3 validators/validate_kind_descriptor.py profiles/cost/cost-record-kind.toml --repo-root . --check-references-exist
KIND DESCRIPTOR VALIDATION PASSED
- file: /srv/repos/external/verivus-oss/agent-assurance/profiles/cost/cost-record-kind.toml
- describes_kind: cost-record
- example_count: 1
- invariant_count: 7
```

Exit code: `0`.

```text
$ python3 validators/validate_profile_descriptor.py --repo-root . profiles/cost/PROFILE.toml
PROFILE DESCRIPTOR VALIDATION PASSED
- files validated: 1
- profiles in resolution set: 3
```

Exit code: `0`.

## 3. ANSWERS TO THE 10 SUBSTANTIVE QUESTIONS

### Q1. Closed-vocabulary completeness

Verdict: `confirmed`.

Evidence:

- `profiles/cost/ontology.toml:57: [[attribute_vocabularies]]`
- `profiles/cost/ontology.toml:58: attribute   = "cost_dimension_category"`
- `profiles/cost/ontology.toml:61:   "token_equivalent",`
- `profiles/cost/ontology.toml:67:   "evidence_run_count",`
- `profiles/cost/ontology.toml:71: ijb_primitive       = "constraint"`
- `profiles/cost/ontology.toml:72: ijb_constraint_type = "structural"`
- `profiles/cost/ontology.toml:74: [[attribute_vocabularies]]`
- `profiles/cost/ontology.toml:75: attribute   = "decider_class"`
- `profiles/cost/ontology.toml:78:   "deterministic_check",`
- `profiles/cost/ontology.toml:85:   "other",`
- `profiles/cost/ontology.toml:89: ijb_primitive       = "constraint"`
- `profiles/cost/ontology.toml:90: ijb_constraint_type = "structural"`
- `profiles/cost/ontology.toml:92: [[attribute_vocabularies]]`
- `profiles/cost/ontology.toml:93: attribute   = "cost_citing_kind"`
- `profiles/cost/ontology.toml:96:   "gate-decision",`
- `profiles/cost/ontology.toml:102:   "other",`
- `profiles/cost/ontology.toml:106: ijb_primitive       = "constraint"`
- `profiles/cost/ontology.toml:107: ijb_constraint_type = "structural"`

### Q2. Validator enforces every declared invariant

Verdict: `refuted_with_evidence`.

`validators/validate_cost.py` enforces INV01–INV06, but not INV07. INV07 is declared as enforced by the IJB validator:

- `profiles/cost/cost-record-kind.toml:249: [[kind.hard_invariants]]`
- `profiles/cost/cost-record-kind.toml:250: id          = "INV07"`
- `profiles/cost/cost-record-kind.toml:251: statement   = "Every entity prefix and relation predicate used in this kind's instance files resolves to an `ijb_primitive` declared in the loaded ontology set (core + cost profile)."`
- `profiles/cost/cost-record-kind.toml:252: enforced_by = "validators/validate_ijb_conformance.py"`
- `validators/validate_cost.py:7:   INV01 — `[record].decider_class` is in the closed `decider_class``
- `validators/validate_cost.py:16:   INV06 — `[record].hash_algorithm` is `sha256` / `sha384` / `sha512``
- `validators/validate_cost.py:20: Closure-root presence is enforced separately by`
- `validators/validate_cost.py:21: `validators/validate_closure_root.py`; this validator does not`
- `validators/validate_cost.py:22: duplicate that check.`

Negative test results:

```text
$ python3 validators/validate_cost.py --repo-root . /tmp/aa-cost-neg-tests.Kej0GO/INV01.toml
FAIL /tmp/aa-cost-neg-tests.Kej0GO/INV01.toml: record.decider_class 'llm_bogus' not in closed vocabulary decider_class=['deterministic_check', 'human_reviewer', 'llm_consensus', 'llm_single', 'notarisation', 'other', 'tee_attested_compute', 'transparency_log_write']

COST-RECORD VALIDATION FAILED: 1 error(s) across 1 file(s).
EXIT:1

$ python3 validators/validate_cost.py --repo-root . /tmp/aa-cost-neg-tests.Kej0GO/INV02.toml
FAIL /tmp/aa-cost-neg-tests.Kej0GO/INV02.toml: record.citing_kind 'unknown-kind' not in closed vocabulary cost_citing_kind=['assertion-bundle', 'evidence-matrix', 'gate-decision', 'other', 'rollback-plan', 'smoke-validation', 'threat-model']

COST-RECORD VALIDATION FAILED: 1 error(s) across 1 file(s).
EXIT:1

$ python3 validators/validate_cost.py --repo-root . /tmp/aa-cost-neg-tests.Kej0GO/INV03.toml
FAIL /tmp/aa-cost-neg-tests.Kej0GO/INV03.toml: record.dimensions[0].category 'currency_usd' not in closed vocabulary cost_dimension_category=['bandwidth_bytes', 'compute_time_seconds', 'energy_equivalent', 'evidence_run_count', 'human_review_time_seconds', 'storage_bytes', 'token_equivalent']

COST-RECORD VALIDATION FAILED: 1 error(s) across 1 file(s).
EXIT:1

$ python3 validators/validate_cost.py --repo-root . /tmp/aa-cost-neg-tests.Kej0GO/INV04.toml
FAIL /tmp/aa-cost-neg-tests.Kej0GO/INV04.toml: record.dimensions[0].quantity must be a non-negative integer (no floats per canonical-form determinism); got float 1.5

COST-RECORD VALIDATION FAILED: 1 error(s) across 1 file(s).
EXIT:1

$ python3 validators/validate_cost.py --repo-root . /tmp/aa-cost-neg-tests.Kej0GO/INV05.toml
FAIL /tmp/aa-cost-neg-tests.Kej0GO/INV05.toml: record.incurred_at must be RFC 3339 date-time, got '2026-05-22 14:32:11'

COST-RECORD VALIDATION FAILED: 1 error(s) across 1 file(s).
EXIT:1

$ python3 validators/validate_cost.py --repo-root . /tmp/aa-cost-neg-tests.Kej0GO/INV06.toml
FAIL /tmp/aa-cost-neg-tests.Kej0GO/INV06.toml: record.hash_algorithm 'md5' is forbidden by SPEC §12.1 (no MD5 or SHA-1); use SHA-256 or stronger.

COST-RECORD VALIDATION FAILED: 1 error(s) across 1 file(s).
EXIT:1

$ python3 validators/validate_ijb_conformance.py /tmp/aa-cost-neg-tests.Kej0GO/INV07.toml --repo-root . --check-references-exist
IJB CONFORMANCE VALIDATION FAILED
- file: /tmp/aa-cost-neg-tests.Kej0GO/INV07.toml
- bogus.id: entity prefix `NOPE` in `NOPE:1` does not resolve to a declared `[[entities]].id_prefix` in the loaded ontologies
EXIT:1

$ python3 validators/validate_cost.py --repo-root . /tmp/aa-cost-neg-tests.Kej0GO/INV07.toml
COST-RECORD VALIDATION PASSED (1 file(s)).
EXIT:0
```

### Q3. Float quantities rejected

Verdict: `confirmed`.

Evidence:

- `profiles/cost/cost-record-kind.toml:87:   - `quantity` (non-negative integer; floats are forbidden per`
- `validators/validate_cost.py:177:             # INV04 — non-negative integer; floats forbidden.`
- `validators/validate_cost.py:180:                     f"{path}: record.dimensions[{i}].quantity must be a "`
- `validators/validate_cost.py:181:                     f"non-negative integer (no floats per canonical-form "`

Command output:

```text
$ python3 validators/validate_cost.py --repo-root . /tmp/aa-cost-neg-tests.Kej0GO/INV04.toml
FAIL /tmp/aa-cost-neg-tests.Kej0GO/INV04.toml: record.dimensions[0].quantity must be a non-negative integer (no floats per canonical-form determinism); got float 1.5

COST-RECORD VALIDATION FAILED: 1 error(s) across 1 file(s).
EXIT:1
```

### Q4. MD5/SHA-1 hash_algorithm rejected

Verdict: `confirmed`.

Evidence:

- `profiles/cost/cost-record-kind.toml:243: statement   = "`[record].hash_algorithm` is one of `sha256`, `sha384`, `sha512`, or a stronger algorithm name. Weaker digests (`md5`, `sha1`) are forbidden per SPEC §12.1."`
- `validators/validate_cost.py:47: FORBIDDEN_HASH_ALGOS = frozenset({"md5", "sha1"})`
- `validators/validate_cost.py:150:         if ha_l in FORBIDDEN_HASH_ALGOS:`

Command output:

```text
$ python3 validators/validate_cost.py --repo-root . /tmp/aa-cost-neg-tests.Kej0GO/INV06.toml
FAIL /tmp/aa-cost-neg-tests.Kej0GO/INV06.toml: record.hash_algorithm 'md5' is forbidden by SPEC §12.1 (no MD5 or SHA-1); use SHA-256 or stronger.

COST-RECORD VALIDATION FAILED: 1 error(s) across 1 file(s).
EXIT:1
```

### Q5. Closure-root requirement is enforced on the cost example

Verdict: `confirmed` for the reviewed commit; dirty working tree command failed for unrelated untracked TOMLs.

Evidence:

- `examples/minimal-cost-record.toml:7: # Empty-closure sentinel — SHA-256("") — required by SPEC §12.1.`
- `examples/minimal-cost-record.toml:8: closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"`
- `validators/validate_closure_root.py:145:         for descriptor in profiles_dir.glob("*/*-kind.toml"):`
- `validators/validate_closure_root.py:148:                 found.add(name)`

Clean reviewed commit output:

```text
$ python3 validators/validate_closure_root.py --discover .
CLOSURE-ROOT VALIDATION PASSED (69 file(s)).
EXIT:0
```

Discovery confirmation from the same clean worktree:

```text
$ python3 - <<'PY'
...
examples/minimal-cost-record.toml
discovered_count 69
```

Direct cost-example validation in dirty repo path:

```text
$ python3 validators/validate_closure_root.py examples/minimal-cost-record.toml
CLOSURE-ROOT VALIDATION PASSED (1 file(s)).
```

Exit code: `0`.

### Q6. Manifest counts match ontology reality

Verdict: `refuted_with_evidence`.

Evidence of MANIFEST claim:

- `reference/database/MANIFEST.toml:33: template_kinds         = 20    # 6 core + 9 agent-assurance + 3 disclosure + 1 cost + 1 meta `kind-descriptor``
- `reference/database/MANIFEST.toml:34: entity_kinds           = 27    # 17 core + 6 agent-assurance + 3 disclosure + 1 cost (COST)`
- `reference/database/MANIFEST.toml:35: relation_predicates    = 31    # one per [[relations]] block in core/ontology.toml (includes SPEC §12 `cites_upstream`)`
- `reference/database/MANIFEST.toml:36: attribute_vocabularies = 41    # 10 core + 24 agent-assurance + 4 disclosure + 3 cost (decider_class, cost_dimension_category, cost_citing_kind)`
- `reference/database/MANIFEST.toml:37: attribute_values       = 106   # union across all closed-and-extensible-vocabulary allowed values (+22 from cost vocabularies: 8 + 7 + 7)`

Independent ontology count:

```text
$ python3 - <<'PY'
...
core/ontology.toml: entities=17 relations=31 attribute_vocabularies=10 attribute_values=39
profiles/agent-assurance/ontology.toml: entities=6 relations=0 attribute_vocabularies=24 attribute_values=91
profiles/disclosure/ontology.toml: entities=3 relations=0 attribute_vocabularies=4 attribute_values=18
profiles/cost/ontology.toml: entities=1 relations=0 attribute_vocabularies=3 attribute_values=22
template_kinds=20
entities=27
relations=31
attribute_vocabularies=41
attribute_values=170
```

The drift script does not check `attribute_values`:

```text
$ bash validators/check_manifest_drift.sh
manifest-drift check (ontology vs reference/database/MANIFEST.toml)
  manifest                    ontology
  template_kinds           20 == 20
  entity_kinds             27 == 27
  relation_predicates      31 == 31
  attribute_vocabularies   41 == 41

rdf-drift check (schema.ttl footer vs ontology)
  schema.ttl                  ontology
  template_kinds           20 == 20
  entity_kinds             27 == 27
  relation_predicates      31 == 31
  attribute_vocabularies   41 == 41

OK — manifest matches ontology
```

Exit code: `0`.

### Q7. Profile-descriptor correctness

Verdict: `confirmed`.

Evidence:

- `profiles/cost/PROFILE.toml:49: [profile]`
- `profiles/cost/PROFILE.toml:50: name              = "cost"`
- `profiles/cost/PROFILE.toml:51: namespace         = "spec.reserved"`
- `profiles/cost/PROFILE.toml:54: extends           = []`
- `profiles/cost/PROFILE.toml:56: contained_kinds   = [`
- `profiles/cost/PROFILE.toml:57:   "cost-record",`
- `profiles/cost/PROFILE.toml:59: ijb_primitive     = "thing"`
- `profiles/cost/PROFILE.toml:60: ijb_class         = "structural"`

Command output:

```text
$ python3 validators/validate_profile_descriptor.py --repo-root . profiles/cost/PROFILE.toml
PROFILE DESCRIPTOR VALIDATION PASSED
- files validated: 1
- profiles in resolution set: 3
```

Exit code: `0`.

### Q8. No-billing-dialect constraints honoured

Verdict: `confirmed`.

Evidence:

- `profiles/cost/cost-record-kind.toml:94: NOT IN SCOPE`
- `profiles/cost/cost-record-kind.toml:96: - Currency, vendor pricing, conversion rates: runtime / control plane.`
- `profiles/cost/cost-record-kind.toml:97: - Vendor SKUs and model identifiers: may be embedded inside the`
- `profiles/cost/cost-record-kind.toml:98:   producer-attested `unit_label` if the producer chooses.`
- `profiles/cost/cost-record-kind.toml:112: The SPEC layer does not normalise units across records. Two records`
- `validators/validate_cost.py:176:             q = dim.get("quantity")`
- `validators/validate_cost.py:178:             if isinstance(q, bool) or not isinstance(q, int) or q < 0:`
- `validators/validate_cost.py:184:             ul = dim.get("unit_label")`
- `validators/validate_cost.py:187:                     f"{path}: record.dimensions[{i}].unit_label must be "`
- `validators/validate_cost.py:188:                     f"a non-empty producer-attested string; got "`

Literal field-name check:

```text
$ rg -n "\b(rate|currency|total|formula|computed|cited_costs|aggregates|sum_of|cost_root|cost_total)\b" profiles/cost validators/validate_cost.py
EXIT:1
```

### Q9. No transitive aggregation surface

Verdict: `confirmed`.

Record field list evidence:

- `profiles/cost/cost-record-kind.toml:51:     [record]`
- `profiles/cost/cost-record-kind.toml:52:     action_id        = "EVMTX:smoke-run-2026-05-22-001"   # free-form citation`
- `profiles/cost/cost-record-kind.toml:53:     incurred_at      = "2026-05-22T14:32:11Z"             # RFC 3339`
- `profiles/cost/cost-record-kind.toml:54:     citing_kind      = "smoke-validation"                  # closed vocab`
- `profiles/cost/cost-record-kind.toml:55:     citing_ref       = "sha256:…#section.checks[3]"       # free-form`
- `profiles/cost/cost-record-kind.toml:56:     decider_class    = "llm_consensus"                     # closed vocab`
- `profiles/cost/cost-record-kind.toml:57:     producer_id      = "did:agent-assurance:runtime:ci-worker-12"`
- `profiles/cost/cost-record-kind.toml:58:     hash_algorithm   = "sha256"`
- `profiles/cost/cost-record-kind.toml:59:     canonical_form   = "rfc8785-jcs"`
- `profiles/cost/cost-record-kind.toml:107: The cost-record is NOT transitive. A gate-decision cites the`
- `profiles/cost/cost-record-kind.toml:110: earlier. Transitive aggregation is a runtime concern.`
- `profiles/cost/cost-record-kind.toml:263: [kind.relation_to_ontology]`
- `profiles/cost/cost-record-kind.toml:266: predicates_used     = []`

### Q10. Decider-class gaming surface

Verdict: `confirmed` that no structural protection exists; `refuted_with_evidence` that this is acknowledged in the kind descriptor or CHANGELOG.

Evidence for closed structural label only:

- `profiles/cost/ontology.toml:88: notes       = "Closed set declaring the class of deciding entity that incurred the cost. Auditors read this to know what threat surface the decision defends against. `other` is deliberately present: a producer that cannot honestly place their decider in the closed set MUST use `other` and accept more suspicious treatment from downstream consumers — silent mislabelling (e.g. tagging an LLM call as `deterministic_check`) is a separation-of-duty violation visible at the schema layer. After first tagged release, adding a value bumps THIS profile's ontology_version; no value MAY be removed."`
- `validators/validate_cost.py:138:     # INV01 — decider_class in closed vocab.`
- `validators/validate_cost.py:140:     if isinstance(dc, str) and dc not in vocab["decider_class"]:`

Evidence that kind descriptor and CHANGELOG say auditors read the class but do not acknowledge the spoofing limit:

- `profiles/cost/cost-record-kind.toml:168: [[kind.required_fields]]`
- `profiles/cost/cost-record-kind.toml:169: path        = "record.decider_class"`
- `profiles/cost/cost-record-kind.toml:171: description = "Closed-set discriminator declaring the class of entity that incurred the cost. Auditors read this to determine which threat surface the decision defends against."`
- `CHANGELOG.md:21:   `decider_class` (8 values: deterministic_check, llm_single,`
- `CHANGELOG.md:37:   IJB). New `validators/validate_cost.py` enforces the seven hard`

## 4. INDEPENDENT FINDINGS

### F-001

Severity: `medium`.

File/line evidence:

- `reference/database/MANIFEST.toml:254: expected_seed_counts = { kind_descriptor = 16, entity_kind_descriptor = 24, relation_descriptor = 31, attribute_vocabulary = 33, attribute_value_allowed = 79 }`
- `reference/database/MANIFEST.toml:285: expected_seed_counts = { kind_descriptor = 16, entity_kind_descriptor = 24, relation_descriptor = 31, attribute_vocabulary = 33, attribute_value_allowed = 79 }`
- `reference/database/MANIFEST.toml:295: expected_seed_counts = { dagtoml_kind_descriptor = 15, dagtoml_entity_kind_descriptor = 23, dagtoml_relation_descriptor = 30, dagtoml_attribute_vocabulary = 29, dagtoml_attribute_value_allowed = 54 }`
- `reference/database/postgres/seed.sql:31: -- kind_descriptor (20 rows: 6 core + 9 agent-assurance + 3 disclosure + 1 cost + 1 meta)`
- `reference/database/postgres/seed.sql:157: -- attribute_vocabulary (33 rows: 10 core + 24 agent-assurance + 4 disclosure + 3 cost)`

Problem: MANIFEST verification expected counts are stale relative to the regenerated seed files. This is separate from the top-level `[counts]` table and can mislead anyone reproducing the database verification commands.

Suggested fix: update the verification expected counts for postgres, duckdb, and sqlite to match the current seed/schema, or remove stale expected count tables if they are no longer authoritative.

### F-002

Severity: `low`.

File/line evidence:

- `reference/database/MANIFEST.toml:21: [ontology_source]`
- `reference/database/MANIFEST.toml:22: core_ontology       = "../../core/ontology.toml"`
- `reference/database/MANIFEST.toml:23: profile_ontology    = "../../profiles/agent-assurance/ontology.toml"`
- `reference/database/MANIFEST.toml:33: template_kinds         = 20    # 6 core + 9 agent-assurance + 3 disclosure + 1 cost + 1 meta `kind-descriptor``

Problem: `[ontology_source]` names only the agent-assurance profile ontology even though `[counts]` includes disclosure and cost. The drift script dynamically discovers all profiles, so the executable check is better than the manifest metadata.

Suggested fix: replace `profile_ontology` with an explicit list or glob that includes `profiles/*/ontology.toml`.

### F-003

Severity: `low`.

File/line evidence:

- `CHANGELOG.md:45: - **Second-pass review filings + round-2 fixes for `arxiv-prep-agent-dag.toml`.**`
- `CHANGELOG.md:46:   Captured the three completed second-pass job outputs (Claude / Codex /`
- `CHANGELOG.md:61:   file. A third-pass review (including a non-plan-mode Claude re-run) is`
- `CHANGELOG.md:62:   required before unconditional approval.`

Problem: the cost-profile commit includes an unrelated CHANGELOG entry for arxiv-prep work. The referenced review files are not part of the reviewed commit. That makes the release note broader than the actual commit contents.

Suggested fix: move this unrelated CHANGELOG entry to the commit that carries the arxiv-prep artifacts, or include the artifacts in the relevant commit.

## 5. TERMINAL VERDICT

CONCRETE UNRESOLVABLE BLOCKERS:

1. `reference/database/MANIFEST.toml:37` claims `attribute_values = 106` as the “union across all closed-and-extensible-vocabulary allowed values,” but independent counting of `core/ontology.toml`, `profiles/agent-assurance/ontology.toml`, `profiles/disclosure/ontology.toml`, and `profiles/cost/ontology.toml` gives `attribute_values=170`. This is not caught by `validators/check_manifest_drift.sh`, whose output compares only template kinds, entity kinds, relation predicates, and attribute vocabularies. Unblock by either correcting the MANIFEST definition/count or changing the drift validator to compute and enforce the intended value count.

2. The requested claim that `validators/validate_cost.py` enforces all seven hard invariants is false. `profiles/cost/cost-record-kind.toml:250-252` declares INV07 enforced by `validators/validate_ijb_conformance.py`, and the negative test shows `validate_cost.py` passes an INV07-violating instance while the IJB validator rejects it. Unblock by correcting the review-facing/CHANGELOG wording to say `validate_cost.py` enforces INV01–INV06 and IJB enforces INV07, or by adding equivalent INV07 enforcement to `validate_cost.py`.
