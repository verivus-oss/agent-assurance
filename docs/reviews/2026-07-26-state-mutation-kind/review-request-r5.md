# Independent design review request, round 5: the conformance corpus itself

Instantiates `tools/review-request-dag.toml`. Rounds 1 to 4 and their verdicts
are in this directory.

- **Initiator (excluded from the standard reviewer set):** Claude (Opus 5), in
  Werner Kasselman's session, 2026-07-27.
- **Reviewer models:** Codex, Grok, Devin, Gemini.
- **Under review:** `67dd095` and `8869fed` on branch
  `profile/state-mutation-kind`.
- **Worktree:** `/srv/repos/external/verivus-oss/aa-state-mutation`

**This round is scoped to the corpus, not the validators.** All three round-4
reviewers said a shared conformance corpus is what ends this review cycle
rather than another round of it. It now exists. That makes it the artefact
every future change to these kinds will be judged against, which inverts the
risk: **a wrong assertion in the corpus is more dangerous than a wrong line of
validator code**, because it silently blesses the defect it was written to
catch.

Do not re-review the validators except where a corpus case is the evidence that
something about them is wrong.

## What landed

```sh
cd /srv/repos/external/verivus-oss/aa-state-mutation
git show 67dd095      # the corpus, runner registration, enumerated-list removal
git show 8869fed      # needle discrimination fix, found by the initiator
ls conformance/cases/state-mutation/{valid,invalid}/
ls conformance/cases/mutation-claim/{valid,invalid}/
cat conformance/runner.py
```

Build both primaries from THIS worktree and run the corpus:

```sh
cd tools/dagtoml-validate-rs && cargo build --release && cd ../..
cd tools/dagtoml-validate-go && go build -o /tmp/dagtoml-validate-go . && cd ../..
python3 conformance/runner.py \
  --rs tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs \
  --go /tmp/dagtoml-validate-go --repo-root .
```

**Do not use the prebuilt binary at
`/srv/repos/external/verivus-oss/agent-assurance/tools/dagtoml-validate-go/`.**

## Priority 1: mutation-test the corpus against the fixes it exists to protect

This is the acid test and the main thing being asked. A corpus that stays green
when you reintroduce a real defect is decoration.

For each of the four fixes this review series produced, revert it in your own
scratch copy of the tree, rebuild, and run the corpus. **The corpus MUST go
red, and it MUST go red on the case that names that defect.**

1. **Round 2, blank and wrong-typed vocabulary tokens.** Restore the
   empty-string skip in the primaries (`if !scheme.is_empty()` in Rust,
   `if scheme != ""` in Go).
2. **Round 3, RKC02 by shape.** Change Go's `hasKey(doc, "execution_proof")`
   back to `tableOf(doc, "execution_proof")`.
3. **Round 4, the malformed kind selector.** Restore the silent
   `return [], []` for a non-string `template_kind` in
   `validators/validate_closure_root.py` and both primaries.
4. **Round 2, calendar validity.** Drop the month/day/hour range checks from
   `is_rfc3339_utc` in all three.

Report, per fix: did the corpus go red, on which case, and was the failure a
verdict mismatch or a needle miss? Any fix the corpus does NOT catch is a
concrete gap and the most valuable thing you can find this round.

## Priority 2: do the needles discriminate, or merely match

Every `error_contains` needle must be present in all three implementations'
output AND must fail if the document were rejected for a different reason. A
needle that any rejection of its own document would contain asserts nothing.

The initiator already found and fixed four of these (`8869fed`): two cases
asserted only `"performed_at"` and were literally interchangeable. Assume more
remain.

- For each invalid case, ask: if this document were rejected by a DIFFERENT
  invariant, would the sidecar still pass? The mechanical version is the swap
  test: exchange two sidecars and confirm both cases fail.
- Are any needles so tight they encode incidental phrasing rather than a defect
  class, so that a harmless message reword breaks CI? Both failure directions
  matter: a needle can be too loose to assert anything or too tight to survive.
- `required-pin-missing-proof.expected.toml` asserts `"SPEC §12.8.1"`. Is
  depending on the section symbol wise, given the initiator had to align `§`
  across three implementations in `67dd095` to make such a needle work?

## Priority 3: does each invalid case fail for exactly ONE reason

A case that fails for two reasons proves neither, and this repo has already
shipped one: `required-pin-missing-proof` declared `source_bytes = 417` against
a 416-byte capture, so it failed on provenance AND on missing pins.

- For every invalid case, enumerate ALL defects each implementation reports.
  Is the intended defect the only one? Where a case legitimately produces
  several (blank scheme and blank finality, say), is the sidecar honest about
  which it is pinning?
- Are `binds_sha256` and `closure_root` correct in every case that edits a
  bound or pinned field? A stale root would make the case fail on RKM04 or the
  closure layer instead of the grammar it claims to test.
- The valid cases must be valid for the RIGHT reason too. Do all four pass
  every layer, or does one pass because something silently declined to run?

## Priority 4: what the corpus does not cover

- Which hard invariants have NO case at all? Walk RKM01 to RKM06 and RKC01 to
  RKC04 and name the ones with no fixture. Which of those are untestable in a
  static corpus, and which are simply missing?
- Which defect classes from rounds 1 to 4 have no case? Cross-check against
  `raw_findings/` rather than against the initiator's summary of it.
- `examples/negative/` and `conformance/cases/` now overlap heavily. Is that
  duplication a hazard (two copies drifting) or defensible (documentation
  versus gate)? Say which, and if it is a hazard, say what should be deleted.

## Priority 5: the repo-wide change riding along

`67dd095` changed `validators/validate_closure_root.py` so the positive sweep
DERIVES its skip of `conformance/cases/*/invalid/` instead of enumerating it.
That is repo-wide and affects every kind.

- Can it skip something it should not? The test is a path shape. What files
  could match it that are not asserted-negative conformance cases?
- The claim is that this matches what the Rust and Go discovery paths always
  did. Verify that against those code paths rather than the comment.
- The workflow's per-fixture negatives are now discovered by glob. Can a file
  land in `examples/negative/` that the glob picks up but that should not be
  asserted to fail, or vice versa?

## Rules

- Verify against files and by execution. Cite `path:line`. Do not accept this
  document, the design record, the verification log, or any previous round's
  verdict as evidence of anything.
- If you cannot build or run, say so explicitly. Round 4's Devin dispatch could
  not execute anything and produced both a real finding and an over-broad
  remedy that one run would have refuted.
- End with unconditional approval or one concrete named blocker. A round with
  no blocker is a real result; do not invent one.
- Never use the em dash character in prose you write.
