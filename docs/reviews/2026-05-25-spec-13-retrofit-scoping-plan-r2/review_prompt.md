# Round-2 review — §13 retrofit plan blocker disposition (2026-05-25)

Fresh-context reviewer. Narrow scope: verify commit `073d5c5`
closes the three blockers codex filed in r1, without introducing
new defects.

## Background — what r1 said (verify, don't trust)

r1 session: `docs/reviews/2026-05-25-spec-13-retrofit-scoping-plan/`

- **codex** (`raw_findings/codex.md`): `concrete_unresolvable_blocker`.
  Three findings:
  - U07-F1 (high): SDP Family C envelope validator-incompatible.
  - U07-F2 (medium): observation-record.v1 description fits only
    cost-record.
  - U07-F3 (medium): plan §9 internal contradiction.
- **gemini** (`raw_findings/gemini.md`): `unconditional_approval`,
  flagged the same SDP and §9 issues as "minor".
- **grok** (`raw_findings/grok.md`): `unconditional_approval`,
  flagged same issues as "caveats".

Codex's blocker bound per strongest-evidence rule (it read
`validate_abstraction_class.py:182,214` to find the validator's
accepted vocabularies; gemini and grok did not).

## Repository

- Working copy: `/srv/repos/external/verivus-oss/agent-assurance`
- Parent (pre-r2): `c88f7ea`
- HEAD (post-r2): `073d5c5`
- Commit range: `c88f7ea..073d5c5` (1 commit; single file modified)
- Plan under review: `docs/planning/2026-05-25-spec-13-retrofit-scoping.md`
- r2 bundle: `docs/reviews/2026-05-25-spec-13-retrofit-scoping-plan-r2/review_bundle.toml`

## Rules (`tools/review-request-dag.toml [policy.*]`)

Verify against bytes; never accept summary. File:line + severity.
`forbidden_approval_bases`: stated_intent, plan_compliance_claim,
should_be_fixed_language. Terminal: `unconditional_approval` or
`concrete_unresolvable_blocker`.

## What to verify

### U08 — `073d5c5`

For each of the three blockers, classify as **closed**, **partial**,
or **open** with file:line evidence.

1. **U07-F1 closure (SDP Family C → A).**
   - Read plan row 18 at HEAD. The `Envelope family` column MUST
     read `A`, NOT `**C**`.
   - The plan MUST NOT propose `entropy_source = "system"` or
     `crypto_keys.{sign, verify}` as live envelope fields anywhere
     in §6 / §7 / §8.
   - The §5 paragraph about Family B/C exceptions MAY still
     mention these as historical context (audit trail of why
     round-1 rejected them) — that's intentional. Verify the
     mentions are inside an explanatory paragraph, not in a live
     proposal.
   - Read `validators/validate_abstraction_class.py:180-225` and
     confirm the validator vocabularies codex cited.

2. **U07-F2 closure (taxonomy reframe).**
   - Read plan §6. The taxonomy preamble MUST now state that the
     class id is a producer-attested LABEL / ROLE, not a
     byte-level structural-shape contract.
   - The table column for observation-record.v1's description
     MUST no longer say "closed-vocab dimensions + integer
     quantities". It should be a general role description.
   - A NEW rule MUST appear (in §6 or §7) saying each kind's
     per-kind `[kind.abstraction_class].description` field MUST
     reflect its own structural shape.
   - Confirm cost-record's existing description at
     `profiles/cost/cost-record-kind.toml:282-286` is cited as
     the canonical shape.

3. **U07-F3 closure (§9 contradiction).**
   - Run: `grep -n 'MUST flip' docs/planning/2026-05-25-spec-13-retrofit-scoping.md`
     This MUST return zero matches.
   - Read plan §9 in full. It MUST contain a single coherent
     statement about closure_root: the sentinel persists per
     SPEC §12.1 / §12.11; the descriptor file's SHA-256 changes
     but its declared closure_root value does not.
   - The §13.4-vs-§12.1 SPEC defect MUST be acknowledged as
     out-of-scope and filed as ISS-005 candidate (§11).

### No new defects

- `git show --stat 073d5c5` MUST show only
  `docs/planning/2026-05-25-spec-13-retrofit-scoping.md` modified.
  No SPEC.md, no kind descriptors, no validators touched.
- `python3 validators/validate_closure_root.py --discover .` MUST
  still exit 0.
- No retcon: `c88f7ea` MUST still be an ancestor of `073d5c5` in
  `git log`.

### Cross-cutting

- Plan §13 (Revision history) — verify it accurately describes
  the round-1 → round-2 fixes (not over-claiming, not retconning).
- Plan §12 (Open questions) — Q4 about SDP envelope MUST be
  dropped (already answered by F1 closure). Q2 MUST be reworded
  to match the reframed taxonomy.

## Required output (no prefatory chit-chat)

1. `## Summary` — terminal classification for U08.
2. `## U08 — 073d5c5` — findings, file:line.
3. `## U07-F1 disposition` — closed / partial / open + evidence.
4. `## U07-F2 disposition` — closed / partial / open + evidence.
5. `## U07-F3 disposition` — closed / partial / open + evidence.
6. `## No new defects` — confirmation.
7. `## Process checks` — one per `[policy.process_checks]` item.
8. `## Terminal verdict` — `unconditional_approval` or
   `concrete_unresolvable_blocker`. Rationale tied to bytes /
   executed commands.

Persistence: your verbatim response will be saved to
`docs/reviews/2026-05-25-spec-13-retrofit-scoping-plan-r2/raw_findings/<your_model_name>.md`.

Start with `## Summary`.
