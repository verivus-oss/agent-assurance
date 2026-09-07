# Governance

DAG-TOML uses a maintainer-led specification process. The goal is a small
and predictable path from reported problem to reviewed change.

## Roles

- **Maintainers** review and merge changes, manage releases, and make
  final calls when consensus is not reached.
- **Contributors** report issues, propose changes, update examples, and
  improve validators.
- **Implementers** consume the specification and provide compatibility
  feedback from real tooling.

Maintainers are expected to explain material decisions in the issue or
pull request where the decision is made.

## Decision Types

| Change type | Required path |
| --- | --- |
| Typo, broken link, small wording fix | Pull request |
| Clarification with no behavior change | Issue plus pull request |
| New field, kind, relation, or allowed value | Issue plus pull request, examples, validators |
| Breaking semantic or file-shape change | Issue, migration note, major version bump |
| Security fix | Private report first, then coordinated disclosure |

## Review Expectations

Specification pull requests should be reviewable in one sitting. Large
changes should be split into smaller pull requests when possible:

- one pull request for a vocabulary addition,
- one for examples,
- one for validator implementation,
- one for editorial follow-up.

Maintainers may close proposals that do not identify a concrete
interoperability, validation, or user-facing problem.

## Releases

The current document maturity is `Draft Specification`. That
label describes the stability of the prose specification and examples;
it is not a Git tag and it is distinct from the `schema_version` field
inside DAG-TOML files.

While the specification remains a draft, the schema pin is a pre-1.0
semver string. The first public stable schema can become
`schema_version = "1.0.0"` when maintainers are ready to make that
compatibility promise. Ontology pins are monotonic positive integer
snapshots; core and profile ontologies stay at `1` until the first
vocabulary change after publication.

The public repository was minted at `v0.1.0` on 2026-05-27. Pre-1.0
release tags may either bind to the schema version, as `v0.1.0` does, or
use calendar-versioned UTC timestamps (`v<YYYY-MM-DD>T<HH-MM-SS>Z`) for
process-only snapshots that do not claim a new schema pin. Published
release notes must state which form they use.

After the public mint:

- Additive file-shape changes use a minor schema-version bump.
- Breaking changes use a major schema-version bump and a migration note.
- Changelog entries are grouped under the release version.
- Published release artifacts should cite the matching commit tag.

## Repository Controls

The public repository keeps `main` protected with required pull requests,
required status checks, force-push and deletion blocks, and CODEOWNERS-backed
review for maintainer-owned paths. Merge commits are the only allowed merge
method. Pull requests targeting `main` must be up to date with `main` before
they can merge.

The database gate rollout must enforce all seven GitHub Actions checks below.
The seventh requirement is pending until live configuration readback and
failed/skipped dependency checks complete:

- `validate (spec + reference validators + security scanning)`
- `commit-messages`
- `Analyze (actions)`
- `Analyze (go)`
- `Analyze (python)`
- `Analyze (rust)`
- `database-vocabulary-gate`

Those names are the job names from `.github/workflows/validate.yml`,
`.github/workflows/no-ai-attribution.yml`, `.github/workflows/codeql.yml`, and
`.github/workflows/database-vocabularies.yml`. Maintainers must enforce this
complete set on the `main-branch-protection` repository ruleset and on classic
branch protection for `main`. Renaming a required job without updating both
settings is a merge-gate break.

During the database gate rollout, retain the existing executed database checks
inside `validate` until both protection settings require the new aggregate and
failed and deliberately skipped dependency candidates demonstrate merge blocking.
The aggregate must run even when its dependencies fail or skip, and must reject
any dependency result other than success. A workflow or policy edit alone does
not complete this transition; record live configuration readback and check-run
evidence before removing the old coverage or closing the rollout issue.

Release tags should be annotated and signed when the maintainer tooling
supports it; release artifacts should include provenance and an SBOM before
the project is promoted beyond draft status.

## Issues and Discussions

Issues are for actionable work: spec defects, validator defects, example
gaps, and concrete proposals. Discussions, when enabled, are for
questions, implementation experience, and early design exploration.
