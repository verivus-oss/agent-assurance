# Verification Report — session 2026-06-05-policy-mode-design (round 2)

Generated 2026-06-04T16:39:44Z. Round-1 verdicts: codex REVISE (5 findings), grok REVISE (7 findings) — persisted as round1_codex_review.md / round1_grok_review.md. All round-1 findings addressed or rebutted below; gemini round 1 pending.

## Round-1 finding dispositions
- codex-1/grok-2 (tracked_files FPs): ACCEPTED — applies_to narrowed to commit_messages+pr_title+pr_body; DESIGN.md §3a; exempt_paths widened and documented inert.
- codex-2 (ANY-vendor claim unimplemented): ACCEPTED — statement re-scoped to pattern-list-in-file; patterns generalised (+perplexity/codeium/tabnine/cody/ai/assistant/agent/bot + email-local heuristic); 12-case table below incl. the three reviewer counterexamples now matching and three new human-FP guards not matching.
- codex-3 (squash surface): ACCEPTED — pr_title stream added; DESIGN.md §7a.
- codex-4/grok-1 (§1 factual errors): ACCEPTED — §1 corrected: #23 OPEN; #21 carries initiator-authored wp1 bundle.
- codex-5 (labels): ACCEPTED — §2/§10/§11/§12 labelled.
- grok-3 (structural contract unspecified): ACCEPTED — §5a algorithm.
- grok-4 (workflow coexistence): ACCEPTED — §7b three-stage migration.
- grok-5 (runner redesign): ACCEPTED — §8 rewritten with case.toml schema + expected_exit.
- grok-7 (stage-0 attack): ACCEPTED — §6 two-PR bootstrap with diff-scope cap.
- grok-6 (reverts/pr_title/github-noreply): ACCEPTED — §8 revert fixture (documented REJECT); pr_title stream; noreply heuristic tested below.
- NEW (self-caught in round 2): angle-bracket regex literals collide with the placeholder gate — pattern rewritten angle-free; DESIGN.md §5b; fixture added to §8 minimum set.

## Artifacts (changed vs origin/main e8e292c)
```
 M docs/reviews/2026-06-05-policy-mode-design/DESIGN.md
 M docs/reviews/2026-06-05-policy-mode-design/VERIFICATION_REPORT.md
 M policy/REPO_POLICY.toml
?? docs/reviews/2026-06-05-policy-mode-design/round1_codex_review.md
?? docs/reviews/2026-06-05-policy-mode-design/round1_grok_review.md
?? go-validator
```
## IMPLEMENTATION_DAG.toml
### rs (exit 0): DAGTOML VALIDATION PASSED (rust primary)
### go (exit 0): DAGTOML VALIDATION PASSED (go primary)
### py (exit 0): IMPLEMENTATION DAG VALIDATION PASSED
## policy/REPO_POLICY.toml
### rs (exit 0): DAGTOML VALIDATION PASSED (rust primary)
### go (exit 0): DAGTOML VALIDATION PASSED (go primary)

## Pattern behaviour (12 cases incl. round-1 counterexamples)
PASS 'Co-Authored-By: Claude Opus <noreply@anthropic.com>' match = True
PASS 'we removed the Co-Authored-By trailers from history' match = False
PASS 'Generated with Claude Code' match = True
PASS 'Generated with great care by Werner' match = False
PASS 'Co-authored-by: Jane Smith <jane@example.com>' match = False
PASS 'co-authored-by: GitHub Copilot <copilot@github.com>' match = True
PASS 'Co-authored-by: AI Assistant <bot@example.com>' match = True
PASS 'Co-authored-by: Perplexity <bot@perplexity.ai>' match = True
PASS 'Co-authored-by: Codeium <bot@codeium.com>' match = True
PASS 'Co-authored-by: Bob <bob@users.noreply.github.com>' match = False
PASS 'Co-authored-by: Botond Nagy <botond@example.com>' match = False
PASS 'Co-authored-by: Aida Smith <aida@example.com>' match = False
ALL 12 PASS
