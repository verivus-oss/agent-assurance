# U07 — rebuttal record

Per `tools/review-request-dag.toml` `[policy.evidence]`:
disagreements with reviewer findings MUST cite code or doc evidence
(file + line), not assertion.

This document records initiator rebuttals across all three review
rounds. Each rebuttal is anchored to a specific reviewer finding by
file:line.

## Round 1 (bc2a7c5)

### Grok round-1

**F1 (high)** — Internal contradiction in §12.9 §11 bullet vs §12.1.

Initiator response: **accepted, no rebuttal.** The contradiction was
genuine — leftover proposal language from when §12.1 said "MAY omit
closure_root when self-contained". After the user directed
"closure_root REQUIRED on every conforming document", I tightened
§12.1 but missed the §12.9 §11 back-reference. Fix: rewrote the
bullet in commit `dc3a7b0`. Verified resolved by grok round 2.

**F2 (medium)** — Incomplete CI enforcement on patched conforming
files (kind descriptors, profiles, ontologies missed by hardcoded
list).

Initiator response: **accepted, no rebuttal.** Replaced hardcoded
list with `--discover` mode in commit `dc3a7b0`. Verified resolved by
codex round 2.

**F3 (low)** — Hand-maintained file lists / no semantic guard.

Initiator response: **accepted, no rebuttal.** Addressed via
`--discover` mode that derives blessed-kind set dynamically.

### Codex round-1

**B1 / F1 (high)** — Eight tracked conforming files outside
`core/profiles/examples` discovery roots lack `closure_root`
(VERIFICATION_REPORT.toml, paper/VERIFICATION_REPORT.toml, six
`skills/convert-md-to-dag/*.toml`).

Initiator response: **accepted, no rebuttal.** Patched the 8 files
with the canonical empty-closure sentinel and broadened CI to
`--discover .` in commit `5c145c8`.

**B2 / F2 (high)** — CI discovery still does not gate every tracked
conforming file.

Initiator response: **accepted, no rebuttal.** Same fix as B1
addresses this.

**F3 (medium)** — Migration guidance is absent.

Initiator response: **initially deferred (no rebuttal but not yet
acted on).** Both reviewers re-raised this in round 2; finally
addressed in commit `20c6207` via SPEC §12.11.

## Round 2 (5c145c8)

### Grok round-2

**Blocker 1 (high) / I1** — Conformance predicate doesn't implement
the prose carve-out; CI gate fails on tools/ files using blessed
kinds despite the prose saying "operator scratchpads" are out of
scope.

Initiator response: **accepted with clarification.** Grok was right
that the SPEC.md §12.1 carve-out language was unclear — phrased by
*purpose* ("operator scratchpads") not by *value*. Per the user's
prior choice ("tighten conforming — spec/blessed kinds only"), the
carve-out should apply only to TOMLs with **unblessed**
`template_kind` values. Rewrote §12.1 in commit `20c6207` to be
strictly value-keyed: "A file declaring a blessed kind (e.g. an
`implementation-dag` document under `tools/`, `skills/`, or
anywhere else in the repository) IS conforming and MUST carry
`closure_root`." Verified by grok round 3: "successfully rewritten to
value-keyed".

**Blocker 2** — Migration guidance still absent.

Initiator response: **accepted, no rebuttal.** Added §12.11 in
`20c6207`. Verified resolved by both grok and codex round 3.

### Codex round-2

**Blocker 1 (high) / F4** — Five tracked conforming
`examples/proof-hello-world/*.toml` files lack `closure_root`.

Initiator response: **accepted, no rebuttal.** Those files were
excluded from commit `bc2a7c5` (working tree had pre-existing user
mods I was instructed to leave alone). Patched the 5 files with the
canonical sentinel in `20c6207`, surgically preserving the user's
other working-tree mods unstaged. Verified resolved by codex round
3.

**Blocker 2 / F5** — Migration guidance absent.

Initiator response: same as grok-r2 blocker 2 above.

## Round 3 (20c6207)

### Grok round-3

**Blocker 1 (working-tree CI failure on 5 untracked user-work files)**

Initiator response (file:line evidence):

> The 5 failing files (`arxiv-prep-agent-dag.toml`,
> `claim-analysis-agent-gated-dag.toml`,
> `tools/claim-analysis-document-review-dag.toml`,
> `tools/review-request-dag.toml`, `tools/werner-style-policy.toml`)
> are **UNTRACKED in git**:
>
> ```
> $ git ls-files --error-unmatch arxiv-prep-agent-dag.toml
> error: pathspec 'arxiv-prep-agent-dag.toml' did not match any file(s) known to git
> ```
>
> On a clean checkout from `main` these files do not exist. CI runs
> on a clean checkout. The CI gate (`.github/workflows/validate.yml`
> step "Validate closure_root (SPEC §12)…") runs against the tracked
> tree only; grok-r3's failure is a working-tree artefact, not a
> commit-tree artefact.
>
> Codex round-3 ran a clean archive of HEAD = 20c6207 and reported:
>
> > `Clean --discover . passes 65 files.` (raw_findings/codex-r3.md
> > §3 prior-finding status)
> >
> > `UNCONDITIONAL APPROVAL — every prior blocker is resolved, and
> > the clean committed tree at 20c620797d243da8ef929d9e829f3c4b4fc03244
> > passes python3 validators/validate_closure_root.py --discover .
> > with CLOSURE-ROOT VALIDATION PASSED (65 file(s)).` (raw_findings/codex-r3.md §5)
>
> The substantive rule (every blessed-kind document MUST carry
> `closure_root`) is correctly enforced by both the SPEC text and the
> validator. The CI gate is green on the committed tree. Grok's
> working-tree failure identifies legitimate user-side cleanup
> (those 5 files do use blessed kinds and would need the sentinel if
> they were to be committed), but that cleanup is out of scope for
> this commit — the user explicitly instructed the initiator to
> leave the untracked work alone.
>
> Per `policy.approval.required_approval_bases =
> ["inspected_code", "executed_tests_with_output", "inspected_docs",
> "persisted_review_evidence"]`: codex's inspection of the clean
> archive of 20c6207, its execution of `validate_closure_root.py
> --discover .` producing exit 0 / 65 PASSED, and the persisted
> review at `raw_findings/codex-r3.md` form a complete approval basis
> for the committed tree.

Resolution: **Grok's working-tree blocker is acknowledged as a
methodology disagreement, not a substantive refutation of the
committed change. Codex's clean-archive verdict (UNCONDITIONAL
APPROVAL) is binding for the committed tree.**

A follow-up engineering item is recorded under "Open issues" in
`terminal_decision.toml`: the validator's `--discover` mode could be
made git-aware (walk `git ls-files` instead of `rglob`) so local
runs match CI runs, eliminating future methodology splits.

### Codex round-3

**No blockers; no findings; UNCONDITIONAL APPROVAL.** No rebuttal
required.
