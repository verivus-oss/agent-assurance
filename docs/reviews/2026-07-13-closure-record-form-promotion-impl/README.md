# Implementation review evidence: closure-record-form promotion (U10)

Review of the U03-U09 implementation stack (see
`docs/planning/closure-record-form-promotion/research/02-verification-record.md`
for the commit table), run 2026-07-13 via the multi-LLM gateway per the
no-self-approval rule. Reviewers built both primaries themselves, ran
all sweeps, and constructed adversarial repo-roots; the orchestrating
session reproduced every load-bearing finding before acceptance
(`orchestrator-verification-log.md`).

## Verdicts

| Reviewer | Final verdict | Items |
|---|---|---|
| codex | APPROVAL WITH REQUIRED FIXES | 6 |
| gemini | APPROVAL WITH REQUIRED FIXES | 2 |
| grok | APPROVAL WITH REQUIRED FIXES | 4 |

No blocker; no unconditional approval; consensus that the frozen
grammar is implemented consistently on the shipped corpus.

## Rounds 2-5 and gate closure

The gate iterated to closure across five rounds, all evidence in
`raw_findings/` (round-1 files keep their original names; later rounds
are prefixed `roundN-`):

| Round | Outcome | Fix commit |
|---|---|---|
| 1 | 3x approval-with-required-fixes (3 P1 triad divergences) | bef13ad |
| 2 | 3x approval-with-required-fixes (2 new P1: residual $-anchors, kind-candidate symlinks; counts re-pinned) | 987a4e8 |
| 3 | 3x fixes-required (guard 4 proven vacuous under mutation; corrected, guard 5 added) | 64fc137 |
| 4 | grok UNCONDITIONAL; codex/gemini required 2 documentation items | 57d1647 |
| 5 | codex and gemini UNCONDITIONAL at 57d1647 (comment-only delta from 64fc137, verified by both) | none needed |

**GATE CLOSED 2026-07-13: 3 of 3 unconditional external approvals**
(grok at 64fc137 with the delta to 57d1647 verified comment-only;
codex and gemini at 57d1647). Every verdict was issued by an external
reviewer; the initiator approved nothing. The behavioural regression
surface produced by the rounds is tracked in
`validators/check_pin_resolution_guards.sh` (16 checks, wired in CI)
plus four conformance cases; the guard-4 mutation-sensitivity proof is
recorded in round-3/4 evidence.

## Disposition

All required fixes were applied in the same stack (commit
"U10: apply implementation-review required fixes"): the three P1
triad-divergence defects (Python trailing-newline anchoring;
duplicate-profile-name pin shadowing, now fail-closed in all three;
Go symlinked-profile-dir discovery plus Python CLI-merge narrowing),
the P2 parity-matrix corpus additions and regressions, and the P3
record/doc corrections (79-file count, byte-identical qualification,
U09 deviation declaration, spec exactly-three-keys sentence, freeze
errata, parity-harness persistence, DAG statuses, EOF whitespace).
The full disposition with per-fix evidence is in the verification
record's "U10 review fixes" section.
