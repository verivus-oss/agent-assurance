# U10 round-2 orchestrator verification log (coordinator; does not approve)

Target: commit bef13ad on impl/crfp-u10-verify. Binaries rebuilt at bef13ad
(cargo reported 0 crates recompiled: already current; go rebuilt to
/tmp/dagtoml-validate-go). All commands run from the repo root or the clean
worktree wt-mine (detached at bef13ad).

## Per-fix verification (orchestrator's own runs)

- F1 (\Z anchors) APPLIED, SWEEP INCOMPLETE. adv5-trailing-newline-pin: rs 1 /
  go 1 / py 1. e7-field-newline: rs 1 / go 1 / py 1. Committed regression
  conformance/cases/api-snapshot/invalid/trailing-newline-pinned-digest.toml
  rejected by py. BUT see N1: two more $-anchored regexes were left in
  validate_profile_descriptor.py and one produces a real verdict divergence.
- F2 (duplicate-name fail-closed) APPLIED. /tmp/crfp-duplicate-name:
  api-snapshot-escape-missing-fp.toml and api-snapshot-escape.toml now exit 1
  in rs, go, py-closure; py --discover exits 1; validate_profile_descriptor
  exits 1. Message semantics identical ("pin resolution refuses to proceed
  (SPEC 12.8.1)"; py renders the section sign). rs/go run the check on every
  invocation (single call site each, before the file loop:
  main.rs:4574, main.go:3393). No-profiles-dir root: no spurious duplicate
  failure in any implementation (rs/go fail later only on the missing core
  ontology, unrelated; py-closure passes). Pin-consuming entry points
  enumerated: rs main, go main, validate_closure_root.py,
  validate_profile_descriptor.py; all four run the check.
  validate_api_snapshot.py does not consume pins (grep: no pin map usage).
- F3a (Go symlink discovery) APPLIED. symlink-pinned-escape.toml with
  --repo-root /tmp/crfp-mini-valid: rs 1 / go 1 / py 1 (was go 0).
  Adversarial: self-referential symlink cycle + dangling symlink in
  profiles/: all three exit 1 on the unresolvable-profile document, no hang,
  no crash (os.Stat returns ELOOP / ENOENT, entry skipped). Symlink alias
  duplicating a real profile name: all three fail closed with the duplicate
  message (symlinks cannot smuggle a shadow past the dup check).
- F3b (Python CLI-merge narrowing) APPLIED. Out-of-tree parent+child pair on
  one CLI invocation: py now exits 1 like rs/go. CI multi-file invocation
  (all 4 discovered descriptors in one call, validate.yml ~760): passes,
  "files validated: 4". Round-1 caveat unchanged and parity-preserved: an
  out-of-tree file whose profile.name collides with a discovered descriptor
  resolves against the discovered doc in all three (e5/e6: 0/0/0).
- F4 (conformance cases) APPLIED with a scope note. make dagtoml-conformance:
  29 cases, CONFORMANCE PASSED. New cases: missing-framework-profile,
  unresolvable-framework-profile, trailing-newline-pinned-digest (invalid),
  unwitnessed-three-record (valid). Sidecars: optional per runner.py:119;
  api-snapshot invalid cases carry none, consistent with the U09 cases.
  F2/F3 regressions are NOT in the corpus; the parity-harness note
  (03-parity-harness.md:15-18) documents why (conflicting PROFILE.toml dirs
  cannot live in the repo's own profile set) but claims the roots are
  "recorded in the U10 review evidence directory", which is only true as
  prose descriptions with /tmp paths (see N4).
- F5 (79 count) APPLIED AT c1be19c, STALE AT bef13ad. Clean worktree:
  c1be19c -> 79 files; bef13ad -> 80 files (delta = the fix commit's own new
  valid conformance case, discovered by the sweep). See N2.
- F6 (byte-identical qualified) APPLIED. Record C04 bullet carries the
  review correction re presence-enum rendering.
- F7 (U09 deviation) APPLIED. Deviations item 4 names the U09
  validate.yml modification.
- F8 (a2d6b92 CHANGELOG) APPLIED. CHANGELOG names a2d6b92 and the
  (field, presence) dedup; record deviations item 3 matches.
- F9 (spec sentence + freeze errata) APPLIED. spec.md ~1192: "EXACTLY the
  three keys `contained_kind`, `field`, and `presence`; unknown keys are
  rejected (INV07)". Freeze errata added as NEW section 6 (sections 1-2
  untouched, so U02 not re-opened; errata states "no frozen-scope change").
  attester_observed naming errata present.
- F10 (evidence hygiene) PARTIAL. m1-m9 harness persisted in
  03-parity-harness.md; all 13 embedded fixtures byte/semantically MATCH the
  runnable copies and the 9 verdicts reproduce exactly (A R R A R R R A A in
  py/rs/go). DAG statuses updated (U03-U09 done, U10 in_progress). EOF
  whitespace: the OLD instance (witness-stripped.toml) fixed, but the fix
  commit INTRODUCES a new blank line at EOF (N3). 30-row baseline: not
  persisted anywhere (N4).

## New findings (orchestrator, pre-reviewer)

- N1 (P1, triad verdict divergence; incomplete F1 sweep):
  validators/validate_profile_descriptor.py:51 REVERSE_DNS_RE (and :50
  UNPREFIXED_RE, same class) still use `$` with .match (line 120-121).
  Python's $ tolerates a trailing newline; Go's regexp `$` and the Rust
  hand-rolled is_reverse_dns (main.rs:3069) do not. Repro
  (adv/r2-name-newline2.toml: profile-descriptor with
  name = "com.example.base\n", namespace com.example, contained_kinds = [],
  validated out-of-tree against /tmp/crfp-mini-repo):
    python3 validators/validate_profile_descriptor.py --repo-root
      /tmp/crfp-mini-repo r2-name-newline2.toml  -> exit 0 (PASSED)
    rs --mode profile -> exit 1 ("[profile].name `com.example.base\n` ...")
    go --mode profile -> exit 1
  Newline directory names are legal on Linux, so this is reachable in-tree
  as well. Contrast: CLOSURE_ROOT_RE (validate_closure_root.py:52) also
  keeps `$`, but every post-match path ends in reject or the raw-string
  equality at line 371 (`value != expected` on the un-stripped value), so no
  ACCEPT is reachable; verdict-safe, hardening-only.
- N2 (P3, record accuracy): 02-verification-record.md:44 and :71 plus
  CHANGELOG say "79 conforming files on a clean tree", but at bef13ad (the
  commit that lands the sentence) a clean tree yields 80: the fix commit's
  own conformance/cases/api-snapshot/valid/unwitnessed-three-record.toml is
  swept. Line 72 also still says "dagtoml-conformance 25 cases" while the
  C01 bullet (line 25) says 29; neither number is pinned to a commit.
- N3 (P3, trivial): git diff --check planning/..bef13ad reports
  "conformance/cases/api-snapshot/valid/unwitnessed-three-record.toml:34:
  new blank line at EOF": the F10 EOF-whitespace fix introduced a new
  instance of the same nit.
- N4 (P3): 03-parity-harness.md:13-18 claims the 30-row U06/U07 baseline
  and the duplicate-name/symlink adversarial roots are "recorded in the U10
  review evidence directory"; the directory contains only prose references
  with ephemeral /tmp paths, not the 30 rows nor reconstructible fixture
  contents.

## Sweeps at bef13ad (orchestrator)

- make dagtoml-conformance: 29 cases PASSED. taplo lint exit 0.
- CI-style discover with 3 excludes: PASSED (80 files, clean worktree).
- adv1-4, e1-e7, m1-m9: full triad parity (details above).

## Round-2 dispatch and adjudication

Gateway: llm-cli-gateway (mcp llm-gateway). The gateway confines
workingDir to registered workspaces, so reviewers ran in fresh git
worktrees under the allowed repos root instead of the scratchpad ones:
aa-r2-codex / aa-r2-gemini / aa-r2-grok, all detached at bef13ad
(scratchpad wt-codex/wt-gemini/wt-grok/wt-mine also moved to bef13ad but
were not used by reviewers). Jobs: codex 7d66eaa9 (13.5 min), gemini
80cb1b42 (4 min), grok 8cdc50eb (3 min). No reviewer modified any
tracked file (git status checked in all three worktrees).

Verdicts: codex / gemini / grok all APPROVAL WITH REQUIRED FIXES, all
evidence-based (commands + file:line cited; no approval-on-intent).
Consolidated list: u10-r2-consolidated-fixes.md (R2-1 .. R2-8; two P1,
two P2, four P3). Reviewer-unique claims adjudicated:
- codex fallback-lookup symlink divergence (R2-2): orchestrator
  reproduced py=0/rs=1/go=1 and confirmed both cited non-following
  dir checks.
- codex stale docstring/diagnostics (R2-7) and conformance README
  counts (R2-8): orchestrator confirmed at the cited lines.
- grok unpref-nl ACCEPT variant of R2-1: orchestrator reproduced.
- No claim rejected this round.

Orchestrator's independent N1-N4 were all independently rediscovered by
at least one reviewer (N1 by all three) without being seeded in the
prompt.
