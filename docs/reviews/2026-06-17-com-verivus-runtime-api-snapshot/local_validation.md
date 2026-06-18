# Local validation log — com.verivus.runtime / api-snapshot

FINAL run. Reviewer iterations: Grok r1 (approved), Codex r1 (2 blockers), Codex r2 (approved after fix). Bad-closure marked out of conformance scope via unblessed template_kind so bare `--discover .` passes. RS=release Rust primary; GO=fresh Go build; Python=system python3 (tomli 2.4.1).

> **2026-06-18 second-pass cross-LLM review addendum** — see §"Second-pass review" at the bottom of this file. One RKV01 enforcement gap was fixed (magic-present-but-markers-absent now fails closed) with a new negative fixture; one finding on `attestation_sha256` was rebutted against design-record D1/D4 (documented RUNTIME-SPEC boundary).

```
## ACCEPTANCE — POSITIVES (expect exit 0)

$ python3 validators/validate_kind_descriptor.py profiles/com.verivus.runtime/api-snapshot-kind.toml --repo-root . --check-references-exist
KIND DESCRIPTOR VALIDATION PASSED
- file: /srv/repos/external/verivus-oss/agent-assurance/profiles/com.verivus.runtime/api-snapshot-kind.toml
exit=0

$ python3 validators/validate_ijb_conformance.py profiles/com.verivus.runtime/ontology.toml
IJB CONFORMANCE VALIDATION PASSED
- file: /srv/repos/external/verivus-oss/agent-assurance/profiles/com.verivus.runtime/ontology.toml
exit=0

$ python3 validators/validate_ijb_conformance.py profiles/com.verivus.runtime/api-snapshot-kind.toml
IJB CONFORMANCE VALIDATION PASSED
- file: /srv/repos/external/verivus-oss/agent-assurance/profiles/com.verivus.runtime/api-snapshot-kind.toml
exit=0

$ python3 validators/validate_ijb_conformance.py examples/minimal-api-snapshot.toml --repo-root .
IJB CONFORMANCE VALIDATION PASSED
- file: /srv/repos/external/verivus-oss/agent-assurance/examples/minimal-api-snapshot.toml
exit=0

$ python3 validators/validate_closure_root.py examples/minimal-api-snapshot.toml profiles/com.verivus.runtime/api-snapshot-kind.toml profiles/com.verivus.runtime/ontology.toml profiles/com.verivus.runtime/PROFILE.toml
CLOSURE-ROOT VALIDATION PASSED (4 file(s)).
exit=0

$ python3 validators/validate_closure_root.py --discover .
CLOSURE-ROOT VALIDATION PASSED (100 file(s)).
exit=0

$ python3 validators/validate_abstraction_class.py profiles/com.verivus.runtime/api-snapshot-kind.toml --repo-root .
ABSTRACTION-CLASS VALIDATION PASSED (1 file(s) checked; 1 declared a §13 block).
exit=0

$ python3 validators/validate_profile_descriptor.py --repo-root . profiles/com.verivus.runtime/PROFILE.toml
PROFILE DESCRIPTOR VALIDATION PASSED
- files validated: 1
exit=0

$ python3 validators/validate_provenance.py examples/minimal-api-snapshot.toml --repo-root .
PROVENANCE VALIDATION PASSED
- files inspected: 1
exit=0

$ python3 validators/validate_api_snapshot.py --repo-root . examples/minimal-api-snapshot.toml
API-SNAPSHOT VALIDATION PASSED
- files inspected: 1
exit=0

$ tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs --repo-root . --mode provenance examples/minimal-api-snapshot.toml profiles/com.verivus.runtime/api-snapshot-kind.toml profiles/com.verivus.runtime/ontology.toml profiles/com.verivus.runtime/PROFILE.toml
DAGTOML VALIDATION PASSED (rust primary)
- files validated: 4
exit=0

$ /tmp/dagtoml-validate-go -repo-root . -mode provenance examples/minimal-api-snapshot.toml profiles/com.verivus.runtime/api-snapshot-kind.toml profiles/com.verivus.runtime/ontology.toml profiles/com.verivus.runtime/PROFILE.toml
DAGTOML VALIDATION PASSED (go primary)
- files validated: 4
exit=0

$ tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs --repo-root . --mode ijb profiles/com.verivus.runtime/ontology.toml profiles/com.verivus.runtime/api-snapshot-kind.toml examples/minimal-api-snapshot.toml
DAGTOML VALIDATION PASSED (rust primary)
- files validated: 3
exit=0

$ /tmp/dagtoml-validate-go -repo-root . -mode ijb profiles/com.verivus.runtime/ontology.toml profiles/com.verivus.runtime/api-snapshot-kind.toml examples/minimal-api-snapshot.toml
DAGTOML VALIDATION PASSED (go primary)
- files validated: 3
exit=0

$ tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs --repo-root . --mode kind-descriptor profiles/com.verivus.runtime/api-snapshot-kind.toml
DAGTOML VALIDATION PASSED (rust primary)
- files validated: 1
exit=0

$ /tmp/dagtoml-validate-go -repo-root . -mode kind-descriptor profiles/com.verivus.runtime/api-snapshot-kind.toml
DAGTOML VALIDATION PASSED (go primary)
- files validated: 1
exit=0

$ tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs --repo-root . --mode abstraction-class profiles/com.verivus.runtime/api-snapshot-kind.toml
DAGTOML VALIDATION PASSED (rust primary)
- files validated: 1
exit=0

$ /tmp/dagtoml-validate-go -repo-root . -mode abstraction-class profiles/com.verivus.runtime/api-snapshot-kind.toml
DAGTOML VALIDATION PASSED (go primary)
- files validated: 1
exit=0

$ tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs --repo-root . --mode profile profiles/com.verivus.runtime/PROFILE.toml
DAGTOML VALIDATION PASSED (rust primary)
- files validated: 1
exit=0

$ /tmp/dagtoml-validate-go -repo-root . -mode profile profiles/com.verivus.runtime/PROFILE.toml
DAGTOML VALIDATION PASSED (go primary)
- files validated: 1
exit=0

$ taplo lint profiles/com.verivus.runtime/api-snapshot-kind.toml profiles/com.verivus.runtime/ontology.toml profiles/com.verivus.runtime/PROFILE.toml examples/minimal-api-snapshot.toml
 INFO taplo:load_config: found configuration file path="/srv/repos/external/verivus-oss/agent-assurance/.taplo.toml"
 INFO taplo:lint_files:collect_files: found files total=4 excluded=0 files=["/srv/repos/external/verivus-oss/agent-assurance/profiles/com.verivus.runtime/api-snapshot-kind.toml", "/srv/repos/external/verivus-oss/agent-assurance/profiles/com.verivus.runtime/ontology.toml", "/srv/repos/external/verivus-oss/agent-assurance/profiles/com.verivus.runtime/PROFILE.toml", "/srv/repos/external/verivus-oss/agent-assurance/examples/minimal-api-snapshot.toml"] cwd="/srv/repos/external/verivus-oss/agent-assurance"
exit=0

## ACCEPTANCE — NEGATIVES (expect exit 1, rejected by all listed impls)

$ python3 validators/validate_closure_root.py examples/negative/api-snapshot-bad-closure.toml
FAIL examples/negative/api-snapshot-bad-closure.toml: `closure_root` does not match SPEC §12.8 source-hash closure. Expected `sha256:f251f64bc6170cb32a4b3c0bcc10d520247c41e7bbf22587d206108e6d19098c` from 1 canonical source-hash input(s), got `sha256:013f3d34bab26a1b9d9fd77ff03aae76a3b07ee112c4995dc5ef448b2d1796db`.

exit=1

$ tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs --repo-root . --mode provenance examples/negative/api-snapshot-bad-closure.toml
DAGTOML VALIDATION FAILED (rust primary)
- --- examples/negative/api-snapshot-bad-closure.toml ---
exit=1

$ /tmp/dagtoml-validate-go -repo-root . -mode provenance examples/negative/api-snapshot-bad-closure.toml
DAGTOML VALIDATION FAILED (go primary)
- --- examples/negative/api-snapshot-bad-closure.toml ---
exit=1

$ python3 validators/validate_provenance.py examples/negative/api-snapshot-bad-closure.toml --repo-root .
PROVENANCE VALIDATION FAILED
- files inspected: 1
exit=1

$ python3 validators/validate_ijb_conformance.py examples/negative/com.verivus.runtime-ontology-bad-ijb.toml
IJB CONFORMANCE VALIDATION FAILED
- file: /srv/repos/external/verivus-oss/agent-assurance/examples/negative/com.verivus.runtime-ontology-bad-ijb.toml
exit=1

$ tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs --repo-root . --mode ijb examples/negative/com.verivus.runtime-ontology-bad-ijb.toml
DAGTOML VALIDATION FAILED (rust primary)
- --- examples/negative/com.verivus.runtime-ontology-bad-ijb.toml ---
exit=1

$ /tmp/dagtoml-validate-go -repo-root . -mode ijb examples/negative/com.verivus.runtime-ontology-bad-ijb.toml
DAGTOML VALIDATION FAILED (go primary)
- --- examples/negative/com.verivus.runtime-ontology-bad-ijb.toml ---
exit=1

$ python3 validators/validate_api_snapshot.py --repo-root . examples/negative/api-snapshot-inlined-secret.toml
API-SNAPSHOT VALIDATION FAILED
- files inspected: 1
exit=1

$ python3 validators/validate_api_snapshot.py --repo-root . examples/negative/api-snapshot-raw-header.toml
API-SNAPSHOT VALIDATION FAILED
- files inspected: 1
exit=1

$ python3 validators/validate_api_snapshot.py --repo-root . examples/negative/api-snapshot-witness-incomplete.toml
API-SNAPSHOT VALIDATION FAILED
- files inspected: 1
exit=1

$ python3 validators/validate_api_snapshot.py --repo-root . examples/negative/api-snapshot-bad-subpart-digest.toml
API-SNAPSHOT VALIDATION FAILED
- files inspected: 1
exit=1

```

## Second-pass review (2026-06-18, stdio gtwy: Codex gpt-5.5 + Grok)

Both reviewers ran with full filesystem access against worktree `/tmp/apisnap-review`,
recomputed every digest, and ran the battery themselves.

**Grok — BLOCKER (fixed).** `validate_api_snapshot.py` recomputed RKV01 sub-parts
only inside `if dmark in data and smark in data:` / `if bmark in data:`. A capture
that *starts with* the `DAGTOML-API-CAPTURE/1` magic (so it IS the profile's own
form) but lacks the section markers, paired with bogus
`descriptor_sha256`/`body_sha256`, passed the api validator (recompute silently
skipped) while closure + provenance held. This is the profile's own capture form,
so D4 requires the recompute. **Fix:** once the magic matches, the markers MUST be
present — absent markers now fail closed (`validate_api_snapshot.py:136-167`). New
regression fixture `examples/negative/api-snapshot-magic-no-markers.toml` (+ capture
`examples/negative/captures/magic-no-markers.capture`) wired into CI
(`validate.yml` "Negative fixtures" step). Verified:

```
$ python3 validators/validate_api_snapshot.py --repo-root . examples/negative/api-snapshot-magic-no-markers.toml
API-SNAPSHOT VALIDATION FAILED  (RKV01: magic present, section markers absent)
exit=1
$ python3 validators/validate_provenance.py examples/negative/api-snapshot-magic-no-markers.toml --repo-root .
PROVENANCE VALIDATION FAILED  (source_bytes 181 != 180; per examples/negative/ convention)
exit=1
$ python3 validators/validate_closure_root.py examples/negative/api-snapshot-magic-no-markers.toml
CLOSURE-ROOT VALIDATION PASSED   (source-only fold correct)
exit=0
$ python3 validators/validate_closure_root.py --discover .
CLOSURE-ROOT VALIDATION PASSED   (positive sweep still green)
exit=0
```
Positive `examples/minimal-api-snapshot.toml` unchanged (markers present → recompute → PASS).

**Codex — finding REBUTTED with design evidence (not a defect).** Codex reported
`snapshot.witness.attestation_sha256` is type-checked but never recomputed against
the shipped `.attestation`, so a wrong attestation digest passes. This is the
documented design boundary, not a gap:
- design-record **D1**: "`attestation_sha256` pins a **separate** witness artefact …
  none of the three [descriptor/body/attestation] are folded at 0.1.0" — deferred
  per `spec.md §12.8`.
- **D4**'s RKV01 covers only the capture's request-descriptor and response-body
  sub-parts; the attestation is a separate artefact, not a capture sub-part.
- `validate_api_snapshot.py` docstring (L42-43): "It does NOT re-fetch the URL,
  **verify the witness**, or resolve the attester — those are RUNTIME-SPEC." Pinning
  (not recomputing/verifying) `attestation_sha256` is the same RUNTIME-SPEC boundary
  as not re-fetching the URL.
Recomputing it would override a documented 0.1.0 scope decision; flagged for Werner's
manual review rather than changed unilaterally.

**Outcome — both reviewers UNCONDITIONAL APPROVAL at HEAD 5bc28d5.** Grok reproduced
its r1 exploit (shipped fixture + a fresh magic-no-markers capture) and confirmed both
now fail closed on RKV01, the positive is unchanged, and the full battery + taplo are
green. Codex independently verified the RKV01 fix and the attestation citations
(design-record D1:19 / D4:83, validator docstring:42, api-snapshot-kind.toml:86/95,
spec.md §12.8:1161/1180) and agreed the attestation behavior is a documented 0.1.0
boundary, not a blocker.

**Non-blocking observation (Grok), for a future schema_version:** `verify_subparts`
locates the capture sub-parts by raw first-occurrence substring split, so a producer
that *smuggles* the section markers into the header area with chosen bytes could make
the recompute extract attacker-positioned slices. This is pre-existing (identical to
the pre-fix recompute branch), orthogonal to this fix, and not exploitable for the
shipped artefacts; hardening the capture parser to anchor the markers is a candidate
follow-up, not a 0.1.0 blocker.

## Third pass — reference-database propagation (2026-06-18, CI manifest-drift)

After the PR opened, the CI `validate` job failed at the **Manifest drift** step
(`validators/check_manifest_drift.sh`). The validators and the prior review passes
exercise the spec validators but NOT the count-mirror gate, so this latent gap in
the original profile work surfaced only on the PR: the new `com.verivus.runtime`
ontology (1 template_kind, 2 closed vocabularies / 6 values) was never propagated
into `reference/database/`. The new-profile diff touched `reference/` zero times.

Fix — propagate the profile across every count-mirror surface
(`validators/check_attribute_values.py` gates all of them):
- `MANIFEST.toml [counts]`: `template_kinds` 20→21, `attribute_vocabularies` 46→48,
  `attribute_values_declared` 202→208, `attribute_values_closed` 109→115
  (both new vocabs `extensible = false`).
- `expected_seed_counts` ×3 engines (postgres/sqlite/duckdb): `kind_descriptor`
  +1, `attribute_vocabulary` +2, `attribute_value_allowed` +6 (138→144).
- `expected_node_counts.graph.KindDescriptor` 20→21; `expected_footer_counts.rdf`
  21/48; `expected_triple_counts.rdf.schema` 1400→1434.
- Seed rows added to `postgres/`, `sqlite/`, `duckdb/` `seed.sql`: 1 `kind_descriptor`
  (`api-snapshot`), 2 `attribute_vocabulary` (`witness_scheme`, `attester_observed`),
  6 `attribute_value_allowed` rows — mirroring the existing `cost` profile rows.
- `rdf/schema.ttl` regenerated by `tools/dagtoml-rdf` (footer + triples authoritative).
- `tools/dagtoml-duckdb/src/main.rs` and `tools/dagtoml-duckdb-go/main.go`
  `EXPECTED_COUNTS` hardcodes bumped to match.

Verified:
```
$ REPO_ROOT=$(pwd) bash validators/check_manifest_drift.sh
manifest-drift check ... 21/27/31/48 all ==
rdf-drift check ... 21/27/31/48 all ==
COUNT-MIRROR OK — every surface agrees with reality.
OK — manifest matches ontology + every count-mirror surface agrees
exit=0
```
`entity_kinds`/`relation_predicates` unchanged (D2 entity-light: `entities_introduced
= []`, no namespaced relations). Positive example + closure `--discover .` + taplo
remain green; the api-snapshot RKV01/02/03 battery is unaffected.

## Fourth pass — schema enum + ruff (CI surfaced two more, post-propagation)

With manifest-drift fixed, CI's `validate` job advanced and surfaced two further
issues; the cross-LLM board (Codex) independently caught the first by *loading the
DuckDB seed* rather than only running the count gate.

1. **Schema rejects the new profile layer (Codex BLOCKER — fixed).** The
   `kind_descriptor.layer` allowlist (`spec_layer` enum in postgres/duckdb,
   `CHECK` in sqlite) stopped at `profile:cost`, so the seed rows for
   `api-snapshot` (`layer = 'profile:com.verivus.runtime'`) failed to load:
   `Conversion Error: Could not convert string 'profile:com.verivus.runtime' to
   UINT8`. The count gate doesn't load the DB, so it passed while the seed was
   broken. Fix: add `profile:com.verivus.runtime` to the enum/CHECK in all three
   schemas. **Verified by actually loading it** — `dagtoml-duckdb` build + verify:
   `OK — counts match expected (21 / 27 / 31 / 48 / 144)`; a raw `duckdb` load of
   `schema.sql`+`seed.sql` exits 0 with the api-snapshot kind, both vocabs, and 6
   value rows present.
2. **ruff S110 (`try`-`except`-`pass`) — fixed.** Pre-existing in
   `validate_api_snapshot.py:main()` (the snapshot-counter), masked until CI got
   past manifest-drift. Replaced with `contextlib.suppress(Exception)` (identical
   behaviour, lint-clean). `ruff check --select S,F --ignore S404 --line-length 120
   validators/` → "All checks passed!".

Stale count comments in the three touched `seed.sql` headers and the
`graph/schema.cypher` note were refreshed to 21/48/144 and to record that
`api-snapshot` joins the existing **documented** disclosure/cost graph-seed
deferral.

**Rebutted, with evidence (not defects in this change):**
- *`instance_file.framework_profile` CHECK (`IN ('agent-assurance','AGDF')`).*
  Not exercised by the seed (which inserts ontology metadata, not instance
  documents — the DuckDB load + tool-verify pass without it), and pre-existing
  incomplete for **disclosure and cost** as well, not just com.verivus.runtime.
  Whether the reference DB should ingest non-agent-assurance *instances* is a
  separate, profile-agnostic reference-DB scope decision, not part of landing this
  profile. Flagged for Werner.
- *`graph/schema.cypher` lists 15 KindDescriptor nodes, not 21.* Documented
  intentional partial (cypher header NOTE: disclosure/cost/profile-descriptor
  kinds "tracked as a follow-up"); the property-graph seed is illustrative and
  `check_attribute_values.py` compares `expected_node_counts` to the ontology, not
  to the UNWIND rows. api-snapshot joins that existing deferral; completing it
  would require seeding unrelated disclosure/cost kinds.
