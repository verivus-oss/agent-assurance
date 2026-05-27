# SPEC §13 Phase 2 retrofit — r2 review (2026-05-25)

Fresh-context reviewer. Narrow scope: verify commit `6b63860`
closes the codex r1 U08 blocker without introducing new defects, and
confirm the U12 disposition is sound.

## Background — what r1 said (verify, don't trust)

R1 session: `docs/reviews/2026-05-25-spec-13-phase-2-declarations/`

- **codex** (`raw_findings/codex.md`): `concrete_unresolvable_blocker`.
  - U08 (BLOCKER, high): the §13 header comment at
    `profiles/agent-assurance/threat-model-kind.toml:156`
    introduced a second occurrence of the IJB-forbidden phrase
    "risk posture" in the file, violating the kind's existing
    IJB-stance note (lines 64-77 pre-commit) which states the
    phrase appears "only in this note where its forbidden status
    is the topic".
  - U12 (informational): three of the nine retrofitted descriptors
    have closure_root on lines 9 / 11 / 13 rather than line 5.
    Codex confirmed these line positions PRE-EXIST at parent
    commit `ec37e7d` (raw_findings/codex.md:195-201). Sentinel
    VALUE is preserved everywhere; §12 validator passes.
- **gemini** (`raw_findings/gemini.md`): `unconditional_approval`.
- **grok** (`raw_findings/grok.md`): `unconditional_approval`.

Codex's U08 finding bound per strongest-evidence rule (it re-ran the
exact grep command and quoted the two-line output).

## Repository

- Working copy: `/srv/repos/external/verivus-oss/agent-assurance`
- Parent (pre-r2): `092bccc`
- HEAD (post-r2): `6b63860`
- Commit range: `092bccc..6b63860` (1 commit; 1 retrofit file modified
  + the r1 review session persisted)
- R2 bundle: `docs/reviews/2026-05-25-spec-13-phase-2-declarations-r2/review_bundle.toml`

## Rules (`tools/review-request-dag.toml [policy.*]`)

Verify against bytes; never accept summary. File:line + severity.
`forbidden_approval_bases`: stated_intent, plan_compliance_claim,
should_be_fixed_language. Terminal: `unconditional_approval` or
`concrete_unresolvable_blocker`.

## What to verify

### U14 — U08 closure (risk-posture leak removed)

Run:

```sh
grep -n 'risk posture' profiles/agent-assurance/threat-model-kind.toml
```

The output MUST contain exactly ONE match:

```
74:for the full reasoning. The IJB-forbidden phrase "risk posture"
```

This is the original pre-existing IJB-stance note at line 74; it is
the allowed location per the kind's own rule. Any second match
re-opens the U08 blocker.

Then inspect the rewritten §13 header comment:

```sh
sed -n '140,170p' profiles/agent-assurance/threat-model-kind.toml
```

The comment block from line 143 to roughly line 155 MUST:
- Still explain that the kind is a threat-declaration that enumerates
  ways the change can go wrong.
- Still reference the IJB-stance note location (lines 64-77).
- NOT contain the literal phrase "risk posture" anywhere.

Per-kind validator:

```sh
python3 validators/validate_abstraction_class.py --repo-root . \
  profiles/agent-assurance/threat-model-kind.toml
python3 validators/validate_ijb_conformance.py \
  profiles/agent-assurance/threat-model-kind.toml
python3 validators/validate_kind_descriptor.py \
  profiles/agent-assurance/threat-model-kind.toml \
  --repo-root . --check-references-exist
```

All MUST exit 0 with PASS.

### U15 — aggregate validators still green

The fix is a comment-only edit; the aggregate run MUST still report
the same totals:

```sh
python3 validators/validate_abstraction_class.py --repo-root . \
  core/*-kind.toml profiles/agent-assurance/*-kind.toml \
  profiles/disclosure/*-kind.toml profiles/cost/*-kind.toml
# 19 file(s) checked; 14 declared a §13 block

python3 validators/validate_closure_root.py --discover .
# CLOSURE-ROOT VALIDATION PASSED (74 file(s)).

taplo lint core/*-kind.toml profiles/*/*-kind.toml
# no FAIL
```

### U16 — U12 disposition (line-5 quibble)

Verify that the three non-line-5 sentinel positions PRE-EXISTED at
the parent commit `ec37e7d`:

```sh
git show ec37e7d:core/implementation-dag-kind.toml | grep -n 'closure_root'
git show ec37e7d:core/profile-descriptor-kind.toml | grep -n 'closure_root'
git show ec37e7d:profiles/disclosure/disclosure-attestation-kind.toml | grep -n 'closure_root'
```

Expected outputs:
- `9:closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"`
- `11:closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"`
- `13:closure_root = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"`

The line positions are determined by each file's pre-existing
header-comment length; the Phase 2 retrofit did NOT change them.

The substantive contract (per SPEC §12.11 + plan §9) is that the
sentinel VALUE is preserved. Verify:

```sh
python3 validators/validate_closure_root.py --discover .
# MUST exit 0 (sentinel value is preserved; the §12 validator
# does NOT check line position)
```

This was prompt-spec imprecision in the r1 prompt's "at line 5"
phrasing. Classify U16 as **closed / not-a-defect** if the parent
commit evidence confirms the line positions pre-existed AND the §12
validator exits 0.

### No new defects

```sh
git show --stat 6b63860
git diff --name-only 092bccc..6b63860
```

Expected: exactly 6 files modified:
- `profiles/agent-assurance/threat-model-kind.toml` (the U08 fix)
- `docs/reviews/2026-05-25-spec-13-phase-2-declarations/raw_findings/codex.md`
- `docs/reviews/2026-05-25-spec-13-phase-2-declarations/raw_findings/gemini.md`
- `docs/reviews/2026-05-25-spec-13-phase-2-declarations/raw_findings/grok.md`
- `docs/reviews/2026-05-25-spec-13-phase-2-declarations/review_bundle.toml`
- `docs/reviews/2026-05-25-spec-13-phase-2-declarations/review_prompt.md`

No SPEC.md, no plan file, no other kind descriptors, no validators
touched.

## Required output (no prefatory chit-chat)

1. `## Summary` — terminal classification for this commit.
2. `## U14 — U08 closure` — closed / partial / open + evidence.
3. `## U15 — aggregate validators` — exit codes + summary lines.
4. `## U16 — U12 disposition` — closed (not-a-defect) /
   partial / open + parent-commit evidence + validator output.
5. `## No new defects` — confirm exactly 6 files modified; confirm
   none of the forbidden files touched.
6. `## Process checks` — one per `[policy.process_checks]` item.
7. `## Terminal verdict` — `unconditional_approval` or
   `concrete_unresolvable_blocker`. Rationale tied to bytes /
   executed commands.

Persistence: your verbatim response will be saved to
`docs/reviews/2026-05-25-spec-13-phase-2-declarations-r2/raw_findings/<your_model_name>.md`.

Start with `## Summary`.
