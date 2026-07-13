# U10 round-3 consolidated required fixes (FINAL; all three verdicts in)

Reviewed ref: 987a4e8 ("U10 round 2: complete the anchor and symlink
sweeps; executable pin-resolution guards"), fresh detached worktrees
aa-r3-{codex,gemini,grok}. Verdicts: codex FIXES REQUIRED, gemini FIXES
REQUIRED, grok FIXES REQUIRED. No unconditional approval; the U10 gate
does NOT close this round. Every load-bearing claim was
orchestrator-reproduced (the headline finding was reproduced by the
coordinator BEFORE any reviewer verdict landed).

## What is confirmed fixed (all three reviewers + orchestrator)

  R2-1 implementation: all five round-2 fixtures now triad-reject
        (py=1 rs=1 go=1); \Z anchors present in both Python validators.
  R2-2: /tmp/r2-codex-kind-symlink now 0/0/0 in profile mode; go uses
        os.Stat (main.go:~2866), rs uses Path::is_dir (main.rs:~3172).
  R2-3 measurements: 79 @ c1be19c, 80 @ bef13ad, 80 @ 987a4e8, each
        independently re-measured from clean worktrees by all four
        parties (three reviewers + coordinator) via the exact CI
        discover invocation.
  R2-5: record says 29 cases (02-verification-record.md:25, :75).
  R2-6: git diff --check clean over merge-base 489d649..HEAD.
  R2-7: stale "explicit --files set" prose gone; singleton-merge
        docstring correct.
  R2-8: conformance/README.md 2v/6i api-snapshot + 3v/18i
        implementation-dag matches the on-disk tree (.expected.toml
        sidecars excluded); 29 total.
  Regression: make dagtoml-conformance 29/29 in all three; CI
        negative-agreement block replayed clean (codex); clippy, fmt
        --check, go vet, taplo lint all clean; no triad divergence in
        any new adversarial construction (symlink loops incl.
        self-referential and double-hop: 0/0/0 no hang; name edge
        matrix trailing space/tab/CR, lone \n, interior newline,
        leading space, empty: 1/1/1; symlink-alias duplicate: 1/1/1
        fail-closed; TOML-invalid duplicate peer: skipped identically
        by all three).

## Required fixes

P1 (blocks the gate; found independently by all three reviewers AND
reproduced first by the orchestrator):

  R3-1. GUARD 4 of validators/check_pin_resolution_guards.sh (:107-119)
        is vacuous: write_profile always sets
        contained_kinds = ["pinned-note"] (:48) but guard 4's root never
        installs a pinned-note-kind.toml (guard 3 does, :100-101), so
        the fixture exits 1 on the INV05/contained_kinds resolution
        error regardless of the name-anchor fix, and expect() (:25-37)
        counts any nonzero exit as the wanted rejection. Mutation proof
        (three independent + orchestrator): revert \Z to $ in an
        untracked validator copy; the stock guard still prints
        PIN-RESOLUTION GUARDS PASSED. With the kind descriptor added,
        fixed py=1 / regressed py=0 and a corrected guard copy fails as
        required. Codex extension (accepted): no guard exercises
        CLOSURE_ROOT_RE either; a $-anchored closure-validator copy
        also passes. Fix: install the kind descriptor in guard 4's root
        (mirror guard 3) so the name regex is the only failure mode,
        optionally assert on the rejection message text, and add a
        closure-root trailing-newline case to the guard (or an
        equivalent tracked regression) so the R2-1 closure-side anchor
        has an executable guard too. Repro fixtures:
        /tmp/crfp-r3-grok/findings/R3-G4-vacuous/,
        /tmp/crfp-r3-codex/guard-r2-1-vacuity/,
        /tmp/crfp-r3-codex/guard-audit/*.log.
        [codex 1; gemini 1; grok R3-1; orchestrator-reproduced first]

P2:

  R3-2. docs/planning/closure-record-form-promotion/evidence-matrix.toml:64
        (known_exclusions for E04) still says "25-case corpus"; runner
        and tree are 29. [grok R3-2; orchestrator-confirmed by direct
        read]

P3:

  R3-3. 02-verification-record.md:44-46 and :71-74 pin 79 to c1be19c by
        hash but call the 80-count ref only "the review-fix ref";
        bef13ad and 987a4e8 appear nowhere in the file (grep 0). Name
        the measured refs explicitly. [codex 2; orchestrator sided with
        codex against grok/gemini acceptance]
  R3-4. Guard hygiene: unwritable TMPDIR dies opaquely at mktemp before
        any guard label (grok R3-3); zero-argument invocation trips $1
        under set -u instead of printing usage (codex non-blocking).

## Contested / adjudicated

  - R2-3 prose: grok and gemini accepted "pinned to refs"; codex
    rejected. Coordinator re-read the record verbatim and sided with
    codex (no hash for the 80 measurements). Filed as R3-3 at codex's
    own P3 severity since the measured values themselves reproduce.
  - Guard-4 severity: gemini filed P2, grok and codex P1. Consolidated
    at P1: it is the only executable regression for the R2-1
    profile-name anchor surface, and the R2-4 acceptance criterion was
    "actually assert what it claims".
  - No reviewer claim was rejected this round.

## Gate status

U10 gate remains OPEN. Land R3-1 (and R3-2/R3-3/R3-4 in the same pass;
they are one-line to few-line changes), then run round 4 as a narrow
confirmation: re-run the three mutation tests against the corrected
guard (anchor revert must now FAIL the guard; closure-anchor revert must
FAIL if a closure guard case is added), re-check the two prose sites,
and re-run the stock guard + conformance corpus for regressions.
