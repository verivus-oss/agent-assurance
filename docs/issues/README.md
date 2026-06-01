# Issue ledger

Filesystem-tracked issue list. Each issue is one markdown file with a
structured header (status, severity, opened) and prose sections for
symptoms / why-it-matters / safeguard / resolution-steps / acceptance.

Issues are NOT DAG-TOML documents and do not carry `closure_root` —
they use non-spec-reserved `template_kind` values (or none at all) and are out of
SPEC §12.1 conformance scope by design. They are project process
artefacts.

| ID | Title | Status | Severity |
|---|---|---|---|
| [ISS-001](2026-05-23-iss-001-self-approval-discipline.md) | Initiator self-approval violates `policy.approval` | closed (884f290) | high |
| [ISS-002](2026-05-23-iss-002-graph-cypher-seed-incomplete.md) | `graph/schema.cypher` UNWIND data missing disclosure + cost + profile-descriptor | open | medium |
| [ISS-003](2026-05-23-iss-003-duckdb-hardcoded-counts-duplication.md) | `dagtoml-duckdb{,-go}` `EXPECTED_COUNTS` mirrors duplicate MANIFEST | open | low |
| [ISS-004](2026-05-24-iss-004-spec-reserved-kind-files-must-land-with-closure-root.md) | Spec-reserved-kind files MUST land with `closure_root` in the same commit | closed (79fe0aa) | medium |
| [ISS-005](2026-06-01-iss-005-tools-dags-unvalidated-inv01-mismatch.md) | Operational `tools/*-dag.toml` DAGs outside CI structural validation; gated-dag violates INV01 | open | medium |

## Conventions

- Filename: `YYYY-MM-DD-ISS-NNN-short-slug.md`
- IDs are monotonic, never reused.
- Closing an issue MUST add a `closed_by` line in the header pointing at the resolving commit SHA, and a closing-note paragraph at the end of the file.
- An issue marked `resolved` MUST keep its safeguard section pointing at the live CI gate or convention that prevents recurrence.
