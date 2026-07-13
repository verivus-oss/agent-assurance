# U10 orchestrator independent verification log (Claude, review coordinator; does not approve)

Role note: this log is the coordinator's claim-verification evidence used to adjudicate
reviewer findings. The approving verdicts are the external models' (codex, gemini, grok).

## Baseline (main checkout, branch impl/crfp-u10-verify, c1be19c)

- Triad accepts examples/minimal-api-snapshot.toml (rs 0 / go 0 / py-closure 0 / py-kind 0).
- make dagtoml-conformance: 25 cases, CONFORMANCE PASSED.
- Bare discover: 5 FAILs across 119 files, all intended negatives.
- CI-style discover with 3 excludes: PASSED. Main (dirty) checkout: 80 files.
  Clean worktree at c1be19c: 79 files. Delta identified by file-list diff:
  tools/werner-style-policy.toml, gitignored local file (.gitignore:78), absent from
  the commit. The record's "80" therefore does not reproduce on the committed tree.
- taplo lint exit 0. Abstraction class: 20 files PASS. 4 profile descriptors pass in
  all three. profile-descriptor-kind: 7 invariants; api-snapshot-kind: 4. Provenance
  positive on the example passes.

## Attack-surface evidence (orchestrator's own runs)

1. Triad parity: negatives bad-closure and witness-stripped rejected by rs/go/py closure.
   Adversarial set (scratchpad/adv): legacy bare `kind = "api-snapshot"` without
   framework_profile rejected by all three; with resolvable framework_profile and
   correct 2-record root accepted by all three; sha384 pinned value rejected by all
   three; unpinned kind with sentinel accepted by all three.
2. Pin resolution modes: rs main.rs routes validate_closure_root in Mode::Auto and
   Mode::Provenance (lines ~4588-4603), pin_map + loaded_profiles built once per run
   before the file loop; go main.go identical structure (lines ~3383-3408). No
   closure-validating path without pins found. Legacy `kind` synonym honored in pin
   resolution by all three (rs pinned_closure_inputs; go pinnedClosureInputs; py
   validate_closure_root.py lines 185-188).
3. Exclusions: every examples/negative/*.toml is named in validate.yml at least once
   in an assertion context (check_rejects or the provenance expected-failure loop);
   the four single-named api-snapshot kind negatives are check_rejects assertions
   against validate_api_snapshot.py (validate.yml lines 827-838). Conformance invalid
   cases asserted by the runner (25-case run requires rs=go=py reject on invalid).
4. Extends dedup: with a child profile com.verivus.child extending com.verivus.runtime
   (no own pins), the shipped example still passes all three (single emission). Child
   re-pinning a parent field is rejected by all three as "duplicate closure-record pin
   ... after the extends union (INV07)". Duplicate with DIFFERENT presence injected
   in place into PROFILE.toml: rejected by all three (dup keyed on (contained_kind,
   field) per frozen grammar). Degraded config (duplicate present in tree): all three
   reject the example document identically, no divergence.
   Caveat discovered: validating an out-of-tree descriptor file whose profile.name
   collides with a discovered descriptor resolves the union by name against the
   DISCOVERED set, so injected duplicates in such a shadow file are not seen; not a
   gate issue (real descriptors are discovered in place), noted for completeness.
5. INV07: shipped negative rejected by all three with the same six violations;
   error text NOT byte-identical (presence enum rendering differs:
   rs ["required", "when-present"] / go [required when-present] / py
   ['required', 'when-present']). New violations (empty field, trailing dot,
   presence typo, closure_records non-array) rejected by all three (verdict parity).
6. RKV03: lingering-digest fixture rejected by validate_api_snapshot.py; py-closure
   ACCEPTS (deliberately closure-valid); rs/go auto reject ONLY on the fixture's
   deliberate provenance error (source_bytes 621 vs 620, documented in the fixture
   header); rs/go closure layer accepts (no 12.8.1 error emitted). Boundary stated in
   the kind descriptor (RKV03 enforced_by validate_api_snapshot.py) and freeze 1.4.
7. Spec 12.8.1 text matches implementations: record shape "<field> <sha256:64hex>\n",
   bytewise sort of the union, sentinel unchanged, sha256-only, required/when-present
   semantics, framework_profile missing/unresolvable rejection, no pin-free
   fall-through. Field grammar identical in go/py regex and rs hand-rolled equivalent.
8. CI coherence: replicated the closure discover step (PASS) and every new
   check_rejects invocation verbatim (all correctly rejected).
9. Process: no em dash and no bare `kind =` in any ADDED diff line; schema_version /
   ontology_version only appear as additions in new files at pinned values; CHANGELOG
   touched by all unit commits EXCEPT a2d6b92.
10. Record numbers: 25 conformance cases reproduces; "80 files" does NOT (79 clean);
    4 descriptors, 7/4 invariants, 20 abstraction-class files, taplo clean reproduce.
    C06 precedence verified: GO commit ddcd365 (2026-07-13T07:12:39+10:00) is an
    ancestor of U03 d22bd8f (07:15:19).

## Consolidated required fixes (final; all three reviewer verdicts in, every item orchestrator-reproduced)

Verdicts: codex APPROVAL WITH REQUIRED FIXES (6 items), gemini APPROVAL WITH
REQUIRED FIXES (2 items), grok APPROVAL WITH REQUIRED FIXES (4 items). No blocker;
no unconditional approval. Merged and ranked:

P1 code fixes (triad divergences / frozen-grammar escapes; all land in the triad together):
  F1. Python full-string anchoring: PINNED_VALUE_RE (validators/validate_closure_root.py:67)
      and CLOSURE_RECORD_FIELD_RE (validators/validate_profile_descriptor.py:66) use "$"
      via re.match, accepting a trailing newline that rs/go reject. VERDICT divergence.
      Repro: scratchpad/adv/adv5-trailing-newline-pin.toml (rs 1 / go 1 / py 0),
      scratchpad/adv/e7-field-newline.toml (rs 1 / go 1 / py 0). [codex 3]
  F2. Duplicate-profile-name pin-map shadowing erases pins in all three (frozen 1.3
      "no pin-free fall-through" escape): validate_closure_root.py:91, main.rs:3037,
      main.go:2773. Repro: --repo-root /tmp/crfp-duplicate-name
      api-snapshot-escape-missing-fp.toml accepted by all three. [codex 1]
  F3. Discovery-semantics parity: (a) Go skips symlinked profile dirs (main.go:2756;
      go 0 vs rs 1 / py 1 on /tmp/crfp-mini-repo/symlink-pinned-escape.toml with
      --repo-root /tmp/crfp-mini-valid); (b) Python merges supplied descriptor files
      into extends resolution, rs/go do not (validate_profile_descriptor.py:471;
      valid parent/child pair passes py, fails rs/go). [codex 2]

P2 test coverage:
  F4. Add tracked conformance fixtures for the frozen parity-matrix rows without repo
      coverage: pinned kind with missing framework_profile, with unresolvable
      framework_profile, when-present absent (accept), unpinned kind (accept), plus
      regressions for F1-F3. [gemini 1; codex 5]

P3 record / spec-text / process:
  F5. 80 -> 79: verification record lines 43 and 66, CHANGELOG.md line 15. Root cause:
      author's count included the gitignored local tools/werner-style-policy.toml.
      [grok 1; gemini 2; codex 5]
  F6. Drop or qualify "byte-identical error sets" (C04): presence-set rendering differs
      (rs ["required", "when-present"] / go [required when-present] / py
      ['required', 'when-present']), or normalize the formatters. [grok 2; codex 5]
  F7. Declare the U09 deviation (.github/workflows/validate.yml touched, absent from
      the planned U09 file list). [grok 3; codex 6]
  F8. CHANGELOG entry for a2d6b92 (only commit in the stack without one). [grok 4; codex 6]
  F9. Reconcile docs: add the frozen "exactly three keys" sentence to spec.md 12.8.1
      (enforcement already exists in all three: unknown key `extra` rejected with
      "INV07: exactly contained_kind / field / presence"); fix freeze 1.4 naming
      `attester_observed` where the schema implements snapshot.witness.observed.
      NOTE: any edit to freeze sections 1-2 re-opens U02 by its own rule; route this
      as a U02-gated errata. [codex 4]
  F10. Evidence hygiene: persist or retract the m1-m9 parity cases and the 30-row
      baseline comparison (cited as C01/C03 evidence, not in the repo); update stale
      unit statuses in implementation-dag.toml (U09 still "pending"); fix EOF
      whitespace flagged by git diff --check. [codex 5, 6]

Contested / corrected during adjudication:
  - Codex's claim that unknown closure-record keys are unenforced: WRONG at the
    enforcement level (all three reject), RIGHT that spec.md text omits the rule;
    folded into F9 as text-only.
  - Codex's field-newline repro file was stale (carries `extra`, rejected by all
    three for that reason); defect confirmed with a clean isolated fixture (F1 stands).
  - Gemini's surface-9 "deviations match" conflicted with grok/codex; grok/codex
    version is evidence-backed (git show --name-only 2da8769) and adopted (F7).
  - Grok/record "primaries ACCEPT the lingering-digest fixture": true at the closure
    layer / provenance mode; in auto mode both primaries reject it on the fixture's
    DELIBERATE source_bytes=621 provenance error (documented in the fixture header);
    not a finding, recorded as a nuance.
