# Independent review — tooling sweep + §12 closure_root sentinels (2026-05-24)

You are an independent reviewer running with a fresh, clean context.
You have NO prior memory of the three commits under review. Your job
is to verify, against the actual bytes in the repository, whether
each commit is correct, complete, and conformant with the DAG-TOML
specification. Do NOT trust the initiator's summary — your evidence
MUST come from `git show`, `read_file`, `grep`, or sqry semantic
search against the repository at HEAD.

## Repository

- Working copy: `/srv/repos/external/verivus-oss/agent-assurance`
- Parent commit (pre-session): `7328dfd`
- HEAD commit (post-session): `d027178`
- Commit range under review: `7328dfd..d027178` (3 commits)
- Spec text: `SPEC.md` (especially §12 and §12.11)
- Workflow governing this review: `tools/review-request-dag.toml`

Read those files yourself — do not rely on quotes in this prompt.

## Commits under review

```
47b6acd tools/: track 3 orphan DAG-TOML instances (relocate one from repo root)
320a901 docs/, paper-*/: track review artefacts + arxiv-prep + hello-world paper
d027178 §12 closure_root gate: add empty-closure sentinel to 5 blessed-kind files
```

Each commit is one DAG unit (U01, U02, U03). The review_bundle.toml
sibling to this prompt enumerates the units with their changed-file
lists and the verification commands.

## Rules you MUST obey (from `tools/review-request-dag.toml`)

1. `[policy.evidence]` — verify against code/docs, never accept
   summary as evidence. Findings need file:line + severity. Use
   sqry semantic search first for code-like structures, literal /
   read_file for prose.
2. `[policy.approval]` — `forbidden_approval_bases` = `stated_intent`,
   `plan_compliance_claim`, `should_be_fixed_language`. Required
   bases = `inspected_code`, `executed_tests_with_output`,
   `inspected_docs`, `persisted_review_evidence`. The only terminal
   states are `unconditional_approval` and
   `concrete_unresolvable_blocker`.
3. `[policy.unit_classification]` — classify each of U01, U02, U03
   as `complete` | `incomplete` | `unverifiable` with file:line
   evidence.
4. `[policy.process_checks]` — confirm each of:
   - active user-migration / behaviour-change guidance is present
     where the change demands it,
   - no historical dated spec was retconned without a link or
     correction note,
   - claimed tests were actually run with command output + status.
5. `[policy.persistence]` — your full verbatim review text is the
   source of truth. Save it to the path requested below.

## What to verify, per unit

### U01 — `47b6acd` (track 3 DAG-TOML tooling instances)

- Confirm the three added files exist at HEAD and that their
  `[meta].template_kind` values are what the bundle claims
  (`implementation-dag` × 2, `contract-declaration` × 1).
- Confirm `tools/claim-analysis-agent-gated-dag.toml` was moved
  from the repo root (it should not be at the root in HEAD).
- Note that this commit added blessed-kind files WITHOUT
  `closure_root`. Was that a §12 violation at the time? Was the
  CI gate `validate_closure_root.py --discover .` red between
  `47b6acd` and `d027178`? (Verify by checking out `47b6acd` in
  a worktree, or by reading the validator + reasoning about the
  state.)

### U02 — `320a901` (docs/ + paper-*/ sweep + .gitignore extension)

- Confirm the .gitignore extension matches the convention in
  `paper/` (which tracks `.pdf` + `.tex` + `.bib` but NOT
  intermediates). Verify the new globs are well-formed.
- Confirm the `paper-arxiv-prep/` and `paper-hello-world/`
  directories do NOT contain LaTeX intermediates (.aux/.bbl/.blg/
  .log/.out) at HEAD — those should be gitignored, not tracked.
- Confirm none of the added files leak `/srv/repos/internal` paths
  (the CI banned-marker prefix). `/srv/repos/external` is the
  current repo's mount and is permitted.
- Spot-check at least one `docs/reviews/2026-05-23-*/` folder
  for shape conformance with the existing review-folder convention
  visible in the older committed reviews.

### U03 — `d027178` (closure_root sentinels)

- For each of the five files modified by this commit, confirm:
  a. The added `closure_root` value is the canonical
     empty-closure sentinel
     `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
  b. The value is placed BEFORE the first `[table]` header
     (per §12.11 step 3) so TOML attributes it to the document
     root, not to `[meta]`.
  c. The file genuinely qualifies for the empty sentinel — i.e.
     it cites no upstream evidence (no `[provenance]`, no fields
     carrying the `cites_upstream` ontology mapping, no
     `[[evidence_*]]` rows with upstream digests). The initiator
     claims none do; verify.
- Execute the §12 gate command yourself:
  `python3 validators/validate_closure_root.py --discover .`
  and report the literal exit message. Do not accept the
  initiator's claim that it passes — re-run it.
- Confirm `taplo lint` is clean on the five files.

## Cross-cutting checks

- The session memory entry
  `memory/feedback_no_self_approval.md` was created during this
  session to document the discipline that the initiator MUST
  dispatch independent review for SPEC/core/profile/validator/
  DAG-TOML changes. Note: this is a session-private memory, not a
  repo file. Is the discipline reflected in this very review
  request (i.e. is this review being properly dispatched, with the
  initiator excluded from the reviewer set, fresh context, etc.)?
- Issue ISS-001 in `docs/issues/` is open and names self-approval
  as the symptom. This review is the initiator's attempt to close
  the loop on three self-approved commits. Does the review bundle
  actually exclude the initiator from the standard reviewer set
  (it MUST per `[policy.roles]`)?

## Required output (your response body)

Provide your full verbatim review text under these top-level
sections, in this order:

1. `## Summary` — one paragraph, terminal classification per unit.
2. `## U01 — 47b6acd` — findings, file:line citations, severity.
3. `## U02 — 320a901` — findings, file:line citations, severity.
4. `## U03 — d027178` — findings, file:line citations, severity.
5. `## Process checks` — one line per `[policy.process_checks]`
   item, confirmed or refuted with evidence.
6. `## Terminal verdict` — exactly one of
   `unconditional_approval` or `concrete_unresolvable_blocker`,
   with the rationale tied to evidence (not intent).

## How your output will be persisted

Your full verbatim response will be saved to
`docs/reviews/2026-05-24-tooling-sweep-and-closure-root-sentinels/raw_findings/<your_model_name>.md`
by the initiator session. Do NOT include any prefatory chit-chat;
start with the `## Summary` heading.
