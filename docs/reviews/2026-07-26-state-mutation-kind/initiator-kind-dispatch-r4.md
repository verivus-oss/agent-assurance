# Initiator finding, round 4: the kind selector fails OPEN

Written after the round-4 review was dispatched and deliberately NOT committed
into the reviewed range, so the target does not move under three reviewers.
Same discipline as `initiator-differential-r2.md`.

The round-4 request names `meta.template_kind` as the untested dispatch point,
on the reasoning that every kind-layer check in all three implementations
branches on it and no round has asked what happens when it is unreadable. This
is what testing it found.

## A document that asserts everything and is validated by nothing

Take `examples/negative/state-mutation-hollow-proof.toml`, which every
implementation currently rejects: it carries `[execution_proof]` with only the
two pinned digests and no typed proof at all. Make two edits:

1. `template_kind = 1` (or delete the line, or `"State-Mutation"`, or
   `"state-mutation "` with a trailing space).
2. Recompute `closure_root` over the SPEC 12.8 one-record source-hash closure.

The result passes **every check in all three implementations**:

| Layer | Python | Rust | Go |
|---|---|---|---|
| closure root | PASS | PASS | PASS |
| provenance | PASS | PASS | PASS |
| kind layer (RKM02/03/04/06) | PASS | PASS | PASS |

The document still carries a full `[mutation]` table and a proof-shaped
`[execution_proof]`. It reads to a human, and to any tool that does not itself
re-check `template_kind`, as a state-mutation. Nothing in the validation stack
disagrees.

## Why

`validators/validate_closure_root.py:228-231`:

```python
    template_kind = meta.get("template_kind")
    if not isinstance(template_kind, str):
        template_kind = meta.get("kind")  # legacy synonym
    if not isinstance(template_kind, str) or template_kind not in pin_map:
        return [], []
```

An unresolvable kind returns no pins AND no errors, so the closure silently
degrades to the weakest form in the SPEC: one record over
`provenance.source_sha256`. The five required pins of this kind are simply not
looked for.

The docstring immediately above that code, at line 222, says:

> There is no pin-free fall-through for a pinned kind.

That is precisely what lines 228-231 provide. The code contradicts its own
stated invariant. The three kind-layer validators then each dispatch on the
same field and correctly conclude "not my kind", so they add nothing.

Every layer behaves reasonably on its own. The composition fails open.

## Scope: this is NOT a defect in this branch

It reproduces on `examples/minimal-api-snapshot.toml`, which is on
`origin/main` and predates this whole stack. Mangle its `template_kind`,
recompute the one-record root as
`sha256:f251f64bc6170cb32a4b3c0bcc10d520247c41e7bbf22587d206108e6d19098c`, and
all three implementations accept it.

That digest is worth recognising: it is the same value recorded in
`initiator-verification-log.md` as the "pre-promotion source-only root" that the
stale Go binary computed in round 1. A stale binary that had never heard of pins
and a current binary that cannot read the kind selector produce byte-identical
output. The round-1 trap and this hole have the same signature.

So this is a SPEC-layer and repo-wide issue, not a `state-mutation` one, and
fixing it is a change to `validate_closure_root.py` plus both primaries that
touches every kind. It should not be smuggled into this branch.

## What the fix probably is

Fail closed at the selector rather than at each consumer. A document whose
`meta.template_kind` is absent, non-string, or unresolvable against the loaded
pin map should be a validation ERROR, not a document with zero pins. The
narrower version, which stays inside SPEC 12.8.1 and is probably what should
land first: if `meta.template_kind` is present but is not a string, that is an
error unconditionally. That case has no legitimate reading at all, unlike an
unknown-but-well-formed kind slug, which a validator that has not loaded the
defining profile may legitimately not recognise.

The unknown-slug case is the genuinely hard one and is a design question rather
than a bug fix: a validator cannot distinguish "kind from a profile I have not
loaded" from "kind that does not exist" without a closed registry, and SPEC
2.3 explicitly lets profiles define new values.

## Outcome

**The board found it, 2 of 3, and one of them was right to push back.**

Codex reproduced it by execution, computing the identical fallback root. Devin,
reviewing this codebase for the first time and unable to run anything, found it
by reading the source. Both filed it as a merge blocker. Grok reproduced the
same behaviour and approved anyway, on the SPEC 12 escape-hatch reasoning
sketched below.

The narrow fix predicted here is what landed, and Grok's argument is why it
stayed narrow. Absent and non-spec-reserved-string `template_kind` remain legal
and are now asserted as legal in the verification log, so a later change cannot
quietly remove the escape hatch that SPEC 12 guarantees. Present-but-non-string
is a closure-layer error in all three implementations. Fixture:
`examples/negative/state-mutation-malformed-kind-selector.toml`.

This is the first initiator finding in the series the board reached
independently. The calendar-validity weakness recorded in
`initiator-differential-r2.md` was not found by any reviewer. The difference
worth noting is that round 4's request named `meta.template_kind` explicitly as
the untested dispatch point, so this is weak evidence about the board's
unprompted reach and strong evidence that a specific, falsifiable pointer in a
review request gets acted on.

## Status when written

**Not fixed here, and deliberately not committed.** Three reviewers are mid-round
against `d12f669`. Recorded so that either a reviewer finds it independently,
which is the better outcome and the direct test of whether round 4's Priority 1
framing worked, or it is addressed after the verdicts return as its own
change against `main`.

Round 2 recorded the calendar-validity weakness the same way and no reviewer
found it. That is now two initiator findings in a row that the board did not
reach on its own, which is itself relevant to round 4's Priority 2 question
about whether this review process is converging.
