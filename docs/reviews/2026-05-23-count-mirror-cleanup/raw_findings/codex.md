**SESSION META**

Reviewer model + version: Codex, GPT-5.

Sandbox / approval posture: `danger-full-access`, network enabled, approval policy `never`; no approvals requested.

MCP servers: sqry MCP was used first via `get_index_status`, `semantic_search`, `pattern_search`, and `get_document_symbols`. The sqry index was stale relative to reviewed `HEAD`: it found `tools/dagtoml-duckdb/*` symbols but did not contain the new `validators/check_attribute_values.py`, so exact verification used direct file inspection and executed commands afterward.

Re-derived `HEAD`:

```bash
git rev-parse HEAD
```

```text
5b1eca1f99e38e46c832b9e4f58095019e763127
```

Worktree note: the repository has unrelated dirty and untracked files. I restored every file I perturbed; `git diff -- reference/database/MANIFEST.toml validators/check_manifest_drift.sh validators/check_attribute_values.py` was empty after perturbation tests.

**PROCESS CONFIRMATIONS**

Migration / naming guidance: confirmed. `reference/database/MANIFEST.toml:37-60` explains `attribute_values_declared` versus `attribute_values_closed`, names the validators, and tells producers that seed-emission counts live under per-engine `expected_seed_counts`.

No SPEC retconning for this cleanup: confirmed. The target cleanup did not add Opus’s proposed SPEC paragraph; the naming convention is in `MANIFEST.toml`, matching the critiques’ recommended scope.

Tests run with output: confirmed. Required command outputs are captured in the 10 answers below, including drift perturbation, independent count scripts, RDF verify, SQLite fresh load via Python stdlib, and the full validator suite.

**ANSWERS TO THE 10 SUBSTANTIVE QUESTIONS**

1. **Does the gate actually fail on drift?**  
Verdict: confirmed for `attribute_values_declared` drift.

Evidence: `validators/check_manifest_drift.sh:151` invokes `validators/check_attribute_values.py`; `validators/check_attribute_values.py:305-314` checks `[counts].attribute_values_declared`.

Command:

```bash
cp reference/database/MANIFEST.toml /tmp/manifest.review.$$
python3 - <<'PY'
from pathlib import Path
p = Path('reference/database/MANIFEST.toml')
s = p.read_text()
s = s.replace('attribute_values_declared = 170', 'attribute_values_declared = 171', 1)
p.write_text(s)
PY
bash validators/check_manifest_drift.sh
rc1=$?
cp /tmp/manifest.review.$$ reference/database/MANIFEST.toml
bash validators/check_manifest_drift.sh
rc2=$?
printf 'PERTURBED_EXIT_CODE=%s\nRESTORED_EXIT_CODE=%s\n' "$rc1" "$rc2"
```

```text
[counts].attribute_values_declared                            171 !=    170   <-- DRIFT
COUNT-MIRROR DRIFT: 1 surface(s) out of sync.
...
[counts].attribute_values_declared                            170 ==    170
COUNT-MIRROR OK — every surface agrees with reality.
OK — manifest matches ontology + every count-mirror surface agrees
PERTURBED_EXIT_CODE=1
RESTORED_EXIT_CODE=0
```

2. **Independent count derivation.**  
Verdict: confirmed.

Evidence: `MANIFEST.toml:42` has `attribute_values_declared = 170`; `MANIFEST.toml:51` has `attribute_values_closed = 99`.

Command:

```bash
python3 - <<'PY'
from pathlib import Path
import tomllib
repo = Path('.')
paths = [repo/'core/ontology.toml'] + sorted((repo/'profiles').glob('*/ontology.toml'))
total_declared = total_closed = 0
for path in paths:
    doc = tomllib.loads(path.read_text())
    declared = closed = blocks = 0
    for vocab in doc.get('attribute_vocabularies', []):
        blocks += 1
        n = len(vocab.get('values', []))
        declared += n
        if vocab.get('extensible') is False:
            closed += n
    total_declared += declared
    total_closed += closed
    print(f'{path}: blocks={blocks} declared={declared} closed={closed}')
manifest = tomllib.loads((repo/'reference/database/MANIFEST.toml').read_text())['counts']
print(f'TOTAL declared={total_declared} closed={total_closed}')
print('MANIFEST attribute_values_declared=', manifest['attribute_values_declared'])
print('MANIFEST attribute_values_closed=', manifest['attribute_values_closed'])
print('MATCH declared=', total_declared == manifest['attribute_values_declared'])
print('MATCH closed=', total_closed == manifest['attribute_values_closed'])
PY
```

```text
core/ontology.toml: blocks=10 declared=39 closed=22
profiles/agent-assurance/ontology.toml: blocks=24 declared=91 closed=51
profiles/cost/ontology.toml: blocks=3 declared=22 closed=22
profiles/disclosure/ontology.toml: blocks=4 declared=18 closed=4
TOTAL declared=170 closed=99
MANIFEST attribute_values_declared= 170
MANIFEST attribute_values_closed= 99
MATCH declared= True
MATCH closed= True
EXIT_CODE=0
```

3. **Seed-row truth.**  
Verdict: confirmed.

Evidence: `MANIFEST.toml:277`, `:308`, and `:318` declare all expected seed counts as `20/27/31/41/106`.

Command:

```bash
python3 - <<'PY'
from pathlib import Path
import re, tomllib
repo = Path('.')
manifest = tomllib.loads((repo/'reference/database/MANIFEST.toml').read_text())['verification']
tables = ['kind_descriptor','entity_kind_descriptor','relation_descriptor','attribute_vocabulary','attribute_value_allowed']
def count_rows(seed_path, table_pattern):
    txt = seed_path.read_text()
    m = re.search(rf'INSERT INTO {table_pattern}\b.*?\bVALUES', txt, re.S)
    rest = txt[m.end():]
    end = re.search(r'\n\s*(?:INSERT INTO|ALTER|CREATE|DROP|COMMIT|--\s*=====)', rest)
    if end:
        rest = rest[:end.start()]
    return sum(1 for line in rest.splitlines() if line.lstrip().startswith('(') and "'" in line)
for engine in ['postgres','sqlite','duckdb']:
    seed = repo/'reference/database'/engine/'seed.sql'
    prefix = 'dagtoml_' if engine == 'sqlite' else r'(?:dagtoml\.)?'
    expected = manifest[engine]['expected_seed_counts']
    print(f'[{engine}] {seed}')
    for table in tables:
        actual = count_rows(seed, f'{prefix}{table}')
        key = f'dagtoml_{table}' if engine == 'sqlite' else table
        print(f'  {key}: actual={actual} manifest={expected[key]} match={actual == expected[key]}')
PY
```

```text
[postgres] reference/database/postgres/seed.sql
  kind_descriptor: actual=20 manifest=20 match=True
  entity_kind_descriptor: actual=27 manifest=27 match=True
  relation_descriptor: actual=31 manifest=31 match=True
  attribute_vocabulary: actual=41 manifest=41 match=True
  attribute_value_allowed: actual=106 manifest=106 match=True
[sqlite] reference/database/sqlite/seed.sql
  dagtoml_kind_descriptor: actual=20 manifest=20 match=True
  dagtoml_entity_kind_descriptor: actual=27 manifest=27 match=True
  dagtoml_relation_descriptor: actual=31 manifest=31 match=True
  dagtoml_attribute_vocabulary: actual=41 manifest=41 match=True
  dagtoml_attribute_value_allowed: actual=106 manifest=106 match=True
[duckdb] reference/database/duckdb/seed.sql
  kind_descriptor: actual=20 manifest=20 match=True
  entity_kind_descriptor: actual=27 manifest=27 match=True
  relation_descriptor: actual=31 manifest=31 match=True
  attribute_vocabulary: actual=41 manifest=41 match=True
  attribute_value_allowed: actual=106 manifest=106 match=True
EXIT_CODE=0
```

4. **Hardcoded mirror consistency.**  
Verdict: confirmed.

Evidence: Rust hardcode at `tools/dagtoml-duckdb/src/main.rs:24-30`; Go hardcode at `tools/dagtoml-duckdb-go/main.go:38-47`; MANIFEST duckdb mirror at `MANIFEST.toml:308`.

```text
MANIFEST.duckdb.expected_seed_counts= {'kind_descriptor': 20, 'entity_kind_descriptor': 27, 'relation_descriptor': 31, 'attribute_vocabulary': 41, 'attribute_value_allowed': 106}
rust.EXPECTED_COUNTS= {'kind_descriptor': 20, 'entity_kind_descriptor': 27, 'relation_descriptor': 31, 'attribute_vocabulary': 41, 'attribute_value_allowed': 106}
go.expectedCounts= {'kind_descriptor': 20, 'entity_kind_descriptor': 27, 'relation_descriptor': 31, 'attribute_vocabulary': 41, 'attribute_value_allowed': 106}
rust_matches_manifest= True
go_matches_manifest= True
EXIT_CODE=0
```

5. **Schema constraint coverage.**  
Verdict: confirmed.

Evidence: SQLite includes `'profile:cost'` in all four layer CHECKs at `sqlite/schema.sql:40`, `:49`, `:68`, `:80`; Postgres includes it in `spec_layer` at `postgres/schema.sql:66-71`; DuckDB includes it at `duckdb/schema.sql:41`.

The `sqlite3` CLI was unavailable, but Python stdlib `sqlite3` successfully loaded schema + seed:

```text
loaded reference/database/sqlite/schema.sql
loaded reference/database/sqlite/seed.sql
dagtoml_kind_descriptor=20
dagtoml_entity_kind_descriptor=27
dagtoml_relation_descriptor=31
dagtoml_attribute_vocabulary=41
dagtoml_attribute_value_allowed=106
PYTHON_SQLITE_LOAD_EXIT_CODE=0
```

6. **RDF triple count.**  
Verdict: confirmed for the artifact count, but see independent blocker F1 about CI gating.

Evidence: `MANIFEST.toml:299` says `expected_triple_counts = { schema = 1291, shapes = 148 }`.

Command:

```bash
tools/dagtoml-rdf/target/release/dagtoml-rdf verify -o reference/database/rdf/schema.ttl
```

```text
verify "reference/database/rdf/schema.ttl": OK — parsed 1291 triples
EXIT_CODE=0
```

7. **Cypher UNWIND data drift acknowledgement.**  
Verdict: confirmed.

Evidence: `graph/schema.cypher:88-93` says ontology declares 20 but UNWIND lists 15; `:114-115` says ontology declares 27 but UNWIND lists 23; `:147-148` says relation predicates list 31.

Command output:

```text
actual_cypher_unwind_counts= {'KindDescriptor': 15, 'EntityKind': 23, 'RelationPredicate': 31}
MANIFEST.expected_node_counts= {'KindDescriptor': 20, 'EntityKind': 27, 'RelationPredicate': 31}
KindDescriptor: actual=15 manifest=20
EntityKind: actual=23 manifest=27
RelationPredicate: actual=31 manifest=31
EXIT_CODE=0
```

8. **ISS-001 self-approval is filed and corroborated.**  
Verdict: confirmed.

Evidence: `docs/issues/2026-05-23-ISS-001-self-approval-discipline.md:36-52` lists the same `bc2a7c5`, `dc3a7b0`, `5c145c8`, and `20c6207` sequence.

`git log --oneline -- SPEC.md`:

```text
20c6207 SPEC §12 round-3: address round-2 reviewer blockers
5c145c8 SPEC §12 round-2: scope tightening + codex-review blockers
dc3a7b0 SPEC §12 follow-up: resolve grok review blockers
bc2a7c5 SPEC §12: closure-root rule (brittleness propagation)
56a191d Anchor SPEC + README on Provable Intent + Structural Governance
...
```

Corroborating review ledger: `terminal_decision.toml:25-55` records grok round 1 against `bc2a7c5` as `concrete_unresolvable_blockers`, codex round 1 against `dc3a7b0` as `concrete_unresolvable_blockers`, and both grok/codex round 2 against `5c145c8` as blockers. `raw_findings/codex-r3.md:112` records final codex `UNCONDITIONAL APPROVAL` against `20c6207`, while `raw_findings/grok-r3.md:72-78` records working-tree blockers.

9. **Validator handles legacy field correctly.**  
Verdict: refuted_with_evidence.

Evidence: `validators/check_attribute_values.py:316-318` only flags legacy `attribute_values` when `attribute_values_declared` is absent:

```text
if "attribute_values" in counts and "attribute_values_declared" not in counts:
```

Required variant with both `attribute_values = 170` and `attribute_values_declared = 170` exited 0 and printed no legacy warning:

```text
count-mirror gate  (declared vs actual)
==========================================================================================

[counts] (ontology-derived):
    [counts].template_kinds                                        20 ==     20
    [counts].entity_kinds                                          27 ==     27
    [counts].relation_predicates                                   31 ==     31
    [counts].attribute_vocabularies                                41 ==     41
    [counts].attribute_values_declared                            170 ==    170
    [counts].attribute_values_closed                               99 ==     99
...
COUNT-MIRROR OK — every surface agrees with reality.
EXIT_CODE=0
```

10. **No regression of prior gates.**  
Verdict: confirmed for listed validators, with the expected working-tree closure-root failures; refuted for the prompt’s claim that the five-file list is in the `[counts].attribute_values_closed` comment. The five files are documented in prior §12 review artifacts, not in `MANIFEST.toml:44-60`.

Command:

```bash
bash validators/check_manifest_drift.sh
python3 validators/validate_closure_root.py --discover .
python3 validators/validate_cost.py --repo-root . examples/minimal-cost-record.toml
python3 validators/validate_ijb_conformance.py core/ontology.toml
python3 validators/validate_ijb_conformance.py profiles/cost/ontology.toml
```

```text
$ bash validators/check_manifest_drift.sh
...
COUNT-MIRROR OK — every surface agrees with reality.

OK — manifest matches ontology + every count-mirror surface agrees
EXIT_CODE=0

$ python3 validators/validate_closure_root.py --discover .
FAIL arxiv-prep-agent-dag.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL claim-analysis-agent-gated-dag.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL tools/claim-analysis-document-review-dag.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL tools/review-request-dag.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
FAIL tools/werner-style-policy.toml: missing required root-level `closure_root` field (SPEC §12.1). Self-contained documents MUST use the empty-closure sentinel `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

CLOSURE-ROOT VALIDATION FAILED: 5 error(s) across 74 file(s).
EXIT_CODE=1

$ python3 validators/validate_cost.py --repo-root . examples/minimal-cost-record.toml
COST-RECORD VALIDATION PASSED (1 file(s)).
EXIT_CODE=0

$ python3 validators/validate_ijb_conformance.py core/ontology.toml
IJB CONFORMANCE VALIDATION PASSED
- file: /srv/repos/external/verivus-oss/agent-assurance/core/ontology.toml
- template_kind: ontology
EXIT_CODE=0

$ python3 validators/validate_ijb_conformance.py profiles/cost/ontology.toml
IJB CONFORMANCE VALIDATION PASSED
- file: /srv/repos/external/verivus-oss/agent-assurance/profiles/cost/ontology.toml
- template_kind: ontology
- framework_profile: cost
EXIT_CODE=0
```

**INDEPENDENT FINDINGS**

F1 — high — `validators/check_manifest_drift.sh:151`, `validators/check_attribute_values.py:257-263`, `:371-382`, `reference/database/MANIFEST.toml:299`.

Quote:

```text
parser.add_argument("--rdf", action="store_true", ...)
...
if args.rdf:
    report.summary.append("\nexpected_triple_counts.rdf (vs dagtoml-rdf verify):")
```

Problem: `expected_triple_counts` is advertised as part of the count-mirror gate, but the CI-facing wrapper calls `check_attribute_values.py` without `--rdf`. I perturbed `expected_triple_counts.schema` from `1291` to `1290`; `bash validators/check_manifest_drift.sh` still exited 0, while `python3 validators/check_attribute_values.py --rdf` exited 1.

Perturbation output:

```text
CHECK_MANIFEST_DRIFT_EXIT_CODE=0
CHECK_ATTRIBUTE_VALUES_RDF_EXIT_CODE=1
```

Suggested fix: invoke `check_attribute_values.py --rdf` from `check_manifest_drift.sh`, or remove the optional flag and always check RDF triples when the built binary exists.

F2 — medium — `validators/check_attribute_values.py:316-318`.

Quote:

```text
if "attribute_values" in counts and "attribute_values_declared" not in counts:
```

Problem: a MANIFEST containing both the legacy `attribute_values = 170` and the new `attribute_values_declared = 170` is accepted as clean. That leaves the removed legacy surface capable of reappearing silently.

Suggested fix: flag `attribute_values` whenever present, regardless of whether new fields also exist.

**TERMINAL VERDICT**

CONCRETE UNRESOLVABLE BLOCKERS:

1. RDF `expected_triple_counts` is not gated by the required drift command. `check_manifest_drift.sh` invokes `check_attribute_values.py` without `--rdf`, and a direct perturbation of `MANIFEST.toml expected_triple_counts.schema` exits 0 under the advertised gate. This violates the target claim that every count-mirror surface is gated.

2. The legacy `attribute_values` field is accepted when it coexists with `attribute_values_declared`, contrary to the required legacy-field handling test. The validator only warns when the new field is absent, so the cleanup does not mechanically prevent the old ambiguous field from returning.
