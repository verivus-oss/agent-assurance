## Summary

Implementation dispositions B1, B2, B3, R1, R2, and R3 are closed against the bytes at `b7e2472`. One cross-cutting required item is not closed: `CHANGELOG.md` does not list every changed file. Terminal classification: `concrete_unresolvable_blocker`.

Scope note: `b7e2472`'s actual parent is `c4286fb`, not `8a63abb`; `8a63abb..b7e2472` contains 2 commits. I used `git show b7e2472` for commit-level checks.

## B1 disposition

Closed.

Evidence:
- `profiles/agent-assurance/ontology.toml:349-356` defines `attribute = "subject_class"`, `applies_to = "gate-decision"`, values including `"self-modification"`, with `ijb_primitive = "constraint"` and `ijb_constraint_type = "structural"`.
- `profiles/agent-assurance/gate-decision-kind.toml:53-56` documents `[decision].subject_class` in ROOT SHAPE.
- `profiles/agent-assurance/gate-decision-kind.toml:120-157` required fields contain only `meta.template_kind`, `meta.framework_profile`, `decision.verdict`, `decision.evidence_root`, `decision.evidence_root_algorithm`, and `decision.decided_at`; `subject_class` is not required.
- `profiles/agent-assurance/gate-decision-kind.toml:199-202` makes INV06 trigger on the artifact value `decision.subject_class = "self-modification"`.
- `examples/self-modification-gate-decision.toml:34-38` provides `subject_class = "self-modification"` plus the four attribution fields.

## B2 disposition

Closed.

Evidence:
- `profiles/agent-assurance/gate-decision-kind.toml:97-101` says provider and family must both differ, and explicitly says same-provider/different-family and different-provider/same-family both fail.
- `profiles/agent-assurance/gate-decision-kind.toml:201` uses `MUST satisfy BOTH ... AND ...` and repeats that both mixed cases fail.
- `grep -n 'and/or' profiles/agent-assurance/gate-decision-kind.toml` exited 0 with no matches.

## B3 disposition

Closed.

Evidence:
- `profiles/agent-assurance/tiers/solo.toml:32-35` C02 excludes self-modification gate-decisions from AI self-sign permission and includes `gate-decision-invariant:INV06@1`.
- `profiles/agent-assurance/tiers/solo.toml:56-59` C05 excludes self-modification gate-decisions from the solo single-signer rule and includes `gate-decision-invariant:INV06@1`.
- `python3 validators/validate_review_readiness.py profiles/agent-assurance/tiers/solo.toml` exited 0: `REVIEW READINESS VALIDATION PASSED`.

## R1 disposition

Closed.

Evidence:
- Required fields block at `profiles/agent-assurance/gate-decision-kind.toml:120-157` excludes all four attribution fields.
- INV06 is the conditional-required site: `profiles/agent-assurance/gate-decision-kind.toml:201` requires all four attribution fields only when `decision.subject_class = "self-modification"`.
- `git show b7e2472 -- examples/minimal-gate-decision.toml --stat --patch` exited 0 with no diff.
- `python3 validators/validate_ijb_conformance.py examples/minimal-gate-decision.toml --repo-root .` exited 0.
- `profiles/agent-assurance/gate-decision-kind.toml:206-210` says the pre-INV06 minimal shape remains valid because INV06 only triggers on `subject_class = "self-modification"`.

## R2 disposition

Closed.

Evidence:
- `profiles/agent-assurance/overview.md:72-89` has the Scope and posture section with the multi-provider operating assumption and rationale.
- `profiles/agent-assurance/overview.md:90-103` covers impact for air-gapped, single-vendor, regulated, and sealed deployments, with coherent options.
- `profiles/agent-assurance/overview.md:105-113` gives migration guidance: pre-INV06 gate-decisions remain valid, new self-modification gates need attribution, and solo tier surface changed.
- `profiles/agent-assurance/tiers/README.md:27` references INV06 in the solo row.
- `profiles/agent-assurance/tiers/README.md:33-40` makes the cross-tier rule profile-level and tied to multi-provider scope.

## R3 disposition

Closed.

Evidence:
- `grep -rni 'agent-federator\|federator' profiles/ SPEC.md core/` exited 0 with zero matches.
- Runtime contract language is topology-open: `profiles/agent-assurance/gate-decision-kind.toml:101-105` limits SPEC validation to field presence, vocabulary membership, and inequality predicates, leaving identity attestation to RUNTIME-SPEC.
- `profiles/agent-assurance/ontology.toml:363` describes provider identity as opaque to SPEC and verification as runtime-defined.

## Reference DB plumbing

Confirmed.

- `python3 validators/check_attribute_values.py` exited 0 and printed `COUNT-MIRROR OK`.
- `bash validators/check_manifest_drift.sh` exited 0 and printed `OK`.
- `tools/dagtoml-rdf/target/release/dagtoml-rdf verify -o reference/database/rdf/schema.ttl` exited 0 and reported `parsed 1400 triples`.
- Cross-engine rows are consistent:
  - Postgres uses `ARRAY[...]` / `ARRAY[]` and adds 3 vocab rows at `reference/database/postgres/seed.sql:217-219`, 22 value rows at `reference/database/postgres/seed.sql:362-385`.
  - DuckDB uses `[...]` and adds 3 vocab rows at `reference/database/duckdb/seed.sql:151-153`, 22 value rows at `reference/database/duckdb/seed.sql:277-298`.
  - SQLite uses `json_array(...)` and adds 3 vocab rows at `reference/database/sqlite/seed.sql:167-169`, 22 value rows at `reference/database/sqlite/seed.sql:293-314`.

## No new defects

Finding N1, severity required/blocking: `CHANGELOG.md` does not list every changed file. `CHANGELOG.md:19-44` introduces "Files changed" and lists profile/example files, but omits `reference/database/MANIFEST.toml`, all three seed files, `reference/database/rdf/schema.ttl`, `tools/dagtoml-duckdb-go/main.go`, and `tools/dagtoml-duckdb/src/main.rs`.

Other checks passed:
- `git show --stat b7e2472` shows exactly 14 files changed, 372 insertions, 33 deletions.
- `git show --format='' --name-only b7e2472 | grep -E '^(SPEC\.md|core/|validators/)'` returned no matches.
- `python3 validators/validate_closure_root.py --discover .` exited 0 over 75 files.
- SPEC §5 remains non-contradictory: `SPEC.md:372-376` delegates machine-readable invariant contracts to kind descriptors and ontology entries; INV06 is added there.
- `git show --format='' b7e2472 | grep -iE 'json schema|jsonschema|json-schema'` returned no matches.
- New example is referenced from `profiles/agent-assurance/gate-decision-kind.toml:212-216`.

## Process checks

- Active-user migration / behavior-change guidance: covered and closed by R2; see `profiles/agent-assurance/overview.md:105-113`.
- No historical dated spec retconned: `git show --format='' --name-only b7e2472 | grep '^docs/reviews/'` returned no matches; commit modifies current profile/reference surfaces only.
- Claimed tests actually run: independently reran more than three bundle commands. Exit 0 for kind descriptor validation, IJB conformance on ontology, IJB conformance on gate-decision-kind, IJB conformance on new example, review-readiness on solo tier, closure-root discovery, count-mirror, manifest drift, and RDF verify.

## Terminal verdict

`concrete_unresolvable_blocker`

Rationale: the six r1 dispositions are closed by concrete file bytes and validators, but the cross-cutting changelog requirement is not: `CHANGELOG.md:19-44` claims a changed-file list while omitting seven files changed by `b7e2472`.
