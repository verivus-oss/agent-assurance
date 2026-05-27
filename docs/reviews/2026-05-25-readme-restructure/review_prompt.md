# README restructure — independent review (2026-05-25)

Fresh-context reviewer. **Narrow scope**: a single-file
documentation change (`README.md` only; +139 / -46 lines). No
SPEC, profile, validator, ontology, kind descriptor, or example
bytes are modified.

## Repository

- Working copy: `/srv/repos/external/verivus-oss/agent-assurance`
- Parent commit: `1f08dea` (Untrack paper-arxiv-prep/)
- HEAD: `b759eaf` (the commit under review)
- Commit range: `1f08dea..b759eaf` (1 commit; 1 file modified)
- Bundle: `docs/reviews/2026-05-25-readme-restructure/review_bundle.toml`

## What landed

A comprehensive refresh of `README.md` for the post-§13,
multi-profile state of the repository. The previous README was
last touched at `bc2a7c5` (SPEC §12 era) and predated SPEC §13
(abstraction-class + capability-envelope), the Cost + Disclosure
profiles, INV06, the safe-Rust + safe-Go primary validators, the
toml-test parser-conformance harnesses, the deployment tiers, and
the first calendar-UTC release tag.

The new README adds:

- a Status table covering core + agent-assurance + cost +
  disclosure surfaces with calendar-UTC tag-convention text;
- a "Start Here" section re-grouped by reader role (understand
  format / author / enforce policy / implement validator);
- a fuller Repository Map (Makefile, all 7 tools/* subdirs,
  per-profile one-line descriptions);
- a NEW "Validation tooling" section describing the three-layer
  triad (syntax / parser conformance / semantics);
- a richer "Local Validation" block;
- a Governance section surfacing the multi-LLM review requirement.

**The load-bearing claim**: every factual statement the README
makes about the repo matches the on-disk state at `b759eaf`, and
every internal link resolves. The README is the public face of
the spec; a falsehood here misleads every new reader.

## Rules (`tools/review-request-dag.toml [policy.*]`)

Verify against bytes; never accept the bundle's summary as evidence.
Findings carry file:line + severity. Forbidden approval bases:
`stated_intent`, `plan_compliance_claim`, `should_be_fixed_language`.
Required bases: `inspected_code`, `executed_tests_with_output`,
`inspected_docs`, `persisted_review_evidence`. Terminal states:
`unconditional_approval` or `concrete_unresolvable_blocker`.

## What to verify (units U01–U06)

Per the bundle. Highlights:

- **U01 — factual accuracy.** Every concrete claim (SPEC §13
  exists at SPEC.md:1195; five deployment tiers; Cost +
  Disclosure profile contents; INV06 in
  `profiles/agent-assurance/gate-decision-kind.toml`; Rust + Go
  primary validators; Rust parser-conformance shim; Makefile
  targets) must match the on-disk state.

- **U02 — link integrity.** All `[label](path)` and
  `[label](path#anchor)` resolve. Re-extract every link target
  yourself and check on disk. For SPEC.md anchors, compute the
  GitHub-flavoured anchor from the `## ` / `### ` headings and
  confirm the cited anchor exists.

- **U03 — reader-role grouping coherence.** The "Start Here"
  section claims to be grouped by reader role. Check that each
  row sits in the appropriate group.

- **U04 — status-table version numbers.** Cross-check every
  `schema_version` / `ontology_version` claim against the
  authoritative on-disk file.

- **U05 — Local Validation block executable.** Every validator
  script, make target, example path, and binary path cited in
  the fenced shell block must resolve.

- **U06 — Governance claim matches policy file.** Confirm
  `tools/review-request-dag.toml` exists and its `[policy.*]`
  tables match the README's description.

## Reproducing the link audit (suggested)

```bash
cd /srv/repos/external/verivus-oss/agent-assurance

# Extract every Markdown link target (path or path#anchor) from README.md
grep -oE '\]\(([^)]+)\)' README.md | sed -E 's/^\]\(//; s/\)$//' | sort -u

# For each repo-relative path: ls it.
# For each SPEC.md#anchor: compare against the headings:
grep -nE '^##+ ' SPEC.md
```

Then cross-check Status table versions:

```bash
grep -nE '^schema_version|^ontology_version' core/ontology.toml \
  profiles/agent-assurance/ontology.toml \
  profiles/cost/PROFILE.toml \
  profiles/disclosure/PROFILE.toml
```

## Process notes

- Search order: prefer `sqry` semantic search first; fall back
  to literal grep only for exact-string confirmation.
- This is a docs-only change. The
  `[[feedback_no_self_approval]]` rule's narrow letter is about
  SPEC/core/profile/validator/DAG-TOML changes. The initiator
  dispatched this review anyway because the README is the public
  face of the spec and a falsehood here is a stated contract
  with every new reader.

## Output format

Persist your full review verbatim to
`docs/reviews/2026-05-25-readme-restructure/raw_findings/<reviewer>.md`
(where `<reviewer>` is `codex`, `gemini`, or `grok`). Conclude
the file with:

```
Terminal verdict: unconditional_approval
```

or

```
Terminal verdict: concrete_unresolvable_blocker
Blocker: <one paragraph; cite file:line>
```
