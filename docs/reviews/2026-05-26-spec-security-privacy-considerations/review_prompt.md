# Review Prompt

You are reviewing a pre-publication correction for `verivus-oss/agent-assurance`.

Do not accept Codex's summary as evidence. Verify claims by inspecting the repository, the exact diff, and validation command output.

## Corrective-Program Spec

Use `docs/reviews/2026-05-26-spec-security-privacy-considerations/verification_report.toml` as the corrective-program spec.

## Exact Scope

Base commit: `12b9473`

Changed-file list under review:

- `SPEC.md` / `spec.md` (working tree currently has `SPEC.md -> spec.md`; inspect the current `spec.md` bytes)
- `CHANGELOG.md`
- `docs/reviews/2026-05-26-spec-security-privacy-considerations/verification_report.toml`
- `docs/reviews/2026-05-26-spec-security-privacy-considerations/review_bundle.toml`
- `docs/reviews/2026-05-26-spec-security-privacy-considerations/reviewer_roster.toml`
- `docs/reviews/2026-05-26-spec-security-privacy-considerations/permission_grant.toml`
- `docs/reviews/2026-05-26-spec-security-privacy-considerations/review_prompt.md`
- `docs/reviews/2026-05-26-spec-security-privacy-considerations/local_validation.md`

Dynamic audit evidence such as `job_ids.toml`, `raw_findings/*.md`, and
`terminal_decision.toml` is produced as the review proceeds and is not
part of this pre-dispatch reviewed-file list.

Review the exact diff with:

```bash
git diff HEAD --find-renames -- SPEC.md spec.md CHANGELOG.md docs/reviews/2026-05-26-spec-security-privacy-considerations/verification_report.toml docs/reviews/2026-05-26-spec-security-privacy-considerations/review_bundle.toml docs/reviews/2026-05-26-spec-security-privacy-considerations/reviewer_roster.toml docs/reviews/2026-05-26-spec-security-privacy-considerations/permission_grant.toml docs/reviews/2026-05-26-spec-security-privacy-considerations/review_prompt.md docs/reviews/2026-05-26-spec-security-privacy-considerations/local_validation.md
```

## Required Checks

Verify C01-C06 in `verification_report.toml` against the actual docs.

Run or inspect the output of these validation commands:

```bash
taplo lint
python3 validators/validate_closure_root.py --discover .
bash validators/check_manifest_drift.sh
python3 validators/validate_profile_descriptor.py --repo-root . profiles/agent-assurance/PROFILE.toml profiles/disclosure/PROFILE.toml profiles/cost/PROFILE.toml
```

## Required Output

Return one terminal state:

- `unconditional_approval`
- `concrete_unresolvable_blocker`

If you find a resolvable issue, report it with file and line evidence, then do not approve. If all acceptance criteria and validations pass, approve unconditionally. Approval must be based on inspected code, tests, docs, and persistent evidence, not on intent or "should be fixed" language.
