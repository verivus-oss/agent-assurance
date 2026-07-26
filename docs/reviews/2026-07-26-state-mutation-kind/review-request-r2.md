# Independent design review request, round 2: mutation kinds, SPEC 12.8.2, and the Rust/Go ports

Instantiates `tools/review-request-dag.toml`. Round 1 request and verdicts are
in this directory; read them, then review the current state.

- **Initiator (excluded from the standard reviewer set):** Claude (Opus 5), in
  Werner Kasselman's session, 2026-07-26.
- **Reviewer models:** Codex, Gemini, Grok, Mistral.
- **Under review:** `8290eb3..cff386b` (three commits) on branch
  `profile/state-mutation-kind`, against `origin/main` (`f9a37cf`).
- **Worktree:** `/srv/repos/external/verivus-oss/aa-state-mutation`

Round 1 ended in four withheld approvals and four named blockers. Everything
since is a response to those. **Do not assume the responses are correct.**

## Get the diff yourself

```sh
cd /srv/repos/external/verivus-oss/aa-state-mutation
git log --oneline origin/main..HEAD
git diff origin/main..HEAD           # the whole stack
git show b657051                     # round-1 fixes
git show cff386b                     # companion kind + Rust/Go ports
```

## Priority 1: SPEC 12.8.2 has been reviewed by nobody

`spec.md` section 12.8.2 "Bound tuples" is **new normative text**. The
initiator wrote it in response to a round-1 blocker and then implemented
against it three times. Three self-consistent implementations of one author's
design are not evidence the design is right, and this is now spec text that
binds every future profile.

Attack it directly:

- Is prehashing values (`<field> sha256:<hex-of-value>\n`) actually sufficient
  for injectivity, or does the sorted-and-concatenated stream still admit a
  collision through some other route? Try to construct one.
- Is "bound tuples have no `when-present` form" the right call, or does it make
  the mechanism unusable for real proof schemes with optional inputs?
- The section says a bound tuple is not a closure input and a profile that
  wants it to cascade must ALSO pin it under 12.8.1. `com.verivus.runtime` does
  exactly that, so `binds_sha256` appears in both streams. Is that double
  commitment sound, or does it create a circularity or an update-ordering
  hazard for a producer?
- Does 12.8.2 conflict with anything in 12.1 to 12.10, or with the profile
  invariants in section 6.1?
- Is the section implementable from its text alone by someone who has not seen
  this code? Name what is still underspecified. Round 1 called out timestamp
  normalization, Unicode form, and whether the `sha256:` prefix is inside the
  hashed value: check whether the current text actually resolves those.

## Priority 2: the Rust and Go ports

New code: `mod mutation_kinds` in `tools/dagtoml-validate-rs/src/main.rs`, and
`validateMutationKinds` plus helpers in `tools/dagtoml-validate-go/main.go`.
Both are wired into auto dispatch and `--mode mutation-kinds`.

- **Differential-test them against the Python reference.** The claim is exact
  parity on RKM02, RKM03, RKM04, RKM06 and RKC02. Construct documents that
  split the three implementations. The hand-rolled RFC3339, operation-token and
  URI-shape checks are the most likely divergence: the Rust and Go versions were
  written to match Python regexes by eye.
- The initiator verified parity on ONE value (the expected `binds_sha256` for
  the unbound fixture). That is weak evidence. Check Unicode, empty strings,
  values with `:` or `+`, long values, and non-ASCII `target_id`.
- Do the ports handle a missing or non-table `[mutation]`, wrong types
  (integer where string expected), or duplicate keys the same way Python does?
- Is anything enforced in Python but silently skipped in a primary, or the
  reverse?

## Priority 3: `mutation-claim` and RKC02

- Does the claim/proof split actually hold, or can a document present as one
  and be read as the other? RKC02 is checked at the kind layer only, since a
  closure stream cannot pin an absence. Is there a path that evades it?
- Is `claim-record.v1` a coherent third abstraction class alongside
  `observation-record.v1` and `execution-record.v1`, or does it overlap one of
  them enough to be redundant?
- The promotion story (claim to proved: add the table, change `template_kind`,
  re-root) is asserted in prose. Try it and see whether it is actually
  mechanical.
- Is three-record closure right for a kind with no proof, or should the claim
  pin something else?

## Priority 4: verify the round-1 fixes, do not take them on trust

Each of these was a named blocker. Confirm the fix or reopen it.

1. **Non-injective bound tuple (Codex).** Reconstruct the original collision
   against the CURRENT code. It should be impossible. If you can still collide
   two documents on one `binds_sha256`, that reopens the blocker.
2. **RKM03 bypass via `proof_locator` (Codex).** Try to smuggle a payload
   through any permitted field in any of the three implementations.
3. **`provenance.source_sha256` unenforced (Grok).** Confirm a document with
   no `[provenance]` is now rejected everywhere.
4. **Hollow proof (Grok).** Confirm all three now reject it.
5. **`provider-receipt` retention (Gemini's blocker, NOT accepted).** The
   initiator kept it, with RKM06 as mitigation, on Grok's argument that
   removing the honest label makes producers mislabel weak evidence as
   `tee-quote`. Re-argue this. If you still think it is wrong, say so plainly:
   the decision is the operator's and a second dissent should be recorded.

## Reproduce the verification

Everything the initiator claims is in
`docs/reviews/2026-07-26-state-mutation-kind/design-record.md` and
`initiator-verification-log.md`. Re-run it. Build the primaries yourself:

```sh
cd tools/dagtoml-validate-rs && cargo build --release
cd tools/dagtoml-validate-go && go build -o /tmp/dagtoml-validate-go .
```

**Do not use the prebuilt binary at
`/srv/repos/external/verivus-oss/agent-assurance/tools/dagtoml-validate-go/`.**
It was built from a pre-12.8.1 branch and silently computes 1-record closures,
so it passes documents it should reject. That trap cost the initiator a false
negative in round 1.

## Rules

- Verify against files. Cite `path:line`. Do not accept this document, the
  design record, or the verification log as evidence of anything.
- Approve only what you inspected. Not on intent, not on plan-compliance, not
  on "should be fixed".
- If you cannot build or run a primary, say so explicitly rather than inferring
  parity from the Python result.
- End with unconditional approval or one concrete named blocker.
- Never use the em dash character in prose you write.
