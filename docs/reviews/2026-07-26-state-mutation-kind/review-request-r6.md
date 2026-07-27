# Round 6 review request: the post-round-5 commits, and the pre-PR gate

- **Branch:** `profile/state-mutation-kind`
- **Head under review:** `2d5809e`
- **PR base:** `origin/main` = `f9a37cf`. `git rev-list --count f9a37cf..2d5809e` = **17**.
- **Worktree on the initiator's host:** `/srv/repos/external/verivus-oss/aa-state-mutation`
- **CI:** run `30238364724` (`validate`) and `30238364717` (`no-ai-attribution`)
  are both `success` at head SHA `2d5809e8609871aff32e5b68c5719abbae55c5b6`.

This is the **pre-PR gate**. No PR is open. Approval here means: this branch is
fit to become a pull request against `main`.

## What is new since round 5

Round 5 reviewed `67dd095` and `8869fed` at head `150600d` and ended split:

| Reviewer | Round-5 verdict |
|---|---|
| Codex | **NOT APPROVED**, one blocker: `hollow-proof.expected.toml` asserted a bare `"RKM02"` needle that also matched three other cases, so it did not discriminate |
| Grok | APPROVED |
| Devin | APPROVED |
| Gemini | no verdict, provider timeout at 5m08s, third consecutive failure |

Five commits have landed since, and **no external reviewer has seen any of
them**:

```
8c3b463 conformance: make every sidecar discriminate, and check that mechanically
c197de4 fix: derived conformance skip must not depend on the path form given
301a322 reference: propagate the two new kinds through every count-mirror surface
16d1729 fix: mutation-claim negatives must fail the provenance gate too
2d5809e style: tagged switches on fieldState, per staticcheck QF1002
```

`8c3b463` is the fix for Codex's round-5 blocker. The other four came from
pushing the branch and reading real CI failures, not from review.

## How the last four defects were found, and why that matters to you

Every one was a gate that **already existed**, was **never run outside CI**, and
would have been caught by a single local invocation. Five review rounds did not
find any of them. The relevant inference for this round is that the reviewed
surface and the gated surface are not the same surface, so please do not confine
yourself to the diff.

| # | Gate | Defect | Fixed in |
|---|---|---|---|
| 1 | manifest drift | two new kinds and two new vocabularies not propagated to seven count-mirror surfaces | `301a322` |
| 2 | provenance negatives | both mutation-claim negatives **passed** a gate they must fail | `16d1729` |
| 3 | golangci-lint | staticcheck QF1002 on two switches | `2d5809e` |
| 4 | (pre-existing, since `cff386b`) | `mutation-claim-with-proof` violated the `examples/negative/` convention for four review rounds | `16d1729` |

Defect 4 in full, because it is the one that most deserves an independent look:
`examples/negative/mutation-claim-with-proof.toml` has carried a comment since
`cff386b` saying `source_bytes` is *"deliberately wrong (185; the capture is
184)"* while actually carrying `224` against a capture that is genuinely 224
bytes. The stated convention was never implemented in that file. The round-3
fixture `mutation-claim-array-proof.toml` was written from it and inherited both
the false comment and the passing value. Neither the conformance corpus nor the
ad hoc negative loops caught it, because both check the **kind layer** and
neither checks that a negative also fails **every other gate it is supposed
to**.

Two numbers in `301a322` were **derived rather than substituted**, and are the
most likely place for a silent arithmetic error:

- `attribute_values_closed` 115 → **123** (both new vocabularies are closed,
  four values each)
- `[verification.rdf].expected_triple_counts.schema` 1434 → **1476**, taken from
  the regenerated file, not predicted

## Verification the initiator ran, at `2d5809e`

Reproduced on the initiator's host today, in the worktree above, with both
primaries rebuilt from this tree (`cargo build --release --locked`,
`go build -o ... ./...`) and `dagtoml-rdf` built in place:

| Gate | Result |
|---|---|
| `conformance/runner.py --rs --go` | PASSED, 45 cases |
| `conformance/discrimination.py --rs --go` | PASSED, 12 sidecars over 12 cases |
| `validators/check_manifest_drift.sh` | PASSED |
| `validators/check_provenance_containment.sh <rs> <go>` | PASSED |
| `validators/check_pin_resolution_guards.sh <rs> <go>` | PASSED |
| `validators/check_safe_tools.sh` | PASSED |
| `ruff check .` (0.15.15, the pinned version) | PASSED |
| `golangci-lint run ./...` (2.12.2, the pinned version) across all four Go modules | PASSED |

This is a **subset** of the 55 named steps in `.github/workflows/validate.yml`,
chosen for the four defects above. The full suite is green in CI at this SHA;
the local subset is what the initiator can reproduce and therefore what the
initiator will stand behind personally. Treat the CI run as evidence for the
rest, and re-run anything you do not trust.

## Named questions

You are not limited to these. They are where the initiator's own confidence is
thinnest.

1. **The discrimination allowlist re-opens the round-5 hole, or it does not.**
   `conformance/discrimination.py:37` carries one `ALLOWED_COLLISIONS` entry,
   `array-proof.toml ~ table-proof.toml`, justified as "same RKC02 defect,
   different TOML shape, so the diagnostic is identical by design; they
   discriminate by verdict instead." A gate built in response to a
   non-discrimination blocker that ships with a non-discrimination exemption
   deserves an adversarial read. Is the stated verdict-discrimination claim
   true? Revert Go's `hasKey` to `tableOf` and check that it reddens
   `array-proof` while leaving `table-proof` green, which is the claim. If it
   does not, the exemption is unearned and this is a blocker.

2. **`c197de4`, path-form dependence in the derived-conformance skip.** A skip
   that behaved differently depending on the form of the path it was given is a
   bypass shape. Confirm the fix is not merely normalising the two forms the
   initiator happened to try.

3. **`16d1729` fixed the comment and the value. Did it fix the class?** Both
   mutation-claim negatives now declare `source_bytes = 225` against a 224-byte
   capture. Verify (a) both are now rejected by `validators/validate_provenance.py`,
   (b) both are still closure-valid, so `closure_root` was genuinely undisturbed,
   (c) both still fail at the kind layer for RKC02, the reason they exist, and
   (d) **no other fixture under `examples/negative/` violates the same
   convention**. The defect was a copied comment; check for other copies.

4. **Both fixtures carry the identical `closure_root`**
   `sha256:f7aeefffc2ab795ba9e6003b5f2d326a23a952e449f4dd2ab677afc17ed41bb8`.
   Two distinct files with the same root is either correct (they pin the same
   records over the same capture) or evidence the root is not binding what it
   should. Decide which, with the SPEC §12.8.1 pinned-record list in hand.

5. **`301a322`'s derived numbers.** Recompute 123 and 1476 independently rather
   than checking that the gate agrees with the manifest. Related: does
   `validators/check_attribute_values.py` compare `expected_seed_counts` against
   the actual seed SQL, or against another manifest field? `attribute_value_allowed`
   stayed at 144 across this change while `attribute_values_closed` moved by 8.
   The initiator believes that is correct because the surfaces differ, and did
   not prove it.

6. **The class of defect 4, generalised.** Nothing currently asserts that a
   negative fixture fails every gate it is nominally subject to. The per-fixture
   provenance assertion lives only in the workflow. Is a repo-level fix in scope
   for this branch, or correctly deferred?

## Disclosed, not defects, but tell us if you disagree

- **Mixed authorship.** 13 of the 17 commits are
  `verivusOSS-releases <oss-release@verivus.com>`, 4 are
  `Werner Kasselman <werner@verivus.com>`. Permanent and public once pushed.
- **Not bisectable-green.** `cff386b` through `4a48069` fail CI for the
  unregistered-conformance-kind reason. Squashing would hide the review history,
  which is itself a deliverable of this branch, so the intent is to leave it.
- `examples/captures/_tmp-fake.capture` was added in `b657051` and removed in
  the post-round-5 range. It is absent at head. Confirm nothing references it.

## Standing open items, carried from the design record

These were open at round 5 and remain open. They are **not** in scope for
approval, but say so if you think any one of them blocks a PR:

- The corpus covers only the two mutation kinds; `traceability`,
  `review-readiness`, `kind-descriptor` and `profile-descriptor` have no corpus.
- Nothing forces a new kind to arrive with conformance cases.
- Promotion from `mutation-claim` to `state-mutation` has never been executed
  end to end as a scripted operation.
- No normative consumer algorithm: the kinds do not say how a consumer decides
  a `provider-receipt` is good enough, nor how any of this binds to
  `profiles/agent-assurance/tiers/`.
- Vocabulary source differs between reference and primaries: Python loads closed
  vocabularies from the profile ontology at run time, both primaries compile
  them in. No CI lock diffs the two.
- Enumerated lists in CI remain a structural hazard (`validate.yml:391`, the
  closure sweep's `--exclude` list). Adding a kind can silently break a sweep.
- Gemini has not reviewed rounds 3, 4 or 5, so its round-2 objection to the
  normalization decision stands unanswered by its author.

## How to review

Read the files yourself. Verify every claim above against the code and the
docs. **Do not accept this document as evidence for anything.** Build both
primaries from the tree, do not use any prebuilt binary you find on disk: a
stale prebuilt Go validator at
`tools/dagtoml-validate-go/dagtoml-validate-go` in the *sibling* checkout
produced silently wrong verdicts in round 1 and cost a false negative.

```sh
git clone --branch profile/state-mutation-kind <repo> r6 && cd r6
git checkout 2d5809e
(cd tools/dagtoml-validate-rs && cargo build --release --locked)
(cd tools/dagtoml-validate-go && go build -o /tmp/dagtoml-validate-go ./...)
python3 conformance/runner.py --rs tools/dagtoml-validate-rs/target/release/dagtoml-validate-rs --go /tmp/dagtoml-validate-go
python3 conformance/discrimination.py --rs ... --go ...
git log --oneline f9a37cf..2d5809e
git diff 150600d..2d5809e
```

Approve **only** on the basis of what you inspected. Do not approve on intent,
on plan-compliance, on "the design record says", or on "should be fixed".
Either give **unconditional approval**, or name **one concrete blocker** with a
file path and line range and a reproduction.
