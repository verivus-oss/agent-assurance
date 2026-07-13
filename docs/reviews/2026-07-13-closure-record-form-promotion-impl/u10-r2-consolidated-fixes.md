# U10 round-2 consolidated required fixes (FINAL; all three verdicts in)

Verdicts: codex APPROVAL WITH REQUIRED FIXES (5 items), gemini APPROVAL
WITH REQUIRED FIXES (3 items), grok APPROVAL WITH REQUIRED FIXES (5
items). No blocker; no unconditional approval. Every load-bearing claim
orchestrator-reproduced. Merged and ranked:

P1 code fixes (triad verdict divergences; land in the triad together with
tracked regressions):

  R2-1. Residual $ anchors in validate_profile_descriptor.py:50-51
        (UNPREFIXED_RE, REVERSE_DNS_RE, used via .match at :120-121).
        Python ACCEPTS profile descriptors whose name ends in a newline;
        rs/go reject. F1's sweep stopped at the two closure-pin regexes
        in the same file. Repro: /tmp/crfp-grok-r2/residual/name-nl.toml
        and unpref-nl.toml, /tmp/codex-r2-regex/profile-name-newline.toml,
        adv/r2-name-newline2.toml: all py=0 rs=1 go=1.
        Optional hardening in the same pass: CLOSURE_ROOT_RE
        (validate_closure_root.py:52) to \Z/fullmatch; verdict-safe today
        (raw-value equality at :371) but the format-error path differs.
        [codex 1; gemini 1; grok 1; orchestrator N1]

  R2-2. Symlinked profile dirs still skipped in the FALLBACK
        kind-descriptor candidate enumeration: go main.go:2866-2870
        (e.IsDir()) and rs main.rs:3172-3177 (entry.file_type().is_dir())
        are non-following; Python follows. F3a fixed only
        discoverDescriptors/profile::discover. Repro:
        /tmp/r2-codex-kind-symlink + /tmp/r2-codex-external-profile:
        py=0 rs=1 go=1 (--mode profile). [codex 2; orchestrator-reproduced]

P2 coverage / record substance:

  R2-3. Clean-tree discover at bef13ad is 80, not 79: the fix commit's own
        conformance/cases/api-snapshot/valid/unwitnessed-three-record.toml
        enters the positive sweep (delta isolated by exclusion). Correct
        02-verification-record.md:44 and :71, CHANGELOG.md:33, review
        README:30, and pin every count to the ref it was measured at
        (79 @ c1be19c, 80 @ bef13ad). [codex 4; gemini 3; grok 2;
        orchestrator N2]

  R2-4. Tracked, executable regressions for the F1 field-path variant and
        the F2/F3 alternate-root cases are still absent (four api-snapshot
        fixtures only), while 02-verification-record.md ~:124 and
        03-parity-harness.md:13-18 claim the roots are "recorded in the
        U10 review evidence directory" (the dir holds prose with
        ephemeral /tmp paths). Either extend the corpus/harness with
        reconstructible alternate roots (they are tiny; the m1-m9 pattern
        works) or reword both claims to match what is actually persisted,
        and persist or retract the 30-row baseline. [codex 3, 5; grok 5;
        orchestrator N4]

P3 record / doc / hygiene:

  R2-5. 02-verification-record.md:72 Full-sweep still says
        "dagtoml-conformance 25 cases" (C01 and CHANGELOG correctly say
        29). [codex 4; grok 3]
  R2-6. EOF blank line at
        conformance/cases/api-snapshot/valid/unwitnessed-three-record.toml:34
        (git diff --check exit 2); introduced by the commit that closed
        the F10 EOF item. [codex 5; gemini 2; grok 4; orchestrator N3]
  R2-7. Stale prose/diagnostics after the F3b narrowing:
        validate_profile_descriptor.py:35 docstring and :379 error text
        still say CLI-passed files join extends resolution ("the explicit
        --files set"). [codex 4; orchestrator-verified]
  R2-8. conformance/README.md:65 coverage counts stale: api-snapshot says
        1 valid / 3 invalid (actual 2 / 6); implementation-dag valid 2
        (actual 3). [codex 4; orchestrator-verified]

Contested / adjudicated:
  - No reviewer claim was rejected this round. Codex "F1 partial / F3
    partial" vs gemini/grok "yes as scoped" is framing, not conflict.
  - Grok/orchestrator agreement that CLOSURE_ROOT_RE has no reachable
    ACCEPT divergence stands (hash equality on the raw value); folded
    into R2-1 as optional hardening.
  - e5/e6 acceptance re-confirmed by grok and orchestrator as the
    pre-existing round-1 name-collision caveat, unchanged by F3b; not a
    regression, remains a recorded caveat.

Cleared surfaces (consensus, adversarially probed):
  F2 fail-closed parity in every mode and entry point (rs/go main before
  the file loop; py closure single-file and --discover; py profile
  validator), incl. symlink-alias duplicates and roots with no profiles
  dir; F3a discovery symlinks: cycles, dangling links, escapes: no hang,
  no crash, verdict parity; rs/go discover() exactly one call site each;
  F3b: CI 4-descriptor single invocation intact, out-of-tree pairs
  rejected by all three; corpus 29/29 in all three; taplo clean; m1-m9
  harness faithful (13/13 embedded fixtures match the runnable copies,
  9/9 verdicts reproduce A R R A R R R A A).
