# U10 round-3 implementation review verdict: grok

Job: 2fd9ee11-9a66-489c-b11e-fc22cae3739d (llm-gateway async, effort high,
bypassPermissions, worktree /srv/repos/external/verivus-oss/aa-r3-grok @
987a4e8, ~3.4 min wall). Iterations: 1. Evidence basis: rebuilt both
primaries; all five R2-1 fixtures (py=1 rs=1 go=1 each); R2-2 symlink root
(0/0/0); clean-worktree CI discover at three refs (79 @ c1be19c, 80 @
bef13ad, 80 @ 987a4e8); guard script run (PASSED, exit 0), CI wiring at
validate.yml:860-869, executable bit 100755; two mutation tests (Go
non-following walk: GUARD 3 fails as it should; Python $-anchor revert:
guard still PASSES, proving GUARD 4 vacuous); adversarial constructions
A1-A5 under /tmp/crfp-r3-grok/adversarial/ (symlink loop, name edge matrix,
symlink-alias dup, double-hop symlink, TOML-invalid dup peer, hostile
TMPDIR); make dagtoml-conformance 29 PASSED; clippy/fmt/vet/taplo all clean;
git diff --check clean at merge-base 489d649..HEAD.

## FINAL VERDICT: FIXES REQUIRED

Per-R2 table: R2-1 yes (code), R2-2 yes, R2-3/5/8 yes for record+tree with
one stale neighbour, R2-4 PARTIAL (guard 3 real, guard 4 decorative),
R2-6 yes, R2-7 yes.

New findings:
1. R3-1 (P1): GUARD 4 of validators/check_pin_resolution_guards.sh:107-119
   is vacuously true. write_profile always sets
   contained_kinds = ["pinned-note"] but GUARD 4's root never installs a
   pinned-note-kind.toml (GUARD 3 does, at :100-101), so all three legs
   exit 1 on INV05 kind resolution regardless of the name-anchor fix.
   Mutation proof: with the $ anchor reverted in an untracked copy, the
   stock guard still prints PIN-RESOLUTION GUARDS PASSED; with a complete
   root (kind descriptor present) fixed py=1 and mutated py=0. Repro:
   /tmp/crfp-r3-grok/findings/R3-G4-vacuous/ (repro.sh, complete-root/,
   incomplete-root/). Fix: install the kind descriptor in the GUARD 4 root
   (mirror GUARD 3) or strip contained_kinds/closure_records so the name
   regex is the only failure mode; optionally assert on the error text.
2. R3-2 (P2): docs/planning/closure-record-form-promotion/
   evidence-matrix.toml:64 (known_exclusions for E04) still says "25-case
   corpus"; runner and tree are 29. 02-verification-record.md itself is
   correct.
3. R3-3 (P3): guard exits opaquely at mktemp when TMPDIR is unwritable;
   hygiene only.

No new triad divergence: symlink loop 0/0/0 no hang; name-edge matrix
(trailing space/tab/CR, lone \n, interior newline, leading space, empty)
1/1/1 everywhere; double-hop symlink 0/0/0; symlink-alias duplicate 1/1/1;
TOML-invalid duplicate peer silently skipped by all three (agreement,
recorded as a parse-skip caveat, not a divergence).

Worktree left clean (git status: nothing to commit).

Orchestrator adjudication: R3-1 independently reproduced by the coordinator
BEFORE grok's verdict landed (same mutation, same root-completion proof,
same conclusion); R3-2 confirmed by direct read of evidence-matrix.toml:64.
No grok claim rejected.

Full raw output preserved by the gateway under job
2fd9ee11-9a66-489c-b11e-fc22cae3739d (llm_job_result).
