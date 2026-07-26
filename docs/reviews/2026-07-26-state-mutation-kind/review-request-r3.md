# Independent design review request, round 3: the round-2 fixes

Instantiates `tools/review-request-dag.toml`. Rounds 1 and 2 and their verdicts
are in this directory (`review-request.md`, `review-request-r2.md`,
`raw_findings/`, `raw_findings/r2-*.md`). Read them, then attack the current
state.

- **Initiator (excluded from the standard reviewer set):** Claude (Opus 5), in
  Werner Kasselman's session, 2026-07-27.
- **Reviewer models:** Codex, Gemini, Grok, Mistral.
- **Under review:** `d333d52` on branch `profile/state-mutation-kind`, and the
  stack `8290eb3..d333d52` against `origin/main` (`f9a37cf`).
- **Worktree:** `/srv/repos/external/verivus-oss/aa-state-mutation`

Round 2 ended in four withheld approvals and three reproducing blockers.
`d333d52` is the response to all of them. **Do not assume it is correct, and do
not assume the previous rounds' conclusions are either.**

## Get the diff yourself

```sh
cd /srv/repos/external/verivus-oss/aa-state-mutation
git log --oneline origin/main..HEAD
git show d333d52                     # the round-2 fixes
git diff origin/main..HEAD           # the whole stack
```

Build both primaries from THIS worktree. **Do not use the prebuilt binary at
`/srv/repos/external/verivus-oss/agent-assurance/tools/dagtoml-validate-go/`**;
it is pre-12.8.1 and silently computes 1-record closures, which cost the
initiator a false negative in round 1.

```sh
cd tools/dagtoml-validate-rs && cargo build --release
cd tools/dagtoml-validate-go && go build -o /tmp/dagtoml-validate-go .
```

## Priority 1: break the fix, do not confirm it

The round-2 root cause was a three-way conflation: absent, present-but-blank,
and present-but-wrong-typed all collapsed into one "skip this check" path. The
fix introduces `Field` (Rust) and `fieldOf` (Go) to separate them.

- Find the next member of that class. What OTHER value can a producer put in a
  required field that some implementation reads as "nothing to check"? Consider
  whitespace-only strings, an empty table, an array, a boolean, a float, a
  TOML datetime, a deeply nested table under a scalar key name, and duplicate
  keys.
- `[execution_proof]` and `[mutation]` are read with `as_table` / `tableOf`.
  What happens when they are present but are NOT tables (`execution_proof = 1`,
  `mutation = []`)? Do all three agree, and is the resulting message honest?
- Are there remaining `str_field` / `stringOf` call sites in the mutation paths
  that still conflate the two cases? The fix changed some and deliberately left
  others (for example the `provenance.source_sha256` check, which fails closed
  through a catch-all). Verify that reasoning holds rather than accepting it.
- Round 2 proved that a fix closing "absent" left "blank" open. Ask the same
  question one level up: what does the CURRENT fix close, and what is the
  nearest thing to it that it does not?

## Priority 2: the calendar-validity change

All three implementations now check month, day-against-month with the
leap-year rule, hour, minute, and second (60 permitted per RFC3339 5.6). This
is newly hand-rolled in three languages, which is exactly where round 2 found
divergence.

- Differential-test it hard. Year `0000`, month `00`, day `00`, February 29 in
  1900 and 2000 and 2100, second `60` and `61`, hour `24`, and the leading-zero
  and overflow behaviour of each implementation's integer parse.
- The Rust and Go parsers accumulate digits into a fixed-width integer. Can any
  20-to-30 character input overflow, wrap, or panic? Rust indexes byte ranges
  directly; construct input that makes it panic if you can.
- Is permitting second 60 unconditionally right, or does it accept leap seconds
  at instants where none has ever been declared? State which behaviour you
  think the spec should require.

## Priority 3: SPEC 12.8.2's round-2 additions

Three new normative bullets, written by the initiator in response to round-2
findings and **reviewed by nobody**. Same standing as the section itself in
round 2.

- The non-string rule, the frozen field-path grammar, and the
  no-Unicode-normalization rule. Is each correct, implementable from the text
  alone, and consistent with 12.8.1 and 12.9?
- The normalization decision is the contestable one. The section REQUIRES that
  no normalization is applied, so canonically equivalent NFC and NFD values
  produce different bindings. Gemini argued in round 2 that the text "must
  mandate a normalization form". The initiator did the opposite and stated why.
  Argue it out and say plainly which is right.
- Does "a profile that needs equivalent strings to bind identically MUST
  constrain the field's grammar so that only one encoding is representable"
  actually work? Construct a grammar that does it, or show that it cannot be
  done for a realistic field such as `target_id`.

## Priority 4: what this board keeps missing

Two data points worth acting on rather than repeating.

1. No round-2 reviewer found the calendar-validity bug. Four models
   differential-tested the timestamp grammar and all four tested its shape
   rather than its meaning. The initiator found it.
2. Three reviewers independently found the same Unicode-normalization gap,
   which is redundant coverage on one axis while another axis went unexamined.

So: name a class of defect that none of the three rounds has looked for, and
look for it. Semantics of values that pass their grammar is one such class.
Find others.

Also verify, since round 2 found CI red on a claim the initiator had made:

- Re-run the repo-wide closure sweep exactly as `.github/workflows/validate.yml`
  invokes it. Does it pass?
- The sweep enumerates its exclusions by directory. Are there OTHER enumerated
  lists in that workflow with the same hazard, where adding a file to a tracked
  directory silently breaks a sweep?
- Every claim in `design-record.md` and `initiator-verification-log.md` is
  meant to be reproducible. Pick the ones that would be most embarrassing if
  false and re-run them.

## Rules

- Verify against files. Cite `path:line`. Do not accept this document, the
  design record, the verification log, or any previous round's verdict as
  evidence of anything.
- Approve only what you inspected. Not on intent, not on plan-compliance, not
  on "should be fixed".
- If you cannot build or run a primary, say so explicitly and do not infer
  parity from the Python result. Round 2 produced one blocker that a single
  execution would have refuted.
- End with unconditional approval or one concrete named blocker.
- Never use the em dash character in prose you write.
