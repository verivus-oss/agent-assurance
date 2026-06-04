# Verification Report — session 2026-06-05-policy-mode-design (round 4)

Generated 2026-06-04T16:58:55Z. Verdict history:
r1: codex REVISE(5) / grok REVISE(7) / gemini REVISE(5)
r2: codex REVISE(2) / grok REVISE(6) / gemini malfunction (retried)
r3: codex APPROVE-UNCONDITIONAL (design phase) on 9704747 / grok REVISE(2) / gemini retry in flight

## Round-3 grok dispositions (this commit)
- grok3-1 (--law-root missing from §7 shim block): ACCEPTED — every policy-mode invocation now carries --law-root /tmp/law, with the rationale inline.
- grok3-2 (vendor alternation not identical; 'Generated with Assistant' accepted): ACCEPTED — pattern 4 group now byte-identical to pattern 1 group (machine-checked below); 'Generated with Assistant' rejects (case 18); the future conformance fixture comparing the two groups is named in §10.5.
- grok3 residual (contract-1 'ANY model' prose): ACCEPTED — reworded to pattern-list-is-the-coverage.
- grok3 fresh-attack observation (vendor-name-as-human-name): ADDRESSED for the worst case — 'cody' removed from the alternation entirely (common human given name; Sourcegraph rides on 'sourcegraph' + vendor-address patterns); case 19 guards it. 'grok'/'bard' retained: vanishingly rare as legal names; appeal path is rewording.

## Machine checks (this commit)
- pattern-1 vendor/term group == pattern-4 group: True (extracted and compared programmatically)
- 'cody' absent from all patterns: True
- validators: rs PASS, go PASS (policy file); rs/go/py PASS (IMPLEMENTATION_DAG.toml)

## Pattern behaviour — 19 cases
PASS 'Co-Authored-By: Claude Opus <noreply@anthropic.com>'          match = True
PASS 'we removed the Co-Authored-By trailers from history'          match = False
PASS 'Generated with Claude Code'                                   match = True
PASS 'Generated with great care by Werner'                          match = False
PASS 'Co-authored-by: Jane Smith <jane@example.com>'                match = False
PASS 'co-authored-by: GitHub Copilot <copilot@github.com>'          match = True
PASS 'Co-authored-by: AI Assistant <bot@example.com>'               match = True
PASS 'Co-authored-by: Perplexity <bot@perplexity.ai>'               match = True
PASS 'Co-authored-by: Codeium <bot@codeium.com>'                    match = True
PASS 'Co-authored-by: Bob <bob@users.noreply.github.com>'           match = False
PASS 'Co-authored-by: Botond Nagy <botond@example.com>'             match = False
PASS 'Co-authored-by: Aida Smith <aida@example.com>'                match = False
PASS 'Co-authored-by: Agent Smith <agent.smith@example.com>'        match = False
PASS 'feat: tidy validators — Generated with Claude Code'           match = True
PASS 'Generated with Perplexity'                                    match = True
PASS 'Generated with Codeium'                                       match = True
PASS 'the footer said generated with claude code'                   match = True
PASS 'Generated with Assistant'                                     match = True
PASS 'Co-authored-by: Cody Johnson <cody@example.com>'              match = False
ALL 19 PASS

Case 17 is the documented §3 trade-off (quoting the literal phrase next to a
vendor term in a scanned stream rejects; cite the short SHA instead).
Case 19 documents the cody-exclusion decision.
