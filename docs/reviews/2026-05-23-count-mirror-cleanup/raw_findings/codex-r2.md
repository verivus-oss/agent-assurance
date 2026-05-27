**SESSION META**

Reviewer: Codex (GPT-5)  
Sandbox/approval: `danger-full-access`, approval policy `never`, network enabled  
MCP: `mcp__sqry__` used first; index present, 47 files, 7542 symbols, sqry version `2024-11-05`  
HEAD: `dc19203227864c891f8077573a3ecbabdbf21528`

**RE-VERIFICATION OF FIX**

Test 1: RDF triple count is now gated

```bash
cp reference/database/MANIFEST.toml /tmp/MANIFEST.reviewbak
cp reference/database/MANIFEST.toml /tmp/MANIFEST.bak
sed -i 's/expected_triple_counts = { schema = 1291/expected_triple_counts = { schema = 999/' reference/database/MANIFEST.toml
bash validators/check_manifest_drift.sh > /tmp/drift.out 2>&1; echo "EXIT=$?"
tail -10 /tmp/drift.out
cp /tmp/MANIFEST.bak reference/database/MANIFEST.toml
```

Output:

```text
EXIT=1
    rust.EXPECTED_COUNTS.attribute_value_allowed                  106 ==    106

tools/dagtoml-duckdb-go/main.go expectedCounts:
    go.expectedCounts.kind_descriptor                              20 ==     20
    go.expectedCounts.entity_kind_descriptor                       27 ==     27
    go.expectedCounts.relation_descriptor                          31 ==     31
    go.expectedCounts.attribute_vocabulary                         41 ==     41
    go.expectedCounts.attribute_value_allowed                     106 ==    106

COUNT-MIRROR DRIFT: 1 surface(s) out of sync.
```

Supplemental confirmation from `/tmp/drift.out`:

```text
60:    rdf.expected_triple_counts.schema                             999 !=   1291   <-- DRIFT
```

Verdict: `fix confirmed`.

Test 2: legacy field is rejected even alongside new fields

```bash
python3 -c '
import pathlib
text = pathlib.Path("reference/database/MANIFEST.toml").read_text()
text = text.replace("attribute_values_closed = 99",
                    "attribute_values_closed = 99\nattribute_values = 170    # legacy", 1)
pathlib.Path("/tmp/MANIFEST_both.toml").write_text(text)
'
cp /tmp/MANIFEST_both.toml reference/database/MANIFEST.toml
bash validators/check_manifest_drift.sh > /tmp/drift.out 2>&1; echo "EXIT=$?"
tail -10 /tmp/drift.out
cp /tmp/MANIFEST.bak reference/database/MANIFEST.toml
```

Output:

```text
EXIT=1
    rust.EXPECTED_COUNTS.attribute_value_allowed                  106 ==    106

tools/dagtoml-duckdb-go/main.go expectedCounts:
    go.expectedCounts.kind_descriptor                              20 ==     20
    go.expectedCounts.entity_kind_descriptor                       27 ==     27
    go.expectedCounts.relation_descriptor                          31 ==     31
    go.expectedCounts.attribute_vocabulary                         41 ==     41
    go.expectedCounts.attribute_value_allowed                     106 ==    106

COUNT-MIRROR DRIFT: 1 surface(s) out of sync.
```

Supplemental grep for the required legacy-field message:

```text
24:    [counts].attribute_values_declared                            170 ==    170
25:    [counts].attribute_values_closed                               99 ==     99
77:COUNT-MIRROR DRIFT: 1 surface(s) out of sync.
```

Verdict: `fix incomplete`. The gate exits `1`, but the required output message naming `[counts].attribute_values` is not printed.

Test 3: clean tree exits 0

```bash
bash validators/check_manifest_drift.sh > /tmp/drift.out 2>&1; echo "EXIT=$?"
tail -5 /tmp/drift.out
```

Output:

```text
EXIT=0
    go.expectedCounts.attribute_value_allowed                     106 ==    106

COUNT-MIRROR OK — every surface agrees with reality.

OK — manifest matches ontology + every count-mirror surface agrees
```

Verdict: `fix confirmed`.

Test 4: RDF tool missing fails the gate

```bash
mv tools/dagtoml-rdf/target/release/dagtoml-rdf /tmp/dagtoml-rdf.bak
bash validators/check_manifest_drift.sh > /tmp/drift.out 2>&1; echo "EXIT=$?"
tail -10 /tmp/drift.out
mv /tmp/dagtoml-rdf.bak tools/dagtoml-rdf/target/release/dagtoml-rdf
```

Output:

```text
EXIT=1
    rust.EXPECTED_COUNTS.attribute_value_allowed                  106 ==    106

tools/dagtoml-duckdb-go/main.go expectedCounts:
    go.expectedCounts.kind_descriptor                              20 ==     20
    go.expectedCounts.entity_kind_descriptor                       27 ==     27
    go.expectedCounts.relation_descriptor                          31 ==     31
    go.expectedCounts.attribute_vocabulary                         41 ==     41
    go.expectedCounts.attribute_value_allowed                     106 ==    106

COUNT-MIRROR DRIFT: 1 surface(s) out of sync.
```

Supplemental grep:

```text
59:expected_triple_counts.rdf (vs dagtoml-rdf verify):
60:  rdf.expected_triple_counts.schema                              (tool not available — gate fail-soft per design)
76:COUNT-MIRROR DRIFT: 1 surface(s) out of sync.
```

Verdict: `fix incomplete`. It fails closed, but it does not print the required missing-binary message or `--no-rdf` opt-out instruction.

Test 5: `--no-rdf` opt-out works

```bash
python3 validators/check_attribute_values.py --no-rdf > /tmp/x.out 2>&1; echo "EXIT=$?"
grep -i "rdf\|triple" /tmp/x.out
```

Output:

```text
EXIT=0
expected_footer_counts.rdf (vs ontology):
    rdf.expected_footer_counts.template_kinds                      20 ==     20
    rdf.expected_footer_counts.entity_kinds                        27 ==     27
    rdf.expected_footer_counts.relation_predicates                 31 ==     31
    rdf.expected_footer_counts.attribute_vocabularies              41 ==     41
```

Supplemental exact check for `expected_triple_counts` returned no output.

Verdict: `fix confirmed`.

**PRIOR BLOCKER STATUS**

Blocker 1, RDF `expected_triple_counts` not gated: `resolved`. Evidence: Test 1 returned `EXIT=1`, and `/tmp/drift.out` line 60 showed `rdf.expected_triple_counts.schema 999 != 1291 <-- DRIFT`.

Blocker 2, legacy `attribute_values` could silently coexist: `resolved for gate behavior`. Evidence: Test 2 returned `EXIT=1` after injecting both fields. However, the diagnostic output is incomplete; see new finding.

**NEW FINDINGS**

1. High: [validators/check_attribute_values.py](/srv/repos/external/verivus-oss/agent-assurance/validators/check_attribute_values.py:228) stores custom failure messages but never prints them. The legacy-field rejection appended at line 329 and the missing-RDF-binary guidance appended at line 392 are invisible to users; `DriftReport.print()` only prints `COUNT-MIRROR DRIFT: N surface(s) out of sync.` This caused required Tests 2 and 4 to fail their expected diagnostic-output criteria.

**TERMINAL VERDICT**

CONCRETE UNRESOLVABLE BLOCKERS:

1. Required diagnostic output is still missing for non-`check()` failures. Tests 2 and 4 both returned `EXIT=1`, but neither printed the required actionable message. The root cause is [validators/check_attribute_values.py](/srv/repos/external/verivus-oss/agent-assurance/validators/check_attribute_values.py:228): `DriftReport.print()` does not emit `self.failures`, so the explicit messages added at lines 329 and 392 are never shown.
