# U10: cross-implementation verification record

Status: sweep complete 2026-07-13; independent implementation review
dispatched per the no-self-approval rule (evidence to be appended under
`docs/reviews/` before merge). Nothing merges on this record alone.

## The stack under verification

Stacked on the planning branch (U01/U02 recorded there; GO 2026-07-13):

| Commit | Unit |
|---|---|
| d22bd8f | U03 spec text (12.1, 12.8.1, 6.1, 12.9) |
| dfe2a9d | U04 INV07 in all three profile-descriptor validators + kind declaration + negative fixture + CI wiring |
| bcf5142 | U05 Python closure pinned records |
| a2d6b92 | U05 follow-up: dedup by (field, presence), extends double-emission fix |
| b8ddbcf | U06 Rust primary pinned records |
| 0bdfdae | U07 Go primary pinned records |
| dbf7dd0 | U08 atomic: profile pin, kind prose/RKV01/RKV03, fixtures, sweep exclusion |
| 2da8769 | U09 conformance corpus + runner Python closure step |

## Contract evidence (sweep of 2026-07-13; full output in the review packet)

- **C01 cross-implementation parity: HOLDS.** `make dagtoml-conformance`:
  25 cases (21 pre-existing implementation-dag + 4 new api-snapshot),
  rs/go/py agree on all; the runner now executes
  `validate_closure_root.py` on every fixture of every kind, so the
  Python side of closure parity is exercised directly (the U09 change
  that makes C01 non-vacuous). The failure-mode parity matrix was
  additionally exercised against a synthetic pinning profile during
  U05-U07 (nine cases, m1-m9, including the extends single-emission
  case; all three verdict-identical).
- **C02 cascade-break / stripping detection: HOLDS.**
  `examples/negative/api-snapshot-witness-stripped.toml` (stale
  four-record root, witness table removed) is rejected by all three
  closure implementations; the conformance corpus repeats the case. The
  complementary downgrade (`present = false`, lingering
  `attestation_sha256`) is rejected by amended RKV03 at the Python kind
  layer (`api-snapshot-witness-lingering-digest.toml`), with the
  enforcement boundary recorded in the kind descriptor and the freeze
  decision (the primaries do not implement RKV03).
- **C03 backward compatibility: HOLDS.** Closure discover across the
  tree passes (80 conforming files after the asserted-negative
  exclusions); the only re-rooted documents are the enumerated
  com.verivus.runtime instances from the U02 sweep (the example, four
  blessed negatives) plus the two new negatives and the polarity-inverted
  bad-closure fixture, all landed in U08. Documents of unpinned kinds
  were verified byte-identical against pre-change binaries during
  U06/U07 (30-row baseline comparison, "IDENTICAL TO BASELINE").
- **C04 enumerability: HOLDS.** The pins are readable from
  `profiles/com.verivus.runtime/PROFILE.toml` alone; INV07 is enforced
  by `validate_profile_descriptor.py` AND both primaries with
  byte-identical error sets on
  `examples/negative/profile-descriptor-bad-closure-record.toml`
  (`--mode profile` in both), wired into the CI negative-agreement step.
- **C05 posture exclusion: HOLDS.** INV07 rejects `meta.*`/posture pins
  (fixture entry 1); a posture-only flip of the shipped example
  (`confidentiality` restricted -> public) leaves the root valid
  (demonstrated in the sweep).
- **C06 gate precedence: HOLDS.** The GO record (planning branch,
  ddcd365, 2026-07-13) precedes every implementation commit in the
  stack; no spec/validator/profile/fixture change landed before it.

## Full-sweep results (all PASS)

closure discover 80 files (exclusions are the asserted-negative sets);
dagtoml-conformance 25 cases; profile descriptors x4 in all three
implementations; kind descriptors (profile-descriptor: 7 invariants;
api-snapshot: 4); IJB on both touched descriptors; abstraction class 20
files; local negative-agreement simulation: every wired negative
rejected by every wired implementation; provenance positive on the
example; taplo lint zero errors.

## Deviations from the planned unit file-lists (recorded, not hidden)

1. U04 also modified `.github/workflows/validate.yml` (negative-agreement
   wiring for the INV07 fixture) and added
   `examples/negative/profile-descriptor-bad-closure-record.toml`; the
   planned list named neither (fixtures were called for by the summary).
2. U08 also modified `validators/validate_closure_root.py` (the new
   `--exclude` discover option) and `.github/workflows/validate.yml`:
   the expected-failure convention the design review demanded (codex
   round-1 finding 6) required keeping stale-root closure negatives out
   of the positive sweep, mirroring the pre-existing `[provenance]`
   sweep exclusion. Each excluded path is asserted to fail explicitly in
   the negative-agreement step; exclusions are printed by the validator.
3. U05 gained a follow-up commit (a2d6b92): the design-review-adjacent
   extends double-emission defect found during U06/U07 porting
   (pin dedup must key on (field, presence), not the extends-graph
   root). Proven by the m9 parity case.

## Boundary statements a reviewer should not have to discover

- RKV03 (including the amendment) is Python-kind-layer only; the
  all-three closure-level stripping test is the witness-stripped
  fixture. Porting RKV03 to the primaries is future work, out of this
  promotion's scope, recorded in the freeze decision section 1.4.
- Pinned records are sha256-only (frozen); the kind-layer digest fields
  admit sha384/sha512 in their generic type but the closure layer
  rejects non-sha256 pinned values for this kind.
- The conformance runner's Python verdict is the combination of the
  kind validator and the closure step; rs/go verdicts come from their
  auto modes, which include their closure checks.
