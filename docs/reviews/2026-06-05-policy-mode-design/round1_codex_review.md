# Round 1 review — Codex (job cf85ef7f, 2026-06-04T16:32Z)

Findings:

1. Policy false-positives legitimate policy prose in tracked files.  
Evidence: `policy/REPO_POLICY.toml:31-42` applies `REG:NO-AI-ATTRIBUTION` to `tracked_files` and exempts only the policy file plus `conformance/cases/policy/**`. The changed-file scan found `docs/reviews/2026-06-05-policy-mode-design/VERIFICATION_REPORT.md:56` matching pattern 3. Repo history also has `.github/workflows/no-ai-attribution.yml:4` matching the same pattern. This contradicts `DESIGN.md:58-59`, which claims prose discussion will not match and only actual footer lines do.

2. “ANY model/vendor” is not implemented by the draft policy.  
Evidence: `policy/REPO_POLICY.toml:25-27` and `DESIGN.md:56-57,173-175` claim any AI/LLM model/vendor/tool. The actual regexes at `policy/REPO_POLICY.toml:35-37` are finite alternations. Test output:  
`'Co-authored-by: AI Assistant <bot@example.com>' -> False`  
`'Co-authored-by: Perplexity <bot@perplexity.ai>' -> False`  
`'Co-authored-by: Codeium <bot@codeium.com>' -> False`

3. The N-1 gate design does not cover the final commit message surface that can land on `main`.  
Evidence: `DESIGN.md:129-134` scans `git log --format=%B "$BASE..$HEAD"` and PR body only; it does not scan PR title or the synthesized merge/squash commit message. `gh repo view` reports `mergeCommitAllowed=true`, `squashMergeAllowed=true`, and `rebaseMergeAllowed=true`, so the final default-branch commit message can differ from the PR commit range. PR #25 demonstrates this: PR commit headline was `ci: pin checkout action by SHA in no-ai-attribution gate`, while merged commit `e8e292c` subject is `ci: pin checkout action by SHA in no-ai-attribution gate (#25)`.

4. The problem statement contains false repo-history claims.  
Evidence: `DESIGN.md:16-24` says PRs `#21–#25` merged and carried no `docs/reviews/` bundle. `gh pr view 23` reports `state=OPEN mergedAt=null`. `gh pr view 21` reports `state=MERGED ... docs_reviews_files=26`.

5. The document’s label claim is not true.  
Evidence: `DESIGN.md:4-5` says every section is labelled `VERIFIABLE` or `UNASSESSABLE`, but `rg` shows sections `## 2`, `## 10`, `## 11`, and `## 12` have no such label.

Positive checks reproduced: C1 and C2 validators passed; `REG:` reuse is semantically supported by `core/ontology.toml:75-82` and `spec.md:329-342`; the provided six-row regex behavior table passes in Python/Go/Rust-regex via `rg --engine=default`; RE2/lookaround/backreference claims were confirmed by Go `regexp` compile errors and Go docs. Source used for GitHub Actions event context: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows

VERDICT: REVISE
