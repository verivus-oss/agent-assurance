# U10 round-3 implementation review verdict: codex

Job: 5cefa03c-e243-41bc-aa05-f59dc4e9680d (llm-gateway async, codex
danger-full-access, worktree /srv/repos/external/verivus-oss/aa-r3-codex @
987a4e8, ~15.5 min, provider session 019f58b6-9d82-7b23-a77c-e7841a46b593).
Iterations: 1. Evidence basis: rebuilt both primaries under
/tmp/crfp-r3-codex; all five R2-1 fixtures triad-rejected (py=1 rs=1 go=1
each, exact commands cited); R2-2 root 0/0/0; CI discover replayed in three
self-created clean worktrees (79 @ c1be19c, 80 @ bef13ad, 80 @ 987a4e8,
logs under /tmp/crfp-r3-codex/root-count-*.log); guard baseline run (13/13,
exit 0, incl. spaced TMPDIR and odd cwd); THREE mutation tests (Python $
anchors: guard stays green, vacuous; pre-R2-2 bef13ad Go binary: guard 3
fails correctly; $-anchored closure validator copy: guard stays green, so
CLOSURE_ROOT_RE is not exercised at all); own symlink-loop root
(self-referential profiles/loop + symlinked real profile + symlinked core)
0/0/0 under timeout 5s; make dagtoml-conformance 29 PASSED; the CI
negative-agreement block (validate.yml:642-846) replayed, exit 0;
clippy/fmt/vet/taplo clean; git diff --check clean at merge-base 489d649;
worktree left clean including --ignored.

## FINAL VERDICT: FIXES REQUIRED

Per-R2 table: R2-1 yes (implementation), R2-2 yes, R2-3 NO (prose pins
incomplete), R2-4 NO (guard decorative for R2-1), R2-5 yes, R2-6 yes,
R2-7 yes, R2-8 yes.

Findings:
1. P1: the R2-4 guard does not protect R2-1. Guard 4's root declares
   contained_kinds = ["pinned-note"] (script line 48) but installs no kind
   descriptor (lines 107-119), and expect() maps every nonzero exit to a
   wanted rejection (line 30), so a genuine rollback to $ anchors stays
   green. Additionally no guard exercises CLOSURE_ROOT_RE
   (validate_closure_root.py:55): a $-anchored closure-validator copy also
   passes the guard. Repro fixtures:
   /tmp/crfp-r3-codex/guard-r2-1-vacuity/ (with-candidate root shows
   current-py=1 regressed-py=0 rs=1 go=1) and
   /tmp/crfp-r3-codex/guard-audit/*.log. A corrected untracked guard copy
   that adds the candidate fails the mutation as required.
2. P3: R2-3 prose pins incomplete. 02-verification-record.md:44-46 and
   :71-74 pin 79 to c1be19c by hash but say only "the review-fix ref" for
   the 80 measurements; bef13ad and 987a4e8 appear nowhere in the file.
   Repro: /tmp/crfp-r3-codex/findings/r2-3-prose-pin-repro.sh (exit 1,
   "missing measured-ref pin: bef13ad").
3. Non-blocking: running the guard with no arguments trips $1 under set -u
   (line 15) instead of printing usage.

Orchestrator adjudication:
- Finding 1 matches grok R3-1, gemini finding 1, and the coordinator's own
  pre-verdict mutation test; the CLOSURE_ROOT_RE extension is codex-unique
  and accepted (mechanism verified by reading the guard: no guard invokes
  a closure-root-format rejection path).
- Finding 2 contradicts grok's and gemini's acceptance of the R2-3 prose;
  coordinator re-read the record verbatim and sided with codex: grep for
  bef13ad|987a4e8 in 02-verification-record.md returns zero matches; "at
  and after the review-fix ref" is descriptive, not a hash pin. Grok and
  gemini over-accepted this item.
No codex claim was rejected.

Full raw output preserved by the gateway under job
5cefa03c-e243-41bc-aa05-f59dc4e9680d (llm_job_result).
