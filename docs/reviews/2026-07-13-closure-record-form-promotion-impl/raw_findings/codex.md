# U10 implementation review verdict: codex (OpenAI Codex CLI, gateway job 659a67ab-4cf8-49f0-81a7-4f3d01a1be7f)

Round 1, completed 2026-07-12T22:27:00Z (host time), 26.5 minutes wall, exit 0,
15.9M input tokens / 58k output tokens. Deepest of the three reviews: replayed the
full CI negative-agreement block, all sweeps, and constructed novel adversarial
repo-root fixtures under /tmp/crfp-* and /tmp/codex-* (still present on the host).

Orchestrator adjudication: every load-bearing finding was independently reproduced
by the orchestrator before acceptance (see u10-orchestrator-verification-log.md).
Two corrections to codex's text, neither overturning a fix:
(a) the freeze "exactly three keys" rule IS enforced by all three implementations
    (all reject an `extra` key with "INV07: exactly contained_kind / field /
    presence"); what is missing is the sentence in spec.md 12.8.1 itself, so
    fix 4's spec-text half stands as a documentation completeness item;
(b) codex's /tmp/codex-crfp-review/profile-field-trailing-newline.toml is a stale
    copy that also carries the `extra` key (all three reject it on that), but the
    underlying defect is real: an isolated fixture with only
    field = "snapshot.request.descriptor_sha256\n" gives rs=1, go=1, py=0.

## FINAL VERDICT: APPROVAL WITH REQUIRED FIXES

1. Duplicate-profile-name pin-map shadowing (frozen 1.3 escape). Later-discovered
   descriptor with the same profile.name overwrites the pin map, erasing pins:
   an api-snapshot doc with NO framework_profile, NO pins, and the empty sentinel
   root is ACCEPTED by all three. Enforce unique discovered profile names /
   contained-kind ownership before building pin maps.
   - Code: validators/validate_closure_root.py:91 (dict overwrite),
     tools/dagtoml-validate-rs/src/main.rs:3037, tools/dagtoml-validate-go/main.go:2773
   - Repro (orchestrator-confirmed rs:0 go:0 py:0):
     ROOT=/tmp/crfp-duplicate-name; <each validator> --repo-root "$ROOT" "$ROOT/api-snapshot-escape-missing-fp.toml"
2. Descriptor-discovery semantics differ across the triad.
   a. Go skips symlinked profile directories; rs/py follow them. Orchestrator-confirmed
      divergence: go:0 vs rs:1/py:1 on /tmp/crfp-mini-repo/symlink-pinned-escape.toml
      with --repo-root /tmp/crfp-mini-valid (--mode provenance for the primaries).
      Code: tools/dagtoml-validate-go/main.go:2756 (non-following dir walk).
   b. Python merges explicitly-supplied descriptor files into the extends-resolution
      set; rs/go resolve extends only against discovered descriptors. Orchestrator-
      confirmed: the valid parent/child pair /tmp/codex-u10-fixtures/profile-extends-base.toml
      + profile-extends-valid-child.toml passes py, fails rs/go with
      "extends entry does not resolve to a loaded profile-descriptor".
      Code: validators/validate_profile_descriptor.py:471 (CLI merge).
3. Python full-string anchoring defect (frozen byte-grammar divergence, verdict-level).
   re.match + "$" accepts a trailing newline in BOTH the pinned value and the INV07
   field path; rs/go reject. Fix with \Z (or fullmatch) and add tracked regressions.
   - Code: validators/validate_closure_root.py:67 (PINNED_VALUE_RE),
     validators/validate_profile_descriptor.py:66 (CLOSURE_RECORD_FIELD_RE)
   - Repro (orchestrator fixtures): scratchpad/adv/adv5-trailing-newline-pin.toml
     (rs:1 go:1 py:0 via validate_closure_root.py) and scratchpad/adv/e7-field-newline.toml
     (rs:1 go:1 py:0 via --mode profile / validate_profile_descriptor.py).
4. Reconcile freeze text, spec text, and schema through U02 where they disagree:
   spec.md 12.8.1 omits the frozen "exactly three keys" sentence (enforcement exists
   in all three; the normative text does not state it), and freeze 1.4 names
   `attester_observed` where the kind schema implements `snapshot.witness.observed`.
   - Files: spec.md (12.8.1 declaration constraints), research/01-grammar-freeze-decision.md
     section 1.4, validators/validate_api_snapshot.py:255
5. Add tracked C01 parity-matrix coverage and repair evidence claims: corpus lacks
   fixtures for absent when-present, missing/unresolvable framework_profile, unpinned
   kind, descriptor collision, symlink policy, and the newline cases; the record's
   m1-m9 and 30-row baseline artifacts are not in the repo; 80 -> 79 in the record
   (lines 43, 66) and CHANGELOG.md line 15; drop or qualify "byte-identical error sets".
6. Process repairs: CHANGELOG entry for a2d6b92; declare U09's
   .github/workflows/validate.yml deviation; update stale unit statuses in
   implementation-dag.toml (U09 line ~192 still "pending"); mark the pre-freeze
   design doc superseded where it disagrees; fix the EOF whitespace
   (git diff --check planning/closure-record-form-promotion..impl/crfp-u10-verify).

## Attack-surface checklist (codex)

1. Finding (py newline acceptance; go symlink skip). 2. Finding (shadowing escape).
3. Verified (19 excluded negatives asserted; 21 corpus invalids exercised).
4. Verified (extends chain two records; post-union duplicates rejected by all three).
5. Finding (py field-path newline; otherwise parity). 6. Verified with scope note
(py rejects lingering digest; rs/go accept at closure layer; auto rejects only the
intentional source_bytes mismatch). 7. Finding (doc gaps, item 4). 8. Verified
locally. 9. Finding (item 6). 10. Finding (79 vs 80; unreproducible cited artifacts).

## Non-reproducible verification-record claims (codex)

- 80-file sweep count (actual 79 under exact CI exclusions).
- m1-m9 synthetic parity matrix and the 30-row baseline comparison: no tracked
  fixture, script, or output in the repository.
- The 100-of-105 U02 compatibility-sweep output is not persisted.
- "byte-identical error sets" for INV07 (three different presence-set renderings).
