# U10 round-4 consolidated result (FINAL; all three verdicts in)

Reviewed ref: 64fc137 ("U10 round 3: de-vacuate guard 4, add closure_root
parity guard, pin counts to hashes"), fresh detached worktrees
aa-r4-{codex,gemini,grok}. Verdicts: grok UNCONDITIONAL APPROVAL, gemini
FIXES REQUIRED, codex FIXES REQUIRED. The U10 gate does NOT close this
round (2 of 3 withhold unconditional approval), but every remaining item
is a documentation/labeling nit; no behavioral finding of any severity
survived round 4.

## What is confirmed fixed (all three reviewers + orchestrator)

  R3-1: guard 4 is genuinely de-vacuated. All four parties ran the
        mutation test independently (validators copy, \Z reverted to $
        in UNPREFIXED_RE + REVERSE_DNS_RE, copied guard against shipped
        rs/go binaries): mutated run exits 1 failing on exactly
        "py newline name (want exit 1, got 0)", 15 ok + 1 fail, no other
        check flips; unmutated tracked script 16/16 ok,
        PIN-RESOLUTION GUARDS PASSED, exit 0. All six round-2/3 repro
        fixtures re-verified by all four parties: five newline files
        1/1/1 reject, kind-symlink root 0/0/0 accept.
  Guard 5 behavior: three-way rejection of the newline-smuggled
        closure_root reproduced by hand by codex and gemini (and via
        the guard by all). CLOSURE_ROOT_RE-only mutation confirmed NOT
        to flip the guard (codex, gemini, grok all verified), exactly
        as the verification record documents; the record's wording was
        judged honest by all three.
  R3-2: evidence-matrix.toml:64 says 29-case corpus; no stale 25
        anywhere in the file (codex: rg '\b25\b' exit 1).
  R3-3 measurements: 79 @ c1be19c, 80 @ bef13ad, 80 @ 987a4e8,
        re-measured from clean detached worktrees by all three
        reviewers via the exact CI discover invocation
        (validate.yml:379); hashes now present at the load-bearing
        sites (02-verification-record.md:44-45, :72-73).
  R3-4: zero-arg run exits 2 with the usage line on stderr; unwritable
        TMPDIR exits 2 with the explicit
        "mktemp failed (TMPDIR unwritable?)" message (all four parties).
  Regression: make dagtoml-conformance 29/29 in all three
        implementations (all four parties); CI negative-agreement block
        replayed clean (codex: 47 checks, Rust 14 / Go 14 / Python 19;
        gemini and orchestrator: equivalent replays clean);
        git diff --check over 489d649..HEAD clean (all).
  Hygiene: all three reviewer worktrees finished porcelain-clean;
        nested measurement worktrees removed.

## Remaining required fixes (consolidated)

P2/P3 (documentation/labeling only; both are few-line edits):

  R4-1. Guard 5 has NO in-script comment block; the parity-pin honesty
        label exists only in 02-verification-record.md:167. The round-4
        mandate (and the round-2/3 decorative-guard standard) requires
        the script itself to label guard 5 as a parity pin that is not
        mutation-detectable (a CLOSURE_ROOT_RE-only anchor revert still
        passes all 16 checks; proven by codex fixture
        /tmp/crfp-r4-codex/validators-root-anchor-mutated/, gemini, and
        grok). Fix: add a # comment immediately above
        validators/check_pin_resolution_guards.sh:133 stating the guard
        pins the three-way parity verdict and does not detect an
        anchor-only reversion because downstream raw-value equality
        also rejects. [gemini P2; codex P3; grok judged the omission
        acceptable; orchestrator pre-confirmed the absence before any
        verdict landed. Consolidated at P2-lite: land it.]
  R4-2. 02-verification-record.md:151 (round-2 recap bullet) still says
        "counts pinned to refs (79 at c1be19c, 80 after)" with no named
        ref for the 80, contradicting the round-3 claim at :172 that
        hashes are named "wherever counts are pinned". Fix: replace
        "80 after" with "80 at bef13ad and 987a4e8". [codex P3;
        orchestrator noticed the same line independently pre-verdict;
        grok listed :151 among hash sites without flagging; gemini
        silent.]

## Contested / adjudicated

  - Guard-5 label: grok explicitly judged "honest enough" (the echo
    line makes no false claim); gemini and codex filed it as a finding.
    Coordinator sides with gemini/codex: the round-4 acceptance
    criterion was "labeled for what it is IN the script", and the
    orchestrator had independently flagged the absence before any
    verdict arrived. Kept as R4-1.
  - No reviewer claim was rejected this round. No new behavioral
    finding exists; both items are prose/comments.

## Gate status

U10 gate remains OPEN on two documentation nits only. Land R4-1 and
R4-2 (a comment block and a half-line of prose; no code paths change),
then run round 5 as a minimal text-confirmation pass: each reviewer
reads the two changed hunks, re-runs the tracked guard once (16/16),
and either grants unconditional approval or names a blocker. No
mutation re-runs are required unless the guard script's executable
lines change.

## Verdict files

  impl-review-r4-verdict-codex.md   (FIXES REQUIRED, 2 x P3)
  impl-review-r4-verdict-gemini.md  (FIXES REQUIRED, 1 x P2)
  impl-review-r4-verdict-grok.md    (UNCONDITIONAL APPROVAL)

Orchestrator reproductions (this session, before verdicts landed):
stock guard 16/16 pass; mutation flips exactly guard-4 py check
(r4-mine-guard-stock.log, r4-mine-guard-mutated.log); five fixtures
1/1/1, symlink 0/0/0; usage exit 2; mktemp message on RO TMPDIR;
29/29 conformance; negative-agreement replay clean; diff --check clean;
guard-5 comment absence confirmed (grep parity|mutation: only the
guard-4 block matches).
