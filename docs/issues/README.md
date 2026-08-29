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
| [ISS-002](2026-05-23-iss-002-graph-cypher-seed-incomplete.md) | `graph/schema.cypher` UNWIND data missing profile-descriptor + disclosure + cost + com.verivus.runtime | open | medium |
| [ISS-003](2026-05-23-iss-003-duckdb-hardcoded-counts-duplication.md) | `dagtoml-duckdb{,-go}` `EXPECTED_COUNTS` mirrors duplicate MANIFEST | open | low |
| [ISS-004](2026-05-24-iss-004-spec-reserved-kind-files-must-land-with-closure-root.md) | Spec-reserved-kind files MUST land with `closure_root` in the same commit | closed (79fe0aa) | medium |
| [ISS-005](2026-06-01-iss-005-tools-dags-unvalidated-inv01-mismatch.md) | Operational `tools/*-dag.toml` DAGs outside CI structural validation; gated-dag violates INV01 | closed (4176bf9) | medium |

## Conventions

- Filename: `YYYY-MM-DD-ISS-NNN-short-slug.md`
- IDs are monotonic, never reused.
- Closing an issue MUST add a `closed_by` line in the header pointing at the resolving commit SHA, and a closing-note paragraph at the end of the file.
- That SHA MUST resolve in this repository. `validators/check_commit_citations.py` fails on any commit-shaped token in `docs/issues/` or `validators/` that git cannot resolve and that is not recorded in `validators/unresolvable-commit-citations.toml`.
- No `closed_by` SHA in the table above resolves in this repository, for two different reasons. ISS-001 through ISS-004 predate the root commit `eccdcab` (2026-05-27) and cite the pre-mint tree. ISS-005 postdates it but cites commits made on a branch that was squash-merged and deleted, which no ref reaches. All thirteen are enumerated with reasons in the baseline file.
- Verify a citation with `git for-each-ref --contains <sha>`, not `git rev-parse`. A local clone can still hold objects that no ref reaches, so `rev-parse` succeeds there and fails for everyone else. That is how ISS-005's two citations were first recorded as resolving.
- An issue marked `resolved` MUST keep its safeguard section pointing at the live CI gate or convention that prevents recurrence.
