**SESSION META**

Model: Codex, GPT-5-based coding agent
HEAD re-derived: `012c1e9fabb0fb4805548f7344e8c89356b3ccee`
Touched test paths restored clean: `reference/database/MANIFEST.toml`, `tools/dagtoml-rdf/target/release/dagtoml-rdf`

**RE-VERIFICATION OF DIAGNOSTIC FIX**

**Test 2 (legacy coexistence)** — EXIT=1:
```
FAILURES (each is one surface out of sync):
  1. [counts].attribute_values is the legacy ambiguous field that was retired in commit 9996826. It has been split into `attribute_values_declared` (170) and `attribute_values_closed` (99). The field MUST NOT be re-introduced regardless of whether the named successors are also present — silent coexistence is itself a defect. Remove the `attribute_values = ...` line from MANIFEST.toml.
```
Verdict: `fix confirmed`.

**Test 4 (missing dagtoml-rdf binary)** — EXIT=1:
```
  rdf.expected_triple_counts.schema                              (tool not available — hard fail, see FAILURES below)

FAILURES (each is one surface out of sync):
  1. RDF triple-count gate could not run: tools/dagtoml-rdf/target/release/dagtoml-rdf is missing or did not produce a parseable `parsed N triples` line. Either `cargo build --release -p dagtoml-rdf --manifest-path tools/dagtoml-rdf/Cargo.toml` or pass `--no-rdf` to acknowledge skipping this surface.
```
Verdict: `fix confirmed`.

**Test 1 (RDF triple count drift)** — Test 1 EXIT=1, `1. rdf.expected_triple_counts.schema: declared 999, actual 1291`. Verdict: `fix confirmed`.

**Test 3 (clean tree)** — EXIT=0, `COUNT-MIRROR OK — every surface agrees with reality. OK — manifest matches ontology + every count-mirror surface agrees`. Verdict: `fix confirmed`.

**Test 5 (--no-rdf opt-out)** — EXIT=0, no RDF section in output. Verdict: `fix confirmed`.

**PRIOR-BLOCKER STATUS**

`DriftReport.print()` not emitting `self.failures`: `resolved`. Evidence: validators/check_attribute_values.py:231 now enters a failure block, prints `FAILURES (each is one surface out of sync):` at line 237, and iterates `self.failures` at line 238. The legacy-field diagnostic appended at line 341 and the missing-RDF diagnostic appended at line 404 are now operator-visible in Tests 2 and 4.

**NEW FINDINGS**

None.

**TERMINAL VERDICT**

UNCONDITIONAL APPROVAL.
