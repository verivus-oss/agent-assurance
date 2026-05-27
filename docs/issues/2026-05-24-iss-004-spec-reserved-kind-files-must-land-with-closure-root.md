---
id: ISS-004
title: Spec-reserved-kind files MUST land with `closure_root` in the same commit
status: closed
severity: medium
opened: 2026-05-24
opened_in_commit: 884f290
closed: 2026-05-25
closed_by: 79fe0aa
classification: §12 conformance / commit-sequencing discipline
---

## Symptom

A spec-reserved `[meta].template_kind` document was added to a commit
without `closure_root`, and the missing field was added in a
subsequent commit two commits later. Between the two commits,
`validators/validate_closure_root.py --discover .` was red on
`main`.

Observed instance (2026-05-24 session):

- Commit `47b6acd` added three spec-reserved-kind files in `tools/`
  (`claim-analysis-agent-gated-dag.toml` and
  `review-request-dag.toml` declaring `implementation-dag`;
  `werner-style-policy.toml` declaring `contract-declaration`).
  None carried `closure_root`. Validator FAILED at this commit.
- Commit `320a901` (one commit later) did not touch the §12 surface.
- Commit `d027178` (two commits after `47b6acd`) finally added the
  canonical empty-closure sentinel to those three files and to
  two other pre-existing offenders (`arxiv-prep-agent-dag.toml`,
  `tools/claim-analysis-document-review-dag.toml`).

This was caught only because the user asked for a status of the
spec, prompting a local `--discover` run that showed the gate was
red. The red CI window between `47b6acd` and `d027178` was real.

Independent confirmation in the round-1 review of the session:
`docs/reviews/2026-05-24-tooling-sweep-and-closure-root-sentinels/raw_findings/codex.md`
(finding U01-F1, severity high) and
`docs/reviews/2026-05-24-tooling-sweep-and-closure-root-sentinels/raw_findings/grok.md`
(§12 violation introduced, severity high).

## Why it matters

`SPEC §12.1` requires every conforming document to carry
`closure_root` at the root. The brittleness-propagation property
described in `SPEC §12.2` and `SPEC §12.4` depends on every
conforming document being inside the closure graph at all times.
A commit that adds a spec-reserved-kind document without `closure_root`
breaks the invariant *for that commit*, regardless of whether a
later commit repairs it. The git history then contains states in
which the spec's own §12 gate would reject the tree, which:

1. Makes `git bisect` over §12-related work unreliable.
2. Leaves the door open to merges or releases cut from an
   intermediate commit that silently lacks `closure_root` on a
   tracked artefact.
3. Violates the producer-side responsibility named in
   `[[memory/project_spec_ethos.md]]` (invalidations must
   propagate visibly; producer-side responsibility is one half
   of the contract).

## Safeguard (what would prevent recurrence)

The mechanism already exists; the gap is discipline, not tooling.

### Safeguard A — convention (the rule itself)

Any commit that adds or modifies a `[meta].template_kind` field
declaring a spec-reserved kind MUST also ensure the file's `closure_root`
is present and correct in the same commit. The author runs
`python3 validators/validate_closure_root.py --discover .` locally
before `git commit`, and does not commit if the validator is red.

This is the minimal change. It costs nothing and prevents the
defect by construction. Same kind of discipline as `cargo build`
before pushing — the tool exists, the rule is to run it.

### Safeguard B — pre-commit hook (optional)

Contributors who want belt-and-braces can install a git pre-commit
hook that runs `validate_closure_root.py --discover .` on the
staged tree and aborts the commit on failure. This is per-contributor
opt-in, not enforced by the repo (the repo cannot mandate hook
installation).

### Safeguard C — non-mechanical

- Add a paragraph to `CONTRIBUTING.md` naming this issue and
  the Safeguard A discipline. This is the contributor-visible
  artefact — the one humans and other agents can actually read.
- Optional: agent-based contributors may add the rule to their
  per-session host-specific auto-memory (e.g. Claude Code's
  `~/.claude/projects/<project-slug>/memory/`) as an
  implementation-side convenience. Such auto-memory is NOT
  contributor-visible and MUST NOT be cited as the load-bearing
  safeguard. `CONTRIBUTING.md` is.

Per the user feedback in the 2026-05-24 session (the same session
that closed ISS-001 — see
[ISS-001 closing note](2026-05-23-iss-001-self-approval-discipline.md)):
do NOT propose a CI gate as a substitute for the discipline. The
validator already runs in CI (`.github/workflows/validate.yml`
line ~180); CI red is the symptom of this issue, not the prevention.

## Resolution steps (the actionable fix)

1. **CONTRIBUTING.md** (load-bearing). Add a "Review Discipline"
   section 2 to `CONTRIBUTING.md` stating: "Any commit that adds
   or modifies a `[meta].template_kind` field declaring a spec-reserved
   kind MUST also carry the file's `closure_root` in the same
   commit. Run `python3 validators/validate_closure_root.py
   --discover .` locally before `git commit`; do not commit if
   red." Cite this issue as the worked counter-example.
2. **Local Checks** (`CONTRIBUTING.md`). Add the validator command
   to the existing "Local Checks" section so contributors see it
   in the same place as the other pre-commit validators.
3. **Optional auto-memory** (per-agent convenience, not load-bearing).
   Agent-based contributors may save the rule to their per-session
   auto-memory (e.g. Claude Code's
   `~/.claude/projects/<project-slug>/memory/`); this is a
   per-agent implementation-side convenience that complements
   `CONTRIBUTING.md`, not a substitute for it.
4. **Optional pre-commit hook stub.** Document (not install) the
   git pre-commit hook in CONTRIBUTING.md or a new
   `tools/hooks/pre-commit.example` for contributors who want it.

## Acceptance criteria

- `CONTRIBUTING.md` includes the discipline under "Review
  Discipline" section 2 and the validator command under "Local
  Checks", linking to this issue.
- A future commit that adds a `[meta].template_kind = "..."`
  declaration without `closure_root` either does not happen
  (discipline held), or is caught by the contributor's pre-commit
  hook (Safeguard B), or is caught by CI on push (existing gate).
- (Optional / per-agent.) Agent-based contributors that use
  session-private auto-memory may save a feedback entry for the
  rule. This is a per-agent convenience, not a load-bearing
  acceptance criterion.

## Worked counter-example

The 2026-05-24 session itself: `47b6acd` added three spec-reserved-kind
files without `closure_root`. A pre-commit run of
`validate_closure_root.py --discover .` would have shown 5 failures
(3 newly introduced + 2 pre-existing) and the fix would have been
to add the empty sentinel to all three in `47b6acd` itself, rather
than deferring it to `d027178` two commits later. The discipline
gap is one habit-change away from being closed for all future work.

## Closing note (2026-05-25)

Closed by commit `79fe0aa`, which added the "Review Discipline"
section to [`CONTRIBUTING.md`](../../CONTRIBUTING.md). Section 2
of that section is verbatim the discipline this issue exists to
document, namely: any commit that adds or modifies a
`[meta].template_kind` field declaring a spec-reserved kind MUST also
carry the file's `closure_root` in the same commit, verified
locally with
`python3 validators/validate_closure_root.py --discover .` before
`git commit`. The same validator runs in CI at
`.github/workflows/validate.yml:178-199`, so CI red is the
symptom; the contributor-visible rule in CONTRIBUTING.md is the
prevention.

The acceptance criterion "CONTRIBUTING.md includes the discipline
under Review Discipline section 2 and the validator command under
Local Checks, linking to this issue" is satisfied by `79fe0aa`
(verified by all three reviewers in
`docs/reviews/2026-05-24-iss-001-closure-and-iss-004-filing-r2/`).
The other two criteria are forward-looking ("a future commit that
adds a spec-reserved `template_kind` without `closure_root` either does
not happen or is caught"); they cannot be proven satisfied today
but they are now mechanically supported by the documented rule
plus the live CI gate, and any recurrence will re-open this issue.
