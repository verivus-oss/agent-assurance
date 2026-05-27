# toml-test parser-conformance harness — independent review (2026-05-25)

Fresh-context reviewer. **Narrow scope**: a small CI/build-tooling
change (3 files, 98 insertions, 0 deletions). No SPEC, profile,
validator, ontology, or example bytes are modified.

## Repository

- Working copy: `/srv/repos/external/verivus-oss/agent-assurance`
- Parent commit: `8cc1110` (Phase 3 review persisted)
- HEAD: `afe354c` (the commit under review)
- Commit range: `8cc1110..afe354c` (1 commit; 3 files modified)
- Bundle: `docs/reviews/2026-05-25-toml-conformance-harness/review_bundle.toml`

## What landed

A new top-level `Makefile` with two targets — `toml-conformance-install`
(`go install`s the pinned `toml-lang/toml-test` runner and the
`BurntSushi/toml` `toml-test-decoder` shim) and `toml-conformance`
(runs the suite) — plus a new step "TOML 1.0 spec conformance" in
`.github/workflows/validate.yml` adjacent to the Taplo lint, plus a
`[Unreleased]` CHANGELOG entry.

**The load-bearing claim**: the `toml-test-decoder` shim is shipped
by the same `BurntSushi/toml v1.4.0` module that
`tools/dagtoml-validate-go/go.mod` requires, so a green run is
direct evidence about the parser the Go validator actually uses at
runtime — not about an unrelated TOML library. The pinned-version
discipline binds this evidence; if the two versions diverge, the
harness silently signals about a different parser.

## Rules (`tools/review-request-dag.toml [policy.*]`)

Verify against bytes; never accept the bundle's summary as evidence.
Findings carry file:line + severity. Forbidden approval bases:
`stated_intent`, `plan_compliance_claim`, `should_be_fixed_language`.
Terminal states: `unconditional_approval` or
`concrete_unresolvable_blocker`.

## What to verify (units U01–U05)

Per the bundle. Highlights:

- **U01** — `Makefile`'s `TOML_TEST_DECODER_VERSION` must match
  `tools/dagtoml-validate-go/go.mod`'s `BurntSushi/toml` line.
  Divergence is a concrete blocker.
- **U02** — The 13-entry `TOML_CONFORMANCE_SKIPS` list must be
  honest: it must equal the actual fail set you observe when running
  the unskipped suite locally, and the rationale comment must be
  present.
- **U03** — The CI step must hard-fail on suite failure (no
  `continue-on-error`, no swallowed exit).
- **U04** — `git diff 8cc1110..afe354c --name-only` must list
  exactly the three files claimed. Any SPEC/profile/validator/instance
  byte appearing is a concrete blocker (scope creep).
- **U05** — The CHANGELOG entry must (a) live under `[Unreleased]`,
  (b) name the parser-binding claim explicitly, (c) honestly flag
  the Rust shim as a deferred follow-up (not as "done").

## Reproducing the local result

```bash
make toml-conformance-install
make toml-conformance
```

Expected:
```
valid tests: 185 passed,  0 failed
invalid tests: 358 passed,  0 failed, 13 skipped
```

If your local environment lacks Go or network access for
`go install`, document that explicitly in your finding and instead
inspect the Makefile recipe + skiplist by reading bytes.

## Process notes

- Search order: prefer `sqry` semantic search first; fall back to
  literal grep only for exact-string confirmation.
- This is not a SPEC change — the
  `[[feedback_no_self_approval]]` rule's narrow letter is about
  SPEC/core/profile/validator/DAG-TOML changes. The initiator
  dispatched this review anyway because the change touches CI
  policy and the load-bearing claim ("the parser the Go validator
  uses") warrants independent confirmation.

## Output format

Persist your full review verbatim. Conclude with:

```
Terminal verdict: unconditional_approval
```

or

```
Terminal verdict: concrete_unresolvable_blocker
Blocker: <one paragraph; cite file:line>
```
