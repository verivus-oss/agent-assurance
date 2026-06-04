# Verification Report — session 2026-06-05-policy-mode-design (round 3)

Generated 2026-06-04T16:50:49Z. Verdict history: r1 codex REVISE(5)/grok REVISE(7)/gemini REVISE(5); r2 codex REVISE(2)/grok REVISE(6)/gemini MALFUNCTION (empty stream, retried). All r2 findings dispositioned below.

## Round-2 finding dispositions
- codex2-1 (generated-with vendor list narrower): ACCEPTED — pattern 4 now carries the IDENTICAL vendor alternation as pattern 1; fixtures extended (Perplexity/Codeium generated-with now reject).
- codex2-2 / grok2-4 (Agent Smith FP): ACCEPTED — bare agent/bot dropped from name tokens (kept ai/assistant); agent dropped from email heuristic; 'Agent Smith <agent.smith@example.com>' now ACCEPTS (case 13).
- grok2-1 (§5a nonexistent fields): ACCEPTED — §5a rebound to template_kind=review-gate-decision, [roster].reviewers_completed, with live-instance citation; terminal_decision/INV06-quartet explicitly out of scope v1.
- grok2-2 (§6 stale changed-files): ACCEPTED — corrected to the three streams.
- grok2-3 (title-tail gap): ACCEPTED — generated-with pattern un-anchored, phrase-scoped with 40-char window; trade-off documented in §3 with both-direction fixtures (cases 14 and 17).
- grok2-5 (§10.5 ANY claim): ACCEPTED — decision rewritten to pattern-list-is-the-coverage.
- grok2-6 (mechanical stage-0): ACCEPTED — §6 adds git diff --name-only subset assertion in PR-A CI.
- grok note (shim block missing pr_title): ACCEPTED — pipe moved into the §7 code block.

## Validators (this commit)
### DAG rs: PASS
### DAG go: PASS
### DAG py: PASS
### policy rs: PASS
### policy go: PASS

## Pattern behaviour — 17 cases (12 prior + 5 round-2-driven)
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
PASS 'Co-authored-by: Agent Smith <agent.smith@example.com>' match = False
PASS 'feat: tidy validators — Generated with Claude Code' match = True
PASS 'Generated with Perplexity' match = True
PASS 'Generated with Codeium' match = True
PASS 'the footer said generated with claude code' match = True
ALL 17 PASS

Case 17 is the documented §3 trade-off: quoting the literal phrase adjacent to a vendor name in a SCANNED STREAM rejects by design; cite the short SHA instead.
