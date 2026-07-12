# Design review evidence: closure-record-form-promotion planning bundle

Review of `docs/planning/closure-record-form-promotion/` (U01 of its
implementation DAG), run 2026-07-12/13 via the multi-LLM gateway per
`tools/review-request-dag.toml` process rules: independent external models
verified every design claim against the repository files themselves; the
initiator did not approve.

## Verdicts

| Reviewer | Final verdict | Iterations | Basis |
|---|---|---|---|
| codex | APPROVAL WITH REQUIRED FIXES (5 groups) | 2 (round 1: BLOCKER, converted on a concrete U02 amendment) | 21-min tool-driven review, file reads across the repo, TOML 1.1 grammar cross-check, live execution of both primary validators |
| gemini | APPROVAL WITH REQUIRED FIXES (4) | 2 (round 1: BLOCKER, same finding, converted on the same amendment) | File reads with line citations; independently recomputed the sha256 record stream |
| grok | APPROVAL WITH REQUIRED FIXES (7) | 1 | File reads; independently recomputed the four-record closure root |

No reviewer approved on intent; every consequential finding was re-verified
against the files by the orchestrating session before adjudication.

## Load-bearing findings and their disposition (all applied 2026-07-12/13)

1. P0 witness-downgrade bypass (all three; round-1 BLOCKER): field-presence
   closure emission plus RKV03 permitting lingering witness fields at
   `present = false` keeps the record set and root identical. Fixed: RKV03
   amendment (witness digest/identity fields MUST be absent when
   `present = false`), lingering-digest negative fixture, enforcement
   boundary recorded (design 3.2, U02/U08, C02).
2. P0 pin-resolution row false (all three): no closure implementation reads
   `framework_profile`; reverse-DNS names are not hard-rejected on missing
   descriptors; silent no-pins fall-through is a pin bypass. Fixed: recast as
   a NEW U02-frozen closure-path rule with a recommended kind-keyed
   resolution (design 3.4, C01).
3. Grammar freeze completeness (codex/grok): byte-frozen field-path regex,
   `closure_root` self-pin exclusion, `extends` inheritance with post-union
   duplicate rejection, sha256-only pin alphabet. Fixed (design 3.1).
4. Invariant id collision + under-scope (grok, gemini-confirmed): INV06 is
   taken; the new invariant is INV07 and lands in
   `core/profile-descriptor-kind.toml` plus both primaries, not Python only.
   Fixed (design 3.1/3.3, U04 rescoped; critical path now 960 LOC).
5. Fixture/CI inventory (codex): the four blessed api-snapshot negatives need
   re-rooting (CI closure-discovers the whole tree); the SPEC 12.1
   profile-input enumeration needs amending. Fixed (U03/U08, design 3.3/3.5).
6. The `sha256:013f3d34...` guidance was wrong (grok; gemini and the
   orchestrator independently recomputed): the four-record stream over the
   shipped digests equals exactly that value. Fixed (design 3.5, U08).
7. Findings concerning the private downstream repository's sequencing bundle
   (unit-id pattern conformance, a second pinned validator ref, leaf-prehash
   feasibility for its evidence rollup): applied there; redacted here (see
   below).

## Raw findings

`raw_findings/{codex,gemini,grok}.md` are the reviewers' final verdicts.
Findings that concern the private downstream repository are replaced by
explicit `[REDACTED ...]` blocks per the repository rule against citing
private artifacts; the unredacted originals are persisted in that
repository's planning records. No public-bundle finding is altered.
