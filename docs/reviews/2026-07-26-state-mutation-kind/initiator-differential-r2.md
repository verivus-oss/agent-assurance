# Initiator differential test, round 2

Written after the round-2 review was dispatched and deliberately NOT committed
into the reviewed range, so the target does not move under four reviewers.

Round 1's parity evidence was one value (the expected `binds_sha256` for a
single fixture), which is weak. This is the stronger version: 19 documents
built to split the three implementations, each with `binds_sha256` and
`closure_root` recomputed so the grammar decides the verdict rather than RKM04.

The first attempt was confounded and is recorded because the mistake is
instructive: editing any bound field changes the tuple, so every case failed on
RKM04 and the grammars were never exercised. A green "all agree" from that run
would have been meaningless.

## Result: no divergence in 19 cases

| Case | Python | Rust | Go |
|---|---|---|---|
| baseline | PASS | PASS | PASS |
| `operation` 64 chars / 65 chars | PASS / FAIL | PASS / FAIL | PASS / FAIL |
| `operation` uppercase, leading dash | FAIL | FAIL | FAIL |
| `target_id` 480 / 481 chars after scheme | PASS / FAIL | PASS / FAIL | PASS / FAIL |
| `target_id` uppercase scheme | FAIL | FAIL | FAIL |
| `target_id` `x+y.z-1:` scheme | PASS | PASS | PASS |
| `target_id` non-ASCII path | PASS | PASS | PASS |
| `proof_locator` 480 / 481 chars | PASS / FAIL | PASS / FAIL | PASS / FAIL |
| `proof_locator` non-ASCII | PASS | PASS | PASS |
| `performed_at` no fraction | PASS | PASS | PASS |
| `performed_at` 9 fractional digits | PASS | PASS | PASS |
| `performed_at` 10 fractional digits | FAIL | FAIL | FAIL |
| `performed_at` trailing dot, no digits | FAIL | FAIL | FAIL |
| `performed_at` lowercase `t` separator | FAIL | FAIL | FAIL |

Boundary lengths, case sensitivity, Unicode, and fractional-second counts all
agree exactly. That is meaningful evidence for the hand-ported grammars, which
were written to match the Python regexes by eye and were the most likely place
for the three to split.

## A real weakness the test surfaced

`performed_at = "2026-99-26T10:15:00Z"` **passes all three**. The grammar checks
shape (digit positions and separators), not calendar validity, so month 99, day
99, and hour 99 are all accepted.

This is not a parity bug: the three agree. It is a design weakness. The field is
a member of the RKM04 bound tuple and carries the freshness claim, so a
timestamp that cannot correspond to any instant weakens what the tuple is worth.
Range checks (month 01-12, day 01-31, hour 00-23, minute 00-59, second 00-60 for
leap seconds) would be cheap in all three implementations.

**Not fixed here.** Four reviewers are mid-review against `1459666`, and moving
the target under them is exactly the failure this file was written to avoid. It
is recorded so that either a reviewer finds it independently, which is the
better outcome, or it is fixed alongside whatever else round 2 returns.

### Outcome

Fixed alongside the round-2 blockers. No reviewer found it independently, which
is the less good of the two outcomes and is worth recording as a datum about
what this review board does and does not catch: four models differential-tested
the timestamp grammar and all four checked its shape rather than its meaning.

All three implementations now validate month, day (against the month, with the
leap-year rule), hour, minute and second (60 permitted, per RFC3339 5.6).
`2026-99-26`, `2026-02-31` and hour 99 are rejected by all three; `2024-02-29`
still passes. Fixture:
`examples/negative/state-mutation-impossible-timestamp.toml`, with
`binds_sha256` and `closure_root` recomputed for the bad timestamp so the
grammar is the only thing that can reject it. That is the same discipline this
file's confounded first attempt failed to apply.

## Reproduction

The generator and the 19 documents are under the session scratchpad at
`.../scratchpad/diff2/`. Both primaries were built from this worktree; the
prebuilt binary in the sibling checkout is pre-12.8.1 and must not be used.
