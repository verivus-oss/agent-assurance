# Initiator mutation test, round 5: does the corpus catch the fixes it exists to protect

Written after the round-5 review was dispatched and deliberately NOT committed
into the reviewed range, so the target does not move under four reviewers. Same
discipline as `initiator-differential-r2.md` and `initiator-kind-dispatch-r4.md`.

This is Priority 1 of `review-request-r5.md`, run by the initiator in parallel
with the board. A corpus that stays green when a real defect returns is
decoration, and until this was run there was no evidence either way.

## Method

The mutations edit validator source, so they were run in a **separate git
worktree** (`git worktree add --detach`) rather than in place. Four reviewers
were mid-round reading the main tree; mutating validator source under them
would have been a worse version of the mistake this file's predecessors were
written to avoid. The main worktree stayed clean at `150600d` throughout, and
the scratch worktree was removed afterwards.

Each fix was reverted individually, both primaries rebuilt from the mutated
source, and the full corpus re-run.

## Result: 4 of 4 caught, each on the case that names it

| Reverted fix | Origin | Corpus | Red on | Failure mode |
|---|---|---|---|---|
| Empty-string skip in the vocabulary check | Round 2 (Grok) | RED | `state-mutation/invalid/blank-vocabulary-tokens` | verdict: all three accepted |
| RKC02 via `tableOf` instead of `hasKey` | Round 3 (Grok, Codex) | RED | `mutation-claim/invalid/array-proof` | verdict: Go accepted |
| Silent no-pins fall-through on a non-string selector | Round 4 (Codex, Devin) | RED | `state-mutation/invalid/malformed-kind-selector` | verdict: all three accepted |
| Calendar range checks in `is_rfc3339_utc` | Round 2 (initiator) | RED | `state-mutation/invalid/impossible-timestamp` | verdict: all three accepted |

Every one is a VERDICT failure (`:FAIL`), not merely a needle miss (`:MSG`),
which is the stronger result: the corpus catches these by the documents being
accepted when they must be rejected, so it would hold even if every sidecar
were deleted.

Two details worth recording because they show the cases are precise rather than
broadly sensitive:

- Reverting only the empty-string skip turned `blank-vocabulary-tokens` red and
  left `wrong-typed-proof-fields` green. Those two cases are siblings covering
  adjacent halves of one defect, and they discriminate: the wrong-type branch
  was still intact, so its case correctly stayed green.
- The RKC02 revert turned `array-proof` red and left `table-proof` green, which
  is exactly right. `tableOf` still sees a table, so the table-shaped fixture
  is still caught; only the array-of-tables shape escapes. If both had gone red
  the corpus would have been failing for the wrong reason.

## What this does and does not establish

**Does:** the four defects this review series actually found are now regression
tested across all three implementations, and each is pinned by a case that
fails for its own reason rather than incidentally.

**Does not:** say anything about defects the series never found. The corpus can
only encode the history it has. It also does not validate the needles, since
all four mutations produced verdict failures rather than message failures; the
sidecars' discrimination was tested separately by the swap test in `8869fed`,
and the fact that these four mutations did not exercise them is itself a limit
worth stating.

## Errata

The first attempt at the calendar mutation failed to compile the Go primary
(`declared and not used: year`), because neutering the range check left a
variable unused. That is a defect in the mutation script, not in the corpus or
the validator, and it is recorded because a build failure in a mutation test
can easily be misread as a passing result: nothing ran, so nothing went red.
The rerun kept every variable live by widening the bounds rather than deleting
the check.
