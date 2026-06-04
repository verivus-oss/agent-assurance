# Verification Report — session 2026-06-05-policy-mode-design (round 6)

Generated 2026-06-04T17:07:02Z. Verdict history:
r1: codex REVISE(5) / grok REVISE(7) / gemini REVISE(5)
r2: codex REVISE(2) / grok REVISE(6) / gemini malfunction->retry REVISE(4)
r3: codex APPROVE(9704747) / grok REVISE(2)
r4: codex REVISE(1: tracked scratch debris) / grok APPROVE-UNCONDITIONAL(d443abf)
r5: codex REVISE(1: stale-artifact presence bypass) / grok APPROVE HOLDS(009be2b) / gemini bare-verdict REJECTED by initiator (no evidence)
r6 dispositions: codex5-1 ACCEPTED — scan-files bound to changed paths, validator refuses uncounted scan-files (defence in depth), stale-artifact and unbound-scan-file fixtures added; grok5 notes dispositioned (examples/conformance exclusion documented in 5a rule 6)

## Round-4 dispositions (this commit)
- codex4-1 / grok4 note (scratch debris): ACCEPTED — reviewer probe scripts and the committed go-validator binary removed from tree and index.
- gemini2-1 (vendor tokens in legal names): DOCUMENTED as section 12 R5 with matrix cases 23-24 as intentional REJECTs and the reword appeal path (grok r4 recommended exactly this disposition).
- gemini2-2 (GitHub automation rejected): ACCEPTED — 'bot' dropped from pattern 3; cases 20-21 (dependabot/github-actions) ACCEPT.
- gemini2-3 (prose capture): ACCEPTED — generated-with window 40->12 chars; case 22 ACCEPTS; title-tail (14) and quoting (17) still REJECT.
- gemini2-4 (contract 2 dead code): ACCEPTED — section 5a rule 5 presence enforcement; required_when_changed globs in the policy file; structural shim invocation in section 7; presence fixture in section 8. Zero-scanned-files is a verdict when spec surfaces changed.

## Machine checks
- pattern-1 vendor group == pattern-4 vendor group: True
- validators: rs+go PASS (policy), rs/go/py PASS (DAG) — re-run this commit

## Pattern behaviour — 24 cases
PASS 'Co-Authored-By: Claude Opus <noreply@anthropic.com>'                                      match = True
PASS 'we removed the Co-Authored-By trailers from history'                                      match = False
PASS 'Generated with Claude Code'                                                               match = True
PASS 'Generated with great care by Werner'                                                      match = False
PASS 'Co-authored-by: Jane Smith <jane@example.com>'                                            match = False
PASS 'co-authored-by: GitHub Copilot <copilot@github.com>'                                      match = True
PASS 'Co-authored-by: AI Assistant <bot@example.com>'                                           match = True
PASS 'Co-authored-by: Perplexity <bot@perplexity.ai>'                                           match = True
PASS 'Co-authored-by: Codeium <bot@codeium.com>'                                                match = True
PASS 'Co-authored-by: Bob <bob@users.noreply.github.com>'                                       match = False
PASS 'Co-authored-by: Botond Nagy <botond@example.com>'                                         match = False
PASS 'Co-authored-by: Aida Smith <aida@example.com>'                                            match = False
PASS 'Co-authored-by: Agent Smith <agent.smith@example.com>'                                    match = False
PASS 'feat: tidy validators — Generated with Claude Code'                                       match = True
PASS 'Generated with Perplexity'                                                                match = True
PASS 'Generated with Codeium'                                                                   match = True
PASS 'the footer said generated with claude code'                                               match = True
PASS 'Generated with Assistant'                                                                 match = True
PASS 'Co-authored-by: Cody Johnson <cody@example.com>'                                          match = False
PASS 'Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>'      match = False
PASS 'Co-authored-by: github-actions[bot] <github-actions[bot]@users.noreply.github.com>'       match = False
PASS 'This bug was generated with a script written by Devin'                                    match = False
PASS 'Co-authored-by: Jean-Claude Van Damme <jc@example.com>'                                   match = True
PASS 'Co-authored-by: Sourcegraph Cody <cody@sourcegraph.com>'                                  match = True
ALL 24 PASS

Cases 17, 23, 24 are documented intentional REJECTs (section 3 quoting trade-off; section 12 R5).
